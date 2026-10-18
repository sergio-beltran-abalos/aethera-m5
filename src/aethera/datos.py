"""
Aethera · capa de datos.

Carga el Data Pack, valida que estén los archivos obligatorios y deja los
DataFrames listos para el resto del sistema. Toda la lógica de datos vive aquí:
el resto de módulos solo consume estas estructuras.
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import pandas as pd

from . import config as C

VARS_CAT = ["contact_channel", "service_type", "reason_code"]
VARS_NUM = ["wait_days"]


def _a_minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _parsear_horario(texto: str) -> tuple[set[int], int, int]:
    """'Mon-Sat 12:00-20:00' → ({0..5}, 720, 1200)"""
    dias, horas = texto.split()
    d0, d1 = dias.split("-")
    h0, h1 = horas.split("-")
    return (set(range(C.DIAS_INGLES[d0], C.DIAS_INGLES[d1] + 1)),
            _a_minutos(h0), _a_minutos(h1))


class FaltanDatasets(RuntimeError):
    """Se lanza cuando el Data Pack no está completo en `data/`."""


def _ruta(codigo: str):
    return C.DATA_DIR / C.ARCHIVOS_DATAPACK[codigo]


def _verificar() -> None:
    faltan = [str(_ruta(c)) for c in C.OBLIGATORIOS if not _ruta(c).exists()]
    if faltan:
        raise FaltanDatasets(
            "Faltan archivos del Data Pack en data/:\n  · "
            + "\n  · ".join(faltan)
            + "\nCopia ahí los 7 archivos (D1–D7). Ver data/LEEME.txt."
        )


@lru_cache(maxsize=1)
def cargar() -> dict:
    """Carga y prepara todo el Data Pack. Se memoiza: solo corre una vez."""
    _verificar()

    d1 = pd.read_csv(_ruta("D1"), parse_dates=["survey_date"])
    d2 = pd.read_csv(_ruta("D2"), parse_dates=["request_date", "appointment_date"])
    d7 = pd.read_csv(_ruta("D7"), parse_dates=["start_date", "end_date"])

    with open(_ruta("D6"), encoding="utf-8") as f:
        geo = json.load(f)
    # Las coordenadas del GeoJSON se mantienen: permiten estimar tiempo de traslado real.
    d6 = pd.DataFrame([
        {**feat["properties"], "lon": feat["geometry"]["coordinates"][0],
         "lat": feat["geometry"]["coordinates"][1]}
        for feat in geo["features"]
    ])
    # "Mon-Sat 12:00-20:00" → días {0..5}, abre 720, cierra 1200
    d6[["dias", "abre", "cierra"]] = d6["schedule"].apply(
        lambda s: pd.Series(_parsear_horario(s)))

    with open(_ruta("D4"), encoding="utf-8") as f:
        d4 = pd.DataFrame(json.load(f))
    with open(_ruta("D5"), encoding="utf-8") as f:
        d5 = pd.DataFrame(json.load(f))

    # D3 es opcional en el sentido de arranque, pero se carga: aporta la carga
    # académica que se usa para calibrar el bloque de clases (ver horarios.py).
    ruta_d3 = _ruta("D3")
    d3 = pd.read_csv(ruta_d3) if ruta_d3.exists() else pd.DataFrame(columns=["student_id"])

    # ── D2: normalización y enriquecido ──────────────────────────────────────
    d2["attended"] = d2["attended"].astype(str).str.strip().str.lower().isin(
        ["true", "1", "yes", "si", "sí"])
    d2 = d2.merge(d6[["service_id", "service_type"]], on="service_id", how="left")

    # ── Servicios: catálogo + evidencia histórica de D2 ─────────────────────
    historico = d2.groupby("service_id").agg(
        solicitudes_d2=("support_event_id", "count"),
        espera_media_dias=("wait_days", "mean"),
        espera_p25=("wait_days", lambda s: float(np.percentile(s, 25))),
        asistencia_historica=("attended", "mean"),
    ).round(3).reset_index()
    servicios = d6.merge(historico, on="service_id", how="left")
    servicios["espera_media_dias"] = servicios["espera_media_dias"].fillna(0).round(1)

    # ── Mapa motivo → tipo de servicio, aprendido de D2 ──────────────────────
    cruce = pd.crosstab(d2["reason_code"], d2["service_type"])
    mapa_motivo_servicio = cruce.idxmax(axis=1).to_dict()

    # ── D5: conversaciones de la línea actual ────────────────────────────────
    d5["texto_inicial"] = d5["messages"].map(lambda m: m[0]["text"])
    d5["modalidad"] = d5["messages"].map(
        lambda m: "evening" if any("modalidad evening" in x["text"] for x in m) else "day")
    d5["inicio"] = pd.to_datetime(d5["started_at"])
    # D5 y D2 nombran distinto este motivo; se unifican para poder compararlos.
    d5["motivo"] = d5["motive"].replace({"service_navigation": "preventive_guidance"})
    d5 = d5.merge(
        servicios[["service_id", "service_type", "schedule"]]
        .rename(columns={"service_id": "referral", "service_type": "tipo_derivado",
                         "schedule": "horario_derivado"}),
        on="referral", how="left")
    d5["tipo_esperado"] = d5["motivo"].map(mapa_motivo_servicio)

    # ── D3: carga académica por estudiante (último período conocido) ─────────
    if len(d3):
        d3_ordenado = d3.sort_values(["student_id", "period_id"])
        carga = d3_ordenado.groupby("student_id").tail(1).set_index("student_id")
    else:
        carga = pd.DataFrame()

    return {
        "D1": d1, "D2": d2, "D3": d3, "D4": d4, "D5": d5, "D6": d6, "D7": d7,
        "servicios": servicios,
        "mapa_motivo_servicio": mapa_motivo_servicio,
        "carga_d3": carga,
        "espera_min": int(d2["wait_days"].min()),
        "espera_max": int(d2["wait_days"].max()),
    }


def servicios() -> pd.DataFrame:
    return cargar()["servicios"]


def mapa_motivo_servicio() -> dict:
    return cargar()["mapa_motivo_servicio"]


def d2() -> pd.DataFrame:
    return cargar()["D2"]


def d3_carga(student_id: str) -> float | None:
    """Créditos del último período registrado en D3 para un estudiante."""
    carga = cargar()["carga_d3"]
    if carga.empty or student_id not in carga.index:
        return None
    valor = carga.loc[student_id, "credit_load"]
    return float(valor) if pd.notna(valor) else None


def resumen() -> dict:
    d = cargar()
    return {
        "D1": len(d["D1"]), "D2": len(d["D2"]), "D3": len(d["D3"]),
        "D4": len(d["D4"]), "D5": len(d["D5"]), "D6": len(d["D6"]), "D7": len(d["D7"]),
        "espera_min": d["espera_min"], "espera_max": d["espera_max"],
        "espera_media": round(float(d["D2"]["wait_days"].mean()), 1),
    }


if __name__ == "__main__":  # pragma: no cover - inspección manual
    r = resumen()
    for k, v in r.items():
        print(f"{k:12} {v}")
