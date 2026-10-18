"""Arranque real de Gradio: confirma que el wiring de los handlers es valido."""
import os
import sys

os.environ["AETHERA_LANZAR_UI"] = "0"          # construye, no lanza
os.environ["AETHERA_PROVEEDOR"] = "gemini"     # sin clave: usa las plantillas
for k in ("GEMINI_API_KEY", "AETHERA_CLAVE_API"):
    os.environ.pop(k, None)

from aethera import ui  # noqa: E402

try:
    app = ui.construir()
except Exception as e:  # noqa: BLE001
    print(f"FALLO al construir la app: {type(e).__name__}: {e}")
    sys.exit(1)

# Recorrer el grafo de dependencias: Gradio falla aqui si un handler no
# devuelve el numero de salidas que se declaro.
n = 0
for dep in app.fns.values():
    n += 1

print(f"  app construida OK · {n} funciones conectadas")
print(f"  bloques: {[b.label for b in app.blocks.values() if getattr(b, 'label', None)][:8]}")
sys.exit(0)
