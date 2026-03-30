"""
Configuración global de T.A.L.O.N.
Manejo de variables de entorno, constantes de negocio y configuración de la IA.
"""
import os
import streamlit as st
import google.generativeai as genai

# ==========================================
# 🤖 CONFIGURACIÓN DEL MODELO DE IA
# ==========================================
def obtener_modelo_agente() -> str:
    """
    Retorna el nombre oficial y estable del modelo de Google Gemini.
    Evitamos usar sufijos '-latest' para prevenir errores 404 cuando Google actualiza sus servidores.
    """
    # Modelo principal sugerido para análisis complejos de datos:
    return "gemini-1.5-pro" 
    
    # Nota: Si en el futuro quieres que el perfilamiento sea mucho más rápido (aunque un poco menos analítico), 
    # puedes cambiar la línea de arriba por: return "gemini-1.5-flash"

def configurar_api_ia():
    """Inicializa la llave de Gemini leyendo desde secrets.toml o variables de entorno."""
    try:
        # 1. Intenta leer de secrets.toml (Estándar de Streamlit)
        api_key = st.secrets.get("GEMINI_API_KEY")
        
        # 2. Si no está en secrets, busca en las variables de entorno locales (.env)
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
            
        if not api_key:
            print("⚠️ ADVERTENCIA: No se encontró la GEMINI_API_KEY. La IA no funcionará.")
            return False
            
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configurando la API de Gemini: {e}")
        return False

# Ejecutamos la configuración automáticamente al importar este archivo en app.py
configurar_api_ia()


# ==========================================
# ⚙️ CONSTANTES DE NEGOCIO Y DOMINIOS (SAP)
# ==========================================

# Catálogo de unidades de medida permitidas para la regla de Validez
UNIDADES_REF = [
    "UN", "M", "KG", "G", "L", "ML", "CJ", "PZ", 
    "CM", "MM", "M2", "M3", "GAL", "TON", "MG", "LB", "OZ"
]

# Configuración de los dominios de datos que maneja la aplicación
DOMINIOS_CONFIG = {
    "Maestro de Materiales": {
        "descripcion": "Gestión de artículos, productos terminados, insumos y repuestos (MARA/MARC).",
        "focos_principales": ["ZFER", "ZROH", "ZERS", "ZVER", "ZHAW", "ZIUC", "ZSER", "ZHAL"]
    },
    "Directorio Comercial": {
        "descripcion": "Gestión de datos maestros de Clientes (KNA1) y Proveedores (LFA1).",
        "focos_principales": ["Clientes", "Proveedores"]
    }
}