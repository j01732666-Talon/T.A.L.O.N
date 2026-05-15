import streamlit as st
import polars as pl
import os
import pyarrow as pa
from google.oauth2 import service_account
from google.cloud import bigquery

try:
    import db_dtypes  # noqa: F401 — registra extensiones BigQuery en Arrow/Pandas cuando está instalado
except ImportError:
    pass

# Ruta absoluta al JSON de credenciales (raíz del proyecto, dos niveles arriba de src/infra/)
_RUTA_CREDENCIALES = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "credenciales_gcp.json")
)


@st.cache_resource
def get_bq_client() -> bigquery.Client:
    """Cliente BigQuery cacheado — se instancia una sola vez por ciclo de vida de la app."""
    if not os.path.exists(_RUTA_CREDENCIALES):
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales GCP en: {_RUTA_CREDENCIALES}"
        )
    credentials = service_account.Credentials.from_service_account_file(_RUTA_CREDENCIALES)
    return bigquery.Client(credentials=credentials, project=credentials.project_id)


def _obtener_cliente_bq() -> bigquery.Client:
    """Alias interno — delega al cliente cacheado para no instanciar múltiples veces."""
    return get_bq_client()


def _arrow_query_job_a_polars(query_job) -> pl.DataFrame:
    """
    BigQuery marca DATETIME con extensión Arrow `google:sqlType:datetime`.
    Polars/PyArrow avisan si no está registrada; cast al tipo de almacenamiento elimina el ruido
    y deja timestamps/datetimes estándar.
    """
    table = query_job.result().to_arrow()
    arrays = []
    for i in range(table.num_columns):
        field = table.schema.field(i)
        col = table.column(i)
        typ = field.type
        if isinstance(typ, pa.ExtensionType):
            col = col.cast(typ.storage_type)
        elif getattr(pa.types, "is_extension_type", lambda t: False)(typ) and hasattr(typ, "storage_type"):
            col = col.cast(typ.storage_type)
        arrays.append(col)
    clean = pa.table(arrays, names=table.column_names)
    return pl.from_arrow(clean)


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
        return _arrow_query_job_a_polars(query_job)

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
            SET
                destino.Fecha_Actualizacion   = origen.fecha_actualiza,
                destino.Fecha_Ingreso         = origen.fecha_creacion,
                destino.Fecha_Actualizacion_M = CURRENT_TIMESTAMP()
            FROM (
                SELECT
                    SKU,
                    fecha_actualiza,
                    fecha_creacion,
                    ROW_NUMBER() OVER (PARTITION BY SKU ORDER BY fecha_actualiza DESC) AS rn
                FROM `brinsa-it-data-lake.SC_TALON.VW_MAESTRO_MATERIALES`
            ) AS origen
            WHERE CAST(destino.SKU AS STRING) = CAST(origen.SKU AS STRING)
              AND origen.rn = 1
              AND IFNULL(CAST(origen.fecha_actualiza AS STRING),      '1900-01-01')
               != IFNULL(CAST(destino.Fecha_Actualizacion AS STRING), '1900-01-01')
        """

        job = client.query(query_update)
        job.result()
        return job.num_dml_affected_rows or 0

    except Exception as e:
        raise Exception(f"Fallo al actualizar fechas en Materiales_TALONBD: {str(e)}")


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
        return _arrow_query_job_a_polars(query_job)
    except Exception as e:
        raise Exception(f"Fallo al extraer las anomalías: {str(e)}")