"""Revision de integridad textual de la documentacion."""
import glob
import io
import re
import sys

PATRONES = re.compile(
    r"rit clone|rithub|serrio|irguraci|irototiio|iiloto|se unoire|gratu.ito|"
    r"obliratori|\blurar\b|\binstalasion\b|\bfuncionaion\b|\bconfigurasion\b|"
    r"\bse dice en demo\b|palabras exactas|palabras a decir|Ojo: haz|\bponme\b|"
    r"\btu laptop\b|antes de entregar"
)

# Caracteres fuera del rango latino. Ninguno tiene motivo legitimo en un
# documento en espanol sobre salud mental universitaria: si aparece, es texto
# de otro idioma filtrado por una escritura automatica que no respeta el
# archivo. Se detectan por rango, no por lista, para no tener que ampliarla.
NO_LATINO = re.compile(r"[\u0370-\u03ff\u0400-\u04ff\u4e00-\u9fff\u3040-\u30ff]")

# Un fallo silencioso de codificacion puede convertir 'g' en 'r' en cualquier
# palabra. Se verifican los terminos que deben aparecer intactos en la
# documentacion: si alguno desaparece, casi seguro fue corrompido.
TERMINOS = [
    "git", "github", "Sergio", "obligatorio", "obligatorios", "lugar",
    "configuración", "Instalación", "gratuito", "lenguaje", "integridad",
    "código", "función", "información", "agrega", "llegar",
]

CLAVES_OBLIGATORIAS = {
    "docs/INSTALACION.md": [
        "github.com/sergio-beltran-abalos/aethera-m5.git",
        "python -m venv .venv",
        "cloudflared",
        "instalar.bat",
        "AETHERA_PROVEEDOR",
        "GEMINI_API_KEY",
    ],
    "README.md": [
        "docs/INSTALACION.md",
        "FICHA_IA_RESPONSABLE.pdf",
        "Sergio Edmundo Beltran Abalos",
        "instalar.bat",
    ],
}

fallos = []

archivos = ["README.md"] + sorted(glob.glob("docs/*.md")) \
    + sorted(glob.glob("src/aethera/*.py")) + sorted(glob.glob("tests/*.py")) \
    + sorted(glob.glob("tools/*.py"))
corpus = ""
for f in archivos:
    texto = io.open(f, encoding="utf-8", errors="replace").read()
    if f.endswith(".md"):
        corpus += texto
    # Este archivo contiene los patrones literalmente: se excluye a si mismo.
    hallazgos = [] if f.endswith("revisar_docs.py") else PATRONES.findall(texto)
    no_latino = sorted(set(NO_LATINO.findall(texto)))
    if hallazgos:
        estado = f"CORRUPTO: {hallazgos}"
    elif no_latino:
        estado = f"CARACTERES NO LATINOS: {no_latino}"
        hallazgos = [estado]
    else:
        estado = "OK"
    print(f"  {f:36} {len(texto):6,} chars  {estado}")
    if hallazgos:
        fallos.append(f"{f}: {hallazgos}")

print("\nTerminos que deben aparecer intactos:")
for t in TERMINOS:
    n = corpus.count(t)
    ok = n > 0
    print(f"  {t:18} {n:4} apariciones  {'OK' if ok else 'NO APARECE (posible corrupcion)'}")
    if not ok:
        fallos.append(f"termino ausente o corrupto: {t!r}")

print("\nClaves obligatorias:")
for f, claves in CLAVES_OBLIGATORIAS.items():
    texto = io.open(f, encoding="utf-8").read()
    for c in claves:
        ok = c in texto
        print(f"  {f:24} {c:44} {'OK' if ok else 'FALTA'}")
        if not ok:
            fallos.append(f"{f} no contiene {c!r}")

print()
if fallos:
    print(f"{len(fallos)} PROBLEMAS")
    sys.exit(1)
print("Documentacion integra y sin lenguaje interno.")
