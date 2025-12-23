
import streamlit as st
import pandas as pd
import plotly.express as px
from src.core.google_sheets_client import GoogleSheetsClient
from fpdf import FPDF
from datetime import datetime
import time
import matplotlib.pyplot as plt
import tempfile
import re
import seaborn as sns
import os
import re

# Configuración de matplotlib para estilo profesional
plt.style.use('ggplot')
sns.set_palette("husl")

# Custom Modules
from src.components.profesionales_component import render_professionals_tab
from src.utils.rutas_utils import create_route_pdf, generate_all_routes_zip, create_municipality_report_pdf, create_general_professionals_report_pdf
from src.utils.trazabilidad_utils import scan_trazabilidades, get_rendicion_stats, load_historical_data_db, load_historical_data_json

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
    
    /* --- MOBILE RESPONSIVENESS (< 768px) --- */
    @media only screen and (max-width: 768px) {
        /* Smaller Headers */
        h1 {
            font-size: 1.8rem !important;
            padding-bottom: 0.5rem;
        }
        h2 {
            font-size: 1.4rem !important;
        }
        h3 {
            font-size: 1.2rem !important;
        }
        
        /* Compact Metrics */
        div[data-testid="stMetric"] {
            padding: 10px;
            margin-bottom: 10px;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 14px !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 20px !important;
        }
        
        /* Reduce spacing container */
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* Adjust buttons */
        .stButton button {
            width: 100%;
        }
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

def clean_therapy_standard(val):
    """
    Normaliza los nombres de terapias a códigos estándar:
    - TL: Terapia de Lenguaje / Fonoaudiología
    - TF: Terapia Física / Fisioterapia
    - TO: Terapia Ocupacional
    - PS: Psicología
    Elimina números y caracteres extra.
    """
    if pd.isna(val): return "N/A"
    s = str(val).upper().strip()
    
    # 1. Códigos estándar y variaciones comunes
    if 'TL' in s or 'FONO' in s or 'LENGUAJ' in s or 'COMUNICA' in s: return 'TL'
    if 'TF' in s or 'FISI' in s: return 'TF'
    if 'TO' in s or 'OCUP' in s: return 'TO'
    if 'PS' in s or 'SICO' in s: return 'PS'
    if 'EDUC' in s or 'ESP' in s: return 'EE'
    
    # 2. Limpieza de prefijos numéricos ("01. TL", "2-TF")
    # Eliminar todo lo que NO sea letra
    cleaned = re.sub(r'[^A-Z]', '', s)
    
    # Si queda algo razonable (2-3 chars), usarlo
    if 2 <= len(cleaned) <= 3:
        return cleaned
        
    # 3. Fallback estricto: Si no se reconoció nada válido (ej: "1", "A", "2023"), agrupar
    return "OTROS"

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
        df_therapy = df_filtered.copy()
        # df_therapy['TIPO DE TERAPIAS'] = df_therapy['TIPO DE TERAPIAS'].astype(str).str.strip().str.upper()
        df_therapy['TIPO DE TERAPIAS'] = df_therapy['TIPO DE TERAPIAS'].apply(clean_therapy_standard)
        
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
        for prof in sorted([p for p in df_filtered['PROFESIONAL'].unique() if pd.notna(p)], key=str):
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

def create_historical_report_pdf(df):
    """Genera un reporte EVOLUTIVO y ANALÍTICO (2018-Presente)"""
    pdf = BasePDF()
    
    # --- HELPER: Save Plot to Temp File ---
    def save_plot_to_image(fig):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            fig.savefig(tmpfile.name, dpi=300, bbox_inches='tight')
            return tmpfile.name

    # Datos Preparados
    if 'AÑO_DATA' not in df.columns:
        return None
        
    # Agrupar por año
    df_yearly = df.groupby('AÑO_DATA').agg({
        'CEDULA': 'nunique',
        'CANTIDAD': 'sum',
        'PROFESIONAL': 'nunique',
        'MUNICIPIO': 'nunique'
    }).reset_index().sort_values('AÑO_DATA')
    df_yearly.columns = ['Año', 'Pacientes', 'Sesiones', 'Profesionales', 'Municipios']

    # ==================== PÁGINA 1: PORTADA Y RESUMEN ====================
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 26)
    pdf.cell(0, 15, "INFORME DE EVOLUCIÓN HISTÓRICA", 0, 1, 'C')
    pdf.set_font("Arial", '', 14)
    min_year = df_yearly['Año'].min()
    max_year = df_yearly['Año'].max()
    pdf.cell(0, 10, f"Análisis Longitudinal {min_year} - {max_year}", 0, 1, 'C')
    pdf.ln(10)
    
    # Resumen acumulado
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Cifras Acumuladas del Periodo:", 0, 1, 'C')
    
    total_sess_hist = df['CANTIDAD'].sum()
    unique_pats_hist = df['CEDULA'].nunique()
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Total Sesiones Realizadas: {int(total_sess_hist):,}", 0, 1, 'C')
    pdf.cell(0, 8, f"Total Pacientes Atendidos: {unique_pats_hist:,}", 0, 1, 'C')
    
    pdf.ln(30)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 5, "Este documento presenta el análisis detallado del comportamiento operativo a lo largo de los años. Se enfoca en identificar tendencias de crecimiento, patrones estacionales y la evolución de la demanda de servicios terapéuticos.", 0, 'C')

    # ==================== PÁGINA 2: EVOLUCIÓN DEL CRECIMIENTO ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "1. CURVA DE CRECIMIENTO ANUAL", 0, 1)
    pdf.ln(5)
    
    # Gráfico 1: Evolución Pacientes vs Sesiones
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    color = 'tab:blue'
    ax1.set_xlabel('Año')
    ax1.set_ylabel('Pacientes', color=color)
    ax1.plot(df_yearly['Año'], df_yearly['Pacientes'], color=color, marker='o', linewidth=2, label='Pacientes')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()  
    color = 'tab:red'
    ax2.set_ylabel('Sesiones', color=color)  
    ax2.plot(df_yearly['Año'], df_yearly['Sesiones'], color=color, marker='s', linestyle='--', linewidth=2, label='Sesiones')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title("Evolución de Volumen Operativo")
    fig.tight_layout()
    
    img_path = save_plot_to_image(fig)
    pdf.image(img_path, x=10, w=190)
    plt.close(fig)
    os.remove(img_path)
    
    pdf.ln(5)
    
    # Tabla de Datos Anual
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(25, 8, "Año", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Pacientes", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Sesiones", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Profesionales", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Var. Pacientes", 1, 1, 'C', 1) # Variación Anual
    
    pdf.set_font("Arial", '', 10)
    prev_pats = 0
    for idx, row in df_yearly.iterrows():
        year = str(int(row['Año']))
        pats = int(row['Pacientes'])
        sess = int(row['Sesiones'])
        profs = int(row['Profesionales'])
        
        # Calcular variación porcentual
        if prev_pats > 0:
            var_pct = ((pats - prev_pats) / prev_pats) * 100
            var_str = f"{var_pct:+.1f}%"
        else:
            var_str = "-"
        prev_pats = pats
        
        pdf.cell(25, 7, year, 1, 0, 'C')
        pdf.cell(40, 7, f"{pats:,}", 1, 0, 'C')
        pdf.cell(40, 7, f"{sess:,}", 1, 0, 'C')
        pdf.cell(40, 7, f"{profs}", 1, 0, 'C')
        pdf.cell(40, 7, var_str, 1, 1, 'C')

    # ==================== PÁGINA 3: EVOLUCIÓN DE SERVICIOS ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "2. EVOLUCIÓN DE TIPOS DE TERAPIA", 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "Análisis de cómo ha cambiado la composición de las terapias a lo largo de los años.")
    pdf.ln(5)
    
    if 'TIPO_TERAPIA' in df.columns or 'TIPO DE TERAPIAS' in df.columns:
        col_terapia = 'TIPO_TERAPIA' if 'TIPO_TERAPIA' in df.columns else 'TIPO DE TERAPIAS'
        
        # Limpieza rápida
        df_srv = df.copy()
        # Limpieza rápida
        df_srv = df.copy()
        # df_srv[col_terapia] = df_srv[col_terapia].astype(str).str.strip().str.upper()
        df_srv[col_terapia] = df_srv[col_terapia].apply(clean_therapy_standard)
        
        # Pivot Table: Año vs Terapia (Cantidad)
        pivot_srv = df_srv.groupby(['AÑO_DATA', col_terapia])['CANTIDAD'].sum().unstack(fill_value=0)
        
        # Filtrar Top 5 Terapias históricas para el gráfico (para no saturar)
        top_services = df_srv.groupby(col_terapia)['CANTIDAD'].sum().sort_values(ascending=False).head(5).index
        pivot_plot = pivot_srv[top_services]
        
        # Área Plot
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        pivot_plot.plot(kind='area', stacked=True, alpha=0.6, ax=ax2)
        plt.title("Tendencia de Volumen por Tipo de Terapia (Top 5)")
        plt.ylabel("Número de Sesiones")
        plt.xlabel("Año")
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        fig2.tight_layout()
        
        img_path2 = save_plot_to_image(fig2)
        pdf.image(img_path2, x=10, w=180)
        plt.close(fig2)
        os.remove(img_path2)
        
    # ==================== PÁGINA 4: ANÁLISIS POR EPS ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "3. DINÁMICA DE CLIENTES (EPS)", 0, 1)
    
    if 'EPS' in df.columns:
        # Pivot: Año vs EPS (Pacientes)
        df_eps_clean = df.copy()
        # Limpiar EPS nulas
        df_eps_clean = df_eps_clean[df_eps_clean['EPS'].notna()]
        
        # Top 6 EPS históricas
        top_eps = df_eps_clean['EPS'].value_counts().head(6).index
        
        df_eps_evo = df_eps_clean[df_eps_clean['EPS'].isin(top_eps)].groupby(['AÑO_DATA', 'EPS'])['CEDULA'].nunique().unstack(fill_value=0)
        
        # Line Plot Multiserie
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        df_eps_evo.plot(kind='line', marker='o', linewidth=2, ax=ax3)
        plt.title("Evolución de Pacientes en Top 6 EPS")
        plt.ylabel("Pacientes Activos")
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        fig3.tight_layout()
        
        img_path3 = save_plot_to_image(fig3)
        pdf.image(img_path3, x=10, w=180)
        plt.close(fig3)
        os.remove(img_path3)
        
    # ==================== CONCLUSIONES (Generadas Dinámicamente) ====================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "4. CONCLUSIONES ESTRATÉGICAS", 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    
    conclusions = []
    
    # 1. Crecimiento Total
    start_vals = df_yearly.iloc[0]
    end_vals = df_yearly.iloc[-1]
    years_diff = end_vals['Año'] - start_vals['Año']
    if years_diff > 0:
        growth_pats = ((end_vals['Pacientes'] - start_vals['Pacientes']) / start_vals['Pacientes']) * 100
        conclusions.append(f"• En el periodo de {int(years_diff)} años, la base de pacientes ha variado un {growth_pats:+.1f}%.")
    
    # 2. Año Pico
    peak_year_row = df_yearly.loc[df_yearly['Sesiones'].idxmax()]
    conclusions.append(f"• El año {int(peak_year_row['Año'])} registró la mayor actividad histórica con {int(peak_year_row['Sesiones']):,} sesiones.")

    # 3. Diversificación
    if 'EPS' in df.columns:
        eps_start = df[df['AÑO_DATA'] == min_year]['EPS'].nunique()
        eps_end = df[df['AÑO_DATA'] == max_year]['EPS'].nunique()
        conclusions.append(f"• La cartera de clientes ha pasado de {eps_start} EPS en {min_year} a {eps_end} EPS en {max_year}.")

    for c in conclusions:
        pdf.multi_cell(0, 8, c.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1', 'replace')

@st.cache_data(ttl=300)
def load_data(sheet_url):
    client = GoogleSheetsClient('credentials.json')
    data = client.get_sheet_data(sheet_url)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def normalize_data(df):
    """
    Global normalization for dataframe.
    - Standardizes Professional Names (specifically merges Yeris Aponte variants).
    """
    if 'PROFESIONAL' in df.columns:
        # Standardize strings to uppercase and strip
        df['PROFESIONAL'] = df['PROFESIONAL'].astype(str).str.strip().str.upper()
        
        # Yeris Aponte Global Unification
        # Matches: "YERIS APONTE", "YERIS APONTE VEREDA", "DR YERIS", etc.
        regex_pattern = r'(YERIS\s+APONTE|DR\.?\s*YERIS)'
        mask_yeris = df['PROFESIONAL'].str.contains(regex_pattern, regex=True, na=False)
        df.loc[mask_yeris, 'PROFESIONAL'] = 'YERIS APONTE'
        
    return df

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

def module_historical_analysis(json_dir):
    """
    Módulo de Análisis Histórico Completo (2018-2025).
    Análisis ejecutivo con KPIs avanzados y reporte descargable.
    """
    st.header("📊 Análisis Histórico Ejecutivo (2018 - Presente)")
    st.markdown("---")

    # Load Data
    with st.spinner("Cargando base de datos histórica..."):
        df = load_historical_data_json(json_dir)
        
    if df.empty:
        st.warning("No se encontraron datos históricos procesados en JSON.")
        return
        
    # Global Normalization
    df = normalize_data(df)

    # --- SIDEBAR FILTERS ---
    st.sidebar.subheader("🔍 Filtros de Análisis")
    
    # 1. Year Filter
    if 'AÑO_DATA' in df.columns:
        available_years = sorted([y for y in df['AÑO_DATA'].unique() if y != 9999])
        selected_years = st.sidebar.multiselect(
            "Seleccionar Años", 
            options=available_years,
            default=available_years
        )
    else:
        selected_years = []
    
    # 2. Therapy Type Filter
    if 'TIPO_TERAPIA' in df.columns:
        available_therapies = sorted([t for t in df['TIPO_TERAPIA'].unique() if pd.notna(t)])
        selected_therapies = st.sidebar.multiselect(
            "Tipo de Terapia",
            options=available_therapies,
            default=available_therapies
        )
    else:
        selected_therapies = []
    
    # 3. EPS Filter
    if 'EPS' in df.columns:
        available_eps = sorted([e for e in df['EPS'].unique() if pd.notna(e)])
        selected_eps = st.sidebar.multiselect(
            "EPS",
            options=available_eps,
            default=available_eps
        )
    else:
        selected_eps = []

    # --- FILTERING LOGIC ---
    mask = pd.Series([True]*len(df))
    
    if selected_years and 'AÑO_DATA' in df.columns:
        mask = mask & df['AÑO_DATA'].isin(selected_years)
        
    if selected_therapies and 'TIPO_TERAPIA' in df.columns:
        mask = mask & df['TIPO_TERAPIA'].isin(selected_therapies)
        
    if selected_eps and 'EPS' in df.columns:
        mask = mask & df['EPS'].isin(selected_eps)
        
    df_filtered = df[mask]
    
    # =========================
    # SECCIÓN 1: KPIs PRINCIPALES (12 INDICADORES)
    # =========================
    st.subheader("📈 Indicadores Clave de Desempeño")
    
    # Calcular métricas
    total_sesiones = df_filtered['CANTIDAD'].sum() if 'CANTIDAD' in df_filtered.columns else 0
    total_pacientes = df_filtered['CEDULA'].nunique() if 'CEDULA' in df_filtered.columns else 0
    total_registros = len(df_filtered)
    prom_sesiones_paciente = total_sesiones / total_pacientes if total_pacientes > 0 else 0
    
    total_profesionales = df_filtered['PROFESIONAL'].nunique() if 'PROFESIONAL' in df_filtered.columns else 0
    total_eps = df_filtered['EPS'].nunique() if 'EPS' in df_filtered.columns else 0
    total_municipios = df_filtered['MUNICIPIO'].nunique() if 'MUNICIPIO' in df_filtered.columns else 0
    total_terapias = df_filtered['TIPO_TERAPIA'].nunique() if 'TIPO_TERAPIA' in df_filtered.columns else 0
    
    # Crecimiento año a año
    if 'AÑO_DATA' in df_filtered.columns and len(selected_years) >= 2:
        years_sorted = sorted(selected_years)
        df_year_current = df_filtered[df_filtered['AÑO_DATA'] == years_sorted[-1]]
        df_year_previous = df_filtered[df_filtered['AÑO_DATA'] == years_sorted[-2]]
        
        sesiones_current = df_year_current['CANTIDAD'].sum() if 'CANTIDAD' in df_year_current.columns else 0
        sesiones_previous = df_year_previous['CANTIDAD'].sum() if 'CANTIDAD' in df_year_previous.columns else 0
        
        growth_rate = ((sesiones_current - sesiones_previous) / sesiones_previous * 100) if sesiones_previous > 0 else 0
    else:
        growth_rate = 0
    
    # Tasa de retención (pacientes que aparecen en múltiples años)
    if 'CEDULA' in df_filtered.columns and 'AÑO_DATA' in df_filtered.columns:
        patient_years = df_filtered.groupby('CEDULA')['AÑO_DATA'].nunique()
        retention_rate = (patient_years[patient_years > 1].count() / total_pacientes * 100) if total_pacientes > 0 else 0
    else:
        retention_rate = 0
    
    # Display KPIs en 4 filas de 3 columnas
    col1, col2, col3 = st.columns(3)
    col1.metric("💉 Total Sesiones", f"{total_sesiones:,.0f}")
    col2.metric("👥 Pacientes Únicos", f"{total_pacientes:,.0f}")
    col3.metric("📋 Total Registros", f"{total_registros:,.0f}")
    
    col4, col5, col6 = st.columns(3)
    col4.metric("👨‍⚕️ Profesionales Activos", f"{total_profesionales}")
    col5.metric("🏥 EPS Atendidas", f"{total_eps}")
    col6.metric("📍 Municipios Cubiertos", f"{total_municipios}")
    
    col7, col8, col9 = st.columns(3)
    col7.metric("🎯 Tipos de Terapia", f"{total_terapias}")
    col8.metric("📊 Prom. Sesiones/Paciente", f"{prom_sesiones_paciente:.1f}")
    col9.metric("📈 Crecimiento Anual", f"{growth_rate:+.1f}%", delta=f"{growth_rate:.1f}%")
    
    col10, col11, col12 = st.columns(3)
    col10.metric("🔄 Tasa de Retención", f"{retention_rate:.1f}%")
    sesiones_por_prof = total_sesiones / total_profesionales if total_profesionales > 0 else 0
    col11.metric("⚡ Sesiones/Profesional", f"{sesiones_por_prof:.0f}")
    pacientes_por_mun = total_pacientes / total_municipios if total_municipios > 0 else 0
    col12.metric("🌍 Pacientes/Municipio", f"{pacientes_por_mun:.1f}")
    
    st.markdown("---")
    
    # =========================
    # SECCIÓN 2: ANÁLISIS TEMPORAL
    # =========================
    st.subheader("📅 Análisis de Tendencias Temporales")
    
    tab1, tab2, tab3 = st.tabs(["📈 Evolución Mensual", "📊 Comparación Anual", "🔄 Estacionalidad"])
    
    with tab1:
        if 'FECHA_INICIO' in df_filtered.columns:
            df_time = df_filtered.dropna(subset=['FECHA_INICIO']).copy()
            if not df_time.empty:
                df_time['Periodo'] = df_time['FECHA_INICIO'].dt.to_period('M').astype(str)
                time_stats = df_time.groupby('Periodo').agg({
                    'CANTIDAD': 'sum',
                    'CEDULA': 'nunique'
                }).reset_index()
                time_stats.columns = ['Periodo', 'Sesiones', 'Pacientes']
                
                fig_time = px.line(
                    time_stats, 
                    x='Periodo', 
                    y=['Sesiones', 'Pacientes'],
                    title='Evolución Mensual: Sesiones y Pacientes',
                    markers=True,
                    template="plotly_white"
                )
                fig_time.update_layout(yaxis_title="Cantidad", xaxis_title="Mes")
                st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No hay datos de fecha disponibles.")
    
    with tab2:
        if 'AÑO_DATA' in df_filtered.columns:
            year_stats = df_filtered.groupby('AÑO_DATA').agg({
                'CANTIDAD': 'sum',
                'CEDULA': 'nunique',
                'PROFESIONAL': 'nunique'
            }).reset_index()
            year_stats.columns = ['Año', 'Sesiones', 'Pacientes', 'Profesionales']
            
            fig_year = px.bar(
                year_stats,
                x='Año',
                y='Sesiones',
                title='Sesiones Totales por Año',
                text='Sesiones',
                template="plotly_white",
                color='Sesiones',
                color_continuous_scale='Viridis'
            )
            fig_year.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_year, use_container_width=True)
            
            # Tabla de comparación
            st.dataframe(year_stats, use_container_width=True, hide_index=True)
    
    with tab3:
        if 'FECHA_INICIO' in df_filtered.columns:
            df_season = df_filtered.dropna(subset=['FECHA_INICIO']).copy()
            if not df_season.empty:
                df_season['Mes'] = df_season['FECHA_INICIO'].dt.month
                season_stats = df_season.groupby('Mes')['CANTIDAD'].sum().reset_index()
                season_stats['Mes_Nombre'] = season_stats['Mes'].apply(lambda x: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][x-1])
                
                fig_season = px.bar(
                    season_stats,
                    x='Mes_Nombre',
                    y='CANTIDAD',
                    title='Patrón Estacional: Sesiones por Mes del Año',
                    template="plotly_white",
                    color='CANTIDAD',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_season, use_container_width=True)
    
    st.markdown("---")
    
    # =========================
    # SECCIÓN 3: ANÁLISIS POR DIMENSIONES
    # =========================
    st.subheader("🔍 Análisis Multidimensional")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🏥 Top 10 EPS por Volumen")
        if 'EPS' in df_filtered.columns:
            eps_stats = df_filtered.groupby('EPS').agg({
                'CANTIDAD': 'sum',
                'CEDULA': 'nunique'
            }).reset_index().sort_values('CANTIDAD', ascending=False).head(10)
            eps_stats.columns = ['EPS', 'Sesiones', 'Pacientes']
            
            fig_eps = px.bar(
                eps_stats,
                y='EPS',
                x='Sesiones',
                orientation='h',
                title='',
                template="plotly_white",
                color='Sesiones',
                color_continuous_scale='Blues',
                text='Sesiones'
            )
            fig_eps.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_eps.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_eps, use_container_width=True)
    
    with col_right:
        st.markdown("#### 🎯 Distribución por Tipo de Terapia")
        if 'TIPO_TERAPIA' in df_filtered.columns:
            # Limpieza de datos visual para el gráfico
            df_chart = df_filtered.copy()
            df_chart['TIPO_TERAPIA_CLEAN'] = df_chart['TIPO_TERAPIA'].apply(clean_therapy_standard)
            
            terapia_stats = df_chart.groupby('TIPO_TERAPIA_CLEAN')['CANTIDAD'].sum().reset_index().sort_values('CANTIDAD', ascending=False)
            
            fig_therapy = px.pie(
                terapia_stats,
                values='CANTIDAD',
                names='TIPO_TERAPIA_CLEAN',
                title='',
                template="plotly_white",
                hole=0.4
            )
            st.plotly_chart(fig_therapy, use_container_width=True)
    
    # =========================
    # SECCIÓN 4: ANÁLISIS DE PROFESIONALES
    # =========================
    st.markdown("---")
    st.subheader("👨‍⚕️ Desempeño de Profesionales")
    
    if 'PROFESIONAL' in df_filtered.columns:
        prof_stats = df_filtered.groupby('PROFESIONAL').agg({
            'CEDULA': 'nunique',
            'CANTIDAD': 'sum',
            'MUNICIPIO': 'nunique'
        }).reset_index()
        prof_stats.columns = ['Profesional', 'Pacientes', 'Sesiones', 'Municipios']
        prof_stats['Prom_Sesiones'] = prof_stats['Sesiones'] / prof_stats['Pacientes']
        prof_stats = prof_stats.sort_values('Sesiones', ascending=False).head(20)
        
        st.dataframe(
            prof_stats.style.format({
                'Pacientes': '{:,.0f}',
                'Sesiones': '{:,.0f}',
                'Prom_Sesiones': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    # =========================
    # SECCIÓN 5: COBERTURA GEOGRÁFICA
    # =========================
    st.markdown("---")
    st.subheader("🗺️ Cobertura Geográfica Completa")
    
    if 'MUNICIPIO' in df_filtered.columns:
        # Calcular estadísticas completas por municipio
        mun_stats_full = df_filtered.groupby('MUNICIPIO').agg({
            'CEDULA': 'nunique',
            'CANTIDAD': 'sum',
            'PROFESIONAL': 'nunique'
        }).reset_index().sort_values('CEDULA', ascending=False)
        mun_stats_full.columns = ['Municipio', 'Pacientes', 'Sesiones', 'Profesionales']
        
        # KPIs de cobertura
        col_geo1, col_geo2, col_geo3 = st.columns(3)
        col_geo1.metric("🌍 Total Municipios", len(mun_stats_full))
        col_geo2.metric("🏆 Municipio Principal", mun_stats_full.iloc[0]['Municipio'] if len(mun_stats_full) > 0 else "N/A")
        col_geo3.metric("👥 Pacientes (Principal)", f"{mun_stats_full.iloc[0]['Pacientes']:,.0f}" if len(mun_stats_full) > 0 else "0")
        
        st.markdown("---")
        
        # Tabs para diferentes vistas
        tab_chart, tab_list, tab_table = st.tabs(["📊 Top 15 Municipios", "📋 Lista Completa", "📈 Tabla Detallada"])
        
        with tab_chart:
            # Gráfico Top 15
            mun_top15 = mun_stats_full.head(15)
            fig_mun = px.bar(
                mun_top15,
                x='Municipio',
                y='Pacientes',
                title='Top 15 Municipios por Pacientes Atendidos',
                template="plotly_white",
                color='Pacientes',
                color_continuous_scale='Greens',
                text='Pacientes'
            )
            fig_mun.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_mun, use_container_width=True)
        
        with tab_list:
            st.markdown("#### 🗺️ Listado Alfabético de Todos los Municipios Atendidos")
            st.caption(f"Total: {len(mun_stats_full)} municipios")
            
            # Ordenar alfabéticamente
            municipios_sorted = sorted(mun_stats_full['Municipio'].dropna().unique())
            
            # Mostrar en columnas para mejor visualización
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, municipio in enumerate(municipios_sorted):
                col_idx = idx % num_cols
                with cols[col_idx]:
                    # Obtener stats del municipio
                    mun_data = mun_stats_full[mun_stats_full['Municipio'] == municipio].iloc[0]
                    st.markdown(f"**{idx+1}. {municipio}**")
                    st.caption(f"👥 {mun_data['Pacientes']:,.0f} pacientes | 💉 {mun_data['Sesiones']:,.0f} sesiones")
        
        with tab_table:
            st.markdown("#### 📊 Estadísticas Detalladas por Municipio")
            
            # Agregar columnas calculadas
            mun_stats_full['Prom_Sesiones_Paciente'] = mun_stats_full['Sesiones'] / mun_stats_full['Pacientes']
            mun_stats_full['% del Total'] = (mun_stats_full['Pacientes'] / mun_stats_full['Pacientes'].sum() * 100)
            
            st.dataframe(
                mun_stats_full.style.format({
                    'Pacientes': '{:,.0f}',
                    'Sesiones': '{:,.0f}',
                    'Profesionales': '{:.0f}',
                    'Prom_Sesiones_Paciente': '{:.1f}',
                    '% del Total': '{:.2f}%'
                }),
                use_container_width=True,
                hide_index=True,
                height=400
            )
    
    # =========================
    # SECCIÓN 6: DEEP DIVE POR AÑO
    # =========================
    st.markdown("---")
    st.subheader("🔍 Análisis Detallado por Año y Mes (Deep Dive)")
    
    if 'AÑO_DATA' in df.columns:
        all_years = sorted(df['AÑO_DATA'].unique())
        c1, c2 = st.columns(2)
        with c1:
            selected_dive_year = st.selectbox("Seleccione un año:", options=all_years, index=len(all_years)-1)
        
        # Filtrar por año primero para obtener meses disponibles
        df_year_raw = df[df['AÑO_DATA'] == selected_dive_year].copy()
        
        # Procesar meses si hay fechas
        if 'FECHA_INICIO' in df_year_raw.columns:
            df_year_raw['Mes_Num'] = df_year_raw['FECHA_INICIO'].dt.month
            meses_disp = sorted(df_year_raw['Mes_Num'].dropna().unique().astype(int))
            meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            meses_opciones = {m: meses_nombres[m-1] for m in meses_disp}
            
            with c2:
                selected_dive_months = st.multiselect(
                    "Filtrar por Meses:", 
                    options=meses_disp, 
                    default=meses_disp,
                    format_func=lambda x: meses_opciones.get(x, str(x))
                )
            
            # Corrección del filtro: usar los meses seleccionados
            if not selected_dive_months:
                df_year = df_year_raw
            else:
                df_year = df_year_raw[df_year_raw['Mes_Num'].isin(selected_dive_months)]
        else:
            df_year = df_year_raw
            st.warning("No se detectaron columnas de fecha para filtrado mensual en este periodo.")

        if not df_year.empty:
            # Asegurar que Mes_Num sea int para evitar TypeErrors en el mapeo
            if 'Mes_Num' in df_year.columns:
                df_year['Mes_Num'] = df_year['Mes_Num'].fillna(0).astype(int)
            
            st.info(f"Mostrando detalles para **{selected_dive_year}** ({len(selected_dive_months) if 'selected_dive_months' in locals() else 'todos'} meses seleccionados)")
            
            # Sub-KPIs para el periodo seleccionado
            s1, s2, s3, s4 = st.columns(4)
            y_sesiones = df_year['CANTIDAD'].sum()
            y_pacientes = df_year['CEDULA'].nunique()
            y_profesionales = df_year['PROFESIONAL'].nunique()
            y_municipios = df_year['MUNICIPIO'].nunique()
            
            s1.metric("💉 Sesiones", f"{y_sesiones:,.0f}")
            s2.metric("👥 Pacientes", f"{y_pacientes:,.0f}")
            s3.metric("👨‍⚕️ Profesionales", y_profesionales)
            s4.metric("📍 Municipios", y_municipios)
            
            # Visualizaciones
            tab_dive1, tab_dive2, tab_dive3 = st.tabs(["📈 Tendencia y EPS", "🔎 Diagnóstico y Geografía", "👥 Lista Detallada"])
            
            with tab_dive1:
                d1, d2 = st.columns(2)
                with d1:
                    # Evolución mensual (o diaria si es un solo mes)
                    if 'Mes_Num' in df_year.columns and len(selected_dive_months) == 1:
                        df_year['Dia'] = df_year['FECHA_INICIO'].dt.day
                        y_day_stats = df_year.groupby('Dia')['CANTIDAD'].sum().reset_index()
                        fig_y_time = px.line(y_day_stats, x='Dia', y='CANTIDAD', title=f'Sesiones Diarias: {meses_opciones[selected_dive_months[0]]} {selected_dive_year}', markers=True)
                    elif 'Mes_Num' in df_year.columns:
                        y_time_stats = df_year.groupby('Mes_Num')['CANTIDAD'].sum().reset_index()
                        # Cast to int to be safe against TypeError
                        meses_list = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                        y_time_stats['Nombre_Mes'] = y_time_stats['Mes_Num'].apply(lambda x: meses_list[int(x)-1] if 0 < int(x) <= 12 else "Sin Mes")
                        fig_y_time = px.line(y_time_stats, x='Nombre_Mes', y='CANTIDAD', title=f'Evolución Mensual en {selected_dive_year}', markers=True)
                    else:
                        st.write("Faltan datos temporales para esta gráfica.")
                    st.plotly_chart(fig_y_time, use_container_width=True)
                
                with d2:
                    if 'EPS' in df_year.columns:
                        y_eps_stats = df_year.groupby('EPS')['CANTIDAD'].sum().reset_index().sort_values('CANTIDAD', ascending=False).head(10)
                        fig_y_eps = px.bar(y_eps_stats, x='CANTIDAD', y='EPS', orientation='h', title='Top 10 EPS', color='CANTIDAD', template="plotly_white")
                        st.plotly_chart(fig_y_eps, use_container_width=True)

            with tab_dive2:
                g1, g2 = st.columns(2)
                with g1:
                    if 'DIAGNOSTICO' in df_year.columns:
                        y_diag_stats = df_year.groupby('DIAGNOSTICO')['CEDULA'].nunique().reset_index().sort_values('CEDULA', ascending=False).head(10)
                        y_diag_stats.columns = ['Diagnóstico', 'Pacientes']
                        fig_y_diag = px.bar(y_diag_stats, x='Pacientes', y='Diagnóstico', orientation='h', title='Top 10 Diagnósticos (Pacientes)', color='Pacientes', color_continuous_scale='Reds')
                        st.plotly_chart(fig_y_diag, use_container_width=True)
                
                with g2:
                    if 'MUNICIPIO' in df_year.columns:
                        y_mun_stats = df_year.groupby('MUNICIPIO')['CANTIDAD'].sum().reset_index().sort_values('CANTIDAD', ascending=False).head(10)
                        fig_y_mun = px.bar(y_mun_stats, x='CANTIDAD', y='MUNICIPIO', orientation='h', title='Top 10 Municipios (Sesiones)', color='CANTIDAD', color_continuous_scale='Purples')
                        st.plotly_chart(fig_y_mun, use_container_width=True)

            with tab_dive3:
                # Detalle de Profesionales y Pacientes
                p_col1, p_col2 = st.columns([1, 1])
                with p_col1:
                    st.markdown(f"#### 👨‍⚕️ Profesionales en el Periodo")
                    y_prof_stats = df_year.groupby('PROFESIONAL').agg({
                        'CANTIDAD': 'sum',
                        'CEDULA': 'nunique'
                    }).reset_index().sort_values('CANTIDAD', ascending=False)
                    y_prof_stats.columns = ['Profesional', 'Sesiones', 'Pacientes']
                    st.dataframe(y_prof_stats, use_container_width=True, hide_index=True)
                
                with p_col2:
                    st.markdown(f"#### 👥 Resumen por EPS")
                    y_eps_detail = df_year.groupby('EPS').agg({
                        'CEDULA': 'nunique',
                        'CANTIDAD': 'sum'
                    }).reset_index().sort_values('CEDULA', ascending=False)
                    y_eps_detail.columns = ['EPS', 'Pacientes', 'Sesiones']
                    st.dataframe(y_eps_detail, use_container_width=True, hide_index=True)
        else:
            st.warning("No se encontraron datos para la combinación de filtros seleccionada.")
    
    # =========================
    # SECCIÓN 7: REPORTE DESCARGABLE
    # =========================
    st.markdown("---")
    st.subheader("📥 Generar Reporte Ejecutivo")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("📄 Descargar Reporte PDF Completo", type="primary", use_container_width=True):
            with st.spinner("Generando reporte ejecutivo profesional..."):
                # Preparar datos para el reporte
                kpi_data = {
                    "Total Sesiones": int(total_sesiones),
                    "Pacientes Únicos": total_pacientes,
                    "Profesionales Activos": total_profesionales,
                    "EPS Atendidas": total_eps,
                    "Municipios Cubiertos": total_municipios,
                    "Crecimiento Anual": f"{growth_rate:.1f}%",
                    "Tasa de Retención": f"{retention_rate:.1f}%"
                }
                
                # Renombrar columnas para compatibilidad con PDF existente
                df_pdf = df_filtered.rename(columns={
                    'NOMBRES': 'NOMBRE',
                    'TIPO_TERAPIA': 'TIPO DE TERAPIAS',
                })
                
                pdf_bytes = create_historical_report_pdf(df_pdf)
                
                if pdf_bytes:
                    st.download_button(
                        "⬇️ Descargar Reporte Histórico PDF",
                        data=pdf_bytes,
                        file_name=f"Reporte_Historico_Ejecutivo_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
    
    with col_btn2:
        # Exportar datos filtrados a CSV
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📊 Exportar Datos a CSV",
            data=csv,
            file_name=f"Datos_Historicos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # --- RAW DATA VIEW ---
    with st.expander("🔎 Ver Datos Detallados (Tabla Completa)"):
        st.dataframe(df_filtered.head(1000), use_container_width=True)

def module_dashboard(df):
    st.markdown("## 📊 Dashboard Analítico")
    st.markdown("Resumen general del estado de la operación.")
    
    # Context Filters for Dashboard
    with st.expander("🔎 Filtros de Visualización", expanded=False):
        c1, c2 = st.columns(2)
        mun_opt = ['Todos'] + sorted([x for x in df['MUNICIPIO'].unique() if pd.notna(x)], key=str) if 'MUNICIPIO' in df.columns else ['Todos']
        sel_mun = c1.selectbox("Filtrar por Municipio", mun_opt)
        
        eps_opt = ['Todas'] + sorted([x for x in df['EPS'].unique() if pd.notna(x)], key=str) if 'EPS' in df.columns else ['Todas']
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
            # Normalizar datos para evitar duplicados
            df_therapy_chart = df_view.copy()
            # df_therapy_chart['TIPO DE TERAPIAS'] = df_therapy_chart['TIPO DE TERAPIAS'].astype(str).str.strip().str.upper()
            df_therapy_chart['TIPO DE TERAPIAS'] = df_therapy_chart['TIPO DE TERAPIAS'].apply(clean_therapy_standard)
            
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
    
    profs_available = sorted([p for p in df['PROFESIONAL'].unique() if pd.notna(p)], key=str)
    
    with tab1:
        # Selection Column
        c_sel, c_view = st.columns([1, 3])
        
        with c_sel:
            st.markdown("### Seleccionar")
            selected_prof = st.selectbox("Profesional:", profs_available)
            
            if selected_prof:
                # 1. Full dataframe for this professional (including pending dates)
                df_prof_full = df[df['PROFESIONAL'] == selected_prof].copy()
                
                # 2. Filtered dataframe for Metrics (Active only)
                # Filtrar solo pacientes con vigencia activa
                df_prof = df_prof_full.copy()
                if 'FECHA DE INGRESO' in df_prof.columns:
                    df_prof = df_prof[
                        (df_prof['FECHA DE INGRESO'].notna()) & 
                        (df_prof['FECHA DE INGRESO'].astype(str).str.strip() != '') &
                        (df_prof['FECHA DE INGRESO'].astype(str).str.lower() != 'nan')
                    ]
                
                # Metric 1: Total Patients (solo activos)
                st.metric("Pacientes Activos", len(df_prof))
                
                # Metric 2: Total Sesiones
                sessions = df_prof['CANTIDAD'].sum() if 'CANTIDAD' in df_prof.columns else 0
                st.metric("Total Sesiones (Activas)", int(sessions))
                
                st.divider()
                
                if len(df_prof_full) > 0:
                    st.info("Descargue la hoja de ruta (Incluye Eventos Pendientes).")
                    
                    # Pre-generate PDF using FULL data
                    pdf_bytes = create_route_pdf(df_prof_full, selected_prof)
                    
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
        
        mun_opt = ['Todos'] + sorted([x for x in df['MUNICIPIO'].unique() if pd.notna(x)], key=str) if 'MUNICIPIO' in df.columns else ['Todos']
        sel_mun = c1.selectbox("Municipio", mun_opt, key="de_mun")
        
        eps_opt = ['Todas'] + sorted([x for x in df['EPS'].unique() if pd.notna(x)], key=str) if 'EPS' in df.columns else ['Todas']
        sel_eps = c2.selectbox("EPS", eps_opt, key="de_eps")
        
        type_opt = sorted([x for x in df['TIPO DE USUARIO'].unique() if pd.notna(x)], key=str) if 'TIPO DE USUARIO' in df.columns else []
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
    
    c_down1, c_down2, c_down3, c_down4 = st.columns(4)
    
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
            # Placeholder for novelty PDF (if existing) or similar
            st.info("Función de novedades en mantenimiento.")
            # pdf_nov = create_novedades_pdf(df_filtered)
            # if pdf_nov:
            #     st.download_button("⬇️ Descargar PDF", pdf_nov, "novedades.pdf", "application/pdf")
            # else:
            #     st.info("Sin novedades.")

    with c_down4:
        st.markdown("**4. Reportes PDF**")
        st.caption("Generación de informes.")
        
        # Report 1: Municipality
        pdf_cov = create_municipality_report_pdf(df_filtered)
        st.download_button("⬇️ Cobertura por Municipio", pdf_cov, "cobertura_municipios.pdf", "application/pdf")
        
        st.divider()
        
        # Report 2: General Directory
        pdf_gen = create_general_professionals_report_pdf(df_filtered)
        st.download_button("⬇️ Directorio General", pdf_gen, "directorio_profesionales.pdf", "application/pdf")

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
        
    # Global Normalization
    df = normalize_data(df)
        
    # Preprocessing
    if 'CANTIDAD' in df.columns:
        df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce').fillna(0)

    # Sidebar Navigation using Radio for clear tabs
    st.sidebar.markdown("---")
    options = ["Dashboard Analítico", "Gestión de Rutas", "Eventos Pendientes", "Explorador de Datos", "Análisis Histórico"]
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
    elif selection == "Análisis Histórico":
        module_historical_analysis('data/processed/trazabilidad_LIMPIA.json')

if __name__ == "__main__":
    main()
