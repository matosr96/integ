"""
Componente de Profesionales para el Dashboard
Este módulo contiene las funciones para mostrar la sección de profesionales
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

def load_consolidated_professionals():
    """Carga los datos consolidados de profesionales"""
    try:
        with open('profesionales_consolidados.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error cargando datos de profesionales: {e}")
        return pd.DataFrame()

def create_professional_card(prof_data):
    """Crea una tarjeta visual para un profesional"""
    nombre = prof_data.get('NOMBRE PROFESIONAL', 'Sin nombre')
    cedula = prof_data.get('CEDULA', 'N/A')
    telefono = prof_data.get('TEL CONTACTO', 'N/A')
    email = prof_data.get('MAIL', 'N/A')
    municipio = prof_data.get('MUNICIPIO', 'N/A')
    vinculacion = prof_data.get('VINCULACION', 'N/A')
    tarifa = prof_data.get('TARIFA', 'N/A')
    
    # Crear HTML para la tarjeta
    card_html = f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0 0 10px 0; color: white;">{nombre}</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
            <div><strong>📋 Cédula:</strong> {cedula}</div>
            <div><strong>📱 Teléfono:</strong> {telefono}</div>
            <div><strong>📧 Email:</strong> {email}</div>
            <div><strong>📍 Municipio:</strong> {municipio}</div>
            <div><strong>💼 Vinculación:</strong> {vinculacion}</div>
            <div><strong>💰 Tarifa:</strong> {tarifa}</div>
        </div>
    </div>
    """
    return card_html

def create_professional_report_pdf(prof_data, patient_data):
    """Genera un reporte PDF individual del profesional"""
    from fpdf import FPDF
    from datetime import datetime
    
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'REPORTE INDIVIDUAL DE PROFESIONAL', 0, 1, 'C')
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    pdf.ln(5)
    
    # Professional Info
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'DATOS DEL PROFESIONAL', 0, 1)
    pdf.set_font('Arial', '', 11)
    
    nombre = prof_data.get('NOMBRE PROFESIONAL', 'Sin nombre')
    cedula = prof_data.get('CEDULA', 'N/A')
    telefono = prof_data.get('TEL CONTACTO', 'N/A')
    email = prof_data.get('MAIL', 'N/A')
    municipio = prof_data.get('MUNICIPIO', 'N/A')
    vinculacion = prof_data.get('VINCULACION', 'N/A')
    tarifa = prof_data.get('TARIFA', 'N/A')
    
    pdf.cell(0, 8, f'Nombre: {nombre}', 0, 1)
    pdf.cell(0, 8, f'Cedula: {cedula}', 0, 1)
    pdf.cell(0, 8, f'Telefono: {telefono}', 0, 1)
    pdf.cell(0, 8, f'Email: {email}', 0, 1)
    pdf.cell(0, 8, f'Municipio: {municipio}', 0, 1)
    pdf.cell(0, 8, f'Vinculacion: {vinculacion}', 0, 1)
    pdf.cell(0, 8, f'Tarifa: {tarifa}', 0, 1)
    pdf.ln(10)
    
    # Patient Statistics
    if patient_data is not None and not patient_data.empty:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'ESTADISTICAS DE PACIENTES', 0, 1)
        pdf.set_font('Arial', '', 11)
        
        total_pacientes = len(patient_data)
        total_sesiones = patient_data['CANTIDAD'].sum() if 'CANTIDAD' in patient_data.columns else 0
        
        pdf.cell(0, 8, f'Total de Pacientes Asignados: {total_pacientes}', 0, 1)
        pdf.cell(0, 8, f'Total de Sesiones: {int(total_sesiones)}', 0, 1)
        pdf.ln(10)
        
        # Patient List
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'LISTA DE PACIENTES', 0, 1)
        pdf.set_font('Arial', '', 9)
        
        # Table header
        pdf.cell(80, 7, 'Paciente', 1)
        pdf.cell(40, 7, 'Municipio', 1)
        pdf.cell(30, 7, 'Tipo Terapia', 1)
        pdf.cell(20, 7, 'Sesiones', 1)
        pdf.ln()
        
        # Table rows
        for _, row in patient_data.head(20).iterrows():  # Limit to 20 patients
            nombre_pac = f"{row.get('NOMBRE', '')} {row.get('APELLIDOS', '')}"[:35]
            mun = str(row.get('MUNICIPIO', ''))[:20]
            tipo = str(row.get('TIPO DE TERAPIAS', ''))[:15]
            cant = str(row.get('CANTIDAD', ''))
            
            pdf.cell(80, 7, nombre_pac, 1)
            pdf.cell(40, 7, mun, 1)
            pdf.cell(30, 7, tipo, 1)
            pdf.cell(20, 7, cant, 1)
            pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def render_professionals_tab(df_patients):
    """Renderiza la pestaña completa de profesionales"""
    st.header("👥 Gestión de Profesionales")
    
    # Load consolidated data
    df_profs = load_consolidated_professionals()
    
    if df_profs.empty:
        st.warning("No se encontraron datos de profesionales consolidados.")
        st.info("Ejecuta el script `consolidar_profesionales.py` primero para generar los datos.")
        return
    
    # Remove internal fields for display
    display_cols = [col for col in df_profs.columns if not col.startswith('_')]
    
    # KPIs
    st.subheader("📊 Resumen General")
    col1, col2, col3, col4 = st.columns(4)
    
    total_profs = len(df_profs)
    profs_con_match = df_profs['_match_encontrado'].sum() if '_match_encontrado' in df_profs.columns else 0
    profs_evento = len(df_profs[df_profs['VINCULACION'].str.upper().str.contains('EVENTO', na=False)]) if 'VINCULACION' in df_profs.columns else 0
    profs_contrato = len(df_profs[df_profs['VINCULACION'].str.upper().str.contains('CONTRATO', na=False)]) if 'VINCULACION' in df_profs.columns else 0
    
    col1.metric("Total Profesionales", total_profs)
    col2.metric("Datos Completos", f"{profs_con_match}/{total_profs}")
    col3.metric("Por Evento", profs_evento)
    col4.metric("Por Contrato", profs_contrato)
    
    st.markdown("---")
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📍 Distribución por Municipio")
        if 'MUNICIPIO' in df_profs.columns:
            mun_counts = df_profs['MUNICIPIO'].value_counts().head(10)
            fig_mun = px.bar(
                x=mun_counts.values,
                y=mun_counts.index,
                orientation='h',
                labels={'x': 'Cantidad', 'y': 'Municipio'},
                color=mun_counts.values,
                color_continuous_scale='Viridis'
            )
            fig_mun.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_mun, use_container_width=True)
    
    with col_chart2:
        st.subheader("💼 Tipo de Vinculación")
        if 'VINCULACION' in df_profs.columns:
            vinc_counts = df_profs['VINCULACION'].value_counts()
            fig_pie = px.pie(
                values=vinc_counts.values,
                names=vinc_counts.index,
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Professional Directory
    st.subheader("📋 Directorio de Profesionales")
    
    # Search and filter
    col_search, col_filter = st.columns([2, 1])
    
    with col_search:
        search_term = st.text_input("🔍 Buscar profesional", placeholder="Nombre, cédula, municipio...")
    
    with col_filter:
        if 'MUNICIPIO' in df_profs.columns:
            municipios = ['Todos'] + sorted(df_profs['MUNICIPIO'].dropna().unique().tolist())
            selected_mun = st.selectbox("Filtrar por municipio", municipios)
    
    # Apply filters
    df_filtered = df_profs.copy()
    
    if search_term:
        mask = df_filtered[display_cols].astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        df_filtered = df_filtered[mask]
    
    if 'MUNICIPIO' in df_profs.columns and selected_mun != 'Todos':
        df_filtered = df_filtered[df_filtered['MUNICIPIO'] == selected_mun]
    
    st.caption(f"Mostrando {len(df_filtered)} de {len(df_profs)} profesionales")
    
    # Display options
    view_mode = st.radio("Modo de visualización", ["Tarjetas", "Tabla", "Detalles"], horizontal=True)
    
    if view_mode == "Tarjetas":
        # Card view
        cols_per_row = 2
        for i in range(0, len(df_filtered), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(df_filtered):
                    with col:
                        prof = df_filtered.iloc[idx]
                        card_html = create_professional_card(prof)
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # WhatsApp button
                        telefono = prof.get('TEL CONTACTO', '')
                        if telefono:
                            from dashboard import get_whatsapp_link
                            wa_link = get_whatsapp_link(telefono, f"Hola {prof.get('NOMBRE PROFESIONAL', '')}")
                            if wa_link:
                                st.markdown(f"[💬 WhatsApp]({wa_link})", unsafe_allow_html=True)
    
    elif view_mode == "Tabla":
        # Table view
        st.dataframe(
            df_filtered[display_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = df_filtered[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar lista (CSV)",
            data=csv,
            file_name='profesionales.csv',
            mime='text/csv'
        )
    
    else:  # Detalles
        # Detailed view with individual reports
        st.subheader("📄 Reportes Individuales")
        
        if not df_filtered.empty:
            selected_prof_name = st.selectbox(
                "Seleccionar profesional",
                df_filtered['NOMBRE PROFESIONAL'].tolist() if 'NOMBRE PROFESIONAL' in df_filtered.columns else []
            )
            
            if selected_prof_name:
                prof_data = df_filtered[df_filtered['NOMBRE PROFESIONAL'] == selected_prof_name].iloc[0]
                
                # Display professional info
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("### Información Personal")
                    st.write(f"**Nombre:** {prof_data.get('NOMBRE PROFESIONAL', 'N/A')}")
                    st.write(f"**Cédula:** {prof_data.get('CEDULA', 'N/A')}")
                    st.write(f"**Teléfono:** {prof_data.get('TEL CONTACTO', 'N/A')}")
                    st.write(f"**Email:** {prof_data.get('MAIL', 'N/A')}")
                
                with col_info2:
                    st.markdown("### Información Laboral")
                    st.write(f"**Municipio:** {prof_data.get('MUNICIPIO', 'N/A')}")
                    st.write(f"**Vinculación:** {prof_data.get('VINCULACION', 'N/A')}")
                    st.write(f"**Tarifa:** {prof_data.get('TARIFA', 'N/A')}")
                    st.write(f"**Dirección:** {prof_data.get('DIRECCION', 'N/A')}")
                
                # Get patient data for this professional
                if df_patients is not None and not df_patients.empty and 'PROFESIONAL' in df_patients.columns:
                    patient_data = df_patients[df_patients['PROFESIONAL'] == selected_prof_name]
                    
                    if not patient_data.empty:
                        st.markdown("---")
                        st.markdown("### 📊 Estadísticas de Pacientes")
                        
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        col_stat1.metric("Pacientes Asignados", len(patient_data))
                        col_stat2.metric("Total Sesiones", int(patient_data['CANTIDAD'].sum()) if 'CANTIDAD' in patient_data.columns else 0)
                        
                        # Generate PDF report
                        st.markdown("---")
                        st.markdown("### 📥 Descargar Reporte")
                        
                        try:
                            pdf_bytes = create_professional_report_pdf(prof_data, patient_data)
                            st.download_button(
                                "📄 Descargar Reporte Individual (PDF)",
                                data=pdf_bytes,
                                file_name=f"reporte_{selected_prof_name.replace(' ', '_')}.pdf",
                                mime='application/pdf',
                                type="primary"
                            )
                        except Exception as e:
                            st.error(f"Error generando PDF: {e}")
                    else:
                        st.info("Este profesional no tiene pacientes asignados actualmente.")
