# Viabilidad y costo

Todo lo que el prototipo necesita para operar en el piloto university del E2.

## 1. Costo marginal: 0 USD dentro del piloto

| Recurso | Plan | Límite | ¿Alcanza? |
|---|---|---|---|
| Modelo de lenguaje | Gemini free tier | 15 req/min · 1M tokens/día | Sí. Un turno ≈ 3 llamadas ≈ 2 500 tokens |
| Alojamiento | Hugging Face Spaces, CPU básica | gratuita | Sí. La app es liviana |
| Modelo de asistencia | scikit-learn local | sin costo | Sí |
| Clasificador de necesidad | scikit-learn local (D5) | sin costo | Sí |
| Datos | Data Pack sintético | sin costo | — |

**Estimación para el piloto university.** Si atienden 826 estudiantes (el segmento
prioritario de NOVA) y cada uno registra 4 días en Pulse y abre 2 chats:

| Concepto | Cálculo | Total |
|---|---|---|
| Turnos de chat | 1 652 chats × 3 llamadas × 2 500 tokens | ~12,4 M tokens |
| Frases de Pulse | 3 304 registros × ~200 tokens | ~0,7 M tokens |
| **Total** | | **~13 M tokens/mes** |

Con el límite gratuito de 1 M/día (≈30 M/mes), **el piloto completo entra en el plan
gratis**. Si se duplicara el alcance, bastaría con pasar al nivel de pago más bajo del
proveedor: el costo seguiría siendo marginal frente al de un profesional de bienestar.

## 2. costo por etapa de despliegue

| Etapa | Volumen | Costo estimado | Nota |
|---|---|---|---|
| Demo / semifinal | ~50 usuarios | 0 USD | |
| Piloto university | 826 estudiantes | 0 USD | Entra en el nivel gratuito |
| city's completa | ~6 700 estudiantes | 15–40 USD/mes | Requiere el siguiente nivel de pago |
| Red regional | >100 000 | Modelo abierto en servidor propio | El diseño ya lo permite |

## 3. Viabilidad técnica

**Arranque.** Carga el Data Pack y entrena dos modelos en ~25 s. No hay base de datos: el
estado vive en memoria durante la sesión.

**Reproducibilidad.** La agenda usa una semilla fija (`random.Random`), así que la demo
produce exactamente los mismos números en cada ejecución. Importante para grabar el video y
para que cualquier revisor vea lo mismo que ve el jurado.

**Degradación.** Cada llamada al modelo tiene respaldo. Sin clave de API la app funciona
completa con el clasificador de D5 y plantillas; con la clave, sube la calidad del lenguaje.
**La app nunca se cae.** En una demo en vivo, un fallo de red no puede dejar la pantalla en
blanco.

**Portabilidad.** Cambiar de institución es una variable:

```bash
set AETHERA_INSTITUCION=INST_NEXUS
```

El Data Pack ya incluye tres instituciones y cinco distritos, y las líneas de ayuda son
bilingües (Perú/Chile). No hay código específico de NOVA fuera de esa constante.

## 4. Cómo crecer sin reescribir

1. **Agenda real.** Hoy la agenda es simulada. Se sustituye `generar_agenda()` por una consulta
   al sistema de citas real; el resto del motor no cambia.
2. **Identidad.** Hoy el `student_id` viene del selector de demo. Se sustituye por SSO de la
   universidad, conservando que el sistema nunca recibe `anxiety_band`.
3. **Persistencia.** El registro de Pulse pasa de memoria a almacenamiento cifrado con control
   de acceso por roles y bitácora, como ya se promete en la ficha.
4. **Modelo de lenguaje.** Ya es intercambiable entre cuatro proveedores y `offline`.

## 5. Riesgos de viabilidad

| Riesgo | Mitigación |
|---|---|
| Cuota gratuita se agota en un evento | Respaldos sin modelo; la app sigue operable |
| Agenda real tiene formas distintas a la simulada | El motor consume un DataFrame con esquema fijo, documentado en `servicios.generar_agenda` |
| Un solo archivo de 2 100 líneas era difícil de mantener | Reestructurado en 11 módulos con pruebas de humo |
| El modelo no generaliza fuera de NOVA | Declarado; el clasificador se reentrena con D5 de otras instituciones |
