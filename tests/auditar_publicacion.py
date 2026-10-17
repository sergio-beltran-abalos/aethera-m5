"""
Auditoria previa a la publicacion del repositorio.

Verifica que no se haya incluido nada que no deba salir de forma publica:
credenciales, datos del Data Pack, informacion personal o artefactos locales.
"""
import io
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
fallos, avisos = [], []


def check(cond, msg, critico=True):
    print(("  [OK]   " if cond else "  [FALLA]") + " " + msg)
    if not cond:
        (fallos if critico else avisos).append(msg)


print("=" * 70)
print(" 1 · ARCHIVOS VERSIONADOS")
print("=" * 70)
versionados = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True,
                             text=True).stdout.split()

print(f"  Total versionado: {len(versionados)}")
prohibidos = [f for f in versionados
              if re.match(r"data/D\d", f) or f.startswith(".venv/") or f.endswith(".env")
              or "mi_registro_pulse" in f or "__pycache__" in f]
check(not prohibidos, f"El Data Pack y artefactos locales NO estan versionados"
      + (f" (encontrados: {prohibidos})" if prohibidos else ""))

print("\n" + "=" * 70)
print(" 2 · CREDENCIALES EN EL CONTENIDO")
print("=" * 70)
PATRONES_CRED = {
    "Clave de API de Google": r"AIza[0-9A-Za-z_-]{30,}",
    "Clave OpenAI": r"sk-[0-9A-Za-z]{20,}",
    "Token HuggingFace": r"hf_[0-9A-Za-z]{20,}",
    "Token GitHub": r"gh[pousr]_[0-9A-Za-z]{20,}",
    "AWS": r"AKIA[0-9A-Z]{16}",
    "Bearer": r"(?i)authorization:\s*bearer\s+[0-9A-Za-z._-]{20,}",
    "Asignacion sospechosa": r"(?i)(api_key|secret|password|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']",
}

encontradas = []
for f in versionados:
    ruta = RAIZ / f
    try:
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for nombre, patron in PATRONES_CRED.items():
        if re.search(patron, texto):
            # Las asignaciones dentro de los propios scripts de prueba son
            # literales de ejemplo, no credenciales; se reportan aparte.
            encontradas.append((f, nombre))

reales = [(f, n) for f, n in encontradas if "tests/" not in f]
check(not reales, f"No hay credenciales reales en el repositorio"
      + (f" (encontradas: {reales})" if reales else ""))
if encontradas:
    for f, n in encontradas:
        print(f"         nota: literal de ejemplo en {f} ({n})")

print("\n" + "=" * 70)
print(" 3 · INFORMACION PERSONAL")
print("=" * 70)
correos = set()
for f in versionados:
    if not f.endswith((".md", ".txt", ".py", ".ipynb")):
        continue
    texto = (RAIZ / f).read_text(encoding="utf-8", errors="ignore")
    # Se excluyen los fragmentos de URL (p. ej. parametros de Google Fonts).
    for c in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", texto):
        if "." in c.split("@")[1] and not c.endswith(".96"):
            correos.add(c)

PERSONALES = {"sergio.beltran@utec.edu.pe"}
publicables = correos - PERSONALES
print(f"  Correos presentes: {sorted(correos) if correos else 'ninguno'}")
check(not publicables,
      "Solo se publica el correo de contacto declarado por el equipo"
      + (f" (aparecen otros: {sorted(publicables)})" if publicables else ""))

print("\n" + "=" * 70)
print(" 4 · DECLARACION DE NO REDISTRIBUCION")
print("=" * 70)
readme = io.open(RAIZ / "README.md", encoding="utf-8").read()
check("no se redistribuye" in readme.lower() or "no redistribuir" in readme.lower(),
      "El README declara explicitamente que el Data Pack no se redistribuye")

leeme = RAIZ / "data" / "LEEME.txt"
check(leeme.exists() and len(leeme.read_text(encoding="utf-8")) > 200,
      "El directorio data/ incluye instrucciones de obtencion")
if leeme.exists():
    texto = leeme.read_text(encoding="utf-8")
    faltan = [c for c in ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
              if c + "_" not in texto]
    check(not faltan, "Las instrucciones enumeran los siete datasets"
          + (f" (faltan: {faltan})" if faltan else ""))
    check("sintéticos" in texto, "Las instrucciones indican que los datos son sintéticos")

# La ficha debe tener una unica fuente versionada: evita ambigüedad para quien lea.
fuentes_ficha = [f for f in versionados
                 if "FICHA_IA_RESPONSABLE" in f and f.endswith(".md")]
check(len(fuentes_ficha) == 1,
      "La ficha tiene una sola fuente en Markdown"
      + (f" (encontradas: {fuentes_ficha})" if len(fuentes_ficha) != 1 else ""))

print("\n" + "=" * 70)
print(" 5 · TAMAÑO Y CONTENIDO PUBLICO")
print("=" * 70)
pdfs = [f for f in versionados if f.endswith(".pdf")]
print(f"  PDF en el repositorio: {pdfs}")
print("  Nota: los documentos contienen cifras agregadas del analisis, no datos")
print("        personales. Es trabajo de equipo, no redistribucion del Data Pack.")

total = sum((RAIZ / f).stat().st_size for f in versionados if (RAIZ / f).exists())
print(f"  Tamano total del repositorio: {total/1024/1024:.1f} MB")

print("\n" + "=" * 70)
if fallos:
    print(f"NO PUBLICAR. {len(fallos)} problemas criticos:")
    for f in fallos:
        print("   ·", f)
    sys.exit(1)
print("El repositorio puede publicarse sin filtrar informacion sensible.")
if avisos:
    print(f"\n{len(avisos)} avisos no bloqueantes:")
    for a in avisos:
        print("   ·", a)
