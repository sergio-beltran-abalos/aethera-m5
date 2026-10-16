"""Ejercita cada handler de la UI con entradas reales y valida las tuplas."""
import os
import sys

os.environ["AETHERA_LANZAR_UI"] = "0"
os.environ["AETHERA_PROVEEDOR"] = "gemini"
for k in ("GEMINI_API_KEY", "AETHERA_CLAVE_API"):
    os.environ.pop(k, None)

from aethera import agente, config as C, servicios, ui  # noqa: E402
from aethera.segmentos import tarjetas_demo  # noqa: E402

fallos = []


def check(nombre, valor, esperados):
    if not isinstance(valor, (tuple, list)):
        valor = (valor,)
    if len(valor) != esperados:
        fallos.append(f"{nombre}: devolvio {len(valor)} salidas, se esperaban {esperados}")
        print(f"  x {nombre}: {len(valor)} != {esperados}")
    else:
        print(f"  . {nombre}: {esperados} salidas OK")
    return valor


nombre = list(tarjetas_demo())[0]
C.FECHA_DEMO = C.FECHAS_DEMO["Semana regular · mar 20 oct 2026"]

salidas = ui._reiniciar(nombre, list(C.FECHAS_DEMO)[0], True)
sesion, chat, *_ = check("_reiniciar", salidas, 10)
print(f"    perfil={sesion.nombre_perfil} chat={len(chat)}")

# 1. consentimiento
r = check("_consentir", ui._consentir(True, True, sesion), 3)
print(f"    consentimiento={sesion.consentimiento_pulse} historial={len(sesion.mood_track)}")

# 2. registro sin seleccionar animo
check("_registrar (sin eleccion)", ui._registrar("", [], "", sesion, "neutro", []), 6)

# 3. registro con animo y estilo neutro -> puede disparar proactividad
r = check("_registrar (con animo)", ui._registrar("pesado", ["Estudios"], "dormi poco",
                                                   sesion, "neutro", []), 6)
frase, track, sesion, chat, aviso, btn = r
print(f"    chat={len(chat)} turno | aviso={len(aviso)} chars | boton visible={btn.get('visible')}")
if chat:
    print(f"    ultimo turno: {str(chat[-1]['content'])[:60]}")

# 4. el chat recibio la oferta proactiva
if not any(m["role"] == "assistant" for m in chat):
    fallos.append("el registro no produjo turno de Ruta")
    print("  x no hubo turno proactivo tras registrar")
else:
    print("  . Ruta escribio primero OK")

# 4b. y ademas se muestra en la pestana donde esta el estudiante
if "Ruta te escribió primero" not in (aviso or ""):
    fallos.append("la oferta no se muestra en la pestana Pulse")
    print("  x el aviso de la oferta no aparece en Pulse")
else:
    print("  . la oferta se ve sin cambiar de pestana OK")

# 5. abrir chat con estilo distinto
r = check("_abrir_chat", ui._abrir_chat(sesion, chat, "servicio"), 5)
print(f"    estilo ahora = {sesion.estilo_evento} | aviso={len(r[3])} chars")

# 6. enviar un mensaje
r = check("_enviar", ui._enviar("tengo muchas entregas y no duermo", sesion, chat), 6)
entrada, chat, sesion, panel, reservas, bienestar = r
print(f"    chat={len(chat)} | panel={len(panel)} chars | reservas={len(reservas)} chars")

# 7. reservar
if sesion.opciones:
    r, = check("reservar", [agente.reservar(sesion, 1)], 1)
    res = r.get("reserva", {})
    print(f"    titulo='{res.get('evento_titulo')}' lugar='{res.get('evento_lugar')}'")
else:
    print("  ! sin opciones para reservar (no se prueba esa rama)")

# 8. tabla de reservas con la columna nueva
html = ui.vistas.tabla_reservas_html()
if "En tu calendario" in html:
    print("  . la tabla muestra la columna del calendario OK")
else:
    fallos.append("la tabla de reservas no muestra la columna del calendario")
    print("  x falta la columna del calendario")

# 9. los demas handlers
check("_borrar", ui._borrar(sesion), 4)
check("_descargar", ui._descargar(sesion), 1)
check("_persona", ui._persona(sesion, []), 4)
check("html_bienestar", ui.vistas.html_bienestar(), 1)

# Arranque en frio: la sesion se crea en app.load. Si un handler llega antes,
# no debe reventar con AttributeError, porque el estudiante solo ve un error.
print("\nArranque en frío (sesion todavia no creada):")
for nombre, fn, args, esperados in [
    ("_consentir", ui._consentir, (True, True, None), 3),
    ("_registrar", ui._registrar, ("regular", [], "", None, "neutro", []), 6),
    ("_abrir_chat", ui._abrir_chat, (None, [], "neutro"), 5),
    ("_borrar", ui._borrar, (None,), 4),
    ("_descargar", ui._descargar, (None,), 1),
    ("_enviar", ui._enviar, ("hola", None, []), 6),
    ("_persona", ui._persona, (None, []), 4),
]:
    try:
        check(nombre, fn(*args), esperados)
    except Exception as e:  # noqa: BLE001
        fallos.append(f"{nombre} sin sesion lanza {type(e).__name__}: {e}")
        print(f"  x {nombre} sin sesion lanza {type(e).__name__}: {e}")

# 10. el panel de trazabilidad debe renderizar tambien el turno proactivo,
#     que no pasa por el LLM y por eso tiene menos campos.
proactivas = [t for t in sesion.trazas if t.get("disparador")]
if proactivas:
    t = proactivas[0]
    print(f"  . el turno proactivo declara: {t['disparador']}")
else:
    print("  (no hubo turno proactivo en esta sesion)")

print()
if fallos:
    print(f"{len(fallos)} FALLOS")
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("Todos los handlers responden con el numero de salidas declarado.")
