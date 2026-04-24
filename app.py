import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai
from datetime import datetime

# --- 1. CONFIGURACIÓN IA (Opcional) ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "AIzaSyDjUtH9G-G__9QR6GNIk3acZn1_xStWm7Q" 

if API_KEY != "AIzaSyDjUtH9G-G__9QR6GNIk3acZn1_xStWm7Q" and API_KEY != "":
    try:
        genai.configure(api_key=API_KEY)
        # Usamos el modelo más estable para reportes rápidos
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        pass

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="MCC - Copec Analytics", page_icon="🚜")

# Estilos CSS personalizados para una apariencia premium
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }
    .stCaption {
        text-align: center;
        font-style: italic;
        color: #94a3b8;
        margin-top: -15px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Función para generar los velocímetros (Gauges)
def crear_gauge(valor, titulo, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': titulo, 'font': {'size': 16, 'color': '#64748b', 'weight': 'bold'}},
        number = {'suffix': "%", 'font': {'size': 20, 'color': '#1e293b'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "#f1f5f9",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
        }
    ))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=10))
    return fig

# --- HEADER DEL DASHBOARD ---
st.title("🚀 MCC - AI Analysis System")
st.caption("Panel de Confiabilidad y Gestión de Mantenimiento • Copec S.A.")

# --- CARGA Y PROCESAMIENTO DE DATOS ---
st.sidebar.header("⚙️ Configuración")
uploaded_file = st.sidebar.file_uploader("Cargar Base de Datos (CSV)", type="csv")

if uploaded_file:
    try:
        # Carga del archivo con detección automática de separador
        df = pd.read_csv(uploaded_file, encoding='latin-1', sep=None, engine='python')
        # Estandarizar nombres de columnas (Mayúsculas y sin espacios)
        df.columns = [c.upper().strip() for c in df.columns]
        
        # Procesamiento de Fechas para filtros temporales
        if 'FECHA_MUESTRA' in df.columns:
            df['FECHA_MUESTRA'] = pd.to_datetime(df['FECHA_MUESTRA'], errors='coerce')
            df = df.dropna(subset=['FECHA_MUESTRA'])
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # --- PANEL DE FILTROS LATERALES ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Filtros de Análisis")
    
    # 1. Filtro por Faena
    faenas = ["Todas"] + sorted(df['NOMBRE_FAENA'].unique().tolist())
    faena_sel = st.sidebar.selectbox("Seleccionar Faena", faenas)
    
    # Filtro inicial por Faena
    df_filtered = df if faena_sel == "Todas" else df[df['NOMBRE_FAENA'] == faena_sel]

    # 2. Filtro por Rango de Fechas
    if 'FECHA_MUESTRA' in df.columns:
        min_date = df['FECHA_MUESTRA'].min().date()
        max_date = df['FECHA_MUESTRA'].max().date()
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Período de Tiempo")
        date_range = st.sidebar.date_input(
            "Seleccionar Rango",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Validación y aplicación del filtro de fecha
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[
                (df_filtered['FECHA_MUESTRA'].dt.date >= start_date) & 
                (df_filtered['FECHA_MUESTRA'].dt.date <= end_date)
            ]

    # --- CÁLCULOS DINÁMICOS DE KPIs ---
    total_m = len(df_filtered)
    if total_m > 0:
        alertas_n = len(df_filtered[df_filtered['ESTADO'] == 'ALERTA'])
        precaucion_n = len(df_filtered[df_filtered['ESTADO'] == 'PRECAUCION'])
        
        criticidad = (alertas_n / total_m * 100)
        tasa_precaucion = (precaucion_n / total_m * 100)

        if 'COMPONENTE' in df_filtered.columns:
            conteo = df_filtered['COMPONENTE'].value_counts()
            tasa_reincidencia = (len(conteo[conteo > 1]) / len(conteo) * 100) if not conteo.empty else 0
        else: 
            tasa_reincidencia = 0
    else:
        criticidad = tasa_precaucion = tasa_reincidencia = 0

    # --- VISUALIZACIÓN: INDICADORES PRINCIPALES ---
    st.markdown(f"### 📊 Dashboard: {faena_sel}")
    if total_m > 0:
        st.write(f"Mostrando datos desde **{df_filtered['FECHA_MUESTRA'].min().strftime('%d/%m/%Y')}** hasta **{df_filtered['FECHA_MUESTRA'].max().strftime('%d/%m/%Y')}**")
    
    g1, g2, g3, g4 = st.columns(4)
    
    with g1:
        st.plotly_chart(crear_gauge(criticidad, "Criticidad", "#ef4444" if criticidad > 20 else "#10b981"), use_container_width=True)
        st.caption("Muestras en ALERTA / Total")
        
    with g2:
        st.plotly_chart(crear_gauge(tasa_precaucion, "Alerta Temprana", "#f59e0b"), use_container_width=True)
        st.caption("Muestras en PRECAUCIÓN")
        
    with g3:
        st.plotly_chart(crear_gauge(tasa_reincidencia, "Reincidencia", "#6366f1"), use_container_width=True)
        st.caption("Fallas repetitivas por componente")
        
    with g4:
        st.plotly_chart(crear_gauge(100-criticidad, "Salud Fluido", "#3b82f6"), use_container_width=True)
        st.caption("Activos con lubricante operativo")

    # --- ANÁLISIS DE CONTAMINACIÓN ---
    st.markdown("---")
    st.subheader("⚠️ Análisis de Contaminación Externo")
    c1, c2 = st.columns([2, 1])

    with c1:
        if 'SILICIO' in df_filtered.columns and 'SODIO' in df_filtered.columns:
            fig_cont = px.scatter(
                df_filtered, x='SILICIO', y='SODIO', color='ESTADO',
                size='HIERRO' if 'HIERRO' in df_filtered.columns else None,
                hover_name='EQUIPO', title="Relación Silicio vs Sodio (Contaminación)",
                color_discrete_map={'ALERTA':'#ef4444','PRECAUCION':'#f59e0b','NORMAL':'#10b981'}
            )
            st.plotly_chart(fig_cont, use_container_width=True)
        else:
            st.warning("Faltan datos de Silicio/Sodio para este período.")

    with c2:
        st.write("**Top Equipos Críticos (Período Seleccionado)**")
        if 'SILICIO' in df_filtered.columns:
            top_cont = df_filtered.nlargest(5, 'SILICIO')[['EQUIPO', 'SILICIO', 'ESTADO']]
            st.dataframe(top_cont, hide_index=True, use_container_width=True)

    # --- DESGASTE METÁLICO (HEATMAP) ---
    st.markdown("---")
    st.subheader("🔍 Mapa de Desgaste por Metales (PPM)")
    metales = ['HIERRO', 'COBRE', 'PLOMO', 'ALUMINIO', 'CROMO']
    metales_presentes = [m for m in metales if m in df_filtered.columns]

    if metales_presentes:
        df_metales = df_filtered.groupby('EQUIPO')[metales_presentes].mean().head(15)
        fig_heat = px.imshow(
            df_metales, text_auto=True, aspect="auto",
            title="Concentración de Metales (Promedio)",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    
    # --- MATRIZ DE DECISIONES DE MANTENIMIENTO ---
    st.markdown("---")
    st.subheader("📋 Matriz de Decisiones de Mantenimiento")
    cols_mant = ['EQUIPO', 'COMPONENTE', 'ESTADO', 'HIERRO', 'SILICIO', 'VISCOSIDAD', 'FECHA_MUESTRA']
    cols_final = [c for c in cols_mant if c in df_filtered.columns]
    
    df_editor = df_filtered[cols_final].copy()
    if 'FECHA_MUESTRA' in df_editor.columns:
        df_editor['FECHA_MUESTRA'] = df_editor['FECHA_MUESTRA'].dt.strftime('%Y-%m-%d')

    st.data_editor(
        df_editor.sort_values(by='HIERRO', ascending=False) if 'HIERRO' in df_editor.columns else df_editor,
        column_config={
            "ESTADO": st.column_config.SelectboxColumn("Prioridad", options=["ALERTA", "PRECAUCION", "NORMAL"]),
            "HIERRO": st.column_config.NumberColumn("Fe (ppm)", format="%d ⚠️"),
            "FECHA_MUESTRA": st.column_config.DateColumn("Fecha Lab")
        },
        use_container_width=True,
        hide_index=True
    )

    # --- DISTRIBUCIÓN POR EQUIPO ---
    st.markdown("---")
    if 'EQUIPO' in df_filtered.columns:
        st.subheader("🚜 Estado por Equipo en el Período")
        e_data = df_filtered.groupby(['EQUIPO', 'ESTADO']).size().unstack(fill_value=0).reset_index()
        # Asegurar que las columnas existan antes de graficar
        for col in ['ALERTA', 'PRECAUCION', 'NORMAL']:
            if col not in e_data.columns:
                e_data[col] = 0
        fig_e = px.bar(e_data, y='EQUIPO', x=['ALERTA', 'PRECAUCION', 'NORMAL'], 
                       orientation='h', color_discrete_map={'ALERTA':'#ef4444','PRECAUCION':'#f59e0b','NORMAL':'#10b981'})
        st.plotly_chart(fig_e, use_container_width=True)

else:
    # Mensaje de bienvenida inicial
    st.info("👋 Por favor, carga tu archivo CSV de laboratorio para activar el dashboard.")
    st.markdown("""
        ### Funcionalidades Disponibles:
        * **Filtro de Faenas y Fechas:** Analice períodos específicos de operación.
        * **Heatmap de Metales:** Identifique qué metal está desgastando sus activos.
        * **Matriz de Decisiones:** Priorice intervenciones técnicas de inmediato.
    """)
