# Entregable 2 — Aethera Pulse + Ruta

**Desafío Ciudad Aethera · Misión M5: estigma y baja búsqueda de ayuda**
Indicador de línea base: **68 %** de los estudiantes con sintomatología ansiosa
moderada-alta nunca consultó un servicio de apoyo.

---

## 1. El problema, delimitado con datos

El Entregable 1 delimitó *dónde* está la brecha con los datasets de la primera oleada
(D1, D2, D3, D6, D7). Para el Entregable 2 analizamos **D4 y D5**, que llegaron en la
segunda oleada, y ahí apareció la causa concreta de la fricción.

**El embudo de M5** (reproducible con `python -m aethera.segmentos`):

| Etapa | Estudiantes |
|---|---|
| Encuestados en UNI_NOVA_AETHER | 6 697 |
| Ansiedad moderada o alta | 2 739 |
| De esos, **nunca** usaron apoyo (**M5**) | **1 868 = 68,2 %** |
| M5 con **≥ 2 fricciones** (segmento prioritario) | 826 = 44,2 % de M5 |

**Tres hallazgos que decisieron el diseño** (todos medidos, ver
`python -m aethera.evaluacion`):

| # | Hallazgo | Evidencia | Decisión de producto |
|---|---|---|---|
| 1 | **Se pide ayuda a cualquier hora** | 62 % de las conversaciones de D5 empiezan fuera de lun–vie 09:00–18:00; **50 % llegan de noche** | Ruta atiende por chat siempre, y propone citas dentro de horarios reales: pares hasta las 20:00 y también sábados |
| 2 | **La derivación actual no depende del motivo** | solo **34,2 %** de las derivaciones de D5 apuntan al tipo de servicio que D2 asocia a ese motivo (azar = 33,3 %) | El mapa motivo → servicio se toma de **D2**, nunca de D5 |
| 3 | **El directorio muestra turnos que el estudiante no puede usar** | 370 turnos por estudiante en 14 días; solo **28,2 %** compatibles; **mediana 102 viables** y **12,7 % del segmento sin ninguno** | El núcleo del producto: un solver que cruza agenda, servicios y distancia |

El hallazgo 3 es el que define la solución. No es un problema de falta de información:
es que **la información existe, pero está enterrada bajo 370 opciones y ninguna cabe
en la vida del estudiante**.

## 2. La solución

### Pulse — el registro de 20 segundos

Un check-in de ánimo, opcional, con consentimiento expreso. No es un test: no calcula
puntajes, no tiene respuestas correctas y no da niveles. Produce un mes en colores que
convierte una sensación difusa en algo visible ("llevo cuatro semanas con dos días
pesados"), que es exactamente lo que dispara la conversación de ayuda.

### Ruta — el asistente que convierte necesidad en cita cumplible

Es un asistente de IA de orientación **no clínica**. No diagnostica, no receta, no es
terapia y no atiende emergencias. Lo que hace es:

1. **Traducir** lenguaje cotidiano a uno de cinco motivos no clínicos.
2. **Cruzar** ese motivo con el tipo de servicio que D2 asocia, el calendario de D7 y la
   agenda real del estudiante.
3. **Proponer** tres citas concretas que no chocan con sus clases, su trabajo ni el
   tiempo de traslado.
4. **Reservar, reprogramar** y, si no hay nada posible, **escalar a una persona**.

La diferencia con un chatbot común es dónde está el esfuerzo: no en la conversación, sino en
el **solver de restricciones horarias**.

## 3. Cómo utiliza la IA

### Arquitectura: el modelo nunca decide datos

```
mensaje
  ① Guardrail de entrada   patrones: crisis · clínico · privacidad · manipulación
  ② Planificador          el LLM elige acción + preferencias + señal de riesgo
       └─ 2.ª capa: el LLM detecta riesgo que las reglas no ven
  ③ Herramientas          clasificación · calendario · catálogo · agenda · ML
  ④ Redactor              el LLM redacta SOLO con los resultados de ③
  ⑤ Guardrail de salida   valida la respuesta; si falla → plantilla verificada
```

El modelo de lenguaje (`gemini-3.5-flash-lite`) interviene en tres puntos, siempre con
una responsabilidad acotada: **elegir una etiqueta de una lista cerrada** y **formular
texto a partir de datos ya calculados**. Servicios, fechas, horas, canales, esperas y
teléfonos salen de herramientas que leen el Data Pack. Si el redactor intenta inventar
un servicio, una fecha o un teléfono, el guardrail de salida lo detecta y **su respuesta
se descarta** por una plantilla con datos verificados.

### Dos modelos propios, entrenados localmente

| Modelo | Entrena en | Para qué | Resultado |
|---|---|---|---|
| Regresión logística | **D2** (9 400 eventos) | Estimar P(asistir) y ordenar las citas | AUC **0,567** (azar 0,50) |
| TF-IDF + regresión logística | **D5** (2 500 etiquetadas) | Clasificar la necesidad | **80,8 %** CV (base 20,5 %) |

El feature más importante del modelo de asistencia es `espera_dias` (+0,053 AUC): la
asistencia cae de **75,3 %** en el cuartil de menor espera a **63,7 %** en el de mayor
espera. Coincide con el diagnóstico del Entregable 1.

### El respaldo sin IA no es un joke

Cada llamada al modelo tiene doble respaldo. Sin clave de API, la app funciona completa:
el clasificador de D5 sustituye al LLM y las plantillas de respaldo sustituyen al
redactor. **La demostración en vivo no puede caerse por un fallo de red.**

### Y el límite del modelo, declarado en pantalla

El modelo se entrena con esperas de 4 a 120 días (mediana 39). La demo ofrece turnos a
1–14 días, que es el **3,4 %** del histórico. En esa franja el modelo **no discrimina
bien**: AUC 0,44 con solo 77 casos de prueba, es decir, por debajo del azar.

No lo escondimos. Ruta calcula un **indicador de confianza** según cuánto histórico hay
alrededor de esa espera, lo pondera en el ranking y **lo muestra en la vista de Bienestar**.
Es un límite conocido del prototipo, asumido a la vista.

## 4. Resultados frente al indicador de la misión

La pregunta que pide el enunciado: **¿qué le pasa al 68 %?**

| | |
|---|---|
| Denominador | 2 739 estudiantes con ansiedad moderada/alta |
| Línea base | **68,2 %** (1 868) |
| Alcance 30 % del prioritario | 248 estudiantes llegan a usar Ruta |
| Conversión 35 % | 87 completan una reserva |
| **Indicador proyectado** | **65,0 %** |
| **Reducción** | **−3,2 pp** |

**Sensibilidad:** con alcances del 10–50 % y conversiones del 20–50 %, la reducción está
entre **−0,6 y −7,5 pp**. El indicador baja en todo el rango.

**Los cinco supuestos, declarados:**

1. Denominador idéntico al de la línea base (el 68 % es sobre moderada/alta, no sobre M5).
2. Alcance: fracción del prioritario que llega a usar Ruta.
3. Conversión: de quienes usan Ruta, fracción que completa una reserva.
4. Contrafactual **conservador**: se asume que sin Ruta esa demanda no se materializa.
   No está demostrado, y es el supuesto que más nos favorece.
5. No se modela el efecto sobre los 1 042 estudiantes de M5 fuera del prioritario.

**Por qué el efecto es modesto y por qué lo declaramos bajo.** La conversión a reserva no
es el indicador: la misión mide *buscar* ayuda. Un estudiante que registra su día y
descubre que existen servicios ya rompió la barrera, aunque no reserve. Y una sola
institución, con un indicador por institución de 68,2 %, casi idéntico al 68,0 % global,
no deja término de ajuste. Preferimos un número defendible a uno grande.

### Indicadores de la demo

La vista de Bienestar calcula en vivo los siete KPIs del Entregable 1 —Activation Rate,
Pulse → Ruta, Match Rate, Booking Conversion, Replanning Success, Time-to-Booking y
Asistencia esperada— y **los etiqueta como indicadores de uso del prototipo, no del
piloto**. El indicador que falta para el Demo Day es el *Match Rate en campo*: la
fracción de reservas reales a las que el estudiante asiste. Eso exige el piloto.

## 5. Sesgos que encontramos en el Data Pack

El Data Pack incorpora sesgos deliberados. Tres los detectamos antes del Demo Day, y cada
uno es una razón concreta de una decisión de diseño:

| Sesgo | Evidencia | Qué hicimos |
|---|---|---|
| El sentimiento de D4 refleja el **canal**, no la persona | el buzón es 100 % `strained`; el foro no | No usamos sentimiento de D4 como señal |
| El motivo declarado en D4 **casi no se refleja** en su texto | un clasificador rinde lo mismo que la clase mayoritaria | No entrenamos con D4 |
| La derivación de D5 **no depende del motivo** | 34,2 % de coherencia, contra 33,3 % de azar | El mapa motivo → servicio sale de D2 |

## 6. Privacidad y supervisión

- **Consentimiento** expreso, informado y con finalidad (Ley 29733, DS 016-2024-JUS). Opcional
  y no condiciona ningún servicio.
- **`anxiety_band` nunca se usa en tiempo de ejecución.** La segmentación es diagnóstico,
  no un disparador. Ruta recibe solo datos operativos: horario, trabajo, distrito, código.
- **ARCO completo desde la interfaz**: consultar, exportar (JSON) y borrar. Borrar elimina
  también el uso posterior en el chat.
- **Vista de Bienestar agregada** con supresión de toda celda de menos de **10 personas**.
  Los ánimos individuales nunca se agregan ni se comparten.
- **Cola de contacto humano** con el mínimo: código, prioridad y motivo no clínico.
  Nunca el texto del estudiante.
- **Panel de trazabilidad**: cada turno deja registro de la acción, el motivo, las
  herramientas, la procedencia de cada dato y los guardrails activados.

Detalle completo en `FICHA_IA_RESPONSABLE.md`.

## 7. Adopción y viabilidad

### 7.1 Los cuatro filtros del proceso de integración

Un asistente de bienestar universitario no se despliega con una demostración: se
integra. Identificamos cuatro filtros, y es más honesto decir cuáles pasamos y cuáles
no que afirmar que el sistema «se puede instalar»:

| Filtro | Qué exige | Estado |
| --- | --- | --- |
| **1 · Sistema de registro** | Estar dentro del SIS o del sistema de matrícula para no crear una agenda paralela | ⚠️ No resuelto: se propone leer, no escribir |
| **2 · Identidad institucional** | Un inicio de sesión que acredite que quien entra es estudiante | ⚠️ Parcial: se resuelve con código + correo institucional |
| **3 · Directorio de servicios** | Un origen de verdad con nombre, horario, capacidad y ubicación de cada servicio | ✅ Resuelto: es D2 del Data Pack |
| **4 · Consentimiento institucional** | Un marco de protección de datos que permita tratar datos de salud mental | ⚠️ Depende de la universidad |

### 7.2 Por qué no almacenamos datos del SIS

El sistema **lee** el perfil operativo del estudiante —código, carrera, jornada, horas de
trabajo, distrito— y **no copia** ese registro a ningún lado. Dos razones:

1. **Legal.** Copiar datos académicos a un sistema nuevo es un tratamiento de datos
   personales nuevo, que exige una base legal y un registro de tratamiento propios. Leer
   desde la fuente autorizada evita duplicar ese riesgo.
2. **Deuda operativa.** Toda copia es una fuente que después hay que sincronizar,
   proteger y responder por ella. Una integración de solo lectura no genera esa carga.

La consecuencia operativa es que **Ruta no puede confirmar una cita en el sistema de la
universidad**: la reserva vive en Aethera y la universidad recibe una notificación por
correo. Es una limitación real, y la declaramos en lugar de disimularla: es la primera
integración que hace falta para pasar de piloto a producción.

### 7.3 Modelo de adopción

1. **Piloto con un grupo pequeño** (una facultad, un semestre) → medir uso real.
2. **Evaluación** con instrumentos ya validados, no con los nuestros.
3. **Licencia libre** del núcleo: el costo marginal del piloto es 0 USD y así se mantiene.
4. **Integración de escritura** en el SIS, que es el filtro 1.

### 7.4 Qué haría que esto no se use

Lo enumeramos porque es la pregunta que más importa en una mesa de jurado: el
abandono no lo causa la falta de funcionalidad, sino la **pérdida de confianza**. Si un
estudiante percibe que su registro se comparte, deja de registrar y el sistema pierde su
única fuente de señal. Por eso la privacidad no es un requisito legal que cumplir al
final, sino la condición de existencia del producto.

---

## 7 bis. Las dos decisiones de producto queisit defienden el estigma

El módulo `disparadores.py` y el estilo de evento en `agente.py` son, juntos, la
respuesta operativa a la misión M5. El diagnóstico del Entregable 1 atribuyó la baja
búsqueda de ayuda a dos causas: el estigma y la certeza de que el caso «no es tan grave».

### 7 bis.1 · Ruta escribe primero

Hasta la versión anterior, el estudiante tenía que hablar para recibir ayuda. Eso excluye
precisamente a quien la misión busca: quien no pide ayuda porque no cree que pueda. Ruta
ahora puede iniciar la conversación por dos motivos, y ninguno requiere que el estudiante
hable de su salud mental:

- **Evento institucional.** Si la semana de pausa y bienestar está a menos de siete días,
  Ruta avisa: *«La semana de pausa y bienestar empieza dentro de 4 días. Es cuando la
  universidad tiene más espacio para acompañar a quien lo necesite, así que te busco un
  apoyo con esa fecha en mente.»*
- **Patrón propio.** Si el propio estudiante registró tres o más días difíciles en una
  semana, Ruta lo señala sin diagnostics: *«No hace falta que sepas explicarme qué te
  pasa: puedo buscarte un espacio.»*

Tres límites que el código impone y las pruebas verifican:

- **Sin consentimiento de Pulse, no hay iniciativa.** Un sistema proactivo que no tiene
  permiso previo se convierte en vigilancia.
- **No insiste.** Cada disparador actúa una vez por sesión.
- **El evento es común a todos.** Se lee del calendario institucional, que no se
  segmenta por perfil: un aviso distinto según el estado de ánimo de cada quien sería
  precisamente la señal que este producto no debe producir.

### 7 bis.2 · La cita no dice de qué se trata

Un evento de calendario titulado «Espacio Lumen Orientación» revela el motivo de la cita a
quien llegue a ver la pantalla. Ninguna frase de normalización evita eso, porque no es
un problema de percepción: es un hecho.

El estudiante elige, en la misma pantalla donde registra su día, cómo aparece su cita:

| Estilo | Título en el calendario | Qué sigue visible |
| --- | --- | --- |
| **Neutro** *(por defecto)* | `Cita campus` | Sede, canal, fecha y hora |
| **Equilibrado** | `Espacio Lumen Orientación` | La sede |
| **Completo** | `Espacio Lumen Orientación · Orientación` | La sede |

El nombre del servicio es lo único que delata a qué se asistió, y la sede es
información que comparte todo el campus. El estudiante conserva dentro de la aplicación
el detalle completo: ocultar el título no impide ni llegar a tiempo ni saber a qué hora
ir. El sistema conserva internamente el servicio real, porque el equipo de bienestar lo
necesita para atender la cita.

Es una mecánica de privacidad ligada al estigma, no una promesa. Y tiene una
consecuencia operativa favorable: como la cita no nombra el servicio, dos estudiantes
que reservan el mismo turno no se delatan entre sí por el título de su evento.

---

## 8. Escalabilidad y costo

**Cambiar de institución es una variable de entorno:** `set AETHERA_INSTITUCION=INST_NEXUS`.
El Data Pack ya trae tres instituciones y cinco distritos, y las líneas de ayuda son
bilingües (Perú 113 / Chile \*4141). No hay código específico de NOVA fuera de esa
constante. Cualquier universidad de América Latina con un directorio de servicios y un
calendario despliega esto sin tocar el núcleo.

**Costo marginal del piloto: 0 USD.** El piloto completo (826 estudiantes) consume
~13 M tokens/mes, dentro del nivel gratuito del proveedor y de un Space gratuito.
Detalle en `docs/COSTOS.md`.

## 8. Cómo reproducir los números

```bash
python -m aethera.segmentos      # embudo M5
python -m aethera.ml             # modelos, AUC, límite del rango
python -m aethera.evaluacion     # los tres experimentos + sensibilidad
python tests/verificar_e2.py     # 82 comprobaciones de extremo a extremo
```

La agenda usa una semilla fija: la demo produce **exactamente los mismos números** en cada
ejecución, así que cualquier revisor ve lo mismo que ve el jurado.

---

*Aethera es una ciudad universitaria ficticia del desafío binacional Chile–Perú. No hay
personas, lugares ni servicios reales. Ruta es orientación no clínica: apoya, no reemplaza
la atención profesional.*
