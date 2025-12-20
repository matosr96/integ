import pandas as pd
import os
import streamlit as st
from datetime import datetime
import re
import json
from unidecode import unidecode

# Mapping of historical column names to standard names
COLUMN_MAPPING = {
    # Names
    'NOMBRE': 'NOMBRES',
    'NOMBRE ': 'NOMBRES',
    'NOMBRES': 'NOMBRES',
    'APELLIDOS': 'APELLIDOS',
    'APELLIDOS ': 'APELLIDOS',
    
    # ID
    'TIPO DE ID': 'TIPO_ID',
    'TIPO DE DOCUMENTO': 'TIPO_ID',
    'NUMERO DE ID': 'CEDULA',
    'NUMERO': 'CEDULA',
    
    # Dates
    'FECHA DE INICIO': 'FECHA_INICIO',
    'FECHA DE INGRESO': 'FECHA_INICIO',
    'FECHA DE ENTREGA ': 'FECHA_INICIO',
    'FECHA DE EGRESO': 'FECHA_EGRESO',
    'FECHA EGRESO': 'FECHA_EGRESO',
    
    # Therapy Details
    'TIPO DE TERAPIAS': 'TIPO_TERAPIA',
    'TIPO DE TERAPIA': 'TIPO_TERAPIA',
    'tipo': 'TIPO_TERAPIA',
    '# TERAPIAS': 'CANTIDAD',
    'SESIONES DE TERAPIAS': 'CANTIDAD',
    'Cantidad': 'CANTIDAD',
    
    # Professional
    'PROFESIONAL': 'PROFESIONAL',
    'TERAPEUTA ENTREGADO': 'PROFESIONAL',
    
    # Location
    'MUNICIPIO': 'MUNICIPIO',
    'MUNICIPO DE ATENCION ': 'MUNICIPIO',
    
    # Others
    'EPS': 'EPS',
    'DIAGNOSTICO': 'DIAGNOSTICO',
    'TIPO DE USUARIO': 'TIPO_USUARIO',
    'OBSERVACIONES': 'OBSERVACIONES',
    'OBSERVACIONES AL PROCESO': 'OBSERVACIONES'
}

@st.cache_data(ttl=3600)
def scan_trazabilidades(base_path):
    """
    Scans the base_path for Excel files and consolidates them.
    Recursively searches through year folders.
    """
    all_data = []
    
    if not os.path.exists(base_path):
        return pd.DataFrame()

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.xlsx') and not file.startswith('~$'):
                file_path = os.path.join(root, file)
                try:
                    # Read Excel
                    df = pd.read_excel(file_path)
                    
                    # Normalize columns
                    df = df.rename(columns={col: COLUMN_MAPPING.get(col, col) for col in df.columns})
                    
                    # Handle potential duplicate column names after mapping
                    df = df.loc[:, ~df.columns.duplicated()].copy()
                    
                    # Standardize NOMBRES/APELLIDOS
                    if 'NOMBRES' in df.columns:
                        df['NOMBRES'] = df['NOMBRES'].astype(str).str.strip().str.upper()
                    if 'APELLIDOS' in df.columns:
                        df['APELLIDOS'] = df['APELLIDOS'].astype(str).str.strip().str.upper()
                    
                    # Extract Year/Month from path or filename if possible
                    # Path usually contains the year (e.g., .../2024/...)
                    year_match = re.search(r'\\(\d{4})\\', file_path)
                    if year_match:
                        df['AÑO_DATA'] = int(year_match.group(1))
                    else:
                        # Try filename if path doesn't have it
                        year_match_file = re.search(r'20\d{2}', file)
                        if year_match_file:
                            df['AÑO_DATA'] = int(year_match_file.group(0))
                        else:
                            df['AÑO_DATA'] = datetime.now().year

                    # Extract Month if filename starts with number (e.g., 01 INGRESOS...)
                    month_match = re.search(r'^(\d{2})', file)
                    if month_match:
                        df['MES_DATA'] = int(month_match.group(1))
                    else:
                        df['MES_DATA'] = 1 # Default

                    # Add file source for traceability
                    df['ORIGEN_ARCHIVO'] = file
                    
                    # Filter for essential columns
                    essential_cols = ['NOMBRES', 'APELLIDOS', 'CEDULA', 'EPS', 'MUNICIPIO', 
                                    'FECHA_INICIO', 'FECHA_EGRESO', 'CANTIDAD', 'TIPO_TERAPIA', 
                                    'PROFESIONAL', 'AÑO_DATA', 'MES_DATA', 'ORIGEN_ARCHIVO']
                    
                    # Intersect available columns with essentials
                    cols_to_keep = [c for c in essential_cols if c in df.columns]
                    df = df[cols_to_keep]
                    
                    all_data.append(df)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    if not all_data:
        return pd.DataFrame()

    # Concatenate all
    consolidated_df = pd.concat(all_data, ignore_index=True)
    
    # Final cleanup
    if 'CANTIDAD' in consolidated_df.columns:
        consolidated_df['CANTIDAD'] = pd.to_numeric(consolidated_df['CANTIDAD'], errors='coerce').fillna(0)
    
    if 'FECHA_INICIO' in consolidated_df.columns:
        consolidated_df['FECHA_INICIO'] = pd.to_datetime(consolidated_df['FECHA_INICIO'], errors='coerce')
        
    if 'FECHA_EGRESO' in consolidated_df.columns:
        consolidated_df['FECHA_EGRESO'] = pd.to_datetime(consolidated_df['FECHA_EGRESO'], errors='coerce')
        
    return consolidated_df

@st.cache_data(ttl=3600)
def load_historical_data_db(db_path):
    """
    Carga los datos históricos desde la base de datos SQLite optimizada.
    """
    if not os.path.exists(db_path):
        return pd.DataFrame()
        
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        df = pd.read_sql('SELECT * FROM trazabilidad', conn)
        conn.close()
        
        # Restaurar tipos de fecha que se guardaron como texto
        if 'FECHA_INICIO' in df.columns:
            df['FECHA_INICIO'] = pd.to_datetime(df['FECHA_INICIO'], errors='coerce')
        if 'FECHA_EGRESO' in df.columns:
            df['FECHA_EGRESO'] = pd.to_datetime(df['FECHA_EGRESO'], errors='coerce')
            
        return df
    except Exception as e:
        print(f"Error leyendo DB: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_historical_data_json(json_dir):
    """
    Loads historical data from processed JSON files.
    Much faster and cleaner than scanning raw Excel files.
    """
    if not os.path.exists(json_dir):
        return pd.DataFrame()
    
    all_data = []
    
    # Iterate over all JSON files
    for root, dirs, files in os.walk(json_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Extract records
                    records = data.get('data', [])
                    
                    if records:
                        df = pd.DataFrame(records)
                        
                        # Ensure year_folder is present if not in records but in metadata
                        # Handle cases where year_folder might not be a valid year (e.g., "TRAZABILIDADES", "JULIO")
                        year_value = data.get('year_folder', datetime.now().year)
                        try:
                            df['AÑO_DATA'] = int(year_value)
                        except (ValueError, TypeError):
                            # If year_folder is not numeric, try to extract from filename
                            year_match = re.search(r'20\d{2}', file)
                            if year_match:
                                df['AÑO_DATA'] = int(year_match.group(0))
                            else:
                                # Assign a special year (9999) for files without year info
                                # This allows them to be loaded and filtered separately
                                df['AÑO_DATA'] = 9999
                        
                        # Map JSON keys to Standard Dashboard Columns if needed
                        # Our JSON keys are lowercase (nombres, apellidos, etc.)
                        # Dashboard expects uppercase or specific names? 
                        # Let's standardize to the Dashboard's expected format for compatibility
                        
                        rename_map = {
                            'nombres': 'NOMBRES',
                            'apellidos': 'APELLIDOS',
                            'tipo_id': 'TIPO_ID',
                            'numero_id': 'CEDULA',
                            'eps': 'EPS',
                            'municipio': 'MUNICIPIO',
                            'direccion': 'DIRECCION',
                            'telefono': 'TELEFONO',
                            'fecha_ingreso': 'FECHA_INICIO',
                            'fecha_egreso': 'FECHA_EGRESO',
                            'profesional': 'PROFESIONAL',
                            'observaciones': 'OBSERVACIONES',
                            'sesiones': 'CANTIDAD',
                            'tipo_terapia': 'TIPO_TERAPIA',
                            'diagnostico': 'DIAGNOSTICO',
                            'sheet_name': 'ORIGEN_HOJA'
                        }
                        df = df.rename(columns=rename_map)
                        
                        # Add Source File
                        df['ORIGEN_ARCHIVO'] = data.get('source_file', file)
                        
                        all_data.append(df)
                        
                except Exception as e:
                    st.error(f"Error loading {file}: {e}")
                    
    if not all_data:
        return pd.DataFrame()

    # Concatenate
    consolidated_df = pd.concat(all_data, ignore_index=True)
    
    # Type Conversion
    if 'CANTIDAD' in consolidated_df.columns:
        consolidated_df['CANTIDAD'] = pd.to_numeric(consolidated_df['CANTIDAD'], errors='coerce').fillna(0)
        
    for date_col in ['FECHA_INICIO', 'FECHA_EGRESO']:
        if date_col in consolidated_df.columns:
            consolidated_df[date_col] = pd.to_datetime(consolidated_df[date_col], errors='coerce')
            
            
    # Standardize Text Fields (AGGRESSIVE CLEANING)
    # This removes duplicates caused by spacing, case, and accent variations
    for txt_col in ['NOMBRES', 'APELLIDOS', 'PROFESIONAL', 'EPS', 'MUNICIPIO', 'TIPO_TERAPIA', 'DIAGNOSTICO', 'TIPO_ID']:
        if txt_col in consolidated_df.columns:
            # Convert to string, handle NaN
            consolidated_df[txt_col] = consolidated_df[txt_col].fillna('').astype(str)
            # Remove 'nan' strings
            consolidated_df[txt_col] = consolidated_df[txt_col].replace('nan', '')
            consolidated_df[txt_col] = consolidated_df[txt_col].replace('NAN', '')
            consolidated_df[txt_col] = consolidated_df[txt_col].replace('None', '')
            # Strip whitespace and convert to uppercase
            consolidated_df[txt_col] = consolidated_df[txt_col].str.strip().str.upper()
            # Remove accents (SAHAGÚN -> SAHAGUN, CHINÚ -> CHINU, etc.)
            consolidated_df[txt_col] = consolidated_df[txt_col].apply(lambda x: unidecode(x) if isinstance(x, str) else x)
            # Remove multiple spaces
            consolidated_df[txt_col] = consolidated_df[txt_col].str.replace(r'\s+', ' ', regex=True)
            # Remove leading/trailing spaces again after multi-space removal
            consolidated_df[txt_col] = consolidated_df[txt_col].str.strip()
            # Replace empty strings with NaN for proper handling
            consolidated_df[txt_col] = consolidated_df[txt_col].replace('', pd.NA)
    
    # =========================
    # CORRECCIÓN DE NOMBRES DE MUNICIPIOS
    # =========================
    if 'MUNICIPIO' in consolidated_df.columns:
        # Diccionario de correcciones comunes
        municipio_corrections = {
            # Montería variations
            'MOTERIA': 'MONTERIA',
            'MONRERIA': 'MONTERIA',
            'MNONTERIA': 'MONTERIA',
            'MTR': 'MONTERIA',
            'VEREDAS MONTERIA': 'MONTERIA',
            
            # Tierralta variations
            'TIERRALA': 'TIERRALTA',
            'VIA TIERRALTA': 'TIERRALTA',
            
            # Ciénaga de Oro variations (sin tilde también)
            'CIENEGA DE ORO': 'CIENAGA DE ORO',
            
            # Los Córdobas variations
            'LOS CORDOBAS': 'LOS CORDOBA',
            'TRES PALMAS + LOS CORDOBA': 'LOS CORDOBA',
            
            # La Apartada variations
            'LA APARATADA': 'LA APARTADA',
            'LA APARTADA DE MONTELIBANO': 'LA APARTADA',
            
            # Moñitos variations (after unidecode: Ñ → N)
            'MOÑITO': 'MOÑITOS',
            'MONITO': 'MONITOS',
            
            # Berastegui variations
            'BERASTEGUI': 'BERASTEGUI',
            'BENAVISTA': 'BUENAVISTA',
            
            # Puerto Escondido variations
            'PUERTO ESCONDICO': 'PUERTO ESCONDIDO',
            
            # San Andrés variations
            'SAN ANSAN ANDRES DE SOTAVENTO': 'SAN ANDRES DE SOTAVENTO',
            
            # Planeta Rica variations
            'P. RICA': 'PLANETA RICA',
            'VIA PLANETA': 'PLANETA RICA',
            
            # San Bernardo variations
            'SAN BERNARDO': 'SAN BERNARDO DEL VIENTO',
            
            # Cerete variations
            'CERETE (VEREDA SAN CARLOS)': 'CERETE',
            
            # Via variations
            'VIA SABANAL': 'SAHAGUN',
            
            # Sectores que no son municipios - marcar como inválidos o asignar al municipio padre
            'EL CRUCERO': None,  # Sector, no municipio
            'TRES PALMAS': None,  # Sector, no municipio
            'UNICOR': None,  # EPS, no municipio
            'ARACHE': None,  # Sector/vereda, no municipio
        }
        
        # Aplicar correcciones
        consolidated_df['MUNICIPIO'] = consolidated_df['MUNICIPIO'].replace(municipio_corrections)
        
        # Eliminar registros con municipios inválidos (None)
        consolidated_df = consolidated_df[consolidated_df['MUNICIPIO'].notna()]

    # Extract Month/Year for filtering if dates are missing
    # We trust the folder structure for Year (AÑO_DATA is already set)
    # But Month might need extraction if FECHA_INICIO is null
    # For now, let's rely on FECHA_INICIO for detailed time series, but we can infer month from file names later if needed.
    
    return consolidated_df

def get_rendicion_stats(df):
    """
    Calculates summary stats for Rendición de Cuentas.
    """
    if df.empty:
        return {}
    
    stats = {
        'total_registros': len(df),
        'total_pacientes_unicos': df['CEDULA'].nunique() if 'CEDULA' in df.columns else 0,
        'total_sesiones': df['CANTIDAD'].sum() if 'CANTIDAD' in df.columns else 0,
        'años_disponibles': sorted(df['AÑO_DATA'].unique()) if 'AÑO_DATA' in df.columns else [],
        'eps_dist': df['EPS'].value_counts().to_dict() if 'EPS' in df.columns else {},
        'municipio_dist': df['MUNICIPIO'].value_counts().to_dict() if 'MUNICIPIO' in df.columns else {}
    }
    return stats
