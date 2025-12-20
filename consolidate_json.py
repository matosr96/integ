import json
import pathlib
import pandas as pd

PROCESSED_DIR = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\PROCESSED_JSON")
OUTPUT_FILE = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\trazabilidad_consolidada.json")

def consolidate_data():
    all_records = []
    files = list(PROCESSED_DIR.glob("*.json"))
    print(f"Found {len(files)} JSON files to consolidate.")
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                
            # Extract metadata
            source_file = content.get("source_file", "unknown")
            year_folder = content.get("year_folder", "unknown")
            data = content.get("data", [])
            
            # Enrich records with metadata
            for record in data:
                record["source_file"] = source_file
                record["year_folder"] = year_folder
                all_records.append(record)
                
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            
    print(f"Total records collected: {len(all_records)}")
    
    # Save consolidated JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)
        
    print(f"Consolidated data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    if PROCESSED_DIR.exists():
        consolidate_data()
    else:
        print(f"Directory {PROCESSED_DIR} does not exist.")
