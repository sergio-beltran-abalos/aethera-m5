---
title: Aethera Pulse + Ruta
emoji: 🌤️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
pinned: false
---

# Aethera Pulse + Ruta

**Entregable 2 · Desafío Ciudad Aethera · Misión M5: estigma y baja búsqueda de ayuda**

Prototipo funcional de un asistente que convierte *«necesito ayuda»* en **una cita que el
estudiante realmente puede cumplir**. Datos 100 % sintéticos del Data Pack de la organización.

---

## 1. Equipo

| | |
|---|---|
| **Equipo** | Aethera Pulse + Ruta |
| **Institución objetivo** | UNI_NOVA_AETHER (ver §7, escalabilidad) |
| **Contacto** | Sergio Edmundo Beltran Abalos · sergio.beltran@utec.edu.pe |

### Integrantes

| # | Nombre | Institución | Rol |
|---|---|---|---|
| 1 | **Sergio Edmundo Beltran Abalos** | Universidad de Ingeniería y Tecnología (UTEC), Perú | **Líder** · arquitectura, modelo de asistencia y solver de horario |
| 2 | Luis Angel De La Cruz Sánchez | Universidad Antonio Ruiz de Montoya, Perú | Análisis de datos · evaluación offline y segmentación |
| 3 | Jean Sanchez Cardenas | Universidad Nacional de Ingeniería, Perú | Data engineering · Data Pack y modelo de necesidad |
| 4 | Vladimir Jaward Hanco Soncco | Universidad Nacional de San Agustín de Arequipa, Perú | Producto e interfaz · experiencia de Pulse y Ruta |
| 5 | Ana Mahns Condeza | Pontificia Universidad Católica de Chile, Chile | IA responsable y privacidad · ficha, guardrails y VIEW agregada |

> **Multidisciplinaria por necesidad, no por casualidad.** El enunciado advierte que no todos
> deben leer los archivos JSON: cada integrante tocó una capa. El equipo cubre las tres
> instituciones y los dos países del desafío.

## 2. Misión abordada

**M5 — Estigma y baja búsqueda de ayuda.** Indicador de línea base: **68 %** de los
estudiantes con sintomatología ansiosa moderada-alta nunca consultó un servicio de apoyo.

> **Continuidad E1 → E2.** El Entregable 1 delimitó *dónde* está la brecha, con D1/D2/D3/D6/D7.
> Para el Entregable 2 analizamos **D4 y D5**, que llegaron en la segunda oleada, y ahí
> aparecieron las tres causas concretas que la app ataca (ver §5).

## 3. Qué hace y cómo funciona

**Qué hace (2–3 líneas).** Pulse es un check-in de ánimo de 20 segundos, opcional y privado.
Ruta es un asistente de IA de orientación **no clínica** que traduce lenguaje cotidiano a un
motivo no clínico, consulta el catálogo y el calendario, y **propone solo citas compatibles
con el horario real del estudiante**: nada que choque con sus clases, su trabajo ni el tiempo
de traslado. Si no hay ninguna cita posible, ofrece pares como primer contacto y escala a una
persona. **No diagnostica, no receta y no atiende emergencias.**

**Arquitectura.** Un turno atraviesa cinco capas:

```
mensaje
  ① Guardrail de entrada   patrones: crisis · clínico · privacidad · manipulación
  ② Planificador          el LLM elige acción + preferencias + señal de riesgo
       └─ 2.ª capa: el LLM detecta riesgo que las reglas no ven
  ③ Herramientas          clasificación, calendario, catálogo, agenda, modelo ML
  ④ Redactor              el LLM redacta SOLO con los resultados de ③
  ⑤ Guardrail de salida   valida la respuesta; si falla → plantilla con datos verificados
```

**El principio que lo sostiene: el modelo de lenguaje nunca decide datos.** Solo decide *qué
hacer* y *cómo decirlo*. Servicios, fechas, horas, canales y tiempos de espera salen de
herramientas que leen el Data Pack. Si el redactor intenta inventar un servicio, una fecha o un
teléfono, el guardrail lo detecta y se descarta su respuesta.

**El motor de compatibilidad horaria es la aporte central.** No es un chatbot más: es un
solver de restricciones que cruza apertura del servicio (D6) × agenda del estudiante (D1) ×
carga académica (D3) × distancia real entre distritos (D6 GeoJSON).

## 4. Modelos y herramientas de IA

| Uso | Herramienta | Propósito |
|---|---|---|
| Clasificador, planificador y redactor | **Gemini `gemini-3.5-flash-lite`** (Google, free tier) | Elegir acción y motivo; redactar. Nunca aportan datos |
| Estimación de asistencia | Regresión logística (scikit-learn) sobre **D2** (9 400 eventos) | Ordenar citas por P(asistir) |
| Clasificador offline | TF-IDF + regresión logística sobre **D5** (2 500 etiquetadas) | Sustituye al LLM cuando no hay clave |

**Transporte multi-proveedor:** `gemini` · `openai` · `huggingface` · `compatible` · `offline`.
**Sin clave de API la app funciona completa** con el clasificador de D5 y plantillas.

## 5. Datasets del Data Pack utilizados

| | Uso en la solución |
|---|---|
| **D1** (12 000) | Segmentación M5, perfiles de demostración, horario y trabajo |
| **D2** (9 400) | Entrenamiento del modelo de asistencia; mapa motivo → servicio; esperas reales |
| **D3** (130 000) | **Carga académica (`credit_load`) que escala el bloque de clases** |
| **D4** (6 000) | Frases de normalización agregadas. Nunca se cita un relato textual |
| **D5** (2 500) | Entrenamiento del clasificador de necesidad |
| **D6** (15) | Catálogo, horarios, capacidad y **coordenadas** para el tiempo de traslado |
| **D7** (32) | Calendario académico: solo se menciona el evento pertinente al motivo |

> El Data Pack **no se redistribuye**. Copia los 7 archivos en `data/` antes de correr.

## 6. Resultados

### ¿Funciona el núcleo?

**Match Rate de Ruta: 100 %** — pero ese 100 % es por construcción, porque filtrar la agenda
*es* el producto. La cifra útil es otra:

| Medida | Valor |
|---|---|
| Turnos que muestra un directorio estático | **370 por estudiante** |
| De esos, compatibles con su horario | **28,2 %** |
| **Mediana de turnos viables por estudiante** | **0** |
| Estudiantes con algún turno viable | 87,3 % |

### ¿Clasifica bien?

| | |
|---|---|
| Clasificador de necesidad (validación cruzada, 5 folds) | **80,8 %** |
| Línea base (clase mayoritaria) | 20,5 % |
| Derivación actual del sistema, medida en D5 | **34,2 %** — es decir, **azar** (33,3 %) |

### ¿El modelo aporta?

| | |
|---|---|
| Modelo elegido | Regresión logística (AUC 0,567 > Gradient boosting 0,542) |
| Feature más importante | `espera_dias` (+0,053 AUC), luego `contact_channel` (+0,020) |
| **Y su límite, declarado** | En la franja que ofrece la demo (esperas ≤ 14 días) el AUC cae a **0,44** con solo 77 casos: **no discrimina bien**. Ruta lo muestra con un indicador de confianza en lugar de ocultarlo |

### ¿Impacto sobre el 68 %?

| Alcance 30 %, conversión 35 % | |
|---|---|
| Línea base | 68,2 % (1 868 de 2 739) |
| Proyectado | **65,0 %** (−3,2 pp) |
| Rango con supuestos plausibles | **−0,6 a −7,5 pp** |

Supuestos declarados uno por uno y con análisis de sensibilidad en
[`docs/IMPACTO.md`](docs/IMPACTO.md). Preferimos un número defendible a uno grande.

## 7. Escalabilidad

Cambiar de institución es **una variable de entorno**:

```bash
set AETHERA_INSTITUCION=INST_NEXUS
```

El Data Pack ya trae 3 instituciones y 5 distritos, y las líneas de ayuda son bilingües
(Perú 113 / Chile \*4141). No hay código específico de NOVA fuera de esa constante. Cualquier
universidad de América Latina con un directorio de servicios, un calendario y un proveedor de
IA despliega esto sin tocar el núcleo.

## 8. Privacidad e IA responsable

Consentimiento expreso · datos sensibles bajo Ley 29733 (DS 016-2024-JUS) · ARCO completo
(exportar y borrar desde la interfaz) · vista de Bienestar con supresión de celdas `< 10` ·
transferencia internacional declarada · **`anxiety_band` nunca se usa en tiempo de ejecución**.

→ Documento completo: [`docs/FICHA_IA_RESPONSABLE.md`](docs/FICHA_IA_RESPONSABLE.md)

## 9. Estructura

```
app.py                        Lanzador (HF Spaces exige app.py en la raíz)
src/aethera/
  config.py       Constantes, supuestos y taxonomías
  datos.py        Carga y preparación del Data Pack
  segmentos.py    Reconstrucción de M5 y perfiles de demo
  horarios.py     Solver de compatibilidad horaria (D1 + D3 + D6 GeoJSON)
  servicios.py    Agenda simulada, ranking y propuesta de citas
  ml.py           Modelo de asistencia + clasificador de necesidad
  calendario.py   D7 y eventos pertinentes
  guardrails.py   Guardrails de entrada y salida
  ia.py           Capa de LLM con respaldos
  agente.py       Orquestación del turno y herramientas
  pulso.py        Check-in, consentimiento, ARCO
  bienestar.py    Agregados y KPIs
  evaluacion.py   Los tres experimentos
  vistas.py       Piezas HTML
  ui.py           Gradio
docs/            Ficha de IA responsable, impacto, costos
tests/           Pruebas de humo
data/            Data Pack (no redistribuir)
```

## 10. Cómo correrlo

```bash
pip install -r requirements.txt

# Windows (CMD)
set GEMINI_API_KEY=tu_clave
# macOS / Linux:  export GEMINI_API_KEY=tu_clave
# Ojo: en PowerShell es  $env:GEMINI_API_KEY="tu_clave"

python app.py                    # abre http://127.0.0.1:7860
python app.py --diagnostico      # comprueba Data Pack, proveedor y clave
python -m aethera.evaluacion      # reproduce las cifras del §6
```

**Sin clave de API** (o con `set AETHERA_PROVEEDOR=offline`) funciona igual, usando el
clasificador de D5 y las plantillas de respaldo.

| Variable | Por defecto | Para qué |
|---|---|---|
| `AETHERA_PROVEEDOR` | `gemini` | `gemini` · `openai` · `huggingface` · `compatible` · `offline` |
| `AETHERA_MODELO` | según proveedor | Sobrescribe el id del modelo |
| `AETHERA_DATA` | `./data` | Ruta alterna del Data Pack |
| `AETHERA_INSTITUCION` | `UNI_NOVA_AETHER` | Otra institución (escalabilidad) |
| `AETHERA_LANZAR_UI` | `1` | `0` para no abrir el navegador |

## 11. Publicar en Hugging Face Spaces

1. **New Space** → SDK **Gradio** → visibilidad **Private** (el Data Pack no se redistribuye).
2. Sube `app.py`, `requirements.txt` y este `README.md`.
3. Crea `data/` y sube los **7** archivos del Data Pack.
4. **Settings → Variables and secrets** → agrega `GEMINI_API_KEY`.
5. El Space se construye solo en una dirección fija, lista para grabar el video.

## 12. Video demostrativo

<!-- ENLACE AL VIDEO -->

---

*Aethera es una ciudad universitaria ficticia del desafío binacional Chile–Perú. No hay
personas, lugares ni servicios reales. Ruta es orientación no clínica: apoya, no reemplaza la
atención profesional.*
