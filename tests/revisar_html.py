"""
Verifica el HTML de todas las vistas mediante un parser real.

El defecto que motivó esta comprobación fue un encabezado construido con
``sep.join([""] * 7)``, que generaba seis etiquetas ``<div>`` sin cerrar. El
navegador las anidaba dentro de la grilla y el calendario de Pulse colapsaba a
una sola columna, haciéndose ilegible.

La comprobación usa ``html.parser`` en lugar de expresiones regulares: los
atributos ``style`` se parten en varias líneas de forma legitima, y un chequeo
basado en líneas marca falsos positivos.
"""
import re
import sys
from html.parser import HTMLParser

from aethera import agente, pulso, servicios, vistas
from aethera.segmentos import tarjetas_demo

fallos = []
VOID = {"br", "hr", "img", "input", "meta", "link", "col", "area", "base", "source"}


class Verificador(HTMLParser):
    """Detecta etiquetas sin cerrar y desbordes de anidamiento."""

    def __init__(self, nombre: str):
        super().__init__(convert_charrefs=True)
        self.nombre = nombre
        self.pila: list[str] = []
        self.sin_cerrar: list[str] = []
        self.desbordes = 0

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.pila.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.pila:
            self.desbordes += 1
            return
        if self.pila[-1] == tag:
            self.pila.pop()
        elif tag in self.pila:
            # Cierre fuera de orden: se contabiliza y se desenreda
            while self.pila and self.pila.pop() != tag:
                pass
            self.desbordes += 1
        else:
            self.sin_cerrar.append(tag)

    def resultado(self) -> str:
        pendientes = len(self.pila)
        if pendientes == 0 and not self.desbordes and not self.sin_cerrar:
            return "OK"
        partes = []
        if pendientes:
            partes.append(f"{pendientes} sin cerrar ({', '.join(self.pila[:4])})")
        if self.desbordes:
            partes.append(f"{self.desbordes} cierre(s) fuera de orden")
        if self.sin_cerrar:
            partes.append(f"{len(self.sin_cerrar)} cierre(s) huérfano(s)")
        return " · ".join(partes)


def revisar(nombre: str, html: str) -> None:
    if not isinstance(html, str) or not html:
        print(f"  {nombre:34} VACIO")
        fallos.append(f"{nombre}: devolvio contenido vacio")
        return
    v = Verificador(nombre)
    v.feed(html)
    r = v.resultado()
    print(f"  {nombre:34} {len(html):6,} chars  {r}")
    if r != "OK":
        fallos.append(f"{nombre}: {r}")


print("=" * 74)
print(" CALENDARIO DE PULSE")
print("=" * 74)

nombre_perfil = next(k for k in tarjetas_demo() if k.startswith("B"))
sesion = agente.Sesion(tarjetas_demo()[nombre_perfil], nombre_perfil, servicios.Agenda())

revisar("html_mood_track (sin consent)", vistas.html_mood_track(sesion))

sesion.consentimiento_pulse = True
sesion.mood_track = pulso.historial_ejemplo(nombre_perfil)
html = vistas.html_mood_track(sesion)
revisar("html_mood_track (con datos)", html)

print("\n  Estructura de la grilla:")
cabeceras = re.findall(r">(lu|ma|mi|ju|vi|sá|do)<", html)
celdas = re.findall(r'title="\d{4}-\d{2}-\d{2}', html)
promedios = re.findall(r"align-self:center", html)
relleno = html.count("<div></div>")
print(f"    cabeceras de dia   : {len(cabeceras)}   {'OK' if len(cabeceras) == 7 else 'DEBE SER 7'}")
print(f"    celdas con fecha   : {len(celdas)}   (dias con registro en la ventana)")
print(f"    celdas de promedio : {len(promedios)}")
print(f"    celdas de relleno  : {relleno}   (alineacion a lunes)")

if len(cabeceras) != 7:
    fallos.append(f"cabecera del calendario: {len(cabeceras)} columnas, se esperaban 7")
if not re.search(r"grid-template-columns:repeat\(7,minmax\(0,1fr\)\)\s*40px", html):
    fallos.append("la grilla del calendario no declara 7 columnas mas el promedio")

print("\n" + "=" * 74)
print(" RESTO DE VISTAS")
print("=" * 74)
revisar("html_que_es_pulse", vistas.html_que_es_pulse())
revisar("html_aviso", vistas.html_aviso())
revisar("html_ficha_perfil", vistas.html_ficha_perfil(nombre_perfil))
revisar("html_frase (vacia)", vistas.html_frase())
revisar("html_frase (sin consent)", vistas.html_frase({"error": "acepta el aviso"}))
revisar("html_bienestar", vistas.html_bienestar())
revisar("html_panel_traza (vacio)", vistas.html_panel_traza(sesion))
revisar("tabla_reservas", vistas.tabla_reservas_html())
revisar("html_estilo_evento", vistas.html_estilo_evento())

r = pulso.registrar(sesion, "regular", ["Descanso"], "")
revisar("html_frase (con resultado)", vistas.html_frase(r))

for msg in ["¿Qué apoyos hay?", "Trabajo de día y estoy solo", "1", "ya no quiero vivir"]:
    agente.procesar_mensaje(sesion, msg)
revisar("html_panel_traza (con turnos)", vistas.html_panel_traza(sesion))
revisar("html_bienestar (con actividad)", vistas.html_bienestar())

# El turno proactivo no pasa por el LLM: su traza tiene menos campos y el panel
# debe saber renderizarla sin romperse.
from aethera import disparadores, servicios  # noqa: E402

s2 = agente.Sesion(tarjetas_demo()[list(tarjetas_demo())[0]], "A", servicios.Agenda())
s2.consentimiento_pulse = True
s2.mood_track = pulso.historial_ejemplo("A")
_, oferta = agente.ofrecer_proactivamente(s2)
revisar("html_panel_traza (turno proactivo)", vistas.html_panel_traza(s2))
revisar("tabla_reservas (con cita)", vistas.tabla_reservas_html())
if oferta:
    print(f"    el panel declara el disparador: "
          f"{'SI' if 'D7' in vistas.html_panel_traza(s2) or 'Pulse' in vistas.html_panel_traza(s2) else 'NO'}")
else:
    fallos.append("no se genero turno proactivo para revisar el panel")

print("\n" + "=" * 74)
if fallos:
    print(f"{len(fallos)} PROBLEMAS:")
    for f in fallos:
        print("   ·", f)
    sys.exit(1)
print("Todas las vistas generan HTML bien formado.")
