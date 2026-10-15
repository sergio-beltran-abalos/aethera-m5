# Viabilidad y sostenibilidad

Este documento describe los recursos que el prototipo requiere para operar en el piloto
universitario del Entregable 2.

## 1. Costo marginal: 0 USD dentro del piloto

| Recurso | Plan | Límite | ¿Suficiente? |
|---|---|---|---|
| Modelo de lenguaje | Gemini, nivel gratuito | 15 req/min · 1 M tokens/día | Sí. Un turno ≈ 3 llamadas ≈ 2 500 tokens |
| Alojamiento | Hugging Face Spaces, CPU básica | gratuita | Sí. La aplicación es liviana |
| Modelo de asistencia | scikit-learn, local | sin costo | Sí |
| Clasificador de necesidad | scikit-learn, local (D5) | sin costo | Sí |
| Datos | Data Pack sintético | sin costo | — |

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

## 2. Costo por etapa de despliegue

| Etapa | Volumen | Costo estimado | Observación |
|---|---|---|---|
| Demostración de semifinal | ~50 usuarios | 0 USD | — |
| Piloto universitario | 826 estudiantes | 0 USD | Dentro del nivel gratuito |
| Institución completa | ~6 700 estudiantes | 15–40 USD/mes | Requiere el nivel de pago siguiente |
| Red regional | >100 000 | Modelo abierto en servidor propio | El diseño ya lo permite |

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
