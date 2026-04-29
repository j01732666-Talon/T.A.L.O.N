"""
Motor de Calidad de Datos (T.A.L.O.N - "Tablero Analítico de Limpieza y Orquestación de Negocios")
Motor de Reglas Dinámico: Lee reglas desde un JSON y las aplica vectorialmente por tipo de material o dominio comercial.
"""
import pandas as pd
import numpy as np
import io
import json
import os
import re
import polars as pl
from typing import Tuple, Any, List

def validar_esquema(columnas_actuales: List[str], columnas_requeridas: List[str]) -> List[str]:
    """
    Compara las columnas presentes en un conjunto de datos contra una lista de columnas requeridas.
    
    Args:
        columnas_actuales (List[str]): Lista con los nombres de las columnas existentes.
        columnas_requeridas (List[str]): Lista con los nombres de las columnas que deben estar presentes.
        
    Returns:
        List[str]: Una lista que contiene únicamente los nombres de las columnas que faltan.
    """
    faltantes = [col for col in columnas_requeridas if col not in columnas_actuales]
    return faltantes

def cargar_reglas_json() -> dict:
    """
    Localiza y carga el archivo maestro de reglas de calidad (reglas_cde.json).
    
    Busca dinámicamente en los directorios 'src/data_ref' y en la raíz del proyecto.
    Si el archivo no existe o no se encuentra, retorna un diccionario de reglas por defecto 
    con pesos equitativos para las dimensiones de calidad.
    
    Returns:
        dict: Diccionario con la configuración de reglas de calidad estructuradas por dominio.
    """
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    dir_src = os.path.dirname(dir_actual)
    ruta_json = os.path.join(dir_src, "data_ref", "reglas_cde.json")
    
    if not os.path.exists(ruta_json):
        dir_raiz = os.path.dirname(dir_src)
        ruta_json = os.path.join(dir_raiz, "data_ref", "reglas_cde.json")

    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"DEFAULT": {"pesos_dimensiones": {"Completitud": 0.25, "Unicidad": 0.25, "Validez": 0.25, "Consistencia": 0.25}}}

def adaptar_reglas_ia_a_motor(json_ia_str, dominio):
    try:
        import json
        import re
        
        # 1. Blindaje: Convertir a diccionario de forma segura
        if isinstance(json_ia_str, dict):
            datos_ia = json_ia_str
        else:
            json_limpio = str(json_ia_str)
            match = re.search(r'\{.*\}', json_limpio, re.DOTALL)
            if match: json_limpio = match.group(0)
            datos_ia = json.loads(json_limpio)
            
        diccionario_ia = datos_ia.get("diccionario_reglas", [])
        if not diccionario_ia:
            if isinstance(datos_ia, list): diccionario_ia = datos_ia
            else: return None 
            
        target_key = "Directorio_Comercial" if "Directorio" in str(dominio) else "DEFAULT"
        reglas_adaptadas = {
            target_key: {
                "pesos_dimensiones": {"Completitud": 0.25, "Unicidad": 0.25, "Validez": 0.25, "Consistencia": 0.25},
                "Completitud": {}, "Validez": {}, "Unicidad": {}, "Consistencia": {}
            }
        }

        # 2. Traductor Inteligente
        for item in diccionario_ia:
            # Detectar dimensión
            dim_cruda = str(item.get("dimension_dama", item.get("dimension", "Validez"))).strip().lower()
            if "complet" in dim_cruda: dim = "Completitud"
            elif "unic" in dim_cruda: dim = "Unicidad"
            elif "consist" in dim_cruda: dim = "Consistencia"
            else: dim = "Validez" 
            
            # Formato A: Anidado (reglas_aplicadas)
            if "reglas_aplicadas" in item:
                for regla in item.get("reglas_aplicadas", []):
                    col_name = str(regla.get("nombre_columna", "")).strip()
                    tipo_regla = str(regla.get("regla", "nulo")).strip()
                    if col_name:
                        reglas_adaptadas[target_key][dim][col_name] = {
                            "regla": tipo_regla,
                            "penalizacion": float(regla.get("penalizacion", 50)),
                            "mensaje": str(regla.get("mensaje", f"Error en {col_name}"))
                        }
                        
            # Formato B: Plano (El de tu JSON reciente)
            elif "columna" in item:
                col_name = str(item.get("columna", "")).strip()
                # Deducimos el comando matemático para Polars
                if dim == "Completitud": tipo_regla = "nulo"
                elif dim == "Unicidad": tipo_regla = "duplicado_multicampo"
                else: tipo_regla = "nulo" # Fallback
                
                if col_name:
                    reglas_adaptadas[target_key][dim][col_name] = {
                        "regla": tipo_regla,
                        "penalizacion": float(item.get("penalizacion_negocio", 50)),
                        "mensaje": str(item.get("descripcion", f"Error en {col_name}"))
                    }

        return reglas_adaptadas
    except Exception as e:
        import streamlit as st
        st.error(f"⚠️ Error traduciendo IA a Polars: {e}")
        return None


def ejecutar_auditoria_completa(datos_entrada, unidades, focos, dominio="Maestro de Materiales", reglas_ia=None):
    """
    Motor principal de evaluación de calidad. Procesa un archivo Excel y aplica reglas 
    vectorizadas de completitud, unicidad, validez y consistencia.
    
    Realiza una lectura segura utilizando Pandas para tolerar errores comunes en archivos 
    (como encabezados vacíos), y luego transfiere el procesamiento a Polars para 
    maximizar el rendimiento. Calcula un 'Score_Calidad' global y documenta las 
    fallas específicas por fila.
    
    Args:
        datos_entrada (str, bytes, file-like object, pd.DataFrame o pl.DataFrame): Los datos a evaluar.
        unidades (list): Lista de unidades de medida válidas (para reglas de catálogo).
        focos (Any): Parámetro de enfoque de reglas.
        dominio (str, opcional): El contexto comercial de los datos. Por defecto es "Maestro de Materiales".
        reglas_ia (str, opcional): Cadena JSON con reglas generadas dinámicamente por la IA.
        
    Returns:
        Tuple[pd.DataFrame, dict]: 
            - pd.DataFrame: Dataframe detallado con las puntuaciones por dimensión, el score final y los hallazgos.
            - dict: Resumen general con el promedio global y por cada dimensión evaluada.
    """
    # =========================================================================
    # LECTURA SEGURA Y ADAPTADOR INTELIGENTE
    # =========================================================================
    try:
        if isinstance(datos_entrada, pd.DataFrame):
            # Si viene de app.py (Pandas de BigQuery o Excel ya leído), lo pasamos a Polars
            df_pd = datos_entrada.copy()
            df_pd.columns = [str(c).strip() for c in df_pd.columns]
            df = pl.from_pandas(df_pd)
        elif isinstance(datos_entrada, pl.DataFrame):
            # Si ya es Polars, lo usamos directo
            df = datos_entrada
        else:
            # Si entra el archivo físico en crudo
            df_pd = pd.read_excel(datos_entrada, dtype=str)
            if df_pd.empty:
                return pd.DataFrame(), {}
            # Limpieza segura de nombres de columnas en Pandas para evitar duplicados en Polars
            df_pd.columns = [str(c).strip() for c in df_pd.columns]
            df = pl.from_pandas(df_pd)
    except Exception as e:
        import streamlit as st
        st.error(f"⚠️ Fallo crítico al leer los datos. Verifica que el archivo no esté corrupto. Error: {e}")
        return pd.DataFrame(), {}

    # =========================================================================
    # CARGA DE REGLAS MAESTRAS
    # =========================================================================
    if reglas_ia:
        # EL ESCUDO: Si las reglas ya vienen listas de app.py, NO las tocamos
        if isinstance(reglas_ia, dict) and ("DEFAULT" in reglas_ia or "Directorio_Comercial" in reglas_ia):
            reglas_maestras = reglas_ia
        else:
            reglas_maestras = adaptar_reglas_ia_a_motor(reglas_ia, dominio)
            if not reglas_maestras: 
                reglas_maestras = cargar_reglas_json()
    else:
        reglas_maestras = cargar_reglas_json()
        
    # ADAPTADOR DE ESQUEMA MULTI-DOMINIO
    if "Directorio" in dominio:
        if 'ID DATO' in df.columns: df = df.with_columns(pl.col('ID DATO').alias('SKU_num'))
        elif 'Cliente' in df.columns: df = df.with_columns(pl.col('Cliente').alias('SKU_num'))
        elif 'Proveedor' in df.columns: df = df.with_columns(pl.col('Proveedor').alias('SKU_num'))
            
        if 'Nombre' in df.columns: df = df.with_columns(pl.col('Nombre').alias('Desc_Material'))
        df = df.with_columns(pl.lit('Directorio_Comercial').alias('tipo_mat'))

    if 'tipo_mat' not in df.columns: df = df.with_columns(pl.lit('DEFAULT').alias('tipo_mat'))
    if 'Desc_Material' not in df.columns: df = df.with_columns(pl.lit('').alias('Desc_Material'))
    if 'SKU_num' in df.columns: df = df.with_columns(pl.col('SKU_num').cast(pl.Utf8))
            
    df = df.with_columns([
        pl.lit(100.0).alias('Score_Unicidad'), pl.lit(100.0).alias('Score_Completitud'),
        pl.lit(100.0).alias('Score_Validez'), pl.lit(100.0).alias('Score_Consistencia'),
        pl.lit(0.0).alias('Score_Calidad'), pl.lit("").alias('Hallazgos_Detallados')
    ])
    
    tipos_presentes = df['tipo_mat'].unique().to_list()
    
    # =========================================================================
    # APLICACIÓN VECTORIAL DE REGLAS (POLARS)
    # =========================================================================
    for tipo in tipos_presentes:
        reglas = reglas_maestras.get(tipo, reglas_maestras.get("DEFAULT", {}))
        p = reglas.get("pesos_dimensiones", reglas_maestras.get("DEFAULT", {}).get("pesos_dimensiones", {"Completitud": 0.25, "Unicidad": 0.25, "Validez": 0.25, "Consistencia": 0.25}))
        
        mask_tipo = pl.col('tipo_mat') == tipo

        # A. UNICIDAD
        for col, config in reglas.get("Unicidad", {}).items():
            if col not in df.columns: continue
            
            if config["regla"] == "duplicado_multicampo":
                cols_grupo = config.get("columnas", [col])
                cols_existentes = [c for c in cols_grupo if c in df.columns]
                
                if len(cols_existentes) > 0:
                    exprs_limpias = [pl.col(c).fill_null("").cast(pl.Utf8).str.strip_chars().str.to_uppercase() for c in cols_existentes]
                    mask_regla = mask_tipo & pl.struct(exprs_limpias).is_duplicated() & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '')
                    
                    if config.get("whitelist"):
                        wl = [str(w).strip().upper() for w in config["whitelist"]]
                        mask_regla = mask_regla & ~pl.col(col).cast(pl.Utf8).str.strip_chars().str.to_uppercase().is_in(wl)
                        
                    if config.get("blacklist"):
                        bl = [str(b).strip().upper() for b in config["blacklist"]]
                        mask_regla = mask_regla | (mask_tipo & pl.col(col).cast(pl.Utf8).str.strip_chars().str.to_uppercase().is_in(bl))

                    if config.get("condicion_columna") in df.columns and config.get("condicion_valor"):
                        mask_regla = mask_regla & (pl.col(config["condicion_columna"]).cast(pl.Utf8) == str(config["condicion_valor"]))
                        
                    df = df.with_columns([
                        pl.when(mask_regla).then(pl.col('Score_Unicidad') - config['penalizacion']).otherwise(pl.col('Score_Unicidad')).alias('Score_Unicidad'),
                        pl.when(mask_regla).then(pl.col('Hallazgos_Detallados') + config['mensaje'] + ", ").otherwise(pl.col('Hallazgos_Detallados')).alias('Hallazgos_Detallados')
                    ])

        # B. COMPLETITUD
        for col, config in reglas.get("Completitud", {}).items():
            if col not in df.columns: continue
            if config["regla"] == "nulo":
                
                # --- LA CURA ANTI-NAN ---
                col_str = pl.col(col).cast(pl.Utf8).str.to_lowercase().str.strip_chars()
                mask_regla = mask_tipo & (pl.col(col).is_null() | (col_str == '') | (col_str == 'nan') | (col_str == 'nat') | (col_str == 'null'))
                
                if config.get("condicion_columna") in df.columns and config.get("condicion_valor"):
                    mask_regla = mask_regla & (pl.col(config["condicion_columna"]).cast(pl.Utf8) == str(config["condicion_valor"]))
                
                # --- NUEVO: CREACIÓN DINÁMICA DEL CAMPO BOOLEANO ---
                # 1. Armamos el nombre exacto de la BD (ej: SKU_nulo)
                col_bd = f"{col}_{config['regla']}"
                
                # 2. Si la columna no existe aún, la creamos asumiendo True (1 = Todo bien)
                if col_bd not in df.columns:
                    df = df.with_columns(pl.lit(True).alias(col_bd))
                # --------------------------------------------------

                # 3. Actualizamos el DataFrame
                df = df.with_columns([
                    pl.when(mask_regla).then(pl.col('Score_Completitud') - config['penalizacion']).otherwise(pl.col('Score_Completitud')).alias('Score_Completitud'),
                    pl.when(mask_regla).then(pl.col('Hallazgos_Detallados') + config['mensaje'] + ", ").otherwise(pl.col('Hallazgos_Detallados')).alias('Hallazgos_Detallados'),
                    
                    # NUEVO: Si falla la regla (mask_regla), ponemos False (0). Si no, conservamos el valor que traía.
                    pl.when(mask_regla).then(False).otherwise(pl.col(col_bd)).alias(col_bd)
                ])

        # C. VALIDEZ
        for col, config in reglas.get("Validez", {}).items():
            if col not in df.columns: continue
            
            if config["regla"] == "mayor_a":
                mask_regla = mask_tipo & (pl.col(col).cast(pl.Float64, strict=False).fill_null(0) <= config.get('valor', 0)) & pl.col(col).is_not_null()
            elif config["regla"] == "catalogo" and config.get("catalogo_ref") == "unidades":
                mask_regla = mask_tipo & ~pl.col(col).cast(pl.Utf8).str.to_uppercase().is_in(unidades) & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '')
            elif config["regla"] == "formato_correo":
                patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                mask_regla = mask_tipo & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '') & ~pl.col(col).cast(pl.Utf8).str.contains(patron)
            elif config["regla"] == "regex_custom":
                patron = config.get("patron_regex", "")
                mask_regla = mask_tipo & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '') & ~pl.col(col).cast(pl.Utf8).str.contains(patron)
            elif config["regla"] == "telefono_colombia":
                col_pais = config.get("columna_pais", "Clave de país/región")
                if col_pais in df.columns:
                    tel_str = pl.col(col).cast(pl.Utf8).str.replace_all(" ", "").str.replace_all(r"\+57", "")
                    mask_co = (pl.col(col_pais) == 'CO') & ~tel_str.str.contains(r'^(3\d{9}|60\d{8})$')
                    mask_otros = (pl.col(col_pais) != 'CO') & ~tel_str.str.contains(r'^\+?[0-9]{7,15}$')
                    mask_regla = mask_tipo & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '') & (mask_co | mask_otros)
                else:
                    tel_str = pl.col(col).cast(pl.Utf8).str.replace_all(" ", "")
                    mask_regla = mask_tipo & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '') & ~tel_str.str.contains(r'^\+?[0-9]{7,15}$')
            elif config["regla"] == "longitud_exacta":
                col_str = pl.col(col).cast(pl.Utf8).str.replace(r"\.0$", "")
                mask_regla = mask_tipo & (col_str != 'nan') & (col_str != '') & (col_str.str.len_chars() != config.get('valor', 0))
            else:
                continue

            if config.get("condicion_columna") in df.columns and config.get("condicion_valor"):
                mask_regla = mask_regla & (pl.col(config["condicion_columna"]).cast(pl.Utf8) == str(config["condicion_valor"]))

            df = df.with_columns([
                pl.when(mask_regla).then(pl.col('Score_Validez') - config['penalizacion']).otherwise(pl.col('Score_Validez')).alias('Score_Validez'),
                pl.when(mask_regla).then(pl.col('Hallazgos_Detallados') + config['mensaje'] + ", ").otherwise(pl.col('Hallazgos_Detallados')).alias('Hallazgos_Detallados')
            ])

        # D. CONSISTENCIA
        for col, config in reglas.get("Consistencia", {}).items():
            if col not in df.columns: continue
            if config["regla"] == "mayor_o_igual_columna":
                col_ref = config.get("columna_ref")
                if col_ref and col_ref in df.columns:
                    mask_regla = mask_tipo & (pl.col(col).cast(pl.Float64, strict=False).fill_null(0) < pl.col(col_ref).cast(pl.Float64, strict=False).fill_null(0)) & pl.col(col).is_not_null()
                    
                    if config.get("condicion_columna") in df.columns and config.get("condicion_valor"):
                        mask_regla = mask_regla & (pl.col(config["condicion_columna"]).cast(pl.Utf8) == str(config["condicion_valor"]))

                    df = df.with_columns([
                        pl.when(mask_regla).then(pl.col('Score_Consistencia') - config['penalizacion']).otherwise(pl.col('Score_Consistencia')).alias('Score_Consistencia'),
                        pl.when(mask_regla).then(pl.col('Hallazgos_Detallados') + config['mensaje'] + ", ").otherwise(pl.col('Hallazgos_Detallados')).alias('Hallazgos_Detallados')
                    ])

        # CÁLCULO DE SCORE FINAL DE CALIDAD
        df = df.with_columns([
            pl.when(mask_tipo).then(
                pl.max_horizontal(0.0, pl.col('Score_Completitud')) * p.get('Completitud', 0) + 
                pl.max_horizontal(0.0, pl.col('Score_Validez')) * p.get('Validez', 0) + 
                pl.max_horizontal(0.0, pl.col('Score_Unicidad')) * p.get('Unicidad', 0) + 
                pl.max_horizontal(0.0, pl.col('Score_Consistencia')) * p.get('Consistencia', 0)
            ).otherwise(pl.col('Score_Calidad')).alias('Score_Calidad')
        ])

        # ANULAR SCORES DE DIMENSIONES NO EVALUADAS
        if float(p.get('Completitud', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Completitud')).alias('Score_Completitud'))
        if float(p.get('Validez', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Validez')).alias('Score_Validez'))
        if float(p.get('Unicidad', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Unicidad')).alias('Score_Unicidad'))
        if float(p.get('Consistencia', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Consistencia')).alias('Score_Consistencia'))

    # =========================================================================
    # LIMPIEZA FINAL Y RESUMEN
    # =========================================================================


    
    # =========================================================================
    # ESTADO DE GESTIÓN (Para la BD)
    # =========================================================================
    df = df.with_columns([
        # Si el Score_Calidad es 100 (sin fallas), Estado_Gestion = 1. Si falla algo, 0.
        pl.when(pl.col('Score_Calidad') == 100.0).then(1).otherwise(0).alias('Estado_Gestion'),
        
        # Las descripciones como las pide la tabla
        pl.when(pl.col('Score_Calidad') == 100.0).then(pl.lit("Bueno")).otherwise(pl.lit("Malo")).alias('Estado_Gestion_Desc')
    ])
    
    # Finalmente convertimos a Pandas
    pdf = df.to_pandas()
    
    pdf['Score_Unicidad'] = pdf['Score_Unicidad'].clip(lower=0)
    pdf['Score_Completitud'] = pdf['Score_Completitud'].clip(lower=0)
    pdf['Score_Validez'] = pdf['Score_Validez'].clip(lower=0)
    pdf['Score_Consistencia'] = pdf['Score_Consistencia'].clip(lower=0)
    
    resumen = {}
    if not pdf.empty:
        resumen = {
            'score_global': pdf['Score_Calidad'].mean() if 'Score_Calidad' in pdf.columns else 0,
            'completitud': pdf['Score_Completitud'].mean() if 'Score_Completitud' in pdf.columns else 0,
            'validez': pdf['Score_Validez'].mean() if 'Score_Validez' in pdf.columns else 0,
            'unicidad': pdf['Score_Unicidad'].mean() if 'Score_Unicidad' in pdf.columns else 0,
            'consistencia': pdf['Score_Consistencia'].mean() if 'Score_Consistencia' in pdf.columns else 0
        }

    return pdf, resumen

def generar_excel_saneamiento_memoria(df: pd.DataFrame) -> bytes:
    """Genera el Excel con los errores separados en columnas individuales marcadas con X."""
    if df.empty: return b""
    import io
    output = io.BytesIO()
    
    df_lite = df[df['Score_Calidad'] < 100].copy()
    df_lite = df_lite.sort_values(by="Score_Calidad", ascending=True)
    
    # Definir columnas base
    if 'ID DATO' in df.columns or 'Cliente' in df.columns or 'Proveedor' in df.columns:
        columnas_ideales = ['SKU_num', 'Desc_Material', 'Dirección', 'Correo electrónico', 'Teléfono', 'Clave de país/región', 'Score_Calidad']
    else:
        columnas_ideales = ['SKU', 'SKU_num', 'tipo_mat', 'Desc_Material', 'cod_UEN', 'cod_grupo_art', 'EAN13', 'SKU_anterior', 'peso_neto', 'peso_bruto', 'UoM_peso', 'empaque_SAP', 'Score_Calidad']
    
    columnas_finales = [col for col in columnas_ideales if col in df_lite.columns]
    
    # --- TRANSFORMACIÓN: CREACIÓN DE COLUMNAS DE MARCADORES ---
    fallas_unicas = df_lite['Hallazgos_Detallados'].str.split(', ').explode().unique()
    fallas_unicas = sorted([str(f).strip() for f in fallas_unicas if f and str(f).strip() != "Sin Errores" and str(f) != "nan"])

    # Aplicamos la marca "X" si el error existe en esa fila
    for falla in fallas_unicas:
        df_lite[falla] = df_lite['Hallazgos_Detallados'].apply(lambda x: "X" if falla in str(x) else "")
    
    # Filtramos para tener solo las columnas base y las nuevas columnas de fallas
    df_export = df_lite[columnas_finales + fallas_unicas].copy()
    df_export['Score_Calidad'] = df_export['Score_Calidad'].round(1)

    # Función para que Excel no falle con caracteres raros en nombres de pestañas
    def limpiar_nombre_hoja(nombre: str) -> str:
        for char in ['\\', '/', '?', '*', '[', ']', ':']: nombre = nombre.replace(char, '')
        if "(" in nombre: nombre = nombre.split("(")[0].strip()
        return nombre[:31]

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Pestaña maestra con todas las columnas
        df_export.to_excel(writer, index=False, sheet_name='Matriz_Saneamiento')
        
        # Pestañas individuales (Mantiene tu funcionalidad original, pero con las columnas "X")
        for falla in fallas_unicas:
            df_falla = df_export[df_export[falla] == "X"]
            if not df_falla.empty:
                nombre_hoja = limpiar_nombre_hoja(falla)
                hojas_existentes = writer.sheets.keys()
                base_nombre = nombre_hoja
                contador = 1
                while nombre_hoja in hojas_existentes:
                    nombre_hoja = f"{base_nombre[:28]}_{contador}"
                    contador += 1
                df_falla.to_excel(writer, index=False, sheet_name=nombre_hoja)
        
    return output.getvalue()