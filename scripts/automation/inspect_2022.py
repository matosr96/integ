import pandas as pd
import pathlib

file_path = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\TRAZABILIDADES\2022\01 INGRESOS TERAPIAS ENERO 2022.xlsx")

def inspect_file(file_path):
    print(f"\n--- Inspecting First 5 rows: {file_path.name} ---")
    try:
        df = pd.read_excel(file_path, header=None, nrows=5)
        print(df.to_string())
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    inspect_file(file_path)
