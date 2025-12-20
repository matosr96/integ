"""
Eliminar registros completamente vacíos de rechazados
"""

import json
import pandas as pd

def eliminar_registros_vacios():
    """Elimina registros que no tienen ninguna información útil"""
    
    print("="*80)
    print("ELIMINACIÓN DE REGISTROS VACÍOS")
    print("="*80)
    
    # Cargar rechazados
    print("\n1. Cargando registros rechazados...")
    with open('data/audit/registros_RECHAZADOS.json', 'r', encoding='utf-8') as f:
        rechazados = json.load(f)
    print(f"   ✓ {len(rechazados)} registros")
    
    # Filtrar registros con información
    print("\n2. Filtrando registros...")
    
    campos_importantes = [
        'nombres', 'apellidos', 'numero_id', 'eps', 'municipio',
        'direccion', 'telefono', 'profesional', 'diagnostico',
        'fecha_ingreso', 'fecha_egreso', 'observaciones'
    ]
    
    rechazados_con_info = []
    rechazados_vacios = []
    
    for rec in rechazados:
        # Verificar si tiene al menos un campo con información
        tiene_info = any(
            rec.get(campo) not in [None, '', 0, 0.0]
            for campo in campos_importantes
        )
        
        if tiene_info:
            rechazados_con_info.append(rec)
        else:
            rechazados_vacios.append(rec)
    
    print(f"   ✓ Con información: {len(rechazados_con_info)}")
    print(f"   ✓ Completamente vacíos: {len(rechazados_vacios)}")
    
    # Guardar solo los que tienen información
    print("\n3. Guardando archivos...")
    
    with open('data/audit/registros_RECHAZADOS.json', 'w', encoding='utf-8') as f:
        json.dump(rechazados_con_info, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/audit/registros_RECHAZADOS.json ({len(rechazados_con_info)} registros)")
    
    # Guardar los vacíos por separado (auditoría)
    if rechazados_vacios:
        with open('data/audit/registros_VACIOS_ELIMINADOS.json', 'w', encoding='utf-8') as f:
            json.dump(rechazados_vacios, f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_VACIOS_ELIMINADOS.json ({len(rechazados_vacios)} registros)")
    
    # Resumen
    print("\n" + "="*80)
    print("✅ LIMPIEZA COMPLETADA")
    print("="*80)
    print(f"\nResultado:")
    print(f"  ✅ Rechazados con información: {len(rechazados_con_info)}")
    print(f"  🗑️  Registros vacíos eliminados: {len(rechazados_vacios)}")
    print()

if __name__ == "__main__":
    eliminar_registros_vacios()
