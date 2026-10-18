"""
Aethera · interfaz (Gradio).

Criterio de diseño: esto NO es un chatbot genérico con tres pestañas pegadas.
Es una pieza de universidad tranquila. Tres superficies con reglas distintas:

  PULSE      → cálida y privada. El mes en colores es el protagonista.
  RUTA       → conversacional, pero con el razonamiento a la vista. En salud
               mental, un sistema que no explica por qué hace lo que hace
               genera desconfianza; por eso el panel de trazabilidad no es
               decoración, es el producto.
  BIENESTAR  → un tablero profesional, sin una sola nota individual.
"""
from __future__ import annotations

from datetime import timedelta

from . import agente, calendario, config as C, datos, horarios, pulso, servicios
from . import bienestar as bst
from .segmentos import segmentacion, tarjetas_demo

# ─────────────────────────────────────────────────────────────────────────────
# Sistema visual
# ─────────────────────────────────────────────────────────────────────────────
TINTA = "#14213D"      # texto principal
PETROLEO = "#0E7C86"   # primario
PETROLEO_OSC = "#0A5F68"
CANVAS = "#F4F7FA"
SUPERFICIE = "#FFFFFF"
BORDE = "#E1E8F0"
TEXTO_SUAVE = "#5B6B80"
ALERTA = "#C0534F"
EXITO = "#2E8B6F"

# Estilos de la entrada de calendario. El estudiante elige cuánto se ve.
# Fuente única: la usan el selector de la interfaz y la tabla de reservas.
ESTILOS_EVENTO = [
    {"clave": "neutro", "etiqueta": "🔒 Neutro — «Cita campus»",
     "ejemplo": "Cita campus · Edificio Norte",
     "nota": "Lo verás con todos los detalles dentro de la aplicación. Fuera de ella, "
             "solo aparece como cita en el campus."},
    {"clave": "servicio", "etiqueta": "Equilibrado — nombre del servicio",
     "ejemplo": "Espacio Lumen · Edificio Norte",
     "nota": "Quien vea tu calendario sabrá a qué servicio acudes, pero no el motivo."},
    {"clave": "completo", "etiqueta": "Completo — servicio y lugar",
     "ejemplo": "Espacio Lumen · Orientación emocional",
     "nota": "Sin ocultamiento. Es la opción con más exposición."},
]

CSS = f"""
:root {{
  --tinta: {TINTA}; --primario: {PETROLEO}; --primario-osc: {PETROLEO_OSC};
  --canvas: {CANVAS}; --superficie: {SUPERFICIE}; --borde: {BORDE};
  --suave: {TEXTO_SUAVE}; --alerta: {ALERTA}; --exito: {EXITO};
  --radio: 16px; --sombra: 0 1px 2px rgba(20,33,61,.05), 0 4px 16px rgba(20,33,61,.05);
}}
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Inter:wght@400;500;600;700&display=swap');

.gradio-container {{
  max-width: 1280px !important; margin: 0 auto !important;
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
  background: var(--canvas) !important;
}}

/* ── Encabezado ───────────────────────────────────────────────── */
#encabezado {{ display:flex; justify-content:space-between; align-items:center;
  gap:20px; padding: 22px 4px 18px; flex-wrap:wrap; }}
#encabezado h1 {{ font-family:'Bricolage Grotesque',sans-serif !important;
  font-weight:800 !important; font-size:32px !important; margin:0 !important;
  color:var(--tinta); letter-spacing:-.6px; line-height:1.1; }}
#encabezado .sub {{ margin:6px 0 0; color:var(--suave); font-size:14.5px; max-width:64ch; line-height:1.5; }}
#marca {{ display:flex; align-items:center; gap:10px; }}

/* ── Tarjetas ─────────────────────────────────────────────────── */
.panel {{ background:var(--superficie) !important; border:1px solid var(--borde) !important;
  border-radius: var(--radio) !important; padding:20px !important; box-shadow:var(--sombra); }}
.titulo-seccion {{ font-family:'Bricolage Grotesque',sans-serif !important;
  font-weight:800 !important; font-size:17px !important; color:var(--tinta);
  display:flex; align-items:center; gap:8px; margin:0 0 4px; }}
.subtitulo {{ font-size:13px; color:var(--suave); margin:0 0 14px; line-height:1.5; }}
.separador {{ height:1px; background:var(--borde); margin:16px 0; border:0; }}

/* ── Selector de ánimo ────────────────────────────────────────── */
#mood-radio .wrap {{ display:grid !important; grid-template-columns:repeat(5,1fr);
  gap:8px; }}
#mood-radio label {{ justify-content:center !important; align-items:center !important;
  text-align:center; padding:14px 6px !important; border-radius:14px !important;
  border:1.5px solid var(--borde) !important; background:#FAFCFD !important;
  transition:all .16s ease !important; cursor:pointer; }}
#mood-radio label:hover {{ border-color:var(--primario) !important; transform:translateY(-2px); }}
#mood-radio label input {{ position:absolute; opacity:0; pointer-events:none; }}
#mood-radio label span {{ display:block; white-space:pre-line; line-height:1.2 !important;
  font-size:12.5px !important; font-weight:500 !important; color:var(--suave); }}
#mood-radio label span::first-line {{ font-size:28px; }}
#mood-radio label.selected, #mood-radio label:has(input:checked) {{
  background:var(--primario) !important; border-color:var(--primario) !important;
  transform:translateY(-2px); box-shadow:0 6px 18px rgba(14,124,134,.25); }}
#mood-radio label.selected span, #mood-radio label:has(input:checked) span {{
  color:#fff !important; }}
#mood-radio label:focus-within {{ outline:3px solid #8ED0D6; outline-offset:2px; }}
#temas-pulse label {{ border-radius:999px !important; font-size:13px !important; }}

/* ── Botones ──────────────────────────────────────────────────── */
#btn-registrar, #btn-hablar {{ border-radius:12px !important; font-weight:600 !important;
  height:44px !important; }}
#btn-persona {{ background:#FFF7EC !important; border:1.5px solid #F0C89A !important;
  color:#8A5416 !important; border-radius:12px !important; font-weight:600 !important; }}
#btn-ayuda {{ font-size:12.5px !important; }}

/* ── Pestañas ─────────────────────────────────────────────────── */
.tabs > .tab-nav {{ background:var(--superficie); border:1px solid var(--borde);
  border-radius:14px; padding:5px; margin-bottom:16px; }}
.tabs > .tab-nav button {{ border-radius:10px !important; font-weight:600 !important;
  font-size:14px !important; padding:9px 16px !important; color:var(--suave); }}
.tabs > .tab-nav button.selected {{ background:var(--primario) !important; color:#fff !important; }}

/* ── Chat ─────────────────────────────────────────────────────── */
#chatbot {{ border-radius:14px !important; border:1px solid var(--borde) !important; }}
.chatbot {{ font-size:14.5px !important; line-height:1.6; }}
#panel-traza {{ font-size:13px !important; line-height:1.65; }}

/* ── Acordeones ───────────────────────────────────────────────── -->
details, .gr-box {{ border-radius:12px !important; }}
.gr-accordion {{ border:1px solid var(--borde) !important; border-radius:14px !important;
  background:var(--superficie); box-shadow:none !important; }}

.footer-nota {{ font-size:11.5px; color:var(--suave); line-height:1.55; text-align:center;
  padding:24px 8px 8px; }}

@media (max-width: 720px) {{
  #encabezado {{ flex-direction:column; align-items:flex-start; }}
  #mood-radio .wrap {{ grid-template-columns:repeat(3,1fr); }}
  #encabezado h1 {{ font-size:26px !important; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Piezas HTML
# ─────────────────────────────────────────────────────────────────────────────
ENCABEZADO = f"""
<div id="encabezado">
  <div>
    <div style="display:flex;align-items:center;gap:9px;margin-bottom:10px">
      <span style="font-size:22px">🌤️</span>
      <span style="font-family:'Bricolage Grotesque',sans-serif;font-weight:800;
        font-size:12px;letter-spacing:1.6px;text-transform:uppercase;color:{PETROLEO}">
        Aethera · UNI_NOVA_AETHER</span>
    </div>
    <h1>Aethera Pulse + Ruta</h1>
    <p class="sub">Registra cómo te sientes en 20 segundos y, si quieres, encuentra un espacio
      de apoyo que <b>realmente puedas usar</b>: Ruta solo propone citas que no chocan con tus
      clases ni con tu trabajo.</p>
  </div>
  <svg width="170" height="46" viewBox="0 0 170 46" aria-hidden="true" style="flex-shrink:0">
    <circle cx="126" cy="17" r="8" fill="#F0B96B"/>
    <polyline points="0,44 26,24 44,33 70,9 95,30 112,21 140,37 154,28 170,44"
      fill="none" stroke="{PETROLEO}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
  </svg>
</div>"""


def _tile(titulo: str, valor: str, sub: str = "", color: str = PETROLEO) -> str:
    return (f'<div style="padding:14px 16px;border-radius:14px;background:#FAFCFD;'
            f'border:1px solid {BORDE}">'
            f'<div style="font-size:11.5px;font-weight:600;letter-spacing:.3px;color:{TEXTO_SUAVE};'
            f'text-transform:uppercase">{titulo}</div>'
            f'<div style="font-size:26px;font-weight:800;color:{color};line-height:1.25;'
            f'margin:2px 0 1px">{valor}</div>'
            f'<div style="font-size:11.5px;color:{TEXTO_SUAVE};line-height:1.45">{sub}</div></div>')


def html_que_es_pulse() -> str:
    pasos = [
        ("①", "Marca", "cómo te sientes y qué está influyendo. Sin preguntas raras."),
        ("②", "Mira", "tu mes en colores. Si ves un patrón, ya no es una sensación."),
        ("③", "Elige", "si quieres, converse con Ruta y encuentra apoyo a tu medida."),
    ]
    celdas = "".join(
        f'<div style="padding:14px;border-radius:14px;background:#FAFCFD;border:1px solid {BORDE}">'
        f'<div style="font-size:19px;font-weight:800;color:{PETROLEO}">{n}</div>'
        f'<div style="font-size:13.5px;font-weight:700;color:{TINTA};margin:2px 0 3px">{t}</div>'
        f'<div style="font-size:12.5px;color:{TEXTO_SUAVE};line-height:1.5">{d}</div></div>'
        for n, t, d in pasos)
    return f"""
    <div class="titulo-seccion">¿Qué es Pulse?</div>
    <p class="subtitulo">Tu diario de ánimo de 20 segundos. No es un test, no tiene
      respuestas correctas y no calcula puntajes. Es una forma simple de notar cómo vas
      y pedir apoyo a tiempo.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">
      {celdas}</div>"""


def html_aviso() -> str:
    a = calendario.aviso_general()
    if not a:
        return ""
    return (f'<div style="display:flex;gap:12px;align-items:flex-start;padding:12px 15px;'
            f'border-radius:14px;background:rgba(14,124,134,.08);'
            f'border:1px solid rgba(14,124,134,.22)">'
            f'<div style="font-size:19px;line-height:1.2">{a["icono"]}</div>'
            f'<div style="flex:1"><div style="font-size:13.5px;color:{TINTA};line-height:1.5">'
            f'{a["texto"]}</div>'
            f'<div style="font-size:11px;color:{TEXTO_SUAVE};margin-top:3px">'
            f'Aviso general para toda la comunidad · no se basa en tus datos</div></div></div>')


def html_mood_track(sesion) -> str:
    if not sesion.consentimiento_pulse:
        return (f'<div style="padding:30px 20px;border-radius:14px;border:1.5px dashed {BORDE};'
                f'text-align:center;background:#FAFCFD">'
                f'<div style="font-size:30px">🌤️</div>'
                f'<div style="font-family:\'Bricolage Grotesque\',sans-serif;font-weight:800;'
                f'font-size:15px;color:{TINTA};margin-top:6px">Tu mes en colores aparecerá aquí</div>'
                f'<div style="font-size:12.5px;color:{TEXTO_SUAVE};margin-top:4px">'
                f'Activa Pulse aceptando el aviso de privacidad.</div></div>')

    fin = pulso.fecha_hoy()
    por_fecha = {e["fecha"]: e for e in sesion.mood_track}
    inicio = fin - timedelta(days=pulso.DIAS_TRACK - 1)
    d = inicio - timedelta(days=inicio.weekday())      # alinear a lunes

    filas = []
    while d <= fin:
        celdas, valores = [], []
        for _ in range(7):
            if d < inicio or d > fin:
                celdas.append('<div></div>')
            else:
                e = por_fecha.get(d.isoformat())
                m = pulso.MOOD[e["mood"]] if e else None
                if e:
                    valores.append(e["valor"])
                fondo = f"{m['color']}33" if m else "#FAFCFD"
                borde = f"2px solid {PETROLEO}" if d == fin else f"1px solid {BORDE}"
                titulo = (f"{d.isoformat()} · {m['label']}"
                          + (f" · {', '.join(e['temas'])}" if e["temas"] else "")
                          + (" (ejemplo)" if e.get("ejemplo") else "")) if e \
                    else f"{d.isoformat()} · sin registro"
                celdas.append(
                    f'<div title="{titulo}" style="background:{fondo};border:{borde};'
                    f'border-radius:10px;padding:5px 0;text-align:center;min-height:40px">'
                    f'<div style="font-size:17px;line-height:1.15">{m["emoji"] if m else "·"}</div>'
                    f'<div style="font-size:9.5px;color:{TEXTO_SUAVE};margin-top:1px">{d.day}</div>'
                    f'</div>')
            d += timedelta(days=1)
        media = f"{sum(valores)/len(valores):.1f}" if valores else "—"
        filas.append("".join(celdas) +
                     f'<div style="font-size:11px;color:{TEXTO_SUAVE};align-self:center;'
                     f'text-align:center;font-weight:600">{media}</div>')

    r = pulso.resumen(sesion)
    tend = {"baja": "↘ bajando", "sube": "↗ mejorando",
            "estable": "→ estable", None: "—"}[r["tendencia"]]
    chips = ("".join(f'<span style="display:inline-block;padding:3px 11px;margin:3px 3px 0 0;'
                     f'border-radius:999px;background:rgba(14,124,134,.13);font-size:12px;'
                     f'color:{TINTA}">{t}</span>' for t in r["temas_frecuentes"])
             or f'<span style="color:{TEXTO_SUAVE};font-size:12.5px">Sin temas aún</span>')
    leyenda = " ".join(f'<span style="font-size:12px;color:{TEXTO_SUAVE};white-space:nowrap;'
                      f'margin-right:10px">{m["emoji"]} {m["label"]}</span>' for m in pulso.MOODS)
    # Encabezado de la grilla. Debe construirse concatenando celdas completas:
    # cualquier otra forma deja etiquetas sin cerrar y el navegador colapsa la
    # grilla en una sola columna.
    etiqueta_dia = (f'<div style="font-size:10.5px;color:{TEXTO_SUAVE};'
                    f'text-align:center;font-weight:600">%s</div>')
    cabecera = "".join(etiqueta_dia % d
                       for d in ["lu", "ma", "mi", "ju", "vi", "sá", "do"])
    cabecera += (f'<div style="font-size:10px;color:{TEXTO_SUAVE};'
                 f'text-align:center;font-weight:600">prom.</div>')

    alerta = ""
    if r["patron_dias_pesados"]:
        alerta = (f'<div style="margin-top:12px;padding:12px 14px;border-radius:12px;'
                  f'background:rgba(192,83,79,.10);border:1px solid rgba(192,83,79,.25);'
                  f'font-size:13px;color:{TINTA};line-height:1.5">Marcaste varios días pesados esta '
                  f'semana. Si quieres, Ruta puede ayudarte a encontrar un espacio de apoyo que '
                  f'calce con tu horario.</div>')

    stats = "".join(_tile(t, v, s) for t, v, s in [
        ("Días registrados", f"{r['dias_registrados_28d']}", "en los últimos 28 días"),
        ("Promedio del mes", f"{r['promedio_28d'] or '—'}", "de 5 puntos"),
        ("Días pesados (7 d)", f"{r['dias_pesados_7d']}", "ánimo bajo"),
        ("Tendencia", tend, "últimos 7 días vs. anteriores"),
    ])

    return f"""
    <div style="display:flex;justify-content:space-between;align-items:baseline;
      flex-wrap:wrap;gap:8px;margin-bottom:12px">
      <div class="titulo-seccion" style="margin:0">Mi mes en Pulse</div>
      <div style="font-size:12px;color:{TEXTO_SUAVE}">{pulso.fecha_hoy().day} de
        {C.MESES_ES[pulso.fecha_hoy().month-1]} · ventana de 28 días</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(7,minmax(0,1fr)) 40px;gap:5px">
      {cabecera}{''.join(filas)}
    </div>
    <hr class="separador">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:9px">
      {stats}</div>
    <div style="margin-top:12px;font-size:12.5px;color:{TEXTO_SUAVE}">Temas de la semana: {chips}</div>
    {alerta}
    <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:2px">{leyenda}</div>
    <div style="margin-top:10px;font-size:11px;color:{TEXTO_SUAVE};line-height:1.5">
      🔒 Solo tú ves este registro. Ruta lo usa únicamente si eliges conversar.
      Los días marcados como ejemplo son sintéticos.</div>"""


def html_frase(resultado: dict | None = None) -> str:
    if not resultado:
        return (f'<div style="padding:16px 18px;border-radius:14px;border:1.5px dashed {BORDE};'
                f'background:#FAFCFD;color:{TEXTO_SUAVE};font-size:13.5px">'
                f'Elige cómo te sientes hoy y toca <b>Registrar mi día</b>.</div>')
    if "error" in resultado:
        return (f'<div style="padding:14px 16px;border-radius:14px;'
                f'background:rgba(240,185,107,.18);border:1px solid rgba(240,185,107,.4);'
                f'font-size:13.5px;color:{TINTA}">🔒 {resultado["error"]}</div>')

    m = pulso.MOOD[resultado["entrada"]["mood"]]
    color = ALERTA if resultado["crisis"] else m["color"]
    pie = ("" if resultado["crisis"]
           else ('Si quieres, toca <b>💬 Hablar con Ruta</b>.' if resultado["sugerir_chat"]
                 else "Puedes volver mañana a registrar tu día."))
    return f"""
    <div style="padding:18px 20px;border-radius:14px;background:{color}18;
      border:1px solid {color}55">
      <div style="font-size:32px;line-height:1">{m['emoji']}</div>
      <div style="font-size:15.5px;margin-top:8px;line-height:1.5;color:{TINTA}">
        {resultado['frase'].replace(chr(10), '<br>')}</div>
      <div style="font-size:12px;color:{TEXTO_SUAVE};margin-top:10px">{pie}</div>
    </div>"""


def html_ficha_perfil(nombre: str) -> str:
    p = tarjetas_demo()[nombre]
    etiquetas = {"day": "Diurno", "evening": "Nocturno"}
    trabajo = {"not_working": "no trabaja", "part_time": "medio tiempo",
               "full_time": "tiempo completo"}.get(p["employment_status"], "")
    return f"""
    <div style="padding:14px 16px;border-radius:14px;background:#FAFCFD;border:1px solid {BORDE}">
      <div style="font-size:13.5px;font-weight:700;color:{TINTA}">{nombre}</div>
      <div style="font-size:12.5px;color:{TEXTO_SUAVE};margin-top:4px;line-height:1.6">
        <code style="font-size:11.5px;background:{BORDE};padding:1px 6px;border-radius:5px">
          {p['student_id']}</code> · {etiquetas.get(p['study_mode'], '?')}, {trabajo}
        · {p['district_id'].replace('DIST_', '')} · {p['country_context']}<br>
        <b style="color:{TINTA}">Ocupado:</b> {p['horario']}<br>
        <b style="color:{TINTA}">Libre:</b> {' · '.join(p['fronteras']['ventanas_libres'])}
        {f" · {p['creditos']:.0f} créditos en D3" if p['creditos'] else ''}
      </div>
      <div style="font-size:11px;color:{TEXTO_SUAVE};margin-top:8px;padding-top:8px;
        border-top:1px solid {BORDE}">
        Fila real de D1 dentro del segmento prioritario de M5.
        Ruta no recibe ni usa el nivel de ansiedad ni ningún puntaje.</div>
    </div>"""


def html_panel_traza(sesion) -> str:
    if sesion is None or not sesion.trazas:
        return (f'<div style="color:{TEXTO_SUAVE};font-size:13px;padding:12px 0">'
                f'_Aún no hay turnos. Escribe un mensaje o abre el chat desde Pulse._</div>')
    t = sesion.trazas[-1]
    L = [f"**Turno {t['turno']}** · {t['segundos']} s",
         f"- 🛡️ **Entrada** · `{t['guardrail_entrada']}`"]
    # El metodo solo existe si el planificador intervino: un turno proactivo no
    # pasa por el LLM, y el panel debe decirlo en vez de romper la vista.
    metodo = (t.get("plan") or {}).get("metodo")
    if metodo:
        L.append(f"- 🧭 **Acción** · `{t['accion']}` _(decidida por {metodo})_")
    elif t.get("plan"):
        L.append(f"- 🧭 **Acción** · `{t['accion']}` _(regla, sin LLM)_")
    else:
        L.append(f"- 🧭 **Acción** · `{t['accion']}`")

    res = t.get("resultados", {})
    if "clasificar" in res:
        c = res["clasificar"]
        # reason_code y confianza los aporta el LLM; el disparador proactivo
        # decide el motivo por regla, asi que se muestran solo si existen.
        if c.get("reason_code"):
            L.append(f"- 🏷️ **Necesidad** · `{c['reason_code']}` "
                     f"(confianza {c.get('confianza', 0):.2f}, vía {c.get('metodo', 'regla')})")
        else:
            L.append(f"- 🏷️ **Necesidad** · `{c.get('etiqueta', 'sin clasificar')}` "
                     f"_(elegida por regla)_")
    if "evento_relevante" in res.get("consultar_calendario", {}):
        e = res["consultar_calendario"]["evento_relevante"]
        L.append(f"- 📅 **D7** · {e['titulo']} ({e['desde']})" if e
                 else "- 📅 **D7** · sin evento pertinente, no se menciona")
    elif t.get("disparador"):
        L.append(f"- 📅 **D7** · {t['disparador']}")
    if "voces" in res:
        v = res["voces"]
        L.append(f"- 🗣️ **D4 agregado** · {v['proporcion']:.0%} de {v['relatos_nova']:,} "
                 f"relatos de NOVA · frase de normalización")
    if "catalogo" in res:
        L.append(f"- 📚 **D6** · {len(res['catalogo'])} tipos de servicio en contexto")

    ops = res.get("proponer_opciones") or res.get("replanificar")
    if ops:
        L.append(f"- 🗂️ **Propuesta** · {len(ops['opciones'])} opciones · "
                 f"tipo principal {ops['tipo_principal']}")
        for o in ops["opciones"]:
            puente = " · <i>puente pares</i>" if o["es_puente_pares"] else ""
            conf = "" if o["confianza_ml"] >= 0.6 else f" · <i>conf. ML {o['confianza_ml']}</i>"
            L.append(f"  - **{o['opcion']}.** {o['dia']} {o['hora']} · {o['servicio']} "
                     f"({o['canal']}) · P(asistir) {o['p_asistencia']:.2f}{conf}{puente}")
    if "reservar" in res and res["reservar"]["ok"]:
        r = res["reservar"]["reserva"]
        L.append(f"- ✅ **Reserva** {r['reserva_id']} · P(asistir) {r['p_asistencia']:.2f} · "
                 f"recordatorios: {', '.join(r['recordatorios'])}")
    if "contacto_humano" in res:
        s = res["contacto_humano"]
        L.append(f"- 🙋 **Contacto humano** · {s['solicitud']} · prioridad {s['prioridad']}")
    if "redaccion" in t:
        L.append(f"- ✍️ **Redacción** · {t['redaccion']} · salida `{t['guardrail_salida']}`")
    if t.get("derivacion_humana"):
        L.append("- 👥 **Derivación o seguimiento humano registrado**")
    return "\n".join(L)


def html_estilo_evento() -> str:
    """Explicación del control de privacidad de la cita."""
    filas = "".join(
        f'<tr style="border-bottom:1px solid {BORDE}">'
        f'<td style="padding:8px 6px;font-size:12.5px;font-weight:600;color:{PETROLEO};'
        f'white-space:nowrap">{s["etiqueta"]}</td>'
        f'<td style="padding:8px 6px;font-size:12.5px;color:{TEXTO_SUAVE}">{s["nota"]}</td>'
        f'</tr>' for s in ESTILOS_EVENTO)
    return f"""
    <div class="subtitulo" style="margin-bottom:8px">
      Tu cita aparece en tu calendario con el título que elijas aquí. Dentro de la
      aplicación siempre ves el detalle completo: el nombre neutro solo cambia lo
      que un tercero alcanza a leer.</div>
    <table style="border-collapse:collapse;width:100%">
      <tr style="border-bottom:2px solid {BORDE}">
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Cómo se ve</th>
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Qué implica</th></tr>
      {filas}</table>"""


def tabla_reservas_html() -> str:
    from .agente import _RESERVAS
    if not _RESERVAS:
        return (f'<div style="color:{TEXTO_SUAVE};font-size:13px;padding:10px 0">'
                f'_Sin reservas todavía._</div>')
    filas = "".join(
        f'<tr style="border-bottom:1px solid {BORDE}">'
        f'<td style="padding:8px 6px;font-size:12.5px;font-weight:600;color:{PETROLEO}">'
        f'{r["reserva_id"]}</td>'
        f'<td style="padding:8px 6px;font-size:12.5px">{r["dia"]} {r["fecha"]}</td>'
        f'<td style="padding:8px 6px;font-size:12.5px">{r["hora"]}</td>'
        f'<td style="padding:8px 6px;font-size:12.5px">{r["servicio"]}</td>'
        f'<td style="padding:8px 6px;font-size:12.5px">'
        f'<code style="font-size:11.5px;background:{CANVAS};padding:2px 6px;'
        f'border-radius:6px">{r.get("evento_titulo", r["servicio"])}</code></td>'
        f'<td style="padding:8px 6px;font-size:12.5px">{r["canal"]}</td></tr>'
        for r in _RESERVAS)
    return f"""
    <table style="border-collapse:collapse;width:100%;margin-top:4px">
      <tr style="border-bottom:2px solid {BORDE}">
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Cód.</th>
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Día</th>
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Hora</th>
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Servicio</th>
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">En tu calendario</th>
        <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE};
          text-transform:uppercase;letter-spacing:.4px">Canal</th></tr>
      {filas}</table>"""


def html_bienestar() -> str:
    ctx = bst.filas_para_html()
    n = ctx["n_conversaciones"]
    k_min = C.K_MINIMO

    cuerpo, recomendacion = "", ""
    if n == 0:
        cuerpo = (f'<div style="color:{TEXTO_SUAVE};font-size:13.5px;padding:14px 0">'
                  f'No hay conversaciones de D5 en los últimos 14 días para esta fecha simulada.</div>')
    else:
        por_motivo = ctx["por_motivo"]
        maximo = por_motivo.max()
        barras = "".join(
            f'<div style="display:grid;grid-template-columns:132px 1fr 52px;gap:10px;'
            f'align-items:center;margin:6px 0">'
            f'<div style="font-size:12.5px;color:{TINTA}">{C.MOTIVO_CORTO[m]}</div>'
            f'<div style="height:10px;border-radius:999px;background:#EDF2F6">'
            f'<div style="height:10px;border-radius:999px;width:{(c/maximo*100) if c>=k_min else 0:.0f}%;'
            f'background:{PETROLEO}"></div></div>'
            f'<div style="font-size:12px;text-align:right;color:{TEXTO_SUAVE};'
            f'font-weight:600">{bst._celda(c)}</div></div>'
            for m, c in por_motivo.items())

        tabla = ctx["cruzada"]
        vmax = max(1, int(tabla.values.max()))
        enc = "".join(f'<th style="padding:7px 6px;font-size:11px;color:{TEXTO_SUAVE};'
                      f'font-weight:600">{f}</th>' for f in tabla.columns)
        filas = "".join(
            f'<tr><td style="padding:7px 6px;font-size:12.5px;color:{TINTA}">'
            f'{C.MOTIVO_CORTO[m]}</td>'
            + "".join(f'<td style="padding:7px 6px;text-align:center;font-size:12.5px;'
                      f'background:rgba(14,124,134,{0 if c<k_min else min(.42, c/vmax*.42):.2f});'
                      f'border-radius:4px">{bst._celda(c)}</td>' for c in fila)
            + "</tr>" for m, fila in tabla.iterrows())

        cuerpo = f"""
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));
          gap:10px;margin-top:14px">
          {_tile("Conversaciones · 14 días", f"{n:,}".replace(",", "."), "línea de orientación · D5")}
          {_tile("Fuera de lun–vie 9–18 h", f"{ctx['fuera_horario']:.0%}",
                 "cuando orientación está cerrada", ALERTA if ctx["fuera_horario"] > .5 else PETROLEO)}
          {_tile("Llega de noche", f"{ctx['noche']:.0%}", "entre 18:00 y 06:00")}
          {_tile("Motivo más frecuente", ctx["motivo_top"][0], f"{ctx['motivo_top'][1]:.0%} de los contactos")}
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
          gap:22px;margin-top:20px">
          <div>
            <div class="titulo-seccion" style="font-size:14px">Demanda por motivo</div>
            <div class="subtitulo" style="margin-bottom:8px">Barras suprimidas bajo n={k_min}.</div>
            {barras}
          </div>
          <div>
            <div class="titulo-seccion" style="font-size:14px">Motivo × franja horaria</div>
            <div class="subtitulo" style="margin-bottom:8px">
              Celdas con menos de {k_min} personas se ocultan.</div>
            <table style="border-collapse:separate;border-spacing:3px;width:100%">
              <tr><th></th>{enc}</tr>{filas}</table>
          </div>
        </div>"""

        recomendacion = (
            f'<div style="margin-top:18px;padding:14px 16px;border-radius:14px;'
            f'background:rgba(46,139,111,.10);border:1px solid rgba(46,139,111,.28);'
            f'font-size:13.5px;color:{TINTA};line-height:1.55">'
            f'💡 <b>Sugerencia para Bienestar.</b> {ctx["noche"]:.0%} de los contactos llega entre '
            f'las 18:00 y las 06:00, pero orientación y trayectoria cierran a las 18:00 y pares a '
            f'las 20:00. Considerar turnos virtuales de orientación nocturnos.</div>')

    pulse_n = sum(1 for e in agente.EVENTOS if e["evento"] == "checkin_iniciado")
    pulse_txt = (f"<b>{pulse_n}</b> registros de ánimo → <b>ocultos</b> (menos de {k_min})"
                 if pulse_n < k_min
                 else f"<b>{pulse_n}</b> registros de ánimo · solo conteos agregados")

    ml = ctx["fila_ml"]
    nota_ml = (f'<span style="color:{TEXTO_SUAVE}">AUC {ml["auc"]:.3f} · '
               f'línea base {ml["tasa_base"]:.0%} de asistencia · '
               f'{ml["n_eventos"]:,} eventos</span>')

    from . import agente as _ag
    pendientes = [s for s in _ag.SOLICITUDES_CONTACTO if s["estado"] == "pendiente"]
    if pendientes:
        filas_cola = "".join(
            f'<tr style="border-bottom:1px solid {BORDE}">'
            f'<td style="padding:8px 6px;font-size:12.5px;font-weight:600;color:{PETROLEO}">'
            f'{s["solicitud"]}</td>'
            f'<td style="padding:8px 6px;font-size:12px;color:{TEXTO_SUAVE}">{s["student_id"]}</td>'
            f'<td style="padding:8px 6px;font-size:12px">'
            f'{"🔴 alta" if s["prioridad"]=="alta" else "🟢 normal"}</td>'
            f'<td style="padding:8px 6px;font-size:12.5px">'
            f'{C.MOTIVO_CORTO.get(s["motivo_no_clinico"], "sin clasificar")}</td>'
            f'<td style="padding:8px 6px;font-size:12px;color:{TEXTO_SUAVE}">{s["origen"]}</td></tr>'
            for s in pendientes)
        cola = f"""
        <table style="border-collapse:collapse;width:100%;margin-top:6px">
          <tr style="border-bottom:2px solid {BORDE}">
            <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE}">Pedido</th>
            <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE}">Estudiante</th>
            <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE}">Prioridad</th>
            <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE}">Tipo de apoyo</th>
            <th style="text-align:left;padding:6px;font-size:11px;color:{TEXTO_SUAVE}">Origen</th>
          </tr>{filas_cola}</table>"""
    else:
        cola = (f'<div style="color:{TEXTO_SUAVE};font-size:13px;padding:8px 0">'
                f'Sin pedidos pendientes.</div>')

    kpis = ctx["kpis"]
    if kpis:
        tiles = []
        for k in kpis:
            v = k["valor"]
            if v is None:
                valor = "—"
            elif k["formato"] == "dias":
                valor = f"{v:.0f} d"
            else:
                valor = f"{v:.0%}"
            sub = (f"{k['texto']} · {k['detalle']}" if k["formato"] != "pct" or v is None
                   else f"{k['texto']} · {k['detalle']}")
            tiles.append(_tile(k["nombre"], valor, sub))
        html_kpis = (f'<div style="display:grid;grid-template-columns:'
                     f'repeat(auto-fit,minmax(160px,1fr));gap:9px;margin-top:12px">'
                     f'{"".join(tiles)}</div>')
    else:
        html_kpis = (f'<div style="color:{TEXTO_SUAVE};font-size:13px;padding:8px 0">'
                     f'Aún no hay actividad en esta demo. Usa Pulse y Ruta y vuelve aquí: '
                     f'los indicadores se recalculan con lo que hagas.</div>')

    return f"""
    <div class="titulo-seccion">Bienestar · vista agregada</div>
    <p class="subtitulo">Solo totales. Ninguna celda muestra grupos de menos de
      {k_min} personas. No incluye ánimos, notas ni conversaciones individuales.</p>
    {cuerpo}{recomendacion}

    <hr class="separador">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px">
      <div>
        <div class="titulo-seccion" style="font-size:14px">Modelo de asistencia</div>
        <div style="font-size:12.5px;color:{TEXTO_SUAVE};line-height:1.6;margin-top:6px">
          {ml['modelo']} sobre D2 · {nota_ml}<br>
          En la franja que ofrece la demo (esperas ≤ 14 días) el modelo
          <b>no discrimina bien</b>: AUC {ml['auc_zona_demo']:.2f} con solo
          {ml['n_zona_demo']} casos de prueba, frente a {ml['cobertura_demo']:.1%} del histórico.
          Ruta lo muestra con un indicador de confianza bajo en vez de ocultarlo.
        </div>
      </div>
      <div>
        <div class="titulo-seccion" style="font-size:14px">Pulso de la comunidad</div>
        <div style="font-size:13px;color:{TEXTO_SUAVE};margin-top:6px;line-height:1.5">
          🌤️ Pulse: {pulse_txt}. El registro de ánimo es del estudiante y no se agrega
          ni se comparte.
        </div>
      </div>
    </div>

    <hr class="separador">
    <div class="titulo-seccion" style="font-size:14px">Indicadores de esta demo</div>
    <div class="subtitulo" style="margin-bottom:6px">Se recalculan con cada acción en
      Pulse y Ruta. Son de uso de la demo, <b>no resultados del piloto</b>.</div>
    {html_kpis}

    <hr class="separador">
    <div class="titulo-seccion" style="font-size:14px">Cola de contacto humano</div>
    <div class="subtitulo" style="margin-bottom:6px">Solo estudiantes que pidieron que
      una persona los contacte, con el mínimo de datos: código, prioridad y tipo de apoyo
      no clínico.</div>
    {cola}"""
