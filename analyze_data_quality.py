import os
import json
import glob
from collections import defaultdict

def analyze_json_files(directory):
    files = glob.glob(os.path.join(directory, "*.json"))
    
    total_records = 0
    categories = defaultdict(int)
    file_stats = {}

    print(f"Analyzing {len(files)} files in {directory}...\n")

    for filepath in files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        data = []
        if isinstance(raw_data, list):
            data = raw_data
        elif isinstance(raw_data, dict):
            if 'data' in raw_data and isinstance(raw_data['data'], list):
                data = raw_data['data']
            else:
                # Try to find any list value that looks like records
                found = False
                for key, val in raw_data.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        data = val
                        found = True
                        break
                if not found:
                    print(f"Skipping {filename}: Could not find record list in dict keys: {list(raw_data.keys())}")
                    continue
        else:
            print(f"Skipping {filename}: Unknown structure {type(raw_data)}")
            continue

        file_valid = 0
        file_partial_prof = 0
        file_partial_session = 0
        file_empty = 0
        
        for record in data:
            total_records += 1
            
            # Helper to check if a value is "present" (not None, not empty string)
            def is_present(val):
                if val is None: return False
                if isinstance(val, str) and val.strip() == "": return False
                return True

            has_name = is_present(record.get('nombres')) or is_present(record.get('apellidos'))
            has_id = is_present(record.get('numero_id'))
            has_prof = is_present(record.get('profesional'))
            has_sessions = is_present(record.get('sesiones'))
            has_dates = is_present(record.get('fecha_ingreso')) or is_present(record.get('fecha_egreso'))

            if has_name and has_id:
                categories['Valid'] += 1
                file_valid += 1
            elif has_prof and has_dates and not has_name:
                categories['Partial (Professional/Dates only)'] += 1
                file_partial_prof += 1
            elif has_sessions and not has_name and not has_prof:
                categories['Partial (Sessions only)'] += 1
                file_partial_session += 1
            else:
                categories['Empty/Noise'] += 1
                if file_empty < 1 and "2018" in filename: # Debug specific file
                     # print(f"  [DEBUG] Noise in {filename}: {record}")
                     pass
                file_empty += 1
        
        file_stats[filename] = {
            'total': len(data),
            'valid': file_valid,
            'partial_prof': file_partial_prof,
            'partial_session': file_partial_session,
            'empty': file_empty
        }

    print("-" * 60)
    print(f"{'TOTAL SUMMARY':^60}")
    print("-" * 60)
    print(f"Total Records Scanned: {total_records}")
    for cat, count in categories.items():
        print(f"  {cat}: {count} ({count/total_records*100:.1f}%)")
    print("-" * 60)
    
    print("\nFILES WITH HIGH INCOMPLETE RATES (>10%):")
    for fname, stats in file_stats.items():
        if stats['total'] == 0: continue
        incomplete = stats['total'] - stats['valid']
        rate = incomplete / stats['total']
        if rate > 0.1:
             print(f"{fname}: {rate*100:.1f}% incomplete ({incomplete}/{stats['total']})")
             print(f"   - Valid: {stats['valid']}")
             print(f"   - Prof/Dates only: {stats['partial_prof']}")
             print(f"   - Sessions only: {stats['partial_session']}")
             print(f"   - Other/Empty: {stats['empty']}")

if __name__ == "__main__":
    analyze_json_files(r"C:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\PROCESSED_JSON")
