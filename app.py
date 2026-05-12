# app.py — Dashboard Inteligente de Mantenimiento con IA

```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
from sklearn.ensemble import IsolationForest

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="CSI • Maintenance Intelligence Center",
    page_icon="🚜",
    layout="wide"
)

# =====================================================
# CONFIG GEMINI
# =====================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# =====================================================
# CSS MODERNO
# =====================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f4f7fb;
    }

    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 6px solid #2563eb;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .ia-box {
        background-color: #eef6ff;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #2563eb;
        margin-top: 10px;
        color: #1e293b;
    }

    .critical-box {
        background-color: #fff1f2;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #ef4444;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FUNCIONES
# =====================================================

@st.cache_data
def load_data(file):
    df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python')

    df.columns = [c.upper().strip() for c in df.columns]

    if 'FECHA_MUESTREO' in df.columns:
        df.rename(columns={'FECHA_MUESTREO': 'FECHA_MUESTRA'}, inplace=True)

    if 'FECHA_MUESTRA' in df.columns:
        df['FECHA_MUESTRA'] = pd.to_datetime(df['FECHA_MUESTRA'], errors='coerce')

    return df


def generar_insight_ia(contexto, titulo="Análisis"):

    if not model:
        return "IA no disponible"

    try:
        prompt = f"""
        Eres un ingeniero senior especialista en análisis de aceite y confiabilidad.

        Analiza:
        {contexto}

        Entrega:
        1. Diagnóstico técnico
        2. Riesgo operacional
        3. Posible causa raíz
        4. Acción recomendada

        Máximo 100 palabras.
        """

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"Error IA: {e}"


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("⚙️ Configuración")

uploaded_file = st.sidebar.file_uploader(
    "Cargar CSV",
    type=['csv']
)

# =====================================================
# MAIN
# =====================================================

st.title("🚜 Maintenance Intelligence Center")
st.caption("CSI / Copec • Analítica Inteligente de Lubricación y Confiabilidad")

if uploaded_file:

    df = load_data(uploaded_file)

    # =====================================================
    # FILTROS
    # =====================================================

    st.sidebar.markdown("---")

    if 'NOMBRE_FAENA' in df.columns:

        faenas = ['Todas'] + sorted(df['NOMBRE_FAENA'].dropna().unique())

        faena_sel = st.sidebar.selectbox(
            'Seleccionar Faena',
            faenas
        )

        if faena_sel != 'Todas':
            df = df[df['NOMBRE_FAENA'] == faena_sel]

    if 'FECHA_MUESTRA' in df.columns:

        min_date = df['FECHA_MUESTRA'].min().date()
        max_date = df['FECHA_MUESTRA'].max().date()

        rango = st.sidebar.date_input(
            'Rango Fechas',
            (min_date, max_date)
        )

        if len(rango) == 2:
            start, end = rango

            df = df[
                (df['FECHA_MUESTRA'].dt.date >= start) &
                (df['FECHA_MUESTRA'].dt.date <= end)
            ]

    # =====================================================
    # KPIs EJECUTIVOS
    # =====================================================

    total = len(df)

    alertas = len(df[df['ESTADO'] == 'ALERTA']) if 'ESTADO' in df.columns else 0

    precaucion = len(df[df['ESTADO'] == 'PRECAUCION']) if 'ESTADO' in df.columns else 0

    criticidad = round(alertas / total * 100, 1) if total > 0 else 0

    salud = round(100 - criticidad, 1)

    # Índice desgaste compuesto
    for col in ['HIERRO', 'COBRE', 'PLOMO', 'ALUMINIO']:
        if col not in df.columns:
            df[col] = 0

    df['IDC'] = (
        df['HIERRO'] * 0.4 +
        df['COBRE'] * 0.3 +
        df['PLOMO'] * 0.2 +
        df['ALUMINIO'] * 0.1
    )

    # Índice contaminación
    for col in ['SILICIO', 'SODIO']:
        if col not in df.columns:
            df[col] = 0

    df['IC'] = df['SILICIO'] + df['SODIO']

    # =====================================================
    # SCORE RIESGO
    # =====================================================

    def normalizar(col):

        if df[col].max() == df[col].min():
            return 0

        return (df[col] - df[col].min()) / (df[col].max() - df[col].min())

    df['RIESGO_SCORE'] = (
        normalizar('HIERRO') * 0.35 +
        normalizar('SILICIO') * 0.25 +
        normalizar('COBRE') * 0.20 +
        normalizar('IDC') * 0.20
    ) * 100

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "🚨 Criticidad",
            f"{criticidad}%",
            delta=f"{alertas} alertas"
        )

    with c2:
        st.metric(
            "🟡 Precaución",
            f"{precaucion}",
            delta="Monitoreo"
        )

    with c3:
        st.metric(
            "🟢 Salud General",
            f"{salud}%",
            delta="Operativo"
        )

    with c4:
        st.metric(
            "⚠️ Riesgo Medio",
            f"{round(df['RIESGO_SCORE'].mean(),1)}",
            delta="IA Score"
        )

    # =====================================================
    # IA EJECUTIVA
    # =====================================================

    st.markdown("---")
    st.subheader("🧠 Executive AI Summary")

    contexto_general = f"""
    Total muestras: {total}
    Alertas: {alertas}
    Precaución: {precaucion}
    Criticidad: {criticidad}%
    Riesgo promedio: {round(df['RIESGO_SCORE'].mean(),1)}
    """

    with st.container():
        st.markdown(
            f"""
            <div class='ia-box'>
            {generar_insight_ia(contexto_general)}
            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # TOP EQUIPOS CRÍTICOS
    # =====================================================

    st.markdown("---")
    st.subheader("🚨 Ranking Inteligente de Equipos")

    if 'EQUIPO' in df.columns:

        top_eq = df.groupby('EQUIPO').agg({
            'RIESGO_SCORE': 'mean',
            'HIERRO': 'mean',
            'SILICIO': 'mean',
            'IDC': 'mean'
        }).reset_index()

        top_eq = top_eq.sort_values(
            by='RIESGO_SCORE',
            ascending=False
        ).head(15)

        fig_top = px.bar(
            top_eq,
            x='RIESGO_SCORE',
            y='EQUIPO',
            orientation='h',
            color='RIESGO_SCORE',
            title='Top Equipos Críticos',
            text_auto='.1f'
        )

        st.plotly_chart(fig_top, use_container_width=True)

        with st.expander("🧠 Insight IA"):
            st.write(
                generar_insight_ia(top_eq.to_string())
            )

    # =====================================================
    # TENDENCIA HIERRO
    # =====================================================

    st.markdown("---")
    st.subheader("📈 Tendencia Temporal de Desgaste")

    if 'FECHA_MUESTRA' in df.columns:

        trend = df.groupby('FECHA_MUESTRA')['HIERRO'].mean().reset_index()

        fig_line = px.line(
            trend,
            x='FECHA_MUESTRA',
            y='HIERRO',
            markers=True,
            title='Tendencia Hierro Promedio'
        )

        st.plotly_chart(fig_line, use_container_width=True)

        with st.expander("🧠 Insight IA"):
            st.write(
                generar_insight_ia(trend.tail(10).to_string())
            )

    # =====================================================
    # CONTAMINACIÓN
    # =====================================================

    st.markdown("---")
    st.subheader("⚠️ Análisis de Contaminación")

    if 'SILICIO' in df.columns and 'SODIO' in df.columns:

        fig_cont = px.scatter(
            df,
            x='SILICIO',
            y='SODIO',
            size='HIERRO' if 'HIERRO' in df.columns else None,
            color='RIESGO_SCORE',
            hover_name='EQUIPO' if 'EQUIPO' in df.columns else None,
            title='Silicio vs Sodio'
        )

        st.plotly_chart(fig_cont, use_container_width=True)

        with st.expander("🧠 Insight IA"):
            st.write(
                generar_insight_ia(df[['SILICIO','SODIO','HIERRO']].describe().to_string())
            )

    # =====================================================
    # HEATMAP METALES
    # =====================================================

    st.markdown("---")
    st.subheader("🔥 Heatmap de Desgaste")

    metales = ['HIERRO', 'COBRE', 'PLOMO', 'ALUMINIO', 'CROMO']

    metales_ok = [m for m in metales if m in df.columns]

    if 'EQUIPO' in df.columns and len(metales_ok) > 0:

        heat = df.groupby('EQUIPO')[metales_ok].mean().head(20)

        fig_heat = px.imshow(
            heat,
            text_auto=True,
            aspect='auto',
            color_continuous_scale='Reds'
        )

        st.plotly_chart(fig_heat, use_container_width=True)

        with st.expander("🧠 Insight IA"):
            st.write(
                generar_insight_ia(heat.to_string())
            )

    # =====================================================
    # DETECCIÓN ANOMALÍAS IA
    # =====================================================

    st.markdown("---")
    st.subheader("🤖 Detección Inteligente de Anomalías")

    cols_model = ['HIERRO', 'COBRE', 'SILICIO', 'IDC']

    cols_model = [c for c in cols_model if c in df.columns]

    if len(cols_model) >= 2:

        X = df[cols_model].fillna(0)

        model_iso = IsolationForest(
            contamination=0.05,
            random_state=42
        )

        df['ANOMALIA'] = model_iso.fit_predict(X)

        anom = df[df['ANOMALIA'] == -1]

        st.write(f"Se detectaron {len(anom)} anomalías potenciales")

        if len(anom) > 0:
            st.dataframe(
                anom[[
                    c for c in [
                        'EQUIPO',
                        'HIERRO',
                        'COBRE',
                        'SILICIO',
                        'RIESGO_SCORE'
                    ] if c in anom.columns
                ]],
                use_container_width=True
            )

            with st.expander("🧠 Insight IA"):
                st.write(
                    generar_insight_ia(anom.head(20).to_string())
                )

    # =====================================================
    # CAUSA RAÍZ
    # =====================================================

    st.markdown("---")
    st.subheader("🔍 Causa Raíz")

    col1, col2 = st.columns(2)

    with col1:

        if 'COMPONENTE' in df.columns:

            comp = df.groupby('COMPONENTE')['RIESGO_SCORE'].mean().reset_index()

            comp = comp.sort_values(
                by='RIESGO_SCORE',
                ascending=False
            ).head(10)

            fig_comp = px.bar(
                comp,
                x='RIESGO_SCORE',
                y='COMPONENTE',
                orientation='h',
                title='Componentes Críticos'
            )

            st.plotly_chart(fig_comp, use_container_width=True)

    with col2:

        if 'LUBRICANTE' in df.columns:

            lub = df.groupby('LUBRICANTE')['RIESGO_SCORE'].mean().reset_index()

            lub = lub.sort_values(
                by='RIESGO_SCORE',
                ascending=False
            ).head(10)

            fig_lub = px.bar(
                lub,
                x='RIESGO_SCORE',
                y='LUBRICANTE',
                orientation='h',
                title='Lubricantes Críticos'
            )

            st.plotly_chart(fig_lub, use_container_width=True)

    # =====================================================
    # MATRIZ OPERACIONAL
    # =====================================================

    st.markdown("---")
    st.subheader("📋 Matriz Operacional Inteligente")

    cols_show = [
        'EQUIPO',
        'COMPONENTE',
        'ESTADO',
        'HIERRO',
        'SILICIO',
        'IDC',
        'RIESGO_SCORE'
    ]

    cols_show = [c for c in cols_show if c in df.columns]

    tabla = df[cols_show].sort_values(
        by='RIESGO_SCORE',
        ascending=False
    )

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # RECOMENDACIONES IA
    # =====================================================

    st.markdown("---")
    st.subheader("🧠 Recomendaciones Inteligentes")

    recomendaciones = generar_insight_ia(tabla.head(20).to_string())

    st.markdown(
        f"""
        <div class='critical-box'>
        {recomendaciones}
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.info("👋 Carga un archivo CSV para comenzar")

    st.markdown("""
    ## Funcionalidades

    - KPIs inteligentes
    - IA técnica integrada
    - Detección anomalías
    - Ranking de criticidad
    - Heatmaps
    - Tendencias temporales
    - Insights IA automáticos
    - Análisis causa raíz
    - Riesgo operacional
    """)

GEMINI_API_KEY = "TU_API_KEY"






