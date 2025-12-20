"""
Script de Identificación de Datos Maestros
Identifica todas las EPS y Municipios únicos para crear listas maestras
"""

import pandas as pd
import json
import re
from collections import Counter

def is_valid_eps(val):
    """Determina si un valor parece ser una EPS válida"""
    if pd.isna(val) or val == '':
        return False
    
    val_str = str(val).strip().upper()
    
    # Descartar números puros
    try:
        float(val_str)
        return False
    except:
        pass
    
    # Descartar fechas
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return False
    
    # Debe tener al menos 3 caracteres
    if len(val_str) < 3:
        return False
    
    # Palabras clave comunes en EPS
    eps_keywords = ['EPS', 'SALUD', 'VIDA', 'SANITAS', 'SURA', 'NUEVA', 
                    'COMFACOR', 'MUTUAL', 'COMPENSAR', 'CAFESALUD', 
                    'COOMEVA', 'FAMISANAR', 'ALIANSALUD']
    
    # Si contiene alguna palabra clave, probablemente es EPS
    for keyword in eps_keywords:
        if keyword in val_str:
            return True
    
    # Si tiene entre 3 y 50 caracteres y no es número ni fecha, probablemente es EPS
    if 3 <= len(val_str) <= 50:
        return True
    
    return False

def is_valid_municipio(val):
    """Determina si un valor parece ser un municipio válido"""
    if pd.isna(val) or val == '':
        return False
    
    val_str = str(val).strip().upper()
    
    # Descartar números puros
    try:
        float(val_str)
        return False
    except:
        pass
    
    # Descartar fechas
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return False
    
    # Debe tener al menos 3 caracteres
    if len(val_str) < 3:
        return False
    
    # Municipios conocidos de Córdoba (algunos ejemplos)
    cordoba_municipios = [
        'MONTERIA', 'CERETE', 'SAHAGUN', 'LORICA', 'PLANETA RICA',
        'MONTELIBANO', 'TIERRALTA', 'AYAPEL', 'PUEBLO NUEVO',
        'CIENAGA DE ORO', 'SAN PELAYO', 'COTORRA', 'CHIMA',
        'SAN BERNARDO', 'PUERTO ESCONDIDO', 'LOS CORDOBA',
        'SAN ANDRES', 'MOMIL', 'PURISIMA', 'CHINU', 'SAN CARLOS',
        'BUENAVISTA', 'LA APARTADA', 'MOÑITOS', 'PUERTO LIBERTADOR',
        'SAN ANTERO', 'TUCHIN', 'VALENCIA', 'CANALETE', 'SAN JOSE'
    ]
    
    # Si coincide con municipios conocidos
    for mun in cordoba_municipios:
        if mun in val_str or val_str in mun:
            return True
    
    # Si tiene entre 3 y 50 caracteres y no es número ni fecha
    if 3 <= len(val_str) <= 50:
        return True
    
    return False

def analyze_masters():
    """Analiza y crea listas maestras de EPS y Municipios"""
    
    file_path = 'data/audit/trazabilidad_consolidada.json'
    
    print("="*80)
    print("IDENTIFICACIÓN DE DATOS MAESTROS")
    print("="*80)
    
    # Cargar datos
    print("\n1. Cargando datos...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data if isinstance(data, list) else data.get('data', [])
    df = pd.DataFrame(records)
    print(f"   ✓ {len(df)} registros cargados")
    
    # Analizar EPS
    print("\n2. Analizando EPS...")
    eps_values = []
    
    if 'eps' in df.columns:
        for val in df['eps'].dropna():
            if is_valid_eps(val):
                eps_values.append(str(val).strip().upper())
    
    eps_counter = Counter(eps_values)
    
    print(f"   ✓ {len(eps_counter)} EPS únicas encontradas")
    print(f"\n   Top 20 EPS por frecuencia:")
    for eps, count in eps_counter.most_common(20):
        print(f"      {count:>5} - {eps}")
    
    # Analizar Municipios
    print("\n3. Analizando Municipios...")
    municipio_values = []
    
    if 'municipio' in df.columns:
        for val in df['municipio'].dropna():
            if is_valid_municipio(val):
                municipio_values.append(str(val).strip().upper())
    
    municipio_counter = Counter(municipio_values)
    
    print(f"   ✓ {len(municipio_counter)} Municipios únicos encontrados")
    print(f"\n   Todos los municipios por frecuencia:")
    for mun, count in municipio_counter.most_common():
        print(f"      {count:>5} - {mun}")
    
    # Analizar contexto de fechas
    print("\n4. Analizando contexto de fechas...")
    
    # Buscar registros donde fecha_ingreso o fecha_egreso son números pequeños
    fecha_issues = []
    
    for col in ['fecha_ingreso', 'fecha_egreso']:
        if col in df.columns:
            for idx, row in df.iterrows():
                val = row[col]
                if pd.notna(val):
                    val_str = str(val).strip()
                    # Si es un número entre 1 y 31 (días del mes)
                    if re.match(r'^\d{1,2}$', val_str):
                        num = int(val_str)
                        if 1 <= num <= 31:
                            fecha_issues.append({
                                'index': idx,
                                'campo': col,
                                'valor': num,
                                'archivo': row.get('source_file', 'N/A'),
                                'year_folder': row.get('year_folder', 'N/A')
                            })
    
    print(f"   ✓ {len(fecha_issues)} registros con fechas incompletas (solo día)")
    
    if fecha_issues:
        print(f"\n   Primeros 10 ejemplos:")
        for issue in fecha_issues[:10]:
            print(f"      Archivo: {issue['archivo']}")
            print(f"      Año carpeta: {issue['year_folder']}")
            print(f"      Campo: {issue['campo']} = {issue['valor']}")
            print()
    
    # Guardar listas maestras
    print("\n5. Guardando listas maestras...")
    
    master_data = {
        'eps_list': [
            {'nombre': eps, 'frecuencia': count}
            for eps, count in eps_counter.most_common()
        ],
        'municipios_list': [
            {'nombre': mun, 'frecuencia': count}
            for mun, count in municipio_counter.most_common()
        ],
        'fecha_issues_sample': fecha_issues[:100],  # Primeros 100 ejemplos
        'estadisticas': {
            'total_eps': len(eps_counter),
            'total_municipios': len(municipio_counter),
            'total_fecha_issues': len(fecha_issues)
        }
    }
    
    with open('data/audit/master_data.json', 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Listas maestras guardadas en: data/audit/master_data.json")
    
    # Crear lista de municipios de Córdoba (los 30)
    print("\n6. Creando lista oficial de municipios de Córdoba...")
    
    municipios_cordoba_oficiales = [
        'MONTERÍA', 'CERETÉ', 'SAHAGÚN', 'LORICA', 'PLANETA RICA',
        'MONTELÍBANO', 'TIERRALTA', 'AYAPEL', 'PUEBLO NUEVO',
        'CIÉNAGA DE ORO', 'SAN PELAYO', 'COTORRA', 'CHIMÁ',
        'SAN BERNARDO DEL VIENTO', 'PUERTO ESCONDIDO', 'LOS CÓRDOBAS',
        'SAN ANDRÉS DE SOTAVENTO', 'MOMIL', 'PURÍSIMA', 'CHINÚ', 
        'SAN CARLOS', 'BUENAVISTA', 'LA APARTADA', 'MOÑITOS', 
        'PUERTO LIBERTADOR', 'SAN ANTERO', 'TUCHÍN', 'VALENCIA', 
        'CANALETE', 'SAN JOSÉ DE URÉ'
    ]
    
    # Comparar con los encontrados
    print(f"\n   Municipios oficiales de Córdoba (30):")
    for i, mun in enumerate(municipios_cordoba_oficiales, 1):
        # Buscar coincidencias en los datos
        matches = [m for m in municipio_counter.keys() if mun.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U') in m or m in mun]
        count = sum(municipio_counter[m] for m in matches) if matches else 0
        print(f"      {i:>2}. {mun:<30} ({count:>5} registros)")
    
    # Guardar lista oficial
    with open('data/audit/municipios_cordoba_oficial.json', 'w', encoding='utf-8') as f:
        json.dump({
            'municipios': municipios_cordoba_oficiales,
            'total': len(municipios_cordoba_oficiales)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n   ✓ Lista oficial guardada en: data/audit/municipios_cordoba_oficial.json")
    
    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*80)
    print(f"\nResumen:")
    print(f"  - {len(eps_counter)} EPS únicas")
    print(f"  - {len(municipio_counter)} municipios únicos en datos")
    print(f"  - 30 municipios oficiales de Córdoba")
    print(f"  - {len(fecha_issues)} registros con fechas incompletas")
    print()

if __name__ == "__main__":
    analyze_masters()
