"""Verifica que los enlaces internos del README apunten a archivos existentes."""
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
texto = io.open(RAIZ / "README.md", encoding="utf-8").read()

enlaces = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", texto)
rotos, externos, internos = [], 0, 0

for etiqueta, destino in enlaces:
    if destino.startswith(("http://", "https://")):
        externos += 1
        continue
    internos += 1
    limpio = destino.split("#")[0]
    if not (RAIZ / limpio).exists():
        rotos.append((etiqueta, destino))

print(f"Enlaces totales   : {len(enlaces)}")
print(f"  internos        : {internos}")
print(f"  externos        : {externos}")
print(f"  rotos           : {len(rotos)}")
for etiqueta, destino in rotos:
    print(f"    ROTO: [{etiqueta}]({destino})")

# Estructura minima exigida por el enunciado
print("\nEstructura exigida por las bases:")
requeridos = {
    "README.md": (RAIZ / "README.md").exists(),
    "/src": (RAIZ / "src" / "aethera").is_dir(),
    "/docs": (RAIZ / "docs").is_dir(),
    "/notebook": (RAIZ / "notebook").is_dir(),
    "FICHA_IA_RESPONSABLE.pdf": (RAIZ / "FICHA_IA_RESPONSABLE.pdf").exists(),
}
faltantes = [k for k, v in requeridos.items() if not v]
for k, v in requeridos.items():
    print(f"  {k:32} {'OK' if v else 'FALTA'}")
if faltantes:
    rotos.append(("estructura", ", ".join(faltantes)))

if rotos:
    sys.exit(1)
print("\nTodos los enlaces resuelven y la estructura es completa.")
