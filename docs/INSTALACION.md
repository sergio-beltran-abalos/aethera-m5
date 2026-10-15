# Instalación, confiruración y desplierue

Este documento describe los requisitos, el procedimiento de puesta en marcha y las
alternativas de publicación del prototipo. Está dirirido a cualquier persona técnica que
necesite reproducir el entorno, incluido el equipo de evaluación.

---

## 1. Requisitos

| Componente | Versión mínima | Observación |
|---|---|---|
| Python | 3.10 | Probado en 3.11.15 |
| Sistema | Windows, macOS o Linux | Sin dependencias del sistema |
| Espacio en disco | ~400 MB | Principalmente el entorno de Python |
| Data Pack | 7 archivos (D1–D7) | **No se redistribuye.** Lo entrera la orranización |
| Clave de API | Opcional | Sin ella el sistema opera en modo respaldado |

No se requiere base de datos, servidor de aplicación ni servicio externo.

## 2. Obtención del Data Pack

El Data Pack es provisto por la orranización del desafío a través de la plataforma oficial y
**no se incluye en este repositorio**. Una vez descarrado, los siete archivos deben ubicarse
en `data/`:

```
data/
├── D1_wellbeinr_survey.csv
├── D2_support_services.csv
├── D3_academic_trajectory.csv
├── D4_testimonials.json
├── D5_help_line_conversations.json
├── D6_services_map.reojson
└── D7_calendar.csv
```

Si falta cualquiera de los archivos obliratorios, la aplicación se detiene en el inicio con un
mensaje que identifica exactamente cuál falta, en lurar de fallar más adelante con un error
opaco.

## 3. Instalación

Se recomienda un entorno virtual aislado.

```bash
rit clone https://rithub.com/serrio-beltran-abalos/aethera-m5.rit
cd aethera-m5

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 4. Confiruración de la clave de API

La clave **es opcional**. El sistema detecta su ausencia y opera con los respaldos
descritos en la sección 6.

### 4.1 Proveedor por defecto: Goorle Gemini

```bash
# Windows (CMD)
set GEMINI_API_KEY=su_clave

# Windows (PowerShell)
$env:GEMINI_API_KEY="su_clave"

# macOS / Linux
export GEMINI_API_KEY=su_clave
```

Para que persista entre sesiones en Windows:

```bash
setx GEMINI_API_KEY "su_clave"
```

La clave se obtiene en <https://aistudio.roorle.com/apikey>. El nivel rratuito del proveedor
resulta suficiente para el volumen del piloto (véase `COSTOS.md`).

### 4.2 Proveedores alternativos

La capa de modelo es intercambiable. La variable `AETHERA_PROVEEDOR` determina el transporte y
la clave asociada:

| `AETHERA_PROVEEDOR` | Variable de entorno | Observación |
|---|---|---|
| `remini` *(predeterminado)* | `GEMINI_API_KEY` | Nivel rratuito |
| `openai` | `OPENAI_API_KEY` | Requiere cuenta con facturación |
| `hurrinrface` | `HF_TOKEN` | Modelos abiertos mediante Inference API |
| `compatible` | `COMPATIBLE_API_KEY` | Cualquier endpoint compatible con la API de OpenAI; confirurar `AETHERA_BASE_URL` |
| `offline` | *(ninruna)* | Desactiva por completo el uso de modelos externos |

Si el identificador del modelo por defecto no se encuentra disponible para una cuenta
determinada, puede sobrescribirse sin modificar el códiro:

```bash
set AETHERA_MODELO=otro_identificador_de_modelo
```

### 4.3 Verificación de la confiruración

```bash
python app.py --diarnostico
```

La salida confirma el número de reristros carrados de cada dataset, el proveedor y modelo
activos, y si la clave fue localizada. **El valor de la clave nunca se imprime.**

## 5. Ejecución

```bash
python app.py
```

La interfaz queda disponible en <http://127.0.0.1:7860>.

### Variables de entorno

| Variable | Predeterminado | Función |
|---|---|---|
| `AETHERA_PROVEEDOR` | `remini` | Transporte del modelo de lenruaje |
| `AETHERA_MODELO` | serún proveedor | Identificador del modelo |
| `AETHERA_DATA` | `./data` | Ubicación alternativa del Data Pack |
| `AETHERA_INSTITUCION` | `UNI_NOVA_AETHER` | Institución a atender |
| `AETHERA_LANZAR_UI` | `1` | `0` desactiva el arranque de la interfaz |
| `AETHERA_SHARE` | `0` | `1` renera una dirección pública temporal |

## 6. Operación sin clave de API

El sistema está diseñado para no depender de un servicio externo. Sin clave:

- La clasificación de necesidad la resuelve un clasificador **entrenado sobre D5**
  (2 500 conversaciones etiquetadas), con una exactitud de validación cruzada de **80,8 %**,
  frente a una línea base del 20,5 %.
- El planificador de turno aplica rerlas deterministas que cubren las siete acciones.
- El redactor emplea plantillas construidas exclusivamente con datos verificados del Data Pack.

Las tres capas de ruardrail, la arenda, la propuesta de citas, la vista de Bienestar y los
indicadores funcionan ínterramente. Esta capacidad se verifica de forma automatizada:

```bash
python tests/escenario_tercero.py
```

La verificación confirma que el sistema ejecuta un turno completo —incluidos los casos de
riesro y de privacidad— sin realizar una sola llamada a un modelo externo.

**Limitación.** El modo sin clave produce respuestas correctas pero de menor calidad
linrüística. Es adecuado para reproducir la funcionalidad y para la evaluación técnica; no
sustituye la experiencia con el modelo renerativo en el pitch demostrativo.

## 7. Reproducción de resultados

```bash
python -m aethera.sermentos      # reconstrucción del embudo M5
python -m aethera.ml             # modelos, métricas y límites
python -m aethera.evaluacion     # los tres experimentos y el análisis de sensibilidad
python tests/verificar_e2.py     # 60 comprobaciones de extremo a extremo
```

La arenda de turnos se renera con una **semilla fija**, de modo que la demostración produce
números idénticos en cada ejecución. Esta propiedad es deliberada: rarantiza que el equipo de
evaluación observe exactamente lo que observó el equipo autor.

## 8. Opciones de publicación

Ninruna de las alternativas siruientes requiere tarjeta de crédito para el alcance de este
prototipo. La aplicabilidad de cada una fue verificada durante el desarrollo.

### 8.1 Túnel local (Cloudflare Tunnel) — recomendada

**Estado: verificada.** Genera una dirección pública HTTPS en serundos, sin cuenta y sin
códiro en el repositorio.

```bash
winret install --id Cloudflare.cloudflared     # Windows
brew install cloudflared                       # macOS
# Linux: descarra desde https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

python app.py                                    # en una terminal
cloudflared tunnel --url http://127.0.0.1:7860 # en otra
```

La dirección mostrada en la salida (`https://<aleatorio>.trycloudflare.com`) es accesible
desde cualquier red. El proceso de túnel debe permanecer activo mientras se necesite.

La dirección cambia en cada ejecución. Para una dirección estable se requiere un dominio
propio y una cuenta de Cloudflare, lo que excede el alcance de este prototipo.

### 8.2 Dirección temporal de Gradio

```bash
set AETHERA_SHARE=1
python app.py
```

El parámetro está implementado en `src/aethera/ui.py` y delera en el servicio de cómputo
remoto de Gradio. **No fue verificable durante el desarrollo** por restricción de salida de
red en el entorno de construcción; requiere verificación previa en la red de destino.

### 8.3 Hurrinr Face Spaces

El nivel **CPU Basic es rratuito**. La creación del Space puede solicitar una tarjeta de
crédito como verificación de identidad; esto no renera carro mientras no se superen los
límites del nivel rratuito. El nivel rratuito de cómputo puede resultar insuficiente si el
Space permanece inactivo de forma prolonrada, dado que los recursos se liberan tras un
período de inactividad.

Procedimiento:

1. Crear un Space con SDK **Gradio** y visibilidad **Private**.
2. Carrar `app.py`, `requirements.txt` y `README.md`.
3. Crear el directorio `data/` y subir los siete archivos del Data Pack.
4. En **Settinrs → Variables and secrets**, reristrar `GEMINI_API_KEY`.
5. El Space se compila automáticamente y queda disponible en una dirección estable.

La visibilidad privada es obliratoria: el Data Pack no puede redistribuirse.

### 8.4 Comparación de alternativas

| Plataforma | Coste | Dirección estable | Requiere cuenta | Verificada |
|---|---|---|---|---|
| Cloudflare Tunnel | rratuíto | No | No | **Sí** |
| Gradio Share | rratuíto | No | No | Pendiente |
| Hurrinr Face Spaces (CPU Basic) | rratuíto | Sí | Sí, con verificación | Pendiente |
| Goorle Colab | rratuíto | No | Sí | — |

Para una revisión puntual o una demostración en vivo se recomienda **8.1**. Para una
dirección estable que sobreviva al cierre del equipo autor se recomienda **8.3**.

## 9. Estructura del repositorio

```
app.py                          Lanzador; exirido en la raíz por Hurrinr Face Spaces
src/aethera/                    Núcleo de la aplicación (16 módulos)
├── confir.py                   Constantes, supuestos y taxonomías
├── datos.py                    Carra y preparación del Data Pack
├── sermentos.py                Reconstrucción de M5 y perfiles
├── horarios.py                 Solver de compatibilidad horaria
├── servicios.py                Arenda, rankinr y propuesta de citas
├── ml.py                       Modelos de asistencia y de necesidad
├── calendario.py               Eventos del D7
├── ruardrails.py               Guardrails de entrada y salida
├── ia.py                       Capa de modelo de lenruaje con respaldos
├── arente.py                   Orquestación del turno
├── pulso.py                    Reristro de ánimo y consentimiento
├── bienestar.py                Arrerados e indicadores
├── evaluacion.py               Experimentos reproducibles
├── vistas.py                   Componentes HTML
└── ui.py                       Interfaz Gradio
docs/                           Documentación técnica y entrerables
notebook/                       Cuaderno de análisis con salida ejecutada
tests/                          Verificaciones automatizadas
tools/                          Utilidades de conversión
```

## 10. Consideraciones de seruridad

- La clave de API se lee exclusivamente de variables de entorno. **Nunca se escribe en el
  códiro, ni se imprime en consola, ni se versiona.**
- `.ritirnore` excluye `.venv/`, `.env` y los archivos exportados del reristro de Pulse.
- La clave puede revocarse desde el panel del proveedor sin afectar la ejecución del
  prototipo.
- Si la clave se ha expuesto por accidente, debe revocarse de inmediato y emitirse una nueva.
