import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ============================
# Configuración inicial
# ============================
EXCEL_PATH = "Inversión sistema fotovoltaico.xlsx"
EXCEL_SHEET = "Total"
INVERSION_INICIAL = 109000
LOGO_PATH = "logo_solar.png"

# ============================
# Cargar y preparar los datos
# ============================
def load_data_from_excel(file_path, sheet_name):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df.columns = [col.strip() for col in df.columns]
        df['Ahorro Total'] = df['Ahorro Total'].replace("[\\$,]", "", regex=True).astype(float)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

df = load_data_from_excel(EXCEL_PATH, EXCEL_SHEET)

# Ajustar nombre de columna según sea necesario
periodo_col = "Periodos" if "Periodos" in df.columns else "Periodo"
origen_col = "Origen" if "Origen" in df.columns else None

# ============================
# Configurar la página principal
# ============================
st.set_page_config(
    page_title="Monitoreo Solar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================
# Sidebar - Logo y filtros
# ============================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_column_width=True)
    
    st.markdown("## Filtros")
    
    with st.expander("Filtros"):
        opciones_periodo = ["Seleccionar todo"] + list(df[periodo_col].unique())
        seleccion_periodo = st.multiselect('Selecciona periodos', opciones_periodo, default=["Seleccionar todo"])
        
        df_filtrado = df.copy()
        if seleccion_periodo and "Seleccionar todo" not in seleccion_periodo:
            df_filtrado = df_filtrado[df_filtrado[periodo_col].isin(seleccion_periodo)]
        
        if origen_col:
            opciones_origen = ["Seleccionar todo"] + list(df[origen_col].unique())
            seleccion_origen = st.multiselect('Selecciona origen', opciones_origen, default=["Seleccionar todo"])
            if seleccion_origen and "Seleccionar todo" not in seleccion_origen:
                df_filtrado = df_filtrado[df_filtrado[origen_col].isin(seleccion_origen)]
        
        opciones_nivel = ["Seleccionar todo"] + ['Básico', 'Intermedio 1', 'Intermedio 2', 'Excedente']
        seleccion_nivel = st.multiselect('Selecciona nivel de cobro', opciones_nivel, default=["Seleccionar todo"])
        if seleccion_nivel and "Seleccionar todo" not in seleccion_nivel:
            columnas_nivel = [col for col in df.columns if any(n in col for n in seleccion_nivel)]
            df_filtrado = df_filtrado[[periodo_col] + ([origen_col] if origen_col else []) + columnas_nivel]

# ============================
# Análisis clave
# ============================
st.title("Monitoreo del Ahorro y Recuperación de Inversión")

# Cálculo de métricas principales
ahorro_acumulado = df_filtrado["Ahorro Total"].sum()
pendiente_recuperar = INVERSION_INICIAL - ahorro_acumulado
progreso = (ahorro_acumulado / INVERSION_INICIAL) * 100 if INVERSION_INICIAL > 0 else 0
meses_faltantes = (pendiente_recuperar / (ahorro_acumulado / len(df_filtrado))) if ahorro_acumulado > 0 else 0
ahorro_promedio_mensual = ahorro_acumulado / len(df_filtrado) if len(df_filtrado) > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Ahorro Acumulado", f"${ahorro_acumulado:,.2f}")
col2.metric("Pendiente para Recuperar", f"${pendiente_recuperar:,.2f}")
col3.metric("Porcentaje Recuperado", f"{progreso:.2f}%")
col4.metric("Meses Estimados Restantes", f"{meses_faltantes:.1f} meses")
col5.metric("Ahorro Promedio por Mes", f"${ahorro_promedio_mensual:,.2f}")

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        div[data-testid="stMetric"] > div:first-child {
            font-weight: bold;
            font-size: 18px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================
# Gráficos de Análisis
# ============================
st.subheader("Tendencia del Ahorro Acumulado")
fig_ahorro = px.area(
    df_filtrado, x=periodo_col, y="Ahorro Total",
    title="Evolución del Ahorro por Periodo",
    markers=True, color_discrete_sequence=["#2ECC71"]
)
st.plotly_chart(fig_ahorro, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Tiempo Estimado de Recuperación")
    fig_dona = px.pie(
        names=["Ahorro Total", "Restante"],
        values=[ahorro_acumulado, max(0, pendiente_recuperar)],
        title="Progreso de Recuperación",
        hole=0.5,
        color_discrete_sequence=["#2ECC71", "#E74C3C"]
    )
    st.plotly_chart(fig_dona, use_container_width=True)

with col2:
    st.subheader("Distribución Total de Costos por Nivel de Cobro")
    df_totales = df_filtrado[["Básico Solar", "Intermedio 1 Solar", "Intermedio 2 Solar", "Excedente Solar", 
                              "Básico CFE", "Intermedio 1 CFE", "Intermedio 2 CFE", "Excedente CFE"]].sum().reset_index()
    df_totales.columns = ["Nivel de Cobro", "Costo Total"]
    fig_treemap = px.treemap(
        df_totales, path=["Nivel de Cobro"], values="Costo Total",
        title="Proporción Total de Costos por Nivel de Cobro",
        color="Costo Total", color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

# ============================
# Nuevo Enfoque: Comparación entre Consumo Real y Estimado
# ============================
st.subheader("Comparación de Consumo Real vs Estimado")
fig_comparativo = px.bar(
    df_filtrado, x=periodo_col, y=["Total de recibo Solar", "Subtotal CFE"],
    barmode="group", title="Consumo Real (Verde) vs Estimado (Amarillo)",
    color_discrete_map={"Total de recibo Solar": "#2ECC71", "Subtotal CFE": "#F4D03F"}
)
st.plotly_chart(fig_comparativo, use_container_width=True)

# ============================
# Periodo con Mayor Ahorro
# ============================
st.subheader("Periodo con Mayor Ahorro")
mes_max_ahorro = df_filtrado.loc[df_filtrado['Ahorro Total'].idxmax()]
st.write(f"El mes con mayor ahorro fue **{mes_max_ahorro[periodo_col]}** con un ahorro de **${mes_max_ahorro['Ahorro Total']:,.2f}**.")

# ============================
# Tabla resumen
# ============================
st.subheader("Tabla Resumen de Datos Filtrados")
# Aplicar formato solo a columnas numéricas
numeric_cols = df_filtrado.select_dtypes(include=['number']).columns
st.dataframe(df_filtrado.style.format({col: "${:,.2f}" for col in numeric_cols}))

st.markdown("---")
st.write("_Monitoreo de paneles solares © 2024_", unsafe_allow_html=True)
