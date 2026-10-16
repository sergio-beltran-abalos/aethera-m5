"""Reestructura el README: elimina secciones duplicadas y renumera."""
import io
import re

P = "README.md"
t = io.open(P, encoding="utf-8").read()

# La cabecera del README ya cubre: que hace, como funciona (con diagrama),
# resultados, documentacion y puesta en marcha. Se eliminan los duplicados.
for a, b in [
    ("## 3. Qué hace y cómo funciona", "## 4. Modelos y herramientas de IA"),
    ("## 6. Resultados", "## 7. Escalabilidad"),
    ("## 10. Documentación", "## 12. Video demostrativo"),
]:
    i, j = t.index(a), t.index(b)
    t = t[:i] + t[j:]

for viejo, nuevo in [
    ("## 4. Modelos y herramientas de IA", "## 3. Modelos y herramientas de IA"),
    ("## 5. Datasets del Data Pack utilizados", "## 4. Datasets del Data Pack utilizados"),
    ("## 7. Escalabilidad", "## 5. Escalabilidad"),
    ("## 8. Privacidad e IA responsable", "## 6. Privacidad e IA responsable"),
    ("## 9. Estructura", "## 7. Estructura"),
    ("## 12. Video demostrativo", "## 8. Video demostrativo"),
    ("(ver §5)", "(ver §4)"),
    ("(ver §7, escalabilidad)", "(ver §5, escalabilidad)"),
]:
    t = t.replace(viejo, nuevo)

io.open(P, "w", encoding="utf-8", newline="\n").write(t)

print("README reestructurado\n")
for m in re.finditer(r"^## .*$", t, re.M):
    print(f"{t[:m.start()].count(chr(10)) + 1:5} {m.group(0)}")
print(f"\nlineas totales: {t.count(chr(10)) + 1}")
