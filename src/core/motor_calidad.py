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

def adaptar_reglas_ia_a_motor(json_ia_str: str, dominio: str) -> dict:
    """
    Convierte la salida JSON (texto) generada por la IA en la estructura de diccionario 
    requerida por el motor de Polars (Blindaje Quirúrgico).
    
    Extrae el contenido JSON limpiando cualquier texto adicional de la IA mediante 
    expresiones regulares. Luego, mapea las reglas de la IA a las dimensiones estándar 
    (Completitud, Unicidad, Validez, Consistencia) ajustando la clave objetivo según el dominio.
    
    Args:
        json_ia_str (str): Cadena de texto generada por la IA que contiene (o envuelve) el JSON de reglas.
        dominio (str): El contexto de los datos (ej. "Directorio Comercial", "Maestro de Materiales").
        
    Returns:
        dict: Diccionario estructurado con las reglas adaptadas, o None si ocurre un error en el parseo.
    """
    try:
        # 1. EXTRACCIÓN QUIRÚRGICA DEL JSON (Ignora cualquier saludo o texto de la IA)
        json_limpio = str(json_ia_str)
        match = re.search(r'\{.*\}', json_limpio, re.DOTALL)
        if match:
            json_limpio = match.group(0)
            
        datos_ia = json.loads(json_limpio)
        
        # 2. FLEXIBILIDAD DE ESTRUCTURA
        diccionario_ia = datos_ia.get("diccionario_reglas")
        if not diccionario_ia:
            if isinstance(datos_ia, list): diccionario_ia = datos_ia
            else: return None 

        target_key = "Directorio_Comercial" if "Directorio" in dominio else "DEFAULT"

        reglas_adaptadas = {
            target_key: {
                "pesos_dimensiones": {"Completitud": 0.25, "Unicidad": 0.25, "Validez": 0.25, "Consistencia": 0.25},
                "Completitud": {}, "Validez": {}, "Unicidad": {}, "Consistencia": {}
            }
        }

        for categoria in diccionario_ia:
            dim_cruda = str(categoria.get("dimension_dama", "Validez")).strip().lower()
            if "complet" in dim_cruda: dim = "Completitud"
            elif "unic" in dim_cruda: dim = "Unicidad"
            elif "consist" in dim_cruda: dim = "Consistencia"
            else: dim = "Validez" 

            for regla in categoria.get("reglas_aplicadas", []):
                col_name = str(regla.get("nombre_columna", "")).strip()
                if not col_name: continue
                
                tipo_regla = str(regla.get("regla", "")).strip()
                
                config = {
                    "regla": tipo_regla,
                    "penalizacion": float(regla.get("penalizacion", 50)),
                    "mensaje": str(regla.get("mensaje", f"Error en {col_name}"))
                }
                
                if regla.get("patron_regex"): config["patron_regex"] = str(regla.get("patron_regex")).strip()
                if regla.get("valor"): config["valor"] = float(regla.get("valor"))
                if regla.get("columna_ref"): config["columna_ref"] = str(regla.get("columna_ref")).strip()
                
                if regla.get("condicion_columna") and regla.get("condicion_valor"):
                    config["condicion_columna"] = str(regla.get("condicion_columna")).strip()
                    config["condicion_valor"] = str(regla.get("condicion_valor")).strip()

                reglas_adaptadas[target_key][dim][col_name] = config

        return reglas_adaptadas
    except Exception as e:
        import streamlit as st
        st.error(f"⚠️ Error leyendo las reglas de la IA. Usando reglas por defecto. Detalle: {e}")
        return None

def ejecutar_auditoria_completa(archivo, unidades_permitidas: list, focos, dominio: str = "Maestro de Materiales", reglas_ia_str: str = None) -> Tuple[pd.DataFrame, dict]:
    """
    Motor principal de evaluación de calidad. Procesa un archivo Excel y aplica reglas 
    vectorizadas de completitud, unicidad, validez y consistencia.
    
    Realiza una lectura segura utilizando Pandas para tolerar errores comunes en archivos 
    (como encabezados vacíos), y luego transfiere el procesamiento a Polars para 
    maximizar el rendimiento. Calcula un 'Score_Calidad' global y documenta las 
    fallas específicas por fila.
    
    Args:
        archivo (str, bytes o file-like object): El archivo Excel a evaluar.
        unidades_permitidas (list): Lista de unidades de medida válidas (para reglas de catálogo).
        focos (Any): Parámetro de enfoque de reglas (actualmente no utilizado explícitamente en el cuerpo principal).
        dominio (str, opcional): El contexto comercial de los datos. Por defecto es "Maestro de Materiales".
        reglas_ia_str (str, opcional): Cadena JSON con reglas generadas dinámicamente por la IA.
        
    Returns:
        Tuple[pd.DataFrame, dict]: 
            - pd.DataFrame: Dataframe detallado con las puntuaciones por dimensión, el score final y los hallazgos.
            - dict: Resumen general con el promedio global y por cada dimensión evaluada.
    """
    # =========================================================================
    # LECTURA SEGURA: Pandas perdona Excels sucios (ej. headers vacíos)
    # =========================================================================
    try:
        df_pd = pd.read_excel(archivo, dtype=str)
        if df_pd.empty:
            return pd.DataFrame(), {}
            
        # Limpieza segura de nombres de columnas en Pandas para evitar duplicados en Polars
        df_pd.columns = [str(c).strip() for c in df_pd.columns]
        df = pl.from_pandas(df_pd)
    except Exception as e:
        import streamlit as st
        st.error(f"⚠️ Fallo crítico al leer el Excel. Verifica que el archivo no esté corrupto. Error: {e}")
        return pd.DataFrame(), {}

    if reglas_ia_str:
        reglas_maestras = adaptar_reglas_ia_a_motor(reglas_ia_str, dominio)
        if not reglas_maestras: reglas_maestras = cargar_reglas_json()
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
                # Forzamos todo a texto minúscula y atrapamos los falsos vacíos ("nan", "nat", "null", "")
                col_str = pl.col(col).cast(pl.Utf8).str.to_lowercase().str.strip_chars()
                mask_regla = mask_tipo & (pl.col(col).is_null() | (col_str == '') | (col_str == 'nan') | (col_str == 'nat') | (col_str == 'null'))
                # ------------------------
                
                if config.get("condicion_columna") in df.columns and config.get("condicion_valor"):
                    mask_regla = mask_regla & (pl.col(config["condicion_columna"]).cast(pl.Utf8) == str(config["condicion_valor"]))
                
                df = df.with_columns([
                    pl.when(mask_regla).then(pl.col('Score_Completitud') - config['penalizacion']).otherwise(pl.col('Score_Completitud')).alias('Score_Completitud'),
                    pl.when(mask_regla).then(pl.col('Hallazgos_Detallados') + config['mensaje'] + ", ").otherwise(pl.col('Hallazgos_Detallados')).alias('Hallazgos_Detallados')
                ])

        # C. VALIDEZ
        for col, config in reglas.get("Validez", {}).items():
            if col not in df.columns: continue
            
            if config["regla"] == "mayor_a":
                mask_regla = mask_tipo & (pl.col(col).cast(pl.Float64, strict=False).fill_null(0) <= config.get('valor', 0)) & pl.col(col).is_not_null()
            elif config["regla"] == "catalogo" and config.get("catalogo_ref") == "unidades":
                mask_regla = mask_tipo & ~pl.col(col).cast(pl.Utf8).str.to_uppercase().is_in(unidades_permitidas) & pl.col(col).is_not_null() & (pl.col(col).cast(pl.Utf8) != '')
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

        df = df.with_columns([
            pl.when(mask_tipo).then(
                pl.max_horizontal(0.0, pl.col('Score_Completitud')) * p.get('Completitud', 0) + 
                pl.max_horizontal(0.0, pl.col('Score_Validez')) * p.get('Validez', 0) + 
                pl.max_horizontal(0.0, pl.col('Score_Unicidad')) * p.get('Unicidad', 0) + 
                pl.max_horizontal(0.0, pl.col('Score_Consistencia')) * p.get('Consistencia', 0)
            ).otherwise(pl.col('Score_Calidad')).alias('Score_Calidad')
        ])

        if float(p.get('Completitud', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Completitud')).alias('Score_Completitud'))
        if float(p.get('Validez', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Validez')).alias('Score_Validez'))
        if float(p.get('Unicidad', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Unicidad')).alias('Score_Unicidad'))
        if float(p.get('Consistencia', 0)) == 0.0: df = df.with_columns(pl.when(mask_tipo).then(pl.lit(None, dtype=pl.Float64)).otherwise(pl.col('Score_Consistencia')).alias('Score_Consistencia'))

    df = df.with_columns(
        pl.when(pl.col('Hallazgos_Detallados') == "")
        .then(pl.lit("Sin Errores"))
        .otherwise(pl.col('Hallazgos_Detallados').str.replace(r", $", ""))
        .alias('Hallazgos_Detallados')
    )
    
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
    """
    Genera un archivo Excel binario en memoria con los registros que no alcanzaron el 100% de calidad.
    
    Crea un reporte enfocado en el saneamiento:
    1. Filtra los datos perfectos.
    2. Reduce las columnas a un set 'ideal' dependiendo del dominio detectado.
    3. Genera una hoja resumen general ("Resumen_General").
    4. Crea hojas separadas por cada tipo de error (hallazgo) para facilitar la corrección.
    
    Args:
        df (pd.DataFrame): El dataframe resultante de la auditoría de calidad.
        
    Returns:
        bytes: El contenido del archivo Excel en formato binario, listo para ser descargado o enviado.
    """
    if df.empty: return b""
    output = io.BytesIO()
    df_lite = df[df['Score_Calidad'] < 100].copy()
    df_lite = df_lite.sort_values(by="Score_Calidad", ascending=True)
    
    if 'ID DATO' in df.columns or 'Cliente' in df.columns or 'Proveedor' in df.columns:
        columnas_ideales = ['SKU_num', 'Desc_Material', 'Dirección', 'Correo electrónico', 'Teléfono', 'Clave de país/región', 'Score_Calidad', 'Hallazgos_Detallados']
    else:
        columnas_ideales = ['SKU_num', 'tipo_mat', 'Desc_Material', 'cod_UEN', 'cod_grupo_art', 'EAN13', 'SKU_anterior', 'peso_neto', 'peso_bruto', 'UoM_peso', 'empaque_SAP', 'Score_Calidad', 'Hallazgos_Detallados']
    
    columnas_finales = [col for col in columnas_ideales if col in df_lite.columns]
    df_lite = df_lite[columnas_finales]
    
    df_lite['Score_Calidad'] = df_lite['Score_Calidad'].round(1)
    df_lite['Nuevo_Valor_Saneado'] = ""
    
    fallas_unicas = df_lite['Hallazgos_Detallados'].str.split(', ').explode().unique()
    fallas_unicas = [str(f).strip() for f in fallas_unicas if f and str(f).strip() != "Sin Errores" and str(f) != "nan"]

    def limpiar_nombre_hoja(nombre: str) -> str:
        for char in ['\\', '/', '?', '*', '[', ']', ':']: nombre = nombre.replace(char, '')
        if "(" in nombre: nombre = nombre.split("(")[0].strip()
        return nombre[:31]

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_lite.to_excel(writer, index=False, sheet_name='Resumen_General')
        for falla in fallas_unicas:
            df_falla = df_lite[df_lite['Hallazgos_Detallados'].str.contains(falla, regex=False, na=False)]
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