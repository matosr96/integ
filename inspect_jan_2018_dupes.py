import json
import pandas as pd

def inspect_jan_2018():
    path = r"C:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\PROCESSED_JSON\01_INGRESOS_TERAPIAS_ENERO_2018.json"
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data['data']
    df = pd.DataFrame(records)
    
    # Check for rows that might be filler
    # Look for rows where Name is same as previous, but maybe other fields suggest it's a spacer
    # Or just print rows where 'sesiones' is null/0
    
    print(f"Total processed records: {len(df)}")
    
    print("\nRows with 0 or Null sessions:")
    suspicious = df[ (df['sesiones'].isna()) | (df['sesiones'] == 0) ]
    print(suspicious[['nombres', 'sesiones', 'sheet_name', 'profesional']].to_string())
    
    # Check for exact duplicates in all columns?
    dupes = df[df.duplicated(keep=False)]
    print(f"\nExact duplicates count: {len(dupes)}")
    if len(dupes) > 0:
        print(dupes.head(10).to_string())

if __name__ == "__main__":
    inspect_jan_2018()
