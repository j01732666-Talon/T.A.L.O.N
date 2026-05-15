"""
Persistencia de auditorías en BigQuery: estados de gestión y carga masiva a Materiales_TALONBD.
"""
from __future__ import annotations

import polars as pl
import pandas as pd
from google.cloud import bigquery

from infra.bigquery_client import get_bq_client

# Mismo criterio que `motor_calidad.ejecutar_auditoria_completa` (tolerancia float).
UMBRAL_SCORE_ESTADO_BUENO = 99.99

TABLA_MATERIALES_AUDITORIA = "brinsa-it-data-lake.SC_TALON.Materiales_TALONBD"

# Columnas que suelen llegar como object/mixtas desde SAP/Polars y disparan
# UserWarning en google.cloud.bigquery._pandas_helpers al inferir esquema.
_COLUMNAS_TEXTO_EXPLICITO_LOAD_BQ = frozenset(
    {
        "SKU_MPT",
        "SKU",
        "Usuario_Auditor",
    }
)


def _nombres_campos_tabla(client: bigquery.Client, table_id: str) -> frozenset[str]:
    table = client.get_table(table_id)
    return frozenset(f.name for f in table.schema)


def _dataframe_solo_columnas_tabla(df: pd.DataFrame, campos_permitidos: frozenset[str]) -> pd.DataFrame:
    """Solo columnas que ya existen en la tabla destino (BigQuery no permite añadir campos en APPEND)."""
    cols = [c for c in df.columns if c in campos_permitidos]
    if not cols:
        raise ValueError(
            "Ninguna columna del DataFrame coincide con el esquema de la tabla destino en BigQuery."
        )
    return df[cols].copy()
def _serie_a_string_nullable(s: pd.Series) -> pd.Series:
    return s.map(lambda v: pd.NA if pd.isna(v) else str(v)).astype(pd.StringDtype())


def _normalizar_tipos_para_load_bigquery(df: pd.DataFrame) -> None:
    """Fuerza dtypes claros para que load_table_from_dataframe no falle la inferencia."""
    for col in _COLUMNAS_TEXTO_EXPLICITO_LOAD_BQ:
        if col in df.columns:
            df[col] = _serie_a_string_nullable(df[col])


def _dataframe_sin_columnas_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    """Conserva la última ocurrencia de cada nombre (valores del motor suelen ir al final)."""
    if df.empty or not df.columns.duplicated().any():
        return df
    return df.loc[:, ~df.columns.duplicated(keep="last")].copy()


def _dedupe_columnas_inplace(df: pd.DataFrame) -> None:
    """Igual que _dataframe_sin_columnas_duplicadas pero sin romper la referencia que recibe el caller."""
    if df.empty or not df.columns.duplicated().any():
        return
    dedup = df.loc[:, ~df.columns.duplicated(keep="last")]
    df.drop(columns=list(df.columns), inplace=True)
    for col in dedup.columns:
        df[col] = dedup[col]


def asignar_estado_gestion_para_bigquery(df: pd.DataFrame) -> None:
    """
    Deriva `Estado_Gestion` (y descripción) desde `Score_Calidad` antes de insertar en BigQuery.
    Mutación in-place del DataFrame.
    """
    if df is None or df.empty:
        return

    _dedupe_columnas_inplace(df)

    if "Score_Calidad" not in df.columns:
        df["Estado_Gestion"] = 0
        df["Estado_Gestion_Desc"] = "Malo"
        return

    scores = pd.to_numeric(df["Score_Calidad"], errors="coerce").fillna(100.0)
    bueno = scores >= UMBRAL_SCORE_ESTADO_BUENO
    df["Estado_Gestion"] = bueno.astype("int64")
    df["Estado_Gestion_Desc"] = df["Estado_Gestion"].map({1: "Bueno", 0: "Malo"})


def cargar_resultados_auditoria(df_resultados) -> int:
    """
    Inserción masiva (bulk append) del resultado de auditoría en Materiales_TALONBD.
    """
    if df_resultados is None or len(df_resultados) == 0:
        return 0

    try:
        client = get_bq_client()

        if isinstance(df_resultados, pl.DataFrame):
            df_pd = df_resultados.to_pandas()
        else:
            df_pd = df_resultados.copy()

        df_pd = _dataframe_sin_columnas_duplicadas(df_pd)

        campos_tabla = _nombres_campos_tabla(client, TABLA_MATERIALES_AUDITORIA)
        df_pd = _dataframe_solo_columnas_tabla(df_pd, campos_tabla)

        _normalizar_tipos_para_load_bigquery(df_pd)

        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            ignore_unknown_values=True,
        )

        job = client.load_table_from_dataframe(
            df_pd, TABLA_MATERIALES_AUDITORIA, job_config=job_config
        )

        job.result()
        return job.output_rows

    except Exception as e:
        raise Exception(f"Fallo insertando los datos en BigQuery: {str(e)}") from e
