import streamlit as st
import requests
import json
import base64
import os
import urllib.parse
from ui.theme import inject_login_css

# ── Logos (cargados una vez al arrancar) ──────────────────────────
_BRINSA_B64 = ""
try:
    _logo_path = os.path.join(os.path.dirname(__file__), "ui", "brinsa_logo.png")
    with open(_logo_path, "rb") as _f:
        _BRINSA_B64 = base64.b64encode(_f.read()).decode()
except Exception:
    pass

# SVG del cuervo codificado en base64 para usar como <img src="data:...">
# (st.markdown sanitiza <svg> inline pero respeta <img> con data URIs)
_CROW_SVG_B64 = ""
try:
    _crow_path = os.path.join(os.path.dirname(__file__), "ui", "crow_logo.svg")
    with open(_crow_path, "rb") as _f:
        _CROW_SVG_B64 = base64.b64encode(_f.read()).decode()
except Exception:
    pass

# ══════════════════════════════════════════════════════════
#  1. CONFIGURACIÓN ÚNICA DE PÁGINA
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="T.A.L.O.N — Brinsa",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════
#  2. LEER CREDENCIALES SSO
# ══════════════════════════════════════════════════════════
try:
    with open("credenciales_sso.json", "r") as f:
        datos_json = json.load(f)
        creds = datos_json.get("web", datos_json.get("installed", {}))
        CLIENT_ID     = creds.get("client_id")
        CLIENT_SECRET = creds.get("client_secret")
        REDIRECT_URI  = "http://localhost:8501"
except Exception:
    st.error("No se encontró el archivo credenciales_sso.json o está mal configurado.")
    st.stop()

# ══════════════════════════════════════════════════════════
#  3. PORTERO — maneja login y sesión
# ══════════════════════════════════════════════════════════
if not st.session_state.get("connected"):
    

    # ── CSS GLOBAL DE LOGIN ──────────────────────────────
    inject_login_css()

    # ── JAVASCRIPT: POPUP SSO ────────────────────────────
    # Cuando el popup regresa con ?code=..., lo detecta y se lo pasa
    # a la ventana padre sin abrir una nueva pestaña.
    st.markdown("""
    <script>
    (function() {
        var params = new URLSearchParams(window.location.search);
        var code   = params.get('code');
        var state  = params.get('state');

        // ► Estamos DENTRO del popup y Google nos devolvió el código
        if (window.opener && code) {
            try {
                window.opener.postMessage(
                    { type: 'talon_oauth_code', code: code },
                    window.location.origin
                );
            } catch(e) { console.error('postMessage error:', e); }
            // Mostrar mensaje de cierre y cerrar el popup
            document.body.innerHTML =
                '<div style="background:#070B12;color:#94A3B8;font-family:IBM Plex Mono,monospace;' +
                'font-size:13px;display:flex;align-items:center;justify-content:center;height:100vh;">' +
                'Autenticación completada. Cerrando...</div>';
            setTimeout(function() { window.close(); }, 800);
            return;
        }

        // ► Estamos en la ventana PRINCIPAL — escuchamos el código del popup
        window.addEventListener('message', function(evt) {
            if (evt.origin !== window.location.origin) return;
            if (evt.data && evt.data.type === 'talon_oauth_code' && evt.data.code) {
                window.location.href = '/?code=' + encodeURIComponent(evt.data.code);
            }
        }, false);
    })();
    </script>
    """, unsafe_allow_html=True)

    params = st.query_params.to_dict()

    # ── A. PROCESAR EL CÓDIGO DE RETORNO DE GOOGLE ──────
    if "code" in params:
        codigo = params["code"]

        if st.session_state.get("codigo_procesado") == codigo:
            st.query_params.clear()
        else:
            st.markdown("""
            <div style="display:flex;align-items:center;justify-content:center;
                        height:100vh;background:#070B12;flex-direction:column;gap:16px;">
              <div style="width:32px;height:32px;border:3px solid #1F2937;
                          border-top-color:#3B82F6;border-radius:50%;
                          animation:spin .8s linear infinite;"></div>
              <p style="font-family:'IBM Plex Mono',monospace;font-size:12px;
                        color:#475569;letter-spacing:1px;">VERIFICANDO IDENTIDAD…</p>
            </div>
            """, unsafe_allow_html=True)

            try:
                st.session_state["codigo_procesado"] = codigo
                respuesta_token = requests.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id":     CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "code":          codigo,
                        "grant_type":    "authorization_code",
                        "redirect_uri":  REDIRECT_URI,
                    },
                )
                datos_token = respuesta_token.json()

                if "access_token" in datos_token:
                    user_info = requests.get(
                        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                        headers={"Authorization": f"Bearer {datos_token['access_token']}"},
                    ).json()
                    st.session_state.user_info = user_info
                    st.session_state.connected = True
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.query_params.clear()
                    st.error("Google rechazó el acceso. El código expiró o ya fue usado.")
                    if st.button("Reintentar"):
                        st.rerun()

            except Exception as e:
                st.query_params.clear()
                st.error("Error técnico al conectar con Google.")
                st.code(str(e))
                if st.button("Limpiar y reintentar"):
                    st.rerun()

# ── B. PANTALLA DE LOGIN ─────────────────────────────
    # ── B. PANTALLA DE LOGIN ─────────────────────────────
    else:
        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
            "response_type=code&"
            "scope=openid%20email%20profile&"
            "prompt=consent&"
            "access_type=offline"
        )

        html_login = f"""
<!-- ── Fondo animado (grid + scan beam + partículas) ── -->
<div class="talon-bg-animated"></div>
<div class="talon-scan-beam"></div>
<div class="talon-dot-1"></div>
<div class="talon-dot-2"></div>
<div class="talon-dot-3"></div>
<div class="talon-dot-4"></div>
<div class="talon-dot-5"></div>
<div class="talon-dot-6"></div>

<!-- ── Tarjeta principal centrada ── -->
<div style="position:fixed;inset:0;display:flex;align-items:center;justify-content:center;z-index:10;padding:20px;">
<div class="talon-card-login">

  <!-- Brackets decorativos de esquina -->
  <div class="corner-tl"></div>
  <div class="corner-tr"></div>
  <div class="corner-bl"></div>
  <div class="corner-br"></div>

  <!-- ── Logo Cuervo (img data URI — evita sanitizador de Streamlit) ── -->
  <div class="talon-raven-wrap">
    {"<img src='data:image/svg+xml;base64," + _CROW_SVG_B64 + "' alt='T.A.L.O.N crow' style='width:60px;height:auto;filter:drop-shadow(0 0 8px rgba(59,130,246,0.6));'/>" if _CROW_SVG_B64 else "<span style='font-size:32px;'>🦅</span>"}
  </div>

  <!-- ── Título con efecto glitch ── -->
  <div class="talon-glitch" data-text="T.A.L.O.N">T.A.L.O.N</div>

  <!-- Subtítulo -->
  <p style="font-family:'IBM Plex Sans',sans-serif;font-size:11px;color:#475569;
            text-align:center;margin:0;letter-spacing:.6px;line-height:1.5;">
    Tablero Analítico de Limpieza y Orquestación de Negocios
  </p>

  <!-- Divisor animado -->
  <div class="talon-divider"></div>

  <!-- Mensaje de acceso -->
  <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13px;color:#94A3B8;
            text-align:center;margin:0 0 24px;line-height:1.7;">
    Accede con tu cuenta corporativa<br>
    <span style="color:#475569;font-size:11px;letter-spacing:.3px;">@brinsa.com.co</span>
  </p>

  <!-- Botón Google SSO -->
  <a href="{auth_url}" target="_self" class="btn-talon-login">
    <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
    Ingresar con Google SSO
  </a>

  <!-- Nota de seguridad -->
  <p style="font-family:'IBM Plex Sans',sans-serif;font-size:10px;color:#2D3A4F;
            text-align:center;margin:18px 0 0;display:flex;align-items:center;
            justify-content:center;gap:5px;letter-spacing:.4px;">
    <svg width="10" height="10" viewBox="0 0 16 16" fill="#2D3A4F">
      <path d="M8 1a3.5 3.5 0 0 0-3.5 3.5v1A1.5 1.5 0 0 0 3 7v6a1.5 1.5 0 0 0 1.5 1.5h7A1.5 1.5 0 0 0 13 13V7a1.5 1.5 0 0 0-1.5-1.5v-1A3.5 3.5 0 0 0 8 1zm0 1.5A2 2 0 0 1 10 4.5v1H6v-1A2 2 0 0 1 8 2.5z"/>
    </svg>
    Autenticación segura vía OAuth 2.0
  </p>

  <!-- Logo Brinsa -->
  <div style="margin-top:22px;padding-top:18px;border-top:1px solid #1F2937;
              text-align:center;">
    <p style="font-family:'IBM Plex Mono',monospace;font-size:9px;color:#2D3A4F;
              margin:0 0 10px;letter-spacing:1.5px;text-transform:uppercase;">
      Desarrollado para
    </p>
    {"<img src='data:image/png;base64," + _BRINSA_B64 + "' alt='Brinsa' style='height:26px;mix-blend-mode:screen;opacity:0.75;'/>" if _BRINSA_B64 else "<span style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#3B82F6;letter-spacing:2px;'>BRINSA</span>"}
  </div>

</div>
</div>
"""
        st.markdown(html_login, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════
#  4. DASHBOARD (sesión activa)
# ══════════════════════════════════════════════════════════
else:
    try:
        from Dashboard import mostrar_panel_principal
        st.session_state['usuario_actual'] = st.session_state.user_info.get('email', 'Usuario SSO')
        mostrar_panel_principal()
    except Exception as e:
        st.error(f"Error al conectar con el motor de TALON: {e}")