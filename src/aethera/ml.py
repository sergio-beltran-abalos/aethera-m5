"""
Aethera · modelo de asistencia, con sus límites declarados.

Responde una sola pregunta: **de estos dos turnos, ¿cuál es más probable que el
estudiante vaya?** No clasifica necesidad, no detecta riesgo y no decide a quién
ayudar. Solo ordena la lista de citas que Ruta puede ofrecer.

Dos decisiones metodológicas que conviene conocer
=================================================

1. `espera_dias` es la espera REAL del evento histórico (D2: `wait_days`), no el
   promedio del servicio. La varianza de `wait_days` es 95% intra-servicio y
   solo 5% entre servicios: colapsarla al promedio del servicio destruye la
   señal y convierte la espera en un simple identificador del servicio.

2. El modelo se evalúa también FUERA de su zona cómoda. D2 tiene esperas de 4 a
   120 días, con mediana 39. La demo de Ruta ofrece turnos a 1–14 días, que es
   el 3.4% del histórico. En esa franja el modelo **no discrimina bien**
   (AUC 0.44, es decir, bajo el azar). No se esconde: se mide, se expone y se
   marca con un indicador de confianza que la app muestra al estudiante y al
   panel de trazabilidad. Es un límite conocido del prototipo, no un defecto
   silencioso.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config as C
from . import datos

VARS_CAT = ["contact_channel", "service_type", "reason_code"]
VARS_NUM = ["espera_dias"]
SEMILLA = C.SEMILLA

# Franja en la que la demo ofrece turnos. Es el parámetro que define la
# "zona cómoda" vs. "zona extrapolation" del modelo.
FRANJA_DEMO_MAX = 14


@dataclass
class ModeloAsistencia:
    pipeline: Pipeline
    metricas: dict = field(default_factory=dict)
    importancia: pd.DataFrame | None = None
    comparativa: pd.DataFrame | None = None
    _esperas: np.ndarray | None = None

    # ── Densidad histórica de esperas, para el indicador de confianza ────────
    def _historico_esperas(self) -> np.ndarray:
        if self._esperas is None:
            self._esperas = datos.cargar()["D2"]["wait_days"].values.astype(float)
        return self._esperas

    def confianza(self, espera_dias: float) -> tuple[float, str]:
        """
        Qué tan respaldada está la predicción.

        Se mide cuánto histórico hay alrededor de esa espera. Si casi ningún
        evento histórico se le parece, el modelo está extrapolando y conviene
        decirlo en lugar de mostrar un número con falsa precisión.
        """
        valores = self._historico_esperas()
        if len(valores) == 0:
            return 0.0, "sin histórico"

        # Ventana relativa: ±50 % de la espera, con un mínimo de ±7 días.
        holgura = max(7.0, espera_dias * 0.5)
        ventana = ((valores >= espera_dias - holgura)
                   & (valores <= espera_dias + holgura)).mean()

        confianza = float(min(1.0, ventana / 0.20))
        if confianza >= 0.6:
            return confianza, "dentro del rango observado"
        if confianza >= 0.25:
            return confianza, "con poca evidencia histórica"
        return confianza, "extrapolación: casi sin datos para esta espera"

    def predecir(self, filas: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict_proba(filas)[:, 1]


def _preprocesar() -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), VARS_CAT),
        ("num", StandardScaler(), VARS_NUM),
    ])


def entrenar() -> ModeloAsistencia:
    d = datos.cargar()
    d2 = d["D2"]

    X = d2[VARS_CAT].copy()
    X["espera_dias"] = d2["wait_days"].astype(float)      # espera real del evento
    y = d2["attended"].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=SEMILLA,
                                              stratify=y)

    candidatos = {
        "Regresión logística": LogisticRegression(max_iter=1000),
        "Gradient boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=SEMILLA),
    }

    filas, pipelines = [], {}
    for nombre, clf in candidatos.items():
        pipe = Pipeline([("prep", _preprocesar()), ("clf", clf)])
        pipe.fit(X_tr, y_tr)
        p = pipe.predict_proba(X_te)[:, 1]
        filas.append({"modelo": nombre,
                      "AUC": roc_auc_score(y_te, p),
                      "Brier": brier_score_loss(y_te, p),
                      "lift_vs_azar": roc_auc_score(y_te, p) - 0.5})
        pipelines[nombre] = pipe

    comparativa = (pd.DataFrame(filas).sort_values("AUC", ascending=False)
                   .round(4).reset_index(drop=True))
    mejor = comparativa.iloc[0]["modelo"]
    pipeline = pipelines[mejor]
    p_te = pipeline.predict_proba(X_te)[:, 1]

    # ── Métricas honestas: global, zona histórica y zona de la demo ─────────
    en_demo = X_te["espera_dias"] <= FRANJA_DEMO_MAX
    metricas = {
        "modelo_elegido": mejor,
        "auc": float(roc_auc_score(y_te, p_te)),
        "brier": float(brier_score_loss(y_te, p_te)),
        "tasa_base": float(y.mean()),
        "n_eventos": int(len(d2)),
        "espera_min": int(d2["wait_days"].min()),
        "espera_max": int(d2["wait_days"].max()),
        "espera_mediana": float(d2["wait_days"].median()),
        "espera_media": round(float(d2["wait_days"].mean()), 1),
        "auc_zona_demo": float(roc_auc_score(y_te[en_demo], p_te[en_demo])) if en_demo.sum() > 20 else None,
        "n_zona_demo": int(en_demo.sum()),
        "cobertura_demo": float((d2["wait_days"] <= FRANJA_DEMO_MAX).mean()),
    }

    perm = permutation_importance(pipeline, X_te, y_te, n_repeats=10, random_state=SEMILLA,
                                  scoring="roc_auc")
    importancia = pd.DataFrame({
        "feature": VARS_CAT + VARS_NUM,
        "importancia": perm.importances_mean,
    }).sort_values("importancia", ascending=False).round(4).reset_index(drop=True)

    return ModeloAsistencia(pipeline=pipeline, metricas=metricas,
                            importancia=importancia, comparativa=comparativa)


_MODELO: ModeloAsistencia | None = None


def modelo() -> ModeloAsistencia:
    global _MODELO
    if _MODELO is None:
        _MODELO = entrenar()
    return _MODELO


def _clip(espera: float) -> float:
    d = datos.cargar()
    return float(np.clip(espera, d["espera_min"], d["espera_max"]))


def p_asistencia(canal: str, tipo: str, motivo: str, espera_dias: float) -> float:
    """Probabilidad de asistencia de un turno."""
    m = modelo()
    fila = pd.DataFrame([{"contact_channel": canal, "service_type": tipo,
                          "reason_code": motivo, "espera_dias": _clip(espera_dias)}])
    return float(m.predecir(fila)[0])


def p_asistencia_lote(agenda: pd.DataFrame, motivo: str) -> np.ndarray:
    """Vectorizada: evita llamar al pipeline fila por fila."""
    m = modelo()
    X = pd.DataFrame({
        "contact_channel": agenda["canal"].values,
        "service_type": agenda["service_type"].values,
        "reason_code": motivo,
        "espera_dias": np.clip(agenda["espera_dias"].astype(float).values,
                               _clip(0), _clip(10_000)),
    })
    return m.predecir(X)


def fila_inferencia(canal: str, tipo: str, motivo: str, espera_dias: float) -> pd.DataFrame:
    """Feature de un turno en el momento de inferencia (expuesto para tests)."""
    return pd.DataFrame([{"contact_channel": canal, "service_type": tipo,
                          "reason_code": motivo, "espera_dias": _clip(espera_dias)}])


# ─────────────────────────────────────────────────────────────────────────────
# Clasificador de necesidad (texto → motivo), entrenado sobre D5
# ─────────────────────────────────────────────────────────────────────────────
# El Data Pack entrega D5 con 2.500 conversaciones YA ETIQUETADAS por motivo.
# La versión anterior del prototipo usaba una lista de palabras escritas a mano,
# que acertaba 27 %: peor que predecir siempre la clase mayoritaria. Con D5 se
# entrena un clasificador real que sí generaliza, y el modelo de lenguaje queda
# como la opción de máxima calidad cuando hay clave disponible.
_CLASIFICADOR = None


def entrenar_clasificador_texto():
    """TF-IDF + regresión logística sobre el motivo declarado en D5."""
    global _CLASIFICADOR
    if _CLASIFICADOR is not None:
        return _CLASIFICADOR

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import Pipeline

    d5 = datos.cargar()["D5"]
    X = d5["texto_inicial"]
    y = d5["motivo"]

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=2000, C=4.0)),
    ])
    acc_cv = float(cross_val_score(pipe, X, y, cv=5).mean())
    pipe.fit(X, y)

    _CLASIFICADOR = {
        "pipeline": pipe,
        "accuracy_cv": acc_cv,
        "linea_base": float(y.value_counts(normalize=True).max()),
        "n": int(len(y)),
        "clases": sorted(y.unique()),
    }
    return _CLASIFICADOR


def clasificar_texto(motivo_texto: str) -> tuple[str, float]:
    """Motivo más probable y su confianza. Es el respaldo sin modelo de lenguaje."""
    c = entrenar_clasificador_texto()
    proba = c["pipeline"].predict_proba([motivo_texto])[0]
    idx = int(proba.argmax())
    return c["pipeline"].classes_[idx], float(proba[idx])


if __name__ == "__main__":  # pragma: no cover
    m = modelo()
    print("== Comparativa de modelos ==")
    print(m.comparativa.to_string(index=False))
    print("\n== Métricas ==")
    for k, v in m.metricas.items():
        print(f"  {k:18} {v}")

    print("\n== Importancia de features (AUC) ==")
    print(m.importancia.to_string(index=False))

    print("\n== Efecto del canal (counseling, academic_pressure, 42 d) ==")
    for c in ["digital", "phone", "in_person"]:
        print(f"  {c:10} {p_asistencia(c, 'counseling', 'academic_pressure', 42):.3f}")

    print("\n== Efecto de la espera (digital, counseling, academic_pressure) ==")
    for e in [4, 14, 30, 42, 70, 120]:
        conf, nota = m.confianza(e)
        print(f"  {e:3} días  P={p_asistencia('digital', 'counseling', 'academic_pressure', e):.3f}"
              f"  confianza={conf:.2f}  ({nota})")

    print("\n== Clasificador de necesidad (D5) ==")
    c = entrenar_clasificador_texto()
    print(f"  Accuracy (CV 5 folds)  {c['accuracy_cv']:.1%}")
    print(f"  Línea base             {c['linea_base']:.1%}")
    print(f"  n conversaciones       {c['n']:,}")
    for texto in ["Tengo tres parciales y no sé por dónde empezar",
                  "Desde que me mudé no tengo con quién hablar",
                  "Termino la carrera y no sé cómo conseguir prácticas",
                  "Duermo 4 horas y ando agotado todo el día",
                  "¿Qué apoyos tiene la universidad?"]:
        motivo, conf = clasificar_texto(texto)
        print(f"    {texto[:44]:46} → {motivo:20} {conf:.2f}")
