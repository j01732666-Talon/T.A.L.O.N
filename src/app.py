"""
    Punto de entrada principal de la aplicación T.A.L.O.N.
    Tablero Analítico de Limpieza y Orquestación de Negocios.
    
    Refactorizado para carga dinámica de catálogos y seguridad mejorada.
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

# --- IMPORTACIONES DINÁMICAS (Desde config.py y catálogos JSON) ---
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

# Inicialización de infraestructura
inicializar_datalake()
inicializar_tabla_usuarios()

st.set_page_config(page_title="T.A.L.O.N", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS CSS MINIMALISTAS ---
st.markdown(
    """
    <style>
        .main-title { color: #FFFFFF; font-size: 2.2rem; font-weight: 700; margin-bottom: 0px; letter-spacing: -0.5px; }
        .subtitle { color: #888888; font-size: 1rem; margin-bottom: 20px; }
        div[data-testid="stForm"] button, button[data-testid="baseButton-primary"] {
            background-color: #007BFF !important; color: white !important; border: none !important; border-radius: 4px !important;
        }
        .action-card { background:#1e1e24; padding:25px; border-radius:10px; border:1px solid #333; margin-top: 20px; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- INICIALIZACIÓN DE ESTADO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = ""
if 'chat_historial' not in st.session_state: st.session_state['chat_historial'] = []
if 'reglas_ia_dinamicas' not in st.session_state: st.session_state['reglas_ia_dinamicas'] = None
if 'mostrar_registro' not in st.session_state: st.session_state['mostrar_registro'] = False

# Dominio corporativo desde secretos
dominio_oficial = st.secrets.get("dominio_empresa", "@brinsa.com.co")

# --- FLUJO DE AUTENTICACIÓN ---
if not st.session_state['autenticado']:
    col_vacia1, col_login, col_vacia3 = st.columns([1.2, 1.2, 1.2])
    with col_login:
        st.markdown('<div style="text-align: center; margin-top: 10vh;"><h1 class="main-title">T.A.L.O.N</h1><p class="subtitle">Tablero Analítico de Limpieza y Orquestación de Negocios</p></div>', unsafe_allow_html=True)
        
        st.markdown("<div class='action-card'>", unsafe_allow_html=True)
        if not st.session_state['mostrar_registro']:
            st.markdown("#### Ingresa a tu cuenta")
            with st.form("formulario_login"):
                correo_login = st.text_input("Correo corporativo", placeholder=f"usuario{dominio_oficial}")
                password_login = st.text_input("Contraseña", type="password")
                if st.form_submit_button("INICIAR SESIÓN", type="primary", use_container_width=True):
                    if validar_credenciales(correo_login, password_login):
                        from infra.auth_manager import registrar_ingreso
                        registrar_ingreso(correo_login.lower())
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_actual'] = correo_login.lower()
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
            if st.button("¿No tienes cuenta? Regístrate aquí", use_container_width=True):
                st.session_state['mostrar_registro'] = True
                st.rerun()
        else:
            st.markdown("#### Nuevo Usuario")
            with st.form("formulario_registro"):
                correo_registro = st.text_input("Correo corporativo", placeholder=f"usuario{dominio_oficial}")
                password_registro = st.text_input("Crear Contraseña", type="password")
                password_confirm = st.text_input("Confirmar Contraseña", type="password")
                if st.form_submit_button("REGISTRARSE", type="primary", use_container_width=True):
                    if password_registro != password_confirm:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        exito, mensaje = registrar_usuario(correo_registro, password_registro, dominio_oficial)
                        if exito:
                            st.success("Cuenta creada. Ya puedes iniciar sesión.")
                            st.session_state['mostrar_registro'] = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(mensaje)
            if st.button("← Volver al Login", use_container_width=True):
                st.session_state['mostrar_registro'] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- ÁREA DE USUARIO AUTENTICADO ---
    def procesar_datos(datos_entrada, unidades, focos, dominio, reglas_ia):
        return ejecutar_auditoria_completa(datos_entrada, unidades, focos, dominio, reglas_ia)

    # --- SIDEBAR BASE ---
    st.sidebar.markdown(f"### ⚙️ Panel de Control\n<span style='color:#888; font-size:0.9em;'>👤 {st.session_state['usuario_actual']}</span>", unsafe_allow_html=True)
    
    # Dominios cargados dinámicamente desde DOMINIOS_CONFIG
# --- BLINDAJE: Si el JSON falla, usamos valores por defecto ---
    opciones_dominio = list(DOMINIOS_CONFIG.keys()) if DOMINIOS_CONFIG else ["Maestro de Materiales", "Directorio Comercial"]
    
    dominio_seleccionado = st.sidebar.radio("1. Dominio de Datos:", opciones_dominio)
    fuente_datos = st.sidebar.radio("2. Fuente de Datos:", ("Archivo Local (.xlsx)", "Conexión Directa (TalonDB)"))

    archivo_subido = None
    datos_crudos = None

    if fuente_datos == "Archivo Local (.xlsx)":
        archivo_subido = st.sidebar.file_uploader("Cargar extracción:", type=['xlsx'])
        if archivo_subido:
            archivo_subido.seek(0)
            # BLINDAJE: Validamos que dominio_seleccionado no sea None antes de buscar en él
            hoja_objetivo = "DATA" if dominio_seleccionado and "Directorio" in dominio_seleccionado else 0
            try:
                datos_crudos = pd.read_excel(archivo_subido, sheet_name=hoja_objetivo)
            except ValueError:
                datos_crudos = pd.read_excel(archivo_subido, sheet_name=0)
            st.session_state['origen_datos'] = archivo_subido.name
            
    else:
        st.sidebar.info("☁️ Conexión segura a BigQuery")
        if st.sidebar.button("🔌 Extraer Datos de SAP/TalonDB", type="primary", use_container_width=True):
            with st.spinner("Conectando a GCP y descargando datos..."):
                try:
                    df_polars = extraer_maestro_materiales()
                    if df_polars is not None:
                        st.session_state['datos_crudos_bd'] = df_polars.to_pandas()
                        st.session_state['origen_datos'] = "TalonDB (BigQuery)"
                        st.sidebar.success("✅ Extracción exitosa.") # <--- Cambiado a sidebar
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    # Aquí atrapamos el error que viene desde bigquery_client.py
                    st.sidebar.error(f"❌ {str(e)}")

        if 'datos_crudos_bd' in st.session_state:
            datos_crudos = st.session_state['datos_crudos_bd']

# --- BOTÓN IA (PERFILAMIENTO CON MEMORIA PRIME) ---
    if datos_crudos is not None:
        st.sidebar.divider()
        if st.sidebar.button("🧠 Autoperfilar con IA", use_container_width=True):
            with st.spinner("Analizando radiografía de datos con Gemini..."):
                texto_ia = generar_reglas_autonomas_ia(datos_crudos, dominio_seleccionado)
                
                st.sidebar.write("### 🕵️‍♂️ DEBUG: ¿Qué dijo Gemini?")
                st.sidebar.code(texto_ia)

                reglas_adaptadas = adaptar_reglas_ia_a_motor(texto_ia, dominio_seleccionado)
                
                if reglas_adaptadas:
                    st.session_state['reglas_ia_dinamicas'] = reglas_adaptadas
                    st.sidebar.success("✅ Perfilamiento completado")
                else:
                    st.sidebar.error("❌ El traductor rechazó el formato de la IA.")
                
                st.rerun()  # <---- ¡PONLE UN # A ESTA LÍNEA O BÓRRALA!

    # --- INTERFAZ VISUAL DE LAS NUEVAS REGLAS ---
    if st.session_state.get('reglas_ia_dinamicas'):
        st.sidebar.markdown("### 📋 Nuevas Reglas de Talon")
        st.sidebar.caption("Estas reglas están impactando el Dashboard actual:")
        
        reglas_ia = st.session_state['reglas_ia_dinamicas']
        
        for foco, contenido in reglas_ia.items():
            if foco == "DEFAULT" and "Directorio" not in dominio_seleccionado:
                nombre_menu = "Reglas Generales (SKUs)"
            else:
                nombre_menu = f"Reglas: {foco}"

            with st.sidebar.expander(f"📦 {nombre_menu}"):
                for dimension, reglas_dim in contenido.items():
                    if dimension == "pesos_dimensiones": continue
                    
                    if reglas_dim: # Solo dibujamos si la dimensión tiene reglas adentro
                        st.markdown(f"**🎯 {dimension}**")
                        for campo, config in reglas_dim.items():
                            mensaje = config.get('mensaje', 'Validación estricta')
                            peso = config.get('penalizacion', 0)
                            st.markdown(f"• **{campo}**: {mensaje} *(-{peso} pts)*")

        # --- CREACIÓN DE LOS MENÚS ---
        if isinstance(reglas_ia, dict):
            for foco, contenido in reglas_ia.items():
                if foco == "DEFAULT": continue # Ocultamos el bloque por defecto
                
                with st.sidebar.expander(f"📦 Reglas para: {foco}"):
                    # Validamos que el contenido sea un diccionario antes de iterar
                    if isinstance(contenido, dict):
                        for dimension, reglas_dim in contenido.items():
                            if dimension == "pesos_dimensiones":
                                continue # Saltamos los pesos
                            
                            st.markdown(f"**🎯 {dimension}**")
                            if isinstance(reglas_dim, dict):
                                for campo, config in reglas_dim.items():
                                    mensaje = config.get('mensaje', 'Validación estricta')
                                    peso = config.get('penalizacion', 0)
                                    st.markdown(f"• **{campo}**: {mensaje} *(Penalización: -{peso} pts)*")

    # --- CUERPO PRINCIPAL ---
    if datos_crudos is not None:
        # 1. Ejecución del Motor Polars
        reglas_actuales = st.session_state.get('reglas_ia_dinamicas')
        df_res, res_original = procesar_datos(datos_crudos, UNIDADES_REF, None, dominio_seleccionado, reglas_actuales)
        
        # 2. Filtro dinámico usando NOMBRES_MATERIALES del catálogo JSON
        materiales_presentes = []
        if 'tipo_mat' in df_res.columns:
            materiales_presentes = [m for m in df_res['tipo_mat'].unique().tolist() if pd.notna(m) and m in NOMBRES_MATERIALES]
            materiales_presentes.sort()

        st.sidebar.markdown("### 🎯 Enfoque")
        filtro_mat = st.sidebar.multiselect(
            "Filtrar Categoría:", 
            options=materiales_presentes, 
            format_func=lambda x: NOMBRES_MATERIALES.get(x, x),
            placeholder="Analizar todo"
        )

        st.sidebar.divider()
        if st.sidebar.button("Cerrar Sesión", key="btn_cerrar_sesion_datos", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        # 3. Aplicar Filtro y recalcular Scores
        df_display = df_res[df_res['tipo_mat'].isin(filtro_mat)] if filtro_mat else df_res
        total_disp = len(df_display)
        
        if total_disp > 0:
            res_dinamico = {
                'score_global': df_display['Score_Calidad'].mean(),
                'completitud': df_display['Score_Completitud'].mean(),
                'validez': df_display['Score_Validez'].mean(),
                'unicidad': df_display['Score_Unicidad'].mean(),
                'consistencia': df_display['Score_Consistencia'].mean()
            }
        else:
            res_dinamico = {k: 0.0 for k in ['score_global', 'completitud', 'validez', 'unicidad', 'consistencia']}

        # 4. Guardado Automático en el Data Lake
        nombre_origen = st.session_state.get('origen_datos', "Sin_Nombre")
        if 'id_ejecucion' not in st.session_state or st.session_state.get('last_file') != nombre_origen:
            st.session_state['id_ejecucion'] = guardar_auditoria(df_display, st.session_state['usuario_actual'], dominio_seleccionado, res_dinamico, filtro_mat)
            st.session_state['last_file'] = nombre_origen

        # --- SECCIÓN VISUAL ---
        if not st.session_state.get('reglas_ia_dinamicas'):
            st.warning("⚠️ Atención: No hay reglas de IA cargadas. Ejecuta 'Autoperfilar con IA' para activar los scores reales.")
            
        renderizar_metricas(res_dinamico)

        st.markdown("<br>", unsafe_allow_html=True)
        col_acc1, col_acc2, col_acc3 = st.columns([1, 1, 2])
        
        with col_acc1:
            excel_bytes = generar_excel_saneamiento_memoria(df_display)
            st.download_button(
                label="📥 Exportar Saneamiento",
                data=excel_bytes,
                file_name=f"TALON_Saneamiento_{int(time.time())}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
            
        with col_acc2:
            # Obtiene el correo del custodio desde el catálogo dinámico CUSTODIOS
            key_custodio = filtro_mat[0] if len(filtro_mat) == 1 else "DEFAULT"
            sugerencia_correo = CUSTODIOS.get(key_custodio, "gobiernodatos@brinsa.com.co")
            
            with st.popover("✉️ Notificar Custodio", use_container_width=True):
                st.markdown("#### 📤 Enviar Reporte")
                correo_destino = st.text_input("Correo del responsable:", value=sugerencia_correo)
                if st.button("🚀 Enviar Excel Ahora", use_container_width=True):
                    if not correo_destino or "@" not in correo_destino:
                        st.error("Ingresa un correo válido.")
                    else:
                        with st.spinner("Enviando correo..."):
                            from infra.notificador import enviar_correo_talon
                            errores_totales = len(df_display[df_display['Score_Calidad'] < 100])
                            exito, mensaje = enviar_correo_talon(
                                correo_custodio=correo_destino, 
                                correo_auditor=st.session_state['usuario_actual'],
                                dominio=dominio_seleccionado,
                                score=round(res_dinamico['score_global'], 1),
                                total_errores=errores_totales,
                                archivo_bytes=excel_bytes
                            )
                            if exito: st.success(f"✅ ¡Enviado a {correo_destino}!")
                            else: st.error(f"❌ Error: {mensaje}")

# --- PESTAÑAS PRINCIPALES ---
        tab_dashboard, tab_ia, tab_datos, tab_historico = st.tabs(["📊 Dashboard", "🧠 Asistente IA", "🔎 Explorador", "🕒 Historial"])

        with tab_dashboard:
            col1, col2 = st.columns(2)
            with col1: renderizar_grafico_dimensiones(res_dinamico)
            with col2: renderizar_grafico_top_errores(df_display)
            renderizar_grafico_por_foco(df_display)

        with tab_ia:
            st.markdown("#### Chat con Talon (Consultor IA)")
            
            # Botón para persistir las reglas como Prime
            if st.session_state.get('reglas_ia_dinamicas'):
                st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
                if st.button("💾 Guardar como Reglas Prime", type="secondary"):
                    resultado = guardar_reglas_prime(st.session_state['reglas_ia_dinamicas'], dominio_seleccionado)
                    st.success(resultado)
                st.markdown("</div>", unsafe_allow_html=True)

            # --- RESTAURACIÓN DEL MENSAJE DE BIENVENIDA ---
            contexto_str = "Global" if not filtro_mat else f"Filtro: {', '.join(filtro_mat)}"
            
            if not st.session_state['chat_historial'] or st.session_state.get('ia_contexto_chat') != contexto_str:
                mensaje_bienvenida = (
                    f"🐦‍⬛ **¡Hola! Soy Talon, tu Consultor de Calidad de Datos.**\n\n"
                    f"He analizado los **{total_disp}** registros y detecté un **Score Global de {res_dinamico['score_global']:.1f}%**.\n\n"
                    f"¿Por dónde te gustaría que empecemos a revisar? Puedo explicarte las anomalías o indicarte cómo ajustar las reglas."
                )
                st.session_state['chat_historial'] = [
                    {"role": "assistant", "content": mensaje_bienvenida}
                ]
                st.session_state['ia_contexto_chat'] = contexto_str

            # Renderizar historial
            contenedor_mensajes = st.container(height=400)
            with contenedor_mensajes:
                for mensaje in st.session_state['chat_historial']:
                    with st.chat_message(mensaje["role"]): 
                        st.markdown(mensaje["content"])
            
            # Input del usuario
            if prompt_usuario := st.chat_input("Pregúntale a Talon sobre las anomalías..."):
                st.session_state['chat_historial'].append({"role": "user", "content": prompt_usuario})
                with contenedor_mensajes:
                    with st.chat_message("user"): 
                        st.markdown(prompt_usuario)
                    with st.chat_message("assistant"):
                        respuesta_ia = responder_chat_ia(prompt_usuario, df_display.head(5), contexto_str, st.session_state['chat_historial'][:-1])
                        st.markdown(respuesta_ia)
                        st.session_state['chat_historial'].append({"role": "assistant", "content": respuesta_ia})
                st.rerun()

        # =========================================================
        # FÍJATE AQUÍ: "with tab_datos:" ahora está alineado a la izquierda, 
        # a la misma altura que "with tab_ia:"
        # =========================================================
        with tab_datos:
            try:
                renderizar_tabla_hallazgos(df_display)
            except Exception as e:
                st.error(f"Error técnico en la tabla: {e}")

        with tab_historico:
            df_hist = obtener_historial_metricas()
            if not df_hist.empty:
                st.dataframe(df_hist[['fecha', 'usuario', 'dominio', 'score_global', 'total_registros']], use_container_width=True, hide_index=True)
            else:
                st.info("Aún no hay auditorías registradas.")

    else:
        # Pantalla de bienvenida / Espera
        st.sidebar.divider()
        # NOTA: Le agregué el key="..." para evitar el error de botones duplicados
        if st.sidebar.button("Cerrar Sesión", key="btn_cerrar_sesion_vacio", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.markdown(
            """
            <div style='text-align: center; margin-top: 15vh; color: #555;'>
                <h1 style='font-size: 4rem;'>🐦‍⬛​</h1>
                <h2>Talon está listo</h2>
                <p>Usa el panel izquierdo para cargar tu extracción de datos y comenzar la auditoría.</p>
            </div>
            """, unsafe_allow_html=True
        )