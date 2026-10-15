"""
Simula a un tercero: repo clonado, SIN clave de API, con el proveedor por
defecto (gemini). Es el escenario mas probable de quien clone el repo, y hay
que confirmar que no se rompe.
"""
import os
import sys

# Sin clave. A proposito.
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("AETHERA_PROVEEDOR", None)

from aethera import agente, config as C, datos, ia, servicios, vistas
from aethera.segmentos import tarjetas_demo

fallos = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALLA ") + msg)
    if not cond:
        fallos.append(msg)


print(f"Proveedor configurado : {C.PROVEEDOR}")
print(f"Modelo                : {C.MODELO}")
print(f"Clave encontrada      : {'si' if ia.obtener_clave() else 'NO (como debe ser)'}")
print(f"Llamadas al modelo    : {ia.LLAMADAS}\n")

check(ia.obtener_clave() is None, "no hay clave: se activan los respaldos")

tarjetas = tarjetas_demo()
nombre = "B · Nocturno, trabaja tiempo completo"
sesion = agente.Sesion(tarjetas[nombre], nombre, servicios.Agenda())

for msg in ["¿Qué apoyos hay en la universidad?",
            "Trabajo todo el día y me siento solo en la U",
            "1",
            "no puedo ese día",
            "Ya no quiero vivir",
            "Dame el teléfono de un psicólogo"]:
    respuesta, traza = agente.procesar_mensaje(sesion, msg)
    check(bool(respuesta) and len(respuesta) > 20,
          f"{msg[:40]:42} -> {traza['accion']:15} [{traza.get('redaccion', 'guion fijo')}]")

check(ia.LLAMADAS["ok"] == 0, "cero llamadas al modelo (nunca intenta sin clave)")
check(ia.LLAMADAS["fallidas"] > 0, "las invocaciones fallaron y se degradaron, sin romperse")

for vista, etiqueta in [(lambda: vistas.html_bienestar(), "Bienestar"),
                        (lambda: vistas.html_panel_traza(sesion), "panel de traza"),
                        (lambda: vistas.tabla_reservas_html(), "tabla de reservas")]:
    h = vista()
    check(isinstance(h, str) and len(h) > 50, f"la vista {etiqueta} renderiza sin clave")

from aethera import pulso
sesion.consentimiento_pulse = True
r = pulso.registrar(sesion, "regular", ["Descanso"], "")
check("frase" in r and r["metodo"] == "frase de respaldo", "Pulse responde con frase de respaldo")

from aethera import bienestar as bst
check(isinstance(bst.calcular_kpis(), list), "los KPIs se calculan sin clave")

print("\n" + "=" * 62)
if fallos:
    print(f"{len(fallos)} FALLAS: el escenario sin clave esta roto")
    sys.exit(1)
print("Un tercero sin clave puede correr el repositorio completo.")
