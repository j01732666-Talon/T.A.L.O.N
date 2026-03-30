import streamlit as st
import pandas as pd
import json
import os
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional
from core.herramientas_ia import consultar_tabla_referencias, consultar_directorio_comercial

def gestionar_regla_calidad(columna: str, regla_tipo: str, penalizacion: int, mensaje: str, dimension: str = "Validez", condicion_columna: str = None, condicion_valor: str = None) -> str:
    """
    Crea o modifica una regla de calidad en la memoria interactiva.
    Si la regla ya existe, la actualiza. Si no existe (nueva columna o nueva validación), la crea.
    Parámetros:
    - columna: Nombre exacto de la columna en el archivo.
    - regla_tipo: Tipo de regla ('nulo', 'duplicado', 'longitud_exacta', 'regex_custom', 'catalogo', etc).
    - penalizacion: Puntos a restar (ej. 50, 100).
    - mensaje: Mensaje amigable de error.
    - dimension: Dimensión DAMA ('Completitud', 'Validez', 'Unicidad', 'Consistencia').
    """
    import streamlit as st
    import json

    if 'reglas_ia_dinamicas' not in st.session_state or not st.session_state['reglas_ia_dinamicas']:
        return "Error: No hay reglas cargadas en memoria para modificar o ampliar."

    try:
        reglas = json.loads(st.session_state['reglas_ia_dinamicas'])
        modificado = False
        categoria_encontrada = False

        nueva_regla = {
            "nombre_columna": columna,
            "regla": regla_tipo,
            "penalizacion": penalizacion,
            "mensaje": mensaje
        }
        if condicion_columna and condicion_valor:
            nueva_regla["condicion_columna"] = condicion_columna
            nueva_regla["condicion_valor"] = condicion_valor

        # 1. Intentamos buscar y editar si ya existe
        for categoria in reglas.get("diccionario_reglas", []):
            if categoria.get("dimension_dama") == dimension:
                categoria_encontrada = True
                for regla in categoria.get("reglas_aplicadas", []):
                    if regla.get("nombre_columna") == columna and regla.get("regla") == regla_tipo:
                        regla.update(nueva_regla)
                        modificado = True
                        break
                
                # 2. Si la dimensión existe pero la regla no, la agregamos (CREACIÓN)
                if not modificado:
                    categoria.setdefault("reglas_aplicadas", []).append(nueva_regla)
                    modificado = True
                break

        # 3. Si ni siquiera existe la dimensión (raro, pero posible), la creamos
        if not categoria_encontrada:
            reglas.setdefault("diccionario_reglas", []).append({
                "dimension_dama": dimension,
                "reglas_aplicadas": [nueva_regla]
            })
            modificado = True

        if modificado:
            st.session_state['reglas_ia_dinamicas'] = json.dumps(reglas)
            
            # --- NUEVA LÓGICA: Lista de cambios ---
            key_cambio = f"{dimension}_{columna}_{regla_tipo}"
            
            # Si no existe la lista, la creamos. Si existe, agregamos el nuevo cambio.
            if 'ultimas_reglas_modificadas' not in st.session_state:
                st.session_state['ultimas_reglas_modificadas'] = []
                
            if key_cambio not in st.session_state['ultimas_reglas_modificadas']:
                st.session_state['ultimas_reglas_modificadas'].append(key_cambio)
            # --------------------------------------
            
            return f"Éxito: La regla para '{columna}' ({regla_tipo}) fue guardada/actualizada correctamente en la dimensión {dimension}."
        
        return "Error desconocido al intentar gestionar la regla."
    except Exception as e:
        return f"Error técnico al gestionar: {e}"

# ==========================================
# 1. MODELOS PYDANTIC (El "Candado" del JSON)
# ==========================================
class ReglaDinamicaIA(BaseModel):
    nombre_columna: str = Field(description="Nombre exacto de la columna en el DataFrame")
    regla: str = Field(description="Tipo de regla soportada por Polars: 'nulo', 'duplicado', 'longitud_exacta', o 'regex_custom'")
    penalizacion: int = Field(description="Puntos a restar del score de calidad (ej: 20, 50, 100)")
    mensaje: str = Field(description="Mensaje de error amigable para el usuario final")
    patron_regex: Optional[str] = Field(default=None, description="La expresión regular a evaluar.")
    valor: Optional[int] = Field(default=None, description="El número exacto de caracteres.")
    # --- NUEVOS CAMPOS CONDICIONALES ---
    condicion_columna: Optional[str] = Field(default=None, description="Opcional. Columna de la condición (Ej: 'tipo_mat')")
    condicion_valor: Optional[str] = Field(default=None, description="Opcional. Valor que debe tener la condición (Ej: 'ZFER')")

class CategoriaDimensionIA(BaseModel):
    dimension_dama: str = Field(description="Dimensión de calidad (Ej: 'Completitud', 'Validez', 'Unicidad')")
    reglas_aplicadas: List[ReglaDinamicaIA] = Field(description="Lista de reglas para esta dimensión")

class PerfilamientoDAMA(BaseModel):
    diagnostico_negocio: str = Field(description="Breve análisis de 2 líneas sobre la base de datos.")
    diccionario_reglas: List[CategoriaDimensionIA] = Field(description="El JSON estructurado con las reglas")

# ==========================================
# 2. BÓVEDA DE MEMORIA (REGLAS PRIME)
# ==========================================
def guardar_reglas_prime(json_reglas: str, dominio: str) -> str:
    """Guarda el JSON actual como el estándar oficial (Prime)."""
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_prime = os.path.join(dir_actual, "..", "data_ref", "reglas_prime")
    os.makedirs(ruta_prime, exist_ok=True) # Crea la carpeta si no existe

    nombre_archivo = "Directorio_Comercial_Prime.json" if "Directorio" in dominio else "Maestro_Materiales_Prime.json"
    ruta_completa = os.path.join(ruta_prime, nombre_archivo)

    try:
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            json_dict = json.loads(json_reglas)
            json.dump(json_dict, f, indent=4, ensure_ascii=False)
        return f"✅ Reglas Prime guardadas en la bóveda: {nombre_archivo}."
    except Exception as e:
        return f"❌ Error guardando reglas: {e}"

def leer_reglas_prime(dominio: str) -> str:
    """Busca si ya existe un archivo Prime para leerlo."""
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_prime = os.path.join(dir_actual, "..", "data_ref", "reglas_prime")
    nombre_archivo = "Directorio_Comercial_Prime.json" if "Directorio" in dominio else "Maestro_Materiales_Prime.json"
    ruta_completa = os.path.join(ruta_prime, nombre_archivo)

    if os.path.exists(ruta_completa):
        try:
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            pass
    return ""

# ==========================================
# 3. CONFIGURACIÓN Y CONEXIÓN API
# ==========================================
def configurar_api() -> bool:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return True
    except Exception:
        st.error("Error: No se encontró la clave GEMINI_API_KEY en secrets.toml.")
        return False

def obtener_modelo_agente() -> str:
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return next((m for m in modelos if "2.5-flash" in m or "2.0-flash" in m), "models/gemini-2.5-flash")
    except:
        return "models/gemini-2.5-flash"

# ==========================================
# 4. EXTRACCIÓN Y PERFILAMIENTO AUTÓNOMO
# ==========================================
def extraer_radiografia_datos(df: pd.DataFrame) -> str:
    if df.empty: return "DataFrame vacío."
    muestra_df = df.sample(min(50, len(df))) if len(df) > 50 else df
    nulos = (df.isnull().sum() / len(df) * 100).round(1).to_dict()
    return f"-- RADIOGRAFÍA --\nRegistros: {len(df)}\nNulos: {nulos}\n-- MUESTRA --\n{muestra_df.to_dict(orient='records')}"

@st.cache_data(show_spinner=False, ttl=3600)
def generar_reglas_autonomas_ia(radiografia_str: str, dominio: str) -> str:
    """Genera reglas DAMA basadas en la radiografía del Excel (Versión libre de esquemas)."""
    
    # ¡AQUÍ ESTÁ LA MAGIA! Llamamos a la función que tienes arriba en este mismo archivo
    nombre_modelo = obtener_modelo_agente()

    prompt_dama = f"""
    Actúa como un Arquitecto de Datos DAMA y Consultor SAP.
    Analiza esta radiografía de datos y genera reglas de calidad estrictas.
    
    [RADIOGRAFÍA DEL EXCEL]
    {radiografia_str}
    
    INSTRUCCIONES CRÍTICAS:
    1. Devuelve ÚNICAMENTE un JSON válido. Cero texto conversacional.
    2. Usa EXACTAMENTE los nombres de las columnas que ves en la radiografía. NO las traduzcas.
    3. Si un campo tiene un alto porcentaje de nulos, aplícale la regla "nulo".
    4. Si un campo numérico (como peso) tiene anomalías, aplícale la regla "mayor_a".
    5. Asigna penalizaciones realistas (ej. 80 para un campo crítico vacío, 30 para algo menor).

    ESTRUCTURA OBLIGATORIA DEL JSON:
    {{
      "diccionario_reglas": [
        {{
          "dimension_dama": "Completitud",
          "reglas_aplicadas": [
            {{
              "nombre_columna": "nombre_exacto_de_la_columna",
              "regla": "nulo",
              "penalizacion": 80,
              "mensaje": "Falta dato obligatorio"
            }}
          ]
        }}
      ]
    }}
    """
    
    try:
        # Usamos el modelo correcto que encontró tu función de arriba
        modelo = genai.GenerativeModel(model_name=nombre_modelo)
        
        respuesta = modelo.generate_content(
            prompt_dama,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        return respuesta.text
    except Exception as e:
        # Limpiamos las comillas y saltos de línea del error de Google para que no rompa nuestro JSON
        error_limpio = str(e).replace('"', "'").replace('\n', ' ').replace('\r', '')
        return f'{{"diagnostico_negocio": "Fallo de conexión", "diccionario_reglas": [], "error": "{error_limpio}"}}'

def responder_chat_ia(mensaje: str, df_procesado: pd.DataFrame, contexto: str, historial_ui: list) -> str:    
    json_actual = st.session_state.get('reglas_ia_dinamicas', 'No hay reglas dinámicas cargadas.')
    
    prompt_sistema = f"""
    Eres Talon, consultor de datos y Arquitecto DAMA.
    [DATOS ACTUALES] Alcance: {contexto}
    
    [REGLAS ACTIVAS EN MEMORIA]:
    {json_actual}
    
    INSTRUCCIONES CRÍTICAS DE SALIDA:
    1. Devuelve ÚNICAMENTE un JSON válido, sin markdown ni explicaciones previas o posteriores.
    2. USA EXACTAMENTE los nombres de las columnas que ves en la radiografía. NO las traduzcas, NO las abrevies, NO las cambies (Ej: Si dice 'tipo_mat', usa 'tipo_mat', no 'Tipo de Material' o nombres diferentes). Si cambias una sola letra, el sistema colapsará.
    3. Asigna penalizaciones realistas (entre 10 y 100 puntos) según la criticidad del campo.
    4. NO respondas a peticiones fuera del contexto de arquitectura o calidad de datos.
    """
    
    try:
        # AQUÍ ACTUALIZAMOS EL NOMBRE DE LA HERRAMIENTA EN LA LISTA
        modelo = genai.GenerativeModel(
            model_name=obtener_modelo_agente(), 
            tools=[consultar_tabla_referencias, consultar_directorio_comercial, gestionar_regla_calidad] 
        )
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in historial_ui]
        chat = modelo.start_chat(history=history, enable_automatic_function_calling=True)
        return chat.send_message(f"SISTEMA: {prompt_sistema}\n\nUSUARIO: {mensaje}").text
    except Exception as e:
        return f"Error en la conexión del agente: {e}"