"""
Motor de IA para T.A.L.O.N.
Responsable del perfilamiento autónomo y la asistencia conversacional.
Totalmente desacoplado de Streamlit.
"""
import json
import re
import os
import google.generativeai as genai
import pandas as pd
from typing import Optional
from config import obtener_modelo_agente, configurar_api_ia


def _manejar_error_ia(exc: Exception) -> str:
    """
    Convierte cualquier excepción de la API de Gemini en un mensaje limpio
    para el usuario. Detecta cuota excedida (429) y errores de red.
    """
    msg = str(exc)
    if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
        retry_match = re.search(r'retry.*?(\d+)\s*s', msg, re.IGNORECASE)
        retry_info = f" Intenta de nuevo en {retry_match.group(1)} segundos." if retry_match else ""
        return (
            "**Límite de API alcanzado.**\n\n"
            "La cuota gratuita de Gemini para esta sesión se ha agotado. "
            "Esto es un límite del proveedor de IA (Google), no un error de la aplicación.\n\n"
            "**¿Qué hacer?**\n"
            "- Espera unos minutos y vuelve a intentarlo.\n"
            "- O actualiza tu plan en [Google AI Studio](https://aistudio.google.com)."
            + (f"\n\n_{retry_info.strip()}_" if retry_info else "")
        )
    if "leaked" in msg.lower() or ("403" in msg and "api key" in msg.lower()):
        return (
            "**API Key bloqueada por Google.**\n\n"
            "La clave de Gemini fue reportada como filtrada y Google la ha desactivado. "
            "La IA no funcionará hasta que se reemplace.\n\n"
            "**Solución:**\n"
            "1. Ve a [aistudio.google.com](https://aistudio.google.com) → **Get API key** → crea una nueva clave.\n"
            "2. Abre el archivo `.streamlit/secrets.toml` en el proyecto.\n"
            "3. Reemplaza el valor de `GEMINI_API_KEY` con la nueva clave.\n"
            "4. Reinicia la aplicación."
        )
    if "403" in msg or "permission" in msg.lower() or "unauthorized" in msg.lower():
        return (
            "**Sin autorización con la API de Gemini.**\n\n"
            "La clave de API no tiene permisos para usar este modelo. "
            "Verifica que la `GEMINI_API_KEY` en `.streamlit/secrets.toml` sea válida."
        )
    if any(k in msg.lower() for k in ("connection", "timeout", "network", "ssl")):
        return (
            "**Sin conexión con la IA.**\n\n"
            "No se pudo comunicar con el servidor de Gemini. "
            "Verifica tu conexión a internet e inténtalo de nuevo."
        )
    # Error genérico — mostrar solo la primera línea, no el JSON completo
    first_line = msg.split("\n")[0][:200]
    return f"**Error de IA:** {first_line}"

def leer_reglas_prime(dominio: str) -> Optional[str]:
    """Lee las reglas del dominio activo desde reglas_cde.json.
    guardar_reglas_prime() escribe en ese archivo (no en un _Prime.json independiente),
    por lo que esta función debe leer el mismo fichero maestro.
    """
    _dir_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(_dir_src, "data_ref", "reglas_cde.json")
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                todas = json.load(f)
            target_key = "Directorio_Comercial" if "Directorio" in dominio else "DEFAULT"
            bloque = todas.get(target_key)
            return json.dumps(bloque, ensure_ascii=False, indent=2) if bloque else None
        except Exception as e:
            print(f"Error leyendo reglas desde {ruta}: {e}")
    return None

def guardar_reglas_prime(nuevas_reglas, dominio):
    try:
        # 1. BLINDAJE: Verificamos si ya es un diccionario o si hay que convertirlo
        if isinstance(nuevas_reglas, dict):
            reglas_nuevas_dict = nuevas_reglas
        else:
            reglas_nuevas_dict = json.loads(nuevas_reglas)

        # 2. Rutas del archivo maestro
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        dir_src = os.path.dirname(dir_actual)
        ruta_json = os.path.join(dir_src, "data_ref", "reglas_cde.json")
        
        if not os.path.exists(ruta_json):
            # Fallback a la raíz si no está en src
            dir_raiz = os.path.dirname(dir_src)
            ruta_json = os.path.join(dir_raiz, "data_ref", "reglas_cde.json")

        # 3. Leer las reglas actuales
        reglas_maestras = {}
        if os.path.exists(ruta_json):
            with open(ruta_json, 'r', encoding='utf-8') as f:
                try:
                    reglas_maestras = json.load(f)
                except json.JSONDecodeError:
                    reglas_maestras = {}

        # 4. Mezclar las reglas de la IA con las maestras (Actualizar el dominio)
        target_key = "Directorio_Comercial" if "Directorio" in str(dominio) else "DEFAULT"
        
        # Si la IA nos dio el formato con la llave target_key, lo extraemos
        if target_key in reglas_nuevas_dict:
            reglas_maestras[target_key] = reglas_nuevas_dict[target_key]
        else:
            # Si no, lo asignamos directamente
            reglas_maestras[target_key] = reglas_nuevas_dict

        # 5. Guardar el archivo sobrescrito
        os.makedirs(os.path.dirname(ruta_json), exist_ok=True) # Crear carpeta si no existe
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(reglas_maestras, f, indent=4, ensure_ascii=False)
            
        return "✅ Reglas Prime guardadas exitosamente en el archivo maestro."

    except Exception as e:
        return f"❌ Error guardando reglas: {str(e)}"
    
def extraer_radiografia_datos(df: pd.DataFrame) -> str:
    """Extrae un resumen estadístico y de metadatos del DataFrame para que la IA lo entienda."""
    if df.empty:
        return "El conjunto de datos está vacío."
    
    # Tomamos una muestra y el describe() para no saturar los tokens de Gemini
    resumen = df.describe(include='all').to_string()
    tipos = df.dtypes.to_string()
    
    radiografia = f"--- TIPOS DE DATOS ---\n{tipos}\n\n--- RESUMEN ESTADÍSTICO ---\n{resumen}"
    return radiografia

def generar_reglas_autonomas_ia(datos_crudos: pd.DataFrame, dominio: str) -> str:
    """
    IA Auditora: Razona sobre la radiografía y el historial Prime para crear reglas.
    """
    radiografia = extraer_radiografia_datos(datos_crudos)
    reglas_previas = leer_reglas_prime(dominio)
    
    contexto_previo = (
        f"\n\nReglas Prime previas para este dominio (úsalas como referencia):\n{reglas_previas}"
        if reglas_previas else ""
    )

    prompt = f"""
    Actúa como un Arquitecto de Datos Maestro (DAMA). 
    Analiza este resumen estadístico de una tabla ({dominio}):
    {radiografia}{contexto_previo}
    
    Genera un diccionario de reglas de calidad en formato JSON ESTRICTO para limpiar estos datos. 
    DEBES usar exactamente esta estructura y no agregar nada más:
    ...
    {{
      "diccionario_reglas": [
        {{
          "dimension_dama": "Completitud",
          "reglas_aplicadas": [
            {{
              "nombre_columna": "nombre_de_la_columna_aqui",
              "regla": "nulo",
              "penalizacion": 100,
              "mensaje": "Falta información vital"
            }}
          ]
        }},
        {{
          "dimension_dama": "Unicidad",
          "reglas_aplicadas": [
            {{
              "nombre_columna": "nombre_de_columna_clave",
              "regla": "duplicado_multicampo",
              "penalizacion": 100,
              "mensaje": "Registro duplicado detectado"
            }}
          ]
        }}
      ]
    }}

    IMPORTANTE: 
    - En el campo "regla", SOLO puedes usar estos comandos de motor: "nulo", "duplicado_multicampo", "mayor_a", "catalogo", "longitud_exacta", "mayor_o_igual_columna". No inventes otras palabras.
    - Agrupa las reglas dentro de "Completitud", "Unicidad", "Validez" y "Consistencia".
    - Devuelve ÚNICAMENTE el JSON, sin texto antes ni después.
"""
    
    try:
        configurar_api_ia()  # Releer la clave desde secrets.toml en cada llamada
        modelo = genai.GenerativeModel(obtener_modelo_agente())
        respuesta = modelo.generate_content(prompt)
        
        # Limpieza quirúrgica de markdown si la IA lo incluye por error
        texto_limpio = respuesta.text.strip()
        match = re.search(r'\{.*\}', texto_limpio, re.DOTALL)
        if match:
            texto_limpio = match.group(0)
            
        return texto_limpio
    except Exception as e:
        return _manejar_error_ia(e)

def responder_chat_ia(mensaje_usuario: str, df_contexto: pd.DataFrame, filtro_str: str, historial_ui: list) -> str:
    """
    Consultor Interactivo: Responde dudas y explica anomalías en lenguaje natural.
    """
    # Formateamos el historial de Streamlit al formato que exige Gemini
    history_gemini = []
    for msg in historial_ui:
        role = "user" if msg["role"] == "user" else "model"
        history_gemini.append({"role": role, "parts": [msg["content"]]})
        
    contexto_datos = df_contexto.to_string()
    
    prompt_sistema = f"""
    Eres Talon, el Asistente Experto en Calidad de Datos SAP.
    Estás analizando la siguiente muestra de registros con anomalías (Filtro: {filtro_str}):
    
    {contexto_datos}
    
    Responde a la duda del usuario de forma concisa, profesional y orientada al negocio.
    Si el usuario pide modificar una regla, indícale cómo hacerlo en el JSON o toma nota mental para la próxima auditoría.
    """
    
    try:
        configurar_api_ia()  # Releer la clave desde secrets.toml en cada llamada
        modelo = genai.GenerativeModel(obtener_modelo_agente())
        chat = modelo.start_chat(history=history_gemini)
        response = chat.send_message(f"{prompt_sistema}\n\nPregunta del usuario: {mensaje_usuario}")
        return response.text
    except Exception as e:
        return _manejar_error_ia(e)