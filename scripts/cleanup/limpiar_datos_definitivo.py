"""
Script de Limpieza Definitiva de Datos
Normaliza EPS, Municipios y reconstruye fechas usando contexto del archivo
"""

import pandas as pd
import json
import re
from datetime import datetime
from unidecode import unidecode

# ============================================================================
# LISTAS MAESTRAS
# ============================================================================

# EPS Normalizadas (mapeo de variaciones a nombre oficial)
EPS_NORMALIZACION = {
    'NUEVA EPS': 'NUEVA EPS',
    'MUTUALSER': 'MUTUALSER',
    'MUTUAL SER': 'MUTUALSER',
    'SALUDTOTAL': 'SALUD TOTAL',
    'SALUD TOTAL': 'SALUD TOTAL',
    'PROMOSALUD': 'PROMOSALUD',
    'SALUDVIDA': 'SALUD VIDA',
    'UNICOR': 'UNICOR',
    'FOMAG': 'FOMAG',
    'SANITAS': 'SANITAS',
    'MEDICINA INTEGRAL': 'MEDICINA INTEGRAL',
    'COLSANITAS': 'COLSANITAS',
    'COOMEVA': 'COOMEVA',
    'COOMEVA PREPAGADA': 'COOMEVA',
    'EPS FAMILIAR DE COLOMBIA': 'EPS FAMILIAR',
    'SURA': 'SURA',
    'SURA PREPAGADA': 'SURA',
    'SURAMERICANA': 'SURA',
    'ALIANSALUD': 'ALIANSALUD',
    'EMDISALUD': 'EMDISALUD',
    'COMFACOR': 'COMFACOR'
}

# Municipios de Córdoba (mapeo de variaciones a nombre oficial)
MUNICIPIOS_NORMALIZACION = {
    'MONTERIA': 'MONTERÍA',
    'VEREDAS MONTERIA': 'MONTERÍA',
    'CERETE': 'CERETÉ',
    'CERETE (VEREDA SAN CARLOS)': 'CERETÉ',
    'SAHAGUN': 'SAHAGÚN',
    'SAHAGÚN': 'SAHAGÚN',
    'VIA SABANAL': 'SAHAGÚN',
    'LORICA': 'LORICA',
    'PLANETA RICA': 'PLANETA RICA',
    'PLANETA  RICA': 'PLANETA RICA',
    'P. RICA': 'PLANETA RICA',
    'VIA PLANETA': 'PLANETA RICA',
    'MONTELIBANO': 'MONTELÍBANO',
    'TIERRALTA': 'TIERRALTA',
    'VIA TIERRALTA': 'TIERRALTA',
    'AYAPEL': 'AYAPEL',
    'PUEBLO NUEVO': 'PUEBLO NUEVO',
    'CIENAGA DE ORO': 'CIÉNAGA DE ORO',
    'CIENEGA DE ORO': 'CIÉNAGA DE ORO',
    'SAN PELAYO': 'SAN PELAYO',
    'COTORRA': 'COTORRA',
    'CHIMA': 'CHIMÁ',
    'SAN BERNARDO': 'SAN BERNARDO DEL VIENTO',
    'SAN BERNARDO DEL VIENTO': 'SAN BERNARDO DEL VIENTO',
    'PUERTO ESCONDIDO': 'PUERTO ESCONDIDO',
    'PUERTO ESCONDICO': 'PUERTO ESCONDIDO',
    'LOS CORDOBA': 'LOS CÓRDOBAS',
    'LOS CORDOBAS': 'LOS CÓRDOBAS',
    'TRES PALMAS  + LOS CORDOBA': 'LOS CÓRDOBAS',
    'SAN ANDRES DE SOTAVENTO': 'SAN ANDRÉS DE SOTAVENTO',
    'MOMIL': 'MOMIL',
    'PURISIMA': 'PURÍSIMA',
    'CHINU': 'CHINÚ',
    'SAN CARLOS': 'SAN CARLOS',
    'BUENAVISTA': 'BUENAVISTA',
    'BENAVISTA': 'BUENAVISTA',
    'LA APARTADA': 'LA APARTADA',
    'LA  APARTADA': 'LA APARTADA',
    'LA APARATADA': 'LA APARTADA',
    'LA APARTADA  DE MONTELIBANO': 'LA APARTADA',
    'MOÑITOS': 'MOÑITOS',
    'PUERTO LIBERTADOR': 'PUERTO LIBERTADOR',
    'SAN ANTERO': 'SAN ANTERO',
    'TUCHIN': 'TUCHÍN',
    'VALENCIA': 'VALENCIA',
    'CANALETE': 'CANALETE',
    'SAN JOSE DE URE': 'SAN JOSÉ DE URÉ',
    'BERASTEGUI': 'BERASTEGUI',  # Sucre, pero aparece en datos
    # Eliminar valores inválidos
    'TRES PALMAS': None,  # Sector, no municipio
    'ARACHE': None,  # Vereda, no municipio
    'EL CRUCERO': None,  # Sector, no municipio
    'NEUROLOGICO': None,  # No es municipio
}

# Meses en español a número
MESES = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
    'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
    'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

# ============================================================================
# FUNCIONES DE LIMPIEZA
# ============================================================================

def normalizar_eps(val):
    """Normaliza nombres de EPS"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip().upper()
    
    # Descartar números puros
    try:
        float(val_str)
        return None
    except:
        pass
    
    # Descartar fechas
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return None
    
    # Buscar en el diccionario de normalización
    if val_str in EPS_NORMALIZACION:
        return EPS_NORMALIZACION[val_str]
    
    # Si no está en el diccionario pero parece válido, retornar como está
    if len(val_str) >= 3:
        return val_str
    
    return None

def normalizar_municipio(val):
    """Normaliza nombres de municipios"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip().upper()
    
    # Remover acentos para comparación
    val_clean = unidecode(val_str)
    
    # Descartar números puros
    try:
        float(val_clean)
        return None
    except:
        pass
    
    # Descartar fechas
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_clean):
        return None
    
    # Buscar en el diccionario de normalización
    if val_clean in MUNICIPIOS_NORMALIZACION:
        normalized = MUNICIPIOS_NORMALIZACION[val_clean]
        return normalized if normalized is not None else None
    
    # Si no está en el diccionario, retornar como está (puede ser válido)
    if len(val_str) >= 3:
        return val_str
    
    return None

def extraer_mes_anio_de_archivo(filename, year_folder):
    """Extrae mes y año del nombre del archivo"""
    # Año
    year = None
    if year_folder and year_folder != '':
        try:
            year = int(year_folder)
        except:
            # Intentar extraer del nombre del archivo
            year_match = re.search(r'20\d{2}', str(filename))
            if year_match:
                year = int(year_match.group(0))
    
    # Mes
    month = None
    filename_upper = str(filename).upper()
    
    # Buscar número de mes al inicio (ej: "01 INGRESOS...")
    month_match = re.match(r'^(\d{2})', filename_upper)
    if month_match:
        month = int(month_match.group(1))
    else:
        # Buscar nombre del mes en el archivo
        for mes_nombre, mes_num in MESES.items():
            if mes_nombre in filename_upper:
                month = mes_num
                break
    
    return year, month

def reconstruir_fecha(val, filename, year_folder, campo):
    """Reconstruye fecha completa usando contexto del archivo"""
    if pd.isna(val) or val == '' or val == 'nan':
        return None
    
    val_str = str(val).strip()
    
    # Si ya es una fecha válida ISO, retornarla
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return val_str
    
    # Si es solo un número (día del mes)
    if re.match(r'^\d{1,2}$', val_str):
        day = int(val_str)
        
        # Validar día
        if day < 1 or day > 31:
            return None
        
        # Obtener mes y año del archivo
        year, month = extraer_mes_anio_de_archivo(filename, year_folder)
        
        if year and month:
            # Para fecha_egreso, si el día es menor que 15, podría ser del mes siguiente
            # Pero por ahora asumimos que es del mismo mes
            try:
                fecha = f"{year}-{month:02d}-{day:02d}"
                # Validar que la fecha sea válida
                datetime.strptime(fecha, '%Y-%m-%d')
                return fecha
            except:
                return None
    
    # Intentar parsear otros formatos
    try:
        # DD/MM/YYYY
        if '/' in val_str:
            parts = val_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year if int(year) < 50 else '19' + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        pass
    
    return None

def limpiar_sesiones(val):
    """Extrae número de sesiones"""
    if pd.isna(val) or val == '':
        return 0
    
    val_str = str(val).strip()
    
    # Si ya es un número, retornarlo
    try:
        return float(val_str)
    except:
        pass
    
    # Extraer números del texto (ej: "30 SESIONES" -> 30)
    numbers = re.findall(r'\d+', val_str)
    if numbers:
        return float(numbers[0])
    
    return 0

def limpiar_texto(val):
    """Limpia campos de texto genéricos"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip()
    
    # Si es una fecha, retornar None
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return None
    
    return val_str

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def limpiar_datos_completo():
    """Limpieza completa de todos los datos"""
    
    input_file = 'data/raw/trazabilidad_consolidada.json'
    output_file = 'data/audit/trazabilidad_consolidada_LIMPIA.json'
    backup_file = 'data/audit/trazabilidad_consolidada_BACKUP.json'
    
    print("="*80)
    print("LIMPIEZA COMPLETA DE DATOS")
    print("="*80)
    
    # Crear backup
    print("\n1. Creando backup...")
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Backup: {backup_file}")
    
    # Cargar datos
    print("\n2. Cargando datos...")
    records = original_data if isinstance(original_data, list) else original_data.get('data', [])
    df = pd.DataFrame(records)
    print(f"   ✓ {len(df)} registros")
    
    # Estadísticas ANTES
    print("\n3. Estadísticas ANTES:")
    print(f"   - EPS únicas: {df['eps'].nunique() if 'eps' in df.columns else 0}")
    print(f"   - Municipios únicos: {df['municipio'].nunique() if 'municipio' in df.columns else 0}")
    print(f"   - Fechas ingreso válidas: {df['fecha_ingreso'].notna().sum() if 'fecha_ingreso' in df.columns else 0}")
    print(f"   - Sesiones válidas: {(df['sesiones'] > 0).sum() if 'sesiones' in df.columns else 0}")
    
    # LIMPIEZA
    print("\n4. Aplicando limpieza...")
    
    # EPS
    if 'eps' in df.columns:
        df['eps'] = df['eps'].apply(normalizar_eps)
        print(f"   ✓ EPS normalizadas: {df['eps'].nunique()} únicas")
    
    # Municipios
    if 'municipio' in df.columns:
        df['municipio'] = df['municipio'].apply(normalizar_municipio)
        print(f"   ✓ Municipios normalizados: {df['municipio'].nunique()} únicos")
    
    # Fechas (con contexto del archivo)
    if 'fecha_ingreso' in df.columns:
        df['fecha_ingreso'] = df.apply(
            lambda row: reconstruir_fecha(
                row['fecha_ingreso'], 
                row.get('source_file', ''), 
                row.get('year_folder', ''),
                'fecha_ingreso'
            ), axis=1
        )
        print(f"   ✓ Fechas ingreso reconstruidas: {df['fecha_ingreso'].notna().sum()}")
    
    if 'fecha_egreso' in df.columns:
        df['fecha_egreso'] = df.apply(
            lambda row: reconstruir_fecha(
                row['fecha_egreso'], 
                row.get('source_file', ''), 
                row.get('year_folder', ''),
                'fecha_egreso'
            ), axis=1
        )
        print(f"   ✓ Fechas egreso reconstruidas: {df['fecha_egreso'].notna().sum()}")
    
    # Sesiones
    if 'sesiones' in df.columns:
        df['sesiones'] = df['sesiones'].apply(limpiar_sesiones)
        print(f"   ✓ Sesiones limpiadas: {(df['sesiones'] > 0).sum()}")
    
    # Otros campos de texto
    for col in ['nombres', 'apellidos', 'direccion', 'telefono', 'profesional', 
                'observaciones', 'diagnostico', 'tipo_terapia']:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_texto)
    
    # Estadísticas DESPUÉS
    print("\n5. Estadísticas DESPUÉS:")
    print(f"   - EPS únicas: {df['eps'].nunique()}")
    print(f"   - Municipios únicos: {df['municipio'].nunique()}")
    print(f"   - Fechas ingreso válidas: {df['fecha_ingreso'].notna().sum()}")
    print(f"   - Fechas egreso válidas: {df['fecha_egreso'].notna().sum()}")
    print(f"   - Sesiones válidas: {(df['sesiones'] > 0).sum()}")
    
    # Guardar
    print("\n6. Guardando datos limpios...")
    df_clean = df.where(pd.notna(df), None)
    records_clean = df_clean.to_dict('records')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records_clean, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Guardado: {output_file}")
    
    # Reporte
    print("\n7. Generando reporte...")
    
    report = {
        'fecha': datetime.now().isoformat(),
        'registros_procesados': len(df),
        'eps_unicas': int(df['eps'].nunique()),
        'municipios_unicos': int(df['municipio'].nunique()),
        'top_eps': df['eps'].value_counts().head(10).to_dict(),
        'top_municipios': df['municipio'].value_counts().head(10).to_dict(),
        'estadisticas': {
            'fechas_ingreso_validas': int(df['fecha_ingreso'].notna().sum()),
            'fechas_egreso_validas': int(df['fecha_egreso'].notna().sum()),
            'sesiones_validas': int((df['sesiones'] > 0).sum())
        }
    }
    
    with open('data/audit/limpieza_reporte.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Reporte: data/audit/limpieza_reporte.json")
    
    print("\n" + "="*80)
    print("✅ LIMPIEZA COMPLETADA")
    print("="*80)
    print(f"\nArchivos generados:")
    print(f"  1. {backup_file}")
    print(f"  2. {output_file}")
    print(f"  3. data/audit/limpieza_reporte.json")
    print()

if __name__ == "__main__":
    limpiar_datos_completo()
