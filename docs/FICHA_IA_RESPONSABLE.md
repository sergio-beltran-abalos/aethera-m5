---
title: Ficha de IA Responsable · Aethera Pulse + Ruta
---

**Entregable 2 · Desafío Ciudad Aethera · Misión M5** · Datos 100 % sintéticos del Data Pack.
Aethera es una ciudad universitaria ficticia del desafío binacional Chile–Perú.

## 1 · Modelos y herramientas

| Herramienta | Modelo / técnica | Propósito |
|---|---|---|
| Clasificador, planificador, redactor | Gemini `gemini-3.5-flash-lite` (free tier) | Elegir 1 de 5 motivos **no clínicos**, 1 de 7 acciones y redactar. Nunca diagnostica |
| Asistencia | Regresión logística sobre **D2** (9 400) | Ordenar citas por P(asistir). AUC 0,567 |
| Clasificador sin LLM | TF-IDF + regresión logística sobre **D5** (2 500) | Sustituye al LLM sin clave. **80,8 %** CV vs 20,5 % base |

**Principio rector: el modelo de lenguaje nunca decide datos**, solo *qué hacer* y *cómo decirlo*.
Servicios, fechas, horas y teléfonos salen de herramientas que leen el Data Pack; si el redactor
los inventa, el guardrail de salida lo detecta y su respuesta se descarta por una plantilla
verificada. Proveedores intercambiables; **sin clave de API la app funciona completa**.

## 2 · Datos utilizados

Solo los siete datasets sintéticos del Data Pack: **D1** (12 000) · **D2** (9 400) · **D3**
(130 000) · **D4** (6 000) · **D5** (2 500) · **D6** (15) · **D7** (32). **No se usan datos reales
ni externos sensibles**; no hay identificadores de personas. Los tres estudiantes de la demo son
filas reales de D1 del segmento M5, con identificadores sintéticos.

**Transferencia internacional:** el texto del chat y, si el estudiante lo autoriza, su registro
de ánimo salen hacia el proveedor del modelo. Bajo la Ley 29733 y su reglamento
(DS 016-2024-JUS) eso exige evaluar el marco de protección del país de destino. Se asumen:
encargado de tratamiento, **sin uso para entrenar**, mínimo de texto, sin identificadores.
Declararlo es condición previa a cualquier despliegue real.

## 3 · Alcance y límites

**Hace:** traduce lenguaje cotidiano a un motivo no clínico; consulta servicios y calendario;
propone citas compatibles con el horario real; reserva, reprograma y deriva a una persona.

**NO hace, por diseño:** no diagnostica ni evalúa gravedad clínica · no receta ni recomienda
medicamentos o tratamientos · no es terapia · no atiende emergencias · no resuelve tareas
académicas · no entrega datos de otros estudiantes · **no usa el nivel de ansiedad de nadie en
tiempo de ejecución** (la segmentación es diagnóstico, no un disparador).
**Apoya, no reemplaza, la atención profesional.**

## 4 · Riesgos y mitigaciones

| Riesgo | Mitigación implementada |
|---|---|
| Etiquetaje clínico | Guardrail de salida con 9 patrones; se acepta solo con negación ("no tienes…"). Si falla, cae a plantilla |
| Falsificación de datos | El LLM no accede a datos; todo pasa por herramientas, validadas contra el catálogo real |
| **Autolesión no detectada por patrón** | **2.ª capa:** el planificador marca `senal_de_riesgo` y activa protocolo de crisis con líneas reales (Perú 113 · Chile \*4141 · SAMU) |
| Manipulación / prompt injection | Patrones dedicados que bloquean y reafirman el rol no clínico |
| Fuga de datos ajenos | Patrón dedicado; la cola de contacto lleva solo código y motivo no clínico |
| Sesgo del Data Pack | Tres sesgos detectados y asumidos como decisiones de diseño (§6) |
| Modelo fuera de rango | Indicador de confianza visible cuando predice fuera de la zona con evidencia histórica |

## 5 · Supervisión humana

- Botón permanente **"Quiero que una persona me contacte"**, que Ruta ofrece sola ante crisis.
- **Cola de contacto humano** en la vista de Bienestar: prioridad, código y motivo **no clínico**;
  nunca el texto ni el estado de ánimo. **Prioridad automática** ante señal de crisis, con la
  línea de ayuda mientras se espera la atención.
- **Escalamiento:** si no hay turnos compatibles, se registra seguimiento y se ofrece pares como
  primer contacto, en vez de responder "no hay nada".
- **Auditoría por diseño:** el panel "Cómo decidió Ruta" registra cada turno —acción, motivo,
  herramientas, procedencia de cada dato y guardrails activados—.

## 6 · Sesgos del Data Pack que encontramos

1. El sentimiento de D4 refleja el **canal**, no la persona (buzón 100 % `strained`, foro no) → no lo usamos como señal.
2. El motivo declarado en D4 **casi no se refleja** en su texto → no entrenamos con D4.
3. La derivación de D5 **no depende del motivo** (34,2 % de coherencia vs 33,3 % de azar) → el mapa motivo → servicio sale de D2.## 7 · Privacidad

**Consentimiento** expreso, informado y con finalidad; opcional y no condiciona ningún servicio.
**Minimización:** el horario se usa solo para calcular franjas libres; nunca notas, puntajes ni
asistencia. **Identidad separada** del contenido. **ARCO completo desde la interfaz** (consultar,
exportar JSON, borrar; borrar elimina también el uso posterior en el chat). **Agregación con
umbral:** la vista de Bienestar suprime toda celda de menos de **10 personas**; los ánimos
individuales nunca se agregan ni se comparten. **Sin uso secundario** (becas, evaluación,
disciplina, publicidad) ni terceros, y **sin acceso individual** a docentes, autoridades ni
áreas académicas o disciplinarias.

**Cita privada:** el estudiante elige el título con que su reserva aparece en el calendario; por
defecto es neutro («Cita campus»), porque nombrar el servicio es lo único que delata el motivo.
Sede, fecha y hora siguen visibles. **Iniciativa con permiso:** Ruta puede escribir primero solo
con consentimiento de Pulse y cada disparador actúa una vez por sesión; el aviso de calendario
que lo dispara es común a toda la comunidad y no se segmenta por perfil.

## 8 · Transparencia hacia el usuario

Ruta se presenta como **IA de orientación no clínica** en el primer turno, en la interfaz y en
cada respuesta de crisis. El estudiante **elige y rechaza** cada ruta y puede replanificar
cuantas veces quiera. El panel de trazabilidad explica en lenguaje llano por qué se propuso
cada cita, y Pulse dice siempre quién ve el registro. El modelo de asistencia **declara sus
límites en pantalla**, incluido que no discrimina bien en el rango de esperas que ofrece la
demo.

## 9 · Marco normativo

**Ley 29733** y su reglamento (**DS 016-2024-JUS**, vigente desde marzo de 2025), que califica
los datos de salud como sensibles y exige consentimiento expreso con finalidad específica; y
**Ley 31814** (**DS 115-2025-PCM**). La clasificación específica de Aethera se confirmará con
asesoría legal antes de cualquier despliegue real, junto con una evaluación de impacto con un
Oficial de Datos Personales. **Precedente:** Woebot cerró su app de consumo en junio de 2025
por el costo de cumplir la autorización de la FDA; Aethera evita ese camino con orientación
no clínica y límites declarados.