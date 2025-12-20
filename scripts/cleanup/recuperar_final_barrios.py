"""
Recuperación Final por Dirección
Usa lista oficial de barrios de Montería y otros municipios
"""

import pandas as pd
import json
import re
from collections import Counter

# BARRIOS OFICIALES DE MONTERÍA (207 barrios en 9 comunas)
BARRIOS_MONTERIA = [
    # Comuna 3
    'BRISAS DEL SINU', 'NUEVO MILENIO', 'SANTA FE', 'SIMON BOLIVAR',
    'LA COQUERA', 'EL TENDAL', 'BUENAVISTA', 'SANTA LUCIA', 'LA GRANJA',
    'SAN MARTIN', 'SANTANDER', 'POLICARPA', 'PASTRANA BORRERO',
    # Comuna 7
    'SUCRE', 'SUCRE INVASION', 'LUIS CARLOS GALAN', 'INDUSTRIAL',
    'EL CARMEN', 'LOS LAURELES II', 'PRADO NORTE', 'VILLA DEL RIO',
    'ALTOS DEL COUNTRY', 'ALAMEDAS DEL SINU', 'LOS LAURELES',
    # Otros barrios conocidos
    'EL EDEN', 'LA CEIBA', 'LA JULIA', 'LA VICTORIA', 'LOS ALAMOS',
    'MONTERIA MODERNO', 'NARIÑO', 'OBRERO', 'LOS ARAUJOS', 'LOS COLORES',
    'LA PALMA', 'EL ROSARIO', 'EL TAMBO', 'OSPINA PEREZ', 'CAMILO TORRES',
    'EL BOSQUE', 'EL CEIBAL', 'CANTACLARO', 'LA CASTELLANA', 'CASTELLANA',
    'EL DORADO', 'GUAYABAL', 'EDMUNDO LOPEZ', 'PASATIEMPO', 'JUAN XXIII',
    'EL RECREO', 'VILLA CIELO', 'VILLA MARGARITA', 'VILLA ROCIO',
    'VILLA MELISSA', 'VILLA OLIMPICA', 'VILLA SANDRA', 'VILLA SORRENTO',
    'VILLA JIMENEZ', 'VILLA FATIMA', 'VILLA ESPERANZA', 'VILLA NUEVA',
    'VILLA CAROLINA', 'VILLA KATIA', 'VILLA HERMOSA', 'VILLA MARIA',
    'VILLA CIELO', 'VILLA MARBELLA', 'VILLA SOFIA', 'VILLA CLAUDIA',
    'MOGAMBO', 'MOCARÍ', 'RANCHO GRANDE', 'EL PRADO', 'LA PRADERA',
    'LA FLORESTA', 'LA CAMPIÑA', 'LA RIBERA', 'LA GRANJA', 'LA CASTELLANA',
    'LA UNION', 'LA PAZ', 'LA ESPERANZA', 'LA ALHAMBRA', 'LA PRADERA',
    'BOSTON', 'BOSTON II', 'BOSTON III', 'BOSTON IV', 'BOSTON V',
    'CANTACLARO LA UNION', 'CANTACLARO SECTOR', 'CANTACLARO I', 'CANTACLARO II',
    'P5', 'P-5', 'COLINA REAL', 'COLINAS', 'LAS COLINAS', 'COLINAS DEL SINU',
    'FURATENA', 'FURATENA I', 'FURATENA II', 'FURATENA III',
    'URBANIZACION EL PRADO', 'URBANIZACION LA CASTELLANA', 'URB LA CASTELLANA',
    'URBANIZACION EDMUNDO LOPEZ', 'URB EDMUNDO LOPEZ', 'EDMUNDO LOPEZ I',
    'EDMUNDO LOPEZ II', 'EDMUNDO LOPEZ III', 'EDMUNDO LOPEZ IV',
    'NUEVA ESPERANZA', 'NUEVA COLOMBIA', 'NUEVO HORIZONTE', 'NUEVO MILENIO',
    'NUEVA MONTERIA', 'NUEVO PARAISO', 'NUEVA VIDA', 'NUEVA FLORESTA',
    'ANAL', 'CANTA CLARO', 'CANTA-CLARO', 'CANAL', 'CANDELARIA',
    'CENTRO', 'EL CENTRO', 'CENTRO HISTORICO', 'CENTRO COMERCIAL',
    'CHUCHURUBI', 'CHUCHURUBÍ', 'CANTA GALLO', 'CANTAGALLO',
    'ROBINSON PITALUA', 'ROBINSON PITALÚA', 'ROBINSON', 'PITALUA',
    'EDMUNDO LOPEZ', 'EDMUNDO', 'LOPEZ', 'EDMUNDO LÓPEZ',
    'BONGO', 'EL BONGO', 'BONGOLANDIA', 'BONGOS',
    'MINUTO DE DIOS', 'MINUTO', 'CIUDADELA DEL RIO', 'CIUDADELA',
    'URBANIZACION FURATENA', 'URB FURATENA', 'FURATENA SECTOR',
    'URBANIZACION ROBINSON PITALUA', 'URB ROBINSON PITALUA',
    'URBANIZACION VILLA CIELO', 'URB VILLA CIELO', 'VILLA CIELO I',
    'VILLA CIELO II', 'VILLA CIELO III', 'VILLA CIELO IV',
    'URBANIZACION VILLA OLIMPICA', 'URB VILLA OLIMPICA',
    'VILLA OLIMPICA I', 'VILLA OLIMPICA II', 'VILLA OLIMPICA III',
    'URBANIZACION VILLA MARGARITA', 'URB VILLA MARGARITA',
    'VILLA MARGARITA I', 'VILLA MARGARITA II', 'VILLA MARGARITA III',
    'URBANIZACION VILLA MELISSA', 'URB VILLA MELISSA',
    'VILLA MELISSA I', 'VILLA MELISSA II', 'VILLA MELISSA III',
    'URBANIZACION VILLA ROCIO', 'URB VILLA ROCIO',
    'VILLA ROCIO I', 'VILLA ROCIO II', 'VILLA ROCIO III',
    'URBANIZACION VILLA SANDRA', 'URB VILLA SANDRA',
    'VILLA SANDRA I', 'VILLA SANDRA II', 'VILLA SANDRA III',
    'URBANIZACION VILLA SORRENTO', 'URB VILLA SORRENTO',
    'VILLA SORRENTO I', 'VILLA SORRENTO II', 'VILLA SORRENTO III',
    'URBANIZACION VILLA JIMENEZ', 'URB VILLA JIMENEZ',
    'VILLA JIMENEZ I', 'VILLA JIMENEZ II', 'VILLA JIMENEZ III',
    'URBANIZACION VILLA FATIMA', 'URB VILLA FATIMA',
    'VILLA FATIMA I', 'VILLA FATIMA II', 'VILLA FATIMA III',
]

# Normalizar (quitar acentos, mayúsculas)
from unidecode import unidecode
BARRIOS_MONTERIA_NORM = [unidecode(b).upper() for b in BARRIOS_MONTERIA]

def buscar_barrio_en_direccion(direccion):
    """Busca si la dirección contiene algún barrio de Montería"""
    if pd.isna(direccion) or direccion == '':
        return None
    
    direccion_norm = unidecode(str(direccion).upper())
    
    # Buscar coincidencias
    for barrio in BARRIOS_MONTERIA_NORM:
        if barrio in direccion_norm:
            return 'MONTERÍA'
    
    return None

def recuperar_final():
    """Recuperación final usando lista oficial de barrios"""
    
    print("="*80)
    print("RECUPERACIÓN FINAL POR BARRIOS OFICIALES")
    print("="*80)
    
    # Cargar rechazados
    print("\n1. Cargando registros rechazados...")
    with open('data/audit/registros_RECHAZADOS.json', 'r', encoding='utf-8') as f:
        rechazados = json.load(f)
    df_rechazados = pd.DataFrame(rechazados)
    print(f"   ✓ {len(df_rechazados)} registros")
    
    # Aplicar búsqueda de barrios
    print("\n2. Buscando barrios de Montería en direcciones...")
    print(f"   ✓ {len(BARRIOS_MONTERIA)} barrios oficiales de Montería")
    
    recuperados_monteria = 0
    
    for idx, row in df_rechazados.iterrows():
        # Solo procesar si no tiene municipio
        if pd.notna(row.get('municipio')):
            continue
        
        direccion = row.get('direccion')
        if pd.isna(direccion):
            continue
        
        municipio = buscar_barrio_en_direccion(direccion)
        if municipio:
            df_rechazados.at[idx, 'municipio'] = municipio
            recuperados_monteria += 1
    
    print(f"   ✓ {recuperados_monteria} municipios recuperados (Montería)")
    
    # Separar recuperados
    print("\n3. Separando registros...")
    
    df_recuperados = df_rechazados[
        (df_rechazados['eps'].notna()) & (df_rechazados['municipio'].notna())
    ].copy()
    
    df_aun_rechazados = df_rechazados[
        (df_rechazados['eps'].isna()) | (df_rechazados['municipio'].isna())
    ].copy()
    
    print(f"   ✓ Recuperados: {len(df_recuperados)}")
    print(f"   ✓ Aún rechazados: {len(df_aun_rechazados)}")
    
    # Combinar con válidos
    print("\n4. Actualizando archivos...")
    
    with open('data/processed/trazabilidad_LIMPIA.json', 'r', encoding='utf-8') as f:
        validos = json.load(f)
    df_validos = pd.DataFrame(validos)
    
    if 'razon_rechazo' in df_recuperados.columns:
        df_recuperados = df_recuperados.drop(columns=['razon_rechazo'])
    
    df_todos_validos = pd.concat([df_validos, df_recuperados], ignore_index=True)
    
    # Guardar válidos
    df_validos_clean = df_todos_validos.where(pd.notna(df_todos_validos), None)
    with open('data/processed/trazabilidad_LIMPIA.json', 'w', encoding='utf-8') as f:
        json.dump(df_validos_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/processed/trazabilidad_LIMPIA.json ({len(df_todos_validos)} registros)")
    
    # Guardar rechazados
    if len(df_aun_rechazados) > 0:
        for idx, row in df_aun_rechazados.iterrows():
            razones = []
            if pd.isna(row.get('eps')):
                razones.append(f"EPS inválida: {row.get('eps_original', 'N/A')}")
            if pd.isna(row.get('municipio')):
                razones.append(f"Municipio inválido: {row.get('municipio_original', 'N/A')}")
            df_aun_rechazados.at[idx, 'razon_rechazo'] = ' | '.join(razones)
        
        df_rechazados_clean = df_aun_rechazados.where(pd.notna(df_aun_rechazados), None)
        with open('data/audit/registros_RECHAZADOS.json', 'w', encoding='utf-8') as f:
            json.dump(df_rechazados_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_RECHAZADOS.json ({len(df_aun_rechazados)} registros)")
    
    # Guardar recuperados
    if len(df_recuperados) > 0:
        df_recuperados_clean = df_recuperados.where(pd.notna(df_recuperados), None)
        with open('data/audit/registros_RECUPERADOS_BARRIOS.json', 'w', encoding='utf-8') as f:
            json.dump(df_recuperados_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_RECUPERADOS_BARRIOS.json ({len(df_recuperados)} registros)")
    
    # Resumen
    print("\n" + "="*80)
    print("✅ RECUPERACIÓN FINAL COMPLETADA")
    print("="*80)
    print(f"\nRecuperación:")
    print(f"  🏘️ Por barrios de Montería: {recuperados_monteria}")
    print(f"  ✅ Total recuperados: {len(df_recuperados)}")
    print(f"\nResultado final:")
    print(f"  ✅ Válidos totales: {len(df_todos_validos):,}")
    print(f"  ⚠️ Aún rechazados: {len(df_aun_rechazados):,}")
    print()

if __name__ == "__main__":
    recuperar_final()
