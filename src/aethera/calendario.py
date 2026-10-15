"""
Aethera · calendario académico (D7).

Cruza el calendario real del Data Pack con la necesidad del estudiante, y solo
menciona el evento si de verdad es pertinente. Mencionar el calendario cuando no
aporta es ruido; y aquí cada estudiante ve lo mismo: no se personaliza por perfil.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from . import config as C
from . import datos

NO_PERTINENTE = {"period_start", "period_end"}

# Qué evento vale la pena mencionar según la necesidad declarada.
EVENTOS_RELEVANTES = {
    "academic_pressure": ["evaluation_week", "wellbeing_activity"],
    "sleep_and_routine": ["evaluation_week", "wellbeing_activity"],
    "social_support": ["university_activity", "wellbeing_activity"],
    "preventive_guidance": ["wellbeing_activity", "university_activity"],
    "career_concern": ["university_activity"],
}

ICONO_EVENTO = {"evaluation_week": "📚", "wellbeing_activity": "🌿",
                "university_activity": "🤝"}

TITULO_LIMPIO = {"period_start", "period_end"}


def _d7():
    return datos.cargar()["D7"]


def fecha_larga(d) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.day} de {C.MESES_ES[d.month - 1]}"


def titulo_limpio(titulo: str) -> str:
    """'Evaluaciones finales del período 1' → 'evaluaciones finales del período 1'"""
    import re
    t = re.sub(r"\s\d+(-\d+)?$", "", str(titulo))
    return t[0].lower() + t[1:] if t else t


def consultar(fecha_referencia: str | None = None, dias: int = C.HORIZONTE_DIAS,
              motivo: str | None = None, institucion: str | None = None) -> dict:
    inst = institucion or C.INSTITUCION
    ref = pd.Timestamp(fecha_referencia or C.FECHA_DEMO)
    fin = ref + pd.Timedelta(days=dias - 1)

    ev = _d7()
    ev = ev[(ev["start_date"] <= fin) & (ev["end_date"] >= ref)
            & ev["institution_id"].isin(["ALL", inst])
            & ~ev["event_type"].isin(NO_PERTINENTE)]

    eventos = [{
        "titulo": e["title"], "tipo": e["event_type"],
        "desde": e["start_date"].date().isoformat(),
        "hasta": e["end_date"].date().isoformat(),
        "en_curso": bool(e["start_date"] <= ref),
        "intensidad": int(e["evaluation_intensity"]),
    } for _, e in ev.sort_values("start_date").iterrows()]

    relevante = next((e for e in eventos
                      if e["tipo"] in EVENTOS_RELEVANTES.get(motivo or "", [])), None)

    return {
        "fecha_referencia": ref.date().isoformat(),
        "eventos": eventos,
        "en_semana_evaluaciones": any(e["tipo"] == "evaluation_week" and e["en_curso"]
                                      for e in eventos),
        "evento_relevante": relevante,
    }


def frase_evento(e: dict | None) -> str:
    """Una frase corta y pertinente, o vacío si no hay nada que decir."""
    if not e:
        return ""
    d0, d1 = date.fromisoformat(e["desde"]), date.fromisoformat(e["hasta"])
    rango = (f"el {fecha_larga(d0)}" if d0 == d1
             else f"del {fecha_larga(d0)} al {fecha_larga(d1)}")
    nombre = titulo_limpio(e["titulo"])

    if e["tipo"] == "evaluation_week":
        inicio = (f"Esta semana son las {nombre}" if e["en_curso"]
                  else f"Las {nombre} son {rango}")
        return inicio + "; en la cita puedes armar un plan para esos días."
    if e["tipo"] == "university_activity":
        return f"{rango.capitalize()} hay un {nombre} en la universidad: puede ser buena ocasión para conocer gente."
    if e["tipo"] == "wellbeing_activity":
        return f"{rango.capitalize()} es la {nombre}, con actividades abiertas para todos."
    return ""


def aviso_general(fecha: str | None = None, institucion: str | None = None) -> dict | None:
    """
    Aviso para toda la comunidad, idéntico para todos.

    Deliberadamente NO se segmenta por perfil: un aviso distinto según la
    ansiedad de cada quien es exactamente el tipo de señal que este proyecto
    no quiere producir.
    """
    inst = institucion or C.INSTITUCION
    ref = pd.Timestamp(fecha or C.FECHA_DEMO)
    ev = _d7()
    ev = ev[(ev["end_date"] >= ref) & (ev["start_date"] <= ref + pd.Timedelta(days=10))
            & ev["institution_id"].isin(["ALL", inst])
            & ev["event_type"].isin(["evaluation_week", "wellbeing_activity",
                                     "university_activity"])]
    if ev.empty:
        return None

    e = ev.sort_values("start_date").iloc[0]
    evento = {"titulo": e["title"], "tipo": e["event_type"],
              "desde": e["start_date"].date().isoformat(),
              "hasta": e["end_date"].date().isoformat(),
              "en_curso": bool(e["start_date"] <= ref)}

    extra = {
        "evaluation_week": " Si necesitas organizarte, Ruta puede ayudarte a encontrar un espacio de apoyo.",
        "wellbeing_activity": "",
        "university_activity": "",
    }[evento["tipo"]]

    return {
        "icono": ICONO_EVENTO[evento["tipo"]],
        "texto": frase_evento(evento).split(";")[0].rstrip(".") + "." + extra,
    }


def fechas_validas() -> set[str]:
    d7 = _d7()
    return set(d7["start_date"].dt.date.astype(str)) | set(d7["end_date"].dt.date.astype(str))


if __name__ == "__main__":  # pragma: no cover
    c = consultar()
    print(f"Referencia {c['fecha_referencia']} · {len(c['eventos'])} eventos · "
          f"en semana de evaluaciones: {c['en_semana_evaluaciones']}")
    for e in c["eventos"]:
        print(f"  [{e['tipo']:20}] {e['titulo']} ({e['desde']} → {e['hasta']})")
    for motivo in C.MOTIVOS:
        rel = consultar(motivo=motivo)["evento_relevante"]
        print(f"\n{motivo:20} → {frase_evento(rel) or '(nada pertinente)'}")
    print("\nAviso:", aviso_general())
