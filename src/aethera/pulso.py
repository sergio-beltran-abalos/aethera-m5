"""
Aethera · Pulse.

Un check-in de 20 segundos. Tres decisiones de producto que conviene que sean
explícitas:

1. NO ES UN TEST. No calcula puntajes, no da niveles y no se guarda nada sin
   consentimiento. La ley 29733 (reglamento DS 016-2024-JUS) clasifica el dato
   de salud como sensible y exige consentimiento expreso, con finalidad.

2. Solo el estudiante ve su registro. Wellbeing nunca ve ánimos, notas ni
   conversaciones individuales: ve conteos agregados con tamaño mínimo de grupo.

3. Se puede borrar y exportar cuando sea. El derecho de supresión no puede
   depender de que alguien conteste un ticket.
"""
from __future__ import annotations

import json
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

from . import config as C, guardrails

MOODS = [
    {"id": "muy_bien", "emoji": "😄", "label": "Muy bien", "valor": 5, "color": "#3F9E7A"},
    {"id": "bien", "emoji": "🙂", "label": "Bien", "valor": 4, "color": "#8FC46B"},
    {"id": "regular", "emoji": "😐", "label": "Regular", "valor": 3, "color": "#E8B84B"},
    {"id": "desanimado", "emoji": "😔", "label": "Desanimado/a", "valor": 2, "color": "#E58A57"},
    {"id": "pesado", "emoji": "😣", "label": "Muy pesado", "valor": 1, "color": "#D26161"},
]
MOOD = {m["id"]: m for m in MOODS}
MOOD_POR_VALOR = {m["valor"]: m["id"] for m in MOODS}
TEMAS = ["Estudios", "Descanso", "Amistades", "Familia", "Trabajo", "Futuro", "Dinero", "Otro"]
DIAS_TRACK = C.DIAS_TRACK

FRASES_RESPALDO = {
    "muy_bien": ["Qué bueno leer eso. Guarda algo de hoy para recordarlo cuando lo necesites.",
                 "Días así también cuentan: date crédito por lo que estás sosteniendo."],
    "bien": ["Bien es un buen lugar para estar. Si algo cambia, aquí estaré.",
             "Gracias por registrarlo: notar cómo estás ya es cuidarte."],
    "regular": ["Un día regular también es válido. Si quieres, conversamos sobre lo que lo cuesta.",
                "No todos los días tienen que ser buenos. Si algo pesa, puedes contármelo."],
    "desanimado": ["Lamento que hoy pese. No tienes que resolverlo solo/a; si quieres, buscamos apoyo juntos.",
                   "Gracias por contarlo con honestidad. Puedes conversar con Ruta cuando quieras."],
    "pesado": ["Gracias por contarlo, se nota que hoy es difícil. Si quieres, conversa con Ruta "
               "y vemos qué apoyo calza con tu horario.",
               "Hoy está pesado y está bien decirlo. No estás solo/a: puedo ayudarte a encontrar "
               "con quién hablar."],
}

INSTR_FRASE = """
Eres Pulse, el registro de ánimo de Aethera (universidad ficticia). Escribe UNA sola frase
breve (máximo 22 palabras), cálida y en español neutro, para un estudiante que acaba de
registrar cómo se siente hoy.
- Si el ánimo es bajo, valida sin dramatizar y recuerda que puede conversar con Ruta.
- Si el ánimo es bueno, celebra con sencillez.
- Puedes aludir a los temas marcados, sin repetirlos todos.
- Sin diagnósticos, sin consejos médicos, sin clichés ("todo pasa por algo", "sé positivo"),
  sin emojis.
Devuelve solo la frase.
"""

TEXTO_CONSENTIMIENTO = ("Acepto que Pulse guarde mi registro de ánimo para mostrármelo. Es "
                         "opcional, solo yo lo veo, no condiciona ningún servicio y puedo "
                         "descargarlo o borrarlo cuando quiera (dato sensible, Ley 29733).")


def fecha_hoy() -> date:
    return date.fromisoformat(C.FECHA_DEMO)


def frase_para(mood_id: str, temas, nota: str) -> tuple[str, str]:
    from . import ia
    try:
        frase = ia.invocar(f"Ánimo: {MOOD[mood_id]['label']}. "
                           f"Temas: {', '.join(temas) or 'ninguno'}. "
                           f"Nota del estudiante: {nota or '(sin nota)'}",
                           INSTR_FRASE, max_tokens=80, temperatura=0.7)
        frase = frase.strip().strip('"').split("\n")[0]
        if guardrails.validar_salida(frase) or len(frase.split()) > 35:
            raise ia.LLMNoDisponible("Frase descartada por el guardrail de salida")
        return frase, "modelo"
    except ia.LLMNoDisponible:
        opciones = FRASES_RESPALDO[mood_id]
        return opciones[fecha_hoy().toordinal() % len(opciones)], "frase de respaldo"


def _registros_en(sesion, dias: int) -> list[dict]:
    fin = fecha_hoy()
    return sorted([e for e in sesion.mood_track
                   if 0 <= (fin - date.fromisoformat(e["fecha"])).days < dias],
                  key=lambda e: e["fecha"])


def resumen(sesion, dias: int = 7) -> dict:
    """Resumen del PROPIO registro. No se comparte con nadie más."""
    recientes = _registros_en(sesion, dias)
    valores = [e["valor"] for e in recientes]
    mes = [e["valor"] for e in _registros_en(sesion, DIAS_TRACK)]
    hoy = next((e for e in recientes if e["fecha"] == fecha_hoy().isoformat()), None)

    tendencia = None
    if len(valores) >= 4:
        reciente, previo = mean(valores[-3:]), mean(valores[:-3])
        tendencia = ("baja" if reciente < previo - 0.4
                     else "sube" if reciente > previo + 0.4 else "estable")
    pesados = sum(v <= 2 for v in valores)
    return {
        "hoy": ({"animo": MOOD[hoy["mood"]]["label"], "temas": hoy["temas"],
                 "nota": hoy["nota"]} if hoy else None),
        "dias_registrados_7d": len(valores),
        "promedio_7d": round(mean(valores), 1) if valores else None,
        "dias_pesados_7d": pesados,
        "patron_dias_pesados": pesados >= 3,
        "tendencia": tendencia,
        "dias_registrados_28d": len(mes),
        "promedio_28d": round(mean(mes), 1) if mes else None,
        "temas_frecuentes": [t for t, _ in Counter(
            t for e in recientes for t in e["temas"]).most_common(3)],
    }


def registrar(sesion, mood_id: str, temas=(), nota: str = "") -> dict:
    """Guarda el registro del día (solo con consentimiento) y devuelve una frase breve."""
    if not sesion.consentimiento_pulse:
        return {"error": "Para guardar tu registro, primero acepta el aviso de privacidad de Pulse."}

    nota = (nota or "").strip()[:200]
    entrada = {"fecha": fecha_hoy().isoformat(), "mood": mood_id, "valor": MOOD[mood_id]["valor"],
               "temas": list(temas), "nota": nota, "ejemplo": False}
    sesion.mood_track = [e for e in sesion.mood_track if e["fecha"] != entrada["fecha"]] + [entrada]
    sesion.registrar("checkin_iniciado", mood=mood_id)

    # Un check-in también puede contener una señal de riesgo: se evalúa igual.
    control = (guardrails.evaluar_entrada(nota, sesion.perfil) if nota
               else {"tipo": "permitido"})
    if control["tipo"] == "crisis":
        sesion.registrar("guardrail_crisis", origen="pulse")
        return {"entrada": entrada, "frase": guardrails.mensaje_crisis(sesion.perfil),
                "metodo": "guardrail de crisis", "crisis": True, "sugerir_chat": True,
                "resumen": resumen(sesion)}

    frase, metodo = frase_para(mood_id, temas, nota)
    r = resumen(sesion)
    return {"entrada": entrada, "frase": frase, "metodo": metodo, "crisis": False,
            "sugerir_chat": entrada["valor"] <= 3 or r["patron_dias_pesados"], "resumen": r}


def borrar(sesion) -> None:
    """Derecho de supresión: borra el registro y su uso en el chat."""
    sesion.mood_track = []
    sesion.contexto_pulse = None
    sesion.registrar("registro_borrado")


def exportar(sesion) -> str:
    """Derecho de acceso y portabilidad: el estudiante descarga su registro."""
    ruta = Path(f"mi_registro_pulse_{sesion.perfil['student_id']}.json")
    ruta.write_text(json.dumps({"estudiante": sesion.perfil["student_id"],
                                "generado": C.FECHA_DEMO,
                                "registros": sesion.mood_track},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    sesion.registrar("registro_exportado")
    return str(ruta)


def abrir_chat(sesion) -> str:
    """El estudiante elige conversar: Ruta usa su registro, con su permiso."""
    sesion.contexto_pulse = resumen(sesion)
    sesion.registrar("pulse_a_chat")
    resultados = {"registro_pulse": sesion.contexto_pulse}
    respuesta, metodo = ia_redactar_desde_pulse(sesion, resultados)

    if guardrails.validar_salida(respuesta):
        respuesta = plantilla_desde_pulse(resultados, sesion)
        metodo = "plantilla de respaldo"

    sesion.historial.append({"rol": "ruta", "texto": respuesta})
    sesion.trazas.append({"turno": 0, "mensaje": "(inicio desde Pulse)",
                          "guardrail_entrada": "permitido", "accion": "abrir_desde_pulse",
                          "herramientas": ["resumen_pulse"], "resultados": resultados,
                          "redaccion": metodo, "guardrail_salida": "ok", "segundos": 0})
    sesion.presentado = True
    return respuesta


def ia_redactar_desde_pulse(sesion, resultados):
    from . import agente, ia
    return ia.redactar("(El estudiante tocó «Hablar con Ruta» tras registrar su día en Pulse)",
                       "abrir_desde_pulse", resultados, sesion)


def plantilla_desde_pulse(resultados, sesion) -> str:
    from .agente import plantilla
    return plantilla("abrir_desde_pulse", resultados, sesion)


# ── Historial sintético de ejemplo (solo para la demo) ─────────────────────
TENDENCIA_EJEMPLO = {
    "A": (3.8, 1.8, ["Estudios", "Descanso", "Familia"]),
    "B": (3.4, 2.2, ["Amistades", "Trabajo", "Descanso"]),
    "C": (4.0, 1.9, ["Estudios", "Trabajo", "Futuro"]),
}


def historial_ejemplo(nombre_perfil: str, dias: int = DIAS_TRACK - 1) -> list[dict]:
    inicio, fin, temas = TENDENCIA_EJEMPLO.get(nombre_perfil[:1].upper(), TENDENCIA_EJEMPLO["A"])
    rng = random.Random(nombre_perfil)
    fin_fecha = fecha_hoy()
    registros = []
    for i in range(dias):
        d = fin_fecha - timedelta(days=dias - i)
        if rng.random() < 0.15:        # hay días sin registro, como en la vida real
            continue
        v = int(min(5, max(1, round(inicio + (fin - inicio) * i / max(1, dias - 1)
                                      + rng.gauss(0, 0.6)))))
        registros.append({"fecha": d.isoformat(), "mood": MOOD_POR_VALOR[v], "valor": v,
                           "temas": rng.sample(temas, k=1 if v >= 3 else 2),
                           "nota": "", "ejemplo": True})
    return registros


if __name__ == "__main__":  # pragma: no cover
    from .agente import Sesion
    from .segmentos import perfiles_demo
    nombre = "B · Nocturno, trabaja tiempo completo"
    s = Sesion(perfiles_demo()[nombre], nombre)
    print("Sin consentimiento:", registrar(s, "pesado")["error"])
    s.consentimiento_pulse = True
    s.mood_track = historial_ejemplo(nombre)
    r = registrar(s, "pesado", ["Estudios", "Descanso"])
    print("Frase:", r["frase"], "|", r["metodo"])
    print("Resumen:", json.dumps(r["resumen"], ensure_ascii=False))
