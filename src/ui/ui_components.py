"""
Componentes modulares de la interfaz de usuario — T.A.L.O.N
Sistema de Diseño: Enterprise Dark — Flat, Limpio, Alto Contraste.
Sin pasteles, sin neón, sin gradientes decorativos.
Paleta: Fondos #0D1117 / #161B22 / #1C2128 · Acento #2F81F7 · Texto #E6EDF3
"""
import streamlit as st
import pandas as pd
import altair as alt
import itertools
from collections import Counter
from typing import Dict, Any
import polars as pl

# ─────────────────────────────────────────────
#  SISTEMA DE COLORES CENTRALIZADO
# ─────────────────────────────────────────────
COLOR_FONDO_CARD   = "#161B22"
COLOR_BORDE        = "#30363D"
COLOR_BORDE_HOVER  = "#58A6FF"
COLOR_TEXTO_PRIM   = "#E6EDF3"
COLOR_TEXTO_SEC    = "#8B949E"
COLOR_ACENTO       = "#2F81F7"

COLOR_ROJO    = "#F85149"   # < 50 %
COLOR_NARANJA = "#D29922"   # 50–84 %
COLOR_VERDE   = "#3FB950"   # ≥ 85 %

COLOR_GRID    = "#21262D"
COLOR_BG_ALT  = "#0D1117"


def obtener_color_semaforo(valor: float) -> str:
    """Retorna el color del semáforo basado en el porcentaje de calidad."""
    if valor < 50:
        return COLOR_ROJO
    elif valor < 85:
        return COLOR_NARANJA
    else:
        return COLOR_VERDE


# ─────────────────────────────────────────────
#  MEDIDOR SVG — Anillo limpio
# ─────────────────────────────────────────────
def crear_grafico_medidor(titulo: str, valor: float):
    """
    Gráfico de anillo SVG puro. Diseño enterprise: plano, centrado,
    sin sombras ni brillos. Solo geometría y tipografía.
    """
    valor = max(0, min(100, valor))
    color = obtener_color_semaforo(valor)

    radio         = 42
    grosor        = 8
    circunferencia = 2 * 3.14159265 * radio
    offset        = circunferencia * (1 - valor / 100)

    # Barra de progreso lineal debajo del anillo (marca de referencia visual)
    barra_ancho = valor  # 0–100 → 0–100%

    html = f"""
<div style="
  background:{COLOR_FONDO_CARD};
  border:1px solid {COLOR_BORDE};
  border-radius:6px;
  padding:18px 12px 14px;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:10px;
  transition:border-color .15s ease;
"
onmouseover="this.style.borderColor='{COLOR_BORDE_HOVER}'"
onmouseout="this.style.borderColor='{COLOR_BORDE}'">

  <!-- Título -->
  <span style="
    font-family:'IBM Plex Mono',monospace;
    font-size:10px;
    font-weight:600;
    letter-spacing:1.2px;
    color:{COLOR_TEXTO_SEC};
    text-transform:uppercase;
    text-align:center;
  ">{titulo}</span>

  <!-- SVG Anillo -->
  <svg width="110" height="110" viewBox="0 0 110 110" xmlns="http://www.w3.org/2000/svg">
    <!-- Track -->
    <circle cx="55" cy="55" r="{radio}"
      stroke="{COLOR_GRID}" stroke-width="{grosor}" fill="none"/>
    <!-- Progreso -->
    <circle cx="55" cy="55" r="{radio}"
      stroke="{color}" stroke-width="{grosor}" fill="none"
      stroke-dasharray="{circunferencia:.4f}"
      stroke-dashoffset="{offset:.4f}"
      stroke-linecap="butt"
      transform="rotate(-90 55 55)"/>
    <!-- Valor central -->
    <text x="55" y="52" text-anchor="middle"
      font-family="'IBM Plex Mono',monospace"
      font-size="20" font-weight="700"
      fill="{color}">{valor:.1f}</text>
    <text x="55" y="67" text-anchor="middle"
      font-family="'IBM Plex Mono',monospace"
      font-size="10" font-weight="400"
      fill="{COLOR_TEXTO_SEC}">/ 100</text>
  </svg>

  <!-- Barra de referencia -->
  <div style="width:100%;background:{COLOR_GRID};border-radius:2px;height:3px;overflow:hidden;">
    <div style="width:{barra_ancho:.1f}%;height:3px;background:{color};border-radius:2px;"></div>
  </div>

</div>"""

    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SECCIÓN: MÉTRICAS PRINCIPALES
# ─────────────────────────────────────────────
def renderizar_metricas(res: Dict[str, Any]) -> None:
    st.markdown(
        f"<p style='font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:11px;font-weight:600;letter-spacing:1.5px;"
        f"color:{COLOR_TEXTO_SEC};text-transform:uppercase;"
        f"margin-bottom:12px;'>Salud General de los Datos</p>",
        unsafe_allow_html=True
    )

    col_global, col1, col2, col3, col4 = st.columns(5)

    with col_global:
        crear_grafico_medidor("Score Global", res['score_global'])

    dimensiones = [
        ("Completitud",  res['completitud']),
        ("Validez",      res['validez']),
        ("Unicidad",     res['unicidad']),
        ("Consistencia", res['consistencia']),
    ]
    dimensiones.sort(key=lambda x: x[1], reverse=True)

    for col, (nombre, valor) in zip([col1, col2, col3, col4], dimensiones):
        with col:
            crear_grafico_medidor(nombre, valor)

    st.markdown(
        f"<hr style='border:none;border-top:1px solid {COLOR_BORDE};margin:28px 0;'>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────
#  SECCIÓN: GRÁFICO COMPARATIVA DE DIMENSIONES
# ─────────────────────────────────────────────
def renderizar_grafico_dimensiones(res: Dict[str, Any]) -> None:
    _subtitulo("Comparativa de Dimensiones")

    chart_df = pd.DataFrame({
        'Dimensión':   ['Completitud', 'Consistencia', 'Unicidad', 'Validez'],
        'Porcentaje':  [res['completitud'], res['consistencia'],
                        res['unicidad'],    res['validez']],
    })
    chart_df['Color'] = chart_df['Porcentaje'].apply(obtener_color_semaforo)

    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=3, height=20)
        .encode(
            x=alt.X('Porcentaje:Q',
                    scale=alt.Scale(domain=[0, 100]),
                    title=None,
                    axis=alt.Axis(grid=True, gridColor=COLOR_GRID,
                                  gridDash=[3, 3], tickColor=COLOR_BORDE,
                                  labelColor=COLOR_TEXTO_SEC,
                                  domainColor=COLOR_BORDE, format='.0f')),
            y=alt.Y('Dimensión:N', sort='-x', title=None,
                    axis=alt.Axis(labelColor=COLOR_TEXTO_PRIM,
                                  labelFontSize=12, domainColor=COLOR_BORDE,
                                  tickColor=COLOR_BORDE)),
            color=alt.Color('Color:N', scale=None),
            tooltip=[
                alt.Tooltip('Dimensión:N', title='Dimensión'),
                alt.Tooltip('Porcentaje:Q', title='Score', format='.1f'),
            ],
        )
        .properties(height=230)
    )

    labels = bars.mark_text(align='left', baseline='middle', dx=6,
                             fontSize=11, fontWeight=600).encode(
        text=alt.Text('Porcentaje:Q', format='.1f'),
        color=alt.Color('Color:N', scale=None),
    )

    st.altair_chart(
        (bars + labels)
        .configure_view(strokeWidth=0, fill=COLOR_BG_ALT)
        .configure_axis(labelFont="IBM Plex Mono", titleFont="IBM Plex Mono")
        .configure(background=COLOR_BG_ALT),
        use_container_width=True,
    )


# ─────────────────────────────────────────────
#  SECCIÓN: TOP ANOMALÍAS
# ─────────────────────────────────────────────
def renderizar_grafico_top_errores(df_procesado: pd.DataFrame) -> None:
    _subtitulo("Top Anomalías Detectadas")

    total_registros = len(df_procesado)
    df_errores = df_procesado[df_procesado['Score_Calidad'] < 100]

    if (df_errores.empty
            or 'Hallazgos_Detallados' not in df_errores.columns
            or total_registros == 0):
        _alerta_vacia("Sin anomalías en la selección actual.")
        return

    textos = df_errores['Hallazgos_Detallados'].dropna().astype(str).tolist()
    conteo = Counter(
        item
        for texto in textos
        for item in texto.split(', ')
        if item not in ('Sin Errores', 'nan', '')
    )

    if not conteo:
        _alerta_vacia("Sin anomalías específicas en esta vista.")
        return

    df_c = (
        pd.DataFrame(conteo.items(), columns=['Anomalía', 'Registros'])
        .sort_values('Registros', ascending=False)
    )
    df_c['% del Total'] = (df_c['Registros'] / total_registros * 100).round(1)

    st.dataframe(
        df_c,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Anomalía":   st.column_config.TextColumn("Tipo de Falla", width="large"),
            "Registros":  st.column_config.NumberColumn("Registros Afectados", format="%d"),
            "% del Total": st.column_config.ProgressColumn(
                "% del Total", format="%.1f%%", min_value=0, max_value=100),
        },
    )


# ─────────────────────────────────────────────
#  SECCIÓN: CALIDAD POR TIPO DE MATERIAL
# ─────────────────────────────────────────────
def renderizar_grafico_por_foco(df_procesado: pd.DataFrame) -> None:
    _subtitulo("Calidad por Tipo de Material")

    if 'tipo_mat' not in df_procesado.columns:
        st.info("No hay datos de tipo de material para agrupar.")
        return

    df_g = (
        df_procesado.groupby('tipo_mat')['Score_Calidad']
        .mean()
        .reset_index()
        .rename(columns={'tipo_mat': 'Tipo', 'Score_Calidad': 'Score'})
    )
    df_g['Color'] = df_g['Score'].apply(obtener_color_semaforo)
    altura = max(220, len(df_g) * 38)

    bars = (
        alt.Chart(df_g)
        .mark_bar(cornerRadiusEnd=3, height=16)
        .encode(
            x=alt.X('Score:Q', scale=alt.Scale(domain=[0, 100]),
                    title=None,
                    axis=alt.Axis(grid=True, gridColor=COLOR_GRID,
                                  gridDash=[3, 3], tickColor=COLOR_BORDE,
                                  labelColor=COLOR_TEXTO_SEC,
                                  domainColor=COLOR_BORDE)),
            y=alt.Y('Tipo:N', sort='-x', title=None,
                    axis=alt.Axis(labelColor=COLOR_TEXTO_PRIM,
                                  labelFontSize=11, domainColor=COLOR_BORDE,
                                  tickColor=COLOR_BORDE, labelOverlap=False)),
            color=alt.Color('Color:N', scale=None),
            tooltip=[
                alt.Tooltip('Tipo:N', title='Categoría'),
                alt.Tooltip('Score:Q', title='Score Promedio', format='.1f'),
            ],
        )
        .properties(height=altura)
    )

    labels = bars.mark_text(align='left', baseline='middle', dx=6,
                             fontSize=11, fontWeight=600).encode(
        text=alt.Text('Score:Q', format='.1f'),
        color=alt.Color('Color:N', scale=None),
    )

    st.altair_chart(
        (bars + labels)
        .configure_view(strokeWidth=0, fill=COLOR_BG_ALT)
        .configure_axis(labelFont="IBM Plex Mono", titleFont="IBM Plex Mono")
        .configure(background=COLOR_BG_ALT),
        use_container_width=True,
    )


# ─────────────────────────────────────────────
#  SECCIÓN: EXPLORADOR DE ANOMALÍAS
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
import polars as pl

def renderizar_tabla_hallazgos(df_resultados):
    """
    Renderiza la tabla de hallazgos sin ruido visual. 
    Solo muestra lo vital y las columnas dinámicas de anomalías.
    """
    if df_resultados is None or len(df_resultados) == 0:
        st.info("No hay hallazgos o anomalías para mostrar.")
        return

    # 1. Asegurar formato Pandas
    if isinstance(df_resultados, pl.DataFrame):
        df = df_resultados.to_pandas()
    else:
        df = df_resultados.copy()

    # 2. Las columnas EXACTAS que queremos ver fijas al inicio
    columnas_principales = ["SKU", "Desc_Material", "Estado_Gestion", "tipo_mat", "Score_Calidad"]
    columnas_mostrar = [col for col in columnas_principales if col in df.columns]

    # 3. Lista negra: Todo el ruido de SAP y BigQuery que NO queremos ver en pantalla
    ruido_sap = [
        "SKU_num", "SKU_anterior", "Tipo_Material", "UoM", "cod_UEN", "UEN", 
        "cod_marca", "marca", "cod_divprd", "tipo_industria_divprd", 
        "cod_grupo_mat", "grupo_material", "cod_grupo_art", "grupo_articulo", 
        "cod_grup_art_ext", "grupo_art_ext", "empaque_SAP", "tipo_empaque", 
        "cod_contenido", "contenido_SAP", "marca_comercial", "item_categ", 
        "EAN13", "EAN14", "peso_bruto", "peso_neto", "UoM_peso", 
        "fecha_creacion", "creado_por", "fecha_actualiza", "actualizado_por",
        "Usuario_Auditor", "Fecha_Ingreso", "Fecha_Actualizacion", "Estado_Gestion_Desc", 
        "Hallazgos_Detallados", "Score_Unicidad", "Score_Completitud", "Score_Validez", "Score_Consistencia"
    ]

    # 4. Extraer únicamente las columnas de anomalías (Las reglas que dan True/False)
    # Si no está en las principales y no es ruido, ¡es una regla!
    columnas_anomalias = [col for col in df.columns if col not in columnas_mostrar and col not in ruido_sap]

    # 5. Armar la tabla final limpia
    df_final = df[columnas_mostrar + columnas_anomalias]

    # 6. Formato visual de Estado_Gestion
    if "Estado_Gestion" in df_final.columns:
        df_final["Estado_Gestion"] = df_final["Estado_Gestion"].apply(
            lambda x: "❌" if x == 0 else ("✅" if x == 1 else x)
        )

    # 7. Renderizar en Streamlit
    st.dataframe(df_final, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
#  HELPERS INTERNOS
# ─────────────────────────────────────────────
def _subtitulo(texto: str):
    """Subtítulo de sección con tipografía monoespaciada."""
    st.markdown(
        f"<p style='font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:11px;font-weight:600;letter-spacing:1.5px;"
        f"color:{COLOR_TEXTO_SEC};text-transform:uppercase;"
        f"margin-bottom:10px;'>{texto}</p>",
        unsafe_allow_html=True
    )


def _alerta_vacia(mensaje: str):
    """Mensaje de estado vacío con diseño consistente."""
    st.markdown(
        f"<div style='"
        f"background:{COLOR_FONDO_CARD};"
        f"border-left:3px solid {COLOR_VERDE};"
        f"border-radius:4px;padding:10px 16px;"
        f"font-family:\"IBM Plex Mono\",monospace;"
        f"font-size:12px;color:{COLOR_TEXTO_PRIM};'>{mensaje}</div>",
        unsafe_allow_html=True
    )