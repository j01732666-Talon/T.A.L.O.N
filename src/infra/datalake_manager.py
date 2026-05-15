"""
Gestor de persistencia — Data Lake Cloud (BigQuery).
Reemplaza DuckDB local por la tabla Historial_Auditorias en BigQuery,
eliminando la dependencia de rutas locales y ficheros .duckdb.

API pública sin cambios:
    inicializar_datalake()
    guardar_auditoria(df_detalle, usuario, dominio, res_dinamico, materiales) -> str
    obtener_historial_metricas() -> pd.DataFrame
"""
import pandas as pd
import time
import streamlit as st
from datetime import datetime, timezone

TABLE_HISTORIAL = "brinsa-it-data-lake.SC_TALON.Historial_Auditorias"


def _client():
    """Devuelve el cliente BigQuery cacheado (instanciado en bigquery_client.py)."""
    from infra.bigquery_client import get_bq_client
    return get_bq_client()


@st.cache_resource
def inicializar_datalake() -> None:
    """
    Crea la tabla Historial_Auditorias en BigQuery si no existe.
    Se ejecuta una sola vez por ciclo de vida de la aplicación gracias al caché.
    """
    query = f"""
        CREATE TABLE IF NOT EXISTS `{TABLE_HISTORIAL}` (
            id_ejecucion        STRING,
            fecha               TIMESTAMP,
            usuario             STRING,
            dominio             STRING,
            materiales_auditados STRING,
            total_registros     INT64,
            score_global        FLOAT64,
            completitud         FLOAT64,
            validez             FLOAT64,
            unicidad            FLOAT64,
            consistencia        FLOAT64
        )
    """
    _client().query(query).result()


def obtener_historial_metricas() -> pd.DataFrame:
    """
    Consulta y recupera el registro histórico de todas las auditorías realizadas.

    Returns:
        pd.DataFrame: DataFrame con el historial de métricas, ordenado por fecha descendente.
                      Devuelve un DataFrame vacío si ocurre cualquier error.
    """
    try:
        query = f"SELECT * FROM `{TABLE_HISTORIAL}` ORDER BY fecha DESC"
        return _client().query(query).result().to_dataframe()
    except Exception:
        return pd.DataFrame()


def guardar_auditoria(
    df_detalle: pd.DataFrame,
    usuario: str,
    dominio: str,
    res_dinamico: dict,
    materiales: list,
) -> str:
    """
    Registra las métricas de una auditoría en la tabla Historial_Auditorias de BigQuery.

    Args:
        df_detalle (pd.DataFrame): El conjunto de datos evaluado con los hallazgos.
        usuario (str): El identificador (email) del usuario que ejecutó la auditoría.
        dominio (str): El contexto de los datos analizados (ej. "Maestro de Materiales").
        res_dinamico (dict): Diccionario con las métricas y scores calculados por el motor.
        materiales (list): Lista de los tipos de materiales específicos evaluados.

    Returns:
        str: El identificador único generado para esta ejecución (id_ejecucion).
    """
    id_ejecucion = f"AUD_{int(time.time())}"
    materiales_str = ", ".join(materiales) if materiales else "Todos"

    def _safe_float(val) -> float:
        try:
            result = float(val)
            return result if result == result else 0.0  # NaN check
        except (TypeError, ValueError):
            return 0.0

    row = {
        "id_ejecucion":         id_ejecucion,
        "fecha":                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "usuario":              usuario,
        "dominio":              dominio,
        "materiales_auditados": materiales_str,
        "total_registros":      len(df_detalle),
        "score_global":         _safe_float(res_dinamico.get("score_global")),
        "completitud":          _safe_float(res_dinamico.get("completitud")),
        "validez":              _safe_float(res_dinamico.get("validez")),
        "unicidad":             _safe_float(res_dinamico.get("unicidad")),
        "consistencia":         _safe_float(res_dinamico.get("consistencia")),
    }

    try:
        errors = _client().insert_rows_json(TABLE_HISTORIAL, [row])
        if errors:
            raise Exception(str(errors))
    except Exception as e:
        st.toast(f"No se pudo registrar en el historial: {e}", icon="⚠️")

    return id_ejecucion
