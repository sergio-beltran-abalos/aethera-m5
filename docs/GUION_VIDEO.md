# Guion del video · Entregable 2 (3–5 min)

**Objetivo:** evidenciar que el prototipo funciona sobre los datos, y encuadrarlo para que
el jurado sepa qué problema resuelve y por qué ese.

> **¿Tiene que incluir el Entregable 1?** Sí, pero **comprimido a 40 segundos**. El enunciado
> pide "mostrar funcionando", así que el grueso es demo en vivo. Pero el jurado califica
> *Comprensión del problema* (15 %) sin haber visto el diagnóstico, y una demo sin encuadre
> no impresiona a nadie. El E1 entra como **la evidencia que justifica la solución**, no como
> una clase de metodología: no recontamos el embudo completo, contamos **la cifra que duele**
> (68 %) y **a quién le duele** (826 personas).

---

## Estructura

| Bloque | Tiempo | Qué |
|---|---|---|
| 1 · El problema | 0:00 – 0:40 | La cifra, por qué NO es culpa del estudiante |
| 2 · La población | 0:40 – 1:05 | Cómo se llegó a los 826 y qué tienen en común |
| 3 · La solución | 1:05 – 2:35 | Demo en vivo: Pulse → Ruta → reservar → replanificar |
| 4 · Qué se mueve | 2:35 – 3:10 | Impacto sobre el 68 %, con supuestos |
| 5 · Los límites | 3:10 – 3:45 | IA responsable, incluido el límite del modelo |
| 6 · Cierre | 3:45 – 4:00 | Reencuadre final |

**Duración objetivo: 4:00.** Margen: 3:00 (corta bloques 4 y 5) — 5:00 (alarga la demo).

---

## 1 · El problema — 0:00 a 0:40

**Pantalla:** la app en la pestaña Pulse, sin tocar nada.

> "En Aethera, el 68 % de los estudiantes con sintomatología ansiosa moderada-alta nunca ha
> consultado un servicio de apoyo. 1 868 personas.
>
> Lo fácil sería decir que no saben que esos servicios existen. Pero al analizar las 2 500
> conversaciones de la línea de orientación encontramos otra cosa: **el 62 % escribe fuera
> del horario de atención, y la mitad llega de noche.**
>
> No es que no busquen ayuda. Es que llegan cuando ya no hay nadie."

**En pantalla:** `68 %` · `62 % fuera de horario` · `50 % de noche`

---

## 2 · La población — 0:40 a 1:05

**Pantalla:** selector de perfil; mostrar el perfil B ya seleccionado.

> "Del cruce de la encuesta de bienestar con el historial académico nos quedó un grupo
> concreto: **826 estudiantes**. Son quienes tienen al menos dos fricciones a la vez.
>
> El caso que usamos hoy sale del dataset: estudia de noche, trabaja a tiempo completo y no
> tiene red de apoyo en la ciudad.
>
> Fíjense en su agenda: **de 8:00 a 16:24 trabajando, de 18:30 a 22:20 en clases.** Le quedan
> dos horas al día. Ese es el margen real con el que hay que cumplir."

**Por qué esta parte importa:** el jurado tiene que entender que la población no es "jóvenes
con ansiedad", sino **gente con una agenda imposible**. De ahí sale todo el producto.

**En pantalla:** `826` · `2 fricciones o más` · la agenda del estudiante

---

## 3 · La solución — 1:05 a 2:35

### 3.1 Pulse (1:05 – 1:30)

1. **Activar el consentimiento.** Señalar el checkbox.
   > "Esto primero: sin consentimiento no se guarda nada."
2. **Elegir ánimo** "Muy pesado" y un tema.
3. **Registrar mi día.**
   > "Veinte segundos. No es un test, no tiene respuestas correctas y no calcula puntajes.
   > Si el estudiante lo autoriza, queda un registro que solo ve él."
4. Presionar **💬 Hablar con Ruta** → salta a la pestaña Ruta.

### 3.2 Ruta (1:30 – 2:15)

**Escribir:** `Trabajo todo el día, estudio de noche y no conozco a nadie en la U`

> "Ruta no diagnostica. Escucha, clasifica lo que cuenta en un motivo no clínico y propone
> citas concretas."

**Señalar las 3 opciones:**

> "Mírenlas: son las 17:00. Ni una sola cae dentro de su horario de trabajo ni dentro de sus
> clases. Eso no es casualidad: es un solver que cruza la apertura de cada servicio con la
> agenda del estudiante."

### 3.3 Reservar (2:15 – 2:35)

**Escribir:** `2`

> "Reserva, y pone recordatorios el día anterior y dos horas antes."

*(Opcional, si sobra tiempo: escribir `no puedo ese día` para mostrar la replanificación.)*

---

## 4 · Qué se mueve — 2:35 a 3:10

**Pantalla:** pestaña Bienestar.

> "En la prueba offline con 300 estudiantes reales del segmento: un directorio tradicional
> les muestra **370 turnos**, de los cuales solo el **28 %** les sirve. La mediana es
> **cero turnos viables**. Ruta les entrega el primero que sí, ya filtrado."

**Luego, la proyección:**

> "Sobre el indicador de la misión: con supuestos declarados uno por uno, el 68 % baja a
> **65 %**, y en todo el rango de supuestos plausibles se mueve entre **0,6 y 7,5 puntos**.
> Es poco, y lo decimos poco: no prometemos cerrar la brecha."

---

## 5 · Los límites — 3:10 a 3:45

**Pantalla:** volver a Ruta. Escribir: `Ya no quiero vivir`

> "Ante una señal de riesgo Ruta deja de orientar. Da líneas reales — la 113 en Perú, el
> 4141 en Chile — y ofrece que una persona lo contacte."

**Luego, sobre el modelo — esto es lo que nos distingue:**

> "Y una cosa más: nuestro modelo de asistencia rinde bien donde hay datos, y **muy mal en
> la franja que la demo ofrece**. Lo medimos: 0,44 de AUC, es decir por debajo del azar. No
> lo escondemos. La app marca confianza baja ahí y lo declara en pantalla."

---

## 6 · Cierre — 3:45 a 4:00

> "Aethera no diagnostica, no receta y no es terapia.
>
> Lo que hace es algo mucho más pequeño y más útil: **convierte «necesito ayuda» en una cita
> que el estudiante realmente puede cumplir.**"

---

## Checklist antes de grabar

- [ ] La IA real respondiendo: el panel debe decir `decidida por modelo`, **nunca** `reglas de respaldo`
- [ ] Dejar respirar la pantalla ~8 segundos por respuesta: se ve lento, pero funciona
- [ ] Pestaña Bienestar abierta y con KPIs visibles antes de grabar ese bloque
- [ ] `Ya no quiero vivir` escrito en el portapapeles
- [ ] Tema claro (la app se fuerza sola por JS)
- [ ] Audio limpio: el video se evalúa por claridad, no por producción
- [ ] Verificar que la agenda muestra `17:00` para el perfil B (si cambias la fecha simulada, cambian las horas)

## Variante corta (3:00) — si se pasa de tiempo

| Bloque | Acción |
|---|---|
| 1 · El problema | **No cortar.** Es el bloque que más puntúa |
| 2 · La población | Comprimir a 15 s: "826 estudiantes, y este es uno de ellos" |
| 3 · La solución | Cortar la replanificación |
| 4 · Qué se mueve | Solo la cifra de los 370 turnos; mover la proyección al cierre |
| 5 · Los límites | **No cortar.** La honestidad sobre el modelo es el diferenciador |
| 6 · Cierre | Mantener literal |

## Preguntas que más cuesta — respuestas cortas

**«¿Por qué no usan un modelo más grande?»**
Equidad: el enunciado exige nivel gratuito. Y el problema no es de inteligencia, es de
restricciones horarias: un modelo más grande no resuelve un choque de agenda.

**«¿Cómo saben que esto funciona y no solo que funciona en la demo?»**
No lo sabemos todavía, y por eso el E2 proyecta con supuestos declarados en vez de afirmar
un resultado. El indicador que falta es el *Match Rate en campo*: la fracción de reservas
reales a las que el estudiante asiste. Eso exige el piloto.

**«¿Y si se detecta una crisis?»**
Dos capas. La primera es por patrón, determinista y auditable. La segunda es el propio modelo
marcando riesgo indirecto. En ambos casos: líneas reales y contacto humano con prioridad alta.

**«¿Por qué 10 personas y no menos en el tablero?»**
k-anonimato. Con menos de 10, en una universidad de ese tamaño, se podría reidentificar a
alguien cruzando dos tablas. Es el mismo criterio que aplica la Ley 29733 a los datos sensibles.

**«El 68 % es un invento del dataset sintético, ¿no?»**
Los datos son sintéticos, sí. Pero el **razonamiento** se sostiene con cualquier dataset: si
la derivación actual acierta 34 % cuando el azar es 33 %, el sistema de referencia no está
transmitiendo el motivo. Ese hallazgo es el que justifica cambiarlo.
