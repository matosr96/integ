
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import zipfile

def clean_text(text):
    if not isinstance(text, str):
        return str(text)
    # Replace common incompatible characters
    replacements = {
        '\u2013': '-',  # en dash
        '\u2014': '--', # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2022': '*',  # bullet
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Final fallback: encode to latin-1 replacing errors, then decode back
    return text.encode('latin-1', 'replace').decode('latin-1')

class RoutePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        # self.cell(0, 10, 'Hoja de Ruta y Logística', 0, 1, 'C') # Custom header per doc usually
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(0, 0, 0) # Ensure footer is Black
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_route_pdf(df_full, professional_name):
    # Switch to Portrait for a document/list feel
    pdf = RoutePDF(orientation='P') 
    pdf.add_page()
    
    # --- HELPER: Identify Valid Date ---
    def is_valid_date(val):
        s = str(val).strip().lower()
        return s and s != 'nan' and s != 'nat' and s != ''
    
    # --- DATA SPLIT ---
    active_rows = []
    pending_rows = []
    
    for idx, row in df_full.iterrows():
        if is_valid_date(row.get('FECHA DE INGRESO')):
            active_rows.append(row)
        else:
            pending_rows.append(row)
            
    # Calculate Stats
    n_active = len(active_rows)
    s_active = sum([float(r.get('CANTIDAD', 0)) for r in active_rows if pd.notna(r.get('CANTIDAD'))])
    
    n_pending = len(pending_rows)
    s_pending = sum([float(r.get('CANTIDAD', 0)) for r in pending_rows if pd.notna(r.get('CANTIDAD'))])

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HOJA DE RUTA DETALLADA", 0, 1, 'C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, f"Profesional: {clean_text(professional_name.upper())}", 0, 1, 'C')
    pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
    
    # NEW METADATA (Split Active vs Pending)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(80, 80, 80) # Dark Gray
    
    summary_text = f"RESUMEN: {n_active} Activos ({int(s_active)} ses.)"
    if n_pending > 0:
        summary_text += f" | {n_pending} Pendientes ({int(s_pending)} ses.)"
        
    pdf.cell(0, 8, summary_text, 0, 1, 'C')
    pdf.set_text_color(0, 0, 0) # Reset to Black
    pdf.ln(5)
    
    # --- RENDER CARD FUNCTION ---
    def render_patient_card(row, is_pending=False):
        # Extract Data
        name = clean_text(f"{row.get('NOMBRE', '')} {row.get('APELLIDOS', '')}")
        address = clean_text(str(row.get('DIRECCION', '')))
        mun = clean_text(str(row.get('MUNICIPIO', '')))
        phone = clean_text(str(row.get('TELEFONO', '')))
        tipo_terapia = clean_text(str(row.get('TIPO DE TERAPIAS', '')))
        cant = clean_text(str(row.get('CANTIDAD', '')))
        doc_type = clean_text(str(row.get('TIPO DE DOCUMENTO', 'Type')))
        doc_num = clean_text(str(row.get('NUMERO', '')))
        user_type = clean_text(str(row.get('TIPO DE USUARIO', '')))
        eps = clean_text(str(row.get('EPS', '')))
        diagnosis = clean_text(str(row.get('DIAGNOSTICO', '')))
        f_ingreso = clean_text(str(row.get('FECHA DE INGRESO', '')))
        f_egreso = clean_text(str(row.get('FECHA DE EGRESO', '')))
        
        # Color Logic
        if is_pending:
            pdf.set_fill_color(255, 240, 230) # Light Orange for Pending
            pdf.set_text_color(200, 0, 0)     # RED TEXT for Pending
            entry_title = f"[PENDIENTE] {name} ({doc_type}: {doc_num})"
        else:
            pdf.set_fill_color(230, 240, 255) # Light Blue for Active
            pdf.set_text_color(0, 0, 0)       # BLACK TEXT for Active
            entry_title = f"{name} ({doc_type}: {doc_num})"

        # Header
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f" {entry_title}", 0, 1, 'L', 1)
        
        # Details Block
        pdf.set_font("Arial", '', 10)
        
        # Helper to print label-value pairs
        def print_field(label, value, end_line=False, w_label=35):
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(w_label, 6, label, 0, 0)
            pdf.set_font("Arial", '', 10)
            val_str = str(value) if value else "N/A"
            if end_line:
                pdf.cell(0, 6, val_str, 0, 1)
            else:
                pdf.cell(60, 6, val_str, 0, 0)

        # Row 1
        print_field("EPS:", eps)
        print_field("Municipio:", mun, end_line=True)
        # Row 2
        print_field("Teléfono:", phone, end_line=True)
        # Row 3
        print_field("Servicio:", f"{tipo_terapia} ({cant} ses.)")
        print_field("Tipo Usuario:", user_type, end_line=True)
        # Row 4 (Dates)
        if is_pending:
             print_field("Estado:", "PENDIENTE DE INGRESO", end_line=True)
        else:
             print_field("Vigencia:", f"{f_ingreso} al {f_egreso}", end_line=True)

        # Full Width Entries
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(35, 6, "Dirección:", 0, 0)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, address)
        
        if diagnosis:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(35, 6, "Diagnóstico:", 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, diagnosis)

        # Separator line
        pdf.ln(4)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_draw_color(0, 0, 0)
        pdf.ln(4)


    # 1. RENDER ACTIVE PATIENTS
    for row in active_rows:
        render_patient_card(row, is_pending=False)
        
    # 2. RENDER PENDING PATIENTS (If any)
    if len(pending_rows) > 0:
        pdf.add_page() # Start pending on new page or just spacing? Let's verify space. 
        # Actually a new page for pending section is cleaner to separate responsibilities.
        # But if active list works, maybe just a strong header is enough.
        # Let's use a strong header.
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(200, 0, 0) # Red
        pdf.cell(0, 10, "EVENTOS PENDIENTES (NO INICIAR SIN AUTORIZACIÓN)", 0, 1, 'C')
        
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(0, 5, "[!] PACIENTES PENDIENTES: Estos usuarios están por llegar. Solo deben iniciarse cuando se envíe la confirmación. Si se trabajan antes, la empresa NO se hace responsable de las sesiones en caso de que no lleguen.", 0, 'C')
        pdf.set_text_color(0, 0, 0) # Reset
        pdf.ln(10)
        
        for row in pending_rows:
            render_patient_card(row, is_pending=True)
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

def generate_all_routes_zip(df_full):
    """
    Generates a ZIP file containing route PDFs for all professionals in the dataframe.
    Returns bytes of the ZIP file.
    """
    zip_buffer = io.BytesIO()
    
    if 'PROFESIONAL' not in df_full.columns:
        return None
        
    professionals = df_full['PROFESIONAL'].dropna().unique()
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for prof in professionals:
            prof_name = str(prof).strip()
            if not prof_name:
                continue
                
            # Filter data for this professional
            df_prof = df_full[df_full['PROFESIONAL'] == prof]
            
            if df_prof.empty:
                continue
                
            try:
                # Generate PDF
                pdf_bytes = create_route_pdf(df_prof, prof_name)
                
                # Add to ZIP
                filename = f"Ruta_{clean_text(prof_name).replace(' ', '_')}.pdf"
                zip_file.writestr(filename, pdf_bytes)
            except Exception as e:
                print(f"Error generating route for {prof_name}: {e}")
                
    return zip_buffer.getvalue()

def create_municipality_report_pdf(df):
    """
    Generates a PDF report listing coverage by Municipality and Specialty.
    """
    pdf = RoutePDF(orientation='P')
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Informe de Cobertura por Municipio", 0, 1, 'C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
    pdf.ln(5)
    
    if 'MUNICIPIO' not in df.columns or 'PROFESIONAL' not in df.columns:
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, "Error: Faltan columnas requeridas (MUNICIPIO, PROFESIONAL).", 0, 1)
        return pdf.output(dest='S').encode('latin-1', 'replace')
        
    # Get Municipalities
    municipalities = sorted([m for m in df['MUNICIPIO'].dropna().unique() if str(m).strip() != ''], key=str)
    
    for muni in municipalities:
        # Filter for Muni
        df_muni = df[df['MUNICIPIO'] == muni]
        
        # Header for Municipality
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f"MUNICIPIO: {clean_text(str(muni).upper())}", 0, 1, 'L', 1)
        pdf.ln(2)
        
        # Identify Professionals and their Specialties in this context
        # We assume a professional has one main specialty per row, or we aggregate logic
        # Logic: Iterate unique professionals, find their most common therapy type
        
        profs_in_muni = df_muni['PROFESIONAL'].dropna().unique()
        
        # Categorize
        specialties_map = {
            'FISIOTERAPIA': [],
            'FONOAUDIOLOGÍA': [],
            'TERAPIA OCUPACIONAL': [],
            'PSICOLOGÍA': [],
            'PEDAGOGÍA': [],
            'OTROS': []
        }
        
        for prof in profs_in_muni:
            # Determine Specialty based on available data for this prof in this muni
            df_p = df_muni[df_muni['PROFESIONAL'] == prof]
            
            # Check therapies
            therapies_str = " ".join(df_p['TIPO DE TERAPIAS'].astype(str).unique()).upper()
            
            clean_name = clean_text(str(prof))
            
            if 'FISIO' in therapies_str or 'FÍSIO' in therapies_str:
                specialties_map['FISIOTERAPIA'].append(clean_name)
            elif 'FONO' in therapies_str or 'TL' in therapies_str or 'LENGUAJE' in therapies_str:
                 specialties_map['FONOAUDIOLOGÍA'].append(clean_name)
            elif 'OCUP' in therapies_str or 'TO' in therapies_str:
                 specialties_map['TERAPIA OCUPACIONAL'].append(clean_name)
            elif 'PSICO' in therapies_str:
                 specialties_map['PSICOLOGÍA'].append(clean_name)
            elif 'PEDAG' in therapies_str:
                 specialties_map['PEDAGOGÍA'].append(clean_name)
            else:
                 specialties_map['OTROS'].append(clean_name)
                 
        # Print Grouped
        for spec_name, prof_list in specialties_map.items():
            if not prof_list:
                continue
                
            # Subheader Specialty
            pdf.set_font("Arial", 'B', 11)
            pdf.set_text_color(0, 51, 102) # Dark Blue
            pdf.cell(0, 8, f"  {spec_name}", 0, 1, 'L')
            
            # List Professionals
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(0, 0, 0)
            for p in sorted(list(set(prof_list))): # Dedupe just in case
                pdf.cell(10, 5, "", 0, 0)
                pdf.cell(0, 5, f"- {p}", 0, 1)
            
            pdf.ln(2)
            
        pdf.ln(3)
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

def create_general_professionals_report_pdf(df):
    """
    Generates a PDF report listing ALL professionals (Uncategorized, Alphabetical).
    """
    pdf = RoutePDF(orientation='P')
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Directorio General de Profesionales", 0, 1, 'C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
    pdf.ln(5)
    
    if 'PROFESIONAL' not in df.columns:
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, "Error: Falta columna PROFESIONAL.", 0, 1)
        return pdf.output(dest='S').encode('latin-1', 'replace')
        
    # Get Unique Professionals
    profs = sorted([p for p in df['PROFESIONAL'].dropna().unique() if str(p).strip() != ''], key=str)
    
    pdf.set_font("Arial", '', 12)
    # 2 columns layout logic could be nice, but simple list for now as requested
    for p in profs:
        clean_name = clean_text(str(p))
        pdf.cell(10, 8, "", 0, 0) # Indent
        pdf.cell(0, 8, f"• {clean_name}", 0, 1)
        
    return pdf.output(dest='S').encode('latin-1', 'replace')
