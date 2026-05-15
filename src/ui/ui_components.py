"""
Componentes modulares de la interfaz de usuario — T.A.L.O.N
Sistema de Diseño: Enterprise Slate / Azure — Premium, limpio, monocromático.
Paleta: Grises fríos (#070B12→#1C2432) · Acento único #3B82F6 (familia azul).

Los componentes leen st.session_state['idioma'] en tiempo de render
para adaptar etiquetas y textos sin necesidad de re-importar el módulo.
"""
import math
import html
import streamlit as st
import streamlit.components.v1 as st_components
import pandas as pd
from typing import Dict, Any, List, Set, Optional, Tuple
import polars as pl
import time

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
        'explorer_sin_fallos': 'Sin incumplimientos detectados para las reglas de completitud en esta selección.',
        'explorer_marks_hint': '✓ conforme · ✗ incumple la regla · — no aplica.',
        'explorer_mark_na': '—',
        'explorer_mark_fail': '✗',
        'explorer_mark_pass': '✓',
        'explorer_hdr_desc_material': 'Descripción Material',
        'explorer_hdr_estado_gestion': 'Estado Gestión',
        'explorer_hdr_tipo_mat': 'Tipo de Material',
        'graf_hdr_escala':     'Escala (0–100)',
        'explorer_err_trunc':  'Mostrando las primeras {n} columnas de error; en los datos hay más tipos de hallazgo distintos.',
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
        'explorer_sin_fallos': 'No completeness rule violations in this selection.',
        'explorer_marks_hint': '✓ pass · ✗ fails rule · — N/A.',
        'explorer_mark_na': '—',
        'explorer_mark_fail': '✗',
        'explorer_mark_pass': '✓',
        'explorer_hdr_desc_material': 'Material description',
        'explorer_hdr_estado_gestion': 'Management status',
        'explorer_hdr_tipo_mat': 'Material type',
        'graf_hdr_escala':       'Scale (0–100)',
        'explorer_err_trunc':    'Showing the first {n} error columns; more distinct finding types exist in the data.',
    },
}

# Etiquetas legibles para columnas *_nulo (False = campo vacío)
_NULO_FIELD_LABELS_ES: Dict[str, str] = {
    "SKU": "SKU",
    "Desc_Material": "Descripción",
    "UoM": "Unidad de medida",
    "grupo_material": "Grupo de material",
    "UEN": "UEN",
    "marca": "Marca",
    "EAN13": "EAN13",
    "EAN14": "EAN14",
    "peso_bruto": "Peso bruto",
    "peso_neto": "Peso neto",
    "empaque_SAP": "Empaque SAP",
    "contenido_SAP": "Contenido SAP",
}

_NULO_FIELD_LABELS_EN: Dict[str, str] = {
    "SKU": "SKU",
    "Desc_Material": "Description",
    "UoM": "Unit of measure",
    "grupo_material": "Material group",
    "UEN": "Strategic BU (UEN)",
    "marca": "Brand",
    "EAN13": "EAN13",
    "EAN14": "EAN14",
    "peso_bruto": "Gross weight",
    "peso_neto": "Net weight",
    "empaque_SAP": "SAP packaging",
    "contenido_SAP": "SAP content",
}


def _lbl(key: str) -> str:
    """Etiqueta traducida según el idioma de la sesión."""
    lang = st.session_state.get('idioma', 'es')
    return _LABELS.get(lang, _LABELS['es']).get(key, key)


def _lang_is_en() -> bool:
    return st.session_state.get('idioma', 'es') == 'en'


def _label_for_nulo_field(col_name: str) -> str:
    base = col_name[:-5] if col_name.endswith('_nulo') else col_name.replace('_nulo', '')
    if _lang_is_en():
        return _NULO_FIELD_LABELS_EN.get(base, base.replace('_', ' '))
    return _NULO_FIELD_LABELS_ES.get(base, base.replace('_', ' '))


MAX_COLUMNAS_ERRORES_EXPLORADOR = 30


def _explorador_matriz_hallazgos(
    df_filtrado: pd.DataFrame,
) -> Tuple[Dict[str, str], pd.DataFrame, bool]:
    """
    Una columna por texto distinto en Hallazgos_Detallados (coherente con la matriz Excel).
    Devuelve: mapa err_i -> mensaje completo, DataFrame de columnas err_* , truncated si hubo límite.
    """
    if df_filtrado is None or len(df_filtrado) == 0:
        return {}, pd.DataFrame(), False
    if "Hallazgos_Detallados" not in df_filtrado.columns:
        return {}, pd.DataFrame(index=df_filtrado.index), False

    hall = df_filtrado["Hallazgos_Detallados"].fillna("").astype(str)
    trozos: List[str] = []
    for txt in hall:
        for p in str(txt).split(", "):
            p = p.strip()
            if p and p not in ("Sin Errores", "nan"):
                trozos.append(p)
    fallas_u = sorted(set(trozos))
    truncated = len(fallas_u) > MAX_COLUMNAS_ERRORES_EXPLORADOR
    if truncated:
        fallas_u = fallas_u[:MAX_COLUMNAS_ERRORES_EXPLORADOR]

    mk_fail = _lbl("explorer_mark_fail")
    err_map: Dict[str, str] = {}
    cols_df: Dict[str, pd.Series] = {}
    for i, falla in enumerate(fallas_u):
        key = f"err_{i}"
        err_map[key] = falla
        cols_df[key] = hall.map(lambda x, f=falla: mk_fail if f in str(x) else "")

    return err_map, pd.DataFrame(cols_df, index=df_filtrado.index), truncated


def _nulo_check_failed(val) -> bool:
    """True si la regla de completitud detectó el campo vacío (False en columna *_nulo)."""
    if pd.isna(val):
        return False
    try:
        if hasattr(val, "item"):
            val = val.item()
    except Exception:
        pass
    return val is False or val == 0


def _marcacion_celda(val) -> str:
    """Distintivo visual para marcas de completitud (no booleano en pantalla)."""
    if pd.isna(val):
        return _lbl("explorer_mark_na")
    return _lbl("explorer_mark_fail") if _nulo_check_failed(val) else _lbl("explorer_mark_pass")


def _estilo_marcacion_explorador(val) -> str:
    """CSS inline para Streamlit dataframe con Pandas Styler (solo columnas de marcas)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s == _lbl("explorer_mark_pass"):
        return "color:#86efac;font-weight:700;background-color:rgba(34,197,94,0.22);text-align:center;"
    if s == _lbl("explorer_mark_fail"):
        return "color:#fecaca;font-weight:700;background-color:rgba(239,68,68,0.26);text-align:center;"
    if s == _lbl("explorer_mark_na"):
        return "color:#94a3b8;font-weight:500;background-color:rgba(148,163,184,0.12);text-align:center;"
    return ""


def _format_sku_celda(val) -> str:
    """SKU siempre como texto legible (evita que la grilla trate el valor como icono o notación científica)."""
    if pd.isna(val):
        return ""
    if isinstance(val, (float, int)) and not isinstance(val, bool):
        try:
            fv = float(val)
            if math.isfinite(fv) and fv == int(fv):
                return str(int(fv))
        except (OverflowError, ValueError, TypeError):
            pass
    s = str(val).strip()
    if len(s) > 2 and s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        return s[:-2]
    return s


def _nombres_unicos_marcas(check_cols: List[str], reservados_core: Set[str]) -> List[tuple[str, str]]:
    """
    Devuelve [(col_origen, nombre_visible), ...].
    Si el nombre de la marca coincidiría con una columna del maestro (p. ej. SKU), se añade sufijo ' · marca'.
    """
    suf = " · marca" if not _lang_is_en() else " · mark"
    res_norm = {r.lower() for r in reservados_core}
    usados: set[str] = set()
    result: List[tuple[str, str]] = []
    for c in check_cols:
        base = _label_for_nulo_field(c)
        nombre = base
        if base in reservados_core or base.lower() in res_norm:
            nombre = base + suf
        n = 2
        while nombre in usados:
            nombre = f"{base}{suf} ({n})"
            n += 1
        usados.add(nombre)
        result.append((c, nombre))
    return result


def _explorador_nulos_analisis(
    df: pd.DataFrame,
) -> Optional[Tuple[List[str], pd.DataFrame, List[str], List[str], List[Tuple[str, str]]]]:
    """Misma lógica de reglas que el Explorador (columnas *_nulo). None si no hay columnas *_nulo."""
    check_cols = sorted([c for c in df.columns if str(c).endswith("_nulo")])
    if not check_cols:
        return None
    fail_mat = pd.DataFrame({c: df[c].map(_nulo_check_failed) for c in check_cols})
    cols_con_fallo = [c for c in check_cols if bool(fail_mat[c].any())]
    columnas_core = ["SKU", "Desc_Material", "Estado_Gestion", "tipo_mat"]
    cols_core = [c for c in columnas_core if c in df.columns]
    pairs = _nombres_unicos_marcas(cols_con_fallo, set(cols_core))
    return check_cols, fail_mat, cols_con_fallo, cols_core, pairs


def _render_barras_porcentaje_html(
    filas: List[Tuple[str, float, str]],
    alto_pista_px: int = 18,
    mostrar_escala: bool = True,
    incremento_escala: int = 10,
    titulo: Optional[str] = None,
    cabecera_columnas: Optional[Tuple[str, str]] = None,
) -> None:
    """
    Gráfico de barras horizontal 0–100% en HTML (siempre visible en Streamlit).
    Si `titulo` se pasa, se dibuja una tarjeta tipo gráfico con el encabezado alineado al área del plot.
    `cabecera_columnas`: (etiqueta columna izquierda, etiqueta valores a la derecha), misma rejilla que las filas.
    filas: (etiqueta, porcentaje, color_hex).
    """
    tc = _tc()
    gutter = html.escape(tc["border_default"], quote=True)
    grid_col = html.escape(tc["color_grid"], quote=True)
    bg_page = html.escape(tc["bg_base"], quote=True)
    bg_card = html.escape(tc["bg_elevated"], quote=True)
    bg_track = html.escape(tc["bg_overlay"], quote=True)
    brd = html.escape(tc["border_subtle"], quote=True)
    accent_esc = html.escape(ACCENT_PRIMARY, quote=True)
    text_hi = html.escape(tc["text_high"], quote=True)
    text_mu = html.escape(tc["text_muted"], quote=True)
    inc = max(1, min(25, int(incremento_escala)))
    track_grid_bg = (
        f"repeating-linear-gradient(90deg, transparent, transparent calc({inc}% - 1px), "
        f"{grid_col} calc({inc}% - 1px), {grid_col} {inc}%)"
    )

    hdr_html = ""
    if cabecera_columnas:
        h_left = html.escape(str(cabecera_columnas[0]), quote=True)
        h_right = html.escape(str(cabecera_columnas[1]), quote=True)
        hdr_html = (
            f'<div style="grid-column:1;text-align:right;padding:0 8px 6px 0;border-bottom:1px solid {brd};'
            f'font-family:&quot;IBM Plex Mono&quot;,monospace;font-size:9px;font-weight:600;letter-spacing:1px;'
            f'text-transform:uppercase;color:{text_mu};align-self:end;line-height:1.2;">{h_left}</div>'
            f'<div style="grid-column:2;text-align:center;padding:0 0 6px;border-bottom:1px solid {brd};'
            f'font-family:&quot;IBM Plex Mono&quot;,monospace;font-size:9px;font-weight:600;letter-spacing:0.8px;'
            f'text-transform:uppercase;color:{text_mu};opacity:0.75;align-self:end;line-height:1.2;">'
            f'{html.escape(_lbl("graf_hdr_escala"), quote=True)}</div>'
            f'<div style="grid-column:3;text-align:right;padding:0 0 6px;border-bottom:1px solid {brd};'
            f'font-family:&quot;IBM Plex Mono&quot;,monospace;font-size:9px;font-weight:600;letter-spacing:1px;'
            f'text-transform:uppercase;color:{text_mu};align-self:end;line-height:1.2;">{h_right}</div>'
        )

    filas_html: List[str] = []
    for i, (etiqueta, valor, color_hex) in enumerate(filas):
        pct = max(0.0, min(100.0, float(valor)))
        lab = html.escape(str(etiqueta), quote=True)
        col = html.escape(str(color_hex), quote=True)
        alto_tr = max(14, int(alto_pista_px))
        texto_val_esc = html.escape(f"{pct:.1f}", quote=True)
        zebra = "rgba(148,163,184,0.04)" if i % 2 == 0 else "transparent"
        filas_html.append(
            f'<div style="text-align:right;padding:6px 8px 6px 0;color:{text_hi};background:{zebra};'
            f'border-radius:6px 0 0 6px;font-family:&quot;IBM Plex Sans&quot;,sans-serif;font-size:12px;font-weight:500;'
            f'line-height:1.35;border-bottom:1px solid {brd};align-self:stretch;display:flex;align-items:center;'
            f'justify-content:flex-end;">{lab}</div>'
            f'<div style="position:relative;height:{alto_tr + 12}px;min-height:30px;border-bottom:1px solid {gutter};'
            f'align-self:center;background:{zebra};border-radius:0;">'
            f'<div style="position:absolute;left:0;right:0;bottom:3px;top:10px;border-radius:6px;'
            f'background:{bg_track};box-shadow:inset 0 1px 0 rgba(255,255,255,0.04);"></div>'
            f'<div style="position:absolute;left:0;right:0;bottom:3px;top:10px;border-radius:6px;'
            f'background:{track_grid_bg};opacity:0.35;pointer-events:none;"></div>'
            f'<div style="position:absolute;left:0;bottom:3px;top:10px;width:{pct:.2f}%;min-width:'
            f'{"3px" if pct > 0 else "0"};border-radius:6px;box-sizing:border-box;z-index:1;'
            f'background:linear-gradient(180deg,rgba(255,255,255,0.14) 0%,rgba(255,255,255,0) 52%),{col};'
            f'box-shadow:0 0 0 1px rgba(0,0,0,0.18) inset,0 2px 10px rgba(0,0,0,0.28),'
            f'0 0 16px rgba(96,165,250,0.08);"></div>'
            "</div>"
            f'<div style="text-align:right;padding:6px 0 6px 6px;font-family:&quot;IBM Plex Mono&quot;,monospace;'
            f'font-size:12px;font-weight:700;color:{col};border-bottom:1px solid {brd};background:{zebra};'
            f'border-radius:0 6px 6px 0;align-self:stretch;display:flex;align-items:center;justify-content:flex-end;">'
            f'<span style="min-width:44px;">{texto_val_esc}</span></div>'
        )

    spans_eje = []
    for t in range(0, 101, inc):
        alin = "center"
        if t == 0:
            alin = "left"
        elif t == 100:
            alin = "right"
        spans_eje.append(
            f'<span style="flex:1;display:block;text-align:{alin};opacity:0.95;">'
            f"{html.escape(str(t), quote=True)}</span>"
        )
    ticks = "".join(spans_eje)
    eje_html = ""
    if mostrar_escala:
        eje_html = (
            f'<div style="grid-column:1;border-bottom:none;"></div>'
            f'<div style="grid-column:2;padding:6px 0 2px;color:{text_mu};'
            f'font-family:&quot;IBM Plex Mono&quot;,monospace;font-size:10px;border-bottom:none;">'
            f'<div style="display:flex;width:100%;">{ticks}</div></div>'
            '<div style="grid-column:3;border-bottom:none;"></div>'
        )

    grid_body = hdr_html + "".join(filas_html) + eje_html

    inner = (
        f'<div style="display:grid;grid-template-columns:minmax(112px,26%) minmax(96px,1fr) 56px;'
        f'column-gap:12px;row-gap:2px;align-items:stretch;width:100%;box-sizing:border-box;">'
        f"{grid_body}</div>"
    )

    if titulo:
        tit_esc = html.escape(titulo, quote=True)
        bloque = (
            f'<div class="talon-bar-chart" style="background:{bg_card};border:1px solid {brd};'
            f'border-radius:12px;padding:0;box-sizing:border-box;width:100%;margin:0;overflow:hidden;'
            f'box-shadow:0 2px 14px rgba(7,11,18,0.45),0 0 0 1px rgba(59,130,246,0.06);">'
            f'<div style="padding:14px 18px 12px 15px;border-left:3px solid {accent_esc};'
            f'border-bottom:1px solid {brd};margin:0;background:linear-gradient(90deg,{bg_track} 0%,transparent 55%);'
            f'box-sizing:border-box;">'
            f'<p style="font-family:&quot;IBM Plex Mono&quot;,monospace;font-size:10px;font-weight:600;'
            f"letter-spacing:1.4px;text-transform:uppercase;color:{text_hi};margin:0;"
            f'line-height:1.35;padding:0;">{tit_esc}</p></div>'
            f'<div style="padding:14px 18px 18px 18px;">{inner}</div></div>'
        )
    else:
        bloque = f'<div style="background:{bg_page};padding:8px 0;width:100%;">{inner}</div>'

    st.markdown(bloque, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MEDIDOR SVG PREMIUM — Anillo con glow
# ─────────────────────────────────────────────
def _df_base_como_explorador(df_procesado: pd.DataFrame) -> pd.DataFrame:
    """Misma población que el Explorador: filas Pendiente (Estado_Gestion == 0). Si no existe la columna, sin filtro."""
    if df_procesado is None or len(df_procesado) == 0:
        return df_procesado
    if "Estado_Gestion" not in df_procesado.columns:
        return df_procesado
    return df_procesado.loc[df_procesado["Estado_Gestion"] == 0]


def _score_grafico(v: Any) -> float:
    try:
        x = float(v)
        if math.isnan(x):
            return 0.0
        return max(0.0, min(100.0, x))
    except (TypeError, ValueError):
        return 0.0


def crear_grafico_medidor(titulo: str, valor: float) -> None:
    """
    Anillo SVG premium: halo radial, trazo redondeado y escala azul-gris.
    Sensación de instrumento de medición profesional.
    """
    tc = _tc()
    try:
        v = float(valor)
        if math.isnan(v):
            v = 0.0
    except (TypeError, ValueError):
        v = 0.0
    valor = max(0, min(100, v))
    color = obtener_color_semaforo(valor)

    radio          = 42
    grosor         = 7
    circunferencia = 2 * math.pi * radio
    offset         = circunferencia * (1 - valor / 100)

    gid = f"glow_{titulo.replace(' ', '').replace('.', '')}_{int(valor)}"

    html = f"""
<div class="talon-meter-gauge" style="
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
    chart_df = pd.DataFrame({
        _lbl('dimension_lbl'):  [
            _lbl('completitud'), _lbl('consistencia'),
            _lbl('unicidad'),    _lbl('validez'),
        ],
        _lbl('score_lbl'): [
            _score_grafico(res['completitud']), _score_grafico(res['consistencia']),
            _score_grafico(res['unicidad']), _score_grafico(res['validez']),
        ],
    })
    chart_df["Color"] = chart_df[_lbl("score_lbl")].apply(obtener_color_semaforo)

    dim_col = _lbl("dimension_lbl")
    score_col = _lbl("score_lbl")
    chart_df = chart_df.sort_values(score_col, ascending=False)
    filas = [
        (str(row[dim_col]), float(row[score_col]), str(row["Color"]))
        for _, row in chart_df.iterrows()
    ]
    _render_barras_porcentaje_html(
        filas,
        titulo=_lbl("comparativa"),
        cabecera_columnas=(_lbl("dimension_lbl"), _lbl("score_lbl")),
        alto_pista_px=20,
        mostrar_escala=True,
        incremento_escala=10,
    )


# ─────────────────────────────────────────────
#  TABLA TOP ANOMALÍAS
# ─────────────────────────────────────────────
def renderizar_tabla_top_errores(df_procesado: pd.DataFrame) -> None:
    _subtitulo(_lbl("top_anomalias"))

    df_base = _df_base_como_explorador(df_procesado)
    total_registros = len(df_base)
    if total_registros == 0:
        _alerta_vacia(_lbl("sin_anomalias"))
        return

    analisis = _explorador_nulos_analisis(df_base)
    if analisis is None:
        _alerta_vacia(_lbl("sin_hallazgos"))
        return

    _chk, fail_mat, cols_con_fallo, _cores, pairs = analisis
    del _chk, _cores

    if not cols_con_fallo:
        st.success(_lbl("explorer_sin_fallos"))
        return

    tipo_col = _lbl("tipo_falla")
    reg_col = _lbl("reg_afectados")
    pct_col = "% del Total"

    rows = [
        {tipo_col: etiqueta, reg_col: int(fail_mat[col_orig].sum())}
        for col_orig, etiqueta in pairs
    ]
    df_c = pd.DataFrame(rows).sort_values(reg_col, ascending=False)
    denom = max(1, total_registros)
    df_c[pct_col] = (df_c[reg_col] / denom * 100).round(1)

    st.dataframe(
        df_c,
        width="stretch",
        hide_index=True,
        column_config={
            tipo_col: st.column_config.TextColumn(tipo_col, width="large"),
            reg_col: st.column_config.NumberColumn(reg_col, format="%d"),
            pct_col: st.column_config.ProgressColumn(pct_col, format="%.1f%%", min_value=0, max_value=100),
        },
    )


# ─────────────────────────────────────────────
#  GRÁFICO CALIDAD POR TIPO DE MATERIAL
# ─────────────────────────────────────────────
def renderizar_grafico_por_foco(df_procesado: pd.DataFrame) -> None:
    if 'tipo_mat' not in df_procesado.columns:
        st.info(_lbl('sin_tipo_mat'))
        return

    df_base = _df_base_como_explorador(df_procesado)
    if len(df_base) == 0:
        _alerta_vacia(_lbl('sin_anomalias'))
        return

    tipo_col  = _lbl('categoria_lbl')
    score_col = _lbl('score_prom_lbl')

    df_g = (
        df_base.groupby('tipo_mat')['Score_Calidad']
        .mean()
        .reset_index()
        .rename(columns={'tipo_mat': tipo_col, 'Score_Calidad': score_col})
    )
    df_g[score_col] = df_g[score_col].map(_score_grafico)
    df_g["Color"] = df_g[score_col].apply(obtener_color_semaforo)
    df_g = df_g.sort_values(score_col, ascending=False)
    filas = [
        (str(row[tipo_col]), float(row[score_col]), str(row["Color"]))
        for _, row in df_g.iterrows()
    ]
    _render_barras_porcentaje_html(
        filas,
        titulo=_lbl("calidad_mat"),
        alto_pista_px=20,
        mostrar_escala=True,
        incremento_escala=5,
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

    df_view = df.copy()

    if "Estado_Gestion" in df_view.columns:
        df_view["Estado_Gestion"] = df_view["Estado_Gestion"].apply(
            lambda x: _lbl("pendiente") if x == 0 else (_lbl("gestionado") if x == 1 else x)
        )

    analisis = _explorador_nulos_analisis(df_view)
    if analisis is None:
        st.info(_lbl("sin_hallazgos"))
        return

    check_cols, fail_mat, cols_con_fallo, cols_core, pairs = analisis

    if not cols_con_fallo:
        st.success(_lbl("explorer_sin_fallos"))
        return

    columnas_ocultar = [
        "Hallazgos_Detallados",
        "Score_Calidad",
        "Score_Completitud",
        "Score_Validez",
        "Score_Unicidad",
        "Score_Consistencia",
    ]

    mascara_falla = fail_mat[cols_con_fallo].any(axis=1)
    df_view = df_view.loc[mascara_falla].copy()

    quitar = [c for c in columnas_ocultar if c in df_view.columns] + list(check_cols)
    df_show = df_view.drop(columns=quitar, errors="ignore")

    for col_orig, nombre_vis in pairs:
        df_show[nombre_vis] = df_view[col_orig].map(_marcacion_celda)

    if "SKU" in df_show.columns:
        df_show["SKU"] = df_show["SKU"].map(_format_sku_celda)

    nombres_marcas = [nombre for _, nombre in pairs]
    ordered: List[str] = list(cols_core) + nombres_marcas
    final_cols: List[str] = []
    for c in ordered:
        if c in df_show.columns and c not in final_cols:
            final_cols.append(c)
    df_main = df_show[final_cols]

    col_config: Dict[str, Any] = {}
    if "SKU" in df_main.columns:
        col_config["SKU"] = st.column_config.TextColumn("SKU", width="medium")
    if "Desc_Material" in df_main.columns:
        col_config["Desc_Material"] = st.column_config.TextColumn(
            _lbl("explorer_hdr_desc_material"),
            width="large",
        )
    if "Estado_Gestion" in df_main.columns:
        col_config["Estado_Gestion"] = st.column_config.TextColumn(
            _lbl("explorer_hdr_estado_gestion"),
            width="small",
        )
    if "tipo_mat" in df_main.columns:
        col_config["tipo_mat"] = st.column_config.TextColumn(
            _lbl("explorer_hdr_tipo_mat"),
            width="small",
        )
    for _, nombre_vis in pairs:
        if nombre_vis in df_main.columns:
            col_config[nombre_vis] = st.column_config.TextColumn(
                nombre_vis,
                width="small",
                help=_lbl("explorer_marks_hint"),
            )

    _renderizar_tabla_con_copia_sku(df_main, nombres_marcas, col_config)


def _renderizar_tabla_con_copia_sku(
    df_main: pd.DataFrame,
    nombres_marcas: List[str],
    col_config: Dict[str, Any],
) -> None:
    """
    Tabla HTML renderizada directamente con st.markdown (sin iframe).
    Al no usar st_components.html() se elimina el límite de 150 px que
    Streamlit inyecta en el iframe y que impedía ver todas las filas.
    El botón de copia de SKU usa un ID único por tabla para que el
    script inline no colisione si hay varias tablas en la misma página.
    """
    import uuid as _uuid
    tabla_id = "tln_" + _uuid.uuid4().hex[:8]

    mark_pass = _lbl("explorer_mark_pass")
    mark_fail = _lbl("explorer_mark_fail")
    mark_na   = _lbl("explorer_mark_na")
    marca_set = set(nombres_marcas)
    cols      = list(df_main.columns)

    def _vis_header(col: str) -> str:
        cfg = col_config.get(col)
        if cfg is not None:
            label = getattr(cfg, "label", None) or getattr(cfg, "_label", None)
            if label:
                return html.escape(str(label))
        return html.escape(col.replace("_", " "))

    # ── THEAD ──────────────────────────────────────────────────────
    ths = "".join(f"<th>{_vis_header(c)}</th>" for c in cols)

    # ── TBODY ──────────────────────────────────────────────────────
    rows_html = ""
    for _, row in df_main.iterrows():
        tds = ""
        for c in cols:
            raw     = row[c]
            val_str = "" if (isinstance(raw, float) and pd.isna(raw)) else str(raw)
            escaped = html.escape(val_str)
            if c == "SKU":
                sku_safe = html.escape(val_str, quote=True)
                tds += (
                    f'<td class="tln-sku-cell">'
                    f'<div class="tln-sku-wrap">'
                    f'<span class="tln-sku-text">{escaped}</span>'
                    f'<button class="tln-sku-copy" data-val="{sku_safe}" title="Copiar SKU">'
                    f'<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">'
                    f'<path d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6'
                    f'a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0'
                    f' 1-1V2a1 1 0 0 0-1-1H6z"/>'
                    f'<path d="M2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1H9v1H2V6h1V5H2z"/>'
                    f'</svg>'
                    f'</button>'
                    f'</div></td>'
                )
            elif c in marca_set:
                if val_str == mark_pass:
                    tds += f'<td class="tln-mc"><span class="tln-mk tln-pass">{escaped}</span></td>'
                elif val_str == mark_fail:
                    tds += f'<td class="tln-mc"><span class="tln-mk tln-fail">{escaped}</span></td>'
                elif val_str == mark_na:
                    tds += f'<td class="tln-mc"><span class="tln-mk tln-na">{escaped}</span></td>'
                else:
                    tds += f'<td class="tln-mc">{escaped}</td>'
            else:
                tds += f'<td>{escaped}</td>'
        rows_html += f"<tr>{tds}</tr>"

    # ── HTML completo — sin iframe, renderizado en el DOM de Streamlit ──
    html_content = f"""
<style>
  /* Scope con prefijo tln- para no colisionar con los estilos de Streamlit */
  .tln-wrap {{
    width: 100%;
    overflow-x: auto;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding-bottom: 8px;
    margin-bottom: 5px;
    box-sizing: border-box;
  }}
  .tln-wrap table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .tln-wrap thead tr {{
    background: #111827;
    border-bottom: 1px solid #1F2937;
  }}
  .tln-wrap th {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #64748B;
    padding: 12px 16px;
    text-align: left;
    white-space: nowrap;
  }}
  .tln-wrap tbody tr {{
    border-bottom: 1px solid #161D28;
    transition: background 0.1s;
  }}
  .tln-wrap tbody tr:nth-child(even) {{ background: rgba(148,163,184,0.03); }}
  .tln-wrap tbody tr:hover {{ background: rgba(59,130,246,0.07); }}
  .tln-wrap td {{
    padding: 14px 16px;
    vertical-align: middle;
    white-space: nowrap;
    font-size: 13px;
    color: #CBD5E1;
  }}
  .tln-sku-cell {{ min-width: 150px; }}
  .tln-sku-wrap {{ display: flex; align-items: center; gap: 6px; }}
  .tln-sku-text {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px;
    color: #E2E8F0;
  }}
  .tln-sku-copy {{
    opacity: 0;
    background: none;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #3B82F6;
    cursor: pointer;
    padding: 2px 4px;
    line-height: 1;
    transition: opacity 0.15s, background 0.15s, border-color 0.15s, color 0.15s;
    flex-shrink: 0;
  }}
  .tln-sku-cell:hover .tln-sku-copy {{ opacity: 1; }}
  .tln-sku-copy:hover {{
    background: rgba(59,130,246,0.15);
    border-color: #3B82F6;
  }}
  .tln-sku-copy.tln-ok {{ opacity: 1 !important; color: #86efac; border-color: #22c55e; }}
  .tln-mc {{ text-align: center; }}
  .tln-mk {{
    display: inline-block;
    min-width: 26px;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 13px;
    text-align: center;
  }}
  .tln-pass {{ color: #86efac; background: rgba(34,197,94,0.18); }}
  .tln-fail {{ color: #fca5a5; background: rgba(239,68,68,0.22); }}
  .tln-na   {{ color: #94a3b8; background: rgba(148,163,184,0.12); }}
</style>
<div class="tln-wrap" id="{tabla_id}">
  <table><thead><tr>{ths}</tr></thead><tbody>{rows_html}</tbody></table>
</div>
<script>
(function() {{
  var tabla = document.getElementById('{tabla_id}');
  if (!tabla) return;
  tabla.querySelectorAll('.tln-sku-copy').forEach(function(btn) {{
    btn.addEventListener('click', function(e) {{
      e.stopPropagation();
      var val = btn.getAttribute('data-val');
      navigator.clipboard.writeText(val).then(function() {{
        var orig = btn.innerHTML;
        btn.classList.add('tln-ok');
        btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>';
        setTimeout(function() {{
          btn.classList.remove('tln-ok');
          btn.innerHTML = orig;
        }}, 1600);
      }});
    }});
  }});
}})();
</script>"""

    st.markdown(html_content, unsafe_allow_html=True)


def renderizar_botones_copia_sku(skus: List[str]) -> None:
    pass  # Ya no se usa — mantenida para no romper imports externos


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