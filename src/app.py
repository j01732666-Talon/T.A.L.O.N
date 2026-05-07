import streamlit as st
import requests
import json
import urllib.parse

# 1. ÚNICA CONFIGURACIÓN
st.set_page_config(page_title="T.A.L.O.N — Brinsa", layout="wide")

# 2. LEER CREDENCIALES MANUALMENTE
try:
    with open("credenciales_sso.json", "r") as f:
        datos_json = json.load(f)
        # Esto lee el archivo sea tipo Web o tipo Escritorio
        creds = datos_json.get("web", datos_json.get("installed", {}))
        CLIENT_ID = creds.get("client_id")
        CLIENT_SECRET = creds.get("client_secret")
        REDIRECT_URI = "http://localhost:8501"
except Exception as e:
    st.error("No se encontró el archivo credenciales_sso.json o está mal configurado.")
    st.stop()

# 3. EL PORTERO (Totalmente independiente de la memoria)
if not st.session_state.get("connected"):
    st.markdown("<h1 style='text-align: center;'>🦅 T.A.L.O.N.</h1>", unsafe_allow_html=True)
    
    params = st.query_params.to_dict()
    
    # --- A. PROCESAR EL REGRESO DE GOOGLE ---
    if "code" in params:
        codigo = params["code"]
        
        # Evitar que Streamlit procese el código dos veces por error
        if st.session_state.get("codigo_procesado") == codigo:
            st.query_params.clear()
        else:
            try:
                st.session_state["codigo_procesado"] = codigo
                
                # 🔥 LA MAGIA: Canjeamos el código manualmente (SIN PKCE / Sin Verifier)
                # Como lo hacemos así, Google no nos pedirá el 'code verifier' que Streamlit olvida
                token_url = "https://oauth2.googleapis.com/token"
                payload = {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code": codigo,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI
                }
                
                respuesta_token = requests.post(token_url, data=payload)
                datos_token = respuesta_token.json()
                
                if "access_token" in datos_token:
                    # Traer los datos del usuario usando el Token
                    user_info = requests.get(
                        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                        headers={"Authorization": f"Bearer {datos_token['access_token']}"}
                    ).json()
                    
                    # ¡Todo exitoso! Guardamos y abrimos la puerta
                    st.session_state.user_info = user_info
                    st.session_state.connected = True
                    
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error("Google rechazó el acceso (Posiblemente el código expiró).")
                    if st.button("Intentar de nuevo"):
                        st.query_params.clear()
                        st.rerun()
                        
            except Exception as e:
                st.error("Error técnico conectando con Google.")
                st.code(str(e))
                if st.button("Limpiar y reintentar"):
                    st.query_params.clear()
                    st.rerun()
                    
    # --- B. PANTALLA DE BOTÓN DE LOGIN ---
    else:
        st.info("Inicia sesión con tu cuenta corporativa para acceder al sistema.")
        
        # Construimos la URL nosotros mismos. 
        # Al no incluir un 'code_challenge', Google JAMÁS nos pedirá el 'code_verifier'.
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile&"
            f"prompt=consent"
        )
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.link_button("Ingresar con Google SSO", auth_url, use_container_width=True)
            
    st.stop()

# 4. AMBIENTE DASHBOARD
else:
    try:
        from Dashboard import mostrar_panel_principal
        st.session_state['usuario_actual'] = st.session_state.user_info.get('email', 'Usuario SSO')
        mostrar_panel_principal()
    except Exception as e:
        st.error(f"Error al conectar con el motor de TALON: {e}")