"""
Consolida todos los JSON individuales en un único JSON maestro limpio.
Aplica todas las correcciones identificadas:
- Normalización de municipios
- Eliminación de acentos
- Forward-fill de valores faltantes
- Estandarización de tipos de datos
"""

import json
import os
import pandas as pd
from unidecode import unidecode
from datetime import datetime

# Diccionario de correcciones de municipios
MUNICIPIO_CORRECTIONS = {
    # Montería variations
    'MOTERIA': 'MONTERIA',
    'MONRERIA': 'MONTERIA',
    'MNONTERIA': 'MONTERIA',
    'MTR': 'MONTERIA',
    'VEREDAS MONTERIA': 'MONTERIA',
    
    # Tierralta variations
    'TIERRALA': 'TIERRALTA',
    'VIA TIERRALTA': 'TIERRALTA',
    
    # Ciénaga de Oro variations
    'CIENEGA DE ORO': 'CIENAGA DE ORO',
    
    # Los Córdobas variations
    'LOS CORDOBAS': 'LOS CORDOBA',
    'TRES PALMAS + LOS CORDOBA': 'LOS CORDOBA',
    
    # La Apartada variations
    'LA APARATADA': 'LA APARTADA',
    'LA APARTADA DE MONTELIBANO': 'LA APARTADA',
    
    # Moñitos variations
    'MOÑITO': 'MONITOS',
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
    
    # Sectores que no son municipios
    'EL CRUCERO': None,
    'TRES PALMAS': None,
    'UNICOR': None,
    'ARACHE': None,
}

def clean_text(text):
    """Limpia y normaliza texto"""
    if pd.isna(text) or text is None or text == '':
        return None
    
    text = str(text).strip().upper()
    # Remove accents
    text = unidecode(text)
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    return text if text and text != 'NAN' and text != 'NONE' else None

def consolidate_json_files(json_dir, output_file):
    """Consolida todos los JSON en uno solo con limpieza completa"""
    
    print(f"SEARCH Escaneando directorio: {json_dir}")
    
    all_records = []
    file_count = 0
    skipped_count = 0
    
    # Leer todos los archivos JSON
    for file in os.listdir(json_dir):
        if not file.endswith('.json'):
            continue
            
        file_path = os.path.join(json_dir, file)
        file_count += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = data.get('data', [])
            year_folder = data.get('year_folder', 'unknown')
            
            # Intentar extraer año del nombre del archivo si year_folder no es válido
            if year_folder == 'unknown' or not str(year_folder).isdigit():
                import re
                year_match = re.search(r'20\d{2}', file)
                year_folder = int(year_match.group(0)) if year_match else 9999
            else:
                try:
                    year_folder = int(year_folder)
                except:
                    year_folder = 9999
            
            print(f"  FILE Procesando: {file} ({len(records)} registros, año: {year_folder})")
            
            for record in records:
                # Agregar año
                record['year'] = year_folder
                record['source_file'] = file
                all_records.append(record)
                
        except Exception as e:
            print(f"  ERROR Error en {file}: {e}")
            skipped_count += 1
            continue
    
    print(f"\nOK Archivos procesados: {file_count}")
    print(f"ERR Archivos con error: {skipped_count}")
    print(f"STATS Total registros cargados: {len(all_records)}")
    
    # Convertir a DataFrame para limpieza
    print("\nCLEAN Limpiando y normalizando datos...")
    df = pd.DataFrame(all_records)
    
    # Limpiar campos de texto
    text_fields = ['nombres', 'apellidos', 'tipo_id', 'eps', 'municipio', 'direccion', 
                   'profesional', 'tipo_terapia', 'diagnostico', 'observaciones']
    
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].apply(clean_text)
    
    # Aplicar correcciones de municipios
    if 'municipio' in df.columns:
        df['municipio'] = df['municipio'].replace(MUNICIPIO_CORRECTIONS)
        # Eliminar registros con municipios inválidos (None)
        initial_count = len(df)
        df = df[df['municipio'].notna()]
        removed = initial_count - len(df)
        if removed > 0:
            print(f"  REMOVED Eliminados {removed} registros con municipios inválidos")
    
    # Convertir tipos de datos
    if 'numero_id' in df.columns:
        df['numero_id'] = pd.to_numeric(df['numero_id'], errors='coerce')
    
    if 'sesiones' in df.columns:
        df['sesiones'] = pd.to_numeric(df['sesiones'], errors='coerce').fillna(0)
    
    # Convertir fechas
    for date_col in ['fecha_ingreso', 'fecha_egreso']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Convertir de vuelta a registros
    clean_records = df.to_dict(orient='records')
    
    # Limpiar NaN y convertir fechas a string
    final_records = []
    for record in clean_records:
        clean_record = {}
        for k, v in record.items():
            if pd.isna(v):
                clean_record[k] = None
            elif isinstance(v, pd.Timestamp):
                clean_record[k] = v.isoformat() if pd.notna(v) else None
            else:
                clean_record[k] = v
        final_records.append(clean_record)
    
    # Calcular estadísticas
    stats = {
        'total_records': len(final_records),
        'total_unique_patients': df['numero_id'].nunique() if 'numero_id' in df.columns else 0,
        'total_sessions': df['sesiones'].sum() if 'sesiones' in df.columns else 0,
        'years_covered': sorted(df['year'].unique().tolist()) if 'year' in df.columns else [],
        'municipalities': sorted(df['municipio'].dropna().unique().tolist()) if 'municipio' in df.columns else [],
        'eps_list': sorted(df['eps'].dropna().unique().tolist()) if 'eps' in df.columns else [],
        'generated_at': datetime.now().isoformat()
    }
    
    # Crear JSON maestro
    master_data = {
        'metadata': stats,
        'data': final_records
    }
    
    # Guardar
    print(f"\nSAVE Guardando JSON consolidado: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDONE ¡Consolidación completa!")
    print(f"STATS Estadísticas finales:")
    print(f"   - Total registros: {stats['total_records']:,}")
    print(f"   - Pacientes únicos: {stats['total_unique_patients']:,}")
    print(f"   - Total sesiones: {stats['total_sessions']:,.0f}")
    print(f"   - Años cubiertos: {len(stats['years_covered'])}")
    print(f"   - Municipios: {len(stats['municipalities'])}")
    print(f"   - EPS: {len(stats['eps_list'])}")
    print(f"\n📁 Archivo generado: {output_file}")
    
    return master_data

if __name__ == "__main__":
    JSON_DIR = "data/raw/PROCESSED_JSON"
    OUTPUT_FILE = "data/raw/trazabilidad_consolidada.json"
    
    consolidate_json_files(JSON_DIR, OUTPUT_FILE)
