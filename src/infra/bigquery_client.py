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