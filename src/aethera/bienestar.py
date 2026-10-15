"""
Aethera · vista de Bienestar NOVA.

Lo que esta vista SÍ puede hacer y lo que NO, es lo más importante del módulo:

- Solo agregados. Ninguna celda muestra grupos de menos de K_MINIMO personas.
- Los ánimos individuales nunca aparecen: ni promedios por estudiante, ni
  distribuciones pequeñas, ni notas. Pulse es del estudiante y no se agrega.
- La cola de contacto humano lleva el mínimo: código, prioridad y motivo no
  clínico. Nunca lo que el estudiante escribió.

Los KPIs se calculan sobre la sesión de demostración, en vivo. Son indicadores
de uso del prototipo, NO resultados de un piloto. Decirlo en pantalla es parte
de la honestidad del ejercicio.
"""
from __future__ import annotations

import pandas as pd

from . import config as C
from . import datos

K_MINIMO = C.K_MINIMO
FRANJAS = [("madrugada", 0, 6), ("mañana", 6, 12), ("tarde", 12, 18), ("noche", 18, 24)]


def franja_de_hora(h: int) -> str:
    return next(n for n, a, b in FRANJAS if a <= h < b)


def demanda_agregada(dias: int = 14) -> pd.DataFrame:
    """Conversaciones de la línea de orientación (D5) en los últimos días."""
    fin = pd.Timestamp(C.FECHA_DEMO) + pd.Timedelta(days=1)
    d5 = datos.cargar()["D5"]
    v = d5[(d5["inicio"] >= fin - pd.Timedelta(days=dias)) & (d5["inicio"] < fin)].copy()
    v["franja"] = v["inicio"].dt.hour.map(franja_de_hora)
    return v


def _celda(n: int) -> str:
    return f"<{K_MINIMO}" if n < K_MINIMO else f"{n:,}".replace(",", ".")


def calcular_kpis() -> list[tuple]:
    """
    KPIs del E1 sobre el registro de eventos de la sesión de demo.
    Se recalculan en cada llamada, así que reflejan lo que el usuario hizo.
    """
    from . import agente
    ev = pd.DataFrame(agente.EVENTOS)
    if ev.empty:
        return []

    def ses(e: str) -> int:
        return int(ev.loc[ev["evento"] == e, "sesion"].nunique())

    def veces(e: str) -> int:
        return int((ev["evento"] == e).sum())

    reservas = ev[ev["evento"] == "reserva_confirmada"]
    base_d2 = datos.cargar()["D2"]["attended"].mean()

    def media(col: str):
        """Promedio de una columna de las reservas, o None si no hay reservas."""
        return float(reservas[col].mean()) if col in reservas.columns and len(reservas) else None

    def ratio(nombre: str, num: int, den: int, detalle: str) -> dict:
        return {"nombre": nombre, "formato": "pct", "valor": (num / den if den else None),
                "texto": (f"{num}/{den}" if den else "—"), "detalle": detalle}

    return [
        ratio("Activation Rate", ses("checkin_iniciado"), ses("checkin_mostrado"),
              "registraron su día / sesiones que vieron Pulse"),
        ratio("Pulse → Ruta", ses("pulse_a_chat"), ses("checkin_iniciado"),
              "abrieron el chat / registraron su día"),
        ratio("Match Rate", veces("opciones_mostradas") - veces("sin_opciones"),
              veces("opciones_mostradas"), "búsquedas con al menos una opción compatible"),
        ratio("Booking Conversion", ses("reserva_confirmada"), ses("busco_ayuda"),
              "reservaron / pidieron ayuda"),
        ratio("Replanning Success", veces("replanificacion_con_opciones"),
              veces("replanificacion_solicitada"), "replanificaciones con nuevas opciones"),
        {"nombre": "Time-to-Booking", "formato": "dias", "valor": media("time_to_booking"),
         "texto": f"{len(reservas)} reservas", "detalle": "días entre pedir y reservar"},
        {"nombre": "Asistencia esperada", "formato": "pct", "valor": media("p_asistencia"),
         "texto": f"{len(reservas)} reservas",
         "detalle": f"modelo ML sobre las reservas (histórico D2: {base_d2:.0%})"},
    ]


def fila_ml() -> dict:
    """Resumen del modelo, para mostrar sus límites sin esconderlos."""
    from . import ml
    m = ml.modelo()
    return {
        "modelo": m.metricas["modelo_elegido"],
        "auc": m.metricas["auc"],
        "auc_zona_demo": m.metricas["auc_zona_demo"],
        "n_zona_demo": m.metricas["n_zona_demo"],
        "cobertura_demo": m.metricas["cobertura_demo"],
        "tasa_base": m.metricas["tasa_base"],
        "n_eventos": m.metricas["n_eventos"],
    }


def fila_segmentacion() -> dict:
    from . import segmentos
    return segmentos.segmentacion().embudo


def filas_para_html() -> dict:
    """Todo lo que la vista necesita, en una llamada."""
    v = demanda_agregada()
    from . import agente
    pendientes = [s for s in agente.SOLICITUDES_CONTACTO if s["estado"] == "pendiente"]

    ctx: dict = {
        "n_conversaciones": len(v),
        "pendientes": len(pendientes),
        "kpis": calcular_kpis(),
        "tabla": v,
        "fila_ml": fila_ml(),
        "embudo": fila_segmentacion(),
    }

    if len(v):
        ctx["fuera_horario"] = float(((v["inicio"].dt.hour < 9) | (v["inicio"].dt.hour >= 18)
                                       | (v["inicio"].dt.weekday >= 5)).mean())
        ctx["noche"] = float(v["franja"].isin(["noche", "madrugada"]).mean())
        ctx["por_motivo"] = v["motivo"].value_counts()
        ctx["motivo_top"] = (C.MOTIVO_CORTO[v["motivo"].value_counts().index[0]],
                             float(v["motivo"].value_counts().iloc[0] / len(v)))
        ctx["cruzada"] = pd.crosstab(v["motivo"], v["franja"]).reindex(
            columns=[f for f, _, _ in FRANJAS], fill_value=0)
    return ctx


if __name__ == "__main__":  # pragma: no cover
    ctx = filas_para_html()
    print(f"Conversaciones 14 d: {ctx['n_conversaciones']:,}")
    if ctx["n_conversaciones"]:
        print(f"  fuera de lun–vie 9–18 h : {ctx['fuera_horario']:.0%}")
        print(f"  llega de noche          : {ctx['noche']:.0%}")
        print(f"  motivo más frecuente    : {ctx['motivo_top'][0]} ({ctx['motivo_top'][1]:.0%})")
    print("\nKPIs de la sesión de demo:")
    for k in ctx["kpis"]:
        print(f"  {k['nombre']:22} {k['formato']:5} {k['valor']}")
        valor = "—" if num is None or (den is not None and not den) else (
            f"{num:.0%}" if den is None else f"{num/den:.0%}")
        print(f"  {nombre:22} {valor:>6}  {detalle}")
    if not ctx["kpis"]:
        print("  (sin actividad todavía)")

    print("\nModelo:")
    for k, val in ctx["fila_ml"].items():
        print(f"  {k:18} {val:.4f}" if isinstance(val, float) else f"  {k:18} {val}")

    print("\nEmbudo:")
    for k, val in ctx["embudo"].items():
        print(f"  {k:20} {val:.1%}" if k.endswith("pct") and isinstance(val, float)
              else f"  {k:20} {val:,}" if isinstance(val, int) else f"  {k:20} {val}")
