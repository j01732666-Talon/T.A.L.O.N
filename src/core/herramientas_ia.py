import pandas as pd
import os

def obtener_ruta_data_ref():
    """
    Encuentra dinámicamente la ruta hacia la carpeta 'data_ref'.
    
    Busca primero en el mismo nivel del directorio 'src' y, si no se encuentra allí, 
    retrocede un nivel en la jerarquía hacia el directorio raíz.
    
    Returns:
        str: La ruta absoluta hacia el directorio 'data_ref'.
    """
    """Encuentra dinámicamente la carpeta data_ref."""
    dir_actual = os.path.dirname(os.path.abspath(__file__)) # src/core
    dir_src = os.path.dirname(dir_actual)                   # src
    
    # 1. Buscar si data_ref está dentro de src/
    ruta_interna = os.path.join(dir_src, "data_ref")
    if os.path.exists(ruta_interna):
        return ruta_interna
        
    # 2. Buscar si data_ref se quedó en la raíz (una carpeta más atrás)
    dir_raiz = os.path.dirname(dir_src)
    return os.path.join(dir_raiz, "data_ref")

def consultar_tabla_referencias(termino_busqueda: str) -> str:
    """
    Busca un término específico dentro del archivo 'Tablas de Referencia.xlsx'.
    
    Itera sobre todas las pestañas del archivo, procesa las categorías definidas 
    en las primeras filas y busca coincidencias exactas o parciales del término 
    (ignorando mayúsculas/minúsculas). La búsqueda se realiza tanto en el nombre 
    de la categoría como en sus datos asociados.
    
    Args:
        termino_busqueda (str): El texto o valor que se desea encontrar.
        
    Returns:
        str: Una cadena de texto formateada con todas las coincidencias encontradas, 
             organizadas por categoría y pestaña. Retorna un mensaje de error si 
             falla la lectura o si no encuentra el archivo.
    """
    ruta_base = obtener_ruta_data_ref()
    ruta_excel = os.path.join(ruta_base, "Tablas de Referencia.xlsx")
    
    if not os.path.exists(ruta_excel):
        return "Error: No se encontró el archivo 'Tablas de Referencia.xlsx'."
        
    try:
        xls = pd.ExcelFile(ruta_excel)
        resultados = []
        termino_lower = str(termino_busqueda).lower()
        
        for hoja in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=hoja, header=None)
            if df.empty or len(df) < 2: 
                continue
            
            df.iloc[0] = df.iloc[0].ffill()
            categorias = [c for c in df.iloc[0].unique() if pd.notna(c)]
            
            for cat in categorias:
                cols_cat = df.columns[df.iloc[0] == cat].tolist()
                cat_str = str(cat).strip()
                sub_enc = [str(x).strip() for x in df.iloc[1, cols_cat].tolist()]
                datos_cat = df.iloc[2:, cols_cat]
                match_categoria = termino_lower in cat_str.lower()
                
                coincidencias = []
                for _, fila in datos_cat.iterrows():
                    fila_vals = fila.tolist()
                    if all(pd.isna(v) or str(v).strip() == "" for v in fila_vals): 
                        continue
                    
                    match_valor = any(termino_lower in str(v).lower() for v in fila_vals)
                    
                    if match_categoria or match_valor:
                        pares = []
                        for i, val in enumerate(fila_vals):
                            if pd.notna(val) and str(val).strip() != "":
                                etiqueta = sub_enc[i] if i < len(sub_enc) else "Dato"
                                pares.append(f"{etiqueta}: {val}")
                        if pares:
                            coincidencias.append(" | ".join(pares))
                
                if coincidencias:
                    resultados.append(f"\n--- Categoría: [{cat_str}] (Pestaña: {hoja}) ---")
                    for c in list(set(coincidencias)):
                        resultados.append(f"- {c}")

        if not resultados:
            return f"No se encontraron coincidencias para '{termino_busqueda}'."
        return "\n".join(resultados)
        
    except Exception as e:
        return f"Error leyendo las tablas de referencia: {str(e)}"

def consultar_directorio_comercial(termino_busqueda: str) -> str:
    """
    Busca un término específico en el conjunto de archivos del directorio comercial.
    
    Explora los archivos predefinidos (Proveedores, Clientes, Materiales), leyendo 
    todas sus pestañas y aplicando un filtro que devuelve las filas completas 
    donde el término de búsqueda aparezca en al menos una columna.
    
    Args:
        termino_busqueda (str): El texto o valor que se desea encontrar.
        
    Returns:
        str: Una cadena de texto formateada que contiene las filas de los dataframes 
             donde hubo coincidencias, indicando el archivo y pestaña de origen. 
             Retorna un mensaje indicando si hubo errores o si no se encontraron datos.
    """
    ruta_base = obtener_ruta_data_ref()
    archivos = [
        ("Proveedores", "LFA1 - Proveedores.xlsx"),
        ("Clientes", "KNA1 - Cliente.xlsx"),
        ("Materiales", "Maestros de Materiales.xlsx")
    ]
        
    resultados = []
    termino_lower = str(termino_busqueda).lower()
    
    for tipo, nombre_archivo in archivos:
        ruta = os.path.join(ruta_base, nombre_archivo)
        if not os.path.exists(ruta):
            continue
            
        try:
            xls = pd.ExcelFile(ruta)
            for hoja in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=hoja)
                mask = df.astype(str).apply(lambda col: col.str.contains(termino_lower, case=False, na=False)).any(axis=1)
                df_filtrado = df[mask]
                
                if not df_filtrado.empty:
                    resultados.append(f"\n--- Directorio de {tipo} (Archivo: {nombre_archivo} | Pestaña: {hoja}) ---")
                    resultados.append(df_filtrado.to_string(index=False))
                    
        except Exception as e:
            resultados.append(f"Error procesando {nombre_archivo}: {str(e)}")
            
    if not resultados:
        return f"No se encontró el término '{termino_busqueda}' en los directorios comerciales."
        
    return "\n\n".join(resultados)