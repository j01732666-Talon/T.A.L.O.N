"""
T.A.L.O.N — Sistema de Diseño Enterprise
Paleta: Grises fríos profundos + Azul como único acento cromático.
Sin arcoíris. Sensación premium y sofisticada.

NOTA DE INYECCIÓN:
Streamlit 1.35+ despojan las etiquetas <style> de st.markdown() y muestran
el texto CSS en el área de contenido. La solución es inyectar estilos vía
JavaScript con st.components.v1.html() (iframe mismo-origen), que sí puede
escribir en window.parent.document.head sin restricciones de sandboxing.
"""

import math as _math
import base64 as _b64
import os as _os

# ── Favicon: SVG del cuervo (cargado una vez al importar el módulo) ──
_CROW_FAVICON_B64 = ""
try:
    _svg_path = _os.path.join(_os.path.dirname(__file__), "crow_logo.svg")
    with open(_svg_path, "rb") as _f:
        _CROW_FAVICON_B64 = _b64.b64encode(_f.read()).decode()
except Exception:
    pass

# ── Fondos ─────────────────────────────────────────────────
BG_DEEP        = "#070B12"   # Fondo máximo (login)
BG_BASE        = "#0D1117"   # Fondo principal de la app
BG_SURFACE     = "#111827"   # Contenedor secundario
BG_ELEVATED    = "#161B22"   # Cards, popovers
BG_OVERLAY     = "#1C2432"   # Hover profundo, dropdowns

# ── Bordes ─────────────────────────────────────────────────
BORDER_SUBTLE  = "#1F2937"
BORDER_DEFAULT = "#2D3A4F"
BORDER_STRONG  = "#3E4C66"

# ── Texto ──────────────────────────────────────────────────
TEXT_HIGH      = "#F1F5F9"
TEXT_DEFAULT   = "#CBD5E1"
TEXT_MUTED     = "#94A3B8"
TEXT_DISABLED  = "#475569"

# ── Acento único (familia azul) ────────────────────────────
ACCENT_PRIMARY = "#3B82F6"
ACCENT_HOVER   = "#60A5FA"
ACCENT_BRIGHT  = "#93C5FD"
ACCENT_DEEP    = "#1D4ED8"
ACCENT_SUBTLE  = "#1E3A5F"

# ── Estados semáforo (escala azul-gris, sin arcoíris) ─────
STATE_HEALTHY  = "#60A5FA"
STATE_WARNING  = "#94A3B8"
STATE_CRITICAL = "#64748B"

# ── Grid ──────────────────────────────────────────────────
COLOR_GRID     = "#1F2937"

# ── Alias de retrocompatibilidad ───────────────────────────
COLOR_BG_ALT      = BG_BASE
COLOR_TEXTO_PRIM  = TEXT_HIGH
COLOR_TEXTO_SEC   = TEXT_MUTED
COLOR_FONDO_CARD  = BG_ELEVATED
COLOR_BORDE       = BORDER_DEFAULT
COLOR_BORDE_HOVER = ACCENT_HOVER
COLOR_ACENTO      = ACCENT_PRIMARY

FONTS_URL = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono"
             ":wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap")


def obtener_color_semaforo(valor: float) -> str:
    """Semáforo en escala azul-gris. Sin arcoíris."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return STATE_CRITICAL
    if _math.isnan(v):
        return STATE_CRITICAL
    if v < 50:
        return STATE_CRITICAL
    elif v < 85:
        return STATE_WARNING
    return STATE_HEALTHY


def get_theme_colors(light_mode: bool = False) -> dict:
    """Devuelve la paleta completa del tema activo.

    Úsala en componentes que construyen estilos inline o Altair charts,
    donde el CSS global no puede llegar (SVG, `configure(background=…)`, etc.).
    """
    if light_mode:
        return {
            'bg_base':        '#F0F4F8',
            'bg_elevated':    '#FFFFFF',
            'bg_overlay':     '#F1F5F9',
            'text_high':      '#0F172A',
            'text_default':   '#1E293B',
            'text_muted':     '#64748B',
            'text_disabled':  '#94A3B8',
            'border_subtle':  '#E2E8F0',
            'border_default': '#CBD5E1',
            'color_grid':     '#E2E8F0',
            'accent':         '#2563EB',
            'state_healthy':  '#2563EB',
        }
    return {
        'bg_base':        BG_BASE,
        'bg_elevated':    BG_ELEVATED,
        'bg_overlay':     BG_OVERLAY,
        'text_high':      TEXT_HIGH,
        'text_default':   TEXT_DEFAULT,
        'text_muted':     TEXT_MUTED,
        'text_disabled':  TEXT_DISABLED,
        'border_subtle':  BORDER_SUBTLE,
        'border_default': BORDER_DEFAULT,
        'color_grid':     COLOR_GRID,
        'accent':         ACCENT_PRIMARY,
        'state_healthy':  STATE_HEALTHY,
    }


# ─────────────────────────────────────────────────────────
#  CONSTRUCTORES DE CSS (devuelven CSS puro, sin etiquetas HTML)
# ─────────────────────────────────────────────────────────

def _build_global_css() -> str:
    """CSS completo del dashboard. Incluye top bar y animaciones dinámicas."""
    return f"""
html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
.stApp {{ background-color: {BG_BASE}; color: {TEXT_DEFAULT}; }}
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* ── Tipografía utilitaria ──────────────────── */
.t-label   {{ font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:600;letter-spacing:1.4px;text-transform:uppercase;color:{TEXT_MUTED}; }}
.t-heading {{ font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:700;color:{TEXT_HIGH};letter-spacing:-0.5px;line-height:1.2; }}
.t-sub     {{ font-family:'IBM Plex Sans',sans-serif;font-size:13px;color:{TEXT_MUTED};line-height:1.5; }}

/* ── Ocultar TODA la barra superior de Streamlit ────────────────
   (Deploy, tres puntos, status widget, decoración)
   El menú de ajustes propio del sidebar reemplaza estas opciones. */
header[data-testid="stHeader"]   {{ display: none !important; }}
[data-testid="stToolbar"]        {{ display: none !important; }}
[data-testid="stDecoration"]     {{ display: none !important; }}
[data-testid="stStatusWidget"]   {{ display: none !important; }}
[data-testid="stMainMenuButton"] {{ display: none !important; }}
.stDeployButton                  {{ display: none !important; }}
#MainMenu                        {{ display: none !important; }}
footer                           {{ display: none !important; }}


/* ── Sidebar ─────────────────────────────────── */
[data-testid="stSidebar"] {{
  background-color: {BG_BASE} !important;
  border-right: 1px solid {BORDER_SUBTLE} !important;
}}
[data-testid="stSidebar"] * {{ color: {TEXT_DEFAULT} !important; }}
[data-testid="stSidebar"] hr {{
  border-color: {BORDER_SUBTLE} !important;
  margin: 10px 0 !important;
}}

/* Eliminar espacio vacío encima del primer elemento del sidebar.
   Streamlit distribuye el espacio en varias capas anidadas;
   hay que neutralizarlas todas. */
[data-testid="stSidebar"] .block-container,
[data-testid="stSidebar"] section {{
  padding-top: 0 !important;
  padding-bottom: 8px !important;
}}
[data-testid="stSidebarContent"]    {{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stSidebarUserContent"]{{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stSidebarHeader"]     {{ min-height: 0 !important; padding: 0 !important; margin: 0 !important; height: 0 !important; overflow: hidden !important; }}
[data-testid="stLogoSpacer"]        {{ display: none !important; }}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0 !important; margin-top: 0 !important; }}
[data-testid="stSidebar"] > div > div:first-child {{ padding-top: 0 !important; }}
[data-testid="stSidebar"] .stMarkdown {{ margin-bottom: 0 !important; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{
  gap: 0 !important;
}}

/* ── Radio buttons (color azul) ──────────────── */
[data-testid="stRadio"] label {{
  padding: 5px 8px !important;
  border-radius: 5px !important;
  transition: background .15s ease, color .15s ease !important;
  cursor: pointer !important;
}}
[data-testid="stRadio"] label:hover {{
  background: {BORDER_SUBTLE} !important;
  color: {ACCENT_HOVER} !important;
}}
/* Dot del radio button → azul */
[data-baseweb="radio"] [role="radio"] div,
[data-baseweb="radio"] [data-checked="true"] > div:first-child,
[data-baseweb="radio"] > div:first-child {{
  border-color: {ACCENT_PRIMARY} !important;
}}
[data-baseweb="radio"] [data-checked="true"] > div:first-child {{
  background-color: {ACCENT_PRIMARY} !important;
  box-shadow: 0 0 6px rgba(59,130,246,0.4) !important;
}}
/* accent-color fallback */
[data-testid="stRadio"] input[type="radio"] {{
  accent-color: {ACCENT_PRIMARY} !important;
}}

/* ── Sidebar: indicador activo izquierdo ─────── */
[data-baseweb="radio"] [data-checked="true"] {{
  background: linear-gradient(90deg, {ACCENT_PRIMARY}18 0%, transparent 100%) !important;
  border-radius: 5px !important;
  animation: sidebarItemIn .2s ease !important;
}}
@keyframes sidebarItemIn {{
  from {{ opacity:.6; transform:translateX(-4px); }}
  to   {{ opacity:1; transform:translateX(0); }}
}}

/* ── Sidebar: botón primario azul ────────────── */
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {{
  background: linear-gradient(135deg, {ACCENT_DEEP} 0%, {ACCENT_PRIMARY} 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: .8px !important;
  box-shadow: 0 0 12px rgba(59,130,246,0.25) !important;
  transition: all .2s ease !important;
  animation: btnGlow 3s ease-in-out infinite !important;
}}
[data-testid="stSidebar"] button[kind="primary"]:hover,
[data-testid="stSidebar"] [data-testid="baseButton-primary"]:hover {{
  background: linear-gradient(135deg, {ACCENT_PRIMARY} 0%, {ACCENT_HOVER} 100%) !important;
  box-shadow: 0 0 24px rgba(59,130,246,0.45) !important;
  transform: translateY(-1px) !important;
}}
@keyframes btnGlow {{
  0%,100% {{ box-shadow: 0 0 8px rgba(59,130,246,0.2); }}
  50%      {{ box-shadow: 0 0 18px rgba(59,130,246,0.45); }}
}}

/* ── Botón secundario (stretch) sidebar ──────── */
[data-testid="stSidebar"] .stButton > button {{
  transition: all .2s ease !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  border-color: {ACCENT_PRIMARY} !important;
  color: {ACCENT_HOVER} !important;
  background: {ACCENT_SUBTLE} !important;
}}

/* ── Botones primarios ─────────────────────────  */
button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {{
  background-color: {ACCENT_PRIMARY} !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 6px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 1px !important;
  padding: 10px 20px !important;
  transition: background-color .2s ease !important;
}}
button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {{
  background-color: {ACCENT_HOVER} !important;
}}

/* ── Botón de sincronización ──────────────────── */
.btn-sync > button {{
  background: linear-gradient(135deg,{ACCENT_SUBTLE} 0%,{BG_OVERLAY} 100%) !important;
  color: {ACCENT_HOVER} !important;
  border: 1px solid {ACCENT_PRIMARY} !important;
  border-radius: 6px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: .8px !important;
  padding: 12px 16px !important;
  transition: all .2s ease !important;
}}
.btn-sync > button:hover {{
  background: linear-gradient(135deg,{ACCENT_PRIMARY} 0%,{ACCENT_DEEP} 100%) !important;
  color: #FFFFFF !important;
  border-color: {ACCENT_HOVER} !important;
}}

/* ── Botones secundarios ──────────────────────── */
.stButton > button {{
  background-color: {BG_ELEVATED} !important;
  color: {TEXT_DEFAULT} !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  border-radius: 6px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: .8px !important;
  transition: border-color .2s ease, color .2s ease !important;
}}
.stButton > button:hover {{
  border-color: {ACCENT_HOVER} !important;
  color: {ACCENT_HOVER} !important;
}}

/* ── Download — botón primario azul sólido ───── */
.stDownloadButton > button {{
  background: linear-gradient(135deg, {ACCENT_PRIMARY} 0%, #2563EB 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: .8px !important;
  box-shadow: 0 0 14px rgba(59,130,246,.45) !important;
  transition: box-shadow .2s, transform .1s !important;
}}
.stDownloadButton > button:hover {{
  box-shadow: 0 0 24px rgba(59,130,246,.75) !important;
  transform: translateY(-1px) !important;
  background: linear-gradient(135deg, #60A5FA 0%, {ACCENT_PRIMARY} 100%) !important;
  color: #FFFFFF !important;
}}
.stDownloadButton > button:active {{
  transform: translateY(0) !important;
}}

/* ── Botón Exportar Saneamiento — alta visibilidad ── */
@keyframes exportPulse {{
  0%,100% {{ box-shadow: 0 0 14px rgba(59,130,246,.35), 0 4px 18px rgba(29,78,216,.45); }}
  50%      {{ box-shadow: 0 0 32px rgba(96,165,250,.70), 0 6px 28px rgba(59,130,246,.60); }}
}}
.btn-exportar .stDownloadButton > button {{
  background: linear-gradient(135deg, {ACCENT_DEEP} 0%, {ACCENT_PRIMARY} 55%, {ACCENT_HOVER} 100%) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(147,197,253,.30) !important;
  border-radius: 10px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: .8px !important;
  padding: 0 20px !important;
  height: 44px !important;
  min-height: 44px !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  animation: exportPulse 2.8s ease-in-out infinite !important;
  transition: transform .15s ease, box-shadow .2s ease !important;
}}
.btn-exportar .stDownloadButton > button *,
.btn-exportar .stDownloadButton > button p {{
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
}}
.btn-exportar .stDownloadButton > button:hover {{
  background: linear-gradient(135deg, {ACCENT_PRIMARY} 0%, {ACCENT_HOVER} 100%) !important;
  border-color: rgba(147,197,253,.55) !important;
  box-shadow: 0 0 40px rgba(96,165,250,.80), 0 8px 32px rgba(59,130,246,.55) !important;
  transform: translateY(-2px) scale(1.01) !important;
  animation: none !important;
}}
.btn-exportar .stDownloadButton > button:active {{
  transform: translateY(0) scale(1) !important;
  box-shadow: 0 0 16px rgba(59,130,246,.50) !important;
}}

/* ── Botón Notificar Custodio — mismas dimensiones que Exportar ── */
.btn-notificar [data-testid="stPopover"] button,
.btn-notificar button {{
  height: 44px !important;
  min-height: 44px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  font-family: 'IBM Plex Mono', monospace !important;
  letter-spacing: .8px !important;
  padding: 0 20px !important;
  border-radius: 10px !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  background-color: {BG_ELEVATED} !important;
  color: {TEXT_DEFAULT} !important;
  white-space: nowrap !important;
  transition: border-color .2s ease, color .2s ease, background-color .2s ease !important;
  width: 100% !important;
  box-sizing: border-box !important;
}}
.btn-notificar [data-testid="stPopover"] button:hover,
.btn-notificar button:hover {{
  border-color: {ACCENT_PRIMARY} !important;
  color: {ACCENT_HOVER} !important;
  background-color: {ACCENT_SUBTLE} !important;
}}

/* ── Inputs ───────────────────────────────────── */
.stTextInput input, .stTextArea textarea {{
  background-color: {BG_BASE} !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  border-radius: 6px !important;
  color: {TEXT_HIGH} !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color: {ACCENT_PRIMARY} !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stMultiSelect label, .stFileUploader label {{
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 1px !important;
  color: {TEXT_MUTED} !important;
  text-transform: uppercase !important;
}}

/* ── Selectbox — combo animado ───────────────── */
[data-baseweb="select"] > div {{
  background-color: {BG_ELEVATED} !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  border-radius: 7px !important;
  transition: border-color 0.22s ease, box-shadow 0.22s ease, background-color 0.22s ease !important;
  cursor: pointer !important;
}}
[data-baseweb="select"] > div:hover {{
  border-color: {ACCENT_PRIMARY} !important;
  background-color: {BG_OVERLAY} !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12), 0 2px 8px rgba(0,0,0,0.35) !important;
}}
[data-baseweb="select"] > div:focus-within {{
  border-color: {ACCENT_PRIMARY} !important;
  background-color: {BG_OVERLAY} !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.18), 0 4px 16px rgba(59,130,246,0.12) !important;
}}
/* Texto del valor seleccionado */
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] span,
[data-baseweb="select"] div[class*="singleValue"] {{
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
  color: {TEXT_HIGH} !important;
  font-weight: 500 !important;
  letter-spacing: 0.2px !important;
}}
/* Placeholder */
[data-baseweb="select"] div[class*="placeholder"] {{
  color: {TEXT_DISABLED} !important;
  font-style: italic !important;
}}
/* Icono caret (chevron) */
[data-baseweb="select"] svg {{
  color: {ACCENT_PRIMARY} !important;
  transition: transform 0.22s ease !important;
}}
[data-baseweb="select"] div[aria-expanded="true"] svg {{
  transform: rotate(180deg) !important;
}}
/* Menú desplegable — slide-in animado */
[data-baseweb="popover"] [data-baseweb="menu"] {{
  background-color: {BG_ELEVATED} !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.55), 0 2px 8px rgba(59,130,246,0.08) !important;
  animation: talon-dropdown-in 0.18s cubic-bezier(0.16,1,0.3,1) both !important;
}}
@keyframes talon-dropdown-in {{
  from {{ opacity: 0; transform: translateY(-6px) scale(0.98); }}
  to   {{ opacity: 1; transform: translateY(0)   scale(1);    }}
}}
/* Opciones del menú */
[data-baseweb="option"] {{
  background-color: transparent !important;
  color: {TEXT_DEFAULT} !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
  border-radius: 5px !important;
  margin: 2px 4px !important;
  transition: background-color 0.14s ease, color 0.14s ease !important;
}}
[data-baseweb="option"]:hover {{
  background-color: {ACCENT_SUBTLE} !important;
  color: {ACCENT_BRIGHT} !important;
}}
[data-baseweb="option"][aria-selected="true"] {{
  background-color: {ACCENT_SUBTLE} !important;
  color: {ACCENT_HOVER} !important;
  font-weight: 600 !important;
}}

/* ── Tabs ─────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background-color: transparent !important;
  border-bottom: 1px solid {BORDER_SUBTLE} !important;
  gap: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
  background-color: transparent !important;
  color: {TEXT_MUTED} !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  padding: 6px 12px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: .8px !important;
  text-transform: uppercase !important;
  transition: color .2s, border-color .2s !important;
}}
@keyframes tabGlowBorder {{
  0%,100% {{ box-shadow: 0 -2px 8px transparent; }}
  50%      {{ box-shadow: 0 -2px 14px rgba(59,130,246,0.35); }}
}}
.stTabs [aria-selected="true"] {{
  color: {TEXT_HIGH} !important;
  border-bottom: 2px solid {ACCENT_PRIMARY} !important;
  text-shadow: 0 0 12px rgba(59,130,246,0.22) !important;
  animation: tabGlowBorder 3.5s ease-in-out infinite !important;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: {TEXT_DEFAULT} !important; }}
.stTabs [data-baseweb="tab-panel"] {{
  padding-top: 10px !important;
  background-color: transparent !important;
}}

/* Columnas (st.columns) — hueco horizontal mínimo */
[data-baseweb="tab-panel"] > [data-testid="stVerticalBlock"],
[data-baseweb="tab-panel"] [data-testid="stVerticalBlock"] {{
  gap: 0.4rem !important;
}}
/* Explorador: separación moderada entre el tip y la tabla (iframe) */
[data-baseweb="tab-panel"] [data-testid="stVerticalBlock"]:has(.talon-explorer-tip) {{
  gap: 0.75rem !important;
}}

/* ── Dataframe ────────────────────────────────── */
[data-testid="stDataFrame"] {{
  border: 1px solid {BORDER_SUBTLE} !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  box-shadow:
    0 0 0 1px rgba(59,130,246,0.08),
    0 12px 40px rgba(7,11,18,0.45) !important;
  transition: box-shadow .35s ease, border-color .25s ease !important;
  --gdg-cell-horizontal-padding: 4px !important;
  --gdg-cell-vertical-padding: 1px !important;
}}
[data-testid="stDataFrame"]:hover {{
  border-color: {BORDER_STRONG} !important;
  box-shadow:
    0 0 0 1px rgba(59,130,246,0.18),
    0 16px 48px rgba(59,130,246,0.08) !important;
}}

/* Explorador — tip superior */
.talon-explorer-tip {{
  background: linear-gradient(135deg, {BG_ELEVATED} 0%, {BG_SURFACE} 100%);
  border: 1px solid {BORDER_DEFAULT};
  border-left: 3px solid {ACCENT_PRIMARY};
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 0 !important;
  animation: explorerTipIn .45s ease both;
}}
/* Explorador — tip "Cómo leer" (Streamlit envuelve el markdown; el hueco hasta la tabla es el gap de la columna) */
div[data-testid="element-container"]:has(.talon-explorer-tip) {{
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}}
div[data-testid="element-container"]:has(.talon-explorer-tip) [data-testid="stMarkdownContainer"],
div[data-testid="element-container"]:has(.talon-explorer-tip) [data-testid="stMarkdownContainer"] p {{
  margin-bottom: 0 !important;
}}
div[data-testid="element-container"]:has(.talon-explorer-tip) + div[data-testid="element-container"] {{
  margin-top: 0 !important;
  padding-top: 0 !important;
}}
.talon-explorer-tip-title {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 1.1px;
  text-transform: uppercase;
  color: {ACCENT_HOVER};
  margin: 0 0 6px 0;
}}
.talon-explorer-tip-text {{
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 11px;
  line-height: 1.42;
  color: {TEXT_DEFAULT};
  margin: 0;
}}
@keyframes explorerTipIn {{
  from {{ opacity: 0; transform: translateY(-6px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

/* Tarjetas de medidor */
.talon-meter-gauge {{
  border-radius: 10px !important;
  animation: gaugePop .55s cubic-bezier(.16,1,.3,1) both;
}}
.talon-meter-gauge:hover {{
  box-shadow:
    0 0 0 1px rgba(59,130,246,0.25),
    0 8px 28px rgba(59,130,246,0.12) !important;
}}
@keyframes gaugePop {{
  from {{ opacity: 0; transform: translateY(8px) scale(.96); }}
  to   {{ opacity: 1; transform: none; }}
}}

/* ── Alertas ──────────────────────────────────── */
.stAlert {{
  border-radius: 6px !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
}}

/* ── Expander ─────────────────────────────────── */
[data-testid="stExpander"] {{
  background-color: {BG_BASE} !important;
  border: 1px solid {BORDER_SUBTLE} !important;
  border-radius: 6px !important;
}}

/* ── Spinner ──────────────────────────────────── */
.stSpinner > div > div {{ border-top-color: {ACCENT_PRIMARY} !important; }}

/* ── Scrollbar ────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG_BASE}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_DEFAULT}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {ACCENT_PRIMARY}; }}

/* ── Cards ────────────────────────────────────── */
.talon-card {{
  background: {BG_ELEVATED};
  border: 1px solid {BORDER_DEFAULT};
  border-radius: 8px;
  padding: 32px 36px;
  box-shadow: 0 4px 24px rgba(7,11,18,0.4);
}}
.talon-card-accent {{
  background: {BG_ELEVATED};
  border: 1px solid {BORDER_DEFAULT};
  border-left: 2px solid {ACCENT_PRIMARY};
  border-radius: 6px;
  padding: 14px 18px;
}}

/* ── Chip sync ────────────────────────────────── */
.sync-status {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: {BG_ELEVATED};
  border: 1px solid {BORDER_SUBTLE};
  border-radius: 20px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: {TEXT_MUTED};
  letter-spacing: .6px;
  margin-bottom: 8px;
}}
.sync-dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: {STATE_HEALTHY};
  animation: pulse 2.4s ease-in-out infinite;
}}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.2}} }}

[data-testid="stChatMessage"] {{
  animation: chatMsgIn .4s cubic-bezier(.16,1,.3,1) both !important;
}}
@keyframes chatMsgIn {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to   {{ opacity: 1; transform: none; }}
}}
[data-testid="stChatMessageContent"] {{
  background: linear-gradient(145deg, {BG_ELEVATED} 0%, {BG_SURFACE} 100%) !important;
  border: 1px solid {BORDER_SUBTLE} !important;
  border-radius: 14px !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
  line-height: 1.55 !important;
  box-shadow: 0 6px 24px rgba(0,0,0,0.28) !important;
  transition: border-color .2s ease, box-shadow .25s ease !important;
}}
[data-testid="stChatMessageContent"]:hover {{
  border-color: rgba(59,130,246,0.35) !important;
  box-shadow: 0 8px 32px rgba(59,130,246,0.12) !important;
}}
[data-testid="stChatFloatingInputContainer"], [data-testid="stBottomBlockContainer"] .stChatInput {{
  backdrop-filter: blur(8px) !important;
}}
.stChatInput textarea {{
  background-color: rgba(22,27,34,0.92) !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  border-radius: 12px !important;
  color: {TEXT_HIGH} !important;
  transition: border-color .2s ease, box-shadow .25s ease !important;
}}
.stChatInput textarea:focus {{
  border-color: {ACCENT_PRIMARY} !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15), 0 4px 20px rgba(59,130,246,0.12) !important;
}}
.talon-chat-subhint {{
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 11px;
  color: {TEXT_MUTED};
  line-height: 1.5;
  margin: 0 0 14px 0;
  padding-left: 2px;
  border-left: 2px solid {ACCENT_SUBTLE};
  padding-left: 10px;
}}
[data-testid="stFileUploader"] {{
  background-color: {BG_BASE} !important;
  border: 1px dashed {BORDER_DEFAULT} !important;
  border-radius: 6px !important;
}}

/* ── Popover ──────────────────────────────────── */
[data-testid="stPopover"] {{
  background-color: {BG_ELEVATED} !important;
  border: 1px solid {BORDER_DEFAULT} !important;
  border-radius: 6px !important;
}}

/* ── Multiselect tags ─────────────────────────── */
[data-baseweb="tag"] {{
  background-color: {BORDER_SUBTLE} !important;
  color: {TEXT_DEFAULT} !important;
  border-radius: 3px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 11px !important;
}}

/* ── Progress bar (st.progress) ───────────────── */
[data-testid="stProgressBar"] > div > div {{
  background-color: {ACCENT_PRIMARY} !important;
}}

/* ── Layout — contenido principal más denso (vista análisis) ───────────────── */
.block-container {{ padding: 10px 1.25rem 14px 1.25rem !important; max-width: 100% !important; }}

/* ── Colapsar iframes de inyección CSS (fuera de pestañas) ───────── */
[data-testid="stIFrame"] {{
  height: 1px !important;
  min-height: 0 !important;
  overflow: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 0 !important;
}}

/*
  En pestañas, components.html sí tiene UI (p. ej. Copiar SKUs).
  El colapso 1px deja el envoltorio a ~38px y el iframe invisible → banda negra vacía.
*/
[data-baseweb="tab-panel"] div[data-testid="element-container"]:has(iframe) {{
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}}
[data-baseweb="tab-panel"] [data-testid="stIFrame"] {{
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
  overflow: visible !important;
  line-height: normal !important;
}}
[data-baseweb="tab-panel"] [data-testid="stIFrame"] iframe {{
  height: 38px !important;
  min-height: 38px !important;
  overflow: visible !important;
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  vertical-align: top !important;
}}

/* ── Animaciones ──────────────────────────────── */
@keyframes fadeIn  {{ from{{opacity:0;transform:translateY(4px)}} to{{opacity:1;transform:translateY(0)}} }}
@keyframes slideIn {{ from{{opacity:0;transform:translateX(-6px)}} to{{opacity:1;transform:translateX(0)}} }}
@keyframes popIn   {{ from{{opacity:0;transform:scale(.96)}} to{{opacity:1;transform:scale(1)}} }}

.stTabs [data-baseweb="tab-panel"] > div {{ animation: fadeIn .25s ease; }}
[data-testid="stSidebar"] > div:first-child {{ animation: slideIn .3s ease; }}
[data-testid="stMetric"] {{ animation: popIn .3s ease both; }}

/* Cards: glow sutil en hover */
.talon-card:hover {{
  box-shadow: 0 4px 32px rgba(7,11,18,0.5), 0 0 0 1px {ACCENT_PRIMARY}22 !important;
  transition: box-shadow .3s ease !important;
}}
"""


def _build_login_css() -> str:
    """CSS del login con animaciones futuristas. Sin wrappers HTML."""
    return f"""
html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
.stApp {{ background-color: {BG_DEEP} !important; overflow: hidden !important; }}
section[data-testid="stMain"] {{ padding: 0 !important; }}
[data-testid="stSidebar"]      {{ display: none !important; }}
[data-testid="stSidebarNav"]   {{ display: none !important; }}
header[data-testid="stHeader"] {{ display: none !important; }}
[data-testid="stToolbar"]      {{ display: none !important; }}
[data-testid="stDecoration"]   {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
#MainMenu                      {{ display: none !important; }}
footer                         {{ display: none !important; }}
.block-container               {{ padding: 0 !important; max-width: 100% !important; }}
.stMainBlockContainer          {{ padding: 0 !important; max-width: 100% !important; }}
[data-testid="stAppViewContainer"] {{ padding: 0 !important; }}

/* ── Botón login ─────────────────────────────────── */
.btn-talon-login {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 14px 20px;
  background: {BG_ELEVATED};
  border: 1px solid {BORDER_DEFAULT};
  border-radius: 8px;
  cursor: pointer;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .8px;
  color: {TEXT_DEFAULT};
  transition: all .25s ease;
  text-transform: uppercase;
  text-decoration: none;
  position: relative;
  overflow: hidden;
}}
.btn-talon-login::before {{
  content: '';
  position: absolute;
  left: -100%;
  top: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.08), transparent);
  transition: left .4s ease;
}}
.btn-talon-login:hover::before {{ left: 100%; }}
.btn-talon-login:hover {{
  border-color: {ACCENT_PRIMARY} !important;
  color: {TEXT_HIGH} !important;
  background: {BG_OVERLAY} !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12), 0 0 20px rgba(59,130,246,0.08) !important;
}}

/* ── Keyframes base ─────────────────────────────── */
@keyframes spin    {{ to{{ transform: rotate(360deg) }} }}
@keyframes fadeUp  {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}

/* ── Fondo animado grid ─────────────────────────── */
.talon-bg-animated {{
  position: fixed;
  inset: 0;
  background: {BG_DEEP};
  background-image:
    linear-gradient(rgba(59,130,246,0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59,130,246,0.045) 1px, transparent 1px);
  background-size: 48px 48px;
  animation: gridPulse 7s ease-in-out infinite;
  z-index: 0;
}}
@keyframes gridPulse {{ 0%,100%{{opacity:.35}} 50%{{opacity:.8}} }}

/* ── Scan beam ──────────────────────────────────── */
.talon-scan-beam {{
  position: fixed;
  top: -220px;
  left: 0; right: 0;
  height: 220px;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(59,130,246,0.012) 30%,
    rgba(59,130,246,0.055) 50%,
    rgba(59,130,246,0.012) 70%,
    transparent 100%
  );
  z-index: 0;
  pointer-events: none;
  animation: scanBeam 9s linear infinite;
}}
@keyframes scanBeam {{ 0%{{top:-220px}} 100%{{top:110vh}} }}

/* ── Partículas flotantes ───────────────────────── */
.talon-dot-1,.talon-dot-2,.talon-dot-3,.talon-dot-4,.talon-dot-5,.talon-dot-6 {{
  position: fixed;
  width: 2px; height: 2px;
  background: {ACCENT_PRIMARY};
  border-radius: 50%;
  opacity: 0;
  pointer-events: none;
  animation: dotRise linear infinite;
  z-index: 0;
}}
.talon-dot-1 {{ left:8%;  animation-duration:8s;  animation-delay:0s;    bottom:-10px; }}
.talon-dot-2 {{ left:22%; animation-duration:11s; animation-delay:1.8s;  bottom:-10px; }}
.talon-dot-3 {{ left:44%; animation-duration:7s;  animation-delay:3.2s;  bottom:-10px; }}
.talon-dot-4 {{ left:62%; animation-duration:13s; animation-delay:0.6s;  bottom:-10px; }}
.talon-dot-5 {{ left:78%; animation-duration:9s;  animation-delay:2.4s;  bottom:-10px; }}
.talon-dot-6 {{ left:90%; animation-duration:10s; animation-delay:4.5s;  bottom:-10px; }}
@keyframes dotRise {{
  0%   {{ opacity:0;   transform:translateY(0); }}
  10%  {{ opacity:.65; }}
  85%  {{ opacity:.65; }}
  100% {{ opacity:0;   transform:translateY(-110vh); }}
}}

/* ── Tarjeta de login ───────────────────────────── */
.talon-card-login {{
  position: relative;
  background: linear-gradient(160deg, {BG_BASE} 0%, {BG_SURFACE} 100%);
  border: 1px solid {BORDER_DEFAULT};
  border-radius: 18px;
  padding: 52px 48px 44px;
  width: 100%;
  max-width: 420px;
  box-shadow:
    0 0 80px rgba(59,130,246,0.07),
    0 32px 80px rgba(0,0,0,.8),
    inset 0 1px 0 rgba(255,255,255,0.04);
  animation: cardEnter .75s cubic-bezier(.16,1,.3,1) both;
  overflow: visible;
  z-index: 10;
}}
.talon-card-login::before {{
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 19px;
  background: linear-gradient(
    135deg,
    {ACCENT_PRIMARY}55 0%,
    transparent 42%,
    transparent 58%,
    {ACCENT_PRIMARY}33 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: exclude;
  mask-composite: exclude;
  padding: 1px;
  animation: borderPulse 4s ease-in-out infinite;
  pointer-events: none;
}}
@keyframes cardEnter   {{ from{{opacity:0;transform:translateY(32px) scale(.96)}} to{{opacity:1;transform:none}} }}
@keyframes borderPulse {{ 0%,100%{{opacity:.3}} 50%{{opacity:1}} }}

/* ── Brackets de esquina ────────────────────────── */
.corner-tl,.corner-tr,.corner-bl,.corner-br {{
  position: absolute;
  width: 14px; height: 14px;
  border-color: {ACCENT_PRIMARY};
  border-style: solid;
  opacity: .65;
  animation: cornerFade 4s ease-in-out infinite;
}}
.corner-tl {{ top:12px;  left:12px;  border-width:1.5px 0 0 1.5px; border-radius:3px 0 0 0; }}
.corner-tr {{ top:12px;  right:12px; border-width:1.5px 1.5px 0 0; border-radius:0 3px 0 0; }}
.corner-bl {{ bottom:12px; left:12px;  border-width:0 0 1.5px 1.5px; border-radius:0 0 0 3px; }}
.corner-br {{ bottom:12px; right:12px; border-width:0 1.5px 1.5px 0; border-radius:0 0 3px 0; }}
@keyframes cornerFade {{ 0%,100%{{opacity:.4}} 50%{{opacity:.9}} }}

/* ── Contenedor logo cuervo ─────────────────────── */
.talon-raven-wrap {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84px; height: 84px;
  background: linear-gradient(135deg, {ACCENT_SUBTLE}, {BG_BASE});
  border: 1px solid {ACCENT_PRIMARY}66;
  border-radius: 20px;
  margin: 0 auto 22px;
  position: relative;
  animation: ravenHalo 3.5s ease-in-out infinite;
}}
.talon-raven-wrap::before {{
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 28px;
  background: radial-gradient(circle, {ACCENT_PRIMARY}1A 0%, transparent 70%);
  animation: auraBreath 3.5s ease-in-out infinite;
  pointer-events: none;
}}
@keyframes ravenHalo {{
  0%,100% {{ box-shadow: 0 0 18px rgba(59,130,246,0.22); }}
  50%      {{ box-shadow: 0 0 48px rgba(59,130,246,0.6), 0 0 100px rgba(59,130,246,0.14); }}
}}
@keyframes auraBreath {{
  0%,100% {{ opacity:0; transform:scale(1); }}
  50%      {{ opacity:1; transform:scale(1.1); }}
}}

/* ── Ojo del cuervo (SVG class) ─────────────────── */
.raven-eye {{
  animation: eyeGlow 2.5s ease-in-out infinite;
}}
@keyframes eyeGlow {{
  0%,100% {{ fill:{ACCENT_PRIMARY}; }}
  50%      {{ fill:#B3D4FF; filter:drop-shadow(0 0 5px #3B82F6); }}
}}

/* ── Título con efecto glitch ───────────────────── */
.talon-glitch {{
  position: relative;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 5px;
  color: {TEXT_HIGH};
  text-align: center;
  margin: 0 0 6px;
  display: block;
  animation: titleGlow 5s ease-in-out infinite;
}}
.talon-glitch::before {{
  content: attr(data-text);
  position: absolute;
  inset: 0;
  color: {ACCENT_BRIGHT};
  text-align: center;
  animation: glitchA 7s steps(1) infinite;
  clip-path: polygon(0 15%, 100% 15%, 100% 38%, 0 38%);
}}
.talon-glitch::after {{
  content: attr(data-text);
  position: absolute;
  inset: 0;
  color: {ACCENT_PRIMARY};
  text-align: center;
  animation: glitchB 7s steps(1) infinite;
  clip-path: polygon(0 60%, 100% 60%, 100% 82%, 0 82%);
}}
@keyframes titleGlow {{
  0%,100% {{ text-shadow:none; }}
  50%      {{ text-shadow:0 0 24px rgba(59,130,246,0.35); }}
}}
@keyframes glitchA {{
  0%,87%,100% {{ transform:none;opacity:0; }}
  89%          {{ transform:translateX(-3px);opacity:.9; }}
  91%          {{ transform:translateX(2px);opacity:.9; }}
  93%          {{ transform:none;opacity:0; }}
}}
@keyframes glitchB {{
  0%,90%,100% {{ transform:none;opacity:0; }}
  92%          {{ transform:translateX(3px);opacity:.7; }}
  94%          {{ transform:translateX(-2px);opacity:.7; }}
  96%          {{ transform:none;opacity:0; }}
}}

/* ── Divisor animado ────────────────────────────── */
.talon-divider {{
  height: 1px;
  background: linear-gradient(90deg, transparent, {BORDER_DEFAULT}, {BORDER_DEFAULT}, transparent);
  margin: 26px 0;
  position: relative;
}}
.talon-divider::after {{
  content: '';
  position: absolute;
  left: 50%; top: -1px;
  transform: translateX(-50%);
  width: 30px; height: 3px;
  background: {ACCENT_PRIMARY};
  border-radius: 2px;
  filter: blur(2px);
  animation: divPulse 3.5s ease-in-out infinite;
}}
@keyframes divPulse {{ 0%,100%{{opacity:.3;width:16px}} 50%{{opacity:1;width:56px}} }}
"""


# ─────────────────────────────────────────────────────────
#  INYECTORES PÚBLICOS — vía JavaScript (evita sanitizador Streamlit 1.35+)
# ─────────────────────────────────────────────────────────

def _inject_css_via_iframe(css: str) -> None:
    """
    Mecanismo central de inyección. Usa st.components.v1.html() con un
    script que escribe en window.parent.document.head (iframe mismo-origen).
    height=0 colapsa el iframe al mínimo.
    """
    import streamlit.components.v1 as components

    safe_css = css.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    components.html(
        f"""<style>html,body{{margin:0;padding:0;overflow:hidden}}</style>
<script>
(function() {{
  var par = window.parent.document;

  if (!par.getElementById('talon-fonts')) {{
    var lnk = par.createElement('link');
    lnk.id   = 'talon-fonts';
    lnk.rel  = 'stylesheet';
    lnk.href = '{FONTS_URL}';
    par.head.appendChild(lnk);
  }}

  /* Favicon personalizado — SVG real del cuervo */
  var existingFavicons = par.querySelectorAll('link[rel*="icon"]');
  existingFavicons.forEach(function(f) {{ f.remove(); }});
  if ('{_CROW_FAVICON_B64}') {{
    var favLink = par.createElement('link');
    favLink.id   = 'talon-favicon';
    favLink.rel  = 'icon';
    favLink.type = 'image/svg+xml';
    favLink.href = 'data:image/svg+xml;base64,{_CROW_FAVICON_B64}';
    par.head.appendChild(favLink);
  }}

  var existing = par.getElementById('talon-css');
  if (existing) existing.remove();
  var s = par.createElement('style');
  s.id = 'talon-css';
  s.textContent = `{safe_css}`;
  par.head.appendChild(s);

  try {{
    var iframes = par.querySelectorAll('iframe[title="streamlit_html"]');
    iframes.forEach(function(f) {{
      /* No colapsar components.html con UI (p. ej. Copiar SKUs en Explorador) */
      if (f.closest('[data-baseweb="tab-panel"]')) return;
      f.style.cssText = 'height:1px!important;display:block!important;overflow:hidden!important;margin:0!important;padding:0!important;';
      var wrapper = f.closest('[data-testid="stIFrame"]');
      if (wrapper) wrapper.style.cssText = 'height:1px!important;overflow:hidden!important;margin:0!important;padding:0!important;min-height:0!important;';
    }});
  }} catch(e) {{}}


}})();
</script>""",
        height=0,
    )


def _build_light_mode_css() -> str:
    """Sobreescritura de colores para el modo claro. Se inyecta DESPUÉS del CSS global oscuro."""
    return """
/* ════════════════════════════════════════════
   MODO CLARO — overrides sobre la base oscura
   ════════════════════════════════════════════ */

/* ── Fondos globales ────────────────────────── */
.stApp, .stAppViewContainer,
.block-container, .stMainBlockContainer,
[data-testid="stAppViewContainer"],
section[data-testid="stMain"]           { background-color: #F0F4F8 !important; }

/* Layout denso (alineado con tema oscuro) */
.block-container, .stMainBlockContainer  { padding: 10px 1.25rem 14px 1.25rem !important; }
[data-testid="stHorizontalBlock"]       { gap: 0.35rem !important; align-items: stretch !important; }
[data-baseweb="tab-panel"] [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
[data-baseweb="tab-panel"] [data-testid="stVerticalBlock"]:has(.talon-explorer-tip) { gap: 0.75rem !important; }

/* ── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"]               { background-color: #FFFFFF !important; border-right: 1px solid #CBD5E1 !important; }
[data-testid="stSidebar"] *             { color: #1E293B !important; }
[data-testid="stSidebar"] hr            { border-color: #E2E8F0 !important; }

/* ── Texto general ──────────────────────────── */
body, html                              { color: #1E293B !important; background: #F0F4F8 !important; }
p, span, label, h1, h2, h3, h4, h5, h6 { color: #1E293B !important; }
.stMarkdown, .stMarkdown *              { color: #1E293B !important; }
.t-label                                { color: #475569 !important; }

/* ── Cards y contenedores ───────────────────── */
.talon-card, .talon-card-accent         { background: #FFFFFF !important; border-color: #CBD5E1 !important; }
[data-testid="stMetric"],
[data-testid="stMetricDelta"],
[data-testid="stMetricValue"]           { color: #0F172A !important; }
[data-testid="stMetricLabel"]           { color: #475569 !important; }

/* ── Pestañas ───────────────────────────────── */
[data-baseweb="tab-list"]               { background: #FFFFFF !important; border-bottom: 1px solid #E2E8F0 !important; }
[data-baseweb="tab"]                    { background: transparent !important; color: #475569 !important; }
[aria-selected="true"][data-baseweb="tab"] { color: #1D4ED8 !important; border-bottom-color: #1D4ED8 !important; }
[data-baseweb="tab-panel"]              { background: #F0F4F8 !important; }
[data-testid="stTabs"]                  { background: #F0F4F8 !important; }

/* ── Inputs / Textareas / Selectbox ─────────── */
input, textarea                         { background: #FFFFFF !important; color: #0F172A !important; border-color: #CBD5E1 !important; }
.stTextInput input, .stTextArea textarea { background: #FFFFFF !important; color: #0F172A !important; }
[data-baseweb="select"] > div,
[data-baseweb="select"] *               { background: #FFFFFF !important; color: #0F172A !important; border-color: #CBD5E1 !important; }
[data-baseweb="input"]                  { background: #FFFFFF !important; border-color: #CBD5E1 !important; }
[data-baseweb="menu"]                   { background: #FFFFFF !important; }
[data-baseweb="option"]                 { background: #FFFFFF !important; color: #1E293B !important; }
[data-baseweb="option"]:hover           { background: #EFF6FF !important; }

/* ── Multiselect ────────────────────────────── */
[data-baseweb="tag"]                    { background: #DBEAFE !important; color: #1D4ED8 !important; }

/* ── Dataframe / tablas ─────────────────────── */
[data-testid="stDataFrame"],
.glideDataEditor,
[data-testid="stDataFrame"] *           { background-color: #FFFFFF !important; color: #1E293B !important; }
.dvn-scroller                           { background: #FFFFFF !important; }

/* ── Popovers / dropdowns ───────────────────── */
[data-testid="stPopover"],
[data-testid="stPopoverBody"],
[data-baseweb="popover"],
[data-baseweb="popover"] *              { background: #FFFFFF !important; color: #1E293B !important; border-color: #CBD5E1 !important; }

/* ── Chat ────────────────────────────────────── */
[data-testid="stChatMessageContent"],
[data-testid="stChatMessageContent"] *  { background: #FFFFFF !important; color: #1E293B !important; border-color: #E2E8F0 !important; }
.stChatInput textarea                   { background: #FFFFFF !important; border-color: #CBD5E1 !important; color: #0F172A !important; }

/* ── Alertas / Notificaciones de Streamlit ──── */
[data-testid="stAlert"]                 { background: #EFF6FF !important; border-color: #BFDBFE !important; color: #1D4ED8 !important; }
[data-testid="stAlert"] *               { color: #1D4ED8 !important; }

/* ── Expanders ──────────────────────────────── */
[data-testid="stExpander"]              { background: #FFFFFF !important; border-color: #E2E8F0 !important; }
[data-testid="stExpander"] *            { color: #1E293B !important; }
[data-testid="stExpander"] summary      { background: #F8FAFC !important; }

/* ── Botones secundarios ────────────────────── */
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondary"] * { background: #F1F5F9 !important; color: #1E293B !important; border-color: #CBD5E1 !important; }
[data-testid="stBaseButton-secondary"]:hover * { background: #E2E8F0 !important; }

/* ── File uploader ──────────────────────────── */
[data-testid="stFileUploader"]          { background: #FFFFFF !important; border-color: #94A3B8 !important; }

/* ── Sync chip / custom chips ───────────────── */
.sync-status                            { background: #F1F5F9 !important; border-color: #CBD5E1 !important; color: #475569 !important; }

/* ── Dividers ───────────────────────────────── */
hr, [data-testid="stSidebar"] hr        { border-color: #CBD5E1 !important; }

/* ── Altair / Vega chart wrappers ───────────── */
.vega-embed, .vega-embed *              { background: transparent !important; }
"""


def inject_global_css(light_mode: bool = False) -> None:
    """Inyecta fuentes y CSS global en el DOM de Streamlit vía st.iframe.
    
    Args:
        light_mode: Si True, inyecta los overrides de modo claro sobre el CSS oscuro base.
    """
    css = _build_global_css()
    if light_mode:
        css += _build_light_mode_css()
    _inject_css_via_iframe(css)


def inject_login_css() -> None:
    """Inyecta fuentes y CSS de login en el DOM de Streamlit vía st.iframe."""
    _inject_css_via_iframe(_build_login_css())
