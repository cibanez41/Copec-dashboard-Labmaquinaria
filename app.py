import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import google.generativeai as genai

from datetime import datetime

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="CSI Maintenance Intelligence Center",
    page_icon="🚜",
    layout="wide"
)

# =====================================================
# CONFIG GEMINI
# =====================================================

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

model = None

if API_KEY:

    try:

        genai.configure(api_key=API_KEY)

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

    except Exception as e:

        st.warning(f"Gemini no disponible: {e}")

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.main {
    background-color: #f4f7fb;
}

div[data-testid="stMetric"] {
    background-color: white;
    border-radius: 15px;
    padding: 15px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
}

.ia-box {
    background-color: #eef6ff;
    padding: 15px;
    border-radius: 12px;
    border-left: 5px solid #2563eb;
    margin-top: 10px;
}

.alert-box {
    background-color: #fff1f2;
    padding: 15px;
    border-radius: 12px;
    border-left: 5px solid #ef4444;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# FUNCIONES
# =====================================================

@st.cache_data
def load_data(file):

    if file.name.endswith(".csv"):

        df = pd.read_csv(
            file,
            encoding="latin-1",
            sep=None,
            engine="python"
        )

    elif file.name.endswith(".xlsx"):

        df = pd.read_excel(file)

    else:

        st.error("Formato no soportado")
        st.stop()

    df.columns = [
        c.upper().strip()
        for c in df.columns
    ]

    if "FECHA_MUESTREO" in df.columns:

        df.rename(
            columns={
                "FECHA_MUESTREO": "FECHA_MUESTRA"
            },
            inplace=True
        )

    if "FECHA_MUESTRA" in df.columns:

        df["FECHA_MUESTRA"] = pd.to_datetime(
            df["FECHA_MUESTRA"],
            errors="coerce"
        )

    return df

def generar_insight_ia(contexto):

    if model is None:

        return "IA no disponible"

    try:

        prompt = f"""
        Actúa como un ingeniero senior especialista en lubricación,
        análisis de aceite y confiabilidad industrial.

        Analiza la siguiente información:

        {contexto}

        Entrega:
        - diagnóstico técnico
        - riesgo operacional
        - posible causa raíz
        - recomendación de mantenimiento

        Máximo 120 palabras.
        """

        response = model.generate_content(
            str(prompt)
        )

        return response.text

    except Exception as e:

        return f"Error IA: {e}"

def normalizar(serie):

    if serie.max() == serie.min():

        return pd.Series(
            [0] * len(serie),
            index=serie.index
        )

    return (
        (serie - serie.min()) /
        (serie.max() - serie.min())
    )

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("⚙️ Configuración")

uploaded_file = st.sidebar.file_uploader(
    "Cargar Archivo",
    type=["csv", "xlsx"]
)

# =====================================================
# MAIN
# =====================================================

st.title("🚜 Maintenance Intelligence Center")

st.caption(
    "CSI / Copec • Analítica Inteligente de Lubricación y Confiabilidad"
)

if uploaded_file:

    try:

        df = load_data(uploaded_file)

        if df.empty:

            st.warning("Archivo sin datos")
            st.stop()

        # =====================================================
        # COLUMNAS BASE
        # =====================================================

        columnas_base = [
            "HIERRO",
            "COBRE",
            "PLOMO",
            "ALUMINIO",
            "SILICIO",
            "SODIO"
        ]

        for col in columnas_base:

            if col not in df.columns:

                df[col] = 0

        # =====================================================
        # FILTRO FAENA
        # =====================================================

        if "NOMBRE_FAENA" in df.columns:

            faenas = ["Todas"] + sorted(
                df["NOMBRE_FAENA"]
                .dropna()
                .astype(str)
                .unique()
            )

            faena_sel = st.sidebar.selectbox(
                "Seleccionar Faena",
                faenas
            )

            if faena_sel != "Todas":

                df = df[
                    df["NOMBRE_FAENA"] == faena_sel
                ]

        # =====================================================
        # FILTRO FECHA
        # =====================================================

        if (
            "FECHA_MUESTRA" in df.columns and
            not df["FECHA_MUESTRA"].isna().all()
        ):

            min_date = df["FECHA_MUESTRA"].min().date()
            max_date = df["FECHA_MUESTRA"].max().date()

            rango = st.sidebar.date_input(
                "Rango Fechas",
                (min_date, max_date)
            )

            if len(rango) == 2:

                start, end = rango

                df = df[
                    (
                        df["FECHA_MUESTRA"].dt.date >= start
                    ) &
                    (
                        df["FECHA_MUESTRA"].dt.date <= end
                    )
                ]

        # =====================================================
        # KPIs
        # =====================================================

        total = len(df)

        if "ESTADO" in df.columns:

            alertas = len(
                df[df["ESTADO"] == "ALERTA"]
            )

            precaucion = len(
                df[df["ESTADO"] == "PRECAUCION"]
            )

        else:

            alertas = 0
            precaucion = 0

        criticidad = round(
            (alertas / total) * 100,
            1
        ) if total > 0 else 0

        salud = round(
            100 - criticidad,
            1
        )

        # =====================================================
        # ÍNDICES
        # =====================================================

        df["IDC"] = (
            df["HIERRO"] * 0.4 +
            df["COBRE"] * 0.3 +
            df["PLOMO"] * 0.2 +
            df["ALUMINIO"] * 0.1
        )

        df["IC"] = (
            df["SILICIO"] +
            df["SODIO"]
        )

        # =====================================================
        # SCORE RIESGO
        # =====================================================

        df["RIESGO_SCORE"] = (

            normalizar(df["HIERRO"]) * 0.35 +

            normalizar(df["SILICIO"]) * 0.25 +

            normalizar(df["COBRE"]) * 0.20 +

            normalizar(df["IDC"]) * 0.20

        ) * 100

        # =====================================================
        # KPIs VISUALES
        # =====================================================

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "🚨 Criticidad",
                f"{criticidad}%",
                f"{alertas} alertas"
            )

        with c2:

            st.metric(
                "🟡 Precaución",
                precaucion
            )

        with c3:

            st.metric(
                "🟢 Salud General",
                f"{salud}%"
            )

        with c4:

            st.metric(
                "⚠️ Riesgo Medio",
                round(
                    df["RIESGO_SCORE"].mean(),
                    1
                )
            )

        # =====================================================
        # RESUMEN IA
        # =====================================================

        st.markdown("---")

        st.subheader("🧠 Executive AI Summary")

        contexto_general = f"""
        Total muestras: {total}
        Alertas: {alertas}
        Precaución: {precaucion}
        Riesgo promedio: {round(df['RIESGO_SCORE'].mean(),1)}
        """

        st.markdown(
            f"""
            <div class='ia-box'>
            {generar_insight_ia(contexto_general)}
            </div>
            """,
            unsafe_allow_html=True
        )

        # =====================================================
        # TOP EQUIPOS
        # =====================================================

        if "EQUIPO" in df.columns:

            st.markdown("---")

            st.subheader(
                "🚨 Ranking Inteligente de Equipos"
            )

            top_eq = df.groupby("EQUIPO").agg({

                "RIESGO_SCORE": "mean",
                "HIERRO": "mean",
                "SILICIO": "mean",
                "IDC": "mean"

            }).reset_index()

            top_eq = top_eq.sort_values(
                by="RIESGO_SCORE",
                ascending=False
            ).head(15)

            fig_top = px.bar(
                top_eq,
                x="RIESGO_SCORE",
                y="EQUIPO",
                orientation="h",
                color="RIESGO_SCORE",
                text_auto=".1f",
                title="Top Equipos Críticos"
            )

            st.plotly_chart(
                fig_top,
                use_container_width=True
            )

            with st.expander("🧠 Insight IA"):

                st.write(
                    generar_insight_ia(
                        top_eq.to_string()
                    )
                )

        # =====================================================
        # TENDENCIA TEMPORAL
        # =====================================================

        if (
            "FECHA_MUESTRA" in df.columns and
            "HIERRO" in df.columns
        ):

            st.markdown("---")

            st.subheader(
                "📈 Tendencia Temporal de Desgaste"
            )

            trend = df.groupby(
                "FECHA_MUESTRA"
            )["HIERRO"].mean().reset_index()

            fig_line = px.line(
                trend,
                x="FECHA_MUESTRA",
                y="HIERRO",
                markers=True,
                title="Tendencia Hierro Promedio"
            )

            st.plotly_chart(
                fig_line,
                use_container_width=True
            )

            with st.expander("🧠 Insight IA"):

                st.write(
                    generar_insight_ia(
                        trend.tail(10).to_string()
                    )
                )

        # =====================================================
        # CONTAMINACIÓN
        # =====================================================

        if (
            "SILICIO" in df.columns and
            "SODIO" in df.columns
        ):

            st.markdown("---")

            st.subheader(
                "⚠️ Análisis de Contaminación"
            )

            fig_cont = px.scatter(
                df,
                x="SILICIO",
                y="SODIO",
                size="HIERRO",
                color="RIESGO_SCORE",
                hover_name=(
                    "EQUIPO"
                    if "EQUIPO" in df.columns
                    else None
                ),
                title="Silicio vs Sodio"
            )

            st.plotly_chart(
                fig_cont,
                use_container_width=True
            )

            with st.expander("🧠 Insight IA"):

                st.write(
                    generar_insight_ia(
                        df[
                            [
                                "SILICIO",
                                "SODIO",
                                "HIERRO"
                            ]
                        ]
                        .describe()
                        .to_string()
                    )
                )

        # =====================================================
        # HEATMAP
        # =====================================================

        metales = [
            "HIERRO",
            "COBRE",
            "PLOMO",
            "ALUMINIO"
        ]

        metales_ok = [
            m for m in metales
            if m in df.columns
        ]

        if (
            "EQUIPO" in df.columns and
            len(metales_ok) > 0
        ):

            st.markdown("---")

            st.subheader(
                "🔥 Heatmap de Desgaste"
            )

            heat = df.groupby(
                "EQUIPO"
            )[metales_ok].mean().head(20)

            fig_heat = px.imshow(
                heat,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Reds"
            )

            st.plotly_chart(
                fig_heat,
                use_container_width=True
            )

        # =====================================================
        # DETECCIÓN ESTADÍSTICA DE ANOMALÍAS
        # =====================================================

        st.markdown("---")

        st.subheader(
            "🤖 Detección Inteligente de Anomalías"
        )

        try:

            variables = [
                "HIERRO",
                "COBRE",
                "SILICIO",
                "IDC"
            ]

            variables = [
                v for v in variables
                if v in df.columns
            ]

            if len(variables) > 0:

                df["ANOMALIA_SCORE"] = 0

                for var in variables:

                    media = df[var].mean()
                    std = df[var].std()

                    if std > 0:

                        zscore = (
                            (
                                df[var] - media
                            ) / std
                        ).abs()

                        df["ANOMALIA_SCORE"] += zscore

                anom = df[
                    df["ANOMALIA_SCORE"] > 8
                ]

                st.write(
                    f"Se detectaron {len(anom)} anomalías potenciales"
                )

                if len(anom) > 0:

                    cols_show = [
                        c for c in [
                            "EQUIPO",
                            "HIERRO",
                            "COBRE",
                            "SILICIO",
                            "RIESGO_SCORE",
                            "ANOMALIA_SCORE"
                        ]
                        if c in anom.columns
                    ]

                    st.dataframe(
                        anom[cols_show]
                        .sort_values(
                            by="ANOMALIA_SCORE",
                            ascending=False
                        ),
                        use_container_width=True
                    )

        except Exception as e:

            st.warning(
                f"Error detección anomalías: {e}"
            )

        # =====================================================
        # MATRIZ OPERACIONAL
        # =====================================================

        st.markdown("---")

        st.subheader(
            "📋 Matriz Operacional Inteligente"
        )

        cols_show = [
            "EQUIPO",
            "COMPONENTE",
            "ESTADO",
            "HIERRO",
            "SILICIO",
            "IDC",
            "RIESGO_SCORE"
        ]

        cols_show = [
            c for c in cols_show
            if c in df.columns
        ]

        tabla = df[cols_show].sort_values(
            by="RIESGO_SCORE",
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

        st.subheader(
            "🧠 Recomendaciones Inteligentes"
        )

        recomendaciones = generar_insight_ia(
            tabla.head(20).to_string()
        )

        st.markdown(
            f"""
            <div class='alert-box'>
            {recomendaciones}
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:

        st.error(f"Error general: {e}")

else:

    st.info(
        "👋 Carga un archivo CSV o XLSX para comenzar"
    )




