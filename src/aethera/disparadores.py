"""
Aethera · disparadores proactivos.

Hasta ahora Ruta esperaba a que el estudiante hablara. Eso deja fuera justo a
quien la misión busca: quien no pide ayuda porque no sabe que puede, o porque
no cree que su caso lo amerite. Estos disparadores invierten el modelo: el
sistema observa lo que ya está autorizado y, si encuentra un momento que lo
justifique, ofrece un espacio sin que nadie lo haya solicitado.

Límites que este módulo respeta sin excepción:

- Solo usa datos del propio estudiante y únicamente con su consentimiento.
- No infiere nada sobre terceros ni comparte señales entre estudiantes.
- El evento del calendario es el mismo para toda la comunidad: no se
  personaliza por perfil, porque un aviso distinto según el estado de ánimo de
  cada quien es precisamente la señal que este producto no debe producir.
- Cada disparador actúa una sola vez por sesión. Un sistema que insiste se
  vuelve molesto, y en este contexto también estigmatizante.
"""
from __future__ import annotations

from datetime import date

from . import config as C
from . import pulso

# Días de anticipación con que se anuncia un evento institucional.
DIAS_ANTICIPACION_EVENTO = 7

# Motivo que se propone ante cada tipo de evento.
MOTIVO_EVENTO = {
    "wellbeing_activity": "preventive_guidance",
    "evaluation_week": "academic_pressure",
}

# Motivo que se propone ante días pesados propios.
MOTIVO_PESADO = "sleep_and_routine"


# ─────────────────────────────────────────────────────────────────────────────
# Lectura de señales
# ─────────────────────────────────────────────────────────────────────────────
def evento_proximo() -> dict | None:
    """
    Próximo evento institucional aprovechable, si está lo bastante cerca.

    El evento es público y común: se lee de D7 sin filtrar por perfil.
    """
    from . import calendario
    hoy = date.fromisoformat(C.FECHA_DEMO)
    c = calendario.consultar(dias=DIAS_ANTICIPACION_EVENTO + 1)
    for e in c["eventos"]:
        if e["tipo"] not in MOTIVO_EVENTO:
            continue
        dias = (date.fromisoformat(e["desde"]) - hoy).days
        if 0 <= dias <= DIAS_ANTICIPACION_EVENTO:
            return {**e, "dias_para": dias}
    return None


def patron_pesado(sesion) -> dict | None:
    """
    Días pesados en la última semana, si el patrón es claro.

    Se exige al menos 3 registros y 3 días pesados: menos que eso es ruido, y
    Offers sobre una muestra insuficiente erosionan la confianza en el resto de
    recomendaciones del sistema.
    """
    r = pulso.resumen(sesion)
    if not r["patron_dias_pesados"]:
        return None
    return {"dias_pesados": r["dias_pesados_7d"],
            "dias_registrados": r["dias_registrados_7d"],
            "tendencia": r["tendencia"]}


# ─────────────────────────────────────────────────────────────────────────────
# Construcción del mensaje
# ─────────────────────────────────────────────────────────────────────────────
def _ventanas(sesion) -> str:
    """Sus huecos libres, en lenguaje natural y solo los dos primeros."""
    from . import horarios
    libres = horarios.resumen_fronteras(sesion.perfil)["ventanas_libres"]
    return " y ".join(libres[:2]) if libres else "las horas que tienes libres"


def _oferta_evento(sesion, evento: dict) -> dict:
    from . import calendario

    titulo = calendario.titulo_limpio(evento["titulo"])
    verbo = {"wellbeing_activity": "empieza", "evaluation_week": "empiezan"}[evento["tipo"]]
    fecha = calendario.fecha_larga(evento["desde"])
    ventana = _ventanas(sesion)
    d = evento["dias_para"]
    plazo = "hoy" if d == 0 else ("mañana" if d == 1 else f"dentro de {d} días")

    if evento["tipo"] == "wellbeing_activity":
        frase = (f"La **{titulo}** {verbo} {plazo}, el {fecha}. Es cuando la universidad tiene "
                 f"más espacio para acompañar a quien lo necesite, así que te busco un apoyo con "
                 f"esa fecha en mente. Hoy tienes libre {ventana}.")
    else:
        frase = (f"Las **{titulo}** {verbo} {plazo}, el {fecha}. Te propongo dejar un espacio "
                 f"acordado antes de esa fecha, para no resolverlo con la cabeza llena. "
                 f"Hoy tienes libre {ventana}.")

    return {"tipo": "evento",
            "clave": f"evento:{evento['titulo']}",
            "motivo": MOTIVO_EVENTO[evento["tipo"]],
            "frase": frase,
            "evento": titulo,
            "evento_fecha": evento["desde"],
            "evento_hasta": evento["hasta"],
            "dias_para": evento["dias_para"]}


def _oferta_patron(sesion, patron: dict) -> dict:
    if patron["tendencia"] == "sube":
        frase = (f"Esta semana registraste {patron['dias_pesados']} días difíciles de "
                 f"{patron['dias_registrados']}, aunque en los últimos días va subiendo. A "
                 f"veces conviene ordenar lo que pasó antes de que vuelva a bajar. "
                 f"Tienes libre {_ventanas(sesion)}.")
    else:
        frase = (f"Llevas {patron['dias_pesados']} días difíciles de {patron['dias_registrados']} "
                 f"registrados en Pulse. No hace falta que sepas explicarme qué te pasa: puedo "
                 f"buscarte un espacio para hablar o para ordenar la carga. "
                 f"Tienes libre {_ventanas(sesion)}.")

    return {"tipo": "patron",
            "clave": "patron_pesado",
            "motivo": MOTIVO_PESADO,
            "frase": frase,
            "dias_pesados": patron["dias_pesados"]}


# ─────────────────────────────────────────────────────────────────────────────
# Evaluación
# ─────────────────────────────────────────────────────────────────────────────
def evaluar(sesion) -> dict | None:
    """
    Devuelve la oferta proactiva si el momento la justifica, o None.

    El orden importa: el evento institucional es común a todos y por tanto no
    revela nada del estudiante. El patrón de días pesados sí es personal, así
    que va después, y solo cuando el estudiante ya lo registró voluntariamente.
    """
    if not sesion.consentimiento_pulse:
        return None

    vistos = sesion.disparadores_vistos

    evento = evento_proximo()
    if evento and f"evento:{evento['titulo']}" not in vistos:
        vistos.add(f"evento:{evento['titulo']}")
        return _oferta_evento(sesion, evento)

    patron = patron_pesado(sesion)
    if patron and "patron_pesado" not in vistos:
        vistos.add("patron_pesado")
        return _oferta_patron(sesion, patron)

    return None


def texto_oferta(oferta: dict) -> str:
    """
    Encabezado del turno proactivo, con su marca de origen.

    Se declara que la iniciativa es de Ruta y no del estudiante: sin esa
    honestidad, un mensaje que aparece sin que nadie lo pidiera se lee como
    vigilancia.
    """
    return (f"{oferta['frase']}\n\n"
            f"Te escribo yo, sin que me lo hayas pedido: veo el calendario de la universidad y, "
            f"si diste tu consentimiento, tu registro de Pulse. Nada de esto es obligatorio.")
