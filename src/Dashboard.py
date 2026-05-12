import streamlit as st

# --- CANDADO DE SEGURIDAD ---
if not st.session_state.get("connected"):
    st.warning("Acceso denegado. Por favor inicia sesión primero.")
    st.switch_page("app.py")
    st.stop()

import pandas as pd
import polars as pl
import time
import threading

try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx
except ImportError:
    from streamlit.scriptrunner import add_script_run_ctx

from config import DOMINIOS_CONFIG, UNIDADES_REF, CUSTODIOS, NOMBRES_MATERIALES
from core.motor_calidad import adaptar_reglas_ia_a_motor, ejecutar_auditoria_completa, generar_excel_saneamiento_memoria
from core.motor_ia import responder_chat_ia, generar_reglas_autonomas_ia, guardar_reglas_prime
from ui.ui_components import (renderizar_metricas, renderizar_grafico_dimensiones,
                               renderizar_tabla_hallazgos, renderizar_tabla_top_errores,
                               renderizar_grafico_por_foco, mostrar_placeholder_grafica)
from ui.theme import inject_global_css
from infra.datalake_manager import inicializar_datalake, guardar_auditoria, obtener_historial_metricas
from infra.auth_manager import inicializar_tabla_usuarios
from infra.bigquery_client import (extraer_materiales_pendientes, cargar_resultados_auditoria,
                                    extraer_anomalias_pendientes, actualizar_fechas_materiales)


def mostrar_panel_principal():
    user_info      = st.session_state.get('user_info', {})
    st.session_state['usuario_actual'] = user_info.get('email', 'Usuario SSO')
    nombre_usuario = user_info.get('name', 'Auditor')

    # ── AJUSTES DE USUARIO (idioma) ────────────────────────────────
    if 'idioma' not in st.session_state:
        st.session_state['idioma'] = 'es'

    _T = {
        'es': {
            'config':       'Configuración',
            'dominio':      'Dominio de datos',
            'fuente':       'Fuente de datos',
            'directa':      'Conexión Directa (TalonDB)',
            'local':        'Archivo Local (.xlsx)',
            'panel_titulo': '☁ TalonDB — Panel de Gobierno',
            'panel_desc':   'Detecta registros nuevos en SAP, los audita\ny carga el tablero de anomalías pendientes.',
            'btn_sync':     '⟳  Sincronizar y Cargar Tablero',
            'btn_sync_help':'Busca registros nuevos en SAP, los audita en segundo plano y carga las anomalías pendientes.',
            'ultima_sync':  'Última sync',
            'iniciando':    'Iniciando tablero — conectando con TalonDB…',
            'autoperfilar': 'Autoperfilar con IA',
            'cargar':       'Cargar extracción',
            'enfoque':      'Enfoque',
            'filtro_cat':   'Filtrar Categoría',
            'todo':         'Analizar todo',
            'reglas_title': 'Reglas activas de Talon',
            'cerrar':       'Cerrar Sesión',
            'paso1':            'Paso 1/2 — Buscando registros nuevos en SAP…',
            'paso2':            'Paso 2/2 — Cargando anomalías pendientes desde BigQuery…',
            'tab_explorer':     'Explorador',
            'tab_dashboard':    'Dashboard',
            'tab_ia':           'Asistente IA',
            'tab_historial':    'Historial',
            'exportar':         '⬇  Exportar Saneamiento (.xlsx)',
            'notificar':        'Notificar Custodio',
            'enviar_reporte':   'Enviar reporte',
            'correo_resp':      'Correo del responsable',
            'enviar_excel':     'Enviar Excel',
            'sin_reglas':       'Sin reglas de IA cargadas — ejecuta <b>Autoperfilar con IA</b> para activar los scores completos.',
            'guardar_prime':    'Guardar como Reglas Prime',
            'registros_lbl':    'registros',
            'chat_label':       'Chat · Consultor Talon IA',
            'chat_bienvenida':  '**Hola, soy Talon.**\n\nAnalicé **{n:,}** registros y detecté un score global de **{s:.1f}%**.\n\n¿Por dónde comenzamos? Puedo explicar las anomalías o ayudarte a ajustar las reglas de validación.',
            'chat_input':       'Pregúntale a Talon sobre las anomalías…',
            'sin_anomalias_ok': '¡Felicidades! No se encontraron anomalías pendientes.',
            'auditorias_reg':   'Auditorías registradas',
            'sin_auditorias':   'Aún no hay auditorías registradas.',
            'conectando_auto':  '⟳ &nbsp;Conectando con TalonDB — los datos aparecerán automáticamente…',
            'cargando_auto':    '⟳ &nbsp;Cargando datos desde TalonDB…',
            'sin_datos_exp':    'El explorador de anomalías aparecerá aquí una vez se carguen los datos.',
            'sin_datos_ia':     'El asistente IA estará disponible tras cargar los datos.',
        },
        'en': {
            'config':       'Configuration',
            'dominio':      'Data domain',
            'fuente':       'Data source',
            'directa':      'Direct Connection (TalonDB)',
            'local':        'Local File (.xlsx)',
            'panel_titulo': '☁ TalonDB — Control Panel',
            'panel_desc':   'Detects new SAP records, audits them\nand loads the anomaly dashboard.',
            'btn_sync':     '⟳  Sync and Load Dashboard',
            'btn_sync_help':'Finds new SAP records, audits them in background and loads the anomaly dashboard.',
            'ultima_sync':  'Last sync',
            'iniciando':    'Starting dashboard — connecting to TalonDB…',
            'autoperfilar': 'AI Auto-profile',
            'cargar':       'Load extract',
            'enfoque':      'Focus',
            'filtro_cat':   'Filter Category',
            'todo':         'Analyze all',
            'reglas_title': 'Active Talon Rules',
            'cerrar':       'Sign Out',
            'paso1':            'Step 1/2 — Searching for new SAP records…',
            'paso2':            'Step 2/2 — Loading pending anomalies from BigQuery…',
            'tab_explorer':     'Explorer',
            'tab_dashboard':    'Dashboard',
            'tab_ia':           'AI Assistant',
            'tab_historial':    'History',
            'exportar':         '⬇  Export Remediation (.xlsx)',
            'notificar':        'Notify Custodian',
            'enviar_reporte':   'Send report',
            'correo_resp':      'Responsible email',
            'enviar_excel':     'Send Excel',
            'sin_reglas':       'No AI rules loaded — run <b>AI Auto-profile</b> to enable full scoring.',
            'guardar_prime':    'Save as Prime Rules',
            'registros_lbl':    'records',
            'chat_label':       'Chat · Talon AI Consultant',
            'chat_bienvenida':  '**Hello, I\'m Talon.**\n\nI analyzed **{n:,}** records and detected a global score of **{s:.1f}%**.\n\nWhere shall we start? I can explain anomalies or help you adjust validation rules.',
            'chat_input':       'Ask Talon about the anomalies…',
            'sin_anomalias_ok': 'Congratulations! No pending anomalies were found.',
            'auditorias_reg':   'Registered audits',
            'sin_auditorias':   'No audits registered yet.',
            'conectando_auto':  '⟳ &nbsp;Connecting to TalonDB — data will appear automatically…',
            'cargando_auto':    '⟳ &nbsp;Loading data from TalonDB…',
            'sin_datos_exp':    'The anomaly explorer will appear here once data is loaded.',
            'sin_datos_ia':     'The AI assistant will be available after loading data.',
        },
    }
    L = _T[st.session_state['idioma']]

    # ── FUNCIONES INTERNAS ──────────────────────────────────────────
    def ejecutar_auditoria_background(df_pendientes, dominio, reglas):
        try:
            df_auditado, _ = ejecutar_auditoria_completa(
                df_pendientes, UNIDADES_REF, None, dominio, reglas
            )
            df_pandas = (
                df_auditado.to_pandas()
                if isinstance(df_auditado, pl.DataFrame)
                else df_auditado.copy()
            )
            st.session_state['datos_crudos_bd'] = df_pandas
            st.session_state['origen_datos']    = "TalonDB (BigQuery)"
            try:
                cargar_resultados_auditoria(df_auditado)
            except Exception as e_bq:
                print(f"ERROR AL GUARDAR EN BIGQUERY: {e_bq}")
        except Exception as e:
            print(f"ERROR FATAL EN EL MOTOR: {e}")

    def procesar_datos(datos_entrada, unidades, focos, dominio, reglas_ia):
        return ejecutar_auditoria_completa(datos_entrada, unidades, focos, dominio, reglas_ia)

    # Inicializar servicios
    inicializar_datalake()
    inicializar_tabla_usuarios()

    # ══════════════════════════════════════════════════════════════
    #  CSS GLOBAL — Sistema de Diseño Enterprise Slate / Azure
    # ══════════════════════════════════════════════════════════════
    inject_global_css()

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] > div:first-child {
            display: flex;
            flex-direction: column;
        }
        .talon-dev-footer {
            margin-top: auto;
            padding: 12px 16px 8px;
            border-top: 1px solid #1E2530;
        }
        .talon-dev-footer p { margin: 0; line-height: 1.5; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════════════════════════
    _text_color  = "#F1F5F9"
    _sub_color   = "#94A3B8"
    _email_color = "#475569"

    with st.sidebar:
        # ── Encabezado usuario ────────────────────────────────────
        st.markdown(
            f"""
            <div style="padding:4px 0 6px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                <div style="width:6px;height:6px;border-radius:50%;background:#3B82F6;
                            box-shadow:0 0 6px rgba(59,130,246,0.7);
                            animation:pulse 2.4s ease-in-out infinite;flex-shrink:0;"></div>
                <p style="font-family:'IBM Plex Mono',monospace;font-size:15px;
                  font-weight:700;letter-spacing:2px;color:{_text_color};margin:0;">
                  T.A.L.O.N
                </p>
              </div>
              <p style="font-family:'IBM Plex Sans',sans-serif;font-size:11px;
                color:{_sub_color};margin:0 0 2px 16px;line-height:1.5;">
                {nombre_usuario}
              </p>
              <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;
                color:{_email_color};margin:0 0 0 16px;letter-spacing:.3px;">
                {st.session_state['usuario_actual']}
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown(f"<p class='t-label'>{L['config']}</p>", unsafe_allow_html=True)
        opciones_dominio  = list(DOMINIOS_CONFIG.keys()) if DOMINIOS_CONFIG else ["Maestro de Materiales", "Directorio Comercial"]
        dominio_seleccionado = st.radio(L['dominio'], opciones_dominio, label_visibility="collapsed")

        st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)
        fuente_datos = st.radio(
            L['fuente'],
            (L['directa'], L['local']),
            label_visibility="collapsed",
        )
        st.divider()

    # ── CARGA DE DATOS ─────────────────────────────────────────────
    archivo_subido = None
    datos_crudos   = None

    with st.sidebar:
        if fuente_datos == L['local']:
            archivo_subido = st.file_uploader(L['cargar'], type=["xlsx"])
            if archivo_subido:
                archivo_subido.seek(0)
                hoja = "DATA" if dominio_seleccionado and "Directorio" in dominio_seleccionado else 0
                try:
                    datos_crudos = pd.read_excel(archivo_subido, sheet_name=hoja)
                except ValueError:
                    datos_crudos = pd.read_excel(archivo_subido, sheet_name=0)
                st.session_state['origen_datos'] = archivo_subido.name

        else:
            # ── BOTÓN ÚNICO: SINCRONIZAR + CARGAR ────────────────
            st.markdown(
                f"""
                <p class='t-label' style='margin-bottom:8px;'>{L['panel_titulo']}</p>
                <p style='font-size:11px;color:#484F58;font-family:"IBM Plex Sans",sans-serif;
                   margin-bottom:12px;line-height:1.5;'>
                  {L['panel_desc'].replace(chr(10), '<br>')}
                </p>
                """,
                unsafe_allow_html=True,
            )

            # ── CARGA AUTOMÁTICA AL INICIO DE SESIÓN ─────────────
            if (
                'datos_crudos_bd' not in st.session_state
                and not st.session_state.get('_auto_carga_intento')
            ):
                st.session_state['_auto_carga_intento'] = True
                with st.spinner(L['iniciando']):
                    try:
                        df_malos_auto = extraer_anomalias_pendientes()
                        if df_malos_auto is not None and len(df_malos_auto) > 0:
                            st.session_state['datos_crudos_bd'] = df_malos_auto.to_pandas()
                            st.session_state['origen_datos']    = "TalonDB (Pendientes)"
                            st.session_state['ultima_sync']     = time.strftime("%H:%M")
                            st.rerun()
                        else:
                            st.session_state['ultima_sync'] = time.strftime("%H:%M")
                    except Exception as e_auto:
                        st.caption(f"⚠ Auto-carga: {str(e_auto)[:80]}")

            # Estado de la última sincronización
            ultima_sync = st.session_state.get('ultima_sync', None)
            if ultima_sync:
                st.markdown(
                    f"<div class='sync-status'><div class='sync-dot'></div>"
                    f"{L['ultima_sync']}: {ultima_sync}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<div class='btn-sync'>", unsafe_allow_html=True)
            btn_sync = st.button(
                L['btn_sync'],
                type="primary",
                width='stretch',
                help=L['btn_sync_help'],
            )
            st.markdown("</div>", unsafe_allow_html=True)

            if btn_sync:
                with st.spinner(L['paso1']):
                    # Caso A: SKUs nuevos → auditar e insertar
                    df_pendientes = extraer_materiales_pendientes()
                    if df_pendientes is not None and len(df_pendientes) > 0:
                        reglas_activas = st.session_state.get('reglas_ia_dinamicas')
                        hilo = threading.Thread(
                            target=ejecutar_auditoria_background,
                            args=(df_pendientes, dominio_seleccionado, reglas_activas),
                        )
                        add_script_run_ctx(hilo)
                        hilo.start()
                        st.toast(f"✓ {len(df_pendientes)} registros nuevos enviados al motor de auditoría", icon="🔄")
                    else:
                        st.toast("Todo al día — sin registros nuevos en SAP", icon="✅")

                    # Caso B: SKUs existentes con fecha_actualiza cambiada → UPDATE
                    try:
                        filas_actualizadas = actualizar_fechas_materiales()
                        if filas_actualizadas > 0:
                            st.toast(f"↻ {filas_actualizadas} registros actualizados por cambio de fecha", icon="🔁")
                    except Exception as e_upd:
                        st.toast(f"Aviso: no se pudo actualizar fechas — {e_upd}", icon="⚠️")

                with st.spinner(L['paso2']):
                    try:
                        df_malos = extraer_anomalias_pendientes()
                        if df_malos is not None and len(df_malos) > 0:
                            st.session_state['datos_crudos_bd'] = df_malos.to_pandas()
                            st.session_state['origen_datos']    = "TalonDB (Pendientes)"
                            st.session_state['ultima_sync']     = time.strftime("%H:%M")
                            st.success(f"✓ {len(df_malos):,} registros cargados para gestión.")
                            st.rerun()
                        else:
                            st.session_state['ultima_sync'] = time.strftime("%H:%M")
                            st.success("¡Sin anomalías pendientes! El maestro está limpio.")
                    except Exception as e:
                        st.error(f"Error al cargar el tablero: {str(e)}")

        if datos_crudos is None and 'datos_crudos_bd' in st.session_state:
            datos_crudos = st.session_state['datos_crudos_bd']

    # ── BOTÓN IA ────────────────────────────────────────────────────
    with st.sidebar:
        if datos_crudos is not None:
            st.divider()
            if st.button(L['autoperfilar'], width='stretch'):
                with st.spinner("Analizando con Gemini…"):
                    texto_ia       = generar_reglas_autonomas_ia(datos_crudos, dominio_seleccionado)
                    reglas_adapt   = adaptar_reglas_ia_a_motor(texto_ia, dominio_seleccionado)
                    if reglas_adapt:
                        st.session_state['reglas_ia_dinamicas'] = reglas_adapt
                        st.success("Perfilamiento completado.")
                    else:
                        st.error("El traductor rechazó el formato de la IA.")
                    st.rerun()

    # ── REGLAS IA ACTIVAS ────────────────────────────────────────────
    with st.sidebar:
        if st.session_state.get('reglas_ia_dinamicas'):
            st.divider()
            st.markdown(f"<p class='t-label'>{L['reglas_title']}</p>", unsafe_allow_html=True)
            reglas_ia = st.session_state['reglas_ia_dinamicas']
            for foco, contenido in reglas_ia.items():
                nombre_menu = (
                    "Reglas Generales (SKUs)"
                    if foco == "DEFAULT" and "Directorio" not in dominio_seleccionado
                    else f"Reglas: {foco}"
                )
                with st.expander(nombre_menu):
                    if isinstance(contenido, dict):
                        for dimension, reglas_dim in contenido.items():
                            if dimension == "pesos_dimensiones" or not reglas_dim:
                                continue
                            st.markdown(
                                f"<p style='font-family:\"IBM Plex Mono\",monospace;font-size:11px;"
                                f"font-weight:600;color:#3B82F6;margin-bottom:4px;letter-spacing:.6px;'>{dimension}</p>",
                                unsafe_allow_html=True,
                            )
                            for campo, config in reglas_dim.items():
                                msg  = config.get('mensaje', 'Validación estricta')
                                peso = config.get('penalizacion', 0)
                                st.markdown(
                                    f"<p style='font-size:11px;color:#CBD5E1;margin:2px 0;'>"
                                    f"<b>{campo}</b>: {msg} "
                                    f"<span style='color:#60A5FA;font-family:IBM Plex Mono,monospace;'>−{peso} pts</span></p>",
                                    unsafe_allow_html=True,
                                )

    # ══════════════════════════════════════════════════════════════
    #  CUERPO PRINCIPAL — SIEMPRE visible (con o sin datos)
    # ══════════════════════════════════════════════════════════════
    if datos_crudos is not None:
        # ── Procesar datos ───────────────────────────────────────
        reglas_actuales = st.session_state.get('reglas_ia_dinamicas')
        df_res, res_original = procesar_datos(
            datos_crudos, UNIDADES_REF, None, dominio_seleccionado, reglas_actuales
        )

        materiales_presentes = []
        if 'tipo_mat' in df_res.columns:
            materiales_presentes = sorted([
                m for m in df_res['tipo_mat'].unique().tolist()
                if pd.notna(m) and m in NOMBRES_MATERIALES
            ])

        with st.sidebar:
            st.divider()
            st.markdown(f"<p class='t-label'>{L['enfoque']}</p>", unsafe_allow_html=True)
            filtro_mat = st.multiselect(
                L['filtro_cat'],
                options=materiales_presentes,
                format_func=lambda x: NOMBRES_MATERIALES.get(x, x),
                placeholder=L['todo'],
                label_visibility="collapsed",
            )
            st.divider()
            if st.button(L['cerrar'], key="btn_cerrar_sesion_datos", width='stretch'):
                st.session_state.clear()
                st.rerun()

        df_display = df_res[df_res['tipo_mat'].isin(filtro_mat)] if filtro_mat else df_res
        total_disp = len(df_display)

        res_dinamico = (
            {
                'score_global': df_display['Score_Calidad'].mean(),
                'completitud':  df_display['Score_Completitud'].mean(),
                'validez':      df_display['Score_Validez'].mean(),
                'unicidad':     df_display['Score_Unicidad'].mean(),
                'consistencia': df_display['Score_Consistencia'].mean(),
            }
            if total_disp > 0
            else {k: 0.0 for k in ['score_global', 'completitud', 'validez', 'unicidad', 'consistencia']}
        )

        nombre_origen = st.session_state.get('origen_datos', "Sin_Nombre")
        if 'id_ejecucion' not in st.session_state or st.session_state.get('last_file') != nombre_origen:
            st.session_state['id_ejecucion'] = guardar_auditoria(
                df_display, st.session_state['usuario_actual'],
                dominio_seleccionado, res_dinamico, filtro_mat,
            )
            st.session_state['last_file'] = nombre_origen

        # ── Encabezado ───────────────────────────────────────────
        col_hdr, col_hdr2 = st.columns([3, 1])
        with col_hdr:
            origen_label = st.session_state.get('origen_datos', '—')
            st.markdown(
                f"""<div style="margin-bottom:4px;">
                  <p class='t-label' style='margin-bottom:4px;'></p>
                  <h2 style="font-family:'IBM Plex Mono',monospace;font-size:20px;
                    font-weight:700;color:{_text_color};margin:0;letter-spacing:-0.3px;">
                    {dominio_seleccionado}
                  </h2>
                  <p style="font-family:'IBM Plex Sans',sans-serif;font-size:12px;
                    color:{_email_color};margin:4px 0 0;">
                    {total_disp:,} {L['registros_lbl']} · {origen_label}
                  </p>
                </div>""",
                unsafe_allow_html=True,
            )

        if not st.session_state.get('reglas_ia_dinamicas'):
            st.markdown(
                "<div class='talon-card-accent' style='border-left-color:#D29922;margin-bottom:20px;'>"
                f"<p style='font-family:\"IBM Plex Sans\",sans-serif;font-size:12px;color:#D29922;margin:0;'>"
                f"{L['sin_reglas']}"
                "</p></div>",
                unsafe_allow_html=True,
            )

        renderizar_metricas(res_dinamico)

        # ── Acciones ─────────────────────────────────────────────
        col_acc1, col_acc2, _ = st.columns([3, 2, 1])
        excel_bytes = generar_excel_saneamiento_memoria(df_display)

        with col_acc1:
            st.markdown('<div class="btn-exportar">', unsafe_allow_html=True)
            st.download_button(
                label=L['exportar'],
                data=excel_bytes,
                file_name=f"TALON_Saneamiento_{int(time.time())}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                width='stretch',
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_acc2:
            key_custodio       = filtro_mat[0] if len(filtro_mat) == 1 else "DEFAULT"
            sugerencia_correo  = CUSTODIOS.get(key_custodio, "gobiernodatos@brinsa.com.co")
            st.markdown('<div class="btn-notificar">', unsafe_allow_html=True)
            with st.popover(L['notificar'], width='stretch'):
                st.markdown(f"<p class='t-label' style='margin-bottom:12px;'>{L['enviar_reporte']}</p>", unsafe_allow_html=True)
                correo_destino = st.text_input(L['correo_resp'], value=sugerencia_correo)
                if st.button(L['enviar_excel'], type="primary", width='stretch'):
                    if not correo_destino or "@" not in correo_destino:
                        _msg_correo = "Ingresa un correo válido." if st.session_state.get('idioma', 'es') == 'es' else "Enter a valid email."
                        st.error(_msg_correo)
                    else:
                        with st.spinner("Enviando…"):
                            from infra.notificador import enviar_correo_talon
                            errores_totales = len(df_display[df_display['Score_Calidad'] < 100])
                            exito, mensaje  = enviar_correo_talon(
                                correo_custodio=correo_destino,
                                correo_auditor=st.session_state['usuario_actual'],
                                dominio=dominio_seleccionado,
                                score=round(res_dinamico['score_global'], 1),
                                total_errores=errores_totales,
                                archivo_bytes=excel_bytes,
                            )
                            if exito: st.success(f"Enviado a {correo_destino}.")
                            else:     st.error(f"Error: {mensaje}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════
        #  PESTAÑAS — orden: Explorador · Dashboard · IA · Historial
        # ══════════════════════════════════════════════════════
        tab_datos, tab_dashboard, tab_ia, tab_historico = st.tabs([
            L['tab_explorer'], L['tab_dashboard'], L['tab_ia'], L['tab_historial'],
        ])

        # ── EXPLORADOR (primera pestaña) ──────────────────────
        with tab_datos:
            try:
                df_solo_fallas = df_display[df_display['Estado_Gestion'] == 0]
                if not df_solo_fallas.empty:
                    renderizar_tabla_hallazgos(df_solo_fallas)
                else:
                    st.success(L['sin_anomalias_ok'])
            except Exception as e:
                st.error(f"Error técnico en la tabla: {e}")

        # ── DASHBOARD ─────────────────────────────────────────
        with tab_dashboard:
            col1, col2 = st.columns(2)
            with col1: renderizar_grafico_dimensiones(res_dinamico)
            with col2: renderizar_tabla_top_errores(df_display)
            renderizar_grafico_por_foco(df_display)

        # ── ASISTENTE IA ──────────────────────────────────────
        with tab_ia:
            st.markdown(f"<p class='t-label' style='margin-bottom:16px;'>{L['chat_label']}</p>", unsafe_allow_html=True)
            if st.session_state.get('reglas_ia_dinamicas'):
                _, col_btn = st.columns([4, 1])
                with col_btn:
                    if st.button(L['guardar_prime'], width='stretch'):
                        resultado = guardar_reglas_prime(st.session_state['reglas_ia_dinamicas'], dominio_seleccionado)
                        st.success(resultado)

            contexto_str = "Global" if not filtro_mat else f"Filtro: {', '.join(filtro_mat)}"
            if (
                not st.session_state.get('chat_historial')
                or st.session_state.get('ia_contexto_chat') != contexto_str
            ):
                bienvenida = L['chat_bienvenida'].format(n=total_disp, s=res_dinamico['score_global'])
                st.session_state['chat_historial']   = [{"role": "assistant", "content": bienvenida}]
                st.session_state['ia_contexto_chat'] = contexto_str

            contenedor_mensajes = st.container(height=400)
            with contenedor_mensajes:
                for msg in st.session_state['chat_historial']:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            if prompt_usuario := st.chat_input(L['chat_input']):
                st.session_state['chat_historial'].append({"role": "user", "content": prompt_usuario})
                with contenedor_mensajes:
                    with st.chat_message("user"):
                        st.markdown(prompt_usuario)
                    with st.chat_message("assistant"):
                        respuesta_ia = responder_chat_ia(
                            prompt_usuario, df_display.head(5),
                            contexto_str, st.session_state['chat_historial'][:-1],
                        )
                        st.markdown(respuesta_ia)
                        st.session_state['chat_historial'].append({"role": "assistant", "content": respuesta_ia})
                st.rerun()

        # ── HISTORIAL ─────────────────────────────────────────
        with tab_historico:
            df_hist = obtener_historial_metricas()
            if not df_hist.empty:
                st.markdown(f"<p class='t-label' style='margin-bottom:12px;'>{L['auditorias_reg']}</p>", unsafe_allow_html=True)
                st.dataframe(
                    df_hist[['fecha', 'usuario', 'dominio', 'score_global', 'total_registros']],
                    width='stretch', hide_index=True,
                )
            else:
                st.markdown(
                    "<div class='talon-card-accent' style='border-left-color:#484F58;'>"
                    f"<p style='font-size:12px;color:#8B949E;margin:0;font-family:\"IBM Plex Sans\",sans-serif;'>"
                    f"{L['sin_auditorias']}</p></div>",
                    unsafe_allow_html=True,
                )

    # ══════════════════════════════════════════════════════════════
    #  PANTALLA DE ESPERA — Sin datos cargados
    #  Las gráficas se pre-inicializan en 0 de forma reactiva
    # ══════════════════════════════════════════════════════════════
    else:
        with st.sidebar:
            st.divider()
            if st.button(L['cerrar'], key="btn_cerrar_sesion_vacio", width='stretch'):
                st.session_state.clear()
                st.rerun()

        # Valores base en cero para pre-inicializar las gráficas
        res_vacio = {k: 0.0 for k in ['score_global', 'completitud', 'validez', 'unicidad', 'consistencia']}

        # ── Banner de estado según si la auto-carga está en curso ─
        _auto_en_curso = (
            fuente_datos == L['directa']
            and st.session_state.get('_auto_carga_intento')
            and 'datos_crudos_bd' not in st.session_state
        )
        if _auto_en_curso:
            st.markdown(
                "<div class='talon-card-accent' style='border-left-color:#3B82F6;margin-bottom:12px;'>"
                f"<p style='font-size:12px;color:#3B82F6;margin:0;font-family:\"IBM Plex Sans\",sans-serif;'>"
                f"{L['conectando_auto']}"
                "</p></div>",
                unsafe_allow_html=True,
            )

        # Métricas pre-inicializadas en 0
        renderizar_metricas(res_vacio)

        # ── Pestañas vacías pero visibles ─────────────────────
        tab_datos, tab_dashboard, tab_ia, tab_historico = st.tabs([
            L['tab_explorer'], L['tab_dashboard'], L['tab_ia'], L['tab_historial'],
        ])

        _msg_espera  = L['cargando_auto'] if _auto_en_curso else L['sin_datos_exp']
        _color_borde = "#3B82F6" if _auto_en_curso else "#30363D"
        _color_texto = "#3B82F6" if _auto_en_curso else _email_color

        with tab_datos:
            st.markdown(
                f"<div class='talon-card-accent' style='border-left-color:{_color_borde};'>"
                f"<p style='font-size:12px;color:{_color_texto};margin:0;font-family:\"IBM Plex Sans\",sans-serif;'>"
                f"{_msg_espera}"
                "</p></div>",
                unsafe_allow_html=True,
            )

        from ui.ui_components import _lbl as _comp_lbl
        with tab_dashboard:
            col1, col2 = st.columns(2)
            with col1:
                renderizar_grafico_dimensiones(res_vacio)
            with col2:
                mostrar_placeholder_grafica(_comp_lbl('top_anomalias'), _comp_lbl('sin_datos_anom'))
            mostrar_placeholder_grafica(_comp_lbl('calidad_mat'), _comp_lbl('sin_datos_mat'))

        with tab_ia:
            st.markdown(
                "<div class='talon-card-accent' style='border-left-color:#30363D;'>"
                f"<p style='font-size:12px;color:{_email_color};margin:0;font-family:\"IBM Plex Sans\",sans-serif;'>"
                f"{L['sin_datos_ia']}"
                "</p></div>",
                unsafe_allow_html=True,
            )

        with tab_historico:
            df_hist = obtener_historial_metricas()
            if not df_hist.empty:
                st.markdown(f"<p class='t-label' style='margin-bottom:12px;'>{L['auditorias_reg']}</p>", unsafe_allow_html=True)
                st.dataframe(
                    df_hist[['fecha', 'usuario', 'dominio', 'score_global', 'total_registros']],
                    width='stretch', hide_index=True,
                )
            else:
                st.markdown(
                    "<div class='talon-card-accent' style='border-left-color:#484F58;'>"
                    f"<p style='font-size:12px;color:#8B949E;margin:0;font-family:\"IBM Plex Sans\",sans-serif;'>"
                    f"{L['sin_auditorias']}</p></div>",
                    unsafe_allow_html=True,
                )

    # ── Pie de sidebar — créditos de desarrollo (siempre visible) ─
    with st.sidebar:
        st.markdown(
            """
            <div class="talon-dev-footer">
              <p style="font-family:'IBM Plex Sans',sans-serif;font-size:9px;
                color:#30363D;letter-spacing:.5px;text-transform:uppercase;">
                Desarrollado por
              </p>
              <p style="font-family:'IBM Plex Sans',sans-serif;font-size:10px;
                color:#475569;font-weight:500;">
                Jose Miguel Muñoz Ríos
              </p>
              <p style="font-family:'IBM Plex Mono',monospace;font-size:9px;
                color:#30363D;letter-spacing:.3px;">
                j01732666@gmail.com
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
