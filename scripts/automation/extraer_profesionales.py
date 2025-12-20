"""
Script mejorado para extraer, limpiar y ordenar información de profesionales desde Google Sheets
"""
import json
from google_sheets_client import GoogleSheetsClient

def extraer_y_ordenar_profesionales():
    """
    Extrae datos de la hoja de cálculo de profesionales, los limpia y ordena
    """
    # URL de la hoja de cálculo
    SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1cVVkrEbiN-enP6VGvAkrjhiqqGMDrPD87qEKQQvBojU/edit?usp=sharing'
    
    # Inicializar cliente
    print("Conectando a Google Sheets...")
    client = GoogleSheetsClient('credentials.json')
    
    # Obtener datos de la primera hoja
    print("Extrayendo datos...")
    data_raw = client.get_sheet_data(SPREADSHEET_URL)
    
    if not data_raw or len(data_raw) < 3:
        print("No se encontraron suficientes datos en la hoja")
        return
    
    print(f"\nTotal de filas extraidas: {len(data_raw)}")
    
    # La segunda fila (índice 1) contiene los encabezados reales
    encabezados_row = data_raw[1]
    
    # Mapear los nombres de columnas genéricos a los nombres reales
    mapeo_columnas = {}
    for key, value in encabezados_row.items():
        if value and value.strip():
            mapeo_columnas[key] = value.strip()
    
    print(f"\nEncabezados identificados:")
    for old_key, new_key in mapeo_columnas.items():
        print(f"  {old_key} -> {new_key}")
    
    # Procesar los datos desde la fila 3 en adelante (índice 2+)
    profesionales = []
    for i, row in enumerate(data_raw[2:], start=3):
        profesional = {}
        
        # Renombrar las columnas usando el mapeo
        for old_key, value in row.items():
            # Usar el nombre mapeado si existe, sino mantener el original
            new_key = mapeo_columnas.get(old_key, old_key)
            
            # Limpiar el valor
            if value:
                value = str(value).strip()
            
            # Solo agregar si tiene valor
            if value:
                profesional[new_key] = value
        
        # Solo agregar si tiene al menos un campo con datos
        if profesional:
            profesionales.append(profesional)
    
    print(f"\nTotal de profesionales procesados: {len(profesionales)}")
    
    # Guardar datos sin ordenar
    with open('profesionales_raw.json', 'w', encoding='utf-8') as f:
        json.dump(profesionales, f, ensure_ascii=False, indent=2)
    print("\n[OK] Datos sin ordenar guardados en: profesionales_raw.json")
    
    # Ordenar por nombre
    nombre_key = 'NOMBRE PROFESIONAL'
    
    if nombre_key in profesionales[0] if profesionales else False:
        profesionales_ordenados = sorted(
            profesionales, 
            key=lambda x: str(x.get(nombre_key, '')).strip().upper()
        )
        print(f"\n[OK] Profesionales ordenados por: {nombre_key}")
    else:
        profesionales_ordenados = profesionales
        print("\n[AVISO] No se encontro columna de nombre, datos sin ordenar")
    
    # Guardar datos ordenados
    with open('profesionales_ordenados.json', 'w', encoding='utf-8') as f:
        json.dump(profesionales_ordenados, f, ensure_ascii=False, indent=2)
    print("[OK] Datos ordenados guardados en: profesionales_ordenados.json")
    
    # Crear también un CSV limpio
    import csv
    if profesionales_ordenados:
        # Obtener todas las columnas únicas
        todas_columnas = set()
        for prof in profesionales_ordenados:
            todas_columnas.update(prof.keys())
        
        columnas_ordenadas = sorted(todas_columnas)
        
        with open('profesionales_ordenados.csv', 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columnas_ordenadas)
            writer.writeheader()
            writer.writerows(profesionales_ordenados)
        
        print("[OK] Datos ordenados guardados en: profesionales_ordenados.csv")
    
    # Mostrar resumen
    print("\n" + "="*70)
    print("RESUMEN DE DATOS EXTRAIDOS Y ORDENADOS")
    print("="*70)
    print(f"Total de profesionales: {len(profesionales)}")
    
    if profesionales_ordenados:
        # Obtener estadísticas de columnas
        columnas_completas = {}
        for prof in profesionales_ordenados:
            for col in prof.keys():
                columnas_completas[col] = columnas_completas.get(col, 0) + 1
        
        print(f"\nColumnas con datos:")
        for col, count in sorted(columnas_completas.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (count / len(profesionales_ordenados)) * 100
            print(f"  - {col}: {count}/{len(profesionales_ordenados)} ({porcentaje:.1f}%)")
        
        print(f"\n{'='*70}")
        print("PRIMEROS 5 PROFESIONALES (ORDENADOS ALFABETICAMENTE)")
        print("="*70)
        
        for i, prof in enumerate(profesionales_ordenados[:5], 1):
            print(f"\n{i}. {prof.get('NOMBRE PROFESIONAL', 'Sin nombre')}")
            for key, value in prof.items():
                if key != 'NOMBRE PROFESIONAL':  # Ya lo mostramos arriba
                    print(f"   - {key}: {value}")
    
    return profesionales_ordenados

if __name__ == "__main__":
    try:
        profesionales = extraer_y_ordenar_profesionales()
        print("\n" + "="*70)
        print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print("\nArchivos generados:")
        print("  1. profesionales_raw.json - Datos limpios sin ordenar")
        print("  2. profesionales_ordenados.json - Datos ordenados alfabeticamente")
        print("  3. profesionales_ordenados.csv - Datos en formato CSV")
    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
