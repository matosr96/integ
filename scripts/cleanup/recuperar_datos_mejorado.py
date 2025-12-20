"""
Script de Recuperación Mejorado
- Busca por cédula Y por nombres+apellidos
- Elimina registros sin identificación (nombres, apellidos y cédula NULL)
"""

import pandas as pd
import json
from collections import Counter
from difflib import SequenceMatcher

def similar(a, b):
    """Calcula similitud entre dos strings"""
    if pd.isna(a) or pd.isna(b):
        return 0
    return SequenceMatcher(None, str(a).upper(), str(b).upper()).ratio()

def recuperar_datos_mejorado():
    """
    Recuperación mejorada con múltiples estrategias:
    1. Por cédula
    2. Por nombres + apellidos (fuzzy matching)
    3. Elimina registros sin identificación
    """
    
    print("="*80)
    print("RECUPERACIÓN MEJORADA DE DATOS")
    print("="*80)
    
    # 1. Cargar datos
    print("\n1. Cargando datos...")
    with open('data/processed/trazabilidad_LIMPIA.json', 'r', encoding='utf-8') as f:
        validos = json.load(f)
    df_validos = pd.DataFrame(validos)
    
    with open('data/audit/registros_RECHAZADOS.json', 'r', encoding='utf-8') as f:
        rechazados = json.load(f)
    df_rechazados = pd.DataFrame(rechazados)
    
    print(f"   ✓ Válidos: {len(df_validos)}")
    print(f"   ✓ Rechazados: {len(df_rechazados)}")
    
    # 2. Eliminar registros sin identificación
    print("\n2. Eliminando registros sin identificación...")
    
    antes_eliminacion = len(df_rechazados)
    
    # Registros sin nombres, apellidos Y cédula
    sin_identificacion = df_rechazados[
        (df_rechazados['nombres'].isna() | (df_rechazados['nombres'] == '')) &
        (df_rechazados['apellidos'].isna() | (df_rechazados['apellidos'] == '')) &
        (df_rechazados['numero_id'].isna() | (df_rechazados['numero_id'] == ''))
    ]
    
    # Mantener solo los que tienen al menos alguna identificación
    df_rechazados = df_rechazados[
        ~((df_rechazados['nombres'].isna() | (df_rechazados['nombres'] == '')) &
          (df_rechazados['apellidos'].isna() | (df_rechazados['apellidos'] == '')) &
          (df_rechazados['numero_id'].isna() | (df_rechazados['numero_id'] == '')))
    ]
    
    eliminados = antes_eliminacion - len(df_rechazados)
    print(f"   ✓ Eliminados: {eliminados} registros sin identificación")
    print(f"   ✓ Restantes: {len(df_rechazados)} registros")
    
    # 3. Crear índices de búsqueda
    print("\n3. Creando índices de búsqueda...")
    
    # Índice por cédula
    cedula_index = {}
    for _, row in df_validos.iterrows():
        cedula = row.get('numero_id')
        if pd.notna(cedula) and str(cedula).strip():
            cedula = str(cedula).strip()
            if cedula not in cedula_index:
                cedula_index[cedula] = {'eps': [], 'municipio': []}
            
            if pd.notna(row.get('eps')):
                cedula_index[cedula]['eps'].append(row.get('eps'))
            if pd.notna(row.get('municipio')):
                cedula_index[cedula]['municipio'].append(row.get('municipio'))
    
    # Índice por nombres+apellidos
    nombre_index = {}
    for _, row in df_validos.iterrows():
        nombres = row.get('nombres')
        apellidos = row.get('apellidos')
        
        if pd.notna(nombres) and pd.notna(apellidos):
            nombres = str(nombres).strip().upper()
            apellidos = str(apellidos).strip().upper()
            key = f"{nombres}|{apellidos}"
            
            if key not in nombre_index:
                nombre_index[key] = {'eps': [], 'municipio': []}
            
            if pd.notna(row.get('eps')):
                nombre_index[key]['eps'].append(row.get('eps'))
            if pd.notna(row.get('municipio')):
                nombre_index[key]['municipio'].append(row.get('municipio'))
    
    print(f"   ✓ Índice por cédula: {len(cedula_index)} pacientes")
    print(f"   ✓ Índice por nombre: {len(nombre_index)} pacientes")
    
    # 4. Recuperar datos
    print("\n4. Recuperando datos...")
    
    recuperados_cedula = 0
    recuperados_nombre = 0
    recuperados_fuzzy = 0
    eps_recuperadas = 0
    municipios_recuperados = 0
    
    for idx, row in df_rechazados.iterrows():
        cambio = False
        
        # Estrategia 1: Búsqueda por cédula exacta
        cedula = row.get('numero_id')
        if pd.notna(cedula) and str(cedula).strip():
            cedula = str(cedula).strip()
            
            if cedula in cedula_index:
                info = cedula_index[cedula]
                
                if pd.isna(row.get('eps')) and info['eps']:
                    eps_mas_comun = Counter(info['eps']).most_common(1)[0][0]
                    df_rechazados.at[idx, 'eps'] = eps_mas_comun
                    eps_recuperadas += 1
                    cambio = True
                
                if pd.isna(row.get('municipio')) and info['municipio']:
                    mun_mas_comun = Counter(info['municipio']).most_common(1)[0][0]
                    df_rechazados.at[idx, 'municipio'] = mun_mas_comun
                    municipios_recuperados += 1
                    cambio = True
                
                if cambio:
                    recuperados_cedula += 1
                    continue
        
        # Estrategia 2: Búsqueda por nombres+apellidos exactos
        nombres = row.get('nombres')
        apellidos = row.get('apellidos')
        
        if pd.notna(nombres) and pd.notna(apellidos):
            nombres = str(nombres).strip().upper()
            apellidos = str(apellidos).strip().upper()
            key = f"{nombres}|{apellidos}"
            
            if key in nombre_index:
                info = nombre_index[key]
                
                if pd.isna(row.get('eps')) and info['eps']:
                    eps_mas_comun = Counter(info['eps']).most_common(1)[0][0]
                    df_rechazados.at[idx, 'eps'] = eps_mas_comun
                    eps_recuperadas += 1
                    cambio = True
                
                if pd.isna(row.get('municipio')) and info['municipio']:
                    mun_mas_comun = Counter(info['municipio']).most_common(1)[0][0]
                    df_rechazados.at[idx, 'municipio'] = mun_mas_comun
                    municipios_recuperados += 1
                    cambio = True
                
                if cambio:
                    recuperados_nombre += 1
                    continue
        
        # Estrategia 3: Fuzzy matching por nombres+apellidos (solo si no se recuperó antes)
        if not cambio and pd.notna(nombres) and pd.notna(apellidos):
            mejor_match = None
            mejor_score = 0
            
            for key_valido, info in nombre_index.items():
                nombres_valido, apellidos_valido = key_valido.split('|')
                
                # Calcular similitud
                sim_nombres = similar(nombres, nombres_valido)
                sim_apellidos = similar(apellidos, apellidos_valido)
                score = (sim_nombres + sim_apellidos) / 2
                
                # Umbral de 0.85 (85% de similitud)
                if score > mejor_score and score >= 0.85:
                    mejor_score = score
                    mejor_match = info
            
            if mejor_match:
                if pd.isna(row.get('eps')) and mejor_match['eps']:
                    eps_mas_comun = Counter(mejor_match['eps']).most_common(1)[0][0]
                    df_rechazados.at[idx, 'eps'] = eps_mas_comun
                    eps_recuperadas += 1
                    cambio = True
                
                if pd.isna(row.get('municipio')) and mejor_match['municipio']:
                    mun_mas_comun = Counter(mejor_match['municipio']).most_common(1)[0][0]
                    df_rechazados.at[idx, 'municipio'] = mun_mas_comun
                    municipios_recuperados += 1
                    cambio = True
                
                if cambio:
                    recuperados_fuzzy += 1
    
    total_recuperados = recuperados_cedula + recuperados_nombre + recuperados_fuzzy
    
    print(f"   ✓ Por cédula: {recuperados_cedula}")
    print(f"   ✓ Por nombre exacto: {recuperados_nombre}")
    print(f"   ✓ Por fuzzy matching: {recuperados_fuzzy}")
    print(f"   ✓ Total recuperados: {total_recuperados}")
    print(f"   ✓ EPS recuperadas: {eps_recuperadas}")
    print(f"   ✓ Municipios recuperados: {municipios_recuperados}")
    
    # 5. Separar válidos y rechazados
    print("\n5. Separando registros...")
    
    df_recuperados = df_rechazados[
        (df_rechazados['eps'].notna()) & (df_rechazados['municipio'].notna())
    ].copy()
    
    df_aun_rechazados = df_rechazados[
        (df_rechazados['eps'].isna()) | (df_rechazados['municipio'].isna())
    ].copy()
    
    print(f"   ✓ Recuperados: {len(df_recuperados)}")
    print(f"   ✓ Aún rechazados: {len(df_aun_rechazados)}")
    
    # 6. Combinar con válidos
    print("\n6. Combinando datos...")
    
    if 'razon_rechazo' in df_recuperados.columns:
        df_recuperados = df_recuperados.drop(columns=['razon_rechazo'])
    
    df_todos_validos = pd.concat([df_validos, df_recuperados], ignore_index=True)
    
    print(f"   ✓ Total válidos: {len(df_todos_validos)}")
    
    # 7. Guardar archivos
    print("\n7. Guardando archivos...")
    
    # Válidos
    df_validos_clean = df_todos_validos.where(pd.notna(df_todos_validos), None)
    with open('data/processed/trazabilidad_LIMPIA.json', 'w', encoding='utf-8') as f:
        json.dump(df_validos_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/processed/trazabilidad_LIMPIA.json ({len(df_todos_validos)} registros)")
    
    # Rechazados
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
    
    # Recuperados (auditoría)
    if len(df_recuperados) > 0:
        df_recuperados_clean = df_recuperados.where(pd.notna(df_recuperados), None)
        with open('data/audit/registros_RECUPERADOS.json', 'w', encoding='utf-8') as f:
            json.dump(df_recuperados_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_RECUPERADOS.json ({len(df_recuperados)} registros)")
    
    # Eliminados (auditoría)
    if len(sin_identificacion) > 0:
        sin_id_clean = sin_identificacion.where(pd.notna(sin_identificacion), None)
        with open('data/audit/registros_ELIMINADOS.json', 'w', encoding='utf-8') as f:
            json.dump(sin_id_clean.to_dict('records'), f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_ELIMINADOS.json ({len(sin_identificacion)} registros)")
    
    # 8. Reporte
    print("\n8. Generando reporte...")
    
    reporte = {
        'fecha': pd.Timestamp.now().isoformat(),
        'registros_originales_rechazados': antes_eliminacion,
        'registros_eliminados_sin_id': eliminados,
        'registros_procesados': len(df_rechazados),
        'recuperacion': {
            'por_cedula': recuperados_cedula,
            'por_nombre_exacto': recuperados_nombre,
            'por_fuzzy_matching': recuperados_fuzzy,
            'total': total_recuperados
        },
        'resultados': {
            'recuperados': len(df_recuperados),
            'aun_rechazados': len(df_aun_rechazados),
            'total_validos_final': len(df_todos_validos)
        },
        'tasa_recuperacion': f"{len(df_recuperados)/len(df_rechazados)*100:.1f}%"
    }
    
    with open('data/audit/reporte_recuperacion_mejorado.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/audit/reporte_recuperacion_mejorado.json")
    
    # 9. Resumen
    print("\n" + "="*80)
    print("✅ RECUPERACIÓN MEJORADA COMPLETADA")
    print("="*80)
    print(f"\nProcesamiento:")
    print(f"  📊 Rechazados originales: {antes_eliminacion:,}")
    print(f"  🗑️  Eliminados sin ID: {eliminados:,}")
    print(f"  🔍 Procesados: {len(df_rechazados):,}")
    print(f"\nRecuperación:")
    print(f"  🔑 Por cédula: {recuperados_cedula:,}")
    print(f"  👤 Por nombre exacto: {recuperados_nombre:,}")
    print(f"  🔄 Por fuzzy matching: {recuperados_fuzzy:,}")
    print(f"  ✅ Total recuperados: {total_recuperados:,} ({len(df_recuperados)/len(df_rechazados)*100:.1f}%)")
    print(f"\nResultado final:")
    print(f"  ✅ Válidos totales: {len(df_todos_validos):,}")
    print(f"  ⚠️  Aún rechazados: {len(df_aun_rechazados):,}")
    print(f"  🗑️  Eliminados: {eliminados:,}")
    print()

if __name__ == "__main__":
    recuperar_datos_mejorado()
