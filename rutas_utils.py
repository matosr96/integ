
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
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_route_pdf(df_filtered, professional_name):
    # Switch to Portrait for a document/list feel
    pdf = RoutePDF(orientation='P') 
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HOJA DE RUTA DETALLADA", 0, 1, 'C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, f"Profesional: {clean_text(professional_name.upper())}", 0, 1, 'C')
    pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
    pdf.ln(5)
    
    # Iterate patients
    for index, row in df_filtered.iterrows():
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

        # --- Card Start ---
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(230, 240, 255) # Light Blue
        
        # Patient Header
        pdf.cell(0, 8, f" {name} ({doc_type}: {doc_num})", 0, 1, 'L', 1)
        
        # Details Block
        pdf.set_font("Arial", '', 10)
        
        # Helper to print label-value pairs
        def print_field(label, value, end_line=False, w_label=35):
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(w_label, 6, label, 0, 0)
            pdf.set_font("Arial", '', 10)
            # Clean value again just in case
            val_str = str(value) if value else "N/A"
            if end_line:
                pdf.cell(0, 6, val_str, 0, 1)
            else:
                pdf.cell(60, 6, val_str, 0, 0)

        # Row 1: EPS | Mun
        print_field("EPS:", eps)
        print_field("Municipio:", mun, end_line=True)
        
        # Row 2: Phone
        print_field("Teléfono:", phone, end_line=True)
        # print_field("No. Autorización:", auth_num[:25], end_line=True) # Limit length
        
        # Row 3: Service | User Type
        print_field("Servicio:", f"{tipo_terapia} ({cant} ses.)")
        print_field("Tipo Usuario:", user_type, end_line=True)

        # Row 4: Dates
        print_field("Vigencia:", f"{f_ingreso} al {f_egreso}", end_line=True)

        # Full Width Entries
        
        # Address
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(35, 6, "Dirección:", 0, 0)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, address)
        
        # Diagnosis
        if diagnosis:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(35, 6, "Diagnóstico:", 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, diagnosis)
            
            
        # Familiar - REMOVED
        # Novedades - REMOVED

        # Separator line
        pdf.ln(4)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_draw_color(0, 0, 0)
        pdf.ln(4)
        
        # Page break check? FPDF handles it mostly, but if a card is huge...
        # Just relying on auto-page break for now.
        
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
