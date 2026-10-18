"""
Markdown → PDF para los entregables del Desafío Ciudad Aethera.

Usa Edge en modo headless para imprimir: sale mejor que un generador de PDF en
Python porque respeta tipografía, tablas y saltos de página de verdad.

    python tools/md_a_pdf.py docs/DOCUMENTO_E2.md DOCUMENTO_E2.pdf
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EDGE = next((p for p in [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
] if Path(p).exists()), None)

CSS = """
@page { size: A4; margin: 16mm 15mm 18mm; }
* { box-sizing: border-box; }
body {
  font-family: 'Segoe UI', Inter, system-ui, sans-serif;
  color: #14213D; font-size: 10pt; line-height: 1.55; margin: 0;
}
h1 { font-size: 21pt; font-weight: 700; letter-spacing: -.4px; margin: 0 0 4pt;
     color: #0E7C86; line-height: 1.15; }
h2 { font-size: 13.5pt; font-weight: 700; margin: 18pt 0 6pt; padding-bottom: 3pt;
     border-bottom: 1.5px solid #0E7C86; color: #14213D; page-break-after: avoid; }
h3 { font-size: 11pt; font-weight: 700; margin: 12pt 0 4pt; color: #0A5F68;
     page-break-after: avoid; }
h1 + p { color: #5B6B80; font-size: 9.5pt; margin-top: 0; }
p { margin: 5pt 0; }
hr { border: 0; border-top: 1px solid #DCE3EA; margin: 12pt 0; }
strong { color: #0A5F68; font-weight: 700; }
code { background: #F1F5F8; color: #0A5F68; padding: 1px 4px; border-radius: 3px;
       font-family: 'Cascadia Mono', Consolas, monospace; font-size: 8.5pt; }
pre { background: #F7FAFB; border: 1px solid #DCE3EA; border-left: 3px solid #0E7C86;
      border-radius: 5px; padding: 8pt 10pt; font-size: 8pt; line-height: 1.45;
      overflow: hidden; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; color: #14213D; font-size: 8pt; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9pt;
        page-break-inside: avoid; }
th { background: #0E7C86; color: #fff; text-align: left; padding: 5pt 7pt;
     font-weight: 600; border: 1px solid #0A5F68; }
td { padding: 5pt 7pt; border: 1px solid #DCE3EA; vertical-align: top; }
tr:nth-child(even) td { background: #F7FAFB; }
blockquote { margin: 8pt 0; padding: 6pt 11pt; background: #FFF8EC;
             border-left: 3px solid #F0B96B; color: #5B4A2E; font-style: italic; }
ul, ol { margin: 5pt 0; padding-left: 17pt; }
li { margin: 2.5pt 0; }
em { color: #5B6B80; }
a { color: #0E7C86; text-decoration: none; }
"""

# Perfil "una página": la ficha de IA responsable lo exige. Menos aire, misma legibilidad.
CSS_COMPACTO = """
@page { size: A4; margin: 7mm 8mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Inter, system-ui, sans-serif;
       color: #14213D; font-size: 6.7pt; line-height: 1.16; margin: 0; }
h1 { font-size: 11.5pt; font-weight: 700; letter-spacing: -.3px; margin: 0 0 1pt;
     color: #0E7C86; line-height: 1.1; }
h2 { font-size: 7.8pt; font-weight: 700; margin: 2.6pt 0 1.2pt; padding-bottom: .8pt;
     border-bottom: 1px solid #0E7C86; color: #14213D; page-break-after: avoid;
     text-transform: uppercase; letter-spacing: .4pt; }
h1 + p { color: #5B6B80; font-size: 6.6pt; margin: 0 0 2pt; }
p { margin: 1.1pt 0; }
hr { border: 0; border-top: 1px solid #DCE3EA; margin: 4pt 0; }
strong { color: #0A5F68; font-weight: 700; }
code { background: #F1F5F8; color: #0A5F68; padding: 0 2px; border-radius: 2px;
       font-family: 'Cascadia Mono', Consolas, monospace; font-size: 6.4pt; }
pre { background: #F7FAFB; border: 1px solid #DCE3EA; border-left: 2px solid #0E7C86;
      padding: 4pt 6pt; font-size: 6.2pt; line-height: 1.3; white-space: pre-wrap;
      margin: 3pt 0; page-break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 2.4pt 0; font-size: 6.2pt;
        page-break-inside: avoid; }
th { background: #0E7C86; color: #fff; text-align: left; padding: 1.2pt 2.4pt;
     font-weight: 600; border: 1px solid #0A5F68; }
td { padding: 1.2pt 2.4pt; border: 1px solid #DCE3EA; vertical-align: top; }
tr:nth-child(even) td { background: #F7FAFB; }
ul, ol { margin: 1.4pt 0; padding-left: 10pt; }
li { margin: 0.4pt 0; }
em { color: #5B6B80; }
a { color: #0E7C86; text-decoration: none; }
"""


def _inline(texto: str) -> str:
    t = html.escape(texto)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def _celda(c: str, cabecera: bool) -> str:
    c = c.strip()
    c = re.sub(r":?-{2,}:?", "", c) if cabecera else c
    tag = "th" if cabecera else "td"
    return f"<{tag}>{_inline(c)}</{tag}>"


def markdown_a_html(md: str, compacto: bool = False) -> str:
    md = re.sub(r"^---\n.*?\n---\n", "", md, flags=re.S)   # front-matter
    css = CSS_COMPACTO if compacto else CSS
    lineas = md.replace("\r\n", "\n").split("\n")
    out, i = [], 0
    dentro_tabla = False

    def cerrar_tabla():
        nonlocal dentro_tabla
        if dentro_tabla:
            out.append("</tbody></table>")
            dentro_tabla = False

    while i < len(lineas):
        linea = lineas[i]

        # Tabla
        if linea.strip().startswith("|") and i + 1 < len(lineas) \
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lineas[i + 1]):
            cerrar_tabla()
            cabecera = [c for c in linea.strip().strip("|").split("|")]
            out.append("<table><thead><tr>"
                       + "".join(_celda(c, True) for c in cabecera) + "</tr></thead><tbody>")
            dentro_tabla = True
            i += 2
            continue
        if dentro_tabla and linea.strip().startswith("|"):
            out.append("<tr>" + "".join(_celda(c, False) for c in
                                        linea.strip().strip("|").split("|")) + "</tr>")
            i += 1
            continue
        cerrar_tabla()

        # Bloque de código
        if linea.strip().startswith("```"):
            i += 1
            buf = []
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                buf.append(lineas[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)", linea)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
            i += 1
            continue

        if re.match(r"^\s*([-*_])\s*\1\s*\1[\s\1]*$", linea):
            out.append("<hr>")
            i += 1
            continue

        if linea.strip().startswith(">"):
            buf = []
            while i < len(lineas) and lineas[i].strip().startswith(">"):
                buf.append(lineas[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + _inline(" ".join(buf)) + "</blockquote>")
            continue

        if re.match(r"^\s*([-*+]|\d+\.)\s+", linea):
            tag = "ul" if re.match(r"^\s*[-*+]", linea) else "ol"
            out.append(f"<{tag}>")
            while i < len(lineas) and re.match(r"^\s*([-*+]|\d+\.)\s+", lineas[i]):
                out.append("<li>" + _inline(re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lineas[i]))
                           + "</li>")
                i += 1
            out.append(f"</{tag}>")
            continue

        if linea.strip():
            out.append(f"<p>{_inline(linea)}</p>")
        i += 1

    cerrar_tabla()
    return ("<!doctype html><html lang='es'><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>{''.join(out)}</body></html>")


def convertir(md_path: Path, pdf_path: Path, compacto: bool = False) -> None:
    if EDGE is None:
        raise RuntimeError("No se encontró Microsoft Edge para imprimir a PDF.")

    html_path = pdf_path.with_suffix(".tmp.html")
    html_path.write_text(markdown_a_html(md_path.read_text(encoding="utf-8"), compacto),
                         encoding="utf-8")
    try:
        subprocess.run([
            EDGE, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path.resolve()}",
            html_path.resolve().as_uri(),
        ], check=True, capture_output=True, timeout=120)
    finally:
        html_path.unlink(missing_ok=True)

    kb = pdf_path.stat().st_size / 1024
    print(f"  {pdf_path.name:34} {kb:7.1f} KB")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--compacto"]
    compacto = "--compacto" in sys.argv
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)
    convertir(Path(args[0]), Path(args[1]), compacto)
