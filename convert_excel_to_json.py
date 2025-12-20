import pandas as pd
import pathlib
import os
import json
import numpy as np

# Configuration
BASE_PATH = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\TRAZABILIDADES")
OUTPUT_DIR = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\PROCESSED_JSON")

# Standardized Column Names Mapping
# Key: Standardized Name, Value: List of possible column names in Excel
COLUMN_MAPPING = {
    "nombres": ["NOMBRE", "NOMBRES"],
    "apellidos": ["APELLIDO", "APELLIDOS"],
    "tipo_id": ["TIPO ID", "TIPO DE ID", "TIPO DE DOCUMENTO", "TIPO"],
    "numero_id": ["NUMERO ID", "NUMERO DE ID", "NUMERO", "ID"],
    "eps": ["EPS"],
    "diagnostico": ["DIAGNOSTICO"],
    "municipio": ["MUNICIPIO", "MUNICIPO DE ATENCION"],
    "direccion": ["DIRECCION", "DIRECCION DE ATENCION"],
    "telefono": ["TELEFONO"],
    "fecha_ingreso": ["FECHA DE INGRESO", "FECHA DE ENTREGA", "FECHA DE INICIO"],
    "fecha_egreso": ["FECHA DE EGRESO", "FECHA EGRESO"],
    "profesional": ["TERAPEUTA ENCARGADO", "PROFESIONAL", "TERAPEUTA ENTREGADO"],
    "observaciones": ["OBSERVACIONES", "OBSERVACION", "OBSERVACIONES AL PROCESO"],
    "sesiones": ["SESIONES", "SESIONES DE TERAPIAS", "# TERAPIAS", "CANTIDAD", "CANTIDAD TOTAL"],
    "tipo_terapia": ["TIPO DE TERAPIAS", "TIPO DE TERAPIA", "TIPO"]
}

def normalize_column_name(col_name):
    if not isinstance(col_name, str):
        return str(col_name)
    return col_name.strip().upper()

def find_header_row(file_path, nrows=20):
    """
    Attempts to find the header row by looking for key columns.
    Returns the dataframe starting from the correct header, or None if not found.
    """
    try:
        # Read the first few rows without header
        df_temp = pd.read_excel(file_path, header=None, nrows=nrows)
        
        # Flatten mapping values to a set of possible headers for quick lookup
        possible_headers = set()
        for variants in COLUMN_MAPPING.values():
            possible_headers.update(v for v in variants)

        best_row_idx = -1
        max_matches = 0

        for idx, row in df_temp.iterrows():
            # Convert row values to potential column names
            row_values = [normalize_column_name(val) for val in row.values if pd.notna(val)]
            
            # Count how many match our expected columns
            matches = sum(1 for val in row_values if val in possible_headers)
            
            # Heuristic: If we find at least 3 matches, it's likely the header
            if matches > max_matches and matches >= 3:
                max_matches = matches
                best_row_idx = idx

        if best_row_idx != -1:
            # Re-read the file with the correct header
            df = pd.read_excel(file_path, header=best_row_idx)
            return df
            
        # Fallback: Try reading with default header=0 if no better match found
        df = pd.read_excel(file_path, header=0)
        return df

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def standardize_dataframe(df):
    """
    Renames columns to standardized names and selects only relevant columns.
    """
    # Normalize current columns
    df.columns = [normalize_column_name(c) for c in df.columns]
    
    # Create a mapping from current file columns to standard columns
    rename_map = {}
    for standard_col, variants in COLUMN_MAPPING.items():
        for variant in variants:
            if variant in df.columns:
                rename_map[variant] = standard_col
                break # Take the first match
    
    # Rename columns
    df = df.rename(columns=rename_map)
    
    # Keep only standard columns that exist in the df
    cols_to_keep = [c for c in COLUMN_MAPPING.keys() if c in df.columns]
    df = df[cols_to_keep]
    
    # Add missing standard columns as null
    for col in COLUMN_MAPPING.keys():
        if col not in df.columns:
            df[col] = None
            
    return df

import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle pandas NaT and numpy NaT - check this first!
        if pd.isna(obj):
            return None
            
        # Handle pandas Timestamps and numpy datetime64
        if isinstance(obj, (pd.Timestamp, np.datetime64)):
            return obj.isoformat()
            
        # Handle standard datetime.datetime and datetime.date objects
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
            
        # Fallback for any other object that might have an isoformat method
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
            
        return super().default(obj)

def process_files():
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        
    files = list(BASE_PATH.rglob("*.xlsx"))
    print(f"Found {len(files)} Excel files.")
    
    processed_count = 0
    error_count = 0
    
    for file_path in files:
        if file_path.name.startswith("~$"):
            continue
            
        print(f"Processing: {file_path.relative_to(BASE_PATH)}")
        
        try:
            # Read all sheets
            xls = pd.ExcelFile(file_path)
            all_records = []
            
            for sheet_name in xls.sheet_names:
                # Skip hidden/system sheets if needed, though usually by name
                
                # We need to pass the sheet name to find_header_row logic
                # Updating find_header_row to accept sheet_name or refactoring here
                
                try:
                    # Read specific sheet to find header
                    # We can't use existing find_header_row easily because it takes a file_path
                    # Let's read a small chunk of the sheet first
                    df_temp = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=20)
                    
                    # Logic to find header (duplicated/adapted from find_header_row)
                    possible_headers = set()
                    for variants in COLUMN_MAPPING.values():
                        possible_headers.update(v for v in variants)

                    best_row_idx = -1
                    max_matches = 0

                    for idx, row in df_temp.iterrows():
                        row_values = [normalize_column_name(val) for val in row.values if pd.notna(val)]
                        matches = sum(1 for val in row_values if val in possible_headers)
                        if matches > max_matches and matches >= 3:
                            max_matches = matches
                            best_row_idx = idx

                    header_idx = best_row_idx if best_row_idx != -1 else 0
                    
                    # Read full sheet
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=header_idx)
                    
                    if df.empty:
                        continue

                    df_std = standardize_dataframe(df)
                    
                    # Forward-fill for merged/grouped cells (ALL relevant columns)
                    # Demographic columns
                    demographic_cols = ['nombres', 'apellidos', 'tipo_id', 'numero_id', 'eps', 'municipio', 'direccion', 'telefono']
                    # Therapy/Service columns that might also be merged
                    service_cols = ['sesiones', 'profesional', 'tipo_terapia', 'diagnostico']
                    # Combine all columns that need forward-fill
                    all_ffill_cols = demographic_cols + service_cols
                    
                    cols_to_fix = [c for c in all_ffill_cols if c in df_std.columns]
                    if cols_to_fix:
                        df_std[cols_to_fix] = df_std[cols_to_fix].ffill()
                    
                    # Fix: Clean/Standardize 'sesiones'
                    if 'sesiones' in df_std.columns:
                         # Using raw string for regex to avoid SyntaxWarning
                         df_std['sesiones'] = df_std['sesiones'].astype(str).str.extract(r'(\d+)').astype(float)

                    # Convert to records
                    sheet_records = df_std.to_dict(orient='records')
                    
                    # Clean and Add Metadata
                    for record in sheet_records:
                        clean_record = {}
                        for k, v in record.items():
                            if pd.isna(v):
                                clean_record[k] = None
                            else:
                                clean_record[k] = v
                        
                        # Add Sheet Metadata
                        clean_record['sheet_name'] = sheet_name
                        all_records.append(clean_record)
                        
                except Exception as e_sheet:
                    print(f"  Error processing sheet {sheet_name}: {e_sheet}")
                    continue

            if not all_records:
                print(f"  Skipping: No valid data found in any sheet.")
                error_count += 1
                continue

            # Filter out invalid or summary rows (Fix for over-counting)
            filtered_records = []
            for record in all_records:
                # 1. Check if name implies a footer/summary
                name_val = str(record.get('nombres', '')).upper()
                if any(x in name_val for x in ['TOTAL', 'SUBTOTAL', 'RESUMEN']):
                    continue
                
                # 2. Check if sessions is 0/None but was kept due to ffill? 
                # Actually, ffill is for demographics. If sessions is 0, it might be a spacer.
                # User wants 158 records. Valid records should have some therapy info.
                
                filtered_records.append(record)
            
            # Calculate Metadata Stats
            df_final = pd.DataFrame(filtered_records)
            unique_patients = 0
            total_sessions = 0
            
            if not df_final.empty:
                # Count unique via ID, fallback to Name
                if 'numero_id' in df_final.columns and df_final['numero_id'].notna().any():
                     unique_patients = df_final['numero_id'].nunique()
                elif 'nombres' in df_final.columns:
                     unique_patients = df_final['nombres'].nunique()
                
                if 'sesiones' in df_final.columns:
                    total_sessions = df_final['sesiones'].sum()

            # Metadata
            output_data = {
                "source_file": str(file_path.name),
                "source_path": str(file_path),
                "year_folder": file_path.parent.name,
                "summary": {
                    "total_records": len(filtered_records),
                    "total_unique_patients": int(unique_patients),
                    "total_sessions": float(total_sessions)
                },
                "data": filtered_records
            }
            
            # Save JSON
            json_name = f"{file_path.stem}_{file_path.parent.name}.json".replace(" ", "_")
            output_path = OUTPUT_DIR / json_name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, cls=DateTimeEncoder, ensure_ascii=False)
                
            processed_count += 1
            
        except Exception as e:
            print(f"  Error processing file: {e}")
            error_count += 1
            
    print(f"\nProcessing Complete. Processed: {processed_count}, Errors: {error_count}")

if __name__ == "__main__":
    process_files()
