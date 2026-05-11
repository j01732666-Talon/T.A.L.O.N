import streamlit as st
import os
from streamlit_google_auth import Authenticate

def obtener_config_auth():
    """
    Gestiona dinámicamente la URL de redirección dependiendo de si estamos 
    en local o en GCP.
    """
    # Usaremos una variable de entorno llamada 'ENTORNO'. 
    # En tu local no existirá (será 'local'), pero en GCP la configuraremos como 'produccion'
    entorno = os.getenv("ENTORNO", "local")
    
    # ⚠️ REEMPLAZA ESTA URL por la que te entregue GCP (Cloud Run / App Engine)
    # Debe llevar el "https://" y la barra "/" al final
    URL_PRODUCCION_GCP = "https://tu-servicio-cloud-run-uc.a.run.app/"
    
    URL_LOCAL = "http://localhost:8501/"
    
    # Asignamos la URL dependiendo de dónde esté corriendo el código
    URL_REDIRECCION = URL_PRODUCCION_GCP if entorno == "produccion" else URL_LOCAL
    
    config = {
        "ruta_json": "credenciales_sso.json",
        "cookie_name": "talon_sso_session",
        "cookie_key": "talon_brinsa_2024_secret",
        "redirect_uri": URL_REDIRECCION
    }
    return config

def inicializar_autenticador():
    """
    Crea la instancia del autenticador usando la configuración centralizada.
    """
    cfg = obtener_config_auth()
    
    if not os.path.exists(cfg["ruta_json"]):
        st.error(f"⚠️ Archivo {cfg['ruta_json']} no encontrado.")
        st.stop()
        
    return Authenticate(
        secret_credentials_path=cfg["ruta_json"],
        cookie_name=cfg["cookie_name"],
        cookie_key=cfg["cookie_key"],
        redirect_uri=cfg["redirect_uri"]
    )

def gestionar_almacenamiento_usuario():
    """
    Maneja el Session State de Streamlit.
    Sincroniza los datos de Google con las variables que tu app ya usa.
    """
    if st.session_state.get("connected"):
        user_info = st.session_state.get("user_info", {})
        
        # Inyectamos los datos en las variables que usan tus demás módulos
        st.session_state['usuario_actual'] = user_info.get("email", "Usuario Desconocido")
        st.session_state['nombre_usuario'] = user_info.get("name", "Auditor")