"""Ejecuta el notebook completo y guarda la salida, para verificar que corre."""
import sys
import warnings
from pathlib import Path

import nbformat
from nbclient import NotebookClient

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[1]
cARPETA = RAIZ / "notebook" / "ENTREGABLE2_analisis.ipynb"

nb = nbformat.read(cARPETA, as_version=4)
client = NotebookClient(nb, timeout=900, kernel_name="python3",
                        resources={"metadata": {"path": str(cARPETA.parent)}})
client.execute()

nbformat.write(nb, cARPETA)
print(f"Notebook ejecutado y guardado con salida: {cARPETA.name}")

errores = 0
for i, celda in enumerate(nb.cells):
    for salida in celda.get("outputs", []):
        if salida.get("output_type") == "error":
            errores += 1
            print(f"  ERROR en celda {i}: {salida['ename']}: {salida['evalue']}")
print(f"Celdas con error: {errores}")
sys.exit(1 if errores else 0)
