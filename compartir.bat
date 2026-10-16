@echo off
REM ============================================================
REM  Aethera Pulse + Ruta · Servidor publico gratuito (Windows)
REM
REM  Doble clic en este archivo. Levanta la aplicacion en tu
REM  equipo y genera una direccion publica HTTPS para que el
REM  equipo pueda abrirla desde cualquier red.
REM
REM  Coste: 0 USD. No requiere cuenta, tarjeta ni tarjeta de
REM  credito. La direccion permanece activa mientras esta
REM  ventana permanezca abierta.
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Aethera - Servidor publico

echo.
echo  ==========================================================
echo   AETHERA PULSE + RUTA  ·  Servidor publico gratuito
echo  ==========================================================
echo.

REM ── 1. Python ────────────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
  echo  [X] Python no esta instalado.
  echo      Descargalo de https://www.python.org/downloads/
  echo      Al instalar, marca "Add Python to PATH".
  pause
  exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [1/4] Python %PYVER%

REM ── 2. Data Pack ─────────────────────────────────────────────────────────
set FALTAN=0
for %%F in (D1_wellbeing_survey.csv D2_support_services.csv D3_academic_trajectory.csv D4_testimonials.json D5_help_line_conversations.json D6_services_map.geojson D7_calendar.csv) do (
  if not exist "data\%%F" set FALTAN=1
)
if "%FALTAN%"=="1" (
  echo.
  echo  [X] Faltan archivos del Data Pack en data\
  echo      Copia los 7 archivos (D1 a D7) y vuelve a ejecutar.
  echo.
  pause
  exit /b 1
)
echo  [2/4] Data Pack completo

REM ── 3. Entorno y dependencias ────────────────────────────────────────────
if not exist ".venv" (
  echo  [3/4] Preparando entorno ^(primera ejecucion, ~2 min^)^...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r requirements.txt
  if errorlevel 1 (
    echo  [X] No se pudieron instalar las dependencias.
    pause
    exit /b 1
  )
) else (
  echo  [3/4] Entorno ya preparado
)

REM ── 4. Comprobacion del puerto ───────────────────────────────────────────
echo  [4/4] Verificando que el puerto 7860 este libre...
netstat -ano | findstr ":7860" | findstr "LISTENING" >nul
if not errorlevel 1 (
  echo  [!] El puerto 7860 ya esta ocupado.
  echo      Puede que la aplicacion ya este corriendo.
  echo      Revisa http://127.0.0.1:7860 en el navegador.
  echo.
  pause
  exit /b 1
)

REM ── Cloudflare Tunnel ────────────────────────────────────────────────────
where cloudflared >nul 2>&1
if errorlevel 1 (
  if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
    set PATH=%PATH%;C:\Program Files (x86)\cloudflared
  ) else (
    if exist "C:\Program Files\cloudflared\cloudflared.exe" (
      set PATH=%PATH%;C:\Program Files\cloudflared
    ) else (
      echo.
      echo  Instalando Cloudflare Tunnel...
      winget install --id Cloudflare.cloudflared --exact --silent ^
        --accept-source-agreements --accept-package-agreements --disable-interactivity
      if errorlevel 1 (
        echo  [X] No se pudo instalar Cloudflare Tunnel.
        echo      Descargalo de https://developers.cloudflare.com/cloudflare-one/
        pause
        exit /b 1
      )
      set PATH=%PATH%;C:\Program Files (x86)\cloudflared
    )
  )
)

REM ── Arranque ─────────────────────────────────────────────────────────────
echo.
echo  Iniciando la aplicacion...
start "Aethera Pulse + Ruta" cmd /c "call .venv\Scripts\activate.bat && python app.py"

timeout /t 12 /nobreak >nul

echo  Abriendo el tunel publico...
start "Aethera - Tunel" cmd /c "cloudflared tunnel --no-autoupdate --url http://127.0.0.1:7860"

echo.
echo  ==========================================================
echo   Generando la direccion publica. Tarda unos 30 segundos.
echo.
echo   La direccion aparecera en la ventana titled
echo   "Aethera - Tunel". Copiala y compartela.
echo.
echo   NO CIERRES ESTA VENTANA mientras quieras que
echo   la direccion siga activa.
echo  ==========================================================
echo.

start "" http://127.0.0.1:7860

echo  Presiona cualquier tecla para dejar de servir.
echo  (esto apaga el tunel y la aplicacion)
echo.
pause >nul

echo  Deteniendo...
taskkill /FI "WINDOWTITLE eq Aethera - Tunel*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Aethera Pulse + Ruta*" /T /F >nul 2>&1
echo  Servidor detenido.

endlocal
