import pandas as pd
import re

def verify_global_normalization():
    print("Starting verification of normalization logic...")
    data = {
        'PROFESIONAL': [
            'YERIS APONTE', 
            'YERIS APONTE VEREDA', 
            'YERIS APONTE VEREDAS', 
            'Dr Yeris',
            'dr. yeris',
            'Dr. Yeris Aponte',
            'Otro Doc',
            'Yeris    Aponte'
        ],
        'VALOR': [1, 2, 3, 4, 5, 6, 7, 8]
    }
    df = pd.DataFrame(data)
    
    print("Original values:")
    print(df['PROFESIONAL'].tolist())
    
    # Simulate the normalization function
    if 'PROFESIONAL' in df.columns:
        # Standardize strings
        df['PROFESIONAL'] = df['PROFESIONAL'].astype(str).str.strip().str.upper()
        
        # Yeris Aponte unification
        # Catch: "YERIS APONTE", "YERIS APONTE VEREDAS", "DR YERIS"
        # Using a regex that handles "DR." with optional dot and space
        regex_pattern = r'(YERIS\s+APONTE|DR\.?\s*YERIS)'
        print(f"Applying regex: {regex_pattern}")
        
        mask_yeris = df['PROFESIONAL'].str.contains(regex_pattern, regex=True, na=False)
        df.loc[mask_yeris, 'PROFESIONAL'] = 'YERIS APONTE'
    
    print("\nNormalized values:")
    print(df['PROFESIONAL'].value_counts())
    
    # Assertions
    yeris_count = len(df[df['PROFESIONAL'] == 'YERIS APONTE'])
    print(f"\nCount of 'YERIS APONTE': {yeris_count}")
    
    expected_yeris_count = 6 # All except 'Otro Doc'
    # 'Yeris    Aponte' becomes 'YERIS    APONTE', might not match simple space regex if we don't normalize spaces first.
    # checking my regex: YERIS\s+APONTE matches one or more whitespace.
    
    if yeris_count >= 6:
        print("✅ SUCCESS: logic captured variations.")
    else:
        print("❌ FAILURE: logic missed some variations.")
        # Debug missed
        print("Missed items that should be Yeris:")
        print(df[df['PROFESIONAL'] != 'YERIS APONTE'])

if __name__ == "__main__":
    verify_global_normalization()
