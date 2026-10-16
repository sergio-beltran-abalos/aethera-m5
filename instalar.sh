#!/usr/bin/env bash
# ============================================================
#  Aethera Pulse + Ruta · instalador automático (macOS / Linux)
#  Ejecuta:  chmod +x instalar.sh  &&  ./instalar.sh
# ============================================================
set -e
cd "$(dirname "$0")"

echo
echo " =========================================================="
echo "  AETHERA PULSE + RUTA  ·  Entregable 2 (Misión M5)"
echo " =========================================================="
echo

# ── 1. Python ───────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  echo " [X] No se encontró Python 3 en este equipo."
  echo "     Instálalo desde https://www.python.org/downloads/"
  exit 1
fi
echo " [1/5] Python detectado: $(python3 --version)"

# ── 2. Data Pack ─────────────────────────────────────────────
FALTAN=0
for F in D1_wellbeing_survey.csv D2_support_services.csv D3_academic_trajectory.csv \
         D4_testimonials.json D5_help_line_conversations.json \
         D6_services_map.geojson D7_calendar.csv; do
  [ -f "data/$F" ] || FALTAN=1
done

if [ "$FALTAN" = "1" ]; then
  echo
  echo " [X] Faltan archivos del Data Pack en la carpeta data/"
  echo
  echo "     El Data Pack lo entrega la organización del desafío y NO"
  echo "     se distribuye con el código. Copia los 7 archivos (D1 a D7)"
  echo "     en la carpeta data/ y vuelve a ejecutar este instalador."
  echo
  exit 1
fi
echo " [2/5] Data Pack completo: 7 archivos en data/"

# ── 3. Entorno virtual ───────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo " [3/5] Creando entorno virtual..."
  python3 -m venv .venv
else
  echo " [3/5] El entorno virtual ya existe"
fi
source .venv/bin/activate

# ── 4. Dependencias ──────────────────────────────────────────
echo " [4/5] Instalando dependencias (puede tardar 1-2 minutos)..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo "       Dependencias listas."

# ── 5. Diagnóstico y arranque ────────────────────────────────
echo " [5/5] Verificando la configuración..."
echo
python app.py --diagnostico
echo

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo " =========================================================="
  echo "  Sin clave de API: la aplicación funciona con respaldos."
  echo "  Para usar el modelo de lenguaje:"
  echo "      export GEMINI_API_KEY=\"tu_clave\""
  echo " =========================================================="
else
  echo " =========================================================="
  echo "  Clave de API detectada: se usará el modelo de lenguaje."
  echo " =========================================================="
fi

echo
echo " Iniciando la aplicación en http://127.0.0.1:7860"
echo " Para detenerla, presiona Ctrl+C."
echo
python app.py
