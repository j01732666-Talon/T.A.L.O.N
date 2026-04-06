"""
Punto de entrada principal de la aplicación Streamlit (T.A.L.O.N).

Tablero Analítico de Limpieza y Orquestación de Negocios. Este script orquesta 
la interfaz de usuario minimalista, gestiona el estado de sesión (autenticación, 
chat, historial de reglas) y coordina la comunicación entre el Motor de Calidad 
(Polars/Pandas), el Agente IA (Gemini) y el Data Lake local (DuckDB).
"""
import sys
import os

# --- ESCUDO DEFINITIVO ANTI-ERRORES DE RUTAS ---
ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_padre = os.path.dirname(ruta_actual)
if ruta_actual not in sys.path: sys.path.append(ruta_actual)
if ruta_padre not in sys.path: sys.path.append(ruta_padre)

import streamlit as st
import pandas as pd
import polars as pl
import time
import urllib.parse
import json

from config import DOMINIOS_CONFIG, UNIDADES_REF
from core.motor_calidad import ejecutar_auditoria_completa, validar_esquema, generar_excel_saneamiento_memoria
from core.motor_ia import responder_chat_ia, extraer_radiografia_datos, generar_reglas_autonomas_ia
from ui.ui_components import (renderizar_metricas, renderizar_grafico_dimensiones, 
                              renderizar_tabla_hallazgos, renderizar_grafico_top_errores, 
                              renderizar_grafico_por_foco)
from infra.datalake_manager import inicializar_datalake, guardar_auditoria, obtener_historial_metricas
from infra.auth_manager import inicializar_tabla_usuarios, registrar_usuario, validar_credenciales
from utils.profiler import medir_rendimiento

inicializar_datalake()
inicializar_tabla_usuarios()

# --- DICCIONARIOS COMPLETOS RESTAURADOS ---
DIRECTORIO_CUSTODIOS = {
    "ZFER": "jose.munoz@brinsa.com.co", 
    "ZHAW": "custodio.mercaderia@tuempresa.com",
    "ZROH": "custodio.materiaprima@tuempresa.com",
    "ZVER": "custodio.empaques@tuempresa.com",
    "ZIUC": "custodio.controlado@tuempresa.com",
    "ZERS": "custodio.repuestos@tuempresa.com",
    "ZSER": "custodio.servicios@tuempresa.com",
    "ZHAL": "custodio.semiterminado@tuempresa.com",
    "Directorio_Comercial": "datos.comerciales@brinsa.com.co",
    "DEFAULT": "gobiernodatos@tuempresa.com"
}

NOMBRES_MATERIALES = {
    "ZFER": "ZFER - Producto Terminado",
    "ZHAW": "ZHAW - Mercadería",
    "ZROH": "ZROH - Materia prima",
    "ZVER": "ZVER - Material Empaque",
    "ZIUC": "ZIUC - Inv uso controlado",
    "ZERS": "ZERS - Piezas de recambio",
    "ZSER": "ZSER - Servicios",
    "ZHAL": "ZHAL - Producto Semielaborado",
    "Directorio_Comercial": "Contactos y Directorio Comercial"
}

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

try:
    dominio_oficial = st.secrets["dominio_empresa"]
except KeyError:
    st.error("Error: Falta 'dominio_empresa' en secrets.toml. Asegúrate de que la carpeta .streamlit esté junto a app.py")
    st.stop()

# --- FLUJO DE AUTENTICACIÓN MINIMALISTA ---
# Gestiona la pantalla de Login y Registro.
# Si el usuario no está autenticado, bloquea el acceso al resto de la aplicación
# y renderiza los formularios. Utiliza st.session_state para mantener la sesión viva.
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
    def procesar_datos(archivo, unidades, focos, dominio, reglas_ia):
        return ejecutar_auditoria_completa(archivo, unidades, focos, dominio, reglas_ia)
    """
        Función envoltorio (wrapper) para invocar el motor de calidad central.
        
        Pasa el archivo cargado y las configuraciones dinámicas de la interfaz 
        hacia el procesador backend (Polars/Pandas).
        
        Args:
            archivo (file-like object): El archivo Excel subido por el usuario.
            unidades (list): Lista de unidades de medida válidas.
            focos (tuple): Elementos específicos a evaluar (actualmente no utilizado).
            dominio (str): Contexto comercial seleccionado en la barra lateral.
            reglas_ia (str): Cadena JSON con las reglas generadas dinámicamente.
            
        Returns:
            Tuple[pd.DataFrame, dict]: El dataframe con los resultados detallados y 
                                       un diccionario con las métricas calculadas.
        """
    # --- SIDEBAR BASE ---
    st.sidebar.markdown(f"### ⚙️ Panel de Control\n<span style='color:#888; font-size:0.9em;'>👤 {st.session_state['usuario_actual']}</span>", unsafe_allow_html=True)
    dominio_seleccionado = st.sidebar.radio("1. Dominio de Datos:", ("Maestro de Materiales", "Directorio Comercial"))
    archivo_subido = st.sidebar.file_uploader("2. Cargar extracción (.xlsx):", type=['xlsx'])

   # --- BOTÓN DE IA EN EL SIDEBAR ---
   # Activa el Agente IA para analizar estructuralmente el archivo cargado.
    # Extrae una radiografía (muestreo y nulos) y se la envía a Gemini para que 
    # devuelva un JSON estricto con las reglas DAMA sugeridas. Estas reglas 
    # se guardan en el session_state para recalcular el score global al instante.
    if archivo_subido is not None:
        st.sidebar.markdown("### 🧠 Auditor IA")
        if st.sidebar.button("Autoperfilar con IA", type="primary", use_container_width=True):
            with st.sidebar.status("Talon está analizando...", expanded=True) as status:
                try:
                    archivo_subido.seek(0)
                    st.write("🔍 Extrayendo radiografía del Excel...")
                    
                    # Carga verdaderamente segura: Intenta buscar 'DATA', si falla, lee la primera hoja (0)
                    try:
                        hoja_objetivo = "DATA" if "Directorio" in dominio_seleccionado else 0
                        df_crudo = pd.read_excel(archivo_subido, sheet_name=hoja_objetivo)
                    except ValueError:
                        # ¡El Plan B anti-crashes! Si la hoja 'DATA' no existe, agarramos la primera por defecto
                        df_crudo = pd.read_excel(archivo_subido, sheet_name=0)
                    
                    radiografia = extraer_radiografia_datos(df_crudo)
                    
                    st.write("⚙️ Generando reglas dinámicas (Gemini está pensando)...")
                    json_reglas = generar_reglas_autonomas_ia(radiografia, dominio_seleccionado)
                    
                    # Validamos que la IA no haya respondido un texto vacío
                    if json_reglas and len(json_reglas) > 10:
                        st.session_state['reglas_ia_dinamicas'] = json_reglas
                        status.update(label="¡Perfilamiento DAMA completado!", state="complete", expanded=False)
                        st.success("✅ ¡Reglas listas! Recargando Tablero...")
                        time.sleep(1.5) # Pequeña pausa para que veas el mensaje de éxito
                        st.rerun() # LA MAGIA: Obliga a la interfaz a mostrar los nuevos porcentajes
                    else:
                        status.update(label="Error en respuesta IA", state="error")
                        st.sidebar.error("❌ La IA devolvió un resultado vacío. Intenta hacer clic nuevamente.")
                        
                except Exception as e:
                    status.update(label="Error fatal", state="error")
                    st.sidebar.error(f"❌ Error al perfilar: {e}")

    # --- CUERPO PRINCIPAL ---
    if archivo_subido is not None:
        archivo_subido.seek(0)
        
        # 1. Procesamiento Silencioso (Motor Polars)
        reglas_dinamicas = st.session_state.get('reglas_ia_dinamicas')
        df_res, _ = procesar_datos(archivo_subido, UNIDADES_REF, tuple(), dominio_seleccionado, reglas_dinamicas)
        
        # 2. Construir lista de materiales dinámica para el Filtro
        if 'tipo_mat' in df_res.columns:
            materiales_presentes = [m for m in df_res['tipo_mat'].unique().tolist() if pd.notna(m) and m in NOMBRES_MATERIALES.keys()]
            materiales_presentes.sort()
        else:
            materiales_presentes = []

        # 3. Dibujar el filtro en el Sidebar con los datos reales que encontró
        st.sidebar.markdown("### 🎯 Enfoque")
        filtro_mat = st.sidebar.multiselect(
            "Filtrar Categoría:", 
            options=materiales_presentes, 
            format_func=lambda x: NOMBRES_MATERIALES.get(x, x),
            placeholder="Analizar todo"
        )

        st.sidebar.divider()
        if st.sidebar.button("Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        # 4. Aplicar el filtro a la vista principal
        if filtro_mat:
            df_display = df_res[df_res['tipo_mat'].isin(filtro_mat)]
        else:
            df_display = df_res

        total_disp = len(df_display)
        res_dinamico = {
            'score_global': df_display['Score_Calidad'].mean() if total_disp > 0 else 0,
            'completitud': df_display['Score_Completitud'].mean() if total_disp > 0 else 0,
            'validez': df_display['Score_Validez'].mean() if total_disp > 0 else 0,
            'unicidad': df_display['Score_Unicidad'].mean() if total_disp > 0 else 0,
            'consistencia': df_display['Score_Consistencia'].mean() if total_disp > 0 else 0
        }

# ==========================================
        # 📋 VISUALIZADOR DE REGLAS APLICADAS (UX MEJORADA)
        # ==========================================
        if st.session_state.get('reglas_ia_dinamicas'):
            st.markdown("### 📋 Reglas definidas por IA (Formato Lectura)")
            try:
                import json
                reglas_dict = json.loads(st.session_state.get('reglas_ia_dinamicas'))
                
                # Leemos la LISTA de modificadas en lugar de un solo string
                ultimas_mods = st.session_state.get('ultimas_reglas_modificadas', [])
                
                if "diccionario_reglas" in reglas_dict:
                    for categoria in reglas_dict["diccionario_reglas"]:
                        dimension = categoria.get("dimension_dama", "Desconocida")
                        
                        # El acordeón se abre si ALGUNA de las reglas dentro fue modificada
                        abrir_desplegable = any(dimension in mod for mod in ultimas_mods)
                        
                        with st.expander(f"📐 Dimensión: {dimension}", expanded=abrir_desplegable):
                            for regla in categoria.get("reglas_aplicadas", []):
                                col = regla.get("nombre_columna", "N/A")
                                tipo = regla.get("regla", "N/A")
                                pen = regla.get("penalizacion", 0)
                                msg = regla.get("mensaje", "Sin mensaje")
                                
                                key_regla = f"{dimension}_{col}_{tipo}"
                                
                                # Si la regla está en la lista, le ponemos la medalla verde
                                es_nueva = (key_regla in ultimas_mods)
                                si_destacado = "✨ <span style='color:#00FF00; font-weight:bold;'>[ACTUALIZADO]</span> " if es_nueva else ""
                                
                                texto_regla = f"{si_destacado}* **`{col}`** ➡️ Regla: **{tipo}** (🔴 -{pen} pts)\n  * *Mensaje de error:* {msg}"
                                
                                if regla.get("condicion_columna") and regla.get("condicion_valor"):
                                    texto_regla += f"\n  * *Condición:* Solo aplica si `{regla['condicion_columna']}` es `{regla['condicion_valor']}`"
                                    
                                st.markdown(texto_regla, unsafe_allow_html=True)
                else:
                    st.info("No hay reglas estructuradas para mostrar.")
            except Exception as e:
                st.error("No se pudo formatear el texto de las reglas para lectura humana.")
            
            # --- LIMPIEZA DE MEMORIA (IMPORTANTE) ---
            # Borramos la lista de destacados después de pintarla, para que la próxima vez 
            # que se hable con Talon, no sigan brillando las reglas viejas.
            st.session_state.pop('ultimas_reglas_modificadas', None)
        # ==========================================

        # ==========================================
        # Guardado Automático Transparente
        if 'id_ejecucion' not in st.session_state or st.session_state.get('last_file') != archivo_subido.name:
            st.session_state['id_ejecucion'] = guardar_auditoria(df_display, st.session_state['usuario_actual'], dominio_seleccionado, res_dinamico, filtro_mat)
            st.session_state['last_file'] = archivo_subido.name

        # --- SECCIÓN VISUAL (MÉTRICAS Y BOTONES) ---
        # --- ESCUDO ANTI 100% FALSO ---
        if not st.session_state.get('reglas_ia_dinamicas'):
                st.warning("⚠️ Atención: No hay reglas de IA cargadas en memoria. Ejecuta 'Autoperfilar con IA' para que los scores sean reales.")
        elif res_dinamico.get('score_global') == 100.0:
                st.info("ℹ️ El score es 100%. Si sabes que hay errores, verifica que los nombres de las columnas en las reglas coincidan exactamente con tu Excel.")
            # -------------------------------
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
            correo_custodio = DIRECTORIO_CUSTODIOS.get(filtro_mat[0] if len(filtro_mat)==1 else "DEFAULT", "gobiernodatos@tuempresa.com")
            asunto = f"T.A.L.O.N - Revisión Requerida"
            cuerpo = f"Score actual: {res_dinamico['score_global']:.1f}%."
            gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={correo_custodio}&su={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"
            st.markdown(f"""<a href="{gmail_link}" target="_blank"><button style="width: 100%; background: transparent; color: #007BFF; border: 1px solid #007BFF; padding: 7px; border-radius: 4px; cursor: pointer;">✉️ Notificar Custodio</button></a>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-top: 1px solid #333; margin-top: 10px;'>", unsafe_allow_html=True)

        # --- PESTAÑAS (TABS) ---
        # Renderizado modular de la interfaz principal en 4 áreas:
        # 1. Dashboard: Gráficos de salud y top de errores.
        # 2. Asistente IA: Chat interactivo con 'Talon' con memoria de sesión y herramientas.
        # 3. Explorador: Tabla interactiva para filtrar registros anómalos.
        # 4. Historial: Consulta de las ejecuciones guardadas en DuckDB.
        tab_dashboard, tab_ia, tab_datos, tab_historico = st.tabs(["📊 Dashboard", "🧠 Asistente IA", "🔎 Explorador", "🕒 Historial"])

        with tab_dashboard:
            col1, col2 = st.columns(2)
            with col1: renderizar_grafico_dimensiones(res_dinamico)
            with col2: renderizar_grafico_top_errores(df_display)
            renderizar_grafico_por_foco(df_display)

        with tab_ia:
            st.markdown("#### Chat con Talon")
            
            # --- SALUDO INICIAL Y PRESENTACIÓN DE TALON ---
            contexto_str = "Global" if not filtro_mat else f"Filtro: {', '.join(filtro_mat)}"
            
            if not st.session_state['chat_historial'] or st.session_state.get('ia_contexto_chat') != contexto_str:
                mensaje_bienvenida = (
                    f"🐦‍⬛ **¡Hola! Soy Talon, tu Consultor y Arquitecto de Calidad de Datos.**\n\n"
                    f"Estoy aquí para ayudarte a perfilar, auditar y sanear tu información. Mis superpoderes incluyen:\n"
                    f"- 🧐 Explicarte el porqué de cada anomalía detectada.\n"
                    f"- ⚙️ **Ajustar las reglas y penalizaciones** en tiempo real si me lo pides en este chat.\n"
                    f"- 🧠 Aprender de tus decisiones cuando guardes mis configuraciones en la bóveda Prime.\n\n"
                    f"📊 **Resumen actual:** He analizado los **{total_disp}** registros de la vista ({contexto_str}) y detecté un **Score Global de {res_dinamico['score_global']:.1f}%**.\n\n"
                    f"¿Por dónde te gustaría que empecemos a revisar?"
                )
                st.session_state['chat_historial'] = [
                    {"role": "assistant", "content": mensaje_bienvenida}
                ]
                st.session_state['ia_contexto_chat'] = contexto_str
            # ----------------------------------------------
            
            # --- BOTÓN DE GUARDADO PRIME ---
            if st.session_state.get('reglas_ia_dinamicas'):
                st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
                if st.button("💾 Guardar como Reglas Prime", type="secondary"):
                    from core.motor_ia import guardar_reglas_prime
                    resultado = guardar_reglas_prime(st.session_state['reglas_ia_dinamicas'], dominio_seleccionado)
                    st.success(resultado)
                st.markdown("</div>", unsafe_allow_html=True)
            # -------------------------------

            contenedor_mensajes = st.container(height=400)
            with contenedor_mensajes:
                for mensaje in st.session_state['chat_historial']:
                    with st.chat_message(mensaje["role"]): 
                        st.markdown(mensaje["content"])
            
            if prompt_usuario := st.chat_input("Pregúntale a Talon sobre las anomalías..."):
                st.session_state['chat_historial'].append({"role": "user", "content": prompt_usuario})
                with contenedor_mensajes:
                    with st.chat_message("user"): 
                        st.markdown(prompt_usuario)
                    with st.chat_message("assistant"):
                        respuesta_ia = responder_chat_ia(prompt_usuario, df_display, str(filtro_mat), st.session_state['chat_historial'][:-1])
                        st.markdown(respuesta_ia)
                        st.session_state['chat_historial'].append({"role": "assistant", "content": respuesta_ia})
                st.rerun()

        with tab_historico:
            df_hist = obtener_historial_metricas()
            if not df_hist.empty:
                st.dataframe(df_hist[['fecha', 'usuario', 'dominio', 'score_global', 'total_registros']], use_container_width=True, hide_index=True)
            else:
                st.info("Aún no hay auditorías.")

        with tab_datos:
            try:
                renderizar_tabla_hallazgos(df_display)
            except Exception as e:
                st.error(f"Error técnico al cargar la tabla: {e}")

    else:
        # PANTALLA DE ESPERA
        st.sidebar.divider()
        if st.sidebar.button("Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.markdown(
            """
            <div style='text-align: center; margin-top: 15vh; color: #555;'>
                <h1 style='font-size: 4rem;'>🐦‍⬛​</h1>
                <h2>Talon está listo</h2>
                <p>Usa el panel izquierdo para cargar tu extracción de datos y comenzar.</p>
            </div>
            """, unsafe_allow_html=True
        )