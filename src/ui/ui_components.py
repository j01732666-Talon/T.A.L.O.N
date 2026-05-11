"""
Componentes modulares de la interfaz de usuario — T.A.L.O.N
Sistema de Diseño: Enterprise Slate / Azure — Premium, limpio, monocromático.
Paleta: Grises fríos (#070B12→#1C2432) · Acento único #3B82F6 (familia azul).

Los componentes leen st.session_state['idioma'] en tiempo de render
para adaptar etiquetas y textos sin necesidad de re-importar el módulo.
"""
import streamlit as st
import pandas as pd
import altair as alt
from collections import Counter
from typing import Dict, Any
import polars as pl

from ui.theme import (
    ACCENT_PRIMARY, ACCENT_HOVER,
    obtener_color_semaforo, get_theme_colors,
)

# ─────────────────────────────────────────────
#  HELPERS DE TEMA E IDIOMA
# ─────────────────────────────────────────────
def _tc() -> dict:
    """Paleta del tema oscuro (único tema activo)."""
    return get_theme_colors(False)


_LABELS = {
    'es': {
        'score_global':    'Score Global',
        'completitud':     'Completitud',
        'validez':         'Validez',
        'unicidad':        'Unicidad',
        'consistencia':    'Consistencia',
        'salud':           'Salud General de los Datos',
        'comparativa':     'Comparativa de Dimensiones',
        'top_anomalias':   'Top Anomalías Detectadas',
        'calidad_mat':     'Calidad por Tipo de Material',
        'tipo_falla':      'Tipo de Falla',
        'reg_afectados':   'Registros Afectados',
        'sin_anomalias':   'Sin anomalías en la selección actual.',
        'sin_anom_esp':    'Sin anomalías específicas en esta vista.',
        'sin_tipo_mat':    'No hay datos de tipo de material para agrupar.',
        'sin_hallazgos':   'No hay hallazgos o anomalías para mostrar.',
        'pendiente':       'Pendiente',
        'gestionado':      'Gestionado',
        'dimension_lbl':   'Dimensión',
        'score_lbl':       'Score',
        'categoria_lbl':   'Categoría',
        'score_prom_lbl':  'Score Promedio',
        'sin_datos_anom':  'Sin datos — las anomalías aparecerán aquí',
        'sin_datos_mat':   'Sin datos — el desglose por material aparecerá aquí',
    },
    'en': {
        'score_global':    'Global Score',
        'completitud':     'Completeness',
        'validez':         'Validity',
        'unicidad':        'Uniqueness',
        'consistencia':    'Consistency',
        'salud':           'Overall Data Health',
        'comparativa':     'Dimension Comparison',
        'top_anomalias':   'Top Detected Anomalies',
        'calidad_mat':     'Quality by Material Type',
        'tipo_falla':      'Failure Type',
        'reg_afectados':   'Affected Records',
        'sin_anomalias':   'No anomalies in current selection.',
        'sin_anom_esp':    'No specific anomalies in this view.',
        'sin_tipo_mat':    'No material type data to group by.',
        'sin_hallazgos':   'No findings or anomalies to display.',
        'pendiente':       'Pending',
        'gestionado':      'Managed',
        'dimension_lbl':   'Dimension',
        'score_lbl':       'Score',
        'categoria_lbl':   'Category',
        'score_prom_lbl':  'Avg Score',
        'sin_datos_anom':  'No data — anomalies will appear here',
        'sin_datos_mat':   'No data — material breakdown will appear here',
    },
}


def _lbl(key: str) -> str:
    """Etiqueta traducida según el idioma de la sesión."""
    lang = st.session_state.get('idioma', 'es')
    return _LABELS.get(lang, _LABELS['es']).get(key, key)


# ─────────────────────────────────────────────
#  MEDIDOR SVG PREMIUM — Anillo con glow
# ─────────────────────────────────────────────
def crear_grafico_medidor(titulo: str, valor: float) -> None:
    """
    Anillo SVG premium: halo radial, trazo redondeado y escala azul-gris.
    Sensación de instrumento de medición profesional.
    """
    tc = _tc()
    valor = max(0, min(100, valor))
    color = obtener_color_semaforo(valor)

    radio          = 42
    grosor         = 7
    circunferencia = 2 * 3.14159265 * radio
    offset         = circunferencia * (1 - valor / 100)

    gid = f"glow_{titulo.replace(' ', '').replace('.', '')}_{int(valor)}"

    html = f"""
<div style="
  background:{tc['bg_elevated']};
  border:1px solid {tc['border_default']};
  border-radius:8px;
  padding:20px 14px 16px;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:8px;
  transition:border-color .2s ease, box-shadow .2s ease;"
onmouseover="this.style.borderColor='{ACCENT_HOVER}';this.style.boxShadow='0 0 0 3px rgba(59,130,246,0.1)'"
onmouseout="this.style.borderColor='{tc['border_default']}';this.style.boxShadow='none'">

  <span style="
    font-family:'IBM Plex Mono',monospace;
    font-size:9px;font-weight:600;letter-spacing:1.4px;
    color:{tc['text_muted']};text-transform:uppercase;text-align:center;line-height:1.4;
  ">{titulo}</span>

  <svg width="108" height="108" viewBox="0 0 108 108" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="{gid}" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stop-color="{color}" stop-opacity="0.20"/>
        <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <circle cx="54" cy="54" r="50" fill="url(#{gid})"/>
    <circle cx="54" cy="54" r="{radio}"
      stroke="{tc['color_grid']}" stroke-width="{grosor}" fill="none"/>
    <circle cx="54" cy="54" r="{radio - grosor - 3}"
      stroke="{tc['border_subtle']}" stroke-width="1" fill="none" opacity="0.4"/>
    <circle cx="54" cy="54" r="{radio}"
      stroke="{color}" stroke-width="{grosor}" fill="none"
      stroke-dasharray="{circunferencia:.4f}"
      stroke-dashoffset="{offset:.4f}"
      stroke-linecap="round"
      transform="rotate(-90 54 54)"/>
    <text x="54" y="51" text-anchor="middle"
      font-family="'IBM Plex Mono',monospace"
      font-size="21" font-weight="700"
      fill="{color}">{valor:.1f}</text>
    <text x="54" y="65" text-anchor="middle"
      font-family="'IBM Plex Mono',monospace"
      font-size="9" font-weight="400"
      fill="{tc['text_muted']}">/ 100</text>
  </svg>
</div>"""

    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MÉTRICAS PRINCIPALES
# ─────────────────────────────────────────────
def renderizar_metricas(res: Dict[str, Any]) -> None:
    tc = _tc()
    st.markdown(
        f"<p style='font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:10px;font-weight:600;letter-spacing:1.4px;"
        f"color:{tc['text_muted']};text-transform:uppercase;"
        f"margin-bottom:12px;'>{_lbl('salud')}</p>",
        unsafe_allow_html=True,
    )

    col_global, col1, col2, col3, col4 = st.columns(5)

    with col_global:
        crear_grafico_medidor(_lbl('score_global'), res['score_global'])

    dimensiones = [
        (_lbl('completitud'),  res['completitud']),
        (_lbl('validez'),      res['validez']),
        (_lbl('unicidad'),     res['unicidad']),
        (_lbl('consistencia'), res['consistencia']),
    ]
    dimensiones.sort(key=lambda x: x[1], reverse=True)

    for col, (nombre, valor) in zip([col1, col2, col3, col4], dimensiones):
        with col:
            crear_grafico_medidor(nombre, valor)

    st.markdown(
        f"<hr style='border:none;border-top:1px solid {tc['border_subtle']};margin:28px 0;'>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  GRÁFICO COMPARATIVA DE DIMENSIONES
# ─────────────────────────────────────────────
def renderizar_grafico_dimensiones(res: Dict[str, Any]) -> None:
    tc = _tc()
    _subtitulo(_lbl('comparativa'))

    chart_df = pd.DataFrame({
        _lbl('dimension_lbl'):  [
            _lbl('completitud'), _lbl('consistencia'),
            _lbl('unicidad'),    _lbl('validez'),
        ],
        _lbl('score_lbl'): [
            res['completitud'], res['consistencia'],
            res['unicidad'],    res['validez'],
        ],
    })
    chart_df['Color'] = chart_df[_lbl('score_lbl')].apply(obtener_color_semaforo)

    dim_col   = _lbl('dimension_lbl')
    score_col = _lbl('score_lbl')

    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=3, height=20)
        .encode(
            x=alt.X(f'{score_col}:Q',
                    scale=alt.Scale(domain=[0, 100]),
                    title=None,
                    axis=alt.Axis(grid=True, gridColor=tc['color_grid'],
                                  gridDash=[3, 3], tickColor=tc['border_default'],
                                  labelColor=tc['text_muted'],
                                  domainColor=tc['border_default'], format='.0f')),
            y=alt.Y(f'{dim_col}:N', sort='-x', title=None,
                    axis=alt.Axis(labelColor=tc['text_high'],
                                  labelFontSize=12, domainColor=tc['border_default'],
                                  tickColor=tc['border_default'])),
            color=alt.Color('Color:N', scale=None),
            tooltip=[
                alt.Tooltip(f'{dim_col}:N', title=dim_col),
                alt.Tooltip(f'{score_col}:Q', title=score_col, format='.1f'),
            ],
        )
        .properties(height=230)
    )

    labels = bars.mark_text(align='left', baseline='middle', dx=6,
                             fontSize=11, fontWeight=600).encode(
        text=alt.Text(f'{score_col}:Q', format='.1f'),
        color=alt.Color('Color:N', scale=None),
    )

    st.altair_chart(
        (bars + labels)
        .configure_view(strokeWidth=0, fill=tc['bg_base'])
        .configure_axis(labelFont="IBM Plex Mono", titleFont="IBM Plex Mono")
        .configure(background=tc['bg_base']),
        width='stretch',
    )


# ─────────────────────────────────────────────
#  TABLA TOP ANOMALÍAS
# ─────────────────────────────────────────────
def renderizar_tabla_top_errores(df_procesado: pd.DataFrame) -> None:
    _subtitulo(_lbl('top_anomalias'))

    total_registros = len(df_procesado)
    df_errores = df_procesado[df_procesado['Score_Calidad'] < 100]

    if (df_errores.empty
            or 'Hallazgos_Detallados' not in df_errores.columns
            or total_registros == 0):
        _alerta_vacia(_lbl('sin_anomalias'))
        return

    textos = df_errores['Hallazgos_Detallados'].dropna().astype(str).tolist()
    conteo = Counter(
        item
        for texto in textos
        for item in texto.split(', ')
        if item not in ('Sin Errores', 'nan', '')
    )

    if not conteo:
        _alerta_vacia(_lbl('sin_anom_esp'))
        return

    tipo_col  = _lbl('tipo_falla')
    reg_col   = _lbl('reg_afectados')
    pct_col   = '% del Total'

    df_c = (
        pd.DataFrame(conteo.items(), columns=[tipo_col, reg_col])
        .sort_values(reg_col, ascending=False)
    )
    df_c[pct_col] = (df_c[reg_col] / total_registros * 100).round(1)

    st.dataframe(
        df_c,
        width='stretch',
        hide_index=True,
        column_config={
            tipo_col:  st.column_config.TextColumn(tipo_col, width="large"),
            reg_col:   st.column_config.NumberColumn(reg_col, format="%d"),
            pct_col:   st.column_config.ProgressColumn(
                pct_col, format="%.1f%%", min_value=0, max_value=100),
        },
    )


# ─────────────────────────────────────────────
#  GRÁFICO CALIDAD POR TIPO DE MATERIAL
# ─────────────────────────────────────────────
def renderizar_grafico_por_foco(df_procesado: pd.DataFrame) -> None:
    tc = _tc()
    _subtitulo(_lbl('calidad_mat'))

    if 'tipo_mat' not in df_procesado.columns:
        st.info(_lbl('sin_tipo_mat'))
        return

    tipo_col  = _lbl('categoria_lbl')
    score_col = _lbl('score_prom_lbl')

    df_g = (
        df_procesado.groupby('tipo_mat')['Score_Calidad']
        .mean()
        .reset_index()
        .rename(columns={'tipo_mat': tipo_col, 'Score_Calidad': score_col})
    )
    df_g['Color'] = df_g[score_col].apply(obtener_color_semaforo)
    altura = max(220, len(df_g) * 38)

    bars = (
        alt.Chart(df_g)
        .mark_bar(cornerRadiusEnd=3, height=16)
        .encode(
            x=alt.X(f'{score_col}:Q', scale=alt.Scale(domain=[0, 100]),
                    title=None,
                    axis=alt.Axis(grid=True, gridColor=tc['color_grid'],
                                  gridDash=[3, 3], tickColor=tc['border_default'],
                                  labelColor=tc['text_muted'],
                                  domainColor=tc['border_default'])),
            y=alt.Y(f'{tipo_col}:N', sort='-x', title=None,
                    axis=alt.Axis(labelColor=tc['text_high'],
                                  labelFontSize=11, domainColor=tc['border_default'],
                                  tickColor=tc['border_default'], labelOverlap=False)),
            color=alt.Color('Color:N', scale=None),
            tooltip=[
                alt.Tooltip(f'{tipo_col}:N', title=_lbl('categoria_lbl')),
                alt.Tooltip(f'{score_col}:Q', title=_lbl('score_prom_lbl'), format='.1f'),
            ],
        )
        .properties(height=altura)
    )

    labels = bars.mark_text(align='left', baseline='middle', dx=6,
                             fontSize=11, fontWeight=600).encode(
        text=alt.Text(f'{score_col}:Q', format='.1f'),
        color=alt.Color('Color:N', scale=None),
    )

    st.altair_chart(
        (bars + labels)
        .configure_view(strokeWidth=0, fill=tc['bg_base'])
        .configure_axis(labelFont="IBM Plex Mono", titleFont="IBM Plex Mono")
        .configure(background=tc['bg_base']),
        width='stretch',
    )


# ─────────────────────────────────────────────
#  EXPLORADOR DE ANOMALÍAS
# ─────────────────────────────────────────────
def renderizar_tabla_hallazgos(df_resultados) -> None:
    if df_resultados is None or len(df_resultados) == 0:
        st.info(_lbl('sin_hallazgos'))
        return

    if isinstance(df_resultados, pl.DataFrame):
        df = df_resultados.to_pandas()
    else:
        df = df_resultados.copy()

    columnas_principales = ["SKU", "Desc_Material", "Estado_Gestion", "tipo_mat", "Score_Calidad"]
    columnas_mostrar = [col for col in columnas_principales if col in df.columns]

    ruido_sap = [
        "SKU_num", "SKU_anterior", "Tipo_Material", "UoM", "cod_UEN", "UEN",
        "cod_marca", "marca", "cod_divprd", "tipo_industria_divprd",
        "cod_grupo_mat", "grupo_material", "cod_grupo_art", "grupo_articulo",
        "cod_grup_art_ext", "grupo_art_ext", "empaque_SAP", "tipo_empaque",
        "cod_contenido", "contenido_SAP", "marca_comercial", "item_categ",
        "EAN13", "EAN14", "peso_bruto", "peso_neto", "UoM_peso",
        "fecha_creacion", "creado_por", "fecha_actualiza", "actualizado_por",
        "Usuario_Auditor", "Fecha_Ingreso", "Fecha_Actualizacion", "Estado_Gestion_Desc",
        "Hallazgos_Detallados", "Score_Unicidad", "Score_Completitud",
        "Score_Validez", "Score_Consistencia",
    ]

    columnas_anomalias = [
        col for col in df.columns
        if col not in columnas_mostrar and col not in ruido_sap
    ]

    df_final = df[columnas_mostrar + columnas_anomalias].copy()

    if "Estado_Gestion" in df_final.columns:
        df_final["Estado_Gestion"] = df_final["Estado_Gestion"].apply(
            lambda x: _lbl('pendiente') if x == 0 else (_lbl('gestionado') if x == 1 else x)
        )

    st.dataframe(df_final, width='stretch', hide_index=True)


# ─────────────────────────────────────────────
#  PLACEHOLDER DE GRÁFICA VACÍA
# ─────────────────────────────────────────────
def mostrar_placeholder_grafica(titulo: str, mensaje: str) -> None:
    """Gráfica vacía estilizada para el estado sin datos."""
    tc = _tc()
    st.markdown(
        f"<p style='font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:10px;font-weight:600;letter-spacing:1.4px;"
        f"color:{tc['text_muted']};text-transform:uppercase;margin-bottom:10px;'>"
        f"{titulo}</p>"
        f"<div style='background:{tc['bg_elevated']};border:1px dashed {tc['border_subtle']};"
        f"border-radius:8px;height:180px;display:flex;align-items:center;"
        f"justify-content:center;'>"
        f"<p style='font-family:\"IBM Plex Sans\",sans-serif;font-size:12px;"
        f"color:{tc['text_disabled']};margin:0;'>{mensaje}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  HELPERS INTERNOS
# ─────────────────────────────────────────────
def _subtitulo(texto: str) -> None:
    tc = _tc()
    st.markdown(
        f"<p style='font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:10px;font-weight:600;letter-spacing:1.4px;"
        f"color:{tc['text_muted']};text-transform:uppercase;"
        f"margin-bottom:10px;'>{texto}</p>",
        unsafe_allow_html=True,
    )


def _alerta_vacia(mensaje: str) -> None:
    tc = _tc()
    st.markdown(
        f"<div style='"
        f"background:{tc['bg_elevated']};"
        f"border-left:2px solid {tc['state_healthy']};"
        f"border-radius:4px;padding:10px 16px;"
        f"font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:12px;color:{tc['text_default']};'>{mensaje}</div>",
        unsafe_allow_html=True,
    )
