# Opciones de publicación

El enunciado exige trabajar con herramientas de nivel gratuito y no depender de servicios
pagados. Este documento compara las vías disponibles según tres criterios, en este orden:
**coste cero**, **ausencia de tarjeta de crédito** y facilidad de reproducción.

**Ninguna de las opciones genera cargo. Ninguna requiere tarjeta de crédito.**

---

## Resumen

| Opción | Coste | Pide tarjeta | Requiere cuenta | Instalación extra | Verificada |
|---|---|---|---|---|---|
| **`compartir.bat` / `.sh`** | 0 USD | No | No | Cloudflare Tunnel | **Sí** |
| **`AETHERA_SHARE=1`** | 0 USD | No | No | Ninguna | **Sí** |
| Google Colab | 0 USD | No | Sí (Google) | Ninguna | — |

Las dos primeras son las dos recomendadas. Ninguna de las dos requiere tarjeta, y por esa
razón **Hugging Face Spaces queda descartada**: aunque su nivel CPU Basic no genera cargo,
la creación del Space solicita una tarjeta de crédito como verificación de identidad.

---

## 1. Enlace público de Gradio — la más simple

**Estado: verificada. Coste 0 USD, sin cuenta, sin tarjeta, sin instalar nada.**

Gradio ofrece un servicio de túnel propio. Basta una variable de entorno:

```bash
set AETHERA_SHARE=1        # Windows (CMD)
export AETHERA_SHARE=1     # macOS / Linux
python app.py
```

La salida muestra la dirección:

```
* Running on public URL: https://<codigo>.gradio.live
```

La dirección es accesible desde cualquier red y cambia en cada ejecución. El proceso debe
permanecer activo.

**Ventaja:** no requiere ningún programa adicional.
**Limitación:** el servicio pertenece a un tercero y su disponibilidad no está garantizada;
si no responde, se cae el enlace sin aviso.

---

## 2. Túnel de Cloudflare — recomendada para la demostración

**Estado: verificada. Coste 0 USD, sin cuenta, sin tarjeta.**

El repositorio incluye un script que automatiza el procedimiento completo.

| Sistema | Archivo | Ejecución |
|---|---|---|
| Windows | `compartir.bat` | Doble clic |
| macOS / Linux | `compartir.sh` | `chmod +x compartir.sh && ./compartir.sh` |

Procedimiento que ejecuta el script:

1. Comprueba que Python esté disponible.
2. Verifica la presencia de los siete archivos del Data Pack.
3. Crea el entorno virtual e instala las dependencias si no existen.
4. Comprueba que el puerto 7860 esté libre.
5. Instala Cloudflare Tunnel mediante el gestor de paquetes del sistema, si no está presente.
6. Inicia la aplicación y abre el túnel.
7. Muestra la dirección pública.

**Ventaja:** el túnel se administra desde el equipo del usuario, sin depender de un
servicio de terceros, y el script deja constancia del procedimiento.
**Limitación:** la dirección cambia en cada ejecución y depende de que el equipo permanezca
encendido y conectado.

---

## 3. Google Colab

Coste cero y sin tarjeta. El cuaderno de `notebook/` puede ejecutarse en Colab y publicar la
interfaz mediante el enlace de Gradio. El enlace tiene vigencia limitada y se desconecta al
cerrar la sesión del cuaderno.

Ventaja: no requiere servidor propio. Inconveniente: la duración de la sesión es limitada y
el cuaderno debe detenerse para publicar la interfaz.

---

## Nota sobre la vía descartada

**Hugging Face Spaces** fue evaluada y descartada. El nivel CPU Basic no genera cargo, pero
la creación del repositorio solicita una tarjeta de crédito como verificación de identidad.
Dado que las opciones 1 y 2 ofrecen las mismas capacidades sin ese requisito, se optó por no
incorporar una tarjeta al proceso.

Si en el futuro se decide habilitar esa vía, el procedimiento es el siguiente:

1. Crear un Space con SDK **Gradio** y visibilidad **Private** (obligatoria: el Data Pack no
   puede redistribuirse).
2. Cargar `app.py`, `requirements.txt` y `README.md`.
3. Crear el directorio `data/` y subir los siete archivos del Data Pack.
4. En **Settings → Variables and secrets**, registrar `GEMINI_API_KEY`.

Los recursos del nivel gratuito pueden liberarse tras un período prolongado de inactividad,
lo que afectaría la estabilidad de la dirección.
