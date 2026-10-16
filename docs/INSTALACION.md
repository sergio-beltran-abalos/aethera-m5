# Instalación, configuración y despliegue

Este documento describe los requisitos, el procedimiento de puesta en marcha y las
alternativas de publicación del prototipo. Está dirigido a cualquier persona técnica que
necesite reproducir el entorno, incluido el equipo de evaluación.

---

## 1. Requisitos

| Componente | Versión mínima | Observación |
|---|---|---|
| Python | 3.10 | Verificado en 3.11.15 |
| Sistema | Windows, macOS o Linux | Sin dependencias del sistema |
| Espacio en disco | ~400 MB | Principalmente el entorno de Python |
| Data Pack | 7 archivos (D1–D7) | **No se redistribuye.** Lo entrega la organización |
| Clave de API | Opcional | Sin ella el sistema opera en modo respaldado |

No se requiere base de datos, servidor de aplicación ni servicio externo.

## 2. Obtención del Data Pack

El Data Pack es provisto por la organización del desafío a través de la plataforma oficial y
**no se incluye en este repositorio**. Una vez descargado, los siete archivos deben ubicarse
en el directorio `data/`:

```
data/
├── D1_wellbeing_survey.csv
├── D2_support_services.csv
├── D3_academic_trajectory.csv
├── D4_testimonials.json
├── D5_help_line_conversations.json
├── D6_services_map.geojson
└── D7_calendar.csv
```

Si falta cualquiera de los archivos obligatorios, la aplicación se detiene en el arranque con
un mensaje que identifica exactamente cuál falta, en lugar de fallar más adelante con un
error no descriptivo.

## 3. Instalación

### 3.1 Procedimiento automático

El repositorio incluye un instalador que comprueba el entorno, crea el entorno virtual,
instala las dependencias y verifica la configuración. **Es el procedimiento recomendado
para el equipo.**

| Sistema | Archivo | Ejecución |
|---|---|---|
| Windows | `instalar.bat` | Doble clic sobre el archivo |
| macOS / Linux | `instalar.sh` | `chmod +x instalar.sh && ./instalar.sh` |

Ambos instaladores verifican la presencia de los siete archivos del Data Pack y detienen la
ejecución indicando cuál falta. También.info si la clave de API fue detectada.

### 3.2 Procedimiento manual

Se recomienda un entorno virtual aislado.

```bash
git clone https://github.com/sergio-beltran-abalos/aethera-m5.git
cd aethera-m5

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 4. Configuración de la clave de API

La clave **es opcional**. El sistema detecta su ausencia y opera con los respaldos descritos
en la sección 7.

### 4.1 Proveedor predeterminado: Google Gemini

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

La clave se obtiene en <https://aistudio.google.com/apikey>. El nivel gratuito del proveedor
resulta suficiente para el volumen del piloto (véase `COSTOS.md`).

### 4.2 Proveedores alternativos

La capa de modelo es intercambiable. La variable `AETHERA_PROVEEDOR` determina el transporte
y la clave asociada:

| `AETHERA_PROVEEDOR` | Variable de entorno | Observación |
|---|---|---|
| `gemini` *(predeterminado)* | `GEMINI_API_KEY` | Nivel gratuito |
| `openai` | `OPENAI_API_KEY` | Requiere cuenta con facturación |
| `huggingface` | `HF_TOKEN` | Modelos abiertos mediante Inference API |
| `compatible` | `COMPATIBLE_API_KEY` | Endpoint compatible con la API de OpenAI; configurar `AETHERA_BASE_URL` |
| `offline` | *(ninguna)* | Desactiva el uso de modelos externos |

Si el identificador del modelo predeterminado no se encuentra disponible para una cuenta
determinada, puede sobrescribirse sin modificar el código:

```bash
set AETHERA_MODELO=otro_identificador_de_modelo
```

### 4.3 Verificación de la configuración

```bash
python app.py --diagnostico
```

La salida confirma el número de registros cargados de cada dataset, el proveedor y modelo
activos, y si la clave fue localizada. **El valor de la clave nunca se imprime.**

## 5. Ejecución

```bash
python app.py
```

La interfaz queda disponible en <http://127.0.0.1:7860>.

### Variables de entorno

| Variable | Predeterminado | Función |
|---|---|---|
| `AETHERA_PROVEEDOR` | `gemini` | Transporte del modelo de lenguaje |
| `AETHERA_MODELO` | según proveedor | Identificador del modelo |
| `AETHERA_DATA` | `./data` | Ubicación alternativa del Data Pack |
| `AETHERA_INSTITUCION` | `UNI_NOVA_AETHER` | Institución a atender |
| `AETHERA_LANZAR_UI` | `1` | `0` desactiva el arranque de la interfaz |
| `AETHERA_SHARE` | `0` | `1` genera una dirección pública temporal |

## 6. Estructura del repositorio

```
instalar.bat                  Instalador automático para Windows
instalar.sh                   Instalador automático para macOS y Linux
app.py                        Lanzador; exigido en la raíz por Hugging Face Spaces
src/aethera/                  Núcleo de la aplicación (16 módulos)
├── config.py                 Constantes, supuestos y taxonomías
├── datos.py                  Carga y preparación del Data Pack
├── segmentos.py              Reconstrucción de M5 y perfiles
├── horarios.py               Solver de compatibilidad horaria
├── servicios.py              Agenda, ranking y propuesta de citas
├── ml.py                     Modelos de asistencia y de necesidad
├── calendario.py             Eventos del calendario académico
├── guardrails.py             Guardrails de entrada y salida
├── ia.py                     Capa de modelo de lenguaje con respaldos
├── agente.py                 Orquestación del turno
├── pulso.py                  Registro de ánimo y consentimiento
├── bienestar.py              Agregados e indicadores
├── evaluacion.py             Experimentos reproducibles
├── vistas.py                 Componentes HTML
└── ui.py                     Interfaz Gradio
docs/                         Documentación técnica y entregables
notebook/                     Cuaderno de análisis con salida ejecutada
tests/                        Verificaciones automatizadas
tools/                        Utilidades de conversión
```

## 7. Operación sin clave de API

El sistema está diseñado para no depender de un servicio externo. En ausencia de clave:

- La clasificación de necesidad la resuelve un clasificador **entrenado sobre D5**
  (2 500 conversaciones etiquetadas), con una exactitud de validación cruzada de **80,8 %**,
  frente a una línea base del 20,5 %.
- El planificador de turno aplica reglas deterministas que cubren las siete acciones.
- El redactor emplea plantillas construidas exclusivamente con datos verificados del Data Pack.

Las tres capas de guardrail, la agenda, la propuesta de citas, la vista de Bienestar y los
indicadores funcionan íntegramente. Esta capacidad se verifica de forma automatizada:

```bash
python tests/escenario_tercero.py
```

La comprobación confirma que el sistema ejecuta un turno completo —incluidos los casos de
riesgo y de privacidad— sin realizar una sola llamada a un modelo externo.

**Limitación.** El modo sin clave produce respuestas correctas pero de menor calidad
lingüística. Resulta adecuado para reproducir la funcionalidad y para la evaluación técnica;
no sustituye la experiencia con el modelo generativo en la demostración.

## 8. Reproducción de resultados

```bash
python -m aethera.segmentos      # reconstrucción del embudo M5
python -m aethera.ml             # modelos, métricas y límites
python -m aethera.evaluacion     # los tres experimentos y el análisis de sensibilidad
python tests/verificar_e2.py     # 60 comprobaciones de extremo a extremo
python tests/revisar_docs.py     # integridad de la documentación
```

La agenda de turnos se genera con una **semilla fija**, de modo que la demostración produce
números idénticos en cada ejecución. Esta propiedad es deliberada: garantiza que el equipo de
evaluación observe exactamente lo que observó el equipo autor.

## 9. Opciones de publicación

Ninguna de las alternativas siguientes requiere tarjeta de crédito para el alcance de este
prototipo. La aplicabilidad de cada una fue verificada durante el desarrollo.

### 9.1 Túnel local (Cloudflare Tunnel) — recomendada

**Estado: verificada.** Genera una dirección pública HTTPS en segundos, sin cuenta y sin
código en el repositorio.

```bash
winget install --id Cloudflare.cloudflared     # Windows
brew install cloudflared                       # macOS
# Linux: descarga desde developers.cloudflare.com

python app.py                                    # en una terminal
cloudflared tunnel --url http://127.0.0.1:7860 # en otra
```

La dirección mostrada en la salida (`https://<aleatorio>.trycloudflare.com`) es accesible
desde cualquier red. El proceso de túnel debe permanecer activo mientras se necesite.

La dirección cambia en cada ejecución. Para una dirección estable se requiere un dominio
propio y una cuenta de Cloudflare, lo que excede el alcance de este prototipo.

### 9.2 Dirección temporal de Gradio

```bash
set AETHERA_SHARE=1
python app.py
```

El parámetro está implementado en `src/aethera/ui.py` y delega en el servicio de cómputo
remoto de Gradio. **No fue verificable durante el desarrollo** por restricción de salida de
red en el entorno de construcción; requiere verificación previa en la red de destino.

### 9.3 Hugging Face Spaces

El nivel **CPU Basic es gratuito**. La creación del Space puede solicitar una tarjeta de
crédito como verificación de identidad; esto no genera cargo mientras no se superen los
límites del nivel gratuito. Los recursos del nivel gratuito pueden liberarse tras un período
prolongado de inactividad.

Procedimiento:

1. Crear un Space con SDK **Gradio** y visibilidad **Private**.
2. Cargar `app.py`, `requirements.txt` y `README.md`.
3. Crear el directorio `data/` y subir los siete archivos del Data Pack.
4. En **Settings → Variables and secrets**, registrar `GEMINI_API_KEY`.
5. El Space se compila automáticamente y queda disponible en una dirección estable.

La visibilidad privada es obligatoria: el Data Pack no puede redistribuirse.

### 9.4 Comparación de alternativas

| Plataforma | Coste | Dirección estable | Requiere cuenta | Verificada |
|---|---|---|---|---|
| Cloudflare Tunnel | gratuito | No | No | **Sí** |
| Gradio Share | gratuito | No | No | Pendiente |
| Hugging Face Spaces (CPU Basic) | gratuito | Sí | Sí, con verificación | Pendiente |
| Google Colab | gratuito | No | Sí | — |

Para una revisión puntual o una demostración en vivo se recomienda **9.1**. Para una
dirección estable que sobreviva al cierre del equipo autor se recomienda **9.3**.

## 10. Consideraciones de seguridad

- La clave de API se lee exclusivamente de variables de entorno. **Nunca se escribe en el
  código, ni se imprime en consola, ni se versiona.**
- `.gitignore` excluye `.venv/`, `.env` y los archivos exportados del registro de Pulse.
- La clave puede revocarse desde el panel del proveedor sin afectar la ejecución del
  prototipo.
- Si la clave se ha expuesto por accidente, debe revocarse de inmediato y emitirse una nueva.
