"""Turno completo del agente con el modelo de lenguaje real, sin interfaz."""
import time

from aethera import agente, config as C, datos, ia, servicios
from aethera.segmentos import tarjetas_demo

print(f"Proveedor: {C.PROVEEDOR} · modelo: {C.MODELO}\n")

tarjetas = tarjetas_demo()
nombre = "B · Nocturno, trabaja tiempo completo"
p = tarjetas[nombre]
print(f"Perfil {nombre}")
print(f"  {p['student_id']} · {p['study_mode']} · {p['employment_status']} · "
      f"{p['creditos']} créditos (D3)")
print(f"  {p['horario']}\n")

sesion = agente.Sesion(p, nombre, servicios.Agenda())

guion = [
    "Hola",
    "Trabajo todo el día, estudio de noche y no conozco a nadie en la universidad",
    "1",
    "No puedo ese día",
    "2",
]
for msg in guion:
    t0 = time.time()
    respuesta, traza = agente.procesar_mensaje(sesion, msg)
    print("=" * 74)
    print(f"👤 {msg}")
    print(f"   [{traza['accion']} · {traza.get('redaccion', '—')} · "
          f"g_ent={traza['guardrail_entrada']} · g_sal={traza.get('guardrail_salida', '—')}]")
    print("-" * 74)
    for linea in respuesta.split("\n"):
        print("🤖 " + linea)
    print()

print("=" * 74)
print(f"Llamadas al modelo: {ia.LLAMADAS['ok']} ok · {ia.LLAMADAS['fallidas']} fallidas")
print(f"Turnos: {sesion.turnos} · tiempo medio: "
      f"{sum(t['segundos'] for t in sesion.trazas)/len(sesion.trazas):.1f} s")
if sesion.reserva:
    r = sesion.reserva
    print(f"Reserva: {r['reserva_id']} · {r['dia']} {r['fecha']} {r['hora']} · "
          f"{r['servicio']} ({r['canal']})")
    print(f"  P(asistir)={r['p_asistencia']} · confianza ML={r['confianza_ml']}")
    print(f"  Recordatorios: {', '.join(r['recordatorios'])}")
