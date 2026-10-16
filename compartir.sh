#!/usr/bin/env bash
# ============================================================
#  Aethera Pulse + Ruta · Servidor público gratuito (macOS / Linux)
#
#  Uso:   chmod +x compartir.sh && ./compartir.sh
#
#  Coste: 0 USD. No requiere cuenta ni tarjeta. La dirección
#  permanece activa mientras esta sesión permanezca abierta.
# ============================================================
set -e
cd "$(dirname "$0")"

echo
echo " =========================================================="
echo "  AETHERA PULSE + RUTA  ·  Servidor público gratuito"
echo " =========================================================="
echo

command -v python3 >/dev/null 2>&1 || {
  echo " [X] Python 3 no está instalado."
  echo "     Descárgalo de https://www.python.org/downloads/"
  exit 1
}
echo " [1/4] Python $(python3 --version | cut -d' ' -f2)"

FALTAN=0
for F in D1_wellbeing_survey.csv D2_support_services.csv D3_academic_trajectory.csv \
         D4_testimonials.json D5_help_line_conversations.json \
         D6_services_map.geojson D7_calendar.csv; do
  [ -f "data/$F" ] || FALTAN=1
done
[ "$FALTAN" = "1" ] && {
  echo
  echo " [X] Faltan archivos del Data Pack en data/"
  echo "     Copia los 7 archivos (D1 a D7) y vuelve a ejecutar."
  exit 1
}
echo " [2/4] Data Pack completo"

if [ ! -d ".venv" ]; then
  echo " [3/4] Preparando entorno (primera ejecución, ~2 min)..."
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r requirements.txt
else
  echo " [3/4] Entorno ya preparado"
  source .venv/bin/activate
fi

command -v cloudflared >/dev/null 2>&1 || {
  echo
  echo " Instalando Cloudflare Tunnel..."
  if command -v brew >/dev/null 2>&1; then
    brew install cloudflared
  else
    echo " [X] Instala Cloudflare Tunnel manualmente:"
    echo "     https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
  fi
}
echo " [4/4] Cloudflare Tunnel disponible"

if lsof -i :7860 >/dev/null 2>&1; then
  echo
  echo " [!] El puerto 7860 ya está ocupado."
  echo "     Puede que la aplicación ya esté corriendo en"
  echo "     http://127.0.0.1:7860"
  exit 1
fi

echo
echo " Iniciando la aplicación..."
python app.py &
APP_PID=$!
sleep 12

echo
echo " =========================================================="
echo "  Generando la dirección pública (unos 30 segundos)."
echo
echo "  La URL aparecerá abajo. Cópiala y compártela."
echo
echo "  Presiona Ctrl+C para detener el servidor."
echo " =========================================================="
echo

trap 'echo; echo " Deteniendo..."; kill $APP_PID 2>/dev/null || true; pkill -f "cloudflared tunnel" 2>/dev/null || true; exit 0' INT TERM

cloudflared tunnel --no-autoupdate --url http://127.0.0.1:7860
