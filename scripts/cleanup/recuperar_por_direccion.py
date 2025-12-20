"""
Recuperación por Dirección
Extrae barrios/sectores de direcciones y los asocia con municipios
para recuperar datos rechazados
"""

import pandas as pd
import json
import re
from collections import Counter

def extraer_barrios_sectores(direccion):
    """Extrae posibles nombres de barrios/sectores de una dirección"""
    if pd.isna(direccion) or direccion == '':
        return []
    
    direccion = str(direccion).upper()
    barrios = []
    
    # Patrones comunes de barrios
    patrones = [
        r'B[/\s]*([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+CRA|\s+CALLE|\s+CLL|\s+KR|\s+DIAGONAL|$)',
        r'BARRIO\s+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+CRA|\s+CALLE|\s+CLL|\s+KR|$)',
        r'VEREDA\s+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+|$)',
        r'CORREGIMIENTO\s+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+|$)',
        r'SECTOR\s+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+|$)',
    ]
    
    for patron in patrones:
        matches = re.findall(patron, direccion)
        for match in matches:
            barrio = match.strip()
            if len(barrio) >= 3:  # Mínimo 3 caracteres
                barrios.append(barrio)
    
    return barrios

def crear_indice_direcciones():
    """
    Crea un índice de barrios/sectores -> municipio
    usando los registros válidos
    """
    
    print("="*80)
    print("CREACIÓN DE ÍNDICE DE DIRECCIONES")
    print("="*80)
    
    # 1. Cargar datos válidos
    print("\n1. Cargando datos válidos...")
    with open('data/processed/trazabilidad_LIMPIA.json', 'r', encoding='utf-8') as f:
        validos = json.load(f)
    df_validos = pd.DataFrame(validos)
    print(f"   ✓ {len(df_validos)} registros")
    
    # 2. Extraer barrios/sectores
    print("\n2. Extrayendo barrios y sectores de direcciones...")
    
    # Diccionario: barrio/sector -> [lista de municipios]
    barrio_municipio = {}
    
    for _, row in df_validos.iterrows():
        direccion = row.get('direccion')
        municipio = row.get('municipio')
        
        if pd.notna(direccion) and pd.notna(municipio):
            barrios = extraer_barrios_sectores(direccion)
            
            for barrio in barrios:
                if barrio not in barrio_municipio:
                    barrio_municipio[barrio] = []
                barrio_municipio[barrio].append(municipio)
    
    print(f"   ✓ {len(barrio_municipio)} barrios/sectores identificados")
    
    # 3. Consolidar (usar el municipio más común para cada barrio)
    print("\n3. Consolidando índice...")
    
    barrio_municipio_final = {}
    
    for barrio, municipios in barrio_municipio.items():
        # Obtener el municipio más común
        municipio_mas_comun = Counter(municipios).most_common(1)[0]
        barrio_municipio_final[barrio] = {
            'municipio': municipio_mas_comun[0],
            'frecuencia': municipio_mas_comun[1],
            'total': len(municipios),
            'confianza': municipio_mas_comun[1] / len(municipios) * 100
        }
    
    # Filtrar solo los que tienen alta confianza (>70%)
    barrio_municipio_confiable = {
        barrio: info for barrio, info in barrio_municipio_final.items()
        if info['confianza'] >= 70
    }
    
    print(f"   ✓ {len(barrio_municipio_confiable)} barrios con alta confianza (≥70%)")
    
    # 4. Mostrar top 20
    print("\n4. Top 20 barrios/sectores más comunes:")
    
    barrios_ordenados = sorted(
        barrio_municipio_confiable.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    for i, (barrio, info) in enumerate(barrios_ordenados[:20], 1):
        print(f"   {i:2}. {barrio[:30]:<30} → {info['municipio']:<20} ({info['total']} veces, {info['confianza']:.0f}% confianza)")
    
    # 5. Guardar índice
    print("\n5. Guardando índice...")
    
    indice_exportable = {
        barrio: {
            'municipio': info['municipio'],
            'frecuencia': info['frecuencia'],
            'total': info['total'],
            'confianza': round(info['confianza'], 1)
        }
        for barrio, info in barrio_municipio_confiable.items()
    }
    
    with open('data/reference/indice_barrios_municipios.json', 'w', encoding='utf-8') as f:
        json.dump(indice_exportable, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ data/reference/indice_barrios_municipios.json")
    
    # 6. Aplicar a registros rechazados
    print("\n6. Aplicando a registros rechazados...")
    
    with open('data/audit/registros_RECHAZADOS.json', 'r', encoding='utf-8') as f:
        rechazados = json.load(f)
    df_rechazados = pd.DataFrame(rechazados)
    
    print(f"   ✓ {len(df_rechazados)} registros rechazados")
    
    recuperados_direccion = 0
    
    for idx, row in df_rechazados.iterrows():
        # Solo procesar si no tiene municipio
        if pd.notna(row.get('municipio')):
            continue
        
        direccion = row.get('direccion')
        if pd.isna(direccion):
            continue
        
        # Extraer barrios de esta dirección
        barrios = extraer_barrios_sectores(direccion)
        
        # Buscar en el índice
        for barrio in barrios:
            if barrio in barrio_municipio_confiable:
                municipio = barrio_municipio_confiable[barrio]['municipio']
                df_rechazados.at[idx, 'municipio'] = municipio
                recuperados_direccion += 1
                break  # Solo usar el primer match
    
    print(f"   ✓ {recuperados_direccion} municipios recuperados por dirección")
    
    # 7. Separar recuperados
    print("\n7. Separando registros...")
    
    df_recuperados = df_rechazados[
        (df_rechazados['eps'].notna()) & (df_rechazados['municipio'].notna())
    ].copy()
    
    df_aun_rechazados = df_rechazados[
        (df_rechazados['eps'].isna()) | (df_rechazados['municipio'].isna())
    ].copy()
    
    print(f"   ✓ Recuperados: {len(df_recuperados)}")
    print(f"   ✓ Aún rechazados: {len(df_aun_rechazados)}")
    
    # 8. Combinar con válidos
    print("\n8. Actualizando archivos...")
    
    with open('data/processed/trazabilidad_LIMPIA.json', 'r', encoding='utf-8') as f:
        validos_actuales = json.load(f)
    df_validos_actuales = pd.DataFrame(validos_actuales)
    
    if 'razon_rechazo' in df_recuperados.columns:
        df_recuperados = df_recuperados.drop(columns=['razon_rechazo'])
    
    df_todos_validos = pd.concat([df_validos_actuales, df_recuperados], ignore_index=True)
    
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
    
    # Guardar recuperados por dirección
    if len(df_recuperados) > 0:
        df_recuperados_clean = df_recuperados.where(pd.notna(df_recuperados), None)
        with open('data/audit/registros_RECUPERADOS_DIRECCION.json', 'w', encoding='utf-8') as f:
            json.dump(df_recuperados_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_RECUPERADOS_DIRECCION.json ({len(df_recuperados)} registros)")
    
    # 9. Reporte
    print("\n9. Generando reporte...")
    
    reporte = {
        'fecha': pd.Timestamp.now().isoformat(),
        'barrios_identificados': len(barrio_municipio),
        'barrios_confiables': len(barrio_municipio_confiable),
        'registros_recuperados': len(df_recuperados),
        'municipios_recuperados_por_direccion': recuperados_direccion,
        'total_validos_final': len(df_todos_validos),
        'total_rechazados_final': len(df_aun_rechazados)
    }
    
    with open('data/audit/reporte_recuperacion_direccion.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/audit/reporte_recuperacion_direccion.json")
    
    # 10. Resumen
    print("\n" + "="*80)
    print("✅ RECUPERACIÓN POR DIRECCIÓN COMPLETADA")
    print("="*80)
    print(f"\nÍndice creado:")
    print(f"  📍 Barrios identificados: {len(barrio_municipio):,}")
    print(f"  ✅ Barrios confiables (≥70%): {len(barrio_municipio_confiable):,}")
    print(f"\nRecuperación:")
    print(f"  🏘️  Municipios recuperados: {recuperados_direccion:,}")
    print(f"  ✅ Registros recuperados: {len(df_recuperados):,}")
    print(f"\nResultado final:")
    print(f"  ✅ Válidos totales: {len(df_todos_validos):,}")
    print(f"  ⚠️  Aún rechazados: {len(df_aun_rechazados):,}")
    print(f"\nArchivos generados:")
    print(f"  1. data/reference/indice_barrios_municipios.json")
    print(f"  2. data/processed/trazabilidad_LIMPIA.json (actualizado)")
    print(f"  3. data/audit/registros_RECUPERADOS_DIRECCION.json")
    print()

if __name__ == "__main__":
    crear_indice_direcciones()
