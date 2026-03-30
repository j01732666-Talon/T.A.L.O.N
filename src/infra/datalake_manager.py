"""
Gestor de persistencia local (Data Lake Serverless).
Utiliza DuckDB para métricas históricas y Parquet para almacenamiento columnar de detalles.
"""
import duckdb
import pandas as pd
import os
import time

# Definición de rutas (Pueden ajustarse a una unidad de red corporativa, ej. Z:/DataLake)
DIR_DATALAKE = "datalake_local"
DIR_PARQUET = os.path.join(DIR_DATALAKE, "detalle_parquet")
DB_PATH = os.path.join(DIR_DATALAKE, "talon_metastore.duckdb")

def inicializar_datalake():
    os.makedirs(DIR_PARQUET, exist_ok=True)
    # El 'with' asegura que la conexión se cierre sola al terminar el bloque
    with duckdb.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS historial_auditorias (
                id_ejecucion VARCHAR,
                fecha TIMESTAMP,
                usuario VARCHAR,
                dominio VARCHAR,
                materiales_auditados VARCHAR,
                total_registros INTEGER,
                score_global DOUBLE,
                completitud DOUBLE,
                validez DOUBLE,
                unicidad DOUBLE,
                consistencia DOUBLE,
                ruta_parquet VARCHAR
            )
        """)

def obtener_historial_metricas() -> pd.DataFrame:
    with duckdb.connect(DB_PATH, read_only=True) as con:
        df_hist = con.execute("SELECT * FROM historial_auditorias ORDER BY fecha DESC").df()
    return df_hist

def guardar_auditoria(df_detalle: pd.DataFrame, usuario: str, dominio: str, res_dinamico: dict, materiales: list) -> str:
    """
    Exporta el DataFrame de detalle a formato Parquet y registra las métricas en DuckDB.
    Retorna el ID de la ejecución.
    """
    id_ejecucion = f"AUD_{int(time.time())}"
    ruta_archivo_parquet = os.path.join(DIR_PARQUET, f"{id_ejecucion}.parquet")
    
    # Exportar a Parquet (comprimido, rápido y eficiente en memoria)
    df_detalle.to_parquet(ruta_archivo_parquet, engine='pyarrow', index=False)
    
    # Preparar datos para DuckDB
    materiales_str = ", ".join(materiales) if materiales else "Todos"
    
    con = duckdb.connect(DB_PATH)
    con.execute("""
        INSERT INTO historial_auditorias 
        VALUES (?, current_timestamp, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_ejecucion, 
        usuario, 
        dominio, 
        materiales_str, 
        len(df_detalle),
        res_dinamico['score_global'], 
        res_dinamico['completitud'],
        res_dinamico['validez'], 
        res_dinamico['unicidad'], 
        res_dinamico['consistencia'],
        ruta_archivo_parquet
    ))
    con.close()
    
    return id_ejecucion

def obtener_historial_metricas() -> pd.DataFrame:
    """
    Consulta la base de datos DuckDB y retorna el histórico de ejecuciones.
    """
    con = duckdb.connect(DB_PATH)
    df_hist = con.execute("SELECT * FROM historial_auditorias ORDER BY fecha DESC").df()
    con.close()
    return df_hist