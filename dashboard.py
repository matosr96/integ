
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
    """Genera un reporte ejecutivo completo y profesional"""
    pdf = BasePDF()
    
    # ==================== PORTADA ====================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 15, "REPORTE APOYO TERAPEUTICO", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Periodo: {datetime.now().strftime('%B %Y')}", 0, 1, 'C')
    pdf.cell(0, 8, f"Fecha de generacion: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
    pdf.ln(60)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, "Documento Confidencial", 0, 1, 'C')
    pdf.cell(0, 6, "Sistema de Gestion Terapeutica", 0, 1, 'C')
    
    # ==================== RESUMEN EJECUTIVO ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "1. RESUMEN EJECUTIVO", 0, 1)
    pdf.ln(3)
    
    # KPIs Principales en cajas
    pdf.set_font("Arial", 'B', 11)
    total_patients = len(df_filtered)
    total_sessions = df_filtered['CANTIDAD'].sum() if 'CANTIDAD' in df_filtered.columns else 0
    active_profs = df_filtered['PROFESIONAL'].nunique() if 'PROFESIONAL' in df_filtered.columns else 0
    municipalities = df_filtered['MUNICIPIO'].nunique() if 'MUNICIPIO' in df_filtered.columns else 0
    
    # Fila 1 de KPIs
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(90, 10, "Total Pacientes Activos", 1, 0, 'L', 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(90, 10, f"{total_patients:,}", 1, 1, 'C')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, "Sesiones Programadas", 1, 0, 'L', 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(90, 10, f"{int(total_sessions):,}", 1, 1, 'C')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, "Profesionales Activos", 1, 0, 'L', 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(90, 10, f"{active_profs}", 1, 1, 'C')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, "Cobertura Geografica", 1, 0, 'L', 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(90, 10, f"{municipalities} municipios", 1, 1, 'C')
    
    pdf.ln(5)
    
    # Promedio de sesiones por paciente
    avg_sessions = total_sessions / total_patients if total_patients > 0 else 0
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, "Promedio Sesiones/Paciente", 1, 0, 'L', 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(90, 10, f"{avg_sessions:.1f}", 1, 1, 'C')
    
    # Promedio de pacientes por profesional
    avg_patients_prof = total_patients / active_profs if active_profs > 0 else 0
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, "Promedio Pacientes/Profesional", 1, 0, 'L', 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(90, 10, f"{avg_patients_prof:.1f}", 1, 1, 'C')
    
    # ==================== DISTRIBUCION POR EPS ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "2. ANALISIS POR EPS", 0, 1)
    pdf.ln(3)
    
    if 'EPS' in df_filtered.columns:
        eps_counts = df_filtered['EPS'].value_counts()
        eps_sessions = df_filtered.groupby('EPS')['CANTIDAD'].sum() if 'CANTIDAD' in df_filtered.columns else None
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(80, 8, "EPS", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Pacientes", 1, 0, 'C', 1)
        pdf.cell(25, 8, "%", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Sesiones", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        for eps in eps_counts.index[:15]:  # Top 15
            eps_str = str(eps)[:35].encode('latin-1', 'replace').decode('latin-1')
            count = eps_counts[eps]
            percentage = (count / total_patients * 100) if total_patients > 0 else 0
            sessions = int(eps_sessions[eps]) if eps_sessions is not None else 0
            
            pdf.cell(80, 7, eps_str, 1, 0, 'L')
            pdf.cell(30, 7, f"{count:,}", 1, 0, 'C')
            pdf.cell(25, 7, f"{percentage:.1f}%", 1, 0, 'C')
            pdf.cell(35, 7, f"{sessions:,}", 1, 1, 'C')
        
        # Total row
        pdf.set_font("Arial", 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(80, 7, "TOTAL", 1, 0, 'L', 1)
        pdf.cell(30, 7, f"{total_patients:,}", 1, 0, 'C', 1)
        pdf.cell(25, 7, "100%", 1, 0, 'C', 1)
        pdf.cell(35, 7, f"{int(total_sessions):,}", 1, 1, 'C', 1)
    
    # ==================== TIPOS DE USUARIO ====================
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. DISTRIBUCION POR TIPO DE USUARIO", 0, 1)
    pdf.ln(3)
    
    if 'TIPO DE USUARIO' in df_filtered.columns:
        # Normalizar datos para evitar duplicados
        df_usertype = df_filtered.copy()
        df_usertype['TIPO DE USUARIO'] = df_usertype['TIPO DE USUARIO'].astype(str).str.strip().str.upper()
        
        type_counts = df_usertype['TIPO DE USUARIO'].value_counts()
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(100, 8, "Tipo de Usuario", 1, 0, 'C', 1)
        pdf.cell(40, 8, "Cantidad", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Porcentaje", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 10)
        for user_type, count in type_counts.items():
            type_str = str(user_type).encode('latin-1', 'replace').decode('latin-1')
            percentage = (count / total_patients * 100) if total_patients > 0 else 0
            pdf.cell(100, 7, type_str, 1, 0, 'L')
            pdf.cell(40, 7, f"{count:,}", 1, 0, 'C')
            pdf.cell(30, 7, f"{percentage:.1f}%", 1, 1, 'C')
    
    # ==================== TIPOS DE TERAPIA ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "4. ANALISIS DE SERVICIOS", 0, 1)
    pdf.ln(3)
    
    if 'TIPO DE TERAPIAS' in df_filtered.columns:
        # Normalizar datos para evitar duplicados (espacios, mayúsculas)
        df_therapy = df_filtered.copy()
        df_therapy['TIPO DE TERAPIAS'] = df_therapy['TIPO DE TERAPIAS'].astype(str).str.strip().str.upper()
        
        therapy_counts = df_therapy['TIPO DE TERAPIAS'].value_counts()
        therapy_sessions = df_therapy.groupby('TIPO DE TERAPIAS')['CANTIDAD'].sum() if 'CANTIDAD' in df_therapy.columns else None
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(60, 8, "Tipo de Terapia", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Pacientes", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Sesiones", 1, 0, 'C', 1)
        pdf.cell(40, 8, "Promedio/Pac", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 10)
        for therapy in therapy_counts.index:
            therapy_str = str(therapy).encode('latin-1', 'replace').decode('latin-1')
            count = therapy_counts[therapy]
            sessions = int(therapy_sessions[therapy]) if therapy_sessions is not None else 0
            avg = sessions / count if count > 0 else 0
            
            pdf.cell(60, 7, therapy_str, 1, 0, 'L')
            pdf.cell(35, 7, f"{count:,}", 1, 0, 'C')
            pdf.cell(35, 7, f"{sessions:,}", 1, 0, 'C')
            pdf.cell(40, 7, f"{avg:.1f}", 1, 1, 'C')
    
    # ==================== CARGA POR PROFESIONAL ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "5. CARGA DE TRABAJO POR PROFESIONAL", 0, 1)
    pdf.ln(3)
    
    if 'PROFESIONAL' in df_filtered.columns and 'MUNICIPIO' in df_filtered.columns:
        # Obtener datos por profesional
        prof_data = []
        for prof in sorted(df_filtered['PROFESIONAL'].unique()):
            df_prof = df_filtered[df_filtered['PROFESIONAL'] == prof]
            count = len(df_prof)
            sessions = int(df_prof['CANTIDAD'].sum()) if 'CANTIDAD' in df_prof.columns else 0
            avg = sessions / count if count > 0 else 0
            # Obtener municipios únicos donde trabaja
            municipios = df_prof['MUNICIPIO'].unique()
            mun_str = ', '.join([str(m)[:20] for m in municipios[:3]])  # Max 3 municipios
            if len(municipios) > 3:
                mun_str += f" (+{len(municipios)-3})"
            
            prof_data.append({
                'nombre': str(prof),
                'pacientes': count,
                'sesiones': sessions,
                'promedio': avg,
                'municipios': mun_str
            })
        
        # Encabezados
        pdf.set_font("Arial", 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(55, 7, "Profesional", 1, 0, 'C', 1)
        pdf.cell(20, 7, "Pac.", 1, 0, 'C', 1)
        pdf.cell(20, 7, "Ses.", 1, 0, 'C', 1)
        pdf.cell(18, 7, "Prom", 1, 0, 'C', 1)
        pdf.cell(57, 7, "Municipios", 1, 1, 'C', 1)
        
        # Datos
        pdf.set_font("Arial", '', 7)
        for item in prof_data:
            prof_str = item['nombre'][:30].encode('latin-1', 'replace').decode('latin-1')
            mun_str = item['municipios'].encode('latin-1', 'replace').decode('latin-1')
            
            pdf.cell(55, 6, prof_str, 1, 0, 'L')
            pdf.cell(20, 6, f"{item['pacientes']}", 1, 0, 'C')
            pdf.cell(20, 6, f"{item['sesiones']}", 1, 0, 'C')
            pdf.cell(18, 6, f"{item['promedio']:.1f}", 1, 0, 'C')
            pdf.cell(57, 6, mun_str, 1, 1, 'L')
    
    # ==================== COBERTURA GEOGRAFICA ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "6. COBERTURA GEOGRAFICA", 0, 1)
    pdf.ln(3)
    
    if 'MUNICIPIO' in df_filtered.columns:
        mun_counts = df_filtered['MUNICIPIO'].value_counts()
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(100, 8, "Municipio", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Pacientes", 1, 0, 'C', 1)
        pdf.cell(35, 8, "Porcentaje", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        for mun in mun_counts.index[:15]:
            mun_str = str(mun)[:45].encode('latin-1', 'replace').decode('latin-1')
            count = mun_counts[mun]
            percentage = (count / total_patients * 100) if total_patients > 0 else 0
            
            pdf.cell(100, 7, mun_str, 1, 0, 'L')
            pdf.cell(35, 7, f"{count:,}", 1, 0, 'C')
            pdf.cell(35, 7, f"{percentage:.1f}%", 1, 1, 'C')
    
    # ==================== INDICADORES CLAVE ====================
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "7. INDICADORES DE GESTION", 0, 1)
    pdf.ln(3)
    
    # Calcular indicadores
    eps_count = df_filtered['EPS'].nunique() if 'EPS' in df_filtered.columns else 0
    therapy_types = df_filtered['TIPO DE TERAPIAS'].nunique() if 'TIPO DE TERAPIAS' in df_filtered.columns else 0
    
    pdf.set_font("Arial", '', 10)
    indicators = [
        ("Numero de EPS atendidas", eps_count),
        ("Tipos de terapia ofrecidos", therapy_types),
        ("Municipios con cobertura", municipalities),
        ("Tasa de ocupacion promedio", f"{(avg_patients_prof / 30 * 100):.1f}%"),
        ("Sesiones por profesional", f"{(total_sessions / active_profs):.1f}" if active_profs > 0 else "0"),
    ]
    
    pdf.set_fill_color(245, 245, 245)
    for indicator, value in indicators:
        pdf.cell(120, 8, indicator, 1, 0, 'L', 1)
        pdf.cell(50, 8, str(value), 1, 1, 'C')
    
    # ==================== CONCLUSIONES ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "8. CONCLUSIONES", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Puntos Destacados:", 0, 1)
    pdf.set_font("Arial", '', 10)
    
    # Generar conclusiones automáticas
    conclusions = []
    
    if total_patients > 0:
        conclusions.append(f"- Se estan atendiendo {total_patients:,} pacientes activos en el periodo.")
    
    if 'EPS' in df_filtered.columns:
        top_eps = df_filtered['EPS'].value_counts().index[0]
        top_eps_count = df_filtered['EPS'].value_counts().iloc[0]
        top_eps_pct = (top_eps_count / total_patients * 100)
        conclusions.append(f"- {top_eps} es la EPS con mayor volumen ({top_eps_count} pacientes, {top_eps_pct:.1f}%).")
    
    if active_profs > 0:
        conclusions.append(f"- El equipo cuenta con {active_profs} profesionales activos.")
        if avg_patients_prof > 25:
            conclusions.append(f"- ALERTA: Carga promedio de {avg_patients_prof:.1f} pacientes/profesional es alta.")
    
    if municipalities > 5:
        conclusions.append(f"- Amplia cobertura geografica en {municipalities} municipios.")
    
    for conclusion in conclusions:
        pdf.multi_cell(0, 6, conclusion.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(2)
    
    # Footer final
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 6, "--- Fin del Reporte Ejecutivo ---", 0, 1, 'C')
    
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
            # Normalizar datos para evitar duplicados
            df_therapy_chart = df_view.copy()
            df_therapy_chart['TIPO DE TERAPIAS'] = df_therapy_chart['TIPO DE TERAPIAS'].astype(str).str.strip().str.upper()
            
            therapy_data = df_therapy_chart['TIPO DE TERAPIAS'].value_counts().reset_index()
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
                # Filtrar solo pacientes con vigencia activa (tienen fecha de inicio)
                df_prof = df[df['PROFESIONAL'] == selected_prof].copy()
                
                # Filtrar pacientes con fecha de inicio válida
                if 'FECHA DE INGRESO' in df_prof.columns:
                    df_prof = df_prof[
                        (df_prof['FECHA DE INGRESO'].notna()) & 
                        (df_prof['FECHA DE INGRESO'].astype(str).str.strip() != '') &
                        (df_prof['FECHA DE INGRESO'].astype(str).str.lower() != 'nan')
                    ]
                
                # Metric 1: Total Patients (solo activos)
                st.metric("Pacientes Activos", len(df_prof))
                
                # Metric 2: Total Sessions
                sessions = df_prof['CANTIDAD'].sum() if 'CANTIDAD' in df_prof.columns else 0
                st.metric("Total Sesiones", int(sessions))
                
                st.divider()
                
                if len(df_prof) > 0:
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
                else:
                    st.warning("⚠️ Este profesional no tiene pacientes activos (con fecha de inicio).")

        with c_view:
            if selected_prof:
                # Usar el mismo df_prof filtrado
                df_prof_filtered = df[df['PROFESIONAL'] == selected_prof].copy()
                
                # Aplicar el mismo filtro de vigencia
                if 'FECHA DE INGRESO' in df_prof_filtered.columns:
                    df_prof_filtered = df_prof_filtered[
                        (df_prof_filtered['FECHA DE INGRESO'].notna()) & 
                        (df_prof_filtered['FECHA DE INGRESO'].astype(str).str.strip() != '') &
                        (df_prof_filtered['FECHA DE INGRESO'].astype(str).str.lower() != 'nan')
                    ]
                
                st.markdown(f"### 📊 Estadísticas: {selected_prof}")
                
                if len(df_prof_filtered) == 0:
                    st.info("No hay pacientes activos para mostrar estadísticas.")
                else:
                    # Charts
                    row1_1, row1_2 = st.columns(2)
                    
                    with row1_1:
                        st.markdown("**Distribución por EPS**")
                        if 'EPS' in df_prof_filtered.columns:
                            eps_counts = df_prof_filtered['EPS'].value_counts().reset_index()
                            eps_counts.columns = ['EPS', 'Pacientes']
                            fig_eps = px.pie(eps_counts, values='Pacientes', names='EPS', hole=0.4)
                            fig_eps.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                            st.plotly_chart(fig_eps, use_container_width=True)
                            
                    with row1_2:
                        st.markdown("**Tipos de Usuario**")
                        if 'TIPO DE USUARIO' in df_prof_filtered.columns:
                            type_counts = df_prof_filtered['TIPO DE USUARIO'].value_counts().reset_index()
                            type_counts.columns = ['Tipo', 'Pacientes']
                            fig_type = px.bar(type_counts, x='Tipo', y='Pacientes', color='Tipo')
                            fig_type.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=False)
                            st.plotly_chart(fig_type, use_container_width=True)
                    
                    st.markdown("**Detalle de Pacientes Activos**")
                    st.dataframe(
                        df_prof_filtered[['NOMBRE', 'APELLIDOS', 'MUNICIPIO', 'EPS', 'TIPO DE USUARIO', 'CANTIDAD']], 
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

def module_pending_events(df):
    st.markdown("## ⏳ Eventos Pendientes de Autorización")
    st.markdown("Pacientes sin fecha de inicio - En espera de autorización de EPS.")
    
    if 'FECHA DE INGRESO' not in df.columns:
        st.warning("No se encontró la columna 'FECHA DE INGRESO' en los datos.")
        return
    
    # Filtrar pacientes SIN fecha de inicio (eventos pendientes)
    df_pending = df[
        (df['FECHA DE INGRESO'].isna()) | 
        (df['FECHA DE INGRESO'].astype(str).str.strip() == '') |
        (df['FECHA DE INGRESO'].astype(str).str.lower() == 'nan')
    ].copy()
    
    if len(df_pending) == 0:
        st.success("✅ No hay eventos pendientes. Todos los pacientes tienen autorización.")
        return
    
    # KPIs
    st.markdown("### Resumen")
    c1, c2, c3, c4 = st.columns(4)
    
    total_pending = len(df_pending)
    pending_eps = df_pending['EPS'].nunique() if 'EPS' in df_pending.columns else 0
    pending_profs = df_pending['PROFESIONAL'].nunique() if 'PROFESIONAL' in df_pending.columns else 0
    pending_sessions = df_pending['CANTIDAD'].sum() if 'CANTIDAD' in df_pending.columns else 0
    
    c1.metric("Total Pendientes", total_pending)
    c2.metric("EPS Involucradas", pending_eps)
    c3.metric("Profesionales Afectados", pending_profs)
    c4.metric("Sesiones en Espera", int(pending_sessions))
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Lista Completa", "🏥 Por EPS", "👨‍⚕️ Por Profesional"])
    
    with tab1:
        st.markdown("#### Todos los Eventos Pendientes")
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            eps_filter = st.multiselect(
                "Filtrar por EPS:",
                options=sorted(df_pending['EPS'].unique()) if 'EPS' in df_pending.columns else [],
                key="pending_eps_filter"
            )
        with col_f2:
            prof_filter = st.multiselect(
                "Filtrar por Profesional:",
                options=sorted(df_pending['PROFESIONAL'].unique()) if 'PROFESIONAL' in df_pending.columns else [],
                key="pending_prof_filter"
            )
        
        # Apply filters
        df_display = df_pending.copy()
        if eps_filter:
            df_display = df_display[df_display['EPS'].isin(eps_filter)]
        if prof_filter:
            df_display = df_display[df_display['PROFESIONAL'].isin(prof_filter)]
        
        # Display table
        display_cols = ['NOMBRE', 'APELLIDOS', 'TIPO DE TERAPIAS', 'EPS', 'PROFESIONAL', 'TIPO DE USUARIO', 'MUNICIPIO', 'CANTIDAD']
        available_cols = [col for col in display_cols if col in df_display.columns]
        
        st.dataframe(
            df_display[available_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Download CSV
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Descargar Lista (CSV)",
            csv,
            "eventos_pendientes.csv",
            "text/csv"
        )
    
    with tab2:
        st.markdown("#### Agrupado por EPS")
        
        if 'EPS' in df_pending.columns:
            eps_summary = df_pending.groupby('EPS').agg({
                'NOMBRE': 'count',
                'CANTIDAD': 'sum'
            }).reset_index()
            eps_summary.columns = ['EPS', 'Pacientes', 'Sesiones']
            eps_summary = eps_summary.sort_values('Pacientes', ascending=False)
            
            # Chart
            fig = px.bar(
                eps_summary,
                x='EPS',
                y='Pacientes',
                title='Eventos Pendientes por EPS',
                color='Pacientes',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.dataframe(eps_summary, use_container_width=True, hide_index=True)
    
    with tab3:
        st.markdown("#### Agrupado por Profesional")
        
        if 'PROFESIONAL' in df_pending.columns:
            prof_summary = df_pending.groupby('PROFESIONAL').agg({
                'NOMBRE': 'count',
                'CANTIDAD': 'sum'
            }).reset_index()
            prof_summary.columns = ['Profesional', 'Pacientes', 'Sesiones']
            prof_summary = prof_summary.sort_values('Pacientes', ascending=False)
            
            # Chart
            fig = px.bar(
                prof_summary,
                x='Profesional',
                y='Pacientes',
                title='Eventos Pendientes por Profesional',
                color='Sesiones',
                color_continuous_scale='Oranges'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.dataframe(prof_summary, use_container_width=True, hide_index=True)

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
    
    options = ["Dashboard Analítico", "Gestión de Rutas", "Eventos Pendientes", "Explorador de Datos"]
    selection = st.sidebar.radio("Ir a:", options, label_visibility="collapsed")
    
    st.sidebar.info(f"📁 Archivo: {sheet_input[:20]}...")

    # Routing
    if selection == "Dashboard Analítico":
        module_dashboard(df)
    elif selection == "Gestión de Rutas":
        module_rutas(df)
    elif selection == "Eventos Pendientes":
        module_pending_events(df)
    elif selection == "Explorador de Datos":
        module_data_explorer(df)

if __name__ == "__main__":
    main()
