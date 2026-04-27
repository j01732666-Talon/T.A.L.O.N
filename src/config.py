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
        print(f"⚠️ Atención: No se encontró el archivo de catálogos en: {RUTA_CATALOGOS}")
    return {}

# --- 3. CREACIÓN DE LA VARIABLE GLOBAL (¡SIN ESPACIOS A LA IZQUIERDA!) ---
CATALOGOS = cargar_catalogos_maestros()

# --- 4. VARIABLES EXPORTADAS PARA APP.PY ---
UNIDADES_REF = CATALOGOS.get("unidades_medida", [])
CUSTODIOS = CATALOGOS.get("custodios_por_tipo", {})
NOMBRES_MATERIALES = CATALOGOS.get("mapeo_nombres_material", {})
DOMINIOS_CONFIG = CATALOGOS.get("dominios_config", {}) 

# --- 5. CONFIGURACIÓN DEL MODELO DE IA ---
def obtener_modelo_agente() -> str:
    """Retorna el nombre oficial y estable del modelo de Google Gemini."""
    return "gemini-1.5-pro" 

def configurar_api_ia():
    """Inicializa la llave de Gemini leyendo desde secrets.toml de Streamlit."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ ADVERTENCIA: No se encontró la GEMINI_API_KEY en .streamlit/secrets.toml.")
            return False
            
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configurando la API de Gemini: {e}")
        return False

# Ejecutamos la configuración automáticamente
configurar_api_ia()