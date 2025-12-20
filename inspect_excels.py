import pandas as pd
import pathlib
import os

base_path = pathlib.Path(r"c:\Users\APOYO TERAPEUTICO\Documents\rep\integ\DATA\TRAZABILIDADES")

def get_sample_files(base_path):
    samples = []
    # Try to get one file from each year folder if possible
    for year_dir in base_path.glob("*"):
        if year_dir.is_dir():
            files = list(year_dir.glob("*.xlsx"))
            if files:
                # Pick the first one that doesn't start with ~$ (temp file)
                for f in files:
                    if not f.name.startswith("~$"):
                        samples.append(f)
                        break
    return samples

def inspect_file(file_path):
    print(f"\n--- Inspecting: {file_path.relative_to(base_path)} ---")
    try:
        # Read header only
        df = pd.read_excel(file_path, nrows=0)
        print("Columns:")
        for col in df.columns:
            print(f"  - {col}")
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    samples = get_sample_files(base_path)
    print(f"Found {len(samples)} sample files.")
    for s in samples:
        inspect_file(s)
