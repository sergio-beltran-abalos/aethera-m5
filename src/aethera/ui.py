"""
Aethera · construcción de la app Gradio.

Mantiene toda la interfaz declarativa en un solo lugar. Los handlers son finos:
 traducen lo que pasó en la UI a llamadas al dominio y.devuelven HTML.
"""
from __future__ import annotations

import os

from . import agente, calendario, config as C, datos, pulso, servicios, vistas
from .segmentos import tarjetas_demo

LANZAR = os.getenv("AETHERA_LANZAR_UI", "1") == "1"
COMPARTIR = os.getenv("AETHERA_SHARE", "0") == "1"
FORZAR_TEMA_CLARO = """() => {
  const u = new URL(window.location);
  if (u.searchParams.get('__theme') !== 'light') {
    u.searchParams.set('__theme', 'light'); window.location.replace(u);
  }
}"""

# Cambio de pestaña por JS en vez de por gr.Tabs: no depende de la version de
# Gradio ni de su API interna de actualizacion, que ha cambiado varias veces.
# Devuelve las entradas sin tocarlas: el js de un evento REEMPLAZA lo que se
# envia al backend, no lo amplía, asi que hay que devolverlas tal cual.
IR_A_RUTA_JS = """(...args) => {
  const b = [...document.querySelectorAll('.tab-nav button, [role=tab]')]
            .find(x => /Ruta/.test(x.textContent || ''));
  if (b) b.click();
  return args;
}"""


def tema():
    import gradio as gr
    try:
        t = gr.themes.Soft(primary_hue="teal", neutral_hue="slate",
                           font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"])
        return t.set(
            body_background_fill=vistas.CANVAS,
            body_text_color=vistas.TINTA,
            button_primary_background_fill=vistas.PETROLEO,
            button_primary_background_fill_hover=vistas.PETROLEO_OSC,
            button_primary_text_color="#FFFFFF",
            block_border_color=vistas.BORDE,
            block_radius="16px",
            input_background_fill="#FAFCFD",
        )
    except Exception:  # noqa: BLE001 - la UI no debe caer por un tema
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────────────────────────
def _reiniciar(nombre: str, etiqueta_fecha: str, con_historial: bool):
    """Cada cambio de configuración parte de una agenda y un registro limpios."""
    C.FECHA_DEMO = C.FECHAS_DEMO[etiqueta_fecha]
    perfil = tarjetas_demo()[nombre]
    sesion = agente.Sesion(perfil, nombre, servicios.Agenda(desde=C.FECHA_DEMO))
    sesion.registrar("checkin_mostrado")
    return (sesion, [], vistas.html_ficha_perfil(nombre),
            vistas.html_mood_track(sesion), vistas.html_frase(),
            vistas.html_panel_traza(sesion), vistas.tabla_reservas_html(),
            vistas.html_bienestar(), None, False)


def _consentir(acepta: bool, con_historial: bool, sesion):
    import gradio as gr
    if sesion is None:
        gr.Warning("Un momento: todavía se está preparando la sesión.")
        return "", vistas.html_frase(), sesion
    if acepta:
        sesion.consentimiento_pulse = True
        sesion.registrar("consentimiento_pulse")
        if con_historial and not sesion.mood_track:
            sesion.mood_track = pulso.historial_ejemplo(sesion.nombre_perfil)
    else:                       # revocar = dejar de guardar y borrar lo ya guardado
        pulso.borrar(sesion)
        sesion.consentimiento_pulse = False
    return vistas.html_mood_track(sesion), vistas.html_frase(), sesion


def _registrar(id_mood: str, temas, nota: str, sesion, estilo_evento: str, chat):
    import gradio as gr
    if sesion is None:          # la sesion se crea en app.load; si falta, es un arranque en frio
        gr.Warning("Un momento: todavía se está preparando la sesión.")
        return (vistas.html_frase(), "", sesion, chat, "",
                gr.update(visible=False))
    if not id_mood:
        gr.Warning("Elige cómo te sientes hoy.")
        return (vistas.html_frase(), vistas.html_mood_track(sesion), sesion, chat,
                "", gr.update(visible=False))

    sesion.estilo_evento = estilo_evento or "neutro"
    resultado = pulso.registrar(sesion, id_mood, temas or [], nota)

    # Un check-in también puede activar crisis: la UI debe derivar igual.
    if resultado.get("crisis"):
        sesion.oferta_contacto = True

    # Si hay sugerencia proactiva (evento o patrón), se evalúa para la tarjeta en Pulse
    # y se preparan las opciones en sesion.opciones, sin volcarlas como elección forzada.
    _, oferta = agente.ofrecer_proactivamente(sesion)
    aviso = vistas.html_oferta_ruta(oferta, len(sesion.opciones or []))

    # El chat inicia como una conversación normal con contexto del registro de Pulse:
    # no manda de frente a elegir citas ni vuelca listas de opciones.
    if not any(m.get("role") == "user" for m in (chat or [])):
        sesion.historial = [h for h in sesion.historial if h.get("rol") == "user"]
        texto = pulso.abrir_chat(sesion)
        chat = [{"role": "assistant", "content": texto}]

    return (vistas.html_frase(resultado), vistas.html_mood_track(sesion),
            sesion, chat, aviso, gr.update(visible=bool(oferta)))


def _abrir_chat(sesion, chat, estilo_evento):
    """
    «Hablar con Ruta»: abre la conversación y saluda.

    La iniciativa es del estudiante. Inicia como un chat normal con contexto de lo
    que registró en Pulse (si registró hoy), sin adelantar opciones ni mandar a
    elegir turnos de frente.
    """
    import gradio as gr
    if sesion is None:
        gr.Warning("Un momento: todavía se está preparando la sesión.")
        return chat, sesion, "", "", gr.update(visible=False)
    sesion.estilo_evento = estilo_evento or "neutro"

    tiene_mensaje_usuario = any(m.get("role") == "user" for m in (chat or []))
    if not tiene_mensaje_usuario:
        if any(e["fecha"] == C.FECHA_DEMO for e in (sesion.mood_track or [])):
            sesion.historial = [h for h in sesion.historial if h.get("rol") == "user"]
            texto = pulso.abrir_chat(sesion)
        else:
            texto = ("Hola 👋 Soy Ruta, un asistente de IA de orientación (no clínica). "
                     "Cuéntame cómo has estado. Si algo te está pesando, lo vemos con calma y, "
                     "cuando lo tengamos claro, te busco un espacio que calce con tu horario. "
                     "Y si prefieres ir directo a los horarios, toca «Ver las citas disponibles».")
        chat = [{"role": "assistant", "content": texto}]
    return (chat, sesion, vistas.html_panel_traza(sesion), "",
            gr.update(visible=False))


def _ver_citas(sesion, chat):
    """
    Muestra las citas sin pasar por la conversación.

    Lo usan dos botones: la tarjeta que Ruta deja en Pulse y el atajo de la pestaña
    Ruta. Es la puerta de quien ya sabe que quiere horarios y no quiere contar antes
    qué le pasa.
    """
    import gradio as gr
    if sesion is None:
        gr.Warning("Un momento: todavía se está preparando la sesión.")
        return chat, sesion, "", ""
    texto, _ = agente.mostrar_citas(sesion)
    chat = (chat or []) + [{"role": "assistant", "content": texto}]
    return (chat, sesion, vistas.html_panel_traza(sesion), vistas.tabla_reservas_html())





def _borrar(sesion):
    import gradio as gr
    if sesion is None:
        gr.Warning("Todavía no hay nada que borrar.")
        return "", vistas.html_frase(), sesion, None
    pulso.borrar(sesion)
    gr.Info("Tu registro de Pulse fue borrado.")
    return vistas.html_mood_track(sesion), vistas.html_frase(), sesion, None


def _descargar(sesion):
    import gradio as gr
    if sesion is None or not sesion.mood_track:
        gr.Warning("Todavía no hay registros para descargar.")
        return None
    return pulso.exportar(sesion)





def _enviar(texto: str, sesion, chat):
    import gradio as gr
    if sesion is None:
        gr.Warning("Un momento: todavía se está preparando la sesión.")
        return "", chat, sesion, "", "", ""
    if not (texto or "").strip():
        return "", chat, sesion, vistas.html_panel_traza(sesion), vistas.tabla_reservas_html(), ""
    respuesta, _ = agente.procesar_mensaje(sesion, texto)
    chat = (chat or []) + [{"role": "user", "content": texto},
                           {"role": "assistant", "content": respuesta}]
    return ("", chat, sesion, vistas.html_panel_traza(sesion),
            vistas.tabla_reservas_html(), vistas.html_bienestar())


def _persona(sesion, chat):
    import gradio as gr
    if sesion is None:
        gr.Warning("Un momento: todavía se está preparando la sesión.")
        return chat, sesion, "", ""
    solicitud = agente.solicitar_contacto_humano(sesion, origen="botón")
    texto = agente.texto_contacto_humano(solicitud, sesion.perfil)
    sesion.historial.append({"rol": "ruta", "texto": texto})
    sesion.trazas.append({
        "turno": sesion.turnos, "mensaje": "(botón de contacto humano)",
        "guardrail_entrada": "permitido", "accion": "contacto_humano",
        "herramientas": ["contacto_humano"], "resultados": {"contacto_humano": solicitud},
        "derivacion_humana": True, "segundos": 0, "redaccion": "plantilla fija",
        "guardrail_salida": "ok"})
    chat = (chat or []) + [{"role": "assistant", "content": texto}]
    return chat, sesion, vistas.html_panel_traza(sesion), vistas.html_bienestar()


# ─────────────────────────────────────────────────────────────────────────────
# Construcción
# ─────────────────────────────────────────────────────────────────────────────
def construir():
    import gradio as gr

    tarjetas = tarjetas_demo()
    nombres = list(tarjetas)
    opciones_mood = [(f"{m['emoji']} {m['label']}", m["id"]) for m in pulso.MOODS]

    with gr.Blocks(title="Aethera Pulse + Ruta", analytics_enabled=False) as app:
        gr.HTML(vistas.ENCABEZADO)
        estado = gr.State()

        # ── Configuración de la demo ────────────────────────────────────────
        with gr.Accordion("Configuración de la demostración", open=True):
            with gr.Row():
                sel_perfil = gr.Dropdown(nombres, value=nombres[0],
                                         label="Estudiante sintético", scale=3)
                sel_fecha = gr.Dropdown(list(C.FECHAS_DEMO), value=list(C.FECHAS_DEMO)[0],
                                        label="Fecha simulada", scale=3)
                chk_historial = gr.Checkbox(value=True,
                                            label="Cargar historial de ejemplo", scale=2)
                btn_nueva = gr.Button("Nueva sesión", scale=1, variant="secondary")
            ficha = gr.HTML()

        with gr.Tabs(selected="pulse") as tabs:
            # ── Pulse ───────────────────────────────────────────────────────
            with gr.Tab("🌤️  Pulse", id="pulse"):
                with gr.Row(equal_height=False):
                    with gr.Column(scale=5, elem_classes="panel"):
                        gr.HTML(vistas.html_que_es_pulse())
                        consentimiento = gr.Checkbox(value=False, label=pulso.TEXTO_CONSENTIMIENTO)
                        aviso = gr.HTML()
                        mood = gr.Radio(opciones_mood, label="¿Cómo te sientes hoy?",
                                        elem_id="mood-radio")
                        temas = gr.CheckboxGroup(pulso.TEMAS,
                                                label="¿Qué está influyendo? (opcional)",
                                                elem_id="temas-pulse")
                        nota = gr.Textbox(label="Una línea para ti (opcional y privada)",
                                          max_lines=2, lines=2,
                                          placeholder="Ej.: dormí poco por las entregas")
                        with gr.Row():
                            btn_registrar = gr.Button("Registrar mi día", variant="primary",
                                                     elem_id="btn-registrar")
                            btn_hablar = gr.Button("💬  Hablar con Ruta", elem_id="btn-hablar")
                        frase = gr.HTML()
                        # Ruta escribe primero, pero desde la pestana Ruta. Si la
                        # oferta solo viviera en el chat, se registraria en otra
                        # pestana y el estudiante no se enteraria: se muestra aqui
                        # y se ofrece el salto.
                        aviso_ruta = gr.HTML()
                        btn_ir_ruta = gr.Button("📅  Ver las citas que me sirven",
                                                elem_id="btn-ir-ruta", visible=False)

                    with gr.Column(scale=6, elem_classes="panel"):
                        track = gr.HTML()
                        with gr.Accordion("Privacidad de la cita", open=False):
                            gr.HTML(vistas.html_estilo_evento())
                            estilo_evento = gr.Radio(
                                [(s["etiqueta"], s["clave"]) for s in vistas.ESTILOS_EVENTO],
                                value="neutro", label="Cómo quieres que aparezca en tu calendario",
                                info="No cambia la cita: cambia lo que ven los demás.")
                        with gr.Row():
                            btn_descargar = gr.Button("Descargar mi registro", size="sm")
                            btn_borrar = gr.Button("Borrar mi registro", size="sm", variant="stop")
                        archivo = gr.File(label="Tu registro (JSON)", visible=False)

            # ── Ruta ────────────────────────────────────────────────────────
            with gr.Tab("💬  Ruta", id="ruta"):
                with gr.Row(equal_height=False):
                    with gr.Column(scale=6, elem_classes="panel"):
                        gr.HTML(
                            f'<div class="titulo-seccion">Ruta</div>'
                            f'<p class="subtitulo">Asistente de IA de orientación '
                            f'<b>no clínica</b>. Te ayuda a entender qué apoyo calza con lo que '
                            f'te pasa, a conocer los servicios y a reservar o mover una cita. '
                            f'Si necesitas a una persona, toca el botón naranja.</p>')
                        chat = gr.Chatbot(height=460, label="Conversación con Ruta",
                                          elem_id="chatbot")
                        entrada = gr.Textbox(label="Mensaje",
                                             placeholder="Escribe como estudiante y pulsa Enter",
                                             elem_id="entrada")
                        btn_persona = gr.Button("🙋  Quiero que una persona me contacte",
                                                elem_id="btn-persona")
                        btn_citas = gr.Button("📅  Ver las citas disponibles",
                                              elem_id="btn-citas")
                        gr.Examples(
                            ["¿Qué apoyos hay en la universidad?",
                             "Trabajo todo el día y me siento solo en la U",
                             "Tengo muchas entregas y casi no duermo",
                             "Termino la carrera y no sé cómo conseguir prácticas",
                             "Me interesa una actividad con otros estudiantes",
                             "Prefiero algo virtual en la tarde",
                             "No puedo los sábados"],
                            inputs=entrada, label="Ideas para probar")

                    with gr.Column(scale=4, elem_classes="panel"):
                        with gr.Accordion("Cómo decidió Ruta", open=True):
                            panel = gr.HTML(elem_id="panel-traza")
                        gr.HTML(f'<div class="titulo-seccion" style="font-size:14px;margin-top:14px">'
                                f'Reservas de esta sesión</div>')
                        reservas = gr.HTML()

            # ── Bienestar ────────────────────────────────────────────────────
            with gr.Tab("🏛️  Bienestar", id="bienestar"):
                with gr.Column(elem_classes="panel"):
                    bienestar = gr.HTML()
                    btn_actualizar = gr.Button("Actualizar vista", size="sm")

        gr.HTML(
            f'<div class="footer-nota">Aethera es una ciudad universitaria <b>ficticia</b>. '
            f'Todos los datos son sintéticos del Data Pack de la organización y no corresponden '
            f'a personas, lugares ni servicios reales.<br>'
            f'orientación no clínica: no diagnostica, no receta y no atiende emergencias · '
            f'proveedor de IA: <code>{C.PROVEEDOR}</code> · modelo: <code>{C.MODELO}</code></div>')

        # ── Conexiones ───────────────────────────────────────────────────────
        salidas = [estado, chat, ficha, track, frase, panel, reservas, bienestar, archivo, mood,
                   aviso_ruta, btn_ir_ruta, aviso]
        entradas = [sel_perfil, sel_fecha, chk_historial]

        def _init(nombre, fecha, hist):
            sesion, chat0, ficha_html, track_html, frase_html, panel_html, \
                reservas_html, bien_html, archivo_out, _ = _reiniciar(nombre, fecha, hist)
            return (sesion, chat0, ficha_html, track_html, frase_html, panel_html,
                    reservas_html, bien_html, archivo_out, None, "",
                    gr.update(visible=False), vistas.html_aviso())

        app.load(_init, entradas, salidas)
        for control in (sel_perfil, sel_fecha, chk_historial):
            control.change(_init, entradas, salidas)
        btn_nueva.click(_init, entradas, salidas)

        consentimiento.input(_consentir, [consentimiento, chk_historial, estado],
                             [track, frase, estado])
        btn_registrar.click(_registrar, [mood, temas, nota, estado, estilo_evento, chat],
                            [frase, track, estado, chat, aviso_ruta, btn_ir_ruta])
        btn_hablar.click(_abrir_chat, [estado, chat, estilo_evento],
                         [chat, estado, panel, aviso_ruta, btn_ir_ruta],
                         js=IR_A_RUTA_JS)
        btn_ir_ruta.click(_ver_citas, [estado, chat], [chat, estado, panel, reservas],
                          js=IR_A_RUTA_JS)
        btn_citas.click(_ver_citas, [estado, chat], [chat, estado, panel, reservas])
        btn_borrar.click(_borrar, [estado], [track, frase, estado, archivo])
        btn_descargar.click(_descargar, [estado], [archivo])
        entrada.submit(_enviar, [entrada, estado, chat],
                       [entrada, chat, estado, panel, reservas, bienestar])
        btn_persona.click(_persona, [estado, chat], [chat, estado, panel, bienestar])
        btn_actualizar.click(lambda: vistas.html_bienestar(), None, [bienestar])

    return app


def lanzar():
    app = construir()
    if LANZAR:
        app.launch(theme=tema(), css=vistas.CSS, js=FORZAR_TEMA_CLARO, share=COMPARTIR)
    return app
