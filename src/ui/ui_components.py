"""
Componentes modulares de la interfaz de usuario (Streamlit).
Diseño Minimalista, Flat y Limpio (Sin efectos neón).
"""
import streamlit as st
import pandas as pd
import altair as alt
import itertools
from collections import Counter
from typing import Dict, Any

def obtener_color_semaforo(valor: float) -> str:
    """Retorna el color del semáforo basado en el porcentaje de calidad."""
    if valor < 50:
        return "#FF2B00" # Rojo sólido/mate
    elif valor < 85:
        return "#F48F0B" # Naranja sólido/mate
    else:
        return "#04FF00" # Verde sólido/mate

def crear_grafico_medidor(titulo: str, valor: float):
    """
    Gráfico de anillo construido matemáticamente con SVG puro.
    Diseño plano, centrado, sin sombras exageradas ni brillos.
    """
    valor = max(0, min(100, valor))
    color_dinamico = obtener_color_semaforo(valor)
    
    radio = 45
    grosor_anillo = 7
    circunferencia = 2 * 3.14159 * radio
    offset = circunferencia - (valor / 100) * circunferencia
    
    html_card = f"""<div style="
background-color: #1e1e24;
border: 1px solid #333;
border-radius: 8px;
padding: 20px;
display: flex; 
flex-direction: column; 
align-items: center; 
justify-content: center;
height: 190px;
transition: border-color 0.2s ease;
"
onmouseover="this.style.borderColor='#555';"
onmouseout="this.style.borderColor='#333';"
>
<div style="font-weight: 600; font-size: 13px; margin-bottom: 15px; color: #CCCCCC; text-align: center; letter-spacing: 0.5px;">{titulo.upper()}</div>
<svg width="100%" height="110" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid meet">
<circle cx="60" cy="60" r="{radio}" stroke="#2b2b36" stroke-width="{grosor_anillo}" fill="none" />
<circle cx="60" cy="60" r="{radio}" stroke="{color_dinamico}" stroke-width="{grosor_anillo}" fill="none" stroke-dasharray="{circunferencia}" stroke-dashoffset="{offset}" stroke-linecap="round" transform="rotate(-90 60 60)" />
<text x="60" y="66" font-family="sans-serif" font-size="22" font-weight="bold" fill="{color_dinamico}" text-anchor="middle">{valor:.1f}%</text>
</svg>
</div>"""
    
    st.markdown(html_card, unsafe_allow_html=True)

def renderizar_metricas(res: Dict[str, Any]) -> None:
    st.markdown("### Salud General de los Datos") 
    col_global, col1, col2, col3, col4 = st.columns(5)
    
    with col_global:
        crear_grafico_medidor("Salud Global", res['score_global'])
        
    dimensiones = [
        ("Completitud", res['completitud']),
        ("Validez", res['validez']),
        ("Unicidad", res['unicidad']),
        ("Consistencia", res['consistencia'])
    ]
    dimensiones.sort(key=lambda x: x[1], reverse=True)
    
    columnas_dims = [col1, col2, col3, col4]
    for col, (nombre, valor) in zip(columnas_dims, dimensiones):
        with col:
            crear_grafico_medidor(nombre, valor)        
    st.markdown("<br><hr style='border-color: #333;'><br>", unsafe_allow_html=True)

def renderizar_grafico_dimensiones(res: Dict[str, Any]) -> None:
    st.markdown("#### Comparativa de Dimensiones")
    chart_df = pd.DataFrame({
        'Dimension': ['Completitud', 'Consistencia', 'Unicidad', 'Validez'],
        'Porcentaje': [res['completitud'], res['consistencia'], res['unicidad'], res['validez']]
    })
    
    chart_df['Color'] = chart_df['Porcentaje'].apply(obtener_color_semaforo)
    
    bars = alt.Chart(chart_df).mark_bar(cornerRadiusEnd=4, height=24).encode(
        x=alt.X('Porcentaje:Q', scale=alt.Scale(domain=[0, 100]), title='Porcentaje (%)', axis=alt.Axis(grid=False)),
        y=alt.Y('Dimension:N', sort='-x', title='', axis=alt.Axis(labelFontWeight='normal')),
        color=alt.Color('Color:N', scale=None),
        tooltip=['Dimension', 'Porcentaje']
    ).properties(height=250)
    
    text = bars.mark_text(align='left', baseline='middle', dx=5, fontSize=12).encode(
        text=alt.Text('Porcentaje:Q', format='.1f'),
        color=alt.Color('Color:N', scale=None)
    )
    
    st.altair_chart((bars + text).configure_view(strokeWidth=0), use_container_width=True)

def renderizar_grafico_top_errores(df_procesado: pd.DataFrame) -> None:
    st.markdown("#### Top Anomalías Detectadas")
    total_registros = len(df_procesado)
    df_errores = df_procesado[df_procesado['Score_Calidad'] < 100]
    
    if df_errores.empty or 'Hallazgos_Detallados' not in df_errores.columns or total_registros == 0:
        st.success("No hay errores en la selección actual.")
        return

    textos_errores = df_errores['Hallazgos_Detallados'].dropna().astype(str).tolist()
    generador_errores = itertools.chain.from_iterable(texto.split(', ') for texto in textos_errores)
    conteo_diccionario = Counter(generador_errores)
    
    conteo_diccionario.pop('Sin Errores', None)
    conteo_diccionario.pop('nan', None)
    
    if not conteo_diccionario:
        st.success("No hay anomalías específicas detectadas en esta vista.")
        return
        
    df_conteo = pd.DataFrame(conteo_diccionario.items(), columns=['Tipo de Anomalía', 'Cantidad Absoluta'])
    st.dataframe(
        df_conteo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tipo de Anomalía": st.column_config.TextColumn("Falla Detectada", width="large"),
            "Cantidad Absoluta": st.column_config.NumberColumn("Registros Afectados", format="%d")
        }
    )

def renderizar_grafico_por_foco(df_procesado: pd.DataFrame) -> None:
    st.markdown("#### Calidad por Tipo de Material")
    if 'tipo_mat' not in df_procesado.columns:
        st.info("No hay datos de tipo de material para agrupar.")
        return
        
    df_agrupado = df_procesado.groupby('tipo_mat')['Score_Calidad'].mean().reset_index()
    df_agrupado.columns = ['Tipo de Material', 'Score Promedio']
    df_agrupado['Color'] = df_agrupado['Score Promedio'].apply(obtener_color_semaforo)

    altura_dinamica = max(200, len(df_agrupado) * 40)

    bars = alt.Chart(df_agrupado).mark_bar(cornerRadiusEnd=4, height=18).encode(
        x=alt.X('Score Promedio:Q', scale=alt.Scale(domain=[0, 100]), title='Score Promedio (%)', axis=alt.Axis(grid=True, gridColor="#333", gridDash=[2,2])),
        y=alt.Y('Tipo de Material:N', sort='-x', title='', axis=alt.Axis(labelOverlap=False, labelFontWeight='normal')),
        color=alt.Color('Color:N', scale=None),
        tooltip=['Tipo de Material', 'Score Promedio']
    ).properties(height=altura_dinamica)
    
    text = bars.mark_text(align='left', baseline='middle', dx=5, fontSize=12).encode(
        text=alt.Text('Score Promedio:Q', format='.1f'),
        color=alt.Color('Color:N', scale=None)
    )
    
    st.altair_chart((bars + text).configure_view(strokeWidth=0), use_container_width=True)

def renderizar_tabla_hallazgos(df: pd.DataFrame):
    """Muestra los registros con errores con columnas dinámicas por cada tipo de hallazgo."""
    st.markdown("### 🔎 Explorador de Anomalías")
    
    if 'Score_Calidad' not in df.columns:
        st.info("Ejecuta la auditoría para ver los datos anómalos aquí.")
        return
        
    # 1. Filtramos para tener solo los errores
    df_mostrar = df[df['Score_Calidad'] < 99.9].copy()
    
    if df_mostrar.empty:
        st.success("🎉 ¡Excelente! No se encontraron anomalías en esta vista.")
        return

    st.warning(f"Se encontraron {len(df_mostrar)} registros con oportunidades de mejora.")

    # --- MAGIA: CREACIÓN DE COLUMNAS DINÁMICAS POR ERROR ---
    import itertools
    lista_errores = df_mostrar['Hallazgos_Detallados'].dropna().astype(str).str.split(', ').tolist()
    errores_unicos = sorted(list(set(itertools.chain.from_iterable(lista_errores))))
    
    # Limpieza
    for err in ["Sin Errores", "nan", ""]:
        if err in errores_unicos: errores_unicos.remove(err)

    # Creamos una columna por cada error único y le ponemos una ❌
    for error in errores_unicos:
        df_mostrar[error] = df_mostrar['Hallazgos_Detallados'].apply(lambda x: "❌" if error in str(x) else "")

    # 2. Definimos las columnas base
    if 'Dirección' in df.columns or 'Cliente' in df.columns:
        cols_base = ['Score_Calidad', 'SKU_num', 'Desc_Material', 'Dirección', 'Correo electrónico', 'Teléfono', 'Clave de país/región']
    else:
        cols_base = ['Score_Calidad', 'SKU_num', 'Desc_Material', 'tipo_mat']

    # Unimos las columnas base con las nuevas columnas de errores
    columnas_tabla = [c for c in cols_base if c in df_mostrar.columns] + errores_unicos

    # 3. Blindaje numérico y renderizado final
    df_mostrar['Score_Calidad'] = pd.to_numeric(df_mostrar['Score_Calidad'], errors='coerce').fillna(0).round(1)

    st.dataframe(
        df_mostrar[columnas_tabla].sort_values("Score_Calidad"), 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Score_Calidad": st.column_config.ProgressColumn("Calidad", format="%d%%", min_value=0, max_value=100)
        }
    )