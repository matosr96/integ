"""
Script de consolidación de datos de profesionales
Combina información de Google Sheets y contacts.csv
"""
import json
import csv
import re
from google_sheets_client import GoogleSheetsClient
from difflib import SequenceMatcher

def limpiar_telefono(telefono):
    """Limpia y normaliza números de teléfono"""
    if not telefono:
        return ""
    # Remover todo excepto dígitos
    telefono = re.sub(r'[^\d]', '', str(telefono))
    # Remover prefijo +57 si existe
    if telefono.startswith('57') and len(telefono) > 10:
        telefono = telefono[2:]
    return telefono

def normalizar_nombre(nombre):
    """Normaliza nombres para comparación"""
    if not nombre:
        return ""
    # Convertir a minúsculas y remover espacios extras
    nombre = str(nombre).lower().strip()
    # Remover acentos
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    for old, new in replacements.items():
        nombre = nombre.replace(old, new)
    return nombre

def similitud_nombres(nombre1, nombre2):
    """Calcula similitud entre dos nombres (0-1)"""
    n1 = normalizar_nombre(nombre1)
    n2 = normalizar_nombre(nombre2)
    return SequenceMatcher(None, n1, n2).ratio()

def cargar_contacts_csv(filepath):
    """Carga y procesa el archivo contacts.csv"""
    contactos = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extraer información relevante
            nombre_completo = f"{row.get('First Name', '')} {row.get('Middle Name', '')} {row.get('Last Name', '')}".strip()
            telefono = row.get('Phone 1 - Value', '')
            email = row.get('E-mail 1 - Value', '')
            
            # Filtrar solo fisioterapeutas (que empiezan con FT)
            if nombre_completo.upper().startswith('FT '):
                contactos.append({
                    'nombre_completo': nombre_completo,
                    'nombre_limpio': nombre_completo.replace('FT ', '').strip(),
                    'telefono': limpiar_telefono(telefono),
                    'telefono_original': telefono,
                    'email': email,
                    'first_name': row.get('First Name', ''),
                    'middle_name': row.get('Middle Name', ''),
                    'last_name': row.get('Last Name', '')
                })
    
    return contactos

def consolidar_datos():
    """
    Consolida datos de Google Sheets y contacts.csv
    """
    # URL de la hoja de cálculo
    SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1cVVkrEbiN-enP6VGvAkrjhiqqGMDrPD87qEKQQvBojU/edit?usp=sharing'
    
    print("="*70)
    print("CONSOLIDACION DE DATOS DE PROFESIONALES")
    print("="*70)
    
    # 1. Cargar datos de Google Sheets
    print("\n[1/4] Conectando a Google Sheets...")
    client = GoogleSheetsClient('credentials.json')
    data_raw = client.get_sheet_data(SPREADSHEET_URL)
    
    if not data_raw or len(data_raw) < 3:
        print("[ERROR] No se encontraron suficientes datos en Google Sheets")
        return
    
    # 2. Procesar datos de Google Sheets
    print("[2/4] Procesando datos de Google Sheets...")
    
    # La segunda fila contiene los encabezados reales
    encabezados_row = data_raw[1]
    mapeo_columnas = {}
    for key, value in encabezados_row.items():
        if value and value.strip():
            mapeo_columnas[key] = value.strip()
    
    # Agregar mapeos para columnas sin nombre
    mapeo_columnas['Column_1'] = 'ID'
    mapeo_columnas['Column_3'] = 'CEDULA'
    
    profesionales_sheets = []
    for i, row in enumerate(data_raw[2:], start=1):
        profesional = {'_fuente': 'Google Sheets', '_id_original': i}
        
        for old_key, value in row.items():
            new_key = mapeo_columnas.get(old_key, old_key)
            if value:
                value = str(value).strip()
                profesional[new_key] = value
        
        if profesional.get('NOMBRE PROFESIONAL') or profesional.get('CEDULA'):
            profesionales_sheets.append(profesional)
    
    print(f"   - Profesionales en Google Sheets: {len(profesionales_sheets)}")
    
    # 3. Cargar datos de contacts.csv
    print("[3/4] Cargando datos de contacts.csv...")
    contactos_csv = cargar_contacts_csv('contacts.csv')
    print(f"   - Fisioterapeutas en contacts.csv: {len(contactos_csv)}")
    
    # 4. Consolidar datos
    print("[4/4] Consolidando datos...")
    
    profesionales_consolidados = []
    matches_encontrados = 0
    
    for prof_sheets in profesionales_sheets:
        profesional_consolidado = prof_sheets.copy()
        profesional_consolidado['_match_encontrado'] = False
        profesional_consolidado['_match_score'] = 0
        
        nombre_sheets = prof_sheets.get('NOMBRE PROFESIONAL', '')
        telefono_sheets = limpiar_telefono(prof_sheets.get('TEL CONTACTO', ''))
        
        mejor_match = None
        mejor_score = 0
        
        # Buscar match en contacts.csv
        for contacto in contactos_csv:
            score = 0
            
            # Comparar por teléfono (más confiable)
            if telefono_sheets and contacto['telefono']:
                if telefono_sheets == contacto['telefono']:
                    score = 1.0  # Match perfecto por teléfono
                elif telefono_sheets in contacto['telefono'] or contacto['telefono'] in telefono_sheets:
                    score = 0.9
            
            # Comparar por nombre si no hay match por teléfono
            if score < 0.9 and nombre_sheets:
                similitud = similitud_nombres(nombre_sheets, contacto['nombre_limpio'])
                if similitud > 0.7:  # Umbral de similitud
                    score = max(score, similitud * 0.8)  # Peso menor que teléfono
            
            if score > mejor_score:
                mejor_score = score
                mejor_match = contacto
        
        # Si encontramos un match razonable, consolidar datos
        if mejor_match and mejor_score >= 0.7:
            profesional_consolidado['_match_encontrado'] = True
            profesional_consolidado['_match_score'] = round(mejor_score, 2)
            profesional_consolidado['_match_tipo'] = 'telefono' if mejor_score >= 0.9 else 'nombre'
            
            # Agregar datos de contacts.csv
            if not profesional_consolidado.get('TEL CONTACTO') and mejor_match['telefono_original']:
                profesional_consolidado['TEL CONTACTO'] = mejor_match['telefono_original']
            
            if not profesional_consolidado.get('MAIL') and mejor_match['email']:
                profesional_consolidado['MAIL'] = mejor_match['email']
            
            profesional_consolidado['_contacto_csv_nombre'] = mejor_match['nombre_completo']
            
            matches_encontrados += 1
        
        profesionales_consolidados.append(profesional_consolidado)
    
    # Ordenar por nombre
    profesionales_consolidados.sort(
        key=lambda x: normalizar_nombre(x.get('NOMBRE PROFESIONAL', ''))
    )
    
    # 5. Guardar resultados
    print("\n" + "="*70)
    print("GUARDANDO RESULTADOS")
    print("="*70)
    
    # Guardar JSON completo
    output_path = 'data/reference/profesionales_consolidados.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profesionales_consolidados, f, ensure_ascii=False, indent=2)
    print(f"[OK] Datos consolidados guardados en: {output_path}")
    
    # Guardar CSV limpio (sin campos internos)
    if profesionales_consolidados:
        csv_path = 'data/reference/profesionales_consolidados.csv'
        campos_excluir = ['_fuente', '_id_original', '_match_encontrado', '_match_score', '_match_tipo', '_contacto_csv_nombre']
        campos = [k for k in profesionales_consolidados[0].keys() if k not in campos_excluir]
        
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(profesionales_consolidados)
        print(f"[OK] Datos consolidados guardados en: {csv_path}")
    
    # 6. Mostrar resumen
    print("\n" + "="*70)
    print("RESUMEN DE CONSOLIDACION")
    print("="*70)
    print(f"Total de profesionales: {len(profesionales_consolidados)}")
    print(f"Matches encontrados con contacts.csv: {matches_encontrados} ({matches_encontrados/len(profesionales_consolidados)*100:.1f}%)")
    print(f"Sin match: {len(profesionales_consolidados) - matches_encontrados}")
    
    # Mostrar ejemplos de matches
    print(f"\n{'='*70}")
    print("EJEMPLOS DE PROFESIONALES CONSOLIDADOS (Primeros 5 con match)")
    print("="*70)
    
    count = 0
    for prof in profesionales_consolidados:
        if prof.get('_match_encontrado') and count < 5:
            count += 1
            print(f"\n{count}. {prof.get('NOMBRE PROFESIONAL', 'Sin nombre')}")
            print(f"   - Cedula: {prof.get('CEDULA', 'N/A')}")
            print(f"   - Telefono: {prof.get('TEL CONTACTO', 'N/A')}")
            print(f"   - Email: {prof.get('MAIL', 'N/A')}")
            print(f"   - Municipio: {prof.get('MUNICIPIO', 'N/A')}")
            print(f"   - Match: {prof.get('_match_tipo', 'N/A')} (score: {prof.get('_match_score', 0)})")
            print(f"   - Contacto CSV: {prof.get('_contacto_csv_nombre', 'N/A')}")
    
    return profesionales_consolidados

if __name__ == "__main__":
    try:
        profesionales = consolidar_datos()
        print("\n" + "="*70)
        print("[OK] CONSOLIDACION COMPLETADA EXITOSAMENTE")
        print("="*70)
    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
