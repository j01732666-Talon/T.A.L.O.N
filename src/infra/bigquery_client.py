"""
import streamlit as st
import polars as pl
import os
from google.oauth2 import service_account
from google.cloud import bigquery

def extraer_maestro_materiales():
    try:
        # 1. Ruta al archivo JSON (asumiendo que está en la raíz del proyecto)
        ruta_credenciales = "credenciales_gcp.json"
        
        # Validamos que el archivo realmente esté ahí para evitar errores raros
        if not os.path.exists(ruta_credenciales):
            raise FileNotFoundError(f"No se encontró el archivo {ruta_credenciales} en la raíz del proyecto.")

        # 2. Google lee el JSON y crea las credenciales automáticamente (¡Sin pelear con saltos de línea!)
        credentials = service_account.Credentials.from_service_account_file(ruta_credenciales)
        
        # 3. Nos conectamos usando el project_id que viene dentro del mismo JSON
        client = bigquery.Client(credentials=credentials, project=credentials.project_id)

        # 4. Ejecutamos la consulta
        query = "SELECT * FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES`"
        query_job = client.query(query)
        
        # 5. Retornamos los datos en Polars
        return pl.from_arrow(query_job.result().to_arrow())

    except Exception as e:
        raise Exception(f"Fallo en la conexión o consulta a BigQuery: {str(e)}")
    
"""
import streamlit as st
import polars as pl
import pandas as pd
import os
from google.oauth2 import service_account
from google.cloud import bigquery

def _obtener_cliente_bq():
    """Función auxiliar interna para no repetir el código de conexión."""
    ruta_credenciales = "credenciales_gcp.json"
    if not os.path.exists(ruta_credenciales):
        raise FileNotFoundError(f"No se encontró el archivo {ruta_credenciales} en la raíz del proyecto.")
    
    credentials = service_account.Credentials.from_service_account_file(ruta_credenciales)
    return bigquery.Client(credentials=credentials, project=credentials.project_id)


def extraer_materiales_pendientes() -> pl.DataFrame:
    """
    Carga Incremental (Delta): Busca en la vista maestra solo los materiales que 
    aún NO han sido insertados en la tabla de auditoría (Materiales_TALONBD).
    """
    try:
        client = _obtener_cliente_bq()

        # Usamos LEFT JOIN para traer solo lo que no está en TALONBD.
        # Si la tabla destino está vacía, traerá los ~20,000 registros iniciales.
        # En el día a día, traerá solo los nuevos.
        # Usamos LEFT JOIN para traer solo lo que no está en TALONBD.
        # Usamos LEFT JOIN y forzamos ambos campos a STRING con CAST para evitar errores de tipo
        query = """
            SELECT origen.* FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES` AS origen
            LEFT JOIN `brinsa-it-data-lake.SC_TALON.Materiales_TALONBD` AS destino
              ON CAST(origen.SKU AS STRING) = CAST(destino.SKU AS STRING)
            WHERE destino.SKU IS NULL
        """
        # Nota: Si más adelante quieres validar también por fecha de modificación, 
        # puedes añadir: OR origen.fecha_actualiza > destino.Fecha_Actualizacion

        query_job = client.query(query)
        df_resultado = pl.from_arrow(query_job.result().to_arrow())
        
        return df_resultado

    except Exception as e:
        raise Exception(f"Fallo en la extracción incremental: {str(e)}")


def cargar_resultados_auditoria(df_resultados) -> int:
    """
    Inserción Masiva (Bulk Insert) a BigQuery.
    """
    if df_resultados is None or len(df_resultados) == 0:
        return 0

    try:
        client = _obtener_cliente_bq()
        table_id = "brinsa-it-data-lake.SC_TALON.Materiales_TALONBD"

        # 1. Nos aseguramos de tener un DataFrame de Pandas
        if isinstance(df_resultados, pl.DataFrame):
            df_pd = df_resultados.to_pandas()
        else:
            df_pd = df_resultados.copy()

        # --- NUEVO: LA CURA DE TIPOS DE DATOS (MÉTODO PANDAS) ---
        # Convertimos la columna a tipo string nativo de pandas para que BQ la acepte
        if "Usuario_Auditor" in df_pd.columns:
            df_pd["Usuario_Auditor"] = df_pd["Usuario_Auditor"].astype("string")
        # --------------------------------------------------------

        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND", 
            ignore_unknown_values=True        
        )

        job = client.load_table_from_dataframe(
            df_pd, table_id, job_config=job_config
        )

        job.result()  
        return job.output_rows

    except Exception as e:
        raise Exception(f"Fallo insertando los datos en BigQuery: {str(e)}")
    
def extraer_anomalias_pendientes() -> pl.DataFrame:
    """
    Trae los datos crudos de SAP, pero SOLO de los SKUs que ya están 
    marcados como "Malos" (Estado_Gestion = 0) en la base de datos.
    Esto alimenta la interfaz de forma ultrarrápida.
    """
    try:
        client = _obtener_cliente_bq()
        query = """
            SELECT origen.* FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES` AS origen
            INNER JOIN `brinsa-it-data-lake.SC_TALON.Materiales_TALONBD` AS destino
              ON CAST(origen.SKU AS STRING) = CAST(destino.SKU AS STRING)
            WHERE destino.Estado_Gestion = 0
        """
        query_job = client.query(query)
        df_resultado = pl.from_arrow(query_job.result().to_arrow())
        return df_resultado
    except Exception as e:
        raise Exception(f"Fallo al extraer las anomalías: {str(e)}")