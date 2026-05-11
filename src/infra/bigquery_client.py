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
    Carga Incremental — Caso A: SKUs que aún NO existen en Materiales_TALONBD.
    Si la tabla destino está vacía trae el universo completo (~20 000 registros).
    En el día a día solo devuelve los SKUs verdaderamente nuevos.
    """
    try:
        client = _obtener_cliente_bq()

        query = """
            SELECT origen.*
            FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES` AS origen
            LEFT JOIN `brinsa-it-data-lake.SC_TALON.Materiales_TALONBD` AS destino
                ON CAST(origen.SKU AS STRING) = CAST(destino.SKU AS STRING)
            WHERE destino.SKU IS NULL
        """

        query_job = client.query(query)
        df_resultado = pl.from_arrow(query_job.result().to_arrow())
        return df_resultado

    except Exception as e:
        raise Exception(f"Fallo en la extracción incremental (Caso A): {str(e)}")


def actualizar_fechas_materiales() -> int:
    """
    Actualización Incremental — Caso B: SKUs que ya existen en Materiales_TALONBD
    pero cuya fecha_actualiza en la vista maestra difiere de Fecha_Actualizacion
    en la tabla de auditoría.

    Ejecuta un UPDATE DML en BigQuery y devuelve el número de filas afectadas.
    """
    try:
        client = _obtener_cliente_bq()

        query_update = """
            UPDATE `brinsa-it-data-lake.SC_TALON.Materiales_TALONBD` AS destino
            SET destino.Fecha_Actualizacion = origen.fecha_actualiza, 
            destino.Fecha_Ingreso = origen.fecha_creacion,  -- Se agrega esta línea
            destino.Fecha_Actualizacion_M = CURRENT_TIMESTAMP()
            FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES` AS origen
            WHERE CAST(destino.SKU AS STRING) = CAST(origen.SKU AS STRING)
              AND IFNULL(CAST(origen.fecha_actualiza AS STRING),      '1900-01-01')
               != IFNULL(CAST(destino.Fecha_Actualizacion AS STRING), '1900-01-01')
        """

        job = client.query(query_update)
        job.result()
        return job.num_dml_affected_rows or 0

    except Exception as e:
        raise Exception(f"Fallo al actualizar fechas en Materiales_TALONBD: {str(e)}")


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
    Trae los datos crudos de SAP solo de los SKUs marcados como
    "Malos" (Estado_Gestion = 0) en la tabla de auditoría.

    Usa EXISTS en lugar de INNER JOIN para evitar registros duplicados
    cuando un mismo SKU tiene múltiples entradas en Materiales_TALONBD.
    """
    try:
        client = _obtener_cliente_bq()
        query = """
            SELECT origen.*
            FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES` AS origen
            WHERE EXISTS (
                SELECT 1
                FROM `brinsa-it-data-lake.SC_TALON.Materiales_TALONBD` AS destino
                WHERE CAST(origen.SKU AS STRING) = CAST(destino.SKU AS STRING)
                  AND destino.Estado_Gestion = 0
            )
        """
        query_job = client.query(query)
        df_resultado = pl.from_arrow(query_job.result().to_arrow())
        return df_resultado
    except Exception as e:
        raise Exception(f"Fallo al extraer las anomalías: {str(e)}")