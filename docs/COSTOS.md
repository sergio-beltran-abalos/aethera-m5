# Viabilidad y sostenibilidad

Este documento describe los recursos que el prototipo requiere para operar en el piloto
universitario del Entregable 2.

## 1. Costo marginal: 0 USD dentro del piloto

| Recurso | Plan | Límite | ¿Suficiente? |
|---|---|---|---|
| Modelo de lenguaje | Gemini, nivel gratuito | 15 req/min · 1 M tokens/día | Sí. Un turno ≈ 3 llamadas ≈ 2 500 tokens |
| Alojamiento | Equipo del usuario + túnel de Cloudflare | gratuita | Sí. La aplicación es liviana |
| Modelo de asistencia | scikit-learn, local | sin costo | Sí |
| Clasificador de necesidad | scikit-learn, local (D5) | sin costo | Sí |
| Datos | Data Pack sintético | sin costo | — |

No se requiere tarjeta de crédito en ninguna etapa. Véase `PUBLICACION.md`.

**Estimación para el piloto universitario.** Si atienden 826 estudiantes (el segmento
prioritario de UNI_NOVA_AETHER) y cada uno registra 4 días en Pulse y abre 2 conversaciones:

| Concepto | Cálculo | Total |
|---|---|---|
| Turnos de conversación | 1 652 chats × 3 llamadas × 2 500 tokens | ~12,4 M tokens |
| Frases de Pulse | 3 304 registros × ~200 tokens | ~0,7 M tokens |
| **Total** | | **~13 M tokens/mes** |

Con el límite gratuito de 1 M/día (≈30 M/mes), **el piloto completo se sitúa dentro del plan
gratuito**. Si el alcance se duplicara, bastaría el nivel de pago más bajo del proveedor; el
costo seguiría siendo marginal frente al de un profesional de bienestar.

## 2. Costo por etapa de despliegue y Plan de Adopción

| Etapa | Volumen | Costo estimado | Observación |
|---|---|---|---|
| Demostración de semifinal | ~50 usuarios | 0 USD | Totalmente funcional |
| Piloto universitario | 826 estudiantes | 0 USD | Dentro de la capa gratuita, sin tarjeta |
| Institución completa | ~6 700 estudiantes | 15–40 USD/mes | Costo marginal despreciable |
| Red regional | >100 000 | 0 USD en cómputo propio | Modelos abiertos (Llama/Gemma) on-premise |

### Plan de adopción institucional en 3 fases

1. **Fase 1 · Conexión Plug & Play (Día 1 · Costo 0 USD):** La universidad no reconstruye su infraestructura. Se integra directamente en el aula virtual o LMS (Canvas, Blackboard o Moodle) mediante iframe o estándar LTI. Solo consume dos fuentes estandarizadas: el catálogo de servicios (D6) y el calendario académico (D7).
2. **Fase 2 · Piloto Focalizado sin Riesgo (Semanas 1 a 4 · Costo 0 USD):** Se habilita en una facultad piloto o durante semanas críticas de exámenes. El equipo de bienestar evalúa el uso real mediante el dashboard con k-anonimato (celdas < 10 suprimidas). No se requiere tarjeta de crédito ni presupuesto previo.
3. **Fase 3 · Escalamiento Sostenible (Mes 2 en adelante):** Expansión a todo el campus. A nivel institucional completo (~6 700 alumnos), el costo computacional de tokens es de apenas 15 a 40 USD mensuales.

### Retorno de inversión (ROI) y sostenibilidad operativa
El sistema es financieramente viable porque no intenta sustituir la atención humana contratando nóminas clínicas masivas. Al clasificar la necesidad y canalizar el malestar cotidiano hacia el **Acompañamiento entre Pares** (`peer_support`), la capacidad de atención se amplía con estudiantes de ciclos superiores becados y formados. La retención de un solo estudiante en riesgo de deserción cubre con creces el costo computacional de toda la universidad.

## 3. Viabilidad técnica

**Arranque.** La aplicación carga el Data Pack y entrena dos modelos en aproximadamente
25 segundos. No requiere base de datos: el estado reside en memoria durante la sesión.

**Reproducibilidad.** La agenda se genera con una semilla fija (`random.Random`), por lo que
la demostración produce exactamente los mismos números en cada ejecución. Esta propiedad es
deliberada: garantiza que el equipo de evaluación observe lo mismo que observó el equipo autor,
y resulta indispensable para la grabación del video.

**Degradación controlada.** Cada invocación al modelo dispone de respaldo. En ausencia de
clave, la aplicación opera íntegramente con el clasificador de D5 y plantillas de respaldo.
**La aplicación no puede colapsar ante un fallo de red**, condición esencial para una
demostración en vivo.

**Portabilidad.** Cambiar de institución es una variable de entorno:

```bash
set AETHERA_INSTITUCION=INST_NEXUS
```

El Data Pack incluye tres instituciones y cinco distritos, y las líneas de ayuda son
bilingües (Perú, Chile). No existe código específico de UNI_NOVA_AETHER fuera de esa
constante.

## 4. Ruta de crecimiento

1. **Agenda real.** Actualmente la agenda es simulada. Se sustituye `generar_agenda()` por una
   consulta al sistema de citas institucional; el resto del motor no se modifica.
2. **Identidad.** El `student_id` procede hoy del selector de demostración. Se sustituye por
   el inicio de sesión institucional, conservando que el sistema nunca recibe `anxiety_band`.
3. **Persistencia.** El registro de Pulse pasa de memoria a almacenamiento cifrado con control
   de acceso por roles y bitácora, conforme a lo declarado en la ficha de IA responsable.
4. **Modelo de lenguaje.** Ya es intercambiable entre cuatro proveedores y el modo sin
   modelo.

## 5. Riesgos de viabilidad

| Riesgo | Mitigación |
|---|---|
| Agotamiento de la cuota gratuita durante un evento | Respaldo sin modelo: la aplicación sigue operativa |
| La agenda real difiere de la simulada | El motor consume un `DataFrame` de esquema fijo, documentado en `servicios.generar_agenda` |
| Mantenimiento de un único archivo extenso | Arquitectura reorganizada en 16 módulos con verificaciones automatizadas |
| El modelo no generaliza fuera de UNI_NOVA_AETHER | Declarado; el clasificador se reentrena con las conversaciones de D5 de las demás instituciones |
| El Data Pack no puede distribuirse con el código | Plantilla `data/LEEME.txt` y un mensaje de arranque que identifica el archivo ausente |
