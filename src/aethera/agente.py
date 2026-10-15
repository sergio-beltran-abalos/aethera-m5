"""
Aethera · agente Ruta.

Orquesta el turno completo:

    mensaje → guardrail de entrada → planificador → herramientas → redactor
            → guardrail de salida → respuesta

Aquí viven las herramientas y el estado de sesión. Los LLM no están aquí: están
en `ia.py`, y solo deciden, nunca aportan datos.
"""
from __future__ import annotations

import itertools
import json
import re
import time
from datetime import date, timedelta

from . import calendario, config as C, guardrails, horarios, ia, ml, servicios
from .horarios import a_hhmm, a_minutos, normalizar

ACCIONES = ia.ACCIONES
EVENTOS: list[dict] = []          # bitácora para KPIs (se recalculan en vivo)
SOLICITUDES_CONTACTO: list[dict] = []
_SESIONES = itertools.count(1)


# ─────────────────────────────────────────────────────────────────────────────
# Sesión
# ─────────────────────────────────────────────────────────────────────────────
class Sesion:
    def __init__(self, perfil: dict, nombre_perfil: str = "", agenda: servicios.Agenda | None = None):
        self.id = f"S-{next(_SESIONES):03d}"
        self.perfil = perfil
        self.nombre_perfil = nombre_perfil
        self.agenda = agenda or servicios.Agenda()
        self.presentado = False
        self.motivo = None
        self.opciones: list[dict] = []
        self.reserva = None
        self.historial: list[dict] = []
        self.trazas: list[dict] = []
        self.turnos = 0
        self.mood_track: list[dict] = []
        self.contexto_pulse = None
        self.eventos_mencionados: set[str] = set()
        self.voces_usadas = False
        self.consentimiento_pulse = False
        self.oferta_contacto = False
        self.hora_inicio = None

    def registrar(self, evento: str, **datos) -> None:
        EVENTOS.append({"sesion": self.id, "evento": evento, "turno": self.turnos, **datos})


# ─────────────────────────────────────────────────────────────────────────────
# Herramientas
# ─────────────────────────────────────────────────────────────────────────────
def buscar_servicios(reason_code: str, perfil: dict) -> list[dict]:
    """Servicios del tipo que D2 asocia a ese motivo, con su evidencia histórica."""
    from . import datos
    tipo = datos.mapa_motivo_servicio()[reason_code]
    df = datos.servicios()
    df = df[df["service_type"] == tipo].copy()
    df["mismo"] = df["district_id"] == perfil["district_id"]
    df = df.sort_values(["mismo", "asistencia_historica"], ascending=[False, False])
    return [{
        "service_id": s["service_id"], "nombre": s["name"], "tipo": C.TIPO_ES[tipo],
        "distrito": s["district_id"], "horario": s["schedule"],
        "canales": [C.CANAL_ES[c] for c in s["channels"]],
        "mismo_distrito": bool(s["mismo"]),
        "asistencia_historica_D2": s["asistencia_historica"],
        "espera_media_dias_D2": s["espera_media_dias"],
    } for _, s in df.iterrows()]


_VOCES = None


def voces_de_aethera(motivo: str) -> dict:
    """
    Normalización con datos AGREGADOS de D4. Nunca se cita un relato textual.

    El texto dice "cerca de N de cada 10", no "el estudiante X escribió Y": en
    salud mental, citar Textos individuales es el camino corto a la reidentificación.
    """
    global _VOCES
    from . import datos
    if _VOCES is None:
        d4 = datos.cargar()["D4"]
        nova = d4[d4["institution_id"] == C.INSTITUCION]
        t = nova["text"].str.lower()
        _VOCES = {
            "academic_pressure": (nova["topic"].eq("academic_pressure"),
                                  "hablan de presión académica"),
            "career_concern": (nova["topic"].eq("career_concern"), "hablan de su futuro laboral"),
            "social_support": (nova["topic"].eq("social_support") | t.str.contains("aislad"),
                               "hablan de sentirse solos o de su red de apoyo"),
            "sleep_and_routine": (t.str.contains("descans|cansancio|dorm"),
                                  "mencionan el descanso o el cansancio"),
            "preventive_guidance": (t.str.contains("conocer opciones de orientación"),
                                    "mencionan querer conocer opciones de orientación"),
        }
        _VOCES["_n"] = len(nova)

    mascara, tema = _VOCES[motivo]
    p = float(mascara.mean())
    return {"fuente": "D4, relatos sintéticos (agregado)", "relatos_nova": _VOCES["_n"],
            "proporcion": round(p, 3),
            "frase": (f"No eres la única persona: cerca de {max(1, round(p * 10))} de cada 10 "
                      f"relatos de estudiantes {tema}.")}


def reservar(sesion: Sesion, numero_opcion: int) -> dict:
    opcion = next((o for o in sesion.opciones if o["opcion"] == numero_opcion), None)
    if opcion is None:
        return {"ok": False, "error": f"No existe la opción {numero_opcion}."}
    if not sesion.agenda.reservar(opcion["slot_id"]):
        return {"ok": False, "error": "Ese turno ya no está disponible."}

    fecha = date.fromisoformat(opcion["fecha"])
    hora_ini = a_minutos(opcion["hora"].split("–")[0])
    sesion.reserva = {
        **opcion,
        "reserva_id": f"R-{len(_RESERVAS) + 1:04d}",
        "student_id": sesion.perfil["student_id"],
        "reservada_el": C.FECHA_DEMO,
        "dias_hasta_reserva": (fecha - date.fromisoformat(C.FECHA_DEMO)).days,
        "recordatorios": [
            f"{(fecha - timedelta(days=1)).isoformat()} 19:00",
            f"{opcion['fecha']} {a_hhmm(hora_ini - 120)}",
        ],
    }
    _RESERVAS.append(sesion.reserva)
    return {"ok": True, "reserva": sesion.reserva}


_RESERVAS: list[dict] = []


def replanificar(sesion: Sesion, **filtros) -> dict:
    excluir = {o["slot_id"] for o in sesion.opciones}
    anterior = None
    if sesion.reserva:
        anterior = sesion.reserva
        sesion.agenda.liberar(anterior["slot_id"])
        excluir.add(anterior["slot_id"])
        _RESERVAS[:] = [r for r in _RESERVAS if r["reserva_id"] != anterior["reserva_id"]]
        sesion.reserva = None

    nuevas = servicios.proponer_opciones(
        sesion.perfil, sesion.motivo or "preventive_guidance", sesion.agenda,
        excluir_slots=excluir, **filtros)
    return {"reserva_liberada": anterior["reserva_id"] if anterior else None, **nuevas}


def solicitar_contacto_humano(sesion: Sesion, origen: str = "chat") -> dict:
    """Registra el pedido con el MÍNIMO de datos: código, prioridad y motivo no clínico."""
    urgente = any("crisis" in str(t.get("guardrail_entrada", "")) for t in sesion.trazas[-2:])
    previa = next((s for s in SOLICITUDES_CONTACTO
                   if s["student_id"] == sesion.perfil["student_id"] and s["estado"] == "pendiente"),
                  None)
    if previa:
        previa["prioridad"] = "alta" if urgente else previa["prioridad"]
        return previa

    solicitud = {"solicitud": f"H-{len(SOLICITUDES_CONTACTO) + 1:03d}",
                 "student_id": sesion.perfil["student_id"],
                 "prioridad": "alta" if urgente else "normal",
                 "motivo_no_clinico": sesion.motivo, "origen": origen,
                 "fecha": C.FECHA_DEMO, "estado": "pendiente"}
    SOLICITUDES_CONTACTO.append(solicitud)
    sesion.registrar("derivacion_humana_solicitada", prioridad=solicitud["prioridad"])
    return solicitud


def texto_contacto_humano(solicitud: dict, perfil: dict) -> str:
    if solicitud["prioridad"] == "alta":
        linea = C.LINEAS_AYUDA.get(perfil.get("country_context"),
                                   C.LINEAS_AYUDA[C.LINEA_POR_DEFECTO])
        return (f"Listo, registré tu pedido con prioridad alta ({solicitud['solicitud']}): una "
                f"persona del equipo de bienestar te contactará. Mientras tanto, no tienes que "
                f"esperar: {linea}")
    return (f"Listo, registré tu pedido ({solicitud['solicitud']}): una persona del equipo de "
            "bienestar te contactará en su horario de atención. Solo compartimos tu código de "
            "estudiante y el tipo de apoyo que buscas, nada de lo que escribiste aquí.")


def lista_opciones(opciones: list[dict]) -> str:
    filas = []
    for o in opciones:
        extra = " — primer contacto con pares" if o["es_puente_pares"] else ""
        filas.append(f"{o['opcion']}. {o['dia'].capitalize()} {o['fecha']}, {o['hora']} · "
                     f"{o['servicio']} ({o['canal']}){extra}")
    return "\n".join(filas)


# ─────────────────────────────────────────────────────────────────────────────
# Plantillas (respaldo y respuestas de datos verificados)
# ─────────────────────────────────────────────────────────────────────────────
def plantilla(accion: str, resultados: dict, sesion: Sesion) -> str:
    intro = ("Soy Ruta, un asistente de IA de orientación (no clínica). "
             if not sesion.presentado else "")

    if accion == "orientar":
        c = resultados["clasificar"]
        ops = resultados["proponer_opciones"]
        texto = (f"{intro}Gracias por contármelo. Por lo que describes, puedo ayudarte con "
                 f"{c['etiqueta'].split(' (')[0]}.")
        if resultados.get("voces"):
            texto += f" {resultados['voces']['frase']}"
        evento = calendario.frase_evento(
            resultados.get("consultar_calendario", {}).get("evento_relevante"))
        if evento:
            texto += f" {evento}"
        if ops["opciones"]:
            if ops.get("nota_preferencia"):
                texto += f"\n\n{ops['nota_preferencia']}"
            texto += f"\n\nEstas opciones calzan con tu horario:\n{lista_opciones(ops['opciones'])}"
            if ops["seguimiento_humano"]:
                texto += ("\n\nLas opciones de pares son un primer contacto mientras se "
                          "coordina la orientación.")
            texto += ("\n\n¿Cuál te acomoda? Responde con el número, o dime si ninguna te "
                      "sirve y busco otras.")
        else:
            texto += ("\n\nNo encontré turnos compatibles con tu horario en las próximas dos "
                      "semanas. Dejo registrado un seguimiento para que el equipo de bienestar "
                      "te contacte.")
        return texto

    if accion == "informar":
        filas = [f"• {c['tipo']}: {c['que_ofrece']} ({c['horario']}; {', '.join(c['canales'])})"
                 for c in resultados["catalogo"]]
        return (f"{intro}En Aethera hay tres tipos de apoyo para estudiantes:\n"
                + "\n".join(filas)
                + "\n\nSi quieres, cuéntame qué necesitas y busco una cita que calce con tu horario.")

    if accion == "reservar":
        r = resultados["reservar"]
        if not r["ok"]:
            return f"{r['error']} ¿Quieres que busque otras opciones?"
        x = r["reserva"]
        return (f"¡Listo! Quedó reservado: {x['dia']} {x['fecha']}, {x['hora']} en "
                f"{x['servicio']} ({x['canal']}). Te enviaré recordatorios el día anterior y 2 "
                "horas antes. Si algo cambia, escríbeme y lo reprogramamos.")

    if accion == "replanificar":
        ops = resultados["replanificar"]
        if not ops["opciones"]:
            return ("No encontré otras opciones con esas condiciones en las próximas dos "
                    "semanas. Dejo registrado un seguimiento para que el equipo de bienestar "
                    "te contacte.")
        return (f"Sin problema, busquemos otra opción:\n{lista_opciones(ops['opciones'])}\n\n"
                "¿Cuál te acomoda?")

    if accion == "calendario":
        ev = resultados["consultar_calendario"]["eventos"]
        if not ev:
            return "No hay eventos académicos en las próximas semanas."
        return "Esto es lo que viene en el calendario:\n" + "\n".join(
            f"• {e['titulo']}: {e['desde']} al {e['hasta']}" for e in ev)

    if accion == "contacto_humano":
        return texto_contacto_humano(resultados["contacto_humano"], sesion.perfil)

    if accion == "abrir_desde_pulse":
        p = resultados["registro_pulse"]
        hoy = p.get("hoy") or {}
        temas = f" (sobre todo por {', '.join(hoy['temas']).lower()})" if hoy.get("temas") else ""
        patron = " También vi que esta semana marcaste varios días pesados." if p.get("patron_dias_pesados") else ""
        return (f"{intro}Vi que hoy marcaste tu día como «{str(hoy.get('animo', 'regular')).lower()}»"
                f"{temas}.{patron} ¿Quieres contarme qué es lo que más te está pesando? Puedo "
                "ayudarte a encontrar un espacio de apoyo que calce con tu horario.")

    if resultados.get("fuera_de_rol"):
        return (f"{intro}Eso no lo puedo hacer: no resuelvo tareas ni temas fuera de la "
                "orientación. Lo que sí puedo es ayudarte a encontrar apoyo en la universidad, "
                "por ejemplo orientación para organizar tus estudios, en un horario que te "
                "acomode. ¿Te sirve?")

    return (f"{intro}Puedo ayudarte a encontrar un espacio de apoyo que calce con tu horario o "
            "contarte qué servicios hay en Aethera. Cuéntame en una frase qué es lo que más te "
            "está pesando: estudios, descanso, sentirte solo/a, tu futuro laboral u otra cosa.")


# ─────────────────────────────────────────────────────────────────────────────
# Ejecución de herramientas
# ─────────────────────────────────────────────────────────────────────────────
def ejecutar(plan: dict, texto: str, sesion: Sesion) -> dict:
    accion = plan["accion"]
    res: dict = {}
    filtros = {k: plan.get(k) for k in ["evitar_dias", "franja", "canal_preferido"] if plan.get(k)}

    if accion == "orientar":
        res["clasificar"] = ia.clasificar(texto)
        sesion.motivo = res["clasificar"]["reason_code"]

        cal = calendario.consultar(motivo=sesion.motivo)
        evento = cal["evento_relevante"]
        if evento and evento["titulo"] in sesion.eventos_mencionados:
            evento = None                       # no repetir el mismo evento
        if evento:
            sesion.eventos_mencionados.add(evento["titulo"])
        res["consultar_calendario"] = {"evento_relevante": evento}

        if not sesion.voces_usadas:            # normalización, una vez por conversación
            res["voces"] = voces_de_aethera(sesion.motivo)
            sesion.voces_usadas = True

        res["buscar_servicios"] = buscar_servicios(sesion.motivo, sesion.perfil)[:3]
        res["proponer_opciones"] = servicios.proponer_opciones(
            sesion.perfil, sesion.motivo, sesion.agenda,
            tipo="peer_support" if plan.get("prefiere_pares") else None, **filtros)

        sesion.opciones = res["proponer_opciones"]["opciones"]
        sesion.registrar("busco_ayuda", motivo=sesion.motivo)
        sesion.registrar("opciones_mostradas", n=len(sesion.opciones))
        if not sesion.opciones:
            sesion.registrar("sin_opciones")

    elif accion == "informar":
        res["catalogo"] = ia.catalogo()

    elif accion == "reservar":
        n = plan.get("opcion") or ia.extraer_numero_opcion(normalizar(texto)) or 1
        res["reservar"] = reservar(sesion, int(n))
        if res["reservar"]["ok"]:
            r = res["reservar"]["reserva"]
            sesion.registrar("reserva_confirmada", canal=r["canal"],
                             p_asistencia=r["p_asistencia"],
                             time_to_booking=r["dias_hasta_reserva"])

    elif accion == "replanificar":
        sesion.registrar("replanificacion_solicitada")
        ref = sesion.reserva or (sesion.opciones[0] if sesion.opciones else None)
        if ref and re.search(r"ese dia|esa fecha", normalizar(texto)):
            filtros["excluir_fechas"] = [ref["fecha"]]
        res["replanificar"] = replanificar(sesion, **filtros)
        sesion.opciones = res["replanificar"]["opciones"]
        if sesion.opciones:
            sesion.registrar("replanificacion_con_opciones")

    elif accion == "calendario":
        res["consultar_calendario"] = calendario.consultar(dias=30)

    elif accion == "contacto_humano":
        res["contacto_humano"] = solicitar_contacto_humano(sesion)

    elif accion == "conversar" and plan.get("fuera_de_rol"):
        res["fuera_de_rol"] = True

    return res


# ─────────────────────────────────────────────────────────────────────────────
# Turno completo
# ─────────────────────────────────────────────────────────────────────────────
def procesar_mensaje(sesion: Sesion, texto: str) -> tuple[str, dict]:
    t0 = time.time()
    traza = {"turno": sesion.turnos + 1, "mensaje": texto}

    control = guardrails.evaluar_entrada(texto, sesion.perfil)
    traza["guardrail_entrada"] = control["tipo"]

    plan = None
    if control["permitido"]:
        plan = ia.planificar(texto, sesion)
        traza["plan"] = plan
        if plan.get("senal_de_riesgo"):
            control = guardrails.respuesta_a_riesgo_llm(sesion.perfil)
            traza["guardrail_entrada"] = control["tipo"]

    sesion.oferta_contacto = False
    if not control["permitido"]:
        respuesta = control["respuesta"]
        sesion.oferta_contacto = control["tipo"].startswith("crisis")
        traza.update({"accion": "bloqueado", "herramientas": [],
                      "derivacion_humana": control["derivacion_humana"]})
        sesion.registrar("guardrail_" + control["tipo"].split()[0])
    else:
        traza["accion"] = plan["accion"]
        resultados = ejecutar(plan, texto, sesion)
        traza["herramientas"] = list(resultados)
        traza["resultados"] = resultados

        respuesta, metodo = ia.redactar(texto, plan["accion"], resultados, sesion)
        traza["redaccion"] = metodo

        problemas = guardrails.validar_salida(respuesta, sesion.opciones)
        traza["guardrail_salida"] = problemas or "ok"
        if problemas:
            respuesta = plantilla(plan["accion"], resultados, sesion)
            sesion.registrar("guardrail_salida_corrigio")
        traza["derivacion_humana"] = bool(
            resultados.get("proponer_opciones", {}).get("seguimiento_humano"))

    traza["segundos"] = round(time.time() - t0, 2)
    sesion.historial += [{"rol": "estudiante", "texto": texto},
                         {"rol": "ruta", "texto": respuesta}]
    sesion.trazas.append(traza)
    sesion.turnos += 1
    sesion.presentado = True
    return respuesta, traza


def reiniciar_demostracion() -> None:
    """Deja el sistema como si nadie lo hubiera tocado (para la demo y los tests)."""
    EVENTOS.clear()
    SOLICITUDES_CONTACTO.clear()
    _RESERVAS.clear()
