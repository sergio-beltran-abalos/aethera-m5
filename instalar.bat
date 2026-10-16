@echo off
REM ============================================================
REM  Aethera Pulse + Ruta · instalador automatico (Windows)
REM  Ejecuta este archivo con doble clic.
REM ============================================================

setlocal
cd /d "%~dp0"
title Aethera - Instalacion

echo.
echo  ==========================================================
echo   AETHERA PULSE + RUTA  ·  Entregable 2 (Mision M5)
echo  ==========================================================
echo.

REM ── 1. Python ─────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
  echo  [X] No se encontro Python en este equipo.
  echo      Descargalo de https://www.python.org/downloads/
  echo      Al instalar, marca "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [1/5] Python detectado: %PYVER%

REM ── 2. Data Pack ───────────────────────────────────────────
set FALTAN=0
for %%F in (D1_wellbeing_survey.csv D2_support_services.csv D3_academic_trajectory.csv D4_testimonials.json D5_help_line_conversations.json D6_services_map.geojson D7_calendar.csv) do (
  if not exist "data\%%F" (
    set FALTAN=1
  )
)

if "%FALTAN%"=="1" (
  echo.
  echo  [X] Faltan archivos del Data Pack en la carpeta data\
  echo.
  echo      El Data Pack lo entrega la organizacion del desafio
  echo      y NO se distribuye con el codigo. Copia los 7 archivos
  echo      ^(D1 a D7^) en la carpeta data\ y vuelve a ejecutar
  echo      este instalador.
  echo.
  pause
  exit /b 1
)
echo  [2/5] Data Pack completo: 7 archivos en data\

REM ── 3. Entorno virtual ─────────────────────────────────────
if not exist ".venv" (
  echo  [3/5] Creando entorno virtual...
  python -m venv .venv
) else (
  echo  [3/5] Entorno virtual ya existe
)

call .venv\Scripts\activate.bat

REM ── 4. Dependencias ────────────────────────────────────────
echo  [4/5] Instalando dependencias (puede tardar 1-2 minutos)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo.
  echo  [X] Fallo al instalar dependencias. Revisa tu conexion.
  pause
  exit /b 1
)
echo        Dependencias listas.

REM ── 5. Diagnostico y arranque ──────────────────────────────
echo  [5/5] Verificando la configuracion...
echo.
python app.py --diagnostico
echo.

if "%GEMINI_API_KEY%"=="" (
  echo  ==========================================================
  echo   Sin clave de API: la app funciona con respaldos.
  echo   Para usar el modelo de lenguaje, en otra ventana ejecuta:
  echo       setx GEMINI_API_KEY "tu_clave"
  echo   y vuelve a abrir esta.
  echo  ==========================================================
) else (
  echo  ==========================================================
  echo   Clave de API detectada: se usara el modelo de lenguaje.
  echo  ==========================================================
)

echo.
echo  Iniciando la aplicacion en http://127.0.0.1:7860
echo  Para detenerla, cierra esta ventana.
echo.
python app.py

endlocal
