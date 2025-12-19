
import streamlit as st
import pandas as pd
import plotly.express as px
from google_sheets_client import GoogleSheetsClient
from fpdf import FPDF
from datetime import datetime
import time

# Custom Modules
from profesionales_component import render_professionals_tab
from rutas_utils import create_route_pdf, generate_all_routes_zip

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Gestión Terapéutica",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
<style>
    /* Main Background & Colors */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E9ECEF;
    }
    
    /* Headers */
    h1 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1A1A1A;
        font-weight: 700;
        font-size: 2.2rem !important;
        padding-bottom: 1rem;
    }
    h2, h3 {
        color: #2C3E50;
        font-weight: 600;
    }
    
    /* Cards/Metrics */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E9ECEF;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# --- UTILS ---

class BasePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Sistema de Gestión Terapéutica', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_executive_pdf(df_filtered, kpi_data):
    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # KPIs
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Resumen Ejecutivo", 0, 1)
    pdf.set_font("Arial", size=11)
    for key, value in kpi_data.items():
        pdf.cell(0, 8, f"{key}: {value}", 0, 1)
    pdf.ln(10)
    
    # EPS Summary
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Distribución por EPS", 0, 1)
    pdf.set_font("Arial", size=10)
    if 'EPS' in df_filtered.columns:
        eps_counts = df_filtered['EPS'].value_counts().head(10)
        pdf.cell(120, 8, "EPS", 1)
        pdf.cell(40, 8, "Pacientes", 1)
        pdf.ln()
        for eps, count in eps_counts.items():
            eps_str = str(eps)[:50].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(120, 8, eps_str, 1)
            pdf.cell(40, 8, str(count), 1)
            pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'replace')

def create_novedades_pdf(df_filtered):
    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "BITÁCORA DE NOVEDADES", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    if 'NOVEDADES' not in df_filtered.columns:
        return None
    df_novedades = df_filtered[df_filtered['NOVEDADES'].astype(str).str.strip() != '']
    for index, row in df_novedades.iterrows():
        name = f"{row.get('APELLIDOS', '')} {row.get('NOMBRE', '')}"
        name = name.encode('latin-1', 'replace').decode('latin-1')
        prof = str(row.get('PROFESIONAL', 'N/A')).encode('latin-1', 'replace').decode('latin-1')
        nov = str(row.get('NOVEDADES', '')).encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"PACIENTE: {name} (Prof: {prof})", 0, 1)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(0, 5, f"OBSERVACIÓN: {nov}")
        pdf.ln(3)
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1', 'replace')

@st.cache_data(ttl=300)
def load_data(sheet_url):
    client = GoogleSheetsClient('credentials.json')
    data = client.get_sheet_data(sheet_url)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def render_sidebar_header():
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 10px;">
            <h2 style="color: #4B4B4B;">🏥 Gestión</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- MODULES ---

def module_dashboard(df):
    st.markdown("## 📊 Dashboard Analítico")
    st.markdown("Resumen general del estado de la operación.")
    
    # Context Filters for Dashboard
    with st.expander("🔎 Filtros de Visualización", expanded=False):
        c1, c2 = st.columns(2)
        mun_opt = ['Todos'] + sorted(list(df['MUNICIPIO'].unique())) if 'MUNICIPIO' in df.columns else ['Todos']
        sel_mun = c1.selectbox("Filtrar por Municipio", mun_opt)
        
        eps_opt = ['Todas'] + sorted(list(df['EPS'].unique())) if 'EPS' in df.columns else ['Todas']
        sel_eps = c2.selectbox("Filtrar por EPS", eps_opt)
        
    # Apply local filters
    df_view = df.copy()
    if sel_mun != 'Todos':
        df_view = df_view[df_view['MUNICIPIO'] == sel_mun]
    if sel_eps != 'Todas':
        df_view = df_view[df_view['EPS'] == sel_eps]
        
    # KPIs
    st.markdown("### Métricas Clave")
    k1, k2, k3, k4 = st.columns(4)
    
    total_patients = len(df_view)
    total_sessions = df_view['CANTIDAD'].sum() if 'CANTIDAD' in df_view.columns else 0
    active_profs = df_view['PROFESIONAL'].nunique() if 'PROFESIONAL' in df_view.columns else 0
    municipalities = df_view['MUNICIPIO'].nunique() if 'MUNICIPIO' in df_view.columns else 0
    
    k1.metric("Pacientes Activos", total_patients, delta_color="normal")
    k2.metric("Sesiones Programadas", f"{int(total_sessions)}")
    k3.metric("Profesionales", active_profs)
    k4.metric("Cobertura (Municipios)", municipalities)
    
    st.markdown("---")
    
    # Charts
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        st.subheader("Distribución por EPS")
        if 'EPS' in df_view.columns:
            eps_data = df_view['EPS'].value_counts().reset_index()
            eps_data.columns = ['EPS', 'Pacientes']
            fig_eps = px.bar(eps_data, x='EPS', y='Pacientes', color='Pacientes', color_continuous_scale='Blues')
            fig_eps.update_layout(xaxis_title="", yaxis_title="Nº Pacientes")
            st.plotly_chart(fig_eps, use_container_width=True)
            
    with c_chart2:
        st.subheader("Tipos de Terapia")
        if 'TIPO DE TERAPIAS' in df_view.columns:
            therapy_data = df_view['TIPO DE TERAPIAS'].value_counts().reset_index()
            therapy_data.columns = ['Tipo', 'Cantidad']
            fig_pie = px.pie(therapy_data, values='Cantidad', names='Tipo', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    # Executive Report Download
    st.markdown("### 📥 Descargas Rapidas")
    if st.button("Generar PDF Resumen Ejecutivo"):
        kpi_data = {
            "Total Pacientes": total_patients,
            "Total Sesiones": int(total_sessions),
            "Profesionales": active_profs,
            "Municipios": municipalities
        }
        pdf_bytes = create_executive_pdf(df_view, kpi_data)
        st.download_button(
            "⬇️ Descargar Reporte PDF",
            data=pdf_bytes,
            file_name="resumen_ejecutivo.pdf",
            mime="application/pdf"
        )

def module_rutas(df):
    st.markdown("## 🚚 Gestión de Rutas y Logística")
    st.markdown("Generación de hojas de ruta detalladas para los profesionales.")
    
    if 'PROFESIONAL' not in df.columns:
        st.error("No se encontró la columna 'PROFESIONAL' en los datos.")
        return

    tab1, tab2 = st.tabs(["👤 Generación Individual", "📦 Generación Masiva (ZIP)"])
    
    profs_available = sorted(list(df['PROFESIONAL'].unique()))
    
    with tab1:
        # Selection Column
        c_sel, c_view = st.columns([1, 3])
        
        with c_sel:
            st.markdown("### Seleccionar")
            selected_prof = st.selectbox("Profesional:", profs_available)
            
            if selected_prof:
                df_prof = df[df['PROFESIONAL'] == selected_prof]
                
                # Metric 1: Total Patients
                st.metric("Pacientes Asignados", len(df_prof))
                
                # Metric 2: Total Sessions
                sessions = df_prof['CANTIDAD'].sum() if 'CANTIDAD' in df_prof.columns else 0
                st.metric("Total Sesiones", int(sessions))
                
                st.divider()
                st.info("Descargue la hoja de ruta lista para imprimir.")
                
                # Pre-generate PDF for direct download (Single Click)
                pdf_bytes = create_route_pdf(df_prof, selected_prof)
                
                st.download_button(
                    label=f"⬇️ Descargar Ruta PDF",
                    data=pdf_bytes,
                    file_name=f"Ruta_{selected_prof.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

        with c_view:
            if selected_prof:
                st.markdown(f"### 📊 Estadísticas: {selected_prof}")
                
                # Charts
                row1_1, row1_2 = st.columns(2)
                
                with row1_1:
                    st.markdown("**Distribución por EPS**")
                    if 'EPS' in df_prof.columns:
                        eps_counts = df_prof['EPS'].value_counts().reset_index()
                        eps_counts.columns = ['EPS', 'Pacientes']
                        fig_eps = px.pie(eps_counts, values='Pacientes', names='EPS', hole=0.4)
                        fig_eps.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                        st.plotly_chart(fig_eps, use_container_width=True)
                        
                with row1_2:
                    st.markdown("**Tipos de Usuario**")
                    if 'TIPO DE USUARIO' in df_prof.columns:
                        type_counts = df_prof['TIPO DE USUARIO'].value_counts().reset_index()
                        type_counts.columns = ['Tipo', 'Pacientes']
                        fig_type = px.bar(type_counts, x='Tipo', y='Pacientes', color='Tipo')
                        fig_type.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=False)
                        st.plotly_chart(fig_type, use_container_width=True)
                
                st.markdown("**Detalle de Pacientes**")
                st.dataframe(
                    df_prof[['NOMBRE', 'APELLIDOS', 'MUNICIPIO', 'EPS', 'TIPO DE USUARIO', 'CANTIDAD']], 
                    use_container_width=True, 
                    hide_index=True
                )

    with tab2:
        st.warning("⚠️ Esta acción generará un archivo ZIP conteniendo un PDF individual para CADA profesional activo.")
        col_zip1, col_zip2 = st.columns([2, 1])
        with col_zip1:
            st.metric("Total Profesionales a Procesar", len(profs_available))
        
        with col_zip2:
            st.write("") # Spacer
            if st.button("🚀 Generar ZIP Completo"):
                with st.spinner("Procesando rutas... por favor espere."):
                    zip_bytes = generate_all_routes_zip(df)
                    if zip_bytes:
                        st.balloons()
                        st.success("¡Paquete de rutas listo!")
                        st.download_button(
                            "📥 Descargar ZIP Rutas",
                            data=zip_bytes,
                            file_name=f"Rutas_Completas_{datetime.now().strftime('%Y%m%d')}.zip",
                            mime="application/zip",
                            type="primary"
                        )
                    else:
                        st.error("Error al generar el ZIP.")

def module_data_explorer(df):
    st.markdown("## 🔎 Explorador de Datos y Reportes")
    st.markdown("Consulta la base de datos completa y genera reportes específicos.")
    
    # Filters
    with st.container():
        st.markdown("#### Filtros")
        c1, c2, c3, c4 = st.columns(4)
        
        mun_opt = ['Todos'] + sorted(list(df['MUNICIPIO'].unique())) if 'MUNICIPIO' in df.columns else ['Todos']
        sel_mun = c1.selectbox("Municipio", mun_opt, key="de_mun")
        
        eps_opt = ['Todas'] + sorted(list(df['EPS'].unique())) if 'EPS' in df.columns else ['Todas']
        sel_eps = c2.selectbox("EPS", eps_opt, key="de_eps")
        
        type_opt = sorted(list(df['TIPO DE USUARIO'].unique())) if 'TIPO DE USUARIO' in df.columns else []
        sel_type = c3.multiselect("Tipo Usuario", type_opt, key="de_type")

        # Filter Logic
        df_filtered = df.copy()
        if sel_mun != 'Todos':
            df_filtered = df_filtered[df_filtered['MUNICIPIO'] == sel_mun]
        if sel_eps != 'Todas':
            df_filtered = df_filtered[df_filtered['EPS'] == sel_eps]
        if sel_type:
            df_filtered = df_filtered[df_filtered['TIPO DE USUARIO'].isin(sel_type)]
            
        c4.metric("Registros", len(df_filtered))

    st.markdown("---")
    
    # Table
    st.dataframe(df_filtered, use_container_width=True, height=400)
    
    # Downloads Section
    st.subheader("📂 Centro de Descargas")
    
    c_down1, c_down2, c_down3 = st.columns(3)
    
    with c_down1:
        st.markdown("**1. Datos Filtrados (CSV)**")
        st.caption("Descarga la tabla visible arriba en formato Excel/CSV.")
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", csv, "data_filtrada.csv", "text/csv")
        
    with c_down2:
        st.markdown("**2. Reporte de Facturación**")
        st.caption("Agrupado por EPS y Tipo de Servicio.")
        if 'EPS' in df_filtered.columns and 'CANTIDAD' in df_filtered.columns and 'TIPO DE TERAPIAS' in df_filtered.columns:
            billing_df = df_filtered.groupby(['EPS', 'TIPO DE TERAPIAS'])['CANTIDAD'].sum().reset_index()
            csv_bill = billing_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Descargar Facturación", csv_bill, "facturacion.csv", "text/csv")
        else:
            st.warning("Faltan columnas para facturación.")

    with c_down3:
        st.markdown("**3. Bitácora de Novedades**")
        st.caption("PDF con observaciones registradas.")
        if st.button("Generar PDF Novedades"):
            pdf_nov = create_novedades_pdf(df_filtered)
            if pdf_nov:
                st.download_button("⬇️ Descargar PDF", pdf_nov, "novedades.pdf", "application/pdf")
            else:
                st.info("Sin novedades.")

# --- MAIN ---

def main():
    render_sidebar_header()
    
    # Sidebar Input
    st.sidebar.markdown("### ⚙️ Origen de Datos")
    sheet_input = st.sidebar.text_input(
        "Nombre o URL:",
        value="",
        placeholder="Ej: 01 INGRESOS...",
        help="Ingrese el nombre exacto del archivo en Drive o la URL."
    )
    
    if not sheet_input:
        st.info("👋 **Bienvenido al Sistema de Gestión Terapéutica**")
        st.markdown("""
        Para comenzar, por favor ingrese el **nombre del archivo** o la **URL** de Google Sheets en la barra lateral izquierda.
        
        **Módulos Disponibles:**
        - 📊 **Dashboard Analítico:** Estadísticas y visión general.
        - 🚚 **Gestión de Rutas:** Generación de hojas de ruta (Individual/Masiva).
        - 🔎 **Explorador de Datos:** Consultas detalladas y reportes.
        """)
        return

    # Load Data
    with st.sidebar:
        with st.spinner("Cargando datos..."):
            try:
                df = load_data(sheet_input)
            except Exception as e:
                st.error(f"Error: {e}")
                return

    if df.empty:
        st.error(f"No se pudieron cargar datos de: '{sheet_input}'")
        return
        
    # Preprocessing
    if 'CANTIDAD' in df.columns:
        df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce').fillna(0)

    # Sidebar Navigation using Radio for clear tabs
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Navegación")
    
    options = ["Dashboard Analítico", "Gestión de Rutas", "Explorador de Datos"]
    selection = st.sidebar.radio("Ir a:", options, label_visibility="collapsed")
    
    st.sidebar.info(f"📁 Archivo: {sheet_input[:20]}...")

    # Routing
    if selection == "Dashboard Analítico":
        module_dashboard(df)
    elif selection == "Gestión de Rutas":
        module_rutas(df)
    elif selection == "Explorador de Datos":
        module_data_explorer(df)

if __name__ == "__main__":
    main()
