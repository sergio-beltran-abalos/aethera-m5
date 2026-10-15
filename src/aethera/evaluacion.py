"""
Aethera · evaluación offline.

Convierte afirmaciones en números. Tres experimentos, todos reproducibles con
semilla fija y sin depender de un modelo de lenguaje:

A) CLASIFICADOR vs. D5
   D5 trae el motivo real de 2.500 conversaciones etiquetado. Se le da solo el
   texto al clasificador y se mide cuánto acierta, contra la derivación que el
   sistema actual hizo en su día.

B) RUTA vs. DIRECTORIO  (el A/B que el E1 prometió prometió)
   Para N estudiantes reales de M5: qué cita propondría un directorio tradicional
   (primer turno libre del servicio correcto, sin mirar la agenda del
   estudiante) frente a Ruta (filtra por horario, distrito y canal).
   Se mide cuántas citas serían realmente cumplibles.

C) PROYECCIÓN sobre el indicador de la misión (68 %)
   Con supuestos declarados uno por uno y análisis de sensibilidad.

Nota de honestidad sobre (B): el 100 % de Ruta es por construcción, porque el
filtro es el producto. El experimento no mide "rendimiento de un modelo", mide
CUÁNTA fricción quita el solver. Escrito así es un número defendible; escrito
como "accuracy" sería una trampa, y con suerte alguien lo detectaría.
"""
from __future__ import annotations

import pandas as pd

from . import config as C, datos, horarios, servicios
from .segmentos import Segmentacion

SEMILLA = C.SEMILLA
N_EVALUACION = 300


# ─────────────────────────────────────────────────────────────────────────────
# A · Clasificador contra las etiquetas de D5
# ─────────────────────────────────────────────────────────────────────────────
def evaluar_clasificador(n: int = 1500) -> dict:
    """
    D5 trae 2.500 conversaciones YA ETIQUETADAS por motivo. Se mide el
    clasificador contra esas etiquetas de referencia, no con intuición.

    Importante: las palabras clave escritas a mano rendían 27 %, PEOR que la
    clase mayoritaria (20,6 %). Ese era el fallback "sin LLM" del prototipo
    anterior y era una falsa red de seguridad. Ahora el fallback es un
    clasificador entrenado sobre el propio D5.
    """
    from .ml import clasificar_texto, entrenar_clasificador_texto

    entrenado = entrenar_clasificador_texto()
    d5 = datos.cargar()["D5"].sample(n=min(n, 2500), random_state=SEMILLA)
    aciertos, filas = 0, []
    por_motivo: dict[str, dict] = {}

    for _, fila in d5.iterrows():
        predicho, conf = clasificar_texto(fila["texto_inicial"])
        real = fila["motivo"]
        ok = predicho == real
        aciertos += ok
        stats = por_motivo.setdefault(real, {"n": 0, "ok": 0})
        stats["n"] += 1
        stats["ok"] += ok
        if len(filas) < 12 and not ok:
            filas.append({"texto": fila["texto_inicial"][:90], "real": real, "predicho": predicho})

    d2 = datos.cargar()["D2"]
    coherencia_actual = float((d5["tipo_derivado"] == d5["tipo_esperado"]).mean())

    return {
        "n": len(d5),
        "accuracy": aciertos / len(d5),
        "accuracy_cv": entrenado["accuracy_cv"],
        "linea_base_clase_mayoritaria": float(d5["motivo"].value_counts(normalize=True).max()),
        "coherencia_derivacion_actual_D5": coherencia_actual,
        "azar_entre_tres_tipos": 1 / 3,
        "por_motivo": {k: {"n": v["n"], "accuracy": v["ok"] / v["n"]}
                       for k, v in por_motivo.items()},
        "errores": filas,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B · Ruta vs. Directorio tradicional
# ─────────────────────────────────────────────────────────────────────────────
def _directorio(agenda: pd.DataFrame, reason_code: str, perfil: dict) -> dict | None:
    """
    Lo que haría un directorio estático: el primer turno libre del tipo de
    servicio que corresponde, sin preguntar nada sobre la agenda del estudiante.
    """
    from . import datos as _d
    tipo = _d.mapa_motivo_servicio()[reason_code]
    libres = agenda[(agenda["estado"] == "libre") & (agenda["service_type"] == tipo)]
    if libres.empty:
        return None
    return libres.sort_values(["fecha", "inicio_min"]).iloc[0]


def _cumplible(perfil: dict, fila) -> bool:
    return horarios.es_compatible(perfil, fila["fecha"], fila["inicio_min"], fila["fin_min"],
                                  fila["canal"], fila["service_id"])


def comparar_ruta_directorio(n: int = N_EVALUACION) -> dict:
    """
    Compara Ruta contra lo que un directorio estatico realmente ofrece.

    La pregunta justa NO es "¿Ruta acierta mas que el azar?", porque el filtro ES
    el producto y entonces el 100 % es tautologico. La pregunta util es:

        ¿la informacion correcta estaba disponible y el estudiante tenia que
        encontrarla entre todos los turnos, o se le entrega ya filtrada?

    Por eso se mide, para cada estudiante del segmento prioritario:
      · cuantos turnos compatibles existen entre los que el directorio muestra
      · que fraccion de los turnos mostrados es compatible
      · y a quantos dias esta la primera opcion de Ruta
    """
    seg = Segmentacion()
    universo = seg.segmento
    if len(universo) > n:
        universo = universo.sample(n, random_state=SEMILLA)

    agenda = servicios.Agenda()
    motivos = list(C.MOTIVOS)

    ruta_ok = ruta_total = 0
    dir_con_alguno = 0
    turnos_totales = turnos_compatibles = 0
    ratios: list[float] = []
    dias_buscados: list[int] = []
    hoy = pd.Timestamp(C.FECHA_DEMO).date()

    for i, (_, est) in enumerate(universo.sample(frac=1.0, random_state=SEMILLA).iterrows()):
        perfil = {c: (est[c].item() if hasattr(est[c], "item") else est[c])
                  for c in ["student_id", "district_id", "country_context", "study_mode",
                            "employment_status", "work_hours_week", "services_awareness",
                            "support_network", "academic_stage"]}
        motivo = motivos[i % len(motivos)]

        # Lo que el directorio muestra: todos los turnos libres del tipo.
        tipo = datos.mapa_motivo_servicio()[motivo]
        oferta = agenda.df[(agenda.df["estado"] == "libre")
                           & (agenda.df["service_type"] == tipo)]
        compatibles = [f for _, f in oferta.iterrows() if _cumplible(perfil, f)] \
            if not oferta.empty else []
        turnos_totales += len(oferta)
        turnos_compatibles += len(compatibles)
        if len(oferta):
            ratios.append(len(compatibles) / len(oferta))
        if compatibles:
            dir_con_alguno += 1

        # Lo que Ruta propone.
        r = servicios.proponer_opciones(perfil, motivo, agenda, n=1)
        if r["opciones"]:
            ruta_total += 1
            op = r["opciones"][0]
            canal = next(k for k, v in C.CANAL_ES.items() if v == op["canal"])
            hhmm = op["hora"].split("–")[0]
            if horarios.es_compatible(perfil, pd.Timestamp(op["fecha"]).date(),
                                       horarios.a_minutos(hhmm),
                                       horarios.a_minutos(hhmm) + 60, canal, op["service_id"]):
                ruta_ok += 1
            dias_buscados.append((pd.Timestamp(op["fecha"]).date() - hoy).days)

    n = len(universo)
    ratios.sort()
    return {
        "n": n,
        "ruta_match_rate": ruta_ok / ruta_total if ruta_total else 0.0,
        "ruta_con_opcion": ruta_total,
        "directorio_con_alguno_turno_util": dir_con_alguno / n if n else 0.0,
        "turnos_promedio_por_estudiante": turnos_totales / n if n else 0.0,
        "fraccion_turnos_compatibles": turnos_compatibles / turnos_totales if turnos_totales else 0.0,
        "mediana_turnos_compatibles_por_estudiante": ratios[len(ratios) // 2] if ratios else 0.0,
        "dias_hasta_primera_opcion": (sum(dias_buscados) / len(dias_buscados)
                                      if dias_buscados else 0.0),
        "nota": ("El 100 % de Ruta es por construccion: filtrar la agenda ES el producto. "
                 "La cifra util es cuantos turnos tenia que revisar el estudiante para "
                 "encontrar uno viable."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# C · Proyección sobre el indicador de la misión (68 %)
# ─────────────────────────────────────────────────────────────────────────────
def proyectar_impacto(alcance: float = 0.30, conversion: float = 0.35) -> dict:
    """
    Proyección EXPLÍCITA, con los supuestos declarados y visibles.

    Cuidado con los denominadores, que es donde estos cálculos suelen fallar:
    el indicador de la misión ("% con sintomatología que nunca consultó un
    servicio") se calcula sobre los estudiantes con ansiedad moderada/alta, NO
    sobre M5. Por eso se resta del numerador y se divide por el mismo
    denominador que la línea base.

    Cada supuesto se puede cambiar desde la interfaz. Eso es lo que hace honesta
    una proyección: se ve de qué depende.
    """
    embudo = Segmentacion().embudo
    moderada_alta = embudo["moderada_alta"]
    m5 = embudo["m5"]
    prioritario = embudo["prioritario"]

    alcanzables = prioritario * alcance
    convertidas = min(m5, alcanzables * conversion)
    nuevo_pct = (m5 - convertidas) / moderada_alta

    return {
        "moderada_alta": moderada_alta,
        "linea_base_m5": m5,
        "m5_pct_base": embudo["m5_pct"],
        "prioritario": prioritario,
        "alcance": alcance,
        "conversion": conversion,
        "alcanzables": round(alcanzables),
        "convertidas": round(convertidas),
        "m5_pct_proyectado": nuevo_pct,
        "reduccion_pp": (embudo["m5_pct"] - nuevo_pct) * 100,
        "supuestos": [
            f"Denominador: {moderada_alta:,} estudiantes con ansiedad moderada/alta "
            f"(igual que la línea base del 68 %).",
            f"Alcance {alcance:.0%}: fracción del segmento prioritario ({prioritario}) que "
            "llega a usar Ruta.",
            f"Conversión {conversion:.0%}: de quienes usan Ruta, fracción que completa una reserva.",
            "Contrafactual conservador: se asume que sin Ruta esa demanda no se materializa. "
            "No está demostrado.",
            f"No se modela efecto sobre los {m5 - prioritario:,} estudiantes de M5 fuera del "
            "segmento prioritario.",
        ],
    }


def sensibilidad() -> pd.DataFrame:
    filas = []
    for alcance in [0.10, 0.20, 0.30, 0.50]:
        for conversion in [0.20, 0.35, 0.50]:
            p = proyectar_impacto(alcance, conversion)
            filas.append({"alcance": f"{alcance:.0%}", "conversión": f"{conversion:.0%}",
                          "M5 antes": f"{p['m5_pct_base']:.1%}",
                          "M5 después": f"{p['m5_pct_proyectado']:.1%}",
                          "reducción": f"{p['reduccion_pp']:+.1f} pp"})
    return pd.DataFrame(filas)


def ejecutar_todo() -> dict:
    return {
        "clasificador": evaluar_clasificador(),
        "ruta_vs_directorio": comparar_ruta_directorio(),
        "impacto": proyectar_impacto(),
        "sensibilidad": sensibilidad(),
    }


if __name__ == "__main__":  # pragma: no cover
    print("=" * 76)
    print("A · CLASIFICADOR DE NECESIDAD vs. D5 (2.500 conversaciones etiquetadas)")
    print("=" * 76)
    a = evaluar_clasificador()
    print(f"  Accuracy sobre muestra          {a['accuracy']:.1%}   (n={a['n']:,})")
    print(f"  Accuracy en CV (5 folds)        {a['accuracy_cv']:.1%}")
    print(f"  Linea base (clase mayoritaria)  {a['linea_base_clase_mayoritaria']:.1%}")
    print(f"  Derivacion actual de D5         {a['coherencia_derivacion_actual_D5']:.1%}"
          f"   (azar entre 3 tipos: {a['azar_entre_tres_tipos']:.1%})")
    print("\n  Por motivo:")
    for motivo, s in sorted(a["por_motivo"].items(), key=lambda kv: -kv[1]["accuracy"]):
        print(f"    {C.MOTIVO_CORTO[motivo]:20} {s['accuracy']:6.1%}  (n={s['n']})")

    print("\n" + "=" * 76)
    print("B · RUTA vs. DIRECTORIO ESTATICO  (300 estudiantes del segmento prioritario)")
    print("=" * 76)
    b = comparar_ruta_directorio()
    print(f"  Match Rate de Ruta                {b['ruta_match_rate']:.1%}")
    print(f"  Turnos que el directorio muestra   {b['turnos_promedio_por_estudiante']:.0f} por estudiante")
    print(f"  De esos, compatibles               {b['fraccion_turnos_compatibles']:.1%}")
    print(f"  Mediana de turnos viables          {b['mediana_turnos_compatibles_por_estudiante']:.0f}")
    print(f"  Estudiantes con AL MENOS 1 turno   {b['directorio_con_alguno_turno_util']:.1%} viable")
    print(f"  Primera opcion de Ruta a           {b['dias_hasta_primera_opcion']:.1f} dias")
    print(f"\n  {b['nota']}")

    print("\n" + "=" * 76)
    print("C · PROYECCION sobre el indicador de la mision")
    print("=" * 76)
    p = proyectar_impacto()
    print(f"  Denominador (ansiedad mod/alta)    {p['moderada_alta']:,}")
    print(f"  Linea base                         {p['m5_pct_base']:.1%}  ({p['linea_base_m5']:,} de {p['moderada_alta']:,})")
    print(f"  Segmento prioritario               {p['prioritario']:,}")
    print(f"  Proyectado (alcance 30%, conv 35%) {p['m5_pct_proyectado']:.1%}  ({p['reduccion_pp']:+.1f} pp)")
    print("\n  Supuestos:")
    for s in p["supuestos"]:
        print(f"    · {s}")

    print("\n  Sensibilidad:")
    print(sensibilidad().to_string(index=False))