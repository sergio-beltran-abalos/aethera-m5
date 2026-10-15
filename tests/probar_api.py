"""Prueba de conexión con el proveedor de IA, sin exponer la clave."""
import os
import sys

from aethera import config as C, ia

print(f"Proveedor : {C.PROVEEDOR}")
print(f"Modelo    : {C.MODELO}")
clave = ia.obtener_clave()
print(f"Clave     : {'presente (' + str(len(clave)) + ' caracteres)' if clave else 'AUSENTE'}")

if not clave:
    sys.exit(1)

# Si el usuario copió algo con comillas o espacios, lo limpiamos aquí.
clave = clave.strip().strip('"').strip("'")
print(f"Prefijo   : {clave[:6]}…")
print(f"Formato   : {'AIza… (API key de Google)' if clave.startswith('AIza') else 'NO parece una API key de Google Gemini'}")

print("\nLlamando al modelo…")
try:
    from google import genai
    from google.genai import types
    cliente = genai.Client(api_key=clave)
    r = cliente.models.generate_content(
        model=C.MODELO,
        contents="Responde solo con la palabra: funciona",
        config=types.GenerateContentConfig(max_output_tokens=20, temperature=0))
    print(f"✓ RESPUESTA: {(r.text or '').strip()}")
    print("\nConexión correcta. El modelo", C.MODELO, "responde.")
except Exception as e:  # noqa: BLE001
    print(f"✗ ERROR ({type(e).__name__}):")
    msg = str(e)
    print("  " + msg[:600])
    sys.exit(2)
