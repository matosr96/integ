import json
import pathlib
import pandas as pd

PROCESSED_DIR = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\PROCESSED_JSON")

def verify_2018():
    files_2018 = list(PROCESSED_DIR.glob("*_2018.json"))
    print(f"Found {len(files_2018)} JSON files for 2018.")
    
    valid_count = 0
    records_count = 0
    
    for file_path in files_2018:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                
            data = content.get("data", [])
            records = len(data)
            print(f"[OK] {file_path.name}: {records} records")
            
            # Check a few random fields in the first record if exists
            if records > 0:
                first = data[0]
                # print(f"   Sample: {first.get('nombres')} {first.get('apellidos')}")
                
            valid_count += 1
            records_count += records
            
        except json.JSONDecodeError:
            print(f"[ERROR] {file_path.name}: JSON Decode Error (likely truncated)")
        except Exception as e:
            print(f"[ERROR] {file_path.name}: {e}")

    print(f"\nSummary 2018: {valid_count}/{len(files_2018)} valid files. Total Records: {records_count}")

if __name__ == "__main__":
    verify_2018()
