# Ficha de IA Responsable — Aethera Pulse + Ruta

**Entregable 2 · Desafío Ciudad Aethera · Misión M5 (estigma y baja búsqueda de ayuda)**
Versión 2.0 · Una página · Datos 100 % sintéticos del Data Pack de la organización

---

## 1. Modelos y herramientas de IA

| Uso | Modelo | Proveedor | Propósito |
|---|---|---|---|
| Clasificador de necesidad | Modelo de lenguaje + respaldo TF-IDF/LogReg | Google Gemini (`gemini-3.5-flash-lite`) | Elegir 1 de 5 motivos **no clínicos**. Nunca diagnostica. |
| Planificador de turno | Modelo de lenguaje + respaldo de reglas | Google Gemini (mismo) | Elegir 1 de 7 acciones y extraer preferencias. No aporta datos. |
| Redactor | Modelo de lenguaje + plantillas fijas | Google Gemini (mismo) | Formular la respuesta **solo** a partir de datos ya calculados. |
| Estimación de asistencia | Regresión logística (scikit-learn) | Entrenado localmente sobre D2 | Ordenar citas por probabilidad de asistencia. |
| Clasificador de necesidad (offline) | TF-IDF + regresión logística | Entrenado localmente sobre D5 | Sustituye al clasificador cuando no hay clave. |

**Transporte de modelos.** Se exponen cuatro proveedores (`gemini`, `openai`, `huggingface`,
`compatible`) y `offline`. La demo y la publicación usan **nivel gratuito**; el costo
marginal estimado es 0 USD dentro de los límites del piloto (ver `docs/COSTOS.md`).

**Principio rector.** El modelo de lenguaje **nunca decide datos**. Solo decide *qué hacer*
y *cómo decirlo*. Servicios, fechas, horas, canales, esperas y teléfonos salen de
herramientas que leen el Data Pack. Si el redactor intenta inventar un servicio, una fecha o
un teléfono, el guardrail de salida lo detecta y su respuesta se descarta por una plantilla
con datos verificados.

## 2. Datos utilizados

Solo los siete datasets sintéticos del Data Pack: **D1** (bienestar, 12 000), **D2** (uso de
servicios, 9 400), **D3** (trayectoria, 130 000), **D4** (testimonios, 6 000), **D5** (conversaciones,
2 500), **D6** (mapa de servicios, 15) y **D7** (calendario, 32).

**No se usan datos reales ni externos sensibles.** No hay identificadores de personas, no
hay freer de contacto, no hay directorios de terceros. Los tres estudiantes de la demo son
filas reales de D1 dentro del segmento M5, con identificadores sintéticos.

**Qué sale del entorno del usuario.** El texto que el estudiante escribe en el chat y, si lo
autoriza, su registro de ánimo. Se envía al proveedor del modelo: eso es una **transferencia
internacional**, y por tanto exige evaluar el marco de protección del país de destino
(Ley 29733, DS 016-2024-JUS). Compromisos asumidos: contrato de encargado de tratamiento,
**sin uso para entrenar**, mínimo de texto posible, sin identificadores y sin datos clínicos.
Esta declaración es una condición previa a cualquier despliegue real, no una descripción de
lo que ya está hecho.

## 3. Alcance y límites

**Lo que hace:** convierte lenguaje cotidiano en un motivo no clínico; consulta los servicios
y el calendario; propone citas compatibles con el horario real del estudiante; reserva,
reprograma y ofrece derivación a una persona.

**Lo que NO hace, por diseño:**
- **No diagnostica.** No evalúa gravedad clínica ni escala de riesgo.
- **No receta ni recomienda medicamentos, dosis ni tratamientos.**
- **No es terapia.** No mantiene seguimiento clínico ni actúa como profesional.
- **No atiende emergencias.** Detecta señales de riesgo y entrega líneas de ayuda reales.
- **No da consejo académico ni resuelve tareas.** Responde con amabilidad qué sí puede hacer.
- **No entrega datos personales** de otros estudiantes ni de profesionales.
- **No usa el nivel de ansiedad de nadie en tiempo de ejecución.** La segmentación por
  `anxiety_band` es un paso de diagnóstico, no un disparador del producto. Ruta recibe solo
  datos operativos: horario de estudio, trabajo, distrito, código de estudiante.

**La solución apoya, no reemplaza, la atención profesional.**

## 4. Riesgos identificados y mitigaciones

| Riesgo | Mitigación implementada |
|---|---|
| **Etiquetaje clínico** — el modelo podría decir "tienes ansiedad" | Guardrail de salida con 9 patrones; se acepta solo con negación previa ("no tienes…"). Si falla, cae a plantilla. |
| **Falsificación de datos** — inventar servicio, fecha o teléfono | El LLM no accede a datos; todo pasa por herramientas. El guardrail valida contra el catálogo real. |
| **Riesgo de autolesión no detectado** — quien dice "quiero desaparecer" sin usar las palabras del patrón | **Segunda capa:** el planificador (LLM) marca `senal_de_riesgo` y se activa el protocolo de crisis con líneas reales (Perú 113 / Chile \*4141 / SAMU). |
| **Manipulación / inyección de prompt** | Patrones dedicados que bloquean y reafirman el rol no clínico. |
| **Fuga de datos de otros estudiantes** | Patrón dedicado; la cola de contacto lleva solo código y motivo no clínico. |
| **Falso consuelo** — el sistema refuerza una decisión equivocada | Tono validativo sin diagnóstico; nunca cierra con "ya estás bien"; ofrece derivación humana de forma explícita. |
| **Sesgo del Data Pack** | Ver sección 5: tres sesgos detectados y documentados. |
| **Modelo fuera de su rango** | El modelo de asistencia muestra un **indicador de confianza** cuando predice fuera de la zona con evidencia histórica, y esa nota se ve en pantalla. |

## 5. Sesgos del Data Pack que encontramos

El Data Pack incorpora sesgos deliberados. Tres los detectamos antes del Demo Day y son
razones concretas de decisiones de diseño:

1. **El sentimiento de D4 refleja el canal, no a la persona.** El buzón está 100 % `strained`
   y el foro no. **Decisión:** no usamos sentimiento de D4 como señal; D4 solo alimenta frases
   de normalización agregadas.
2. **El motivo declarado en D4 casi no se refleja en su texto.** Un clasificador de texto
   rinde lo mismo que la clase mayoritaria. **Decisión:** no entrenamos con D4.
3. **La derivación de D5 no depende del motivo.** Solo 34 % de las derivaciones apuntan al
   tipo de servicio que D2 asocia a ese motivo, frente a 33 % de azar. **Decisión:** el mapa
   motivo → servicio se toma de D2, nunca de D5.

## 6. Supervisión humana

- **Derivación explícita.** Botón permanente "Quiero que una persona me contacte". Ruta lo
  ofrece sola ante señal de crisis.
- **Cola de contacto humano.** La vista de Bienestar muestra los pedidos pendientes con
  prioridad, código de estudiante y motivo **no clínico**; nunca el texto ni el estado de ánimo.
- **Prioridad automática.** Un pedido marcado en crisis entra con prioridad **alta** y la
  respuesta incluye la línea de ayuda mientras se espera la atención humana.
- **Escalamiento por falta de opciones.** Si no hay turnos compatibles, se registra
  seguimiento y se ofrece pares como primer contacto, en vez de responder "no hay nada".
- **Auditoría.** El panel "Cómo decidió Ruta" deja registro de cada turno: acción, motivo,
  herramientas, procedencia de cada dato y guardrails activados. Es auditable por diseño.

## 7. Privacidad

- **Consentimiento.** Pulse no guarda nada sin consentimiento expreso, informed y con finalidad
  declarada. Es opcional y no condiciona ningún servicio.
- **Minimización.** El horario se usa solo para calcular franjas libres. No se usan puntajes,
  notas ni asistencia para decidir nada. El registro de ánimo **nunca** se comparte con
  Bienestar, ni en agregado.
- **Identidad separada del contenido.** El código de estudiante se separa del contenido del
  registro; el registro se cifra y es visible solo para su dueño.
- **Derechos ARCO.** Consultar, corregir, **exportar** (JSON) y **borrar** desde la interfaz,
  sin pasar por un ticket. Borrar elimina también el uso posterior en el chat.
- **Agregación con umbral.** La vista de Bienestar suprime toda celda con menos de
  **10 personas** (`K_MINIMO`). No hay medias individuals ni distribuciones pequeñas.
- **Sin uso secundario.** Los datos no se usan para becas, evaluación, disciplina ni publicidad,
  y no se comparten con terceros.
- **Sin acceso individual.** Docentes, autoridades y áreas académicas o disciplinarias no
  acceden al registro individual.

## 8. Transparencia hacia el usuario

- Ruta se presenta como **IA de orientación no clínica** en el primer turno y lo repite en la
  interfaz y en cada respuesta de crisis.
- El estudiante **elige y rechaza** cada ruta propuesta; puede replanificar cuantas veces quiera.
- El panel de trazabilidad explica, en lenguaje llano, por qué se propuso cada cita.
- Pulse dice siempre quién ve el registro y para qué se usaría.
- El modelo de asistencia declara sus límites en la vista de Bienestar, incluido el hecho de
  que **no discrimina bien en el rango de esperas que la demo ofrece**.
- Aethera es una ciudad ficticia y todos los datos son sintéticos; se declara en pantalla.

## 9. Contexto normativo

Diseñado dentro del marco Peruvian: **Ley 29733** y su reglamento (**DS 016-2024-JUS**, en
vigor desde el 30 de marzo de 2025), que califica los datos de salud como sensibles y exige
consentimiento previo, informado, expreso e inequívoco con finalidad específica; y la **Ley
31814** (**DS 115-2025-PCM**) sobre IA. La clasificación específica de Aethera se confirmará
con asesoría legal antes de cualquier despliegue real, junto con una evaluación de impacto en
protección de datos con un Oficial de Datos Personales.

**Referencias de ecosistema.** El precedente más cercano, Woebot, cerró su aplicación de
consumo en junio de 2025 por el costo de cumplir la autorización de la FDA y por falta de un
marco claro para modelos de lenguaje. Aethera evita deliberadamente ese camino: no ofrece
intervención clínica, mantiene la frontera con la atención profesional y es explícito con el
usuario sobre sus límites.

---

*Aethera es una ciudad universitaria ficticia del desafío binacional Chile–Perú. No hay
personas, lugares ni servicios reales.*
