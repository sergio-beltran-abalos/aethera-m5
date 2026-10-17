"""
Aethera · motor de compatibilidad horaria.

Este es el núcleo del producto. Convierte "¿qué servicios necesito?" en "¿qué
citas puedo realmente cumplir?", resolviendo tres restricciones a la vez:

  1. Cuándo está abierto el servicio        → D6 (`schedule`)
  2. Cuándo está ocupado el estudiante      → D1 (`study_mode`, `employment_status`)
     y D3 (`credit_load`) para la carga real de clases
  3. Cuánto se demora en llegar             → D6 GeoJSON (coordenadas reales)

Lo que NO se infiere: en qué franja del día choca el estudiante. Eso se lo
pregunta la app en la conversación. Jamás se adivina.
"""
from __future__ import annotations

import math
import unicodedata
import re

import pandas as pd

from . import config as C
from . import datos

# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de tiempo
# ─────────────────────────────────────────────────────────────────────────────
def a_minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def a_hhmm(minutos: float | int) -> str:
    return f"{int(minutos) // 60:02d}:{int(minutos) % 60:02d}"


def parsear_horario(texto: str) -> tuple[set[int], int, int]:
    """'Mon-Sat 12:00-20:00' → ({0..5}, 720, 1200)"""
    dias, horas = texto.split()
    d0, d1 = dias.split("-")
    h0, h1 = horas.split("-")
    return (set(range(C.DIAS_INGLES[d0], C.DIAS_INGLES[d1] + 1)),
            a_minutos(h0), a_minutos(h1))


def normalizar(texto: str) -> str:
    texto = str(texto).lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto)
                    if unicodedata.category(c) != "Mn")
    return re.sub(r"[¿?¡!.,;:()\"']", " ", texto)


# ─────────────────────────────────────────────────────────────────────────────
# Distancias (D6 GeoJSON)
# ─────────────────────────────────────────────────────────────────────────────
_RADIO_TIERRA_KM = 6371.0


def _haversina(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df = f2 - f1
    dl = math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * _RADIO_TIERRA_KM * math.asin(math.sqrt(a))


_CENTROIDS: dict[str, tuple[float, float]] | None = None


def centroide_distrito(distrito: str) -> tuple[float, float] | None:
    """Punto medio de los servicios de un distrito (derivado de D6)."""
    global _CENTROIDS
    if _CENTROIDS is None:
        srv = datos.servicios()
        _CENTROIDS = {d: (float(g["lat"].mean()), float(g["lon"].mean()))
                      for d, g in srv.groupby("district_id")}
    return _CENTROIDS.get(distrito)


def minutos_traslado(origen_distrito: str, servicio_id: str) -> int:
    """
    Tiempo estimado de ida a una cita presencial, en minutos.

    Antes era una constante plana de 45 minutos para todos. Ahora sale de la
    distancia real entre el centro del distrito del estudiante y la sede.
    """
    srv = datos.servicios()
    fila = srv[srv["service_id"] == servicio_id]
    origen = centroide_distrito(origen_distrito)
    if fila.empty or origen is None:
        return int(C.SUPUESTOS_HORARIO["minutos_traslado_piso"])
    destino = (float(fila.iloc[0]["lat"]), float(fila.iloc[0]["lon"]))
    km = _haversina(origen[0], origen[1], destino[0], destino[1])
    vel = C.SUPUESTOS_HORARIO["velocidad_caminata_kmh"]
    return int(round(km / vel * 60)) + C.SUPUESTOS_HORARIO["minutos_traslado_piso"]


# ─────────────────────────────────────────────────────────────────────────────
# Carga académica (D3)
# ─────────────────────────────────────────────────────────────────────────────
def bloque_clases(perfil: dict) -> tuple[int, int]:
    """
    Ventana de clases del estudiante.

    El punto de partida es un supuesto explícito (no hay horarios en el pack),
    pero la DURACIÓN se escala con `credit_load` de D3: 20 créditos → bloque
    completo; menos créditos → bloque más corto. Así la carga real del dato
    modula la suposición en vez de ignorarla.
    """
    S = C.SUPUESTOS_HORARIO
    base = S["clases_diurno"] if perfil.get("study_mode") == "day" else S["clases_nocturno"]
    inicio, fin = a_minutos(base[0]), a_minutos(base[1])
    completo = fin - inicio

    creditos = datos.d3_carga(perfil.get("student_id", ""))
    if creditos is not None:
        proporcion = min(1.0, max(0.45, creditos / S["creditos_bloque_completo"]))
        # Mínimo de 3 h: siempre hay clases, aunque la carga sea baja.
        fin = inicio + max(180, int(completo * proporcion))
    return inicio, fin


# ─────────────────────────────────────────────────────────────────────────────
# Bloques ocupados y compatibilidad
# ─────────────────────────────────────────────────────────────────────────────
def bloques_ocupados(perfil: dict, dia_semana: int) -> list[tuple[int, int]]:
    """Intervalos (inicio, fin) en minutos en los que el estudiante NO puede asistir."""
    S = C.SUPUESTOS_HORARIO
    bloques: list[tuple[int, int]] = []

    if dia_semana <= 4:  # lunes a viernes
        bloques.append(bloque_clases(perfil))

        horas_dia = float(perfil.get("work_hours_week") or 0) / 5
        if horas_dia > 0:
            if horas_dia >= S["almuerzo_si_jornada_de"]:
                horas_dia += 1          # jornada larga: una hora de almuerzo
            clave = ("inicio_trabajo_diurno" if perfil.get("study_mode") == "day"
                     else "inicio_trabajo_nocturno")
            inicio = a_minutos(S[clave])
            bloques.append((inicio, inicio + int(horas_dia * 60)))
    elif dia_semana == 5 and not S["sabado_libre"]:
        bloques.append((a_minutos("08:00"), a_minutos("14:00")))

    return bloques


def margen_para(perfil: dict, canal: str, servicio_id: str | None = None) -> int:
    """Colchón antes/después de la cita, según canal y distancia real."""
    if canal != "in_person":
        return C.SUPUESTOS_HORARIO["margen_virtual_min"]
    if servicio_id:
        return minutos_traslado(perfil.get("district_id", ""), servicio_id)
    return int(C.SUPUESTOS_HORARIO["minutos_traslado_piso"]) + 35


def es_compatible(perfil: dict, fecha, inicio_min: int, fin_min: int,
                  canal: str, servicio_id: str | None = None) -> bool:
    margen = margen_para(perfil, canal, servicio_id)
    for a, b in bloques_ocupados(perfil, fecha.weekday()):
        if inicio_min < b + margen and fin_min > a - margen:
            return False
    return True


def describir_horario(perfil: dict) -> str:
    inicio, fin = bloque_clases(perfil)
    textos = [f"{a_hhmm(inicio)}–{a_hhmm(fin)}"]
    for a, b in bloques_ocupados(perfil, 0)[1:]:
        textos.append(f"{a_hhmm(a)}–{a_hhmm(b)}")
    return "Lun–Vie ocupado: " + ", ".join(textos) + (
        " · sábado libre" if C.SUPUESTOS_HORARIO["sabado_libre"] else "")


def resumen_fronteras(perfil: dict) -> dict:
    """
    Ventanas realmente libres en un día lectivo, en minutos.

    Se calculan restando los bloques ocupados, en vez de sondear tres horas
    sueltas: sondear las 15:00 da "ocupado" a un estudiante libre a las 17:00.

    La ventana se recorta al rango en que un servicio puede abrir realmente
    (06:00–23:30). Mostrar "libre de 00:00" no aporta información y confunde.
    """
    DIA_INICIO = a_minutos("06:00")
    DIA_FIN = a_minutos("23:30")

    ocupados = sorted(bloques_ocupados(perfil, 0))
    libres, cursor = [], DIA_INICIO
    for a, b in ocupados:
        if b <= DIA_INICIO or a >= DIA_FIN:
            continue
        a, b = max(a, DIA_INICIO), min(b, DIA_FIN)
        if a > cursor:
            libres.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < DIA_FIN:
        libres.append((cursor, DIA_FIN))

    return {
        "clases": _txt(bloque_clases(perfil)),
        "ventanas_libres": [f"{a_hhmm(a)}–{a_hhmm(b)}" for a, b in libres],
        "manana": any(a < 12 * 60 for a, _ in libres),
        "tarde": any(12 * 60 <= a < 18 * 60 for a, _ in libres),
        "noche": any(a >= 18 * 60 for a, _ in libres),
    }


def horarios_ocupados(perfil: dict, dia: int) -> list[tuple[int, int]]:
    """Alias explícito, para legibilidad en los callers."""
    return bloques_ocupados(perfil, dia)


def _txt(par: tuple[int, int]) -> str:
    return f"{a_hhmm(par[0])}–{a_hhmm(par[1])}"
