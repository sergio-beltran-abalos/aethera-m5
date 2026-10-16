# Opciones de publicación

El enunciado exige trabajar con herramientas de nivel gratuito y no depender de servicios
pagados. Este documento compara las alternativas disponibles según tres criterios, en este
orden: **coste cero**, **ausencia de tarjeta de crédito** y facilidad de reproducción.

**Ninguna de las opciones genera cargo.**

---

## Resumen

| Opción | Coste | Pide tarjeta | Requiere cuenta | Dirección estable | Verificada |
|---|---|---|---|---|---|
| **`compartir.bat` / `.sh`** | 0 USD | **No** | No | No | **Sí** |
| Gradio Share | 0 USD | No | No | No | Pendiente |
| Google Colab | 0 USD | No | Sí (Google) | No | — |
| Hugging Face Spaces | 0 USD | **Sí** | Sí | Sí | Pendiente |

**Opción recomendada: `compartir.bat`.** Es la única que cumple simultáneamente coste cero,
ausencia de tarjeta y ausencia de registro.

---

## 1. Script de servidor público — recomendada

**Estado: verificada. Coste 0 USD, sin cuenta, sin tarjeta.**

El repositorio incluye un script que levanta la aplicación en el equipo del usuario y genera
una dirección pública HTTPS mediante un túnel de Cloudflare.

| Sistema | Archivo | Ejecución |
|---|---|---|
| Windows | `compartir.bat` | Doble clic sobre el archivo |
| macOS / Linux | `compartir.sh` | `chmod +x compartir.sh && ./compartir.sh` |

El script ejecuta el siguiente procedimiento:

1. Comprueba que Python esté disponible.
2. Verifica la presencia de los siete archivos del Data Pack.
3. Crea el entorno virtual e instala las dependencias si no existen.
4. Comprueba que el puerto 7860 esté libre.
5. Instala Cloudflare Tunnel mediante el gestor de paquetes del sistema, si no está presente.
6. Inicia la aplicación y abre el túnel.
7. Muestra la dirección pública resultante.

La dirección permanece activa mientras la sesión permanezca abierta.

**Ventajas:** coste cero, sin registro, sin tarjeta, sin cuota que agotar.
**Limitación:** la dirección cambia en cada ejecución y depende de que el equipo del usuario
esté encendido y conectado a internet.

---

## 2. Dirección temporal de Gradio

```bash
set AETHERA_SHARE=1
python app.py
```

El parámetro está implementado en `src/aethera/ui.py` y delega en el servicio de cómputo
remoto de Gradio. No requiere cuenta ni tarjeta. **No fue verificable durante el desarrollo**
por restricción de salida de red en el entorno de construcción; requiere verificación previa
en la red de destino.

---

## 3. Google Colab

Coste cero y sin tarjeta. El cuaderno de `notebook/` puede ejecutarse en Colab y publicar la
interfaz mediante el mecanismo de enlace de Gradio. El enlace tiene vigencia limitada y se
desconecta al cerrar la sesión del cuaderno.

Ventaja: no requiere servidor propio. Inconveniente: la duración de la sesión es limitada.

---

## 4. Hugging Face Spaces

El nivel **CPU Basic no genera cargo**. Sin embargo, la creación del Space puede solicitar una
tarjeta de crédito como verificación de identidad. **Por ese motivo se descarta cuando la
política del equipo no admite registrar una tarjeta**, dado que la opción 1 ofrece las mismas
capacidades sin ese requisito.

Procedimiento, en caso de decidirse por esta vía:

1. Crear un Space con SDK **Gradio** y visibilidad **Private**.
2. Cargar `app.py`, `requirements.txt` y `README.md`.
3. Crear el directorio `data/` y subir los siete archivos del Data Pack.
4. En **Settings → Variables and secrets**, registrar `GEMINI_API_KEY`.
5. El Space se compila automáticamente y queda disponible en una dirección estable.

El despliegue automatizado está disponible en `tools/desplegar_hf.py` y requiere un token de
escritura de Hugging Face en la variable de entorno `HF_TOKEN`. El token se lee del entorno o
del registro del sistema; nunca se acepta como argumento de línea de comandos.

**Advertencia operativa:** los recursos del nivel gratuito pueden liberarse tras un período
prolongado de inactividad, lo que rompería la dirección estable.
