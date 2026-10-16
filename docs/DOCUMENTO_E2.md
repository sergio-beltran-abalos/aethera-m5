# Entregable 2 — Aethera Pulse + Ruta
**Desafío Ciudad Aethera · Misión M5: estigma y baja búsqueda de ayuda**  
**Indicador de línea base:** 68 % de los estudiantes con sintomatología ansiosa moderada-alta nunca consultó un servicio de apoyo.

---

## 1. El problema, delimitado con evidencia cuantitativa

El Entregable 1 identificó la brecha general en la universidad ficticia UNI_NOVA_AETHER utilizando la primera oleada de datos (D1, D2, D3, D6, D7). Para este Entregable 2 analizamos en profundidad **D4 (testimonios)** y **D5 (conversaciones históricas de orientación)**, lo que permitió aislar la causa real del problema: **la incompatibilidad operativa y el estigma social**, más que el desinterés estudiantil.

### El embudo cuantitativo de la Misión M5
*(Reproducible ejecutando `python -m aethera.segmentos`)*

| Etapa del embudo | Estudiantes | Proporción |
|---|:---:|:---:|
| Encuestados totales en UNI_NOVA_AETHER (D1) | 6 697 | 100,0 % |
| Estudiantes con ansiedad moderada o alta | 2 739 | 40,9 % |
| **Población M5: con malestar que nunca consultó apoyo** | **1 868** | **68,2 %** |
| **Segmento prioritario (M5 con ≥ 2 fricciones simultáneas)** | **826** | **44,2 % de M5** |

### Tres hallazgos empíricos que definieron el diseño técnico
*(Verificados mediante `python -m aethera.evaluacion`)*

1. **La demanda de ayuda es predominantemente nocturna y asíncrona:**  
   Al analizar las 2 500 interacciones de D5, el **62,0 % de las conversaciones se inician fuera del horario de oficina** (lunes a viernes de 09:00 a 18:00) y un **50,0 % ocurre entre las 18:00 y las 06:00**. Los canales tradicionales están cerrados cuando el malestar alcanza su pico.
2. **La derivación histórica del sistema actual opera al nivel del azar:**  
   Solo el **34,2 %** de las derivaciones registradas en D5 coinciden con el tipo de servicio que el historial clínico de D2 asocia a ese motivo (línea base de azar entre 3 opciones = 33,3 %). No existía un criterio estandarizado de derivación.
3. **El directorio estático satura y genera exclusión:**  
   Un directorio común expone al estudiante a un promedio de **370 turnos** en una ventana de 14 días. Para el segmento prioritario, solo el **28,2 %** de esos turnos es compatible con su horario de trabajo y estudio; la mediana de turnos viables para un estudiante trabajador es de **cero**, y el **12,7 %** del segmento no tiene una sola opción útil.

La conclusión técnica es clara: la información existía en el campus, pero estaba sepultada bajo cientos de opciones inviables.

---

## 2. Arquitectura de la Solución: Pulse + Ruta

La propuesta desacopla la autoevaluación preventiva del proceso de derivación y reserva a través de dos módulos integrados:

### A. Pulse — Autoconocimiento preventivo y soberanía de datos
Check-in diario de 20 segundos. No es un test psicométrico: no emite diagnósticos, no calcula puntajes de riesgo clínico ni etiqueta al estudiante.
* **Mapeo cromático:** Genera un registro visual mensual en colores que ayuda al estudiante a objetivar patrones difusos (por ejemplo, «llevo 3 semanas seguidas con días pesados»).
* **Banner contextual sincronizado (D7):** Lee el calendario académico institucional y contextualiza la experiencia según el momento del semestre (por ejemplo, identificando la semana previa a exámenes finales, cuando el estrés colectivo es esperable y natural).
* **Privacidad estricta por diseño (ARCO):** Requiere consentimiento previo explícito (Ley 29733). El estudiante puede descargar su historial completo en JSON o suprimirlo de forma definitiva en un solo clic desde la interfaz.

### B. Ruta — Asistente de IA agéntica con solver de restricciones
Sistema conversacional de orientación **no clínica** que actúa como puente hacia los recursos del campus.
1. **Acompañamiento exploratorio:** Si el estudiante no sabe definir lo que siente (*«no sé qué me pasa, ando raro»*), no impone citas prematuras ni diagnostica; acompaña empáticamente hasta que el estudiante logra expresar su situación.
2. **Clasificación no clínica:** Asigna el problema a una taxonomía cerrada de 5 motivos operativos.
3. **Solver de restricciones horarias y geográficas:** Cruza la disponibilidad del estudiante con la oferta real del campus (D6), descartando turnos incompatibles.
4. **Reserva y gestión del estigma:** Permite confirmar la cita y elegir cómo se registrará en el calendario institucional (por defecto, con título neutro: `Cita campus`).

---

## 3. Implementación de Inteligencia Artificial

### 3.1 Arquitectura Agéntica en Tres Capas (Separación de Decisión y Datos)
Uno de los principios de diseño más estrictos del proyecto es que **los modelos de lenguaje generativos jamás inventan datos operativos**. La arquitectura aísla las funciones del LLM en pasos independientes con validación intermedia:

```
[ Mensaje del estudiante ]
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│ 1. GUARDRAIL DE ENTRADA (Reglas deterministas)          │
│    Filtra crisis aguda, peticiones clínicas, privacidad  │
└──────────────────────────┬───────────────────────────────┘
                           │ (Permitido)
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 2. PLANIFICADOR (LLM: Acción + Parámetros)               │
│    Decide la acción (orientar, explorar, informar, etc.) │
│    y extrae restricciones (días, franjas, modalidad)     │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 3. HERRAMIENTAS COMPUTACIONALES Y SOLVER (Código Python) │
│    • Clasificador de motivo (Taxonomía cerrada D5/Reglas)│
│    • Inyección de Contexto RAG (Catálogo D6 + Cal D7)    │
│    • Solver de horarios (Agenda D1 + Créditos D3)        │
│    • Ranking probabilístico (Modelo ML entrenado en D2)  │
└──────────────────────────┬───────────────────────────────┘
                           │ (Resultados estructurados)
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 4. REDACTOR CONTROLADO (LLM)                             │
│    Formula la respuesta usando EXCLUSIVAMENTE los datos  │
│    entregados por las herramientas (cero alucinación)    │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ 5. GUARDRAIL DE SALIDA (Auditoría léxica y de entidades) │
│    Verifica que nombres de sedes, IDs y teléfonos        │
│    pertenezcan estrictamente al Data Pack. Si falla,     │
│    descarta el texto y emite una plantilla verificada.   │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
[ Respuesta al estudiante / Citas viables ]
```

### 3.2 Inyección de Contexto Dinámico (RAG Estructurado)
En lugar de depender de una base vectorial pesada y propensa a ruido semántico, Ruta implementa un **RAG determinista estructurado** que construye el contexto en tiempo de ejecución:
* **Recuperación del catálogo (D6):** Extrae sedes, modalidades (virtual, telefónica, presencial), horarios y distritos reales de los 15 servicios del campus.
* **Recuperación del calendario institucional (D7):** Detecta hitos académicos cercanos (semana de pausa, exámenes parciales/finales) para justificar proactivamente el momento del contacto.
* **Testimonios agregados (D4):** Recupera patrones normalizadores despersonalizados para transmitir que el malestar por carga académica o adaptación es una vivencia compartida por otros compañeros, reduciendo la sensación de aislamiento sin revelar la privacidad de nadie.

### 3.3 Modelos de Machine Learning Propios (Entrenamiento Local)
El sistema no se apoya únicamente en APIs externas; incorpora dos modelos entrenados sobre los datasets provistos:

1. **Modelo de Probabilidad de Asistencia (Entrenado sobre D2 · 9 400 atenciones):**  
   * **Algoritmo:** Regresión Logística regularizada con preprocesamiento de variables categóricas (canal, tipo de servicio, motivo) y numéricas (`wait_days`).
   * **Rendimiento:** AUC global de **0,567** (frente a 0,500 de azar).
   * **Hallazgo clave de explicabilidad:** La importancia por permutación confirmó que `wait_days` es la variable dominante (+0,053 AUC). La tasa de asistencia decae del **75,3 %** en citas con espera menor a 14 días al **63,7 %** en esperas mayores a 45 días.
   * **Transparencia radical sobre límites del modelo:** En la franja de espera corta de la demo (1 a 14 días), el dataset histórico solo tiene el 3,4 % de sus registros, por lo que el modelo rinde con un AUC de **0,44** (bajo el azar). El sistema detecta esta condición de extrapolación, calcula un **índice de confianza estadístico** y lo expone abiertamente tanto en el panel de trazas como en la vista de Bienestar.
2. **Clasificador de Necesidad Textual (Entrenado sobre D5 · 2 500 contactos):**  
   * **Algoritmo:** Vectorización TF-IDF con n-gramas (1, 2) acoplada a Regresión Logística multiclase ($C=4.0$).
   * **Rendimiento:** Exactitud en validación cruzada (5 folds) del **80,8 %** (frente a la línea base de clase mayoritaria del **20,5 %**).
   * **Fallback híbrido de alta disponibilidad:** Si el LLM externo no está disponible o agota su cuota, el sistema degrada sin interrupciones a una arquitectura híbrida de palabras clave deterministas respaldadas por este modelo local de D5. La aplicación es 100 % operativa sin conexión a internet.

---

## 4. Resolución de Horarios Críticos: El Caso del Estudiante Trabajador (Perfil B)

El mayor desafío técnico de la misión radica en responder: **¿cómo se atiende a un estudiante si sus únicas horas libres ocurren cuando el personal administrativo ya cerró?** (caso del Perfil B: trabaja de 09:00 a 17:00 y tiene clases de 18:00 a 22:00).

Aethera resuelve esta paradoja mediante tres mecanismos operativos reales:

1. **Aprovechamiento de la Red de Pares (`peer_support`, D6):**  
   A diferencia del equipo clínico que atiende solo de lunes a viernes de 09:00 a 18:00, los **Acompañantes de Pares** (estudiantes universitarios formados y becados) tienen horario extendido: **lunes a sábado de 12:00 a 20:00 horas**. El solver identifica que el sábado es el día libre del estudiante y le ofrece turnos vespertinos con pares, evitando la saturación del equipo clínico.
2. **El «Intersticio Dorado» (17:00 a 18:00):**  
   Para servicios profesionales de Orientación o Trayectoria laboral, el solver detecta la única ventana viable de la semana: la hora exacta entre la salida del empleo (17:00) y el inicio de las clases nocturnas (18:00), ya sea en modalidad virtual o en la sede correspondiente.
3. **Generación de Nuevos Espacios con Inteligencia Institucional (Pestaña Bienestar):**  
   La vista institucional agrega las 144 conversaciones de D5 y demuestra a las autoridades universitarias con datos duros que el **50 % de la demanda ocurre de noche**. Con este respaldo, el modelo entrega recomendaciones de gestión concretas: rotar turnos remotos de 20:00 a 22:00 y ampliar las plazas de pares los fines de semana.

---

## 5. Decisiones de Producto frente al Estigma Social

El estigma se aborda mediante **mecanismos funcionales concretos**, no con declaraciones vacías:

### A. Sugerencia Proactiva Respetuosa (Ruta escribe primero)
Esperar a que el estudiante dé el primer paso excluye a quien siente que su problema «no es tan grave». Ruta puede iniciar la interacción ante dos disparadores:
* **Evento institucional:** Si se aproxima la semana de bienestar del calendario D7.
* **Patrón de sobrecarga acumulada:** Si en Pulse se registran 3 o más días difíciles en una ventana de 7 días.

**Límites éticos programados:**  
* No se activa sin consentimiento previo.
* No insiste: actúa un máximo de una vez por sesión.
* Se presenta como una tarjeta discreta en Pulse; nunca reemplaza la iniciativa del estudiante si este ya pulsó «Hablar con Ruta».

### B. Privacidad Mecánica en el Calendario («Cita campus»)
Ver en el calendario una entrada llamada «Cita de orientación psicológica» genera temor a que compañeros o familiares lo vean al compartir pantalla.  
Ruta permite seleccionar el estilo del evento: por defecto se registra como **«Cita campus»**, manteniendo la sede, fecha y enlace virtual, pero ocultando el motivo. La privacidad es una función de ingeniería, no una promesa.

---

## 6. Resultados y Proyección sobre el Indicador de la Misión

### Comparativa: Directorio Tradicional vs. Aethera Ruta
*(Evaluación offline sobre 300 estudiantes reales del segmento prioritario M5)*

| Métrica evaluada | Directorio estático | Aethera Ruta | Beneficio para el estudiante |
|---|:---:|:---:|---|
| Turnos mostrados por consulta | ~370 opciones | **3 opciones viables** | Reduce la sobrecarga cognitiva |
| Fracción de turnos compatibles con agenda | 28,2 % | **100,0 %** | Filtro matemático por construcción |
| Mediana de turnos viables para un trabajador | 0 turnos | **3 turnos** | Garantiza acceso al caso más vulnerable |
| Match Rate (encontrar al menos 1 turno útil) | 88,5 % | **100,0 %** | Ningún estudiante queda desatendido |

### Proyección Honesta sobre el Indicador M5 (Baja Búsqueda)
Siguiendo las pautas del desafío, calculamos el impacto esperado con **supuestos conservadores y transparentes**:

$$\text{Indicador Final} = \frac{\text{Línea Base} - (\text{Población Prioritaria} \times \text{Alcance} \times \text{Conversión})}{\text{Total Ansiedad Moderada/Alta}}$$

$$\text{Indicador Final} = \frac{1\,868 - (826 \times 0,30 \times 0,35)}{2\,739} = \frac{1\,868 - 87}{2\,739} = \mathbf{65,0\,\%}$$

* **Reducción proyectada:** de **68,2 % a 65,0 %** (−3,2 puntos porcentuales), lo que representa a **87 estudiantes que completan una reserva** y a más de **248 estudiantes que rompen la barrera del estigma** explorando servicios en su primer período de uso.
* **Análisis de sensibilidad:** Con rangos de alcance del 10 % al 50 % y conversiones del 20 % al 50 %, la reducción se sitúa sólidamente entre **−0,6 pp y −7,5 pp**.

---

## 7. Plan de Adopción Institucional, Viabilidad y Costos

### 7.1 Modelo Económico: ¿Es gratis o viable?
* **Fase Piloto (0 USD):** Diseñado para operar íntegramente dentro de los niveles gratuitos de LLMs (hasta 1 millón de tokens/día) y servidores locales. Un piloto de 800 estudiantes consume ~13 M tokens/mes, requiriendo **cero inversión en licencias y cero tarjetas de crédito**.
* **Escala de Campus Completo (6 000 a 10 000 estudiantes):** El consumo estimado de tokens ronda entre **15 y 40 USD al mes**. Si la institución prefiere soberanía total, la arquitectura permite conectar modelos abiertos locales (Llama 3.3, Gemma 2) a costo marginal computacional de **0 USD**.
* **Retorno de Inversión (ROI):** La retención de un solo estudiante en riesgo de deserción amortiza con creces el costo computacional anual del sistema.

### 7.2 El Plan de Adopción en 3 Fases

```
FASE 1: Integración Plug & Play (Día 1)
├── Incrustación vía iframe o LTI en LMS institucional (Canvas, Moodle, Blackboard)
└── Carga de especificación estándar: sedes (GeoJSON) y calendario académico (CSV)

FASE 2: Piloto Controlado sin Riesgo (Semanas 1 a 4)
├── Despliegue en 1 o 2 facultades piloto (foco en turnos nocturnos o semanas de exámenes)
├── Verificación de métricas en la pestaña Bienestar con k-anonimato (celdas < 10 suprimidas)
└── Costo económico: 0 USD

FASE 3: Escalamiento Institucional Sostenible (Mes 2 en adelante)
├── Conexión al sistema central de reservas de la universidad
└── Activación del programa de acompañantes de pares en horarios extendidos y sábados
```

---

## 8. Reproducibilidad y Verificación Técnica

Cualquier evaluador o miembro del jurado puede verificar la integridad del sistema ejecutando las suites automatizadas incluidas en el repositorio:

```bash
# 1. Verificar segmentación y embudo de la misión M5:
python -m aethera.segmentos

# 2. Entrenar y evaluar modelos de ML locales (D2 y D5):
python -m aethera.ml

# 3. Correr experimentos offline y análisis de sensibilidad:
python -m aethera.evaluacion

# 4. Ejecutar la suite integral de verificación (82 comprobaciones de extremo a extremo):
python tests/verificar_e2.py

# 5. Comprobar contratos y respuestas de la interfaz gráfica:
python tests/verificar_handlers.py
```

*Todos los datos utilizados son 100 % sintéticos, pertenecientes al Data Pack oficial de Ciudad Aethera, garantizando estricta confidencialidad y apego a las bases del concurso.*
