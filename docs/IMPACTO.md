# Impacto estimado sobre el indicador de la misión

Entregable 2 · Misión M5 · Indicador de línea base: **68 %**

Este documento responde a una sola pregunta: **¿qué le pasa al indicador de la misión
si esta solución funciona?** Y lo hace con los supuestos a la vista, porque una proyección
sin supuestos visibles no es una proyección: es publicidad.

Todas las cifras se reproducen con `python -m aethera.evaluacion` (semilla fija).

---

## 1. La línea base

| Concepto | Valor | Fuente |
|---|---|---|
| Estudiantes con ansiedad moderada/alta en NOVA | 2 739 | D1 |
| De ellos, **nunca** consultaron un servicio (M5) | **1 868 = 68,2 %** | D1 |
| Segmento prioritario (M5 con ≥ 2 fricciones) | 826 = 44,2 % de M5 | D1 |

El embudo completo del E1 se reproduce exactamente: 12 000 en total → 6 697 de NOVA →
2 739 moderada/alta → 1 868 M5 (68,2 %) → 826 prioritario (44,2 % de M5, 30,2 % de moderada/alta).

> ⚠️ **El denominador importa.** El 68 % es sobre *estudiantes con ansiedad moderada/alta*,
> no sobre todos los estudiantes ni sobre M5. Cualquier proyección que mezcle esos
> denominadores se va de 27 a 95 pp por un error aritmético, no por el impacto del producto.

## 2. La fricción que el producto elimina

Este es el hallazgo que sostiene el impacto. No es una afirmación: es una medición.

| Medida | Valor | Qué significa |
|---|---|---|
| Turnos que muestra un directorio estático | **370 por estudiante** | en 14 días, para su tipo de servicio |
| De esos, compatibles con su horario | **28,2 %** | el resto choca con clases o trabajo |
| Mediana de turnos viables por estudiante | **0** | la mitad del segmento no encuentra ninguno |
| Estudiantes con algún turno viable | 87,3 % | 12,7 % no tiene ninguna opción |
| Primera opción de Ruta | día 13,7 | ya filtrada |

En palabras: **el estudiante de M5 tiene que revisar 370 turnos para encontrar, en el mejor
caso, uno solo que pueda usar.** Esa es la brecha entre necesitar ayuda y pedirla.

Se cruza con el dato de D5: **62 % de las conversaciones de la línea de orientación empiezan
fuera de lun–vie 09:00–18:00**, y **50 % llegan entre las 18:00 y las 06:00** — franjas en
las que orientación y trayectoria ya están cerradas y pares solo llega hasta las 20:00.

## 3. Proyección

Con alcance y conversión declarados:

| | Valor |
|---|---|
| Denominador | 2 739 (ansiedad moderada/alta) |
| Línea base | **68,2 %** (1 868) |
| Alcance 30 % del prioritario | 248 estudiantes llegan a usar Ruta |
| Conversión 35 % | 87 completan una reserva |
| **Indicador proyectado** | **65,0 %** |
| **Reducción** | **−3,2 pp** |

**Supuestos, todos explícitos:**

1. Denominador idéntico al de la línea base.
2. Alcance 30 %: fracción del segmento prioritario (826) que llega a usar Ruta.
3. Conversión 35 %: de quienes usan Ruta, fracción que completa una reserva.
4. Contrafactual **conservador**: se asume que sin Ruta esa demanda no se materializa.
   No está demostrado; es el supuesto que más nos favorece y aun así lo declaramos.
5. No se modela efecto sobre los 1 042 estudiantes de M5 fuera del prioritario.

## 4. Sensibilidad

El indicador **siempre baja**, que es lo que importa. Cuánto depende de los supuestos:

| Alcance | Conversión | M5 antes | M5 después | Reducción |
|---|---|---|---|---|
| 10 % | 20 % | 68,2 % | 67,6 % | −0,6 pp |
| 10 % | 50 % | 68,2 % | 66,7 % | −1,5 pp |
| 20 % | 35 % | 68,2 % | 66,1 % | −2,1 pp |
| 30 % | 20 % | 68,2 % | 66,4 % | −1,8 pp |
| **30 %** | **35 %** | **68,2 %** | **65,0 %** | **−3,2 pp** |
| 30 % | 50 % | 68,2 % | 63,7 % | −4,5 pp |
| 50 % | 35 % | 68,2 % | 62,9 % | −5,3 pp |
| 50 % | 50 % | 68,2 % | 60,7 % | −7,5 pp |

En el rango completo de supuestos plausibles, la reducción está entre **−0,6 y −7,5 pp**.

## 5. Por qué el efecto es modesto, y por qué eso es una virtud

Un −3,2 pp puede parecer poco. Tres razones por las que lo declaramos bajo:

1. **La conversión a reserva no es el indicador.** La misión no mide reservas, mide *buscar
   ayuda*. Un estudiante que entra a Pulse, registra su día y sabe que existen servicios ya
   rompió la barrera, aunque no reserve. Los KPIs de la app miden ese tramo intermedio.
2. **No modelamos a los 1 042 estudiantes de M5 fuera del prioritario.** Una implementación
   real alcanzaría también a quienes tienen 0 o 1 fricción, donde el efecto marginal es
   distinto y probablemente menor.
3. **Una sola institución.** El piloto es NOVA. El indicador por institución es 68,2 %, muy
   parecido al 68,0 % global, así que no hay término de ajusto.

Preferimos un número defendible a uno grande. El discurso útil para el Demo Day es:

> «No prometemos cerrar la brecha del 68 %. Medimos que el estudiante tiene 370 turnos
> delante, de los cuales solo el 28 % le sirve, y que uno de cada ocho no tiene ninguno
> viable aunque mire la pantalla entera. Ruta le entrega el primero que sí. Si eso mueve el
> indicador 3 puntos con supuestos conservadores, la implementación real puede moverlo más;
> si mueve menos, lo vamos a poder ver.»

## 6. Qué medirían los KPIs de la app

Los KPIs de la vista de Bienestar se calculan sobre la sesión de demostración y son
**indicadores de uso del prototipo, no del piloto**. Sirven para mostrar que la cadena
completa funciona de punta a punta:

| KPI | Definición |
|---|---|
| Activation Rate | registros de Pulse / sesiones que vieron Pulse |
| Pulse → Ruta | chats abiertos / quienes registraron su día |
| Match Rate | búsquedas con al menos una opción compatible |
| Booking Conversion | reservas / quienes pidieron ayuda |
| Replanning Success | replanificaciones con nuevas opciones |
| Time-to-Booking | días entre pedir y reservar |
| Asistencia esperada | P(asistir) media de las reservas, según el modelo |

El indicador que falta para Demo Day es **Match Rate en campo**, no en demo: la fracción de
reservas reales a las que el estudiante efectivamente asiste. Eso requiere el piloto.
