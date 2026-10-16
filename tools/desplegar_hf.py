"""
Despliegue del prototipo en Hugging Face Spaces.

Crea el Space, sube el codigo y el Data Pack, registra el secreto de la clave de
API y devuelve la direccion publica.

    python tools/desplegar_hf.py --espacio aethera-m5

Requisitos
----------
- Variable de entorno ``HF_TOKEN`` con un token de escritura de Hugging Face.
  Se obtiene en https://huggingface.co/settings/tokens (rol: Write).
- Variable de entorno con la clave del modelo, ``GEMINI_API_KEY``.

El token nunca se imprime ni se escribe en disco.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATAPACK = ["D1_wellbeing_survey.csv", "D2_support_services.csv",
            "D3_academic_trajectory.csv", "D4_testimonials.json",
            "D5_help_line_conversations.json", "D6_services_map.geojson",
            "D7_calendar.csv"]
CODIGO = ["app.py", "requirements.txt", "README.md"]


def obtener(nombre: str) -> str | None:
    """Lee un secreto del entorno o, en Windows, del registro del usuario."""
    valor = os.getenv(nombre)
    if valor:
        return valor
    if os.name == "nt":
        import winreg
        for root, clave in ((winreg.HKEY_CURRENT_USER, "Environment"),):
            try:
                with winreg.OpenKey(root, clave) as k:
                    return winreg.QueryValueEx(k, nombre)[0]
            except OSError:
                pass
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Despliega Aethera en Hugging Face Spaces")
    ap.add_argument("--espacio", default="aethera-m5", help="Nombre del Space")
    ap.add_argument("--privado", action="store_true", default=True,
                    help="Space privado (el Data Pack no puede redistribuirse)")
    args = ap.parse_args()

    from huggingface_hub import HfApi

    token = obtener("HF_TOKEN")
    if not token:
        print("FALTA HF_TOKEN")
        print("  1. Abre https://huggingface.co/settings/tokens")
        print("  2. Crea un token con rol 'Write'")
        print('  3. Guardalo sin pegarlo aqui:  setx HF_TOKEN "hf_..."')
        return 1

    api = HfApi(token=token)
    usuario = token.split(":")[0] if token.startswith("api_org_") else None
    try:
        usuario = api.whoami()["name"]
    except Exception as e:  # noqa: BLE001
        print(f"El token no es valido: {type(e).__name__}")
        return 1

    repo_id = f"{usuario}/{args.espacio}"
    print(f"Destino: {repo_id}")

    # ── 1. Crear el Space ────────────────────────────────────────────────────
    try:
        if api.repo_exists(repo_id, repo_type="space"):
            print("El Space ya existe; se actualizara.")
        else:
            api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="gradio",
                            private=True, exist_ok=True)
            print("Space creado.")
    except Exception as e:  # noqa: BLE001
        print(f"No se pudo crear el Space: {type(e).__name__}: {e}")
        return 1

    # ── 2. Verificar el Data Pack ────────────────────────────────────────────
    faltan = [f for f in DATAPACK if not (RAIZ / "data" / f).exists()]
    if faltan:
        print("FALTAN ARCHIVOS DEL DATA PACK en data/:")
        for f in faltan:
            print(f"  · {f}")
        return 1
    total = sum((RAIZ / "data" / f).stat().st_size for f in DATAPACK) / 1024 / 1024
    print(f"Data Pack verificado: {total:.1f} MB")

    # ── 3. Subir codigo y datos ─────────────────────────────────────────────
    from huggingface_hub import CommitOperationAdd

    operaciones = []
    for f in CODIGO:
        operaciones.append(CommitOperationAdd(path_in_repo=f, path_or_fileobj=RAIZ / f))
    operaciones.append(CommitOperationAdd(path_in_repo="data/LEEME.txt",
                                         path_or_fileobj=RAIZ / "data" / "LEEME.txt"))
    for f in DATAPACK:
        operaciones.append(CommitOperationAdd(path_in_repo=f"data/{f}",
                                             path_or_fileobj=RAIZ / "data" / f))

    print(f"Subiendo {len(operaciones)} archivos...")
    api.create_commit(repo_id=repo_id, repo_type="space",
                      operations=operaciones, commit_message="Aethera Pulse + Ruta (M5)")
    print("Subida completada.")

    # ── 4. Secreto del modelo ────────────────────────────────────────────────
    clave = obtener("GEMINI_API_KEY")
    if clave:
        api.add_space_secret(repo_id=repo_id, key="GEMINI_API_KEY", value=clave)
        print("Secreto GEMINI_API_KEY registrado.")
    else:
        print("AVISO: no hay GEMINI_API_KEY; el Space operara con respaldos.")

    # ── 5. Estado ────────────────────────────────────────────────────────────
    url = f"https://huggingface.co/spaces/{repo_id}"
    print()
    print("=" * 66)
    print(f"  Space: {url}")
    print(f"  La compilacion puede tardar 2-5 minutos.")
    print(f"  Consultar estado:  python tools/desplegar_hf.py --estado")
    print("=" * 66)

    for i in range(10):
        time.sleep(20)
        try:
            info = api.space_info(repo_id=repo_id)
            stage = getattr(getattr(info, "runtime", None), "stage", "?")
            print(f"  [{i+1}] estado: {stage}")
            if stage == "RUNNING":
                break
        except Exception:  # noqa: BLE001
            print(f"  [{i+1}] compilando...")
    return 0


def estado() -> int:
    from huggingface_hub import HfApi
    token = obtener("HF_TOKEN")
    if not token:
        print("Falta HF_TOKEN")
        return 1
    api = HfApi(token=token)
    usuario = api.whoami()["name"]
    import glob
    for d in glob.glob(RAIZ.parent / "*"):
        if (Path(d) / ".git").exists():
            break
    print("Consulta: https://huggingface.co/spaces/"
          f"{usuario}/<nombre-del-space>")
    return 0


if __name__ == "__main__":
    if "--estado" in sys.argv:
        sys.exit(estado())
    sys.exit(main())
