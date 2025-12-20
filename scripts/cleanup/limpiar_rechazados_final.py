"""
Eliminar registros rechazados con datos inválidos
"""

import json
import re

def es_numero_id_valido(numero_id):
    """Verifica si el número de ID es válido"""
    if not numero_id or numero_id in [None, '', 'nan']:
        return False
    
    numero_str = str(numero_id).strip().upper()
    
    # Descartar palabras comunes que no son IDs
    palabras_invalidas = [
        'LENGUAJE', 'TERAPIA', 'SESIONES', 'NOMBRE', 'APELLIDO',
        'DIRECCION', 'TELEFONO', 'EPS', 'MUNICIPIO', 'BARRIO',
        'FECHA', 'OBSERVACIONES', 'DIAGNOSTICO', 'PROFESIONAL',
        'TIPO', 'CANTIDAD', 'CEDULA', 'DOCUMENTO'
    ]
    
    if numero_str in palabras_invalidas:
        return False
    
    # Debe ser numérico o tener formato de cédula
    if re.match(r'^\d+$', numero_str):
        return True
    
    return False

def tiene_informacion_util(registro):
    """Verifica si el registro tiene información útil y válida"""
    
    # Verificar nombres y apellidos
    tiene_nombre = registro.get('nombres') not in [None, '', 'nan']
    tiene_apellido = registro.get('apellidos') not in [None, '', 'nan']
    
    # Verificar número de ID válido
    tiene_id_valido = es_numero_id_valido(registro.get('numero_id'))
    
    # Verificar otros campos útiles
    tiene_direccion = registro.get('direccion') not in [None, '', 'nan']
    tiene_telefono = registro.get('telefono') not in [None, '', 'nan']
    tiene_profesional = registro.get('profesional') not in [None, '', 'nan']
    tiene_diagnostico = registro.get('diagnostico') not in [None, '', 'nan']
    tiene_observaciones = registro.get('observaciones') not in [None, '', 'nan']
    
    # Debe tener al menos:
    # - Nombre O apellido
    # - Y al menos uno de: ID válido, dirección, teléfono, profesional, diagnóstico
    
    tiene_identificacion = tiene_nombre or tiene_apellido
    tiene_datos_adicionales = (tiene_id_valido or tiene_direccion or tiene_telefono or 
                               tiene_profesional or tiene_diagnostico or tiene_observaciones)
    
    return tiene_identificacion and tiene_datos_adicionales

def limpiar_rechazados():
    """Limpia registros rechazados eliminando los que no tienen información útil"""
    
    print("="*80)
    print("LIMPIEZA DE REGISTROS RECHAZADOS")
    print("="*80)
    
    # Cargar
    print("\n1. Cargando registros rechazados...")
    with open('data/audit/registros_RECHAZADOS.json', 'r', encoding='utf-8') as f:
        rechazados = json.load(f)
    print(f"   ✓ {len(rechazados)} registros")
    
    # Filtrar
    print("\n2. Filtrando registros...")
    
    rechazados_validos = []
    rechazados_invalidos = []
    
    for rec in rechazados:
        if tiene_informacion_util(rec):
            rechazados_validos.append(rec)
        else:
            rechazados_invalidos.append(rec)
    
    print(f"   ✓ Con información útil: {len(rechazados_validos)}")
    print(f"   ✓ Con datos inválidos: {len(rechazados_invalidos)}")
    
    # Mostrar ejemplos de inválidos
    if rechazados_invalidos:
        print(f"\n   Ejemplos de registros inválidos:")
        for i, rec in enumerate(rechazados_invalidos[:3], 1):
            print(f"   {i}. numero_id: {rec.get('numero_id')}, nombres: {rec.get('nombres')}, apellidos: {rec.get('apellidos')}")
    
    # Guardar
    print("\n3. Guardando archivos...")
    
    with open('data/audit/registros_RECHAZADOS.json', 'w', encoding='utf-8') as f:
        json.dump(rechazados_validos, f, indent=2, ensure_ascii=False)
    print(f"   ✓ data/audit/registros_RECHAZADOS.json ({len(rechazados_validos)} registros)")
    
    if rechazados_invalidos:
        with open('data/audit/registros_INVALIDOS_ELIMINADOS.json', 'w', encoding='utf-8') as f:
            json.dump(rechazados_invalidos, f, indent=2, ensure_ascii=False)
        print(f"   ✓ data/audit/registros_INVALIDOS_ELIMINADOS.json ({len(rechazados_invalidos)} registros)")
    
    # Resumen
    print("\n" + "="*80)
    print("✅ LIMPIEZA COMPLETADA")
    print("="*80)
    print(f"\nResultado:")
    print(f"  ✅ Rechazados válidos: {len(rechazados_validos)}")
    print(f"  🗑️  Registros inválidos eliminados: {len(rechazados_invalidos)}")
    print()

if __name__ == "__main__":
    limpiar_rechazados()
