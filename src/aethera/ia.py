"""
Aethera · capa de IA.

Principio de diseño: **el modelo nunca decide datos, solo decisiones y redacción.**

- El CLASIFICADOR elige un motivo de una taxonomía cerrada.
- El PLANIFICADOR elige una acción y extrae preferencias.
- El REDACTOR formula la respuesta a partir de RESULTADOS ya calculados.

Cada uno tiene un respaldo de reglas que corre si no hay clave, si la API falla
o si el modelo devuelve algo que no parsea. La app nunca se cae por falta de
internet: degrada a un asistente de plantillas, que es menos bueno pero honesto.
"""
from __future__ import annotations

import json
import os
import re
import time

from . import config as C
from .horarios import normalizar

LLAMADAS = {"ok": 0, "fallidas": 0, "proveedor": C.PROVEEDOR, "modelo": C.MODELO}


class LLMNoDisponible(Exception):
    """No hay modelo utilizable: se activan los respaldos de reglas."""


# ─────────────────────────────────────────────────────────────────────────────
# Transporte
# ─────────────────────────────────────────────────────────────────────────────
def obtener_clave() -> str | None:
    valor = os.getenv(C.clave_api())
    if valor:
        return valor
    try:  # Colab
        from google.colab import userdata
        return userdata.get(C.clave_api())
    except Exception:
        return None


def _gemini(mensaje: str, instr: str, max_tokens: int, temperatura: float, json_mode: bool):
    from google import genai
    from google.genai import types
    from google.genai.errors import ServerError

    clave = obtener_clave()
    if not clave:
        raise LLMNoDisponible(f"Falta {C.clave_api()} en el entorno.")
    cliente = genai.Client(api_key=clave)
    config = types.GenerateContentConfig(
        system_instruction=instr, temperature=temperatura, max_output_tokens=max_tokens,
        response_mime_type="application/json" if json_mode else "text/plain")

    for intento, espera in enumerate([2, 4, 8], start=1):
        try:
            r = cliente.models.generate_content(model=C.MODELO, contents=mensaje, config=config)
            texto = (r.text or "").strip()
            if not texto:
                raise LLMNoDisponible("El modelo respondió vacío.")
            return texto
        except ServerError:
            if intento == 3:
                raise
            time.sleep(espera)


def _openai_compatible(mensaje: str, instr: str, max_tokens: int, temperatura: float,
                       _json: bool):
    from openai import OpenAI
    clave = obtener_clave()
    if not clave:
        raise LLMNoDisponible(f"Falta {C.clave_api()} en el entorno.")
    kwargs = {"api_key": clave}
    if C.PROVEEDOR == "compatible":
        kwargs["base_url"] = C.COMPATIBLE_BASE_URL
    r = OpenAI(**kwargs).chat.completions.create(
        model=C.MODELO,
        messages=[{"role": "system", "content": instr}, {"role": "user", "content": mensaje}],
        max_tokens=max_tokens, temperature=temperatura)
    return r.choices[0].message.content.strip()


def _huggingface(mensaje: str, instr: str, max_tokens: int, temperatura: float, _json: bool):
    from huggingface_hub import InferenceClient
    token = obtener_clave()
    if not token:
        raise LLMNoDisponible(f"Falta {C.clave_api()} en el entorno.")
    r = InferenceClient(api_key=token, provider="auto").chat.completions.create(
        model=C.MODELO,
        messages=[{"role": "system", "content": instr}, {"role": "user", "content": mensaje}],
        max_tokens=max_tokens, temperature=temperatura)
    return r.choices[0].message.content.strip()


def invocar(mensaje: str, instr: str, max_tokens=600, temperatura=0.2, json_mode=False) -> str:
    if C.PROVEEDOR == "offline":
        raise LLMNoDisponible("Modo offline: se usan reglas de respaldo.")

    RUTAS = {"gemini": _gemini, "openai": _openai_compatible,
            "compatible": _openai_compatible, "huggingface": _huggingface}
    fn = RUTAS.get(C.PROVEEDOR)
    if fn is None:
        raise LLMNoDisponible(f"Proveedor no reconocido: {C.PROVEEDOR}")

    try:
        texto = fn(mensaje, instr, max_tokens, temperatura, json_mode)
        LLAMADAS["ok"] += 1
        return texto
    except LLMNoDisponible:
        LLAMADAS["fallidas"] += 1
        raise
    except Exception as e:  # noqa: BLE001 - queremos degradar, no romper
        LLAMADAS["fallidas"] += 1
        raise LLMNoDisponible(f"{type(e).__name__}: {e}") from e


def extraer_json(texto: str) -> dict:
    ini, fin = texto.find("{"), texto.rfind("}")
    if ini == -1 or fin < ini:
        raise ValueError("La respuesta no contiene JSON.")
    return json.loads(texto[ini:fin + 1])


def invocar_json(mensaje: str, instr: str, max_tokens=400) -> dict:
    try:
        return extraer_json(invocar(mensaje, instr, max_tokens=max_tokens,
                                    temperatura=0.0, json_mode=True))
    except Exception as e:  # noqa: BLE001
        raise LLMNoDisponible(f"JSON inválido: {e}") from e


# ─────────────────────────────────────────────────────────────────────────────
# Contexto de Aethera (se construye una vez y se inyecta en el prompt)
# ─────────────────────────────────────────────────────────────────────────────
HORARIO_ES = {
    "Mon-Fri 09:00-18:00": "lunes a viernes de 09:00 a 18:00",
    "Mon-Sat 12:00-20:00": "lunes a sábado de 12:00 a 20:00",
}
DESCRIPCION_TIPO = {
    "counseling": ("orientación con el equipo de bienestar: organización de estudios, carga "
                   "académica, descanso y rutina, y orientación general. No es atención clínica "
                   "ni de urgencia."),
    "peer_support": ("conversaciones con estudiantes formados como acompañantes: sentirse parte, "
                     "conocer gente, compartir experiencias. Atiende hasta las 20:00 y también "
                     "los sábados."),
    "career_guidance": "orientación sobre prácticas, empleabilidad, CV, entrevistas y decisiones de carrera.",
}


def catalogo() -> list[dict]:
    from . import datos
    out = []
    for tipo, grupo in datos.servicios().groupby("service_type"):
        s0 = grupo.iloc[0]
        out.append({
            "tipo": C.TIPO_ES[tipo],
            "que_ofrece": DESCRIPCION_TIPO[tipo],
            "horario": HORARIO_ES.get(s0["schedule"], s0["schedule"]),
            "canales": [C.CANAL_ES[c] for c in s0["channels"]],
            "sedes": [f"{r['name']} ({r['district_id'].replace('DIST_', '')})"
                      for _, r in grupo.iterrows()],
        })
    return out


def construir_contexto() -> str:
    from . import datos
    lineas = [f"- {c['tipo']}: {c['que_ofrece']} Horario: {c['horario']}. "
              f"Canales: {', '.join(c['canales'])}. Sedes: {'; '.join(c['sedes'])}."
              for c in catalogo()]
    d2 = datos.cargar()["D2"]
    return f"""SOBRE AETHERA
- Aethera es una ciudad universitaria ficticia del desafío binacional Chile–Perú.
  Todo es sintético: no hay personas, lugares ni servicios reales.
- Este piloto atiende a una institución: {C.INSTITUCION}. Hay estudiantes de horario
  diurno y nocturno, y muchos trabajan además de estudiar.

SERVICIOS DE APOYO (fuente: D6, {len(datos.servicios())} servicios)
{chr(10).join(lineas)}
- Para derivar a un servicio se usa: código de estudiante, canal preferido y un motivo NO clínico.
- La atención virtual o telefónica puede ser con cualquier sede; la presencial, en la sede del
  distrito del estudiante.
- Referencia del histórico (D2, {len(d2):,} eventos): la espera media es de
  {d2['wait_days'].mean():.0f} días y la asistencia {d2['attended'].mean():.0%}.

CALENDARIO ACADÉMICO (fuente: D7)
- Cada período tiene inicio, evaluaciones intermedias, una semana de pausa y bienestar,
  evaluaciones finales y cierre.
- Durante el período hay encuentros estudiantiles en cada institución.

QUÉ ES RUTA
- Asistente de IA de orientación NO clínica, parte de Aethera Pulse + Ruta.
- Ayuda a entender qué tipo de apoyo calza con lo que el estudiante cuenta, a conocer
  los servicios y a reservar o reprogramar citas compatibles con su horario.
- No diagnostica, no da tratamientos ni medicación, no es terapia y no atiende emergencias.
- Ante señales de riesgo entrega líneas de ayuda reales y ofrece contacto con una persona
  del equipo de bienestar."""


CONTEXTO = construir_contexto()


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Clasificador
# ─────────────────────────────────────────────────────────────────────────────
# Último recurso: palabras clave. Solo se usa si tampoco hay clasificador
# entrenado. La versión anterior de la app se apoyaba solo aquí y acertaba 27 %,
# peor que la clase mayoritaria (20,6 %): era una falsa red de seguridad.
PALABRAS_MOTIVO = {
    "social_support": ["solo", "sola", "amig", "nadie", "aislad", "conocer gente", "companer",
                       "lejos de mi familia", "soledad", "encajar", "no tengo con quien", "extrano",
                       "mude", "migr"],
    "career_concern": ["practica", "empleo", "cv", "curriculum", "egres", "futuro laboral",
                       "entrevista", "linkedin", "chamba", "trabajo cuando termine",
                       "carrera profesional", "conseguir trabajo", "pasantia"],
    "sleep_and_routine": ["dorm", "sueno", "insomnio", "desvel", "cansad", "rutina", "organiz",
                           "agotad", "energia", "no descanso", "horario", "madrug", "tiempo"],
    "preventive_guidance": ["que servicios", "informacion", "prevenir", "por si acaso", "taller",
                           "como funciona", "que apoyos", "que hay", "conocer los servicios",
                           "orientacion general"],
    "academic_pressure": ["examen", "evaluacion", "parcial", "final", "nota", "curso", "tarea",
                          "entrega", "estudi", "jalar", "desaprob", "carga", "sobrepasad",
                          "rendimiento", "clase", "universidad no", "no avanzo",
                          "no me alcanza el tiempo para estudiar"],
}

INSTR_CLASIFICADOR = f"""
Eres el CLASIFICADOR de Ruta, asistente de orientación NO clínica de una universidad ficticia.
Tu única tarea es elegir el motivo no clínico que mejor describe lo que el estudiante necesita.
No diagnostiques. No uses términos clínicos. No respondas al estudiante.

MOTIVOS VÁLIDOS (usa el código exacto):
{chr(10).join(f"- {k}: {v}" for k, v in C.MOTIVOS.items())}

EJEMPLOS:
- "Tengo tres parciales y no sé por dónde empezar" → academic_pressure
- "Desde que me mudé no tengo con quién hablar" → social_support
- "Termino la carrera y no sé cómo conseguir prácticas" → career_concern
- "Duermo 4 horas y ando agotado todo el día" → sleep_and_routine
- "¿Qué apoyos tiene la universidad?" → preventive_guidance

Devuelve SOLO JSON: {{"reason_code": "<código>", "confianza": <0 a 1>,
"resumen": "<máx. 15 palabras, sin lenguaje clínico>"}}
"""


def clasificar_por_reglas(texto: str) -> tuple[str, float]:
    """Respaldo en dos peldaños: clasificador entrenado sobre D5, y si falla, palabras."""
    try:
        from .ml import clasificar_texto
        motivo, conf = clasificar_texto(texto)
        return motivo, round(conf, 2)
    except Exception:  # noqa: BLE001 - último recurso, nunca debe romper el turno
        pass

    t = normalizar(texto)
    puntos = {m: sum(1 for p in pals if p in t) for m, pals in PALABRAS_MOTIVO.items()}
    mejor = max(puntos, key=puntos.get)
    if puntos[mejor] == 0:
        return "preventive_guidance", 0.3
    return mejor, round(puntos[mejor] / sum(puntos.values()), 2)


def clasificar(texto: str) -> dict:
    try:
        r = invocar_json(f"Mensaje del estudiante:\n{texto}", INSTR_CLASIFICADOR, max_tokens=150)
        codigo = r.get("reason_code")
        if codigo not in C.MOTIVOS:
            raise LLMNoDisponible(f"Código inválido: {codigo}")
        return {"reason_code": codigo, "etiqueta": C.MOTIVOS[codigo],
                "confianza": float(r.get("confianza", 0.7)),
                "resumen": r.get("resumen", ""), "metodo": "modelo de lenguaje"}
    except LLMNoDisponible as e:
        codigo, conf = clasificar_por_reglas(texto)
        return {"reason_code": codigo, "etiqueta": C.MOTIVOS[codigo], "confianza": conf,
                "resumen": "", "metodo": "clasificador D5 (sin LLM)", "detalle": str(e)[:120]}


# ─────────────────────────────────────────────────────────────────────────────
# 2 · Planificador
# ─────────────────────────────────────────────────────────────────────────────
ACCIONES = ["orientar", "informar", "reservar", "replanificar", "calendario",
            "contacto_humano", "conversar"]

INSTR_PLANIFICADOR = """
Eres el PLANIFICADOR de Ruta, agente de orientación no clínica de una universidad ficticia.
No respondes al estudiante: decides la acción.

ACCIONES:
- orientar: cuenta una dificultad o pide ayuda/apoyo/hablar con alguien → clasificar su
  necesidad y proponer citas.
- informar: pregunta qué es Aethera o Ruta, qué servicios hay, cómo funcionan u horarios,
  sin contar una dificultad propia.
- reservar: ya se le mostraron opciones y elige una (por número o descripción).
- replanificar: una opción o reserva no le sirve y quiere otra (otro día, hora o canal).
- calendario: solo pregunta por fechas del calendario académico.
- contacto_humano: pide que una persona del equipo de bienestar lo contacte, o acepta ("sí")
  cuando Ruta se lo ofreció.
- conversar: saludo, agradecimiento, charla breve, pedidos fuera del rol de Ruta (resolver
  tareas, otros temas) o algo que no encaja. En los pedidos fuera de rol marca
  "fuera_de_rol": true.

Extrae también, si aparecen: días que NO puede (0=lunes … 6=domingo), franja preferida
(mañana, tarde, noche; "temprano" = mañana, "final de la tarde" = tarde, "horario extendido"
o "después del trabajo" = noche), canal preferido (digital = virtual/chat/escrito; phone;
in_person = presencial o cerca de su distrito) y si prefiere apoyo entre pares o grupal.

senal_de_riesgo = true SOLO si el mensaje sugiere, aunque sea de forma indirecta, intención de
hacerse daño, de morir o de no seguir viviendo. Tristeza, estrés, cansancio o frustración por
sí solos NO son señal de riesgo.

Devuelve SOLO JSON:
{"accion": "...", "opcion": <número o null>, "evitar_dias": [..],
 "franja": <"mañana"|"tarde"|"noche"|null>, "canal_preferido": <"digital"|"phone"|"in_person"|null>,
 "senal_de_riesgo": <true|false>, "prefiere_pares": <true|false>, "fuera_de_rol": <true|false>,
 "razon": "<breve>"}
"""

DIAS_TEXTO = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
DIFICULTAD = (r"me siento|estoy |no puedo|me cuesta|tengo (problemas|ansiedad|miedo)|"
              r"\bsol[oa]\b|cansad|agotad|estres|triste|sobrepas")
PREGUNTA_INFO = (r"que (servicios|apoyos|tipo de apoyo|es|son|hace|ofrece|puedes)|como funciona|"
                 r"horario de|donde (queda|esta)|quien eres|que es (aethera|ruta)|que hay en")
FUERA_DE_ROL = r"resuelve|resolver|hazme|haz mi|hacer mi (tarea|trabajo)|respuestas? de(l)? (examen|tarea)"


def extraer_numero_opcion(t: str) -> int | None:
    palabras = {"1": 1, "uno": 1, "primera": 1, "primero": 1, "2": 2, "dos": 2, "segunda": 2,
                "segundo": 2, "3": 3, "tres": 3, "tercera": 3, "tercero": 3}
    for token in re.findall(r"\w+", t):
        if token in palabras:
            return palabras[token]
    return None


def extraer_preferencias(t: str) -> dict:
    evitar = [i for i, d in enumerate(DIAS_TEXTO)
              if re.search(rf"\b{d}s?\b", t)
              and re.search(r"no puedo|no me sirve|no me queda|evitar|excepto|menos", t)]
    franja = next((f for f in ["manana", "tarde", "noche"]
                   if re.search(rf"\b(en la |por la )?{f}\b", t)), None)
    franja = {"manana": "mañana"}.get(franja, franja)
    if re.search(r"temprano", t):
        franja = "mañana"
    if re.search(r"horario extendido|despues del trabajo|despues de las 6|noches", t):
        franja = "noche"
    canal = ("digital" if re.search(r"virtual|online|en linea|videollamada|zoom|meet|digital|por escrito|por chat", t)
             else "phone" if re.search(r"telefon|llamada", t)
             else "in_person" if re.search(r"presencial|en persona", t) else None)
    pares = bool(re.search(r"\bpares\b|grupal|otros estudiantes|companeros que", t))
    return {"evitar_dias": evitar, "franja": franja, "canal_preferido": canal,
            "prefiere_pares": pares}


def plan_respaldo(texto: str, sesion) -> dict:
    """Reglas simples, activas solo si el modelo no está disponible."""
    t = normalizar(texto)
    prefs = extraer_preferencias(t)
    cambio = re.search(r"no puedo|no me sirve|no me queda|cambiar|otro dia|otra hora|reprogram|mover|ninguna", t)
    n = extraer_numero_opcion(t)
    pide_persona = re.search(r"que me (contacten|llamen|escriban)|contacte(n)? una persona|"
                             r"hablar con una persona|persona (real|humana)|avisales|"
                             r"avisa a bienestar|pide que me contacten", t)
    afirma = re.fullmatch(r"\s*(si|claro|ok|dale|por favor|bueno)(\s+(por favor|porfa|avisales|gracias))?\s*", t)

    if pide_persona or (sesion.oferta_contacto and afirma):
        accion = "contacto_humano"
    elif (sesion.opciones or sesion.reserva) and cambio:
        accion = "replanificar"
    elif sesion.opciones and n and not sesion.reserva:
        accion = "reservar"
    elif n and len(t.split()) <= 3:
        accion = "conversar"
    elif re.search(FUERA_DE_ROL, t):
        accion = "conversar"
    elif re.search(PREGUNTA_INFO, t) and not re.search(DIFICULTAD, t) and not prefs["prefiere_pares"]:
        accion = "informar"
    elif re.search(r"calendario|cuando (son|es|empiezan)|fechas? de", t) and not re.search(r"ayuda|apoyo", t):
        accion = "calendario"
    elif re.fullmatch(r"\s*(hola|buenas|buenos dias|buenas tardes|buenas noches|gracias|ok|vale|chau)\s*", t):
        accion = "conversar"
    else:
        accion = "orientar"

    return {"accion": accion, "opcion": n, **prefs, "senal_de_riesgo": False,
            "fuera_de_rol": bool(re.search(FUERA_DE_ROL, t)),
            "metodo": "reglas de respaldo"}


def planificar(texto: str, sesion) -> dict:
    estado = {
        "ya_hay_opciones": [f"{o['opcion']}: {o['dia']} {o['hora']} {o['servicio']} ({o['canal']})"
                            for o in sesion.opciones],
        "ya_hay_reserva": bool(sesion.reserva),
        "ultimo_mensaje_de_ruta": (sesion.historial[-1]["texto"][:300]
                                   if sesion.historial else None),
        "ruta_ofrecio_contacto_humano": sesion.oferta_contacto,
    }
    try:
        r = invocar_json(f"ESTADO: {json.dumps(estado, ensure_ascii=False)}\nMENSAJE: {texto}",
                         INSTR_PLANIFICADOR, max_tokens=250)
        if r.get("accion") not in ACCIONES:
            raise LLMNoDisponible("Acción inválida")
        if r["accion"] == "reservar" and not sesion.opciones:
            r["accion"] = "orientar"
        dias = [int(d) for d in (r.get("evitar_dias") or [])
                if str(d).isdigit() and 0 <= int(d) <= 6]
        return {
            "accion": r["accion"], "opcion": r.get("opcion"), "evitar_dias": dias,
            "franja": r.get("franja") if r.get("franja") in ("mañana", "tarde", "noche") else None,
            "canal_preferido": (r.get("canal_preferido")
                                if r.get("canal_preferido") in C.CANAL_ES else None),
            "senal_de_riesgo": bool(r.get("senal_de_riesgo")),
            "fuera_de_rol": bool(r.get("fuera_de_rol")),
            "prefiere_pares": bool(r.get("prefiere_pares")),
            "razon": r.get("razon", ""), "metodo": "modelo",
        }
    except (LLMNoDisponible, ValueError, TypeError) as e:
        plan = plan_respaldo(texto, sesion)
        plan["detalle"] = str(e)[:120]
        return plan


# ─────────────────────────────────────────────────────────────────────────────
# 3 · Redactor
# ─────────────────────────────────────────────────────────────────────────────
INSTR_REDACTOR = f"""
Eres Ruta, asistente de IA de ORIENTACIÓN NO CLÍNICA de Aethera Pulse + Ruta.

{CONTEXTO}

CÓMO RESPONDES
- Usa solo este contexto y RESULTADOS. No inventes servicios, fechas, horas, personas ni
  teléfonos.
- No diagnostiques, no pongas etiquetas clínicas a la persona, no recomiendes medicamentos ni
  tratamientos. No eres terapeuta.
- Si es el primer turno, preséntate en una frase como asistente de IA de orientación.
- Tono cálido, cercano y concreto, en español neutro. Máximo 120 palabras. Valida lo que
  siente sin dramatizar ni sermonear.
- Según la ACCIÓN:
  · orientar: reconoce lo que cuenta, explica en una frase qué tipo de apoyo calza y muestra
    las opciones numeradas EXACTAMENTE como vienen (número, día, fecha, hora, servicio, canal).
    Si una opción es de pares (es_puente_pares=true), explica que es un primer contacto con
    estudiantes formados mientras se coordina orientación. Cierra pidiendo que elija un número
    o diga si ninguna le sirve.
  · informar: responde con el contexto y ofrece buscar una cita si le sirve.
  · reservar: confirma día, hora, servicio, canal y recordatorios; recuerda que puede reprogramar.
  · replanificar: muestra las nuevas opciones numeradas.
  · calendario: resume las fechas pedidas.
  · contacto_humano: confirma con el código del pedido que una persona de bienestar lo
    contactará; si la prioridad es alta, repite las líneas de ayuda (Perú: Línea 113 opción 5;
    Chile: *4141).
  · conversar o abrir_desde_pulse: escucha, valida y pregunta qué le pesa. No presiones para
    reservar.
- Calendario: solo si RESULTADOS trae "evento_relevante", menciónalo en UNA frase conectada
  con lo que cuenta. Si no viene, no hables del calendario ni de evaluaciones.
- Si viene "voces_de_aethera", usa su frase (o una equivalente) UNA vez para normalizar, sin
  exagerar ni dramatizar. Habla de "relatos de estudiantes"; nunca cites relatos textuales.
- Si "proponer_opciones" trae "nota_preferencia", dilo con naturalidad antes de las opciones.
- Si hay "registro_pulse", úsalo con delicadeza (p. ej. "vi que marcaste varios días pesados"),
  sin repetir datos de más.
- Si piden algo fuera de tu rol, explica con amabilidad qué sí puedes hacer.
- Nunca menciones probabilidades, modelos, códigos internos (reason_code, slot_id, service_id)
  ni datos de otros estudiantes.
"""


def redactar(texto: str, accion: str, resultados: dict, sesion) -> tuple[str, str]:
    if accion == "contacto_humano":
        from .agente import texto_contacto_humano
        return texto_contacto_humano(resultados["contacto_humano"], sesion.perfil), \
            "plantilla fija (contacto humano)"

    contexto = {
        "primer_turno": not sesion.presentado,
        "accion": accion,
        "perfil_operativo": resumen_perfil(sesion.perfil),
        "historial_reciente": sesion.historial[-4:],
        "resultados": resultados,
    }
    if sesion.contexto_pulse and "registro_pulse" not in resultados:
        contexto["registro_pulse"] = sesion.contexto_pulse

    try:
        return invocar(f"MENSAJE DEL ESTUDIANTE:\n{texto}\n\nRESULTADOS:\n"
                       f"{json.dumps(contexto, ensure_ascii=False, default=str, indent=1)}",
                       INSTR_REDACTOR, max_tokens=700, temperatura=0.3), "modelo"
    except LLMNoDisponible:
        from .agente import plantilla
        return plantilla(accion, resultados, sesion), "plantilla de respaldo"


def resumen_perfil(perfil: dict) -> str:
    """Solo los datos OPERATIVOS. Nunca ansiedad, puntajes ni uso previo."""
    trabajo = {"not_working": "no trabaja", "part_time": "trabaja medio tiempo",
               "full_time": "trabaja tiempo completo"}.get(perfil.get("employment_status"), "")
    return (f"estudia en horario {'diurno' if perfil.get('study_mode') == 'day' else 'nocturno'}, "
            f"{trabajo}, distrito {perfil.get('district_id')}, "
            f"{'no conoce' if perfil.get('services_awareness') == 'unaware' else 'conoce'} los servicios")


if __name__ == "__main__":  # pragma: no cover
    print(f"Proveedor: {C.PROVEEDOR} | Modelo: {C.MODELO}")
    print(f"Clave {C.clave_api()}: {'encontrada' if obtener_clave() else 'NO ENCONTRADA'}")
    for texto in ["Tengo tres parciales y no sé por dónde empezar",
                  "Desde que me mudé no tengo con quién hablar",
                  "Termino la carrera y no sé cómo conseguir prácticas",
                  "Duermo 4 horas y ando agotado",
                  "¿Qué apoyos tiene la universidad?"]:
        r = clasificar(texto)
        print(f"  {texto[:46]:48} → {r['reason_code']:20} ({r['metodo']})")
