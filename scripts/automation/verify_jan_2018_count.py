import json
import pandas as pd
import os

def verify_jan_2018_count():
    file_path = r"C:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\PROCESSED_JSON\01_INGRESOS_TERAPIAS_ENERO_2018.json"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        records = data.get('data', [])
        df = pd.DataFrame(records)
        
        print(f"Total Records in File: {len(df)}")
        
        # Method 1: Unique IDs
        if 'numero_id' in df.columns:
            unique_ids = df['numero_id'].dropna().unique()
            print(f"Unique IDs found: {len(unique_ids)}")
            
        # Method 2: Unique Names (in case IDs are missing or 0)
        if 'nombres' in df.columns:
            unique_names = df['nombres'].dropna().unique()
            print(f"Unique Names found: {len(unique_names)}")
            
        # Method 3: Combined Name+ID for robustness
        # Clean data first
        df['clean_id'] = df['numero_id'].astype(str).str.replace(r'\.0$', '', regex=True)
        df['clean_name'] = df['nombres'].astype(str).str.strip().str.upper()
        
        # Group by ID
        unique_patients = df.groupby('clean_id').first()
        print(f"\nUnique Patients (Grouped by ID): {len(unique_patients)}")
        
        # Show first 5 and last 5 IDs for sanity check
        print("\nSample IDs found:")
        print(sorted(df['clean_id'].unique())[:5])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_jan_2018_count()
