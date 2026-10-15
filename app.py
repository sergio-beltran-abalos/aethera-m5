"""
Aethera Pulse + Ruta — punto de entrada.

Entregable 2 · Desafío Ciudad Aethera (Misión M5: estigma y baja búsqueda de ayuda).

Este archivo es deliberadamente un launcher'solo: HF Spaces exige `app.py` en la
raíz, y el repositorio exige `/src`. Así se cumplen las dos cosas sin duplicar
código. Toda la lógica vive en `src/aethera/`.

    local:     pip install -r requirements.txt  →  python app.py
    HF Spaces: secreto GEMINI_API_KEY + los 7 archivos del Data Pack en data/

Variables de entorno
    AETHERA_PROVEEDOR   gemini | openai | huggingface | compatible | offline
    AETHERA_MODELO      sobrescribe el id del modelo
    AETHERA_DATA        ruta alterna a la carpeta data/
    AETHERA_INSTITUCION institución a atender (demuestra escalabilidad)
    AETHERA_LANZAR_UI   0 para solo importar y probar sin abrir el navegador
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from aethera import config as C          # noqa: E402
from aethera.ui import lanzar            # noqa: E402


def diagnostico() -> None:
    from aethera import datos, ia
    try:
        r = datos.resumen()
    except Exception as e:  # noqa: BLE001
        print(f"✗ Data Pack incompleto: {e}")
        return

    clave = ia.obtener_clave()
    print("=" * 68)
    print("  AETHERA PULSE + RUTA · diagnóstico")
    print("=" * 68)
    print(f"  Data Pack      D1 {r['D1']:,} · D2 {r['D2']:,} · D3 {r['D3']:,} · "
          f"D4 {r['D4']:,} · D5 {r['D5']:,} · D6 {r['D6']} · D7 {r['D7']}")
    print(f"  Espera (D2)    {r['espera_min']}–{r['espera_max']} días "
          f"(media {r['espera_media']}, mediana 39)")
    print(f"  Proveedor      {C.PROVEEDOR} · modelo {C.MODELO}")
    print(f"  Clave          {C.clave_api()} "
          f"{'✓ encontrada' if clave else '· no encontrada (modo reglas)'}")
    print("=" * 68)


if __name__ == "__main__":
    if "--diagnostico" in sys.argv or "--sin-ui" in sys.argv:
        diagnostico()
        if "--sin-ui" in sys.argv:
            print("\nUI desactivada (AETHERA_LANZAR_UI=0). Fin.")
    else:
        lanzar()
