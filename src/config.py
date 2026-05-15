"""
Configuración global de T.A.L.O.N.
Carga dinámica de catálogos y configuración de la IA.
"""
import os
import json
import streamlit as st
import google.generativeai as genai

# --- 1. RUTA DINÁMICA ANTI-ERRORES ---
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_CATALOGOS = os.path.join(DIR_ACTUAL, "data_ref", "catalogos_negocio.json")
# Unidades de medida oficiales — raíz del proyecto: data_ref/Unidades de Referencia.txt
_RUTA_UNIDADES_TXT = os.path.normpath(
    os.path.join(DIR_ACTUAL, "..", "data_ref", "Unidades de Referencia.txt")
)
_RUTA_UNIDADES_TXT_ALT = os.path.join(DIR_ACTUAL, "data_ref", "Unidades de Referencia.txt")


def _cargar_unidades_desde_txt() -> list[str]:
    """
    Lee códigos SAP de unidad desde data_ref/Unidades de Referencia.txt.
    Formato por línea: CODIGO<TAB>Descripción (se usa solo el código).
    """
    rutas = (_RUTA_UNIDADES_TXT, _RUTA_UNIDADES_TXT_ALT)
    for ruta in rutas:
        if not os.path.isfile(ruta):
            continue
        try:
            codigos: set[str] = set()
            with open(ruta, encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    codigo = line.split("\t", 1)[0].strip()
                    if codigo:
                        codigos.add(codigo.upper())
            return sorted(codigos)
        except OSError as e:
            print(f"Error leyendo unidades desde {ruta}: {e}")
    return []


# --- 2. FUNCIÓN DE CARGA ---
def cargar_catalogos_maestros():
    """Lee el archivo maestro JSON de forma segura."""
    if os.path.exists(RUTA_CATALOGOS):
        try:
            with open(RUTA_CATALOGOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error leyendo el JSON de catálogos: {e}")
    else:
        print(f"Atención: No se encontró el archivo de catálogos en: {RUTA_CATALOGOS}")
    return {}

# --- 3. CREACIÓN DE LA VARIABLE GLOBAL (¡SIN ESPACIOS A LA IZQUIERDA!) ---
CATALOGOS = cargar_catalogos_maestros()

# --- 4. VARIABLES EXPORTADAS PARA APP.PY ---
_UNID_DESDE_TXT = _cargar_unidades_desde_txt()
_UNID_DESDE_JSON = CATALOGOS.get("unidades_medida", [])
UNIDADES_REF = (
    _UNID_DESDE_TXT
    if _UNID_DESDE_TXT
    else (list(_UNID_DESDE_JSON) if isinstance(_UNID_DESDE_JSON, list) else [])
)
CUSTODIOS = CATALOGOS.get("custodios_por_tipo", {})
NOMBRES_MATERIALES = CATALOGOS.get("mapeo_nombres_material", {})
DOMINIOS_CONFIG = CATALOGOS.get("dominios_config", {}) 

# --- 5. CONFIGURACIÓN DEL MODELO DE IA ---
def obtener_modelo_agente() -> str:
    """Retorna el nombre del modelo de Google Gemini activo en T.A.L.O.N."""
    return "gemini-2.5-flash"

def configurar_api_ia():
    """Inicializa la llave de Gemini leyendo desde secrets.toml de Streamlit."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            print("ADVERTENCIA: No se encontró la GEMINI_API_KEY en .streamlit/secrets.toml.")
            return False
            
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configurando la API de Gemini: {e}")
        return False

# La configuración de la API se llama explícitamente antes de cada uso en motor_ia.py