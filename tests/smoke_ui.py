"""Prueba de las piezas HTML y del cableado de Gradio (sin abrir navegador)."""
from aethera import agente, calendario, config as C, pulso, servicios, vistas
from aethera.ui import construir
from aethera.segmentos import tarjetas_demo

errores = []


def check(nombre, html, debe_contener=()):
    if not html or not isinstance(html, str):
        errores.append(f"{nombre}: devolvió {type(html).__name__}, no texto")
        return
    for token in debe_contener:
        if token not in html:
            errores.append(f"{nombre}: falta {token!r}")
    print(f"  {nombre:26} {len(html):>6,} chars  ✓")


print("== Vistas HTML ==")
tarjetas = tarjetas_demo()
nombre = list(tarjetas)[1]
sesion = agente.Sesion(tarjetas[nombre], nombre, servicios.Agenda())

check("html_que_es_pulse", vistas.html_que_es_pulse(), ["¿Qué es Pulse?", "Marca"])
check("html_aviso", vistas.html_aviso())
check("html_ficha_perfil", vistas.html_ficha_perfil(nombre), [tarjetas[nombre]["student_id"]])
check("html_mood_track (sin consent)", vistas.html_mood_track(sesion), ["privacidad"])

sesion.consentimiento_pulse = True
sesion.mood_track = pulso.historial_ejemplo(nombre)
sesion.mood_track += [{"fecha": C.FECHA_DEMO, "mood": "pesado", "valor": 1,
                       "temas": ["Estudios"], "nota": "", "ejemplo": False}]
check("html_mood_track (con datos)", vistas.html_mood_track(sesion), ["Mi mes en Pulse"])

r = pulso.registrar(sesion, "regular", ["Descanso"], "")
check("html_frase", vistas.html_frase(r), [r["frase"][:20]])
check("html_frase (vacía)", vistas.html_frase())
check("html_frase (sin consent)", vistas.html_frase({"error": "acepta el aviso"}))
check("html_bienestar", vistas.html_bienestar(), ["Bienestar", "AUC", "AUC"])
check("html_panel_traza (vacío)", vistas.html_panel_traza(sesion))

print("\n== Turno completo del agente (modo reglas) ==")
for msg in ["¿Qué apoyos hay en la universidad?",
            "Trabajo todo el día y me siento solo en la U",
            "Tengo muchas entregas y casi no duermo",
            "Prefiero algo virtual en la tarde",
            "2",
            "No puedo ese día",
            "Ya no quiero vivir",
            "Dame el teléfono de un psicólogo",
            "Resuélveme la tarea de Networks"]:
    respuesta, traza = agente.procesar_mensaje(sesion, msg)
    print(f"  {msg[:44]:46} → {traza['accion']:16} "
          f"g_ent={traza['guardrail_entrada'][:14]:16} "
          f"g_sal={str(traza.get('guardrail_salida', '—'))[:18]}")

check("html_panel_traza (con turnos)", vistas.html_panel_traza(sesion), ["Turno"])
check("html_bienestar (con KPIs)", vistas.html_bienestar(), ["Indicadores"])
check("tabla reservas", vistas.tabla_reservas_html())

print("\n== KPIs ==")
from aethera import bienestar as bst
for k in bst.calcular_kpis():
    v = k["valor"]
    shown = "—" if v is None else (f"{v:.0f} d" if k["formato"] == "dias" else f"{v:.0%}")
    print(f"  {k['nombre']:22} {shown:>7}   {k['texto']:12} · {k['detalle']}")

print("\n== Construcción de la app Gradio ==")
app = construir()
print(f"  Blocks construido: {type(app).__name__} ✓")
print(f"  CSS: {len(vistas.CSS):,} caracteres")
print(f"  Tema: {type(__import__('aethera.ui', fromlist=['tema']).tema()).__name__}")

print("\n" + "=" * 60)
if errores:
    print(f"✗ {len(errores)} PROBLEMAS:")
    for e in errores:
        print("   ·", e)
else:
    print("✓ Todo OK")
