# Especificación del video demostrativo · Entregable 2

Este documento define el contenido, la estructura y los objetivos evaluativos del video
demostrativo del Entregable 2. El material resultante constituye respaldo documental de la
entrega y sirve como guía de producción.

- **Duración objetivo:** 4 minutos
- **Rango admitido por el enunciado:** 3 a 5 minutos
- **Modalidad:** grabación de pantalla con narración
- **Requisitos técnicos verificados:** aplicación en ejecución, proveedor de IA configurado,
  tema claro activo

---

## 1. Objetivos evaluativos

El video debe permitir al jurado verificar cinco afirmaciones. Cada una se corresponde con
un bloque de la estructura.

| # | Afirmación que debe verificarse | Bloque |
|---|---|---|
| 1 | El problema está delimitado con evidencia cuantitativa del Data Pack | 1 y 2 |
| 2 | La población objetivo está identificada y es alcanzable | 2 |
| 3 | El prototipo opera sobre datos reales del Data Pack | 3 |
| 4 | La solución restringe el conjunto de candidatos según restricciones verificadas | 3 |
| 5 | El sistema opera dentro de límites declarados y escala a otra institución | 5 |

## 2. Estructura

| Bloque | Duración | Contenido | Evidencia en pantalla |
|---|---|---|---|
| 1 · Diagnóstico | 0:00 – 0:40 | Indicador de la misión y su causa más probable | 68,2 % · 62 % fuera de horario · 50 % nocturno |
| 2 · Población | 0:40 – 1:05 | Segmento prioritario y caso representativo | 826 estudiantes · agenda del perfil |
| 3 · Funcionamiento | 1:05 – 2:35 | Ejecución del prototipo de punta a punta | Consentimiento, registro de ánimo, propuesta, reserva, cita con título neutro |
| 4 · Resultados | 2:35 – 3:10 | Evaluación offline y proyección sobre el indicador | 370 turnos · mediana 0 viables · 68,2 % → 65,0 % |
| 5 · Alcance y límites | 3:10 – 3:45 | Supervisión humana y límites del modelo | Protocolo de crisis · AUC declarada |
| 6 · Cierre | 3:45 – 4:00 | Encuadre del alcance del producto | — |

## 3. Desarrollo de cada bloque

### Bloque 1 · Diagnóstico (0:00 – 0:40)

**Contenido.** Presentación del indicador de la misión M5: 68,2 % de los estudiantes con
sintomatología ansiosa moderada-alta no ha consultado un servicio de apoyo, equivalente a
1 868 personas en UNI_NOVA_AETHER. Se introduce el hallazgo de la segunda oleada de datos
(D4 y D5): el 62 % de las conversaciones de la línea de orientación se inician fuera del
horario de atención y el 50 % entre las 18:00 y las 06:00.

**Justificación narrativa.** Este bloque establece que el problema no es la desconocencia de
la existencia de los servicios, sino la incompatibilidad entre la disponibilidad del
estudiante y la del servicio. Esa distinción sustenta la totalidad del diseño.

**Verificación.** Las cifras provienen de `aethera.evaluacion` y son reproducibles.

### Bloque 2 · Población (0:40 – 1:05)

**Contenido.** Descripción del segmento prioritario: 826 estudiantes que presentan dos o
más fricciones simultáneas. Se presenta un caso representativo tomado del dataset, con su
régimen de estudios, su jornada laboral y sus ventanas libres.

**Verificación en pantalla.** La ficha del perfil muestra la bloquear ocupada —clases y
trabajo— y las ventanas libres restantes, lo que hace visible la restricción que la
solución debe resolver.

### Bloque 3 · Funcionamiento (1:05 – 2:35)

**Contenido.** Ejecución del prototipo en tres pasos consecutivos.

| Paso | Acción | Evidencia |
|---|---|---|
| 3.1 | Activación del consentimiento y registro del estado de ánimo | La interfaz rechaza el registro sin consentimiento previo |
| 3.2 | Ruta escribe primero: registra los días difíciles de la semana y ofrece un espacio sin que se le pregunte | El turno aparece en el chat con la marca de que la iniciativa es de Ruta |
| 3.3 | Selección y confirmación de una cita | Código de reserva y recordatorios programados |
| 3.4 | Apertura de «Privacidad de la cita» y elección del estilo neutro | La tabla de reservas muestra «Cita campus» en la columna del calendario |

**Fecha de demostración para el paso 3.2.** El disparador de evento institucional se
activa con la fecha **«Antes de finales · jue 26 nov 2026»**, que deja la semana de pausa y
bienestar a cuatro días. Con la fecha regular del 20 de octubre el disparador que se
demuestra es el del patrón de días pesados, que también funciona.

**Verificación en pantalla.** El panel «Cómo decidió Ruta» permanece visible durante todo el
bloque, mostrando la acción decidida, el motivo clasificado, las herramientas invocadas y
la procedencia de cada dato.

**Observación relevante para el jurado.** Dos hechos se comprueban a simple vista:

1. Las tres citas propuestas se ubican invariablemente en la franja libre del estudiante.
   Esta restricción es verificable a ojo y constituye la contribución técnica central.
2. La reserva aparece como **«Cita campus»** en la columna del calendario, sin nombrar el
   servicio. El sistema conserva internamente el servicio real, pero la entrada que ve un
   tercero no lo delata. Este es el punto del video donde el jurado comprueba que la
   privacidad es una mecánica y no una declaración.

### Bloque 4 · Resultados (2:35 – 3:10)

**Contenido.** Resultados de la evaluación offline sobre 300 estudiantes reales del segmento
prioritario: un directorio estático ofrece 370 turnos por estudiante, de los cuales el 28,2 %
resulta compatible con su horario, con una mediana de cero turnos viables. Se presenta
asimismo la proyección sobre el indicador de la misión bajo supuestos declarados.

**Precisión requerida.** La proyección debe presentarse como *estimación condicionada*, nunca
como resultado observado. Los cinco supuestos deben enunciarse.

### Bloque 5 · Alcance y límites (3:10 – 3:45)

**Contenido.** Dos demostraciones.

1. **Supervisión humana.** Una entrada que activa el protocolo de riesgo; el sistema deja de
   orientar, entrega las líneas de ayuda verificadas y ofrece la derivación a una persona.
2. **Transparencia sobre el modelo.** El modelo de asistencia rinde por debajo del azar en la
   franja de esperas que el prototipo ofrece. El sistema expone esta condición mediante un
   indicador de confianza, y la vista de Bienestar declara la métrica.

**Justificación.** Declarar el límite propio es la evidencia más directa de criterio en IA
responsable, y el enunciado evalúa expresamente este criterio.

### Bloque 6 · Cierre (3:45 – 4:00)

**Contenido.** Encuadre del alcance: el sistema no diagnostica, no prescribe y no sustituye la
atención profesional. Su función consiste en convertir una necesidad expresada en lenguaje
cotidiano en una cita que el estudiante puede realmente cumplir dentro de su agenda real.

## 4. Condiciones previas a la grabación

| Condición | Verificación |
|---|---|
| Proveedor de IA operativo | El panel de trazabilidad indica `decidida por modelo` |
| Data Pack completo | `python app.py --diagnostico` sin observaciones |
| Tema claro activo | La aplicación lo fuerza automáticamente |
| Perfil correcto seleccionado | El perfil B, de horario nocturno y jornada completa |
| Caption del video | *Aethera es una ciudad universitaria ficticia; todos los datos son sintéticos* |

## 5. Adaptaciones por duración

**Si se dispone de menos de 3:30.** El bloque 1 conserva su duración completa, por ser el de
mayor ponderación en la evaluación. Se reduce el bloque 2 a una mención del segmento y una
del perfil, y se omite la replanificación dentro del bloque 3.

**Si se dispone de más de 4:30.** El bloque 3 se amplía con una segunda ronda de
replanificación y con la demostración de portabilidad a otra institución mediante la variable
`AETHERA_INSTITUCION`.

**Nunca deben suprimirse** el bloque 1 (comprensión del problema) ni el apartado 5 del
bloque 5 (límites del modelo), por ser los de mayor valor en la rúbrica de evaluación.

## 6. Verificación posterior a la grabación

| Punto | Comprobación |
|---|---|
| Duración | Dentro del rango de 3 a 5 minutos |
| Audio | Comprensible sin subtítulos |
| Legibilidad | Los números citados en pantalla coinciden con lo narrado |
| Caption | Presente y visible |
| Ausencia de datos reales | Ninguna pantalla muestra datos de personas identificables |

---

*Este documento no sustituye al video: lo especifica. El enlace al material grabado se
consigna en la sección 12 del `README.md`.*
