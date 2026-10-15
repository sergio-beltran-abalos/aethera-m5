"""
Aethera · agenda y motor de propuesta de citas.

La agenda es SIMULADA y determinista (semilla fija) para que el video y las
evaluaciones salgan siempre iguales. Los horarios de apertura, la capacidad y
las coordenadas sí vienen del Data Pack (D6); la ocupación se simula.

Ranking de un turno:

    puntaje = P(asistir)  +  0.03·(sede en su distrito)  −  0.002·días_hasta

`P(asistir)` viene del modelo entrenado sobre D2. Los otros dos términos son
preferencias de producto: acercar la sede al estudiante y ofrecerla cuanto antes.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd

from . import config as C
from . import datos, horarios
from .horarios import a_hhmm, a_minutos, es_compatible

DURACION_MIN = 60
PESO_DISTRITO = 0.03
PESO_ANTICIPACION = 0.002


# ─────────────────────────────────────────────────────────────────────────────
# Agenda simulada
# ─────────────────────────────────────────────────────────────────────────────
def generar_agenda(semilla: int = C.SEMILLA, desde: str | None = None,
                   horizonte: int = C.HORIZONTE_DIAS) -> pd.DataFrame:
    srv = datos.servicios().copy()
    inicio = date.fromisoformat(desde or C.FECHA_DEMO) + timedelta(days=1)
    cmin, cmax = srv["capacity"].min(), srv["capacity"].max()

    filas = []
    for d in range(horizonte):
        fecha = inicio + timedelta(days=d)
        for _, s in srv.iterrows():
            dias, abre, cierra = s["dias"], s["abre"], s["cierra"]
            if fecha.weekday() not in dias:
                continue
            # Un servicio con más capacidad se satura menos por turno.
            p_ocupado = 0.75 - 0.35 * (s["capacity"] - cmin) / max(1, (cmax - cmin))
            rng = random.Random(f"{semilla}|{s['service_id']}|{fecha}|{abre}")
            for h in range(abre, cierra, DURACION_MIN):
                for canal in s["channels"]:
                    filas.append({
                        "slot_id": f"{s['service_id']}|{fecha}|{a_hhmm(h)}|{canal}",
                        "service_id": s["service_id"],
                        "service_name": s["name"],
                        "service_type": s["service_type"],
                        "district_id": s["district_id"],
                        "lon": s["lon"], "lat": s["lat"],
                        "fecha": fecha,
                        "inicio_min": h,
                        "fin_min": h + DURACION_MIN,
                        "canal": canal,
                        # Espera REAL del servicio (D2): es lo que se le pasa al
                        # modelo, dentro de su rango de entrenamiento.
                        "espera_servicio": float(s["espera_media_dias"]),
                        "estado": "ocupado" if rng.random() < p_ocupado else "libre",
                    })
    return pd.DataFrame(filas)


class Agenda:
    """Agenda mutable: se pueden reservar y liberar turnos durante la sesión."""

    def __init__(self, desde: str | None = None):
        self.desde = desde or C.FECHA_DEMO
        self.regenerar()

    def regenerar(self) -> None:
        self.df = generar_agenda(desde=self.desde)

    def reservar(self, slot_id: str) -> bool:
        idx = self.df.index[self.df["slot_id"] == slot_id]
        if len(idx) == 0 or self.df.loc[idx[0], "estado"] != "libre":
            return False
        self.df.loc[idx[0], "estado"] = "reservado"
        return True

    def liberar(self, slot_id: str) -> None:
        idx = self.df.index[self.df["slot_id"] == slot_id]
        if len(idx):
            self.df.loc[idx[0], "estado"] = "libre"

    def estadisticas(self) -> dict:
        libres = self.df["estado"] == "libre"
        return {
            "turnos": len(self.df),
            "libres": int(libres.sum()),
            "tasa_libre": float(libres.mean()),
            "reservados": int((self.df["estado"] == "reservado").sum()),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Compatibilidad (vectorizada)
# ─────────────────────────────────────────────────────────────────────────────
def _mascara_compatible(perfil: dict, df: pd.DataFrame) -> pd.Series:
    """
    Igual que `horarios.es_compatible` pero por weekday, sin `apply` fila a fila.

    Los bloques ocupados solo dependen del perfil y del día de la semana, así
    que se calculan 7 veces en vez de una por fila.
    """
    if df.empty:
        return pd.Series(dtype=bool)

    semana = {d: horarios.bloques_ocupados(perfil, d) for d in range(7)}
    margen_cache: dict[tuple, int] = {}

    def fila_ok(s) -> bool:
        clave = (s["canal"], s["service_id"])
        if clave not in margen_cache:
            margen_cache[clave] = horarios.margen_para(perfil, s["canal"], s["service_id"])
        margen = margen_cache[clave]
        for a, b in semana[s["fecha"].weekday()]:
            if s["inicio_min"] < b + margen and s["fin_min"] > a - margen:
                return False
        return True

    return df.apply(fila_ok, axis=1)


# ─────────────────────────────────────────────────────────────────────────────
# Candidatos y ranking
# ─────────────────────────────────────────────────────────────────────────────
def candidatos(perfil: dict, tipo: str, agenda: pd.DataFrame, *,
               excluir_slots=(), evitar_dias=(), excluir_fechas=(),
               franja=None, canal_preferido=None) -> pd.DataFrame:
    """Turnos libres, del tipo pedido, accesibles y compatibles con el horario."""
    df = agenda[(agenda["estado"] == "libre") & (agenda["service_type"] == tipo)]
    if df.empty:
        return df.copy()

    # Presencial solo si la sede está en su distrito; virtual/teléfono en cualquiera.
    df = df[(df["canal"] != "in_person") | (df["district_id"] == perfil["district_id"])]

    if excluir_slots:
        df = df[~df["slot_id"].isin(set(excluir_slots))]
    if evitar_dias:
        df = df[~df["fecha"].map(lambda f: f.weekday()).isin(set(evitar_dias))]
    if excluir_fechas:
        df = df[~df["fecha"].map(lambda f: f.isoformat()).isin(set(excluir_fechas))]
    if franja == "mañana":
        df = df[df["inicio_min"] < 12 * 60]
    elif franja == "tarde":
        df = df[(df["inicio_min"] >= 12 * 60) & (df["inicio_min"] < 18 * 60)]
    elif franja == "noche":
        df = df[df["inicio_min"] >= 18 * 60]
    if canal_preferido in C.CANAL_ES:
        df = df[df["canal"] == canal_preferido]

    return df[_mascara_compatible(perfil, df)]


def puntuar_para(df: pd.DataFrame, perfil: dict, motivo: str) -> pd.DataFrame:
    """Ranking completo de un conjunto de candidatos, con el motivo como entrada del modelo."""
    if df.empty:
        df = df.copy()
        df["dias_hasta"] = []
        df["espera_dias"] = []
        df["p_asistencia"] = []
        df["puntaje"] = []
        df["confianza_ml"] = []
        return df

    from . import ml

    hoy = date.fromisoformat(C.FECHA_DEMO)
    df = df.copy()
    # El feature `espera_dias` del modelo es el retraso real que enfrenta el
    # estudiante: hoy pide y le ofrecen un turno a `dias_hasta` días. Es la
    # misma magnitud que `wait_days` en D2 (cita − solicitud).
    df["dias_hasta"] = df["fecha"].map(lambda f: (f - hoy).days)
    df["espera_dias"] = df["dias_hasta"].astype(float)
    df["p_asistencia"] = ml.p_asistencia_lote(df, motivo)

    # Si el modelo está extrapolando, su orden pesa menos: el término de
    # cercanía y de anticipación mandan. No se oculta la señal, se la pondera.
    confianza = df["espera_dias"].map(lambda e: ml.modelo().confianza(float(e))[0])
    df["confianza_ml"] = confianza.round(2)
    peso_ml = 1.0 + (confianza - 1.0) * 0.8      # confianza 0 → peso 0.2
    df["puntaje"] = (peso_ml * df["p_asistencia"]
                     + PESO_DISTRITO * (df["district_id"] == perfil["district_id"])
                     - PESO_ANTICIPACION * df["dias_hasta"])
    return df.sort_values("puntaje", ascending=False)


def seleccionar_diversas(df: pd.DataFrame, n: int) -> list:
    """
    Top-n evitando repetir día y combinación servicio+canal.

    Que la variedad importa en salud mental: ofrecer tres citas el mismo martes
    en el mismo lugar no es "tres opciones", es una sola.
    """
    elegidas, dias, combos = [], set(), set()
    for _, s in df.iterrows():
        if s["fecha"] in dias or (s["service_id"], s["canal"]) in combos:
            continue
        elegidas.append(s)
        dias.add(s["fecha"])
        combos.add((s["service_id"], s["canal"]))
        if len(elegidas) == n:
            return elegidas

    for _, s in df.iterrows():
        if len(elegidas) == n:
            break
        if not any(s["slot_id"] == e["slot_id"] for e in elegidas):
            elegidas.append(s)
    return elegidas


# ─────────────────────────────────────────────────────────────────────────────
# Propuesta
# ─────────────────────────────────────────────────────────────────────────────
def formatear_opcion(i: int, s, puente: bool) -> dict:
    from . import ml
    conf, nota_conf = ml.modelo().confianza(float(s["espera_dias"]))
    return {
        "opcion": i,
        "slot_id": s["slot_id"],
        "service_id": s["service_id"],
        "servicio": s["service_name"],
        "tipo": C.TIPO_ES[s["service_type"]],
        "canal": C.CANAL_ES[s["canal"]],
        "distrito": s["district_id"],
        "dia": C.DIAS_ES[s["fecha"].weekday()],
        "fecha": s["fecha"].isoformat(),
        "hora": f"{a_hhmm(s['inicio_min'])}–{a_hhmm(s['fin_min'])}",
        "es_puente_pares": puente,
        "p_asistencia": round(float(s["p_asistencia"]), 3),
        "confianza_ml": round(float(conf), 2),
        "nota_confianza": nota_conf,
        # Espera media real de ese servicio en D2: contexto honesto para el estudiante.
        "espera_servicio_dias": int(round(float(s["espera_servicio"]))),
    }


def proponer_opciones(perfil: dict, reason_code: str, agenda: Agenda, n: int = 3,
                      tipo: str | None = None, **filtros) -> dict:
    """
    Propone hasta `n` turnos.

    `tipo` fuerza un tipo de servicio (p. ej. pares si el estudiante lo pide).
    Si el tipo principal no alcanza, completa con pares y marca seguimiento
    humano: nunca se responde "no hay nada".
    """
    tipo = tipo or datos.mapa_motivo_servicio()[reason_code]
    df_agenda = agenda.df

    def buscar(tipo_srv: str, k: int, **f) -> list:
        df = candidatos(perfil, tipo_srv, df_agenda, **f)
        return seleccionar_diversas(puntuar_para(df, perfil, reason_code), k)

    principales = buscar(tipo, n, **filtros)

    nota_preferencia = None
    preferencias = {k for k in ("franja", "canal_preferido") if filtros.get(k)}
    if not principales and preferencias:
        relajados = {k: v for k, v in filtros.items() if k not in preferencias}
        principales = buscar(tipo, n, **relajados)
        if principales:
            nota_preferencia = ("No hay turnos con esa preferencia de horario o canal; "
                                "estas son las opciones más cercanas.")
            filtros = relajados

    opciones = [formatear_opcion(i + 1, s, False) for i, s in enumerate(principales)]

    nota = None
    if len(opciones) < n and tipo != "peer_support":
        puente = buscar("peer_support", n - len(opciones), **filtros)
        opciones += [formatear_opcion(len(opciones) + i + 1, s, True) for i, s in enumerate(puente)]
        nota = ("No hay suficientes turnos compatibles del servicio principal; se agregan "
                "espacios de pares como primer contacto y se marca seguimiento humano.")

    return {
        "tipo_principal": C.TIPO_ES[tipo],
        "opciones": opciones,
        "nota": nota,
        "nota_preferencia": nota_preferencia,
        "seguimiento_humano": nota is not None,
    }
