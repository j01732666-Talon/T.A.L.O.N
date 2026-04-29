"""
    Punto de entrada principal de la aplicación T.A.L.O.N.
    Tablero Analítico de Limpieza y Orquestación de Negocios.

    Sistema de Diseño: Enterprise Dark — Flat, Limpio, Alto Contraste.
"""
import sys
import os

# --- ESCUDO DE RUTAS ---
ruta_actual = os.path.dirname(os.path.abspath(__file__))
if ruta_actual not in sys.path:
    sys.path.append(ruta_actual)

import streamlit as st
import pandas as pd
import polars as pl
import time
import json

from config import DOMINIOS_CONFIG, UNIDADES_REF, CUSTODIOS, NOMBRES_MATERIALES
from core.motor_calidad import adaptar_reglas_ia_a_motor
from core.motor_calidad import ejecutar_auditoria_completa, generar_excel_saneamiento_memoria
from core.motor_ia import responder_chat_ia, generar_reglas_autonomas_ia, guardar_reglas_prime
from ui.ui_components import (renderizar_metricas, renderizar_grafico_dimensiones,
                               renderizar_tabla_hallazgos, renderizar_grafico_top_errores,
                               renderizar_grafico_por_foco)
from infra.datalake_manager import inicializar_datalake, guardar_auditoria, obtener_historial_metricas
from infra.auth_manager import inicializar_tabla_usuarios, registrar_usuario, validar_credenciales
from infra.bigquery_client import extraer_maestro_materiales

inicializar_datalake()
inicializar_tabla_usuarios()

st.set_page_config(
    page_title="T.A.L.O.N — Auditoría de Datos",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
#  SISTEMA DE DISEÑO GLOBAL — CSS
#  Paleta: #0D1117 fondo · #161B22 card · #21262D borde suave
#          #30363D borde estándar · #E6EDF3 texto · #8B949E muted
#          #2F81F7 acento azul · #F85149 error · #3FB950 ok
# ═══════════════════════════════════════════════════════════════
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
    /* ── Base ───────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stApp {
        background-color: #0D1117;
        color: #E6EDF3;
    }

    /* ── Tipografía utilitaria ──────────────────────────── */
    .t-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        color: #8B949E;
    }
    .t-heading {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 28px;
        font-weight: 700;
        color: #E6EDF3;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .t-sub {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px;
        color: #8B949E;
        line-height: 1.5;
    }

    /* ── Sidebar ────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #0D1117 !important;
        border-right: 1px solid #21262D !important;
    }
    [data-testid="stSidebar"] * {
        color: #C9D1D9 !important;
    }
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stMultiSelect label {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
    }
    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: #21262D !important;
    }

    /* ── Botones primarios ──────────────────────────────── */
    div[data-testid="stForm"] button[kind="primaryFormSubmit"],
    button[data-testid="baseButton-primary"],
    .stButton > button[kind="primary"] {
        background-color: #2F81F7 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        padding: 10px 20px !important;
        transition: background-color .15s ease !important;
    }
    div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background-color: #388BFD !important;
    }

    /* Botones secundarios */
    .stButton > button[kind="secondary"],
    .stButton > button {
        background-color: #161B22 !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
        border-radius: 4px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        letter-spacing: .8px !important;
        transition: border-color .15s ease, color .15s ease !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button:hover {
        border-color: #58A6FF !important;
        color: #58A6FF !important;
    }

    /* ── Download button ────────────────────────────────── */
    .stDownloadButton > button {
        background-color: #161B22 !important;
        color: #3FB950 !important;
        border: 1px solid #3FB950 !important;
        border-radius: 4px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        letter-spacing: .8px !important;
    }
    .stDownloadButton > button:hover {
        background-color: #3FB950 !important;
        color: #0D1117 !important;
    }

    /* ── Inputs / Text ──────────────────────────────────── */
    .stTextInput input, .stTextArea textarea {
        background-color: #0D1117 !important;
        border: 1px solid #30363D !important;
        border-radius: 4px !important;
        color: #E6EDF3 !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2F81F7 !important;
        box-shadow: none !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stMultiSelect label, .stFileUploader label {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        color: #8B949E !important;
        text-transform: uppercase !important;
    }

    /* ── Tabs ───────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid #21262D !important;
        gap: 0px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8B949E !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 10px 20px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: .8px !important;
        text-transform: uppercase !important;
        transition: color .15s ease, border-color .15s ease !important;
    }
    .stTabs [aria-selected="true"] {
        color: #E6EDF3 !important;
        border-bottom: 2px solid #2F81F7 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #C9D1D9 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px !important;
        background-color: transparent !important;
    }

    /* ── Dataframe / Tabla ──────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid #21262D !important;
        border-radius: 6px !important;
        overflow: hidden !important;
    }

    /* ── Alertas / mensajes ─────────────────────────────── */
    .stAlert {
        border-radius: 4px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
    }
    [data-testid="stNotification"] {
        background-color: #161B22 !important;
        border: 1px solid #21262D !important;
        border-radius: 4px !important;
    }

    /* ── Expander sidebar ───────────────────────────────── */
    [data-testid="stExpander"] {
        background-color: #0D1117 !important;
        border: 1px solid #21262D !important;
        border-radius: 4px !important;
    }

    /* ── Spinner ─────────────────────────────────────────── */
    .stSpinner > div > div {
        border-top-color: #2F81F7 !important;
    }

    /* ── Scrollbar global ───────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0D1117; }
    ::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #484F58; }

    /* ── Cards utilitarias ──────────────────────────────── */
    .talon-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 28px 32px;
    }
    .talon-card-accent {
        background: #161B22;
        border: 1px solid #30363D;
        border-left: 3px solid #2F81F7;
        border-radius: 6px;
        padding: 14px 18px;
    }

    /* ── Chat ───────────────────────────────────────────── */
    [data-testid="stChatMessageContent"] {
        background-color: #161B22 !important;
        border: 1px solid #21262D !important;
        border-radius: 6px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
    }
    .stChatInput textarea {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 4px !important;
        color: #E6EDF3 !important;
    }

    /* ── File uploader ──────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background-color: #0D1117 !important;
        border: 1px dashed #30363D !important;
        border-radius: 6px !important;
    }

    /* ── Popover ────────────────────────────────────────── */
    [data-testid="stPopover"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 6px !important;
    }

    /* ── Multiselect tags ───────────────────────────────── */
    [data-baseweb="tag"] {
        background-color: #21262D !important;
        color: #C9D1D9 !important;
        border-radius: 3px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
    }

    /* ── Quita padding excesivo del main ────────────────── */
    .block-container {
        padding-top: 28px !important;
        padding-bottom: 40px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
#  ESTADO INICIAL
# ─────────────────────────────────────────────
defaults = {
    'autenticado':      False,
    'usuario_actual':   "",
    'chat_historial':   [],
    'reglas_ia_dinamicas': None,
    'mostrar_registro': False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

dominio_oficial = st.secrets.get("dominio_empresa", "@brinsa.com.co")


# ═══════════════════════════════════════════════════════════════
#  FLUJO DE AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════
if not st.session_state['autenticado']:
    _, col_login, _ = st.columns([1, 1.1, 1])

    with col_login:
        st.markdown("<div style='margin-top:8vh;'></div>", unsafe_allow_html=True)

        # Logo / título
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:32px;">
              <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;
                font-weight:600;letter-spacing:3px;color:#8B949E;
                text-transform:uppercase;margin-bottom:8px;">
                Sistema de Auditoría
              </p>
              <h1 style="font-family:'IBM Plex Mono',monospace;font-size:36px;
                font-weight:700;color:#E6EDF3;letter-spacing:-1px;margin:0;">
                T.A.L.O.N
              </h1>
              <p style="font-family:'IBM Plex Sans',sans-serif;font-size:12px;
                color:#484F58;margin-top:6px;letter-spacing:.3px;">
                Tablero Analítico de Limpieza y Orquestación de Negocios
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not st.session_state['mostrar_registro']:
            st.markdown(
                "<p class='t-label' style='margin-bottom:20px;'>Acceso a la plataforma</p>",
                unsafe_allow_html=True,
            )
            with st.form("formulario_login"):
                correo_login   = st.text_input("Correo corporativo",
                                               placeholder=f"usuario{dominio_oficial}")
                password_login = st.text_input("Contraseña", type="password")
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("INICIAR SESIÓN",
                                         type="primary",
                                         use_container_width=True):
                    if validar_credenciales(correo_login, password_login):
                        from infra.auth_manager import registrar_ingreso
                        registrar_ingreso(correo_login.lower())
                        st.session_state['autenticado']    = True
                        st.session_state['usuario_actual'] = correo_login.lower()
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")

            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            if st.button("¿Sin cuenta? Regístrate aquí",
                         use_container_width=True):
                st.session_state['mostrar_registro'] = True
                st.rerun()

        else:
            st.markdown(
                "<p class='t-label' style='margin-bottom:20px;'>Nuevo usuario</p>",
                unsafe_allow_html=True,
            )
            with st.form("formulario_registro"):
                correo_registro   = st.text_input("Correo corporativo",
                                                   placeholder=f"usuario{dominio_oficial}")
                password_registro = st.text_input("Crear contraseña", type="password")
                password_confirm  = st.text_input("Confirmar contraseña", type="password")
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("CREAR CUENTA",
                                         type="primary",
                                         use_container_width=True):
                    if password_registro != password_confirm:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        exito, mensaje = registrar_usuario(
                            correo_registro, password_registro, dominio_oficial
                        )
                        if exito:
                            st.success("Cuenta creada. Ya puedes iniciar sesión.")
                            st.session_state['mostrar_registro'] = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(mensaje)

            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            if st.button("← Volver al inicio de sesión",
                         use_container_width=True):
                st.session_state['mostrar_registro'] = False
                st.rerun()


# ═══════════════════════════════════════════════════════════════
#  ÁREA AUTENTICADA
# ═══════════════════════════════════════════════════════════════
else:
    def procesar_datos(datos_entrada, unidades, focos, dominio, reglas_ia):
        return ejecutar_auditoria_completa(datos_entrada, unidades,
                                           focos, dominio, reglas_ia)

    # ── Sidebar ──────────────────────────────────────────────
    with st.sidebar:
        # Marca / usuario
        st.markdown(
            f"""
            <div style="padding:16px 0 12px;">
              <p style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                font-weight:700;letter-spacing:2px;color:#E6EDF3;margin:0;">
                T.A.L.O.N
              </p>
              <p style="font-family:'IBM Plex Sans',sans-serif;font-size:11px;
                color:#484F58;margin:4px 0 0;">
                {st.session_state['usuario_actual']}
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown("<p class='t-label'>Configuración</p>", unsafe_allow_html=True)
        opciones_dominio = list(DOMINIOS_CONFIG.keys()) if DOMINIOS_CONFIG \
            else ["Maestro de Materiales", "Directorio Comercial"]
        dominio_seleccionado = st.radio("Dominio de datos", opciones_dominio,
                                        label_visibility="collapsed")

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        fuente_datos = st.radio("Fuente de datos",
                                ("Archivo Local (.xlsx)",
                                 "Conexión Directa (TalonDB)"),
                                label_visibility="collapsed")

        st.divider()

    # ── Carga de datos ───────────────────────────────────────
    archivo_subido = None
    datos_crudos   = None

    with st.sidebar:
        if fuente_datos == "Archivo Local (.xlsx)":
            archivo_subido = st.file_uploader("Cargar extracción", type=["xlsx"])
            if archivo_subido:
                archivo_subido.seek(0)
                hoja = "DATA" if dominio_seleccionado \
                    and "Directorio" in dominio_seleccionado else 0
                try:
                    datos_crudos = pd.read_excel(archivo_subido, sheet_name=hoja)
                except ValueError:
                    datos_crudos = pd.read_excel(archivo_subido, sheet_name=0)
                st.session_state['origen_datos'] = archivo_subido.name
        else:
            st.markdown(
                "<p style='font-size:11px;color:#8B949E;"
                "font-family:\"IBM Plex Sans\",sans-serif;'>☁ BigQuery / SAP</p>",
                unsafe_allow_html=True,
            )
            if st.button("Extraer Datos de TalonDB",
                         type="primary",
                         use_container_width=True):
                with st.spinner("Conectando a GCP..."):
                    try:
                        df_polars = extraer_maestro_materiales()
                        if df_polars is not None:
                            st.session_state['datos_crudos_bd'] = df_polars.to_pandas()
                            st.session_state['origen_datos'] = "TalonDB (BigQuery)"
                            st.success("Extracción exitosa.")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"{str(e)}")

        if 'datos_crudos_bd' in st.session_state:
            datos_crudos = st.session_state['datos_crudos_bd']

    # ── Botón IA ─────────────────────────────────────────────
    with st.sidebar:
        if datos_crudos is not None:
            st.divider()
            if st.button("Autoperfilar con IA",
                         use_container_width=True):
                with st.spinner("Analizando con Gemini..."):
                    texto_ia = generar_reglas_autonomas_ia(
                        datos_crudos, dominio_seleccionado
                    )
                    reglas_adaptadas = adaptar_reglas_ia_a_motor(
                        texto_ia, dominio_seleccionado
                    )
                    if reglas_adaptadas:
                        st.session_state['reglas_ia_dinamicas'] = reglas_adaptadas
                        st.success("Perfilamiento completado.")
                    else:
                        st.error("El traductor rechazó el formato de la IA.")
                    st.rerun()

    # ── Reglas IA en sidebar ─────────────────────────────────
    with st.sidebar:
        if st.session_state.get('reglas_ia_dinamicas'):
            st.divider()
            st.markdown("<p class='t-label'>Reglas activas de Talon</p>",
                        unsafe_allow_html=True)
            reglas_ia = st.session_state['reglas_ia_dinamicas']
            for foco, contenido in reglas_ia.items():
                nombre_menu = ("Reglas Generales (SKUs)"
                               if foco == "DEFAULT"
                               and "Directorio" not in dominio_seleccionado
                               else f"Reglas: {foco}")
                with st.expander(nombre_menu):
                    if isinstance(contenido, dict):
                        for dimension, reglas_dim in contenido.items():
                            if dimension == "pesos_dimensiones":
                                continue
                            if reglas_dim:
                                st.markdown(
                                    f"<p style='font-family:\"IBM Plex Mono\",monospace;"
                                    f"font-size:11px;font-weight:600;"
                                    f"color:#8B949E;margin-bottom:4px;'>{dimension}</p>",
                                    unsafe_allow_html=True,
                                )
                                for campo, config in reglas_dim.items():
                                    msg  = config.get('mensaje',      'Validación estricta')
                                    peso = config.get('penalizacion', 0)
                                    st.markdown(
                                        f"<p style='font-size:11px;color:#C9D1D9;"
                                        f"margin:2px 0;'>"
                                        f"<b>{campo}</b>: {msg} "
                                        f"<span style='color:#F85149;'>−{peso} pts</span></p>",
                                        unsafe_allow_html=True,
                                    )

    # ── Cuerpo principal ─────────────────────────────────────
    if datos_crudos is not None:
        reglas_actuales = st.session_state.get('reglas_ia_dinamicas')
        df_res, res_original = procesar_datos(
            datos_crudos, UNIDADES_REF, None, dominio_seleccionado, reglas_actuales
        )

        # Filtros
        materiales_presentes = []
        if 'tipo_mat' in df_res.columns:
            materiales_presentes = sorted([
                m for m in df_res['tipo_mat'].unique().tolist()
                if pd.notna(m) and m in NOMBRES_MATERIALES
            ])

        with st.sidebar:
            st.divider()
            st.markdown("<p class='t-label'>Enfoque</p>", unsafe_allow_html=True)
            filtro_mat = st.multiselect(
                "Filtrar Categoría",
                options=materiales_presentes,
                format_func=lambda x: NOMBRES_MATERIALES.get(x, x),
                placeholder="Analizar todo",
                label_visibility="collapsed",
            )
            st.divider()
            if st.button("Cerrar Sesión",
                         key="btn_cerrar_sesion_datos",
                         use_container_width=True):
                st.session_state.clear()
                st.rerun()

        df_display  = df_res[df_res['tipo_mat'].isin(filtro_mat)] if filtro_mat else df_res
        total_disp  = len(df_display)

        if total_disp > 0:
            res_dinamico = {
                'score_global': df_display['Score_Calidad'].mean(),
                'completitud':  df_display['Score_Completitud'].mean(),
                'validez':      df_display['Score_Validez'].mean(),
                'unicidad':     df_display['Score_Unicidad'].mean(),
                'consistencia': df_display['Score_Consistencia'].mean(),
            }
        else:
            res_dinamico = {k: 0.0 for k in
                            ['score_global', 'completitud', 'validez',
                             'unicidad', 'consistencia']}

        # Guardado en data lake
        nombre_origen = st.session_state.get('origen_datos', "Sin_Nombre")
        if ('id_ejecucion' not in st.session_state
                or st.session_state.get('last_file') != nombre_origen):
            st.session_state['id_ejecucion'] = guardar_auditoria(
                df_display, st.session_state['usuario_actual'],
                dominio_seleccionado, res_dinamico, filtro_mat
            )
            st.session_state['last_file'] = nombre_origen

        # ── Header de la vista ────────────────────────────────
        col_hdr, col_hdr2 = st.columns([3, 1])
        with col_hdr:
            origen_label = st.session_state.get('origen_datos', '—')
            st.markdown(
                f"""
                <div style="margin-bottom:4px;">
                  <p class='t-label' style='margin-bottom:4px;'></p>
                  <h2 style="font-family:'IBM Plex Mono',monospace;font-size:20px;
                    font-weight:700;color:#E6EDF3;margin:0;letter-spacing:-0.3px;">
                    {dominio_seleccionado}
                  </h2>
                  <p style="font-family:'IBM Plex Sans',sans-serif;font-size:12px;
                    color:#484F58;margin:4px 0 0;">
                    {total_disp:,} registros · {origen_label}
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Aviso sin reglas IA ───────────────────────────────
        if not st.session_state.get('reglas_ia_dinamicas'):
            st.markdown(
                f"<div class='talon-card-accent' style='"
                f"border-left-color:#D29922;margin-bottom:20px;'>"
                f"<p style='font-family:\"IBM Plex Sans\",sans-serif;"
                f"font-size:12px;color:#D29922;margin:0;'>"
                f"Sin reglas de IA cargadas — ejecuta <b>Autoperfilar con IA</b> "
                f"en el panel izquierdo para activar los scores completos.</p></div>",
                unsafe_allow_html=True,
            )

        # ── Métricas ──────────────────────────────────────────
        renderizar_metricas(res_dinamico)

        # ── Acciones ──────────────────────────────────────────
        col_acc1, col_acc2, col_acc3 = st.columns([1, 1, 2])

        excel_bytes = generar_excel_saneamiento_memoria(df_display)

        with col_acc1:
            st.download_button(
                label="Exportar Saneamiento (.xlsx)",
                data=excel_bytes,
                file_name=f"TALON_Saneamiento_{int(time.time())}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_acc2:
            key_custodio    = filtro_mat[0] if len(filtro_mat) == 1 else "DEFAULT"
            sugerencia_correo = CUSTODIOS.get(key_custodio, "gobiernodatos@brinsa.com.co")

            with st.popover("Notificar Custodio", use_container_width=True):
                st.markdown(
                    "<p class='t-label' style='margin-bottom:12px;'>Enviar reporte</p>",
                    unsafe_allow_html=True,
                )
                correo_destino = st.text_input("Correo del responsable",
                                               value=sugerencia_correo)
                if st.button("Enviar Excel", type="primary",
                             use_container_width=True):
                    if not correo_destino or "@" not in correo_destino:
                        st.error("Ingresa un correo válido.")
                    else:
                        with st.spinner("Enviando..."):
                            from infra.notificador import enviar_correo_talon
                            errores_totales = len(
                                df_display[df_display['Score_Calidad'] < 100]
                            )
                            exito, mensaje = enviar_correo_talon(
                                correo_custodio=correo_destino,
                                correo_auditor=st.session_state['usuario_actual'],
                                dominio=dominio_seleccionado,
                                score=round(res_dinamico['score_global'], 1),
                                total_errores=errores_totales,
                                archivo_bytes=excel_bytes,
                            )
                            if exito:
                                st.success(f"Enviado a {correo_destino}.")
                            else:
                                st.error(f"Error: {mensaje}")

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # ── Pestañas principales ─────────────────────────────
        tab_dashboard, tab_ia, tab_datos, tab_historico = st.tabs([
            "Dashboard",
            "Asistente IA",
            "Explorador",
            "Historial",
        ])

        with tab_dashboard:
            col1, col2 = st.columns(2)
            with col1:
                renderizar_grafico_dimensiones(res_dinamico)
            with col2:
                renderizar_grafico_top_errores(df_display)
            renderizar_grafico_por_foco(df_display)

        with tab_ia:
            st.markdown(
                "<p class='t-label' style='margin-bottom:16px;'>"
                "Chat · Consultor Talon IA</p>",
                unsafe_allow_html=True,
            )

            if st.session_state.get('reglas_ia_dinamicas'):
                _, col_btn = st.columns([4, 1])
                with col_btn:
                    if st.button("Guardar como Reglas Prime",
                                 use_container_width=True):
                        resultado = guardar_reglas_prime(
                            st.session_state['reglas_ia_dinamicas'],
                            dominio_seleccionado,
                        )
                        st.success(resultado)

            contexto_str = ("Global" if not filtro_mat
                            else f"Filtro: {', '.join(filtro_mat)}")

            if (not st.session_state['chat_historial']
                    or st.session_state.get('ia_contexto_chat') != contexto_str):
                bienvenida = (
                    f"**Hola, soy Talon.**\n\n"
                    f"Analicé **{total_disp:,}** registros y detecté un score global "
                    f"de **{res_dinamico['score_global']:.1f}%**.\n\n"
                    f"¿Por dónde comenzamos? Puedo explicar las anomalías "
                    f"o ayudarte a ajustar las reglas de validación."
                )
                st.session_state['chat_historial']   = [{"role": "assistant",
                                                          "content": bienvenida}]
                st.session_state['ia_contexto_chat'] = contexto_str

            contenedor_mensajes = st.container(height=400)
            with contenedor_mensajes:
                for msg in st.session_state['chat_historial']:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            if prompt_usuario := st.chat_input(
                "Pregúntale a Talon sobre las anomalías..."
            ):
                st.session_state['chat_historial'].append(
                    {"role": "user", "content": prompt_usuario}
                )
                with contenedor_mensajes:
                    with st.chat_message("user"):
                        st.markdown(prompt_usuario)
                    with st.chat_message("assistant"):
                        respuesta_ia = responder_chat_ia(
                            prompt_usuario,
                            df_display.head(5),
                            contexto_str,
                            st.session_state['chat_historial'][:-1],
                        )
                        st.markdown(respuesta_ia)
                        st.session_state['chat_historial'].append(
                            {"role": "assistant", "content": respuesta_ia}
                        )
                st.rerun()

        with tab_datos:
            try:
                renderizar_tabla_hallazgos(df_display)
            except Exception as e:
                st.error(f"Error técnico en la tabla: {e}")

        with tab_historico:
            df_hist = obtener_historial_metricas()
            if not df_hist.empty:
                st.markdown(
                    "<p class='t-label' style='margin-bottom:12px;'>"
                    "Auditorías registradas</p>",
                    unsafe_allow_html=True,
                )
                st.dataframe(
                    df_hist[['fecha', 'usuario', 'dominio',
                              'score_global', 'total_registros']],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.markdown(
                    "<div class='talon-card-accent' style='border-left-color:#484F58;'>"
                    "<p style='font-size:12px;color:#8B949E;margin:0;font-family:"
                    "\"IBM Plex Sans\",sans-serif;'>"
                    "Aún no hay auditorías registradas.</p></div>",
                    unsafe_allow_html=True,
                )

    # ── Pantalla de espera (sin datos) ───────────────────────
    else:
        with st.sidebar:
            st.divider()
            if st.button("Cerrar Sesión",
                         key="btn_cerrar_sesion_vacio",
                         use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.markdown(
            """
            <div style="text-align:center;margin-top:18vh;">
              <p style="font-family:'IBM Plex Mono',monospace;font-size:40px;
                color:#30363D;margin-bottom:16px;"></p>
              <h2 style="font-family:'IBM Plex Mono',monospace;font-size:18px;
                font-weight:700;color:#484F58;letter-spacing:-0.3px;margin:0;">
                Talon está listo
              </h2>
              <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13px;
                color:#30363D;margin-top:8px;max-width:320px;display:inline-block;">
                Usa el panel izquierdo para cargar tu extracción<br>
                de datos y comenzar la auditoría.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )