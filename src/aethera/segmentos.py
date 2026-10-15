"""
Aethera · segmentación y perfiles de demostración.

Reconstruye M5 exactamente como en el Entregable 1:

    D1 → anxiety_band ∈ {moderate, high}
       → previous_support_use == "never"          (≈68 % de ese grupo)
       → ≥2 fricciones primarias                 (segmento prioritario)

Las cifras deben coincidir con el E1; si no coinciden, algo se rompió.
"""
from __future__ import annotations

import pandas as pd

from . import config as C
from . import datos

COLUMNAS_PERFIL = [
    "student_id", "district_id", "country_context", "study_mode", "employment_status",
    "work_hours_week", "services_awareness", "support_network", "academic_stage",
]

FRICCIONES = {
    "f_desconoce": ("services_awareness", lambda s: s.eq("unaware")),
    "f_sin_red": ("support_network", lambda s: s.isin(["limited", "none"])),
    "f_nocturno": ("study_mode", lambda s: s.eq("evening")),
}

# Tres arquetipos del segmento prioritario. Cada uno es una fila real de D1,
# escogida por ser la mediana de su categoría (no la primera por orden de id),
# para que la demo no dependa de un caso arbitrario.
PERFILES_DEMO = {
    "A · Diurno, sin red de apoyo":
        dict(study_mode="day", employment_status="not_working", support_network="none"),
    "B · Nocturno, trabaja tiempo completo":
        dict(study_mode="evening", employment_status="full_time", support_network="limited"),
    "C · Nocturno, trabaja medio tiempo":
        dict(study_mode="evening", employment_status="part_time"),
}


class Segmentacion:
    def __init__(self, institucion: str | None = None):
        self.institucion = institucion or C.INSTITUCION
        self.nova = self._construir()

    def _construir(self) -> pd.DataFrame:
        d1 = datos.cargar()["D1"]
        base = d1[d1["institution_id"] == self.institucion].copy()
        for nombre, (columna, fn) in FRICCIONES.items():
            base[nombre] = fn(base[columna])
        base["n_fricciones"] = base[list(FRICCIONES)].sum(axis=1)
        base["es_mod_alta"] = base["anxiety_band"].isin(["moderate", "high"])
        base["es_m5"] = base["es_mod_alta"] & base["previous_support_use"].eq("never")
        return base

    @property
    def embudo(self) -> dict:
        """El funnel completo, para mostrarlo en el documento y en la app."""
        n = len(self.nova)
        mod = int(self.nova["es_mod_alta"].sum())
        m5 = int(self.nova["es_m5"].sum())
        seg = int((self.nova["es_m5"] & (self.nova["n_fricciones"] >= 2)).sum())
        return {
            "institucion": self.institucion,
            "encuestados": n,
            "moderada_alta": mod,
            "m5": m5,
            "m5_pct": m5 / mod if mod else 0.0,
            "prioritario": seg,
            "prioritario_pct_m5": seg / m5 if m5 else 0.0,
            "prioritario_pct_mod": seg / mod if mod else 0.0,
        }

    @property
    def segmento(self) -> pd.DataFrame:
        return self.nova[self.nova["es_m5"] & (self.nova["n_fricciones"] >= 2)]

    def _mediana(self, **cond) -> dict:
        """Perfil representativo: la fila mediana dentro de los filtros dados."""
        df = self.segmento
        for col, val in cond.items():
            df = df[df[col] == val]
        if df.empty:
            # Relajamos condiciones una por una antes de rendirnos.
            for col in list(cond)[::-1]:
                if df.empty:
                    df = self.segmento[self.segmento[col] == cond[col]]
                else:
                    df = df[df[col] == cond[col]]
        if df.empty:
            raise ValueError(f"No hay estudiantes con {cond}")

        clave = "work_hours_week" if "work_hours_week" in df else COLUMNAS_PERFIL[1]
        objetivo = df[clave].median()
        fila = df.iloc[(df[clave] - objetivo).abs().argsort().iloc[0]]
        return {c: (fila[c].item() if hasattr(fila[c], "item") else fila[c])
                for c in COLUMNAS_PERFIL}

    def perfiles(self) -> dict[str, dict]:
        return {nombre: self._mediana(**cond) for nombre, cond in PERFILES_DEMO.items()}

    def tarjetas(self) -> dict[str, dict]:
        """Perfiles + su horario, para pintar en la UI."""
        from . import horarios
        out = {}
        for nombre, p in self.perfiles().items():
            p = dict(p)
            p["nombre"] = nombre
            p["horario"] = horarios.describir_horario(p)
            p["fronteras"] = horarios.resumen_fronteras(p)
            p["creditos"] = datos.d3_carga(p["student_id"])
            out[nombre] = p
        return out


_SEG: Segmentacion | None = None


def segmentacion() -> Segmentacion:
    global _SEG
    if _SEG is None:
        _SEG = Segmentacion()
    return _SEG


def perfiles_demo() -> dict[str, dict]:
    return segmentacion().perfiles()


def tarjetas_demo() -> dict[str, dict]:
    return segmentacion().tarjetas()


if __name__ == "__main__":  # pragma: no cover
    seg = segmentacion()
    print("== Embudo M5 ==")
    for k, v in seg.embudo.items():
        if isinstance(v, float):
            print(f"  {k:20} {v:.1%}" if k.endswith("pct") else f"  {k:20} {v:.3f}")
        elif isinstance(v, str):
            print(f"  {k:20} {v}")
        else:
            print(f"  {k:20} {v:,}")
    print("\n== Perfiles ==")
    for nombre, p in seg.tarjetas().items():
        print(f"  {nombre}")
        print(f"    {p['student_id']} · {p['district_id']} · {p['study_mode']}"
              f" · {p['employment_status']} · {p['creditos']} créditos")
        print(f"    {p['horario']} | libre: {p['fronteras']['ventanas_libres']}")
