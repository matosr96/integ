import pandas as pd
import os

def debug_excel_counts():
    file_path = r"C:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\TRAZABILIDADES\2018\01 INGRESOS TERAPIAS ENERO.xlsx"
    
    print(f"Analyzing: {file_path}")
    try:
        xls = pd.ExcelFile(file_path)
        print(f"Sheets found: {xls.sheet_names}")
        
        total_raw_rows = 0
        
        for sheet in xls.sheet_names:
            print(f"\n--- Sheet: {sheet} ---")
            # Read without header logic to see everything
            df = pd.read_excel(xls, sheet_name=sheet)
            print(f"Total Rows (pandas default): {len(df)}")
            
            # Print first few rows to visually check where data starts
            print("First 5 rows values:")
            print(df.head(5).values)
            
            non_empty_rows = df.dropna(how='all').shape[0]
            print(f"Non-empty rows: {non_empty_rows}")
            total_raw_rows += non_empty_rows

        print(f"\nTotal Non-Empty Rows in Workbook: {total_raw_rows}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_excel_counts()
