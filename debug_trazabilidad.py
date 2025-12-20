import pandas as pd
import os
import re

def debug_files():
    base_path = os.path.join("DATA", "TRAZABILIDADES")
    years_to_check = ['2019', '2020', '2021']
    
    print("--- INICIANDO DIAGNÓSTICO DE ARCHIVOS ANTIGUOS ---")
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.xlsx') and not file.startswith('~$'):
                # Check if file belongs to target years
                year_match = re.search(r'\\(\d{4})\\', os.path.join(root, file))
                if year_match:
                    year = year_match.group(1)
                    if year in years_to_check:
                        file_path = os.path.join(root, file)
                        print(f"\nAnalizando: {file} (Año: {year})")
                        try:
                            df = pd.read_excel(file_path, nrows=5) # Solo leer cabeceras
                            print("Columnas encontradas:")
                            print(list(df.columns))
                            
                            # Verificar si tiene columnas mapeables
                            potential_cols = ['CANTIDAD', '# TERAPIAS', 'SESIONES', 'NOMBRES', 'NOMBRE', 'PACIENTE']
                            found = [c for c in df.columns if any(p in str(c).upper() for p in potential_cols)]
                            print(f"Columnas clave detectadas: {found}")
                            
                        except Exception as e:
                            print(f"Error leyendo archivo: {e}")
                            
if __name__ == "__main__":
    debug_files()
