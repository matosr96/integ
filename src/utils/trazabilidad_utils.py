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
                    year_match = re.search(r'\\(\d{4})\\', file_path)
                    if year_match:
                        df['AÑO_DATA'] = int(year_match.group(1))
                    else:
                        year_match_file = re.search(r'20\d{2}', file)
                        if year_match_file:
                            df['AÑO_DATA'] = int(year_match_file.group(0))
                        else:
                            df['AÑO_DATA'] = datetime.now().year

                    # Extract Month if filename starts with number
                    month_match = re.search(r'^(\d{2})', file)
                    if month_match:
                        df['MES_DATA'] = int(month_match.group(1))
                    else:
                        df['MES_DATA'] = 1 

                    # Add file source for traceability
                    df['ORIGEN_ARCHIVO'] = file
                    
                    # Filter for essential columns
                    essential_cols = ['NOMBRES', 'APELLIDOS', 'CEDULA', 'EPS', 'MUNICIPIO', 
                                    'FECHA_INICIO', 'FECHA_EGRESO', 'CANTIDAD', 'TIPO_TERAPIA', 
                                    'PROFESIONAL', 'AÑO_DATA', 'MES_DATA', 'ORIGEN_ARCHIVO']
                    
                    cols_to_keep = [c for c in essential_cols if c in df.columns]
                    df = df[cols_to_keep]
                    
                    all_data.append(df)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    if not all_data:
        return pd.DataFrame()

    consolidated_df = pd.concat(all_data, ignore_index=True)
    
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
        
        if 'FECHA_INICIO' in df.columns:
            df['FECHA_INICIO'] = pd.to_datetime(df['FECHA_INICIO'], errors='coerce')
        if 'FECHA_EGRESO' in df.columns:
            df['FECHA_EGRESO'] = pd.to_datetime(df['FECHA_EGRESO'], errors='coerce')
            
        return df
    except Exception as e:
        print(f"Error leyendo DB: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_historical_data_json(path):
    """
    Carga datos históricos desde archivos JSON individuales o un archivo consolidado.
    Realiza normalización automática de columnas.
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    
    all_data = []

    # Rename map para normalizar claves de JSON a columnas del Dashboard
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

    # PROCESAMIENTO
    if os.path.isfile(path):
        # Caso 1: Archivo único (.json)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            if records:
                if isinstance(records, list):
                    df = pd.DataFrame(records)
                elif isinstance(records, dict) and 'data' in records:
                    df = pd.DataFrame(records['data'])
                else:
                    return pd.DataFrame()
                
                df = df.rename(columns=rename_map)
                all_data.append(df)
        except Exception as e:
            st.error(f"Error cargando JSON consolidado: {e}")
            return pd.DataFrame()
    else:
        # Caso 2: Directorio de archivos JSON
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        records = data.get('data', [])
                        if records:
                            df = pd.DataFrame(records)
                            
                            # Intentar obtener año de metadatos o nombre de archivo
                            year_val = data.get('year_folder')
                            if not year_val:
                                y_match = re.search(r'20\d{2}', file)
                                year_val = y_match.group(0) if y_match else datetime.now().year
                            
                            df['AÑO_DATA'] = int(year_val)
                            df['ORIGEN_ARCHIVO'] = data.get('source_file', file)
                            df = df.rename(columns=rename_map)
                            all_data.append(df)
                    except Exception as e:
                        print(f"Error cargando {file}: {e}")

    if not all_data:
        return pd.DataFrame()

    consolidated_df = pd.concat(all_data, ignore_index=True)
    
    # --- PROCESAMIENTO FINAL ---
    
    # 1. Asegurar AÑO_DATA si falta
    if 'AÑO_DATA' not in consolidated_df.columns:
        if 'FECHA_INICIO' in consolidated_df.columns:
            temp_dates = pd.to_datetime(consolidated_df['FECHA_INICIO'], errors='coerce')
            consolidated_df['AÑO_DATA'] = temp_dates.dt.year.fillna(datetime.now().year).astype(int)
        else:
            consolidated_df['AÑO_DATA'] = datetime.now().year

    # 2. Conversiones de tipos
    if 'CANTIDAD' in consolidated_df.columns:
        consolidated_df['CANTIDAD'] = pd.to_numeric(consolidated_df['CANTIDAD'], errors='coerce').fillna(0)
        
    for date_col in ['FECHA_INICIO', 'FECHA_EGRESO']:
        if date_col in consolidated_df.columns:
            consolidated_df[date_col] = pd.to_datetime(consolidated_df[date_col], errors='coerce')
            
    # 3. Limpieza Agresiva de Texto
    text_cols = ['NOMBRES', 'APELLIDOS', 'PROFESIONAL', 'EPS', 'MUNICIPIO', 'TIPO_TERAPIA', 'DIAGNOSTICO', 'TIPO_ID']
    for txt_col in text_cols:
        if txt_col in consolidated_df.columns:
            consolidated_df[txt_col] = consolidated_df[txt_col].fillna('').astype(str).str.strip().str.upper()
            consolidated_df[txt_col] = consolidated_df[txt_col].replace(['NAN', 'NONE', 'nan', 'none', ''], pd.NA)
            # Quitar acentos
            consolidated_df[txt_col] = consolidated_df[txt_col].apply(lambda x: unidecode(x) if isinstance(x, str) else x)
            # Quitar múltiples espacios
            consolidated_df[txt_col] = consolidated_df[txt_col].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # 4. Correcciones Geográficas
    if 'MUNICIPIO' in consolidated_df.columns:
        corrections = {
            'MOTERIA': 'MONTERIA', 'MONRERIA': 'MONTERIA', 'MNONTERIA': 'MONTERIA',
            'TIERRALA': 'TIERRALTA', 'CIENEGA DE ORO': 'CIENAGA DE ORO',
            'LOS CORDOBAS': 'LOS CORDOBA', 'MOÑITO': 'MOÑITOS', 'MONITO': 'MOÑITOS'
        }
        consolidated_df['MUNICIPIO'] = consolidated_df['MUNICIPIO'].replace(corrections)

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
        'años_disponibles': sorted([int(y) for y in df['AÑO_DATA'].unique() if pd.notna(y)]) if 'AÑO_DATA' in df.columns else [],
        'eps_dist': df['EPS'].value_counts().to_dict() if 'EPS' in df.columns else {},
        'municipio_dist': df['MUNICIPIO'].value_counts().to_dict() if 'MUNICIPIO' in df.columns else {}
    }
    return stats
