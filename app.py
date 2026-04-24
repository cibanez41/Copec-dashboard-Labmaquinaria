import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai
# --- 1. CONFIGURACIÓN IA ---
# Buscamos la etiqueta 'GEMINI_API_KEY' en los secretos de la nube
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    # Si estás en tu PC local, puedes poner tu clave aquí para probar
    API_KEY = "AIzaSyDjUtH9G-G__9QR6GNIk3acZn1_xStWm7Q" 

# Configuración final
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # Cambiamos 'gemini-1.5-flash' por 'gemini-pro' o el nombre técnico completo
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
    except Exception as e:
        st.error(f"Error al configurar IA: {e}")
        
# Solo configuramos si la clave no es el texto por defecto
if API_KEY != "TU_API_KEY_LOCAL_AQUÍ" and API_KEY != "":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="MCC - Copec Analytics AI", page_icon="🤖")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;        
    }
    /* Estilo para que el caption se vea centrado y pequeño como en el diseño */
    .stCaption {
        text-align: center;
        font-style: italic;
        color: #94a3b8;
        margin-top: -20px;
        padding-bottom: 20px;
    }     
    </style>
    """, unsafe_allow_html=True)

# Función para crear Velocímetros
def crear_gauge(valor, titulo, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': titulo, 'font': {'size': 18, 'color': '#64748b', 'weight': 'bold'}},
        number = {'suffix': "%", 'font': {'size': 24, 'color': '#1e293b'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "#f1f5f9",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- HEADER ---
st.title("🚀 MCC - AI Analysis System")
st.caption("Panel de Confiabilidad • Copec S.A.")

# --- CARGA DE DATOS ---
st.sidebar.header("⚙️ Configuración")
uploaded_file = st.sidebar.file_uploader("Cargar Base de Datos (CSV)", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='latin-1', sep=None, engine='python')
        df.columns = [c.upper().strip() for c in df.columns]
    except Exception as e:
        st.error(f"Error al leer: {e}")
        st.stop()

    # FILTROS
    faenas = ["Todas"] + sorted(df['NOMBRE_FAENA'].unique().tolist())
    faena_sel = st.sidebar.selectbox("Seleccionar Faena", faenas)
    df_filtered = df if faena_sel == "Todas" else df[df['NOMBRE_FAENA'] == faena_sel]

    # --- CÁLCULOS DINÁMICOS ---
    total_m = len(df_filtered)
    alertas_n = len(df_filtered[df_filtered['ESTADO'] == 'ALERTA'])
    precaucion_n = len(df_filtered[df_filtered['ESTADO'] == 'PRECAUCION'])
    criticidad = (alertas_n / total_m * 100) if total_m > 0 else 0
    tasa_precaucion = (precaucion_n / total_m * 100) if total_m > 0 else 0
    
    # Reincidencia Real
    if 'COMPONENTE' in df_filtered.columns:
        conteo = df_filtered['COMPONENTE'].value_counts()
        tasa_reincidencia = (len(conteo[conteo > 1]) / len(conteo) * 100) if not conteo.empty else 0
    else: tasa_reincidencia = 0

# --- INDICADORES (VELOCÍMETROS) ---
    st.markdown("### 📊 Salud de Activos")
    g1, g2, g3, g4 = st.columns(4)
    
    with g1:
        st.plotly_chart(crear_gauge(criticidad, "Criticidad Flota", "#ef4444" if criticidad > 20 else "#10b981"), use_container_width=True)
        st.caption("Impacto de muestras en Alerta sobre el Total")
        
    with g2:
        st.plotly_chart(crear_gauge(tasa_precaucion, "Alerta Temprana", "#f59e0b"), use_container_width=True)
        st.caption("Muestras en observación preventiva")
        
    with g3:
        st.plotly_chart(crear_gauge(tasa_reincidencia, "Reincidencia", "#6366f1"), use_container_width=True)
        st.caption("Componentes con fallas repetitivas")
        
    with g4:
        st.plotly_chart(crear_gauge(100-criticidad, "Salud Fluido", "#3b82f6"), use_container_width=True)
        st.caption("Activos con fluido operativo")

    ## --- CONSULTOR IA ---
    st.markdown("---")
    st.header("🤖 Consultor Experto IA")
    
    if API_KEY == "TU_API_KEY_AQUÍ":
        st.warning("⚠️ Falta configurar la API KEY en el código para activar la IA.")
    else:
        if st.button("✨ Generar Reporte Técnico"):
            with st.spinner('Analizando datos de laboratorio...'):
                try:
                    # Resumen para la IA
                    hierro_avg = df_filtered['HIERRO'].mean() if 'HIERRO' in df_filtered.columns else 0
                    prompt = f"""
                    Actúa como Ingeniero Senior de Lubricación. Analiza estos datos:
                    Faena: {faena_sel}
                    Criticidad: {criticidad:.1f}%
                    Reincidencia: {tasa_reincidencia:.1f}%
                    Hierro Promedio: {hierro_avg:.1f} ppm.
                    Genera un reporte técnico de 3 puntos clave y una recomendación de acción inmediata.
                    """
                    # IMPORTANTE: Aquí usamos 'model'
                    response = model.generate_content(prompt)
                    st.info("### 📝 Reporte Técnico Sugerido")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error de IA: {e}")

    # --- GRÁFICOS (ORDENADOS VERTICALMENTE) ---
    st.markdown("---")
    
    # Salud por Faena (Cambia orientación si se filtra)
    st.subheader("📍 Salud por Faena")
    f_data = df.groupby(['NOMBRE_FAENA', 'ESTADO']).size().unstack(fill_value=0).reset_index()
    for col in ['ALERTA', 'PRECAUCION', 'NORMAL']:
        if col not in f_data: f_data[col] = 0

    if faena_sel == "Todas":
        fig_f = px.bar(f_data, y='NOMBRE_FAENA', x=['ALERTA', 'PRECAUCION', 'NORMAL'], orientation='h', color_discrete_map={'ALERTA':'#ef4444','PRECAUCION':'#f59e0b','NORMAL':'#10b981'}, text_auto=True)
    else:
        f_data_f = f_data[f_data['NOMBRE_FAENA'] == faena_sel]
        fig_f = px.bar(f_data_f, x='NOMBRE_FAENA', y=['ALERTA', 'PRECAUCION', 'NORMAL'], orientation='v', color_discrete_map={'ALERTA':'#ef4444','PRECAUCION':'#f59e0b','NORMAL':'#10b981'}, text_auto=True)
    
    st.plotly_chart(fig_f, use_container_width=True)

    # Salud por Equipo
    st.subheader("🚜 Salud por Equipo")
    if 'EQUIPO' in df_filtered.columns:
        e_data = df_filtered.groupby(['EQUIPO', 'ESTADO']).size().unstack(fill_value=0).reset_index()
        for col in ['ALERTA', 'PRECAUCION', 'NORMAL']:
            if col not in e_data: e_data[col] = 0
        fig_e = px.bar(e_data, y='EQUIPO', x=['ALERTA', 'PRECAUCION', 'NORMAL'], orientation='h', color_discrete_map={'ALERTA':'#ef4444','PRECAUCION':'#f59e0b','NORMAL':'#10b981'}, text_auto=True)
        st.plotly_chart(fig_e, use_container_width=True)

else:
    st.info("👋 Sube tu archivo CSV para activar el sistema.")
