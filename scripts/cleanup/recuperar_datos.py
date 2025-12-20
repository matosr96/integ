"""
Script de Recuperación de Datos
Recupera EPS y Municipio de registros rechazados usando información de otros registros del mismo paciente
"""

import pandas as pd
import json
from collections import Counter

def recuperar_datos_faltantes():
    """
    Recupera datos faltantes (EPS, Municipio) de registros rechazados
    usando información de otros registros del mismo paciente (por cédula)
    """
    
    print("="*80)
    print("RECUPERACIÓN DE DATOS FALTANTES")
    print("="*80)
    
    # 1. Cargar datos válidos
    print("\n1. Cargando datos válidos...")
    with open('data/processed/trazabilidad_LIMPIA.json', 'r', encoding='utf-8') as f:
        validos = json.load(f)
    df_validos = pd.DataFrame(validos)
    print(f"   ✓ {len(df_validos)} registros válidos")
    
    # 2. Cargar datos rechazados
    print("\n2. Cargando datos rechazados...")
    with open('data/audit/registros_RECHAZADOS.json', 'r', encoding='utf-8') as f:
        rechazados = json.load(f)
    df_rechazados = pd.DataFrame(rechazados)
    print(f"   ✓ {len(df_rechazados)} registros rechazados")
    
    # 3. Crear índice de pacientes (por cédula)
    print("\n3. Creando índice de pacientes...")
    
    # Diccionario: cedula -> {eps: [lista], municipio: [lista]}
    pacientes_info = {}
    
    for _, row in df_validos.iterrows():
        cedula = row.get('numero_id')
        eps = row.get('eps')
        municipio = row.get('municipio')
        
        if pd.notna(cedula):
            cedula = str(cedula).strip()
            
            if cedula not in pacientes_info:
                pacientes_info[cedula] = {'eps': [], 'municipio': []}
            
            if pd.notna(eps):
                pacientes_info[cedula]['eps'].append(eps)
            if pd.notna(municipio):
                pacientes_info[cedula]['municipio'].append(municipio)
    
    print(f"   ✓ {len(pacientes_info)} pacientes únicos indexados")
    
    # 4. Intentar recuperar datos
    print("\n4. Recuperando datos faltantes...")
    
    recuperados = 0
    eps_recuperadas = 0
    municipios_recuperados = 0
    
    for idx, row in df_rechazados.iterrows():
        cedula = row.get('numero_id')
        
        if pd.isna(cedula):
            continue
        
        cedula = str(cedula).strip()
        
        if cedula not in pacientes_info:
            continue
        
        info = pacientes_info[cedula]
        cambio = False
        
        # Recuperar EPS
        if pd.isna(row.get('eps')) and info['eps']:
            # Usar la EPS más común para este paciente
            eps_mas_comun = Counter(info['eps']).most_common(1)[0][0]
            df_rechazados.at[idx, 'eps'] = eps_mas_comun
            eps_recuperadas += 1
            cambio = True
        
        # Recuperar Municipio
        if pd.isna(row.get('municipio')) and info['municipio']:
            # Usar el municipio más común para este paciente
            mun_mas_comun = Counter(info['municipio']).most_common(1)[0][0]
            df_rechazados.at[idx, 'municipio'] = mun_mas_comun
            municipios_recuperados += 1
            cambio = True
        
        if cambio:
            recuperados += 1
    
    print(f"   ✓ {recuperados} registros recuperados")
    print(f"   ✓ {eps_recuperadas} EPS recuperadas")
    print(f"   ✓ {municipios_recuperados} municipios recuperados")
    
    # 5. Separar recuperados de los que siguen rechazados
    print("\n5. Separando registros...")
    
    # Recuperados: ahora tienen EPS Y municipio
    df_recuperados = df_rechazados[
        (df_rechazados['eps'].notna()) & (df_rechazados['municipio'].notna())
    ].copy()
    
    # Aún rechazados: les falta EPS o municipio
    df_aun_rechazados = df_rechazados[
        (df_rechazados['eps'].isna()) | (df_rechazados['municipio'].isna())
    ].copy()
    
    print(f"   ✓ Recuperados: {len(df_recuperados)}")
    print(f"   ✓ Aún rechazados: {len(df_aun_rechazados)}")
    
    # 6. Combinar válidos originales con recuperados
    print("\n6. Combinando datos válidos...")
    
    # Remover columnas de auditoría de los recuperados
    if 'razon_rechazo' in df_recuperados.columns:
        df_recuperados = df_recuperados.drop(columns=['razon_rechazo'])
    
    # Combinar
    df_todos_validos = pd.concat([df_validos, df_recuperados], ignore_index=True)
    
    print(f"   ✓ Total válidos: {len(df_todos_validos)}")
    print(f"     - Originales: {len(df_validos)}")
    print(f"     - Recuperados: {len(df_recuperados)}")
    
    # 7. Guardar archivos actualizados
    print("\n7. Guardando archivos...")
    
    # Guardar datos válidos actualizados
    df_validos_clean = df_todos_validos.where(pd.notna(df_todos_validos), None)
    records_validos = df_validos_clean.to_dict('records')
    
    with open('data/processed/trazabilidad_LIMPIA.json', 'w', encoding='utf-8') as f:
        json.dump(records_validos, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/processed/trazabilidad_LIMPIA.json actualizado")
    
    # Guardar rechazados actualizados (solo los que no se pudieron recuperar)
    if len(df_aun_rechazados) > 0:
        # Actualizar razones de rechazo
        for idx, row in df_aun_rechazados.iterrows():
            razones = []
            if pd.isna(row.get('eps')):
                razones.append(f"EPS inválida: {row.get('eps_original', 'N/A')}")
            if pd.isna(row.get('municipio')):
                razones.append(f"Municipio inválido: {row.get('municipio_original', 'N/A')}")
            df_aun_rechazados.at[idx, 'razon_rechazo'] = ' | '.join(razones)
        
        df_rechazados_clean = df_aun_rechazados.where(pd.notna(df_aun_rechazados), None)
        records_rechazados = df_rechazados_clean.to_dict('records')
        
        with open('data/audit/registros_RECHAZADOS.json', 'w', encoding='utf-8') as f:
            json.dump(records_rechazados, f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_RECHAZADOS.json actualizado")
    
    # Guardar registros recuperados por separado (para auditoría)
    if len(df_recuperados) > 0:
        df_recuperados_clean = df_recuperados.where(pd.notna(df_recuperados), None)
        records_recuperados = df_recuperados_clean.to_dict('records')
        
        with open('data/audit/registros_RECUPERADOS.json', 'w', encoding='utf-8') as f:
            json.dump(records_recuperados, f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_RECUPERADOS.json creado (auditoría)")
    
    # 8. Generar reporte
    print("\n8. Generando reporte...")
    
    reporte = {
        'fecha_recuperacion': pd.Timestamp.now().isoformat(),
        'registros_originales_validos': len(df_validos),
        'registros_originales_rechazados': len(df_rechazados),
        'registros_recuperados': len(df_recuperados),
        'registros_aun_rechazados': len(df_aun_rechazados),
        'total_validos_final': len(df_todos_validos),
        'tasa_recuperacion': f"{len(df_recuperados)/len(df_rechazados)*100:.1f}%",
        'detalles': {
            'eps_recuperadas': eps_recuperadas,
            'municipios_recuperados': municipios_recuperados,
            'pacientes_con_info': len(pacientes_info)
        }
    }
    
    with open('data/audit/reporte_recuperacion.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/audit/reporte_recuperacion.json")
    
    # 9. Resumen final
    print("\n" + "="*80)
    print("✅ RECUPERACIÓN COMPLETADA")
    print("="*80)
    print(f"\nResultados:")
    print(f"  📊 Registros procesados: {len(df_rechazados):,}")
    print(f"  ✅ Recuperados: {len(df_recuperados):,} ({len(df_recuperados)/len(df_rechazados)*100:.1f}%)")
    print(f"  ⚠️  Aún rechazados: {len(df_aun_rechazados):,} ({len(df_aun_rechazados)/len(df_rechazados)*100:.1f}%)")
    print(f"\nDatos válidos totales:")
    print(f"  Antes: {len(df_validos):,}")
    print(f"  Después: {len(df_todos_validos):,}")
    print(f"  Incremento: +{len(df_recuperados):,} ({len(df_recuperados)/len(df_validos)*100:.1f}%)")
    print(f"\nArchivos actualizados:")
    print(f"  1. data/processed/trazabilidad_LIMPIA.json ({len(df_todos_validos):,} registros)")
    print(f"  2. data/audit/registros_RECHAZADOS.json ({len(df_aun_rechazados):,} registros)")
    print(f"  3. data/audit/registros_RECUPERADOS.json ({len(df_recuperados):,} registros)")
    print()

if __name__ == "__main__":
    recuperar_datos_faltantes()
