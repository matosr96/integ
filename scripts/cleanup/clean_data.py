"""
Script de Limpieza de Datos - Sistema de Gestión Terapéutica
Corrige automáticamente todos los errores de tipo de datos encontrados
"""

import pandas as pd
import json
import re
from datetime import datetime
import os

def clean_sesiones(val):
    """Extrae el número de sesiones del texto"""
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

def clean_fecha(val):
    """Limpia y valida fechas"""
    if pd.isna(val) or val == '' or val == 'nan':
        return None
    
    val_str = str(val).strip()
    
    # Si ya es una fecha válida ISO, retornarla
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return val_str
    
    # Si es solo un número (día del mes), no es una fecha válida completa
    if re.match(r'^\d{1,2}$', val_str):
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

def clean_text_field(val):
    """Limpia campos de texto, removiendo números puros o fechas"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip()
    
    # Si es un número puro, retornar None
    try:
        float(val_str)
        return None
    except:
        pass
    
    # Si es una fecha, retornar None
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return None
    
    return val_str

def clean_telefono(val):
    """Limpia números de teléfono"""
    if pd.isna(val) or val == '':
        return None
    
    val_str = str(val).strip()
    
    # Si es una fecha, retornar None
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return None
    
    # Remover caracteres no numéricos excepto guiones y espacios
    # pero mantener el formato original si es válido
    return val_str

def clean_data():
    """Limpia todos los datos del archivo consolidado"""
    
    input_file = 'data/raw/trazabilidad_consolidada.json'
    output_file = 'data/audit/trazabilidad_consolidada_CLEAN.json'
    backup_file = 'data/audit/trazabilidad_consolidada_BACKUP.json'
    
    print("="*80)
    print("LIMPIEZA DE DATOS - Sistema de Gestión Terapéutica")
    print("="*80)
    
    # Crear backup
    print("\n1. Creando backup del archivo original...")
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Backup guardado en: {backup_file}")
    
    # Cargar datos
    print("\n2. Cargando datos...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data if isinstance(data, list) else data.get('data', [])
    df = pd.DataFrame(records)
    print(f"   ✓ {len(df)} registros cargados")
    
    # Estadísticas antes de limpieza
    print("\n3. Estadísticas ANTES de limpieza:")
    print(f"   - Total registros: {len(df)}")
    print(f"   - Campos: {len(df.columns)}")
    
    # Aplicar limpieza
    print("\n4. Aplicando limpieza campo por campo...")
    
    # Limpiar APELLIDOS (remover números)
    if 'apellidos' in df.columns:
        before = df['apellidos'].notna().sum()
        df['apellidos'] = df['apellidos'].apply(clean_text_field)
        after = df['apellidos'].notna().sum()
        print(f"   ✓ apellidos: {before} -> {after} válidos")
    
    # Limpiar NOMBRES (remover números)
    if 'nombres' in df.columns:
        before = df['nombres'].notna().sum()
        df['nombres'] = df['nombres'].apply(clean_text_field)
        after = df['nombres'].notna().sum()
        print(f"   ✓ nombres: {before} -> {after} válidos")
    
    # Limpiar EPS (remover números puros)
    if 'eps' in df.columns:
        before = df['eps'].notna().sum()
        df['eps'] = df['eps'].apply(clean_text_field)
        after = df['eps'].notna().sum()
        print(f"   ✓ eps: {before} -> {after} válidos")
    
    # Limpiar DIRECCION (remover fechas)
    if 'direccion' in df.columns:
        before = df['direccion'].notna().sum()
        df['direccion'] = df['direccion'].apply(clean_text_field)
        after = df['direccion'].notna().sum()
        print(f"   ✓ direccion: {before} -> {after} válidos")
    
    # Limpiar TELEFONO (remover fechas)
    if 'telefono' in df.columns:
        before = df['telefono'].notna().sum()
        df['telefono'] = df['telefono'].apply(clean_telefono)
        after = df['telefono'].notna().sum()
        print(f"   ✓ telefono: {before} -> {after} válidos")
    
    # Limpiar FECHA_INGRESO
    if 'fecha_ingreso' in df.columns:
        before = df['fecha_ingreso'].notna().sum()
        df['fecha_ingreso'] = df['fecha_ingreso'].apply(clean_fecha)
        after = df['fecha_ingreso'].notna().sum()
        print(f"   ✓ fecha_ingreso: {before} -> {after} válidos")
    
    # Limpiar FECHA_EGRESO
    if 'fecha_egreso' in df.columns:
        before = df['fecha_egreso'].notna().sum()
        df['fecha_egreso'] = df['fecha_egreso'].apply(clean_fecha)
        after = df['fecha_egreso'].notna().sum()
        print(f"   ✓ fecha_egreso: {before} -> {after} válidos")
    
    # Limpiar SESIONES (extraer números)
    if 'sesiones' in df.columns:
        before = df['sesiones'].notna().sum()
        df['sesiones'] = df['sesiones'].apply(clean_sesiones)
        after = (df['sesiones'] > 0).sum()
        print(f"   ✓ sesiones: {before} -> {after} válidos")
    
    # Estadísticas después de limpieza
    print("\n5. Estadísticas DESPUÉS de limpieza:")
    print(f"   - Total registros: {len(df)}")
    print(f"   - Registros con nombre válido: {df['nombres'].notna().sum()}")
    print(f"   - Registros con apellido válido: {df['apellidos'].notna().sum()}")
    print(f"   - Registros con fecha_ingreso válida: {df['fecha_ingreso'].notna().sum()}")
    print(f"   - Registros con sesiones > 0: {(df['sesiones'] > 0).sum()}")
    
    # Convertir de vuelta a JSON
    print("\n6. Guardando datos limpios...")
    
    # Convertir NaN a None para JSON
    df_clean = df.where(pd.notna(df), None)
    
    # Guardar en formato lista de diccionarios
    records_clean = df_clean.to_dict('records')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records_clean, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Datos limpios guardados en: {output_file}")
    
    # Generar reporte de limpieza
    print("\n7. Generando reporte de limpieza...")
    
    report = {
        'fecha_limpieza': datetime.now().isoformat(),
        'registros_procesados': len(df),
        'campos_limpiados': [
            'apellidos', 'nombres', 'eps', 'direccion', 'telefono',
            'fecha_ingreso', 'fecha_egreso', 'sesiones'
        ],
        'estadisticas': {
            'nombres_validos': int(df['nombres'].notna().sum()),
            'apellidos_validos': int(df['apellidos'].notna().sum()),
            'eps_validos': int(df['eps'].notna().sum()),
            'fechas_ingreso_validas': int(df['fecha_ingreso'].notna().sum()),
            'fechas_egreso_validas': int(df['fecha_egreso'].notna().sum()),
            'sesiones_validas': int((df['sesiones'] > 0).sum())
        }
    }
    
    with open('data/audit/cleaning_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Reporte guardado en: data/audit/cleaning_report.json")
    
    print("\n" + "="*80)
    print("✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
    print("="*80)
    print(f"\nArchivos generados:")
    print(f"  1. {backup_file} (backup original)")
    print(f"  2. {output_file} (datos limpios)")
    print(f"  3. data/audit/cleaning_report.json (reporte)")
    print(f"\nPara usar los datos limpios, actualiza tu código para leer:")
    print(f"  '{output_file}'")
    print()

if __name__ == "__main__":
    clean_data()
