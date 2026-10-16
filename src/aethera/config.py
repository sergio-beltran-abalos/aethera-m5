"""
Aethera · configuración central.

Todo lo ajustable vive aquí: rutas, proveedor de IA, Taxonomía de motivos,
supuestos de horario y fechas de la demo. Ningún otro módulo define constantes
de negocio.
"""
from __future__ import annotations

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────────────────────────────────────
RAIZ = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("AETHERA_DATA", RAIZ / "data"))

ARCHIVOS_DATAPACK = {
    "D1": "D1_wellbeing_survey.csv",
    "D2": "D2_support_services.csv",
    "D3": "D3_academic_trajectory.csv",
    "D4": "D4_testimonials.json",
    "D5": "D5_help_line_conversations.json",
    "D6": "D6_services_map.geojson",
    "D7": "D7_calendar.csv",
}
OBLIGATORIOS = ["D1", "D2", "D4", "D5", "D6", "D7"]

# ─────────────────────────────────────────────────────────────────────────────
# IA
# ─────────────────────────────────────────────────────────────────────────────
PROVEEDOR = os.getenv("AETHERA_PROVEEDOR", "gemini").lower()

# Los IDs por defecto se pueden sobrescribir con AETHERA_MODELO sin tocar código.
MODELOS_POR_DEFECTO = {
    # gemini-3.5-flash activo y con cuota disponible en la capa gratuita
    "gemini": "gemini-3.5-flash",
    "openai": "gpt-5.6-luna",
    "huggingface": "meta-llama/Llama-3.3-70B-Instruct",
    "compatible": "TU_MODELO",
    "offline": "reglas-sin-llm",
}
MODELO = os.getenv("AETHERA_MODELO") or MODELOS_POR_DEFECTO.get(PROVEEDOR, "reglas-sin-llm")
COMPATIBLE_BASE_URL = os.getenv("AETHERA_BASE_URL", "https://TU-PROVEEDOR/v1")

# Claves que se exporta(n) como variable de entorno o como secreto en HF Spaces.
CLAVE_POR_PROVEEDOR = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "compatible": "COMPATIBLE_API_KEY",
    "huggingface": "HF_TOKEN",
}

# Límites de la capa gratuita, para la sección de costo de la ficha.
COSTO_REF = {
    "gemini": "Gemini free tier (15 RPM · 1 millón de tokens/día)",
    "alojamiento": "equipo propio + túnel de Cloudflare · sin costo, sin tarjeta",
    "nota": "Costo marginal ≈ 0 USD; ninguna etapa requiere tarjeta de crédito. "
            "Ver docs/COSTOS.md y docs/PUBLICACION.md",
}

# ─────────────────────────────────────────────────────────────────────────────
# Alcance del piloto
# ─────────────────────────────────────────────────────────────────────────────
INSTITUCION = os.getenv("AETHERA_INSTITUCION", "UNI_NOVA_AETHER")
NOMBRE_INSTITUCION = "NOVA"

FECHAS_DEMO = {
    "Semana regular · mar 20 oct 2026": "2026-10-20",
    "Semana de evaluaciones · mar 10 nov 2026": "2026-11-10",
    "Antes de finales · jue 26 nov 2026": "2026-11-26",
}
FECHA_DEMO = FECHAS_DEMO["Semana regular · mar 20 oct 2026"]

# Ventana que se muestra al estudiante. Es una decisión de producto, no del modelo:
# aunque el modelo de asistencia se entrena con esperas de hasta ~120 días,
# ofrecer una cita esta semana es el argumento de valor de Ruta.
HORIZONTE_DIAS = 14
# Multiplicador de carga académica que sí se modela (ver horarios.py).
CARGA_BASE_CREDITOS = 20
SEMILLA = 42

# ─────────────────────────────────────────────────────────────────────────────
# Taxonomía de motivos (dominio de D2, nunca texto libre del LLM)
# ─────────────────────────────────────────────────────────────────────────────
MOTIVOS = {
    "academic_pressure": "presión académica (evaluaciones, carga, notas, organización de estudios)",
    "social_support": "apoyo social (sentirse solo/a, pocas personas cerca, adaptación)",
    "career_concern": "preocupación laboral o de futuro profesional (prácticas, empleo, carrera)",
    "sleep_and_routine": "sueño y rutina (descanso, cansancio, manejo del tiempo)",
    "preventive_guidance": "orientación preventiva (quiere conocer qué apoyos existen)",
}
MOTIVO_CORTO = {
    "academic_pressure": "Presión académica",
    "social_support": "Apoyo social",
    "career_concern": "Futuro laboral",
    "sleep_and_routine": "Sueño y rutina",
    "preventive_guidance": "Orientación general",
}

TIPO_ES = {
    "counseling": "Orientación",
    "peer_support": "Acompañamiento entre pares",
    "career_guidance": "Orientación de trayectoria y empleabilidad",
}
CANAL_ES = {"in_person": "presencial", "digital": "virtual", "phone": "telefónico"}

DIAS_INGLES = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DIAS_ES_CORTO = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# ─────────────────────────────────────────────────────────────────────────────
# Supuestos de horario
# ─────────────────────────────────────────────────────────────────────────────
# Nota metodológica importante:
#   Los bloques base son SUPUESTOS (el Data Pack no trae horarios de clases).
#   Lo que sí viene de los datos es la duración del bloque, que se escala con
#   `credit_load` de D3 (ver horarios.py), y el lugar del trabajo, que se deriva
#   de `study_mode`. Estar en que parte del día choca NO se infiere del texto.
SUPUESTOS_HORARIO = {
    "clases_diurno": ("08:00", "13:00"),
    "clases_nocturno": ("18:30", "22:30"),
    "creditos_que_llenan_bloque": CARGA_BASE_CREDITOS,
    "creditos_bloque_completo": 26,
    "inicio_trabajo_diurno": "15:00",
    "inicio_trabajo_nocturno": "08:00",
    "almuerzo_si_jornada_de": 6,
    "margen_virtual_min": 15,
    # El traslado presencial ya NO es una constante plana: se estima con la
    # distancia real entre el distrito del estudiante y la sede (D6 GeoJSON).
    "velocidad_caminata_kmh": 4.5,
    "minutos_traslado_piso": 10,
    "sabado_libre": True,
}

# ─────────────────────────────────────────────────────────────────────────────
# Privacidad
# ─────────────────────────────────────────────────────────────────────────────
K_MINIMO = 10          # supresión de celdas pequeñas en la vista de Bienestar
DIAS_TRACK = 28        # ventana del mes en colores de Pulse

LINEAS_AYUDA = {
    "Peru": "Línea 113, opción 5 (salud mental, Minsa; gratuita, 24 horas). Emergencias: SAMU 106.",
    "Chile": "*4141 (Línea de prevención del suicidio, Minsal; gratuita, 24 horas). Emergencias: SAMU 131.",
}
LINEA_POR_DEFECTO = "Peru"


def clave_api() -> str:
    """Nombre de la variable de entorno que guarda la clave del proveedor actual."""
    return CLAVE_POR_PROVEEDOR.get(PROVEEDOR, "GEMINI_API_KEY")
