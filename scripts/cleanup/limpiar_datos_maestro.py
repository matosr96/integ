"""
Script de Limpieza Definitiva con Listas Maestras Oficiales
- 28 EPS autorizadas en Colombia (2024-2025)
- 30 Municipios oficiales de Córdoba
- Normalización inteligente con fuzzy matching
"""

import pandas as pd
import json
import re
from datetime import datetime
from unidecode import unidecode
from difflib import get_close_matches

# ============================================================================
# LISTAS MAESTRAS OFICIALES
# ============================================================================

# 28 EPS AUTORIZADAS EN COLOMBIA (2024-2025)
EPS_OFICIALES = [
    # Régimen Contributivo y Subsidiado
    'COOSALUD',
    'NUEVA EPS',
    'MUTUAL SER',
    # Régimen Contributivo
    'ALIANSALUD',
    'SALUD TOTAL',
    'SANITAS',
    'SURA',
    'FAMISANAR',
    'SOS',  # Servicio Occidental de Salud
    'COMFENALCO VALLE',
    'COMPENSAR',
    'EPM',  # Empresas Públicas de Medellín
    'FONDO DE PASIVO SOCIAL FERROCARRILES',
    'SALUD MIA',
    # Régimen Subsidiado
    'CAJACOPI ATLANTICO',
    'CAPRESOCA',
    'COMFACHOCO',
    'COMFAORIENTE',
    'EPS FAMILIAR',
    'ASMET SALUD',
    'EMSSANAR',
    'CAPITAL SALUD',
    'SAVIA SALUD',
    'DUSAKAWI',
    'ASOCIACION INDIGENA DEL CAUCA',
    'ANAS WAYUU',
    'MALLAMAS',
    'PIJAOS SALUD',
    'SALUD BOLIVAR',
    # Otras comunes en Córdoba
    'COMFACOR',
    'FOMAG',
    'MEDICINA INTEGRAL',
    'COLSANITAS',
    'COOMEVA',
    'PROMOSALUD',
    'SALUDVIDA',
    'UNICOR',
    'EMDISALUD',
    'AXACOLPATRIA',
    'COLMENA',
    'COLMEDICA',
    'PARTICULAR',
    'GRUPO VIVIR',
    'CLINICA UNIVERSITARIA'
]

# 30 MUNICIPIOS OFICIALES DE CÓRDOBA
MUNICIPIOS_OFICIALES = [
    'AYAPEL',
    'BUENAVISTA',
    'CANALETE',
    'CERETÉ',
    'CHIMÁ',
    'CHINÚ',
    'CIÉNAGA DE ORO',
    'COTORRA',
    'LA APARTADA',
    'LOS CÓRDOBAS',
    'MOMIL',
    'MONTELÍBANO',
    'MONTERÍA',
    'MOÑITOS',
    'PLANETA RICA',
    'PUEBLO NUEVO',
    'PUERTO ESCONDIDO',
    'PUERTO LIBERTADOR',
    'PURÍSIMA',
    'SAHAGÚN',
    'SAN ANDRÉS DE SOTAVENTO',
    'SAN ANTERO',
    'SAN BERNARDO DEL VIENTO',
    'SAN CARLOS',
    'SAN JOSÉ DE URÉ',
    'SAN PELAYO',
    'SANTA CRUZ DE LORICA',  # Nombre oficial completo
    'TIERRALTA',
    'TUCHÍN',
    'VALENCIA'
]

# Crear versiones sin acentos para matching
EPS_OFICIALES_NORMALIZED = [unidecode(eps).upper() for eps in EPS_OFICIALES]
MUNICIPIOS_OFICIALES_NORMALIZED = [unidecode(mun).upper() for mun in MUNICIPIOS_OFICIALES]

# Diccionario de mapeo EPS (variaciones conocidas -> oficial)
EPS_VARIACIONES = {
    'MUTUALSER': 'MUTUAL SER',
    'SALUDTOTAL': 'SALUD TOTAL',
    'SALUD VIDA': 'SALUDVIDA',
    'COOMEVA PREPAGADA': 'COOMEVA',
    'SURA PREPAGADA': 'SURA',
    'SURAMERICANA': 'SURA',
    'EPS FAMILIAR DE COLOMBIA': 'EPS FAMILIAR',
    'SERVICIO OCCIDENTAL DE SALUD': 'SOS',
    'EMPRESAS PUBLICAS DE MEDELLIN': 'EPM',
    'AXA COLPATRIA': 'AXACOLPATRIA',
    'AXA': 'AXACOLPATRIA',
    'COLPATRIA': 'AXACOLPATRIA',
    'FAMILIAR DE COLOMBIA': 'EPS FAMILIAR',
    'UNICORDOBA': 'UNICOR',
    'PROMOSALUD-COOMEVA': 'PROMOSALUD',
    'CLINICA UNIVERSITARIA': 'UNICOR',
}

# Diccionario de mapeo Municipios (variaciones conocidas -> oficial)
MUNICIPIOS_VARIACIONES = {
    'MONTERIA': 'MONTERÍA',
    'VEREDAS MONTERIA': 'MONTERÍA',
    'CERETE': 'CERETÉ',
    'CERETE (VEREDA SAN CARLOS)': 'CERETÉ',
    'SAHAGUN': 'SAHAGÚN',
    'VIA SABANAL': 'SAHAGÚN',
    'LORICA': 'SANTA CRUZ DE LORICA',
    'PLANETA  RICA': 'PLANETA RICA',
    'P. RICA': 'PLANETA RICA',
    'VIA PLANETA': 'PLANETA RICA',
    'MONTELIBANO': 'MONTELÍBANO',
    'VIA TIERRALTA': 'TIERRALTA',
    'CIENAGA DE ORO': 'CIÉNAGA DE ORO',
    'CIENEGA DE ORO': 'CIÉNAGA DE ORO',
    'CHIMA': 'CHIMÁ',
    'CHINU': 'CHINÚ',
    'SAN BERNARDO': 'SAN BERNARDO DEL VIENTO',
    'PUERTO ESCONDICO': 'PUERTO ESCONDIDO',
    'LOS CORDOBA': 'LOS CÓRDOBAS',
    'TRES PALMAS  + LOS CORDOBA': 'LOS CÓRDOBAS',
    'SAN ANDRES DE SOTAVENTO': 'SAN ANDRÉS DE SOTAVENTO',
    'PURISIMA': 'PURÍSIMA',
    'LA  APARTADA': 'LA APARTADA',
    'LA APARATADA': 'LA APARTADA',
    'LA APARTADA  DE MONTELIBANO': 'LA APARTADA',
    'MOÑITO': 'MOÑITOS',
    'TUCHIN': 'TUCHÍN',
    'SAN JOSE DE URE': 'SAN JOSÉ DE URÉ',
    'BENAVISTA': 'BUENAVISTA',
    # Corregimientos y sectores de Montería
    'TRES PALMAS': 'MONTERÍA',
    '3 PALMAS': 'MONTERÍA',
    'KM 8 VDA LAS PULGAS': 'MONTERÍA',
    'KM 8': 'MONTERÍA',
    'BARRIO SAN JOSE': 'MONTERÍA',
    'SAN JOSE': 'MONTERÍA',
    'GALILEA': 'MONTERÍA',
    'EL RECUERDO': 'MONTERÍA',
    'LOS RECUERDOS': 'MONTERÍA',
    'MI REFUGIO': 'MONTERÍA',
    'KM 7 VIA CERETE': 'MONTERÍA',
    'KM 7': 'MONTERÍA',
    'EDIFICIO INDIGO': 'MONTERÍA',
    'INDIGO': 'MONTERÍA',
    'BONANZA': 'MONTERÍA',
    '6 DE MARZO': 'MONTERÍA',
    # Municipios fuera de Córdoba donde se prestaron servicios
    'CAUCASIA': 'CAUCASIA',
    # Valores inválidos (no son municipios)
    'ARACHE': None,
    'EL CRUCERO': None,
    'NEUROLOGICO': None,
    'ARBOLETES': None,
    'SAMPUES': None,
    'BERASTEGUI': None,
    'BELLO': None,
}

# Meses en español
MESES = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
    'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
    'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

# ============================================================================
# FUNCIONES DE NORMALIZACIÓN INTELIGENTE
# ============================================================================

def normalizar_eps_inteligente(val):
    """Normaliza EPS usando lista oficial y fuzzy matching"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip().upper()
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
    
    # Muy corto
    if len(val_clean) < 3:
        return None
    
    # 1. Buscar en variaciones conocidas
    if val_clean in EPS_VARIACIONES:
        return EPS_VARIACIONES[val_clean]
    
    # 2. Buscar coincidencia exacta en lista oficial
    if val_clean in EPS_OFICIALES_NORMALIZED:
        idx = EPS_OFICIALES_NORMALIZED.index(val_clean)
        return EPS_OFICIALES[idx]
    
    # 3. Fuzzy matching (buscar similares)
    matches = get_close_matches(val_clean, EPS_OFICIALES_NORMALIZED, n=1, cutoff=0.8)
    if matches:
        idx = EPS_OFICIALES_NORMALIZED.index(matches[0])
        return EPS_OFICIALES[idx]
    
    # 4. Si contiene palabras clave de EPS conocidas
    for eps_oficial in EPS_OFICIALES:
        eps_words = eps_oficial.split()
        val_words = val_clean.split()
        # Si comparten al menos 2 palabras significativas
        common_words = set(eps_words) & set(val_words)
        if len(common_words) >= 2 or (len(common_words) >= 1 and len(eps_words) == 1):
            return eps_oficial
    
    # 5. Si no se encuentra, retornar None (será marcado para revisión)
    return None

def normalizar_municipio_inteligente(val):
    """Normaliza municipios usando lista oficial y fuzzy matching"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip().upper()
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
    
    # Muy corto
    if len(val_clean) < 3:
        return None
    
    # 1. Buscar en variaciones conocidas
    if val_clean in MUNICIPIOS_VARIACIONES:
        return MUNICIPIOS_VARIACIONES[val_clean]
    
    # 2. Buscar coincidencia exacta en lista oficial
    if val_clean in MUNICIPIOS_OFICIALES_NORMALIZED:
        idx = MUNICIPIOS_OFICIALES_NORMALIZED.index(val_clean)
        return MUNICIPIOS_OFICIALES[idx]
    
    # 3. Fuzzy matching (buscar similares)
    matches = get_close_matches(val_clean, MUNICIPIOS_OFICIALES_NORMALIZED, n=1, cutoff=0.85)
    if matches:
        idx = MUNICIPIOS_OFICIALES_NORMALIZED.index(matches[0])
        return MUNICIPIOS_OFICIALES[idx]
    
    # 4. Buscar si contiene el nombre del municipio
    for mun_oficial in MUNICIPIOS_OFICIALES:
        mun_clean = unidecode(mun_oficial).upper()
        if mun_clean in val_clean or val_clean in mun_clean:
            return mun_oficial
    
    # 5. Si no se encuentra, retornar None
    return None

def extraer_mes_anio_de_archivo(filename, year_folder):
    """Extrae mes y año del nombre del archivo"""
    year = None
    if year_folder and year_folder != '':
        try:
            year = int(year_folder)
        except:
            year_match = re.search(r'20\d{2}', str(filename))
            if year_match:
                year = int(year_match.group(0))
    
    month = None
    filename_upper = str(filename).upper()
    
    # Buscar número de mes al inicio
    month_match = re.match(r'^(\d{2})', filename_upper)
    if month_match:
        month = int(month_match.group(1))
    else:
        # Buscar nombre del mes
        for mes_nombre, mes_num in MESES.items():
            if mes_nombre in filename_upper:
                month = mes_num
                break
    
    return year, month

def reconstruir_fecha(val, filename, year_folder):
    """Reconstruye fecha completa usando contexto del archivo"""
    if pd.isna(val) or val == '' or val == 'nan':
        return None
    
    val_str = str(val).strip()
    
    # Si ya es una fecha válida ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return val_str
    
    # Si es solo un número (día del mes)
    if re.match(r'^\d{1,2}$', val_str):
        day = int(val_str)
        
        if day < 1 or day > 31:
            return None
        
        year, month = extraer_mes_anio_de_archivo(filename, year_folder)
        
        if year and month:
            try:
                fecha = f"{year}-{month:02d}-{day:02d}"
                datetime.strptime(fecha, '%Y-%m-%d')
                return fecha
            except:
                return None
    
    # Intentar parsear DD/MM/YYYY
    try:
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
    
    try:
        return float(val_str)
    except:
        pass
    
    numbers = re.findall(r'\d+', val_str)
    if numbers:
        return float(numbers[0])
    
    return 0

def limpiar_texto(val):
    """Limpia campos de texto genéricos"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip()
    
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return None
    
    return val_str

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def limpiar_datos_maestro():
    """Limpieza completa con listas maestras oficiales"""
    
    input_file = 'data/audit/trazabilidad_consolidada.json'
    output_file = 'data/processed/trazabilidad_LIMPIA.json'
    backup_file = 'data/audit/trazabilidad_BACKUP.json'
    
    print("="*80)
    print("LIMPIEZA CON LISTAS MAESTRAS OFICIALES")
    print("="*80)
    print(f"EPS Oficiales: {len(EPS_OFICIALES)}")
    print(f"Municipios Oficiales: {len(MUNICIPIOS_OFICIALES)}")
    
    # Backup
    print("\n1. Creando backup...")
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {backup_file}")
    
    # Cargar
    print("\n2. Cargando datos...")
    records = original_data if isinstance(original_data, list) else original_data.get('data', [])
    df = pd.DataFrame(records)
    print(f"   ✓ {len(df)} registros")
    
    # Estadísticas ANTES
    print("\n3. ANTES de limpieza:")
    eps_antes = df['eps'].nunique() if 'eps' in df.columns else 0
    mun_antes = df['municipio'].nunique() if 'municipio' in df.columns else 0
    print(f"   - EPS únicas: {eps_antes}")
    print(f"   - Municipios únicos: {mun_antes}")
    
    # LIMPIEZA
    print("\n4. Normalizando datos...")
    
    # EPS
    if 'eps' in df.columns:
        df['eps_original'] = df['eps']  # Guardar original para auditoría
        df['eps'] = df['eps'].apply(normalizar_eps_inteligente)
        eps_validas = df['eps'].notna().sum()
        eps_unicas = df['eps'].nunique()
        print(f"   ✓ EPS: {eps_validas} válidas, {eps_unicas} únicas")
    
    # Municipios
    if 'municipio' in df.columns:
        df['municipio_original'] = df['municipio']  # Guardar original
        df['municipio'] = df['municipio'].apply(normalizar_municipio_inteligente)
        mun_validos = df['municipio'].notna().sum()
        mun_unicos = df['municipio'].nunique()
        print(f"   ✓ Municipios: {mun_validos} válidos, {mun_unicos} únicos")
    
    # Fechas
    if 'fecha_ingreso' in df.columns:
        df['fecha_ingreso'] = df.apply(
            lambda row: reconstruir_fecha(
                row['fecha_ingreso'],
                row.get('source_file', ''),
                row.get('year_folder', '')
            ), axis=1
        )
        print(f"   ✓ Fechas ingreso: {df['fecha_ingreso'].notna().sum()}")
    
    if 'fecha_egreso' in df.columns:
        df['fecha_egreso'] = df.apply(
            lambda row: reconstruir_fecha(
                row['fecha_egreso'],
                row.get('source_file', ''),
                row.get('year_folder', '')
            ), axis=1
        )
        print(f"   ✓ Fechas egreso: {df['fecha_egreso'].notna().sum()}")
    
    # Sesiones
    if 'sesiones' in df.columns:
        df['sesiones'] = df['sesiones'].apply(limpiar_sesiones)
        print(f"   ✓ Sesiones: {(df['sesiones'] > 0).sum()}")
    
    # Otros campos
    for col in ['nombres', 'apellidos', 'direccion', 'telefono', 'profesional',
                'observaciones', 'diagnostico', 'tipo_terapia']:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_texto)
    
    # Estadísticas DESPUÉS
    print("\n5. DESPUÉS de limpieza:")
    print(f"   - EPS únicas: {df['eps'].nunique()}")
    print(f"   - Municipios únicos: {df['municipio'].nunique()}")
    print(f"   - Fechas ingreso: {df['fecha_ingreso'].notna().sum()}")
    print(f"   - Sesiones válidas: {(df['sesiones'] > 0).sum()}")
    
    # Separar registros válidos e inválidos
    print("\n6. Separando registros válidos e inválidos...")
    
    # Registros válidos: tienen EPS Y municipio válidos
    df_validos = df[(df['eps'].notna()) & (df['municipio'].notna())].copy()
    
    # Registros rechazados: EPS o municipio inválido
    df_rechazados = df[(df['eps'].isna()) | (df['municipio'].isna())].copy()
    
    print(f"   ✓ Válidos: {len(df_validos)} registros")
    print(f"   ✓ Rechazados: {len(df_rechazados)} registros")
    
    # Guardar registros válidos
    print("\n7. Guardando registros válidos...")
    df_validos_clean = df_validos.where(pd.notna(df_validos), None)
    records_validos = df_validos_clean.to_dict('records')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records_validos, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {output_file}")
    
    # Guardar registros rechazados para revisión
    if len(df_rechazados) > 0:
        print("\n8. Guardando registros rechazados para revisión...")
        
        rechazados_file = 'data/audit/registros_RECHAZADOS.json'
        df_rechazados_clean = df_rechazados.where(pd.notna(df_rechazados), None)
        records_rechazados = df_rechazados_clean.to_dict('records')
        
        # Agregar razón del rechazo
        for record in records_rechazados:
            razones = []
            if not record.get('eps'):
                razones.append(f"EPS inválida: {record.get('eps_original', 'N/A')}")
            if not record.get('municipio'):
                razones.append(f"Municipio inválido: {record.get('municipio_original', 'N/A')}")
            record['razon_rechazo'] = ' | '.join(razones)
        
        with open(rechazados_file, 'w', encoding='utf-8') as f:
            json.dump(records_rechazados, f, indent=2, ensure_ascii=False)
        
        print(f"   ✓ {rechazados_file}")
        print(f"   ℹ️  Estos registros requieren revisión manual")
    
    # Reporte detallado
    print("\n9. Generando reporte...")
    
    report = {
        'fecha_limpieza': datetime.now().isoformat(),
        'registros_procesados': len(df),
        'registros_validos': len(df_validos),
        'registros_rechazados': len(df_rechazados),
        'eps': {
            'antes': eps_antes,
            'despues': int(df_validos['eps'].nunique()),
            'top_10': df_validos['eps'].value_counts().head(10).to_dict()
        },
        'municipios': {
            'antes': mun_antes,
            'despues': int(df_validos['municipio'].nunique()),
            'top_10': df_validos['municipio'].value_counts().head(10).to_dict()
        },
        'fechas': {
            'ingreso_validas': int(df_validos['fecha_ingreso'].notna().sum()),
            'egreso_validas': int(df_validos['fecha_egreso'].notna().sum())
        },
        'sesiones_validas': int((df_validos['sesiones'] > 0).sum()),
        'rechazos_por_razon': {
            'eps_invalida': int((df['eps'].isna()).sum()),
            'municipio_invalido': int((df['municipio'].isna()).sum())
        }
    }
    
    with open('data/audit/reporte_limpieza.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/audit/reporte_limpieza.json")
    
    print("\n" + "="*80)
    print("✅ LIMPIEZA COMPLETADA")
    print("="*80)
    print(f"\nResultados:")
    print(f"  📊 Total procesados: {len(df):,}")
    print(f"  ✅ Válidos: {len(df_validos):,} ({len(df_validos)/len(df)*100:.1f}%)")
    print(f"  ⚠️  Rechazados: {len(df_rechazados):,} ({len(df_rechazados)/len(df)*100:.1f}%)")
    print(f"\nMejoras:")
    print(f"  EPS: {eps_antes} → {df_validos['eps'].nunique()} únicas")
    print(f"  Municipios: {mun_antes} → {df_validos['municipio'].nunique()} únicos")
    print(f"\nArchivos generados:")
    print(f"  1. {output_file} - Datos limpios y válidos")
    print(f"  2. data/audit/registros_RECHAZADOS.json - Para revisión manual")
    print(f"  3. {backup_file} - Backup original")
    print()

if __name__ == "__main__":
    limpiar_datos_maestro()
