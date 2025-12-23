import pandas as pd
import json
import re

def is_date(val):
    """Check if value looks like a date"""
    val = str(val).strip()
    if val in ['', 'nan', 'None', 'NaT']: return False
    # Match patterns like YYYY-MM-DD or DD/MM/YYYY or YYYY/MM/DD
    if re.match(r'^\d{4}-\d{2}-\d{2}', val): return True
    if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}', val): return True
    if re.match(r'^\d{4}/\d{1,2}/\d{1,2}', val): return True
    return False

def is_numeric(val):
    """Check if value is numeric"""
    val = str(val).strip()
    if val in ['', 'nan', 'None']: return False
    try:
        float(val)
        return True
    except:
        return False

def is_phone(val):
    """Check if value looks like a phone number"""
    val = str(val).strip()
    if val in ['', 'nan', 'None']: return False
    # Phone numbers typically have 7-15 digits
    digits = re.sub(r'\D', '', val)
    return len(digits) >= 7 and len(digits) <= 15

def analyze():
    file_path = 'data/raw/trazabilidad_consolidada.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        records = data if isinstance(data, list) else data.get('data', [])
        df = pd.DataFrame(records)
        
        print(f"Total rows: {len(df)}")
        print("Columns:", df.columns.tolist())
        print("\n" + "="*80)
        print("VALIDACIÓN CAMPO POR CAMPO")
        print("="*80)
        
        # Define expected data types for each field
        validations = {
            'nombres': {'type': 'text', 'should_not_be': ['date', 'numeric']},
            'apellidos': {'type': 'text', 'should_not_be': ['date', 'numeric']},
            'tipo_id': {'type': 'text', 'should_not_be': ['date', 'numeric']},
            'numero_id': {'type': 'id', 'should_not_be': ['date']},
            'eps': {'type': 'text', 'should_not_be': ['date', 'numeric']},
            'municipio': {'type': 'text', 'should_not_be': ['date', 'numeric']},
            'direccion': {'type': 'text', 'should_not_be': ['date']},
            'telefono': {'type': 'phone', 'should_not_be': ['date']},
            'fecha_ingreso': {'type': 'date', 'should_be': 'date'},
            'fecha_egreso': {'type': 'date', 'should_be': 'date'},
            'profesional': {'type': 'text', 'should_not_be': ['date', 'numeric']},
            'observaciones': {'type': 'text', 'should_not_be': []},
            'sesiones': {'type': 'numeric', 'should_be': 'numeric'},
            'tipo_terapia': {'type': 'text', 'should_not_be': ['date']},
            'diagnostico': {'type': 'text', 'should_not_be': ['date']}
        }
        
        errors_found = []
        
        for col, rules in validations.items():
            if col not in df.columns:
                continue
                
            print(f"\n{'─'*80}")
            print(f"Campo: {col.upper()}")
            print(f"{'─'*80}")
            
            # Check for dates where they shouldn't be
            if 'date' in rules.get('should_not_be', []):
                bad_dates = df[df[col].astype(str).apply(is_date)]
                if not bad_dates.empty:
                    print(f"❌ ENCONTRADAS {len(bad_dates)} FECHAS en {col} (no debería tener fechas)")
                    print(f"   Ejemplos: {bad_dates[col].head(3).tolist()}")
                    errors_found.append({
                        'campo': col,
                        'error': 'fecha_invalida',
                        'count': len(bad_dates),
                        'ejemplos': bad_dates[[col, 'source_file']].head(3).to_dict('records')
                    })
            
            # Check for numbers where they shouldn't be
            if 'numeric' in rules.get('should_not_be', []):
                bad_nums = df[df[col].astype(str).apply(lambda x: is_numeric(x) and not is_date(x))]
                if not bad_nums.empty:
                    print(f"❌ ENCONTRADOS {len(bad_nums)} NÚMEROS en {col} (no debería tener números)")
                    print(f"   Ejemplos: {bad_nums[col].head(3).tolist()}")
                    errors_found.append({
                        'campo': col,
                        'error': 'numero_invalido',
                        'count': len(bad_nums),
                        'ejemplos': bad_nums[[col, 'source_file']].head(3).to_dict('records')
                    })
            
            # Check if dates are actually dates
            if rules.get('should_be') == 'date':
                non_null = df[df[col].notna() & (df[col].astype(str) != '') & (df[col].astype(str) != 'nan')]
                if not non_null.empty:
                    bad_dates = non_null[~non_null[col].astype(str).apply(is_date)]
                    if not bad_dates.empty:
                        print(f"❌ ENCONTRADOS {len(bad_dates)} VALORES NO-FECHA en {col} (debería ser fecha)")
                        print(f"   Ejemplos: {bad_dates[col].head(3).tolist()}")
                        errors_found.append({
                            'campo': col,
                            'error': 'no_es_fecha',
                            'count': len(bad_dates),
                            'ejemplos': bad_dates[[col, 'source_file']].head(3).to_dict('records')
                        })
            
            # Check if numbers are actually numbers
            if rules.get('should_be') == 'numeric':
                non_null = df[df[col].notna() & (df[col].astype(str) != '') & (df[col].astype(str) != 'nan')]
                if not non_null.empty:
                    bad_nums = non_null[~non_null[col].astype(str).apply(is_numeric)]
                    if not bad_nums.empty:
                        print(f"❌ ENCONTRADOS {len(bad_nums)} VALORES NO-NUMÉRICOS en {col} (debería ser número)")
                        print(f"   Ejemplos: {bad_nums[col].head(3).tolist()}")
                        errors_found.append({
                            'campo': col,
                            'error': 'no_es_numero',
                            'count': len(bad_nums),
                            'ejemplos': bad_nums[[col, 'source_file']].head(3).to_dict('records')
                        })
            
            # Show sample valid values
            valid_samples = df[df[col].notna() & (df[col].astype(str) != '') & (df[col].astype(str) != 'nan')][col].head(3).tolist()
            if valid_samples:
                print(f"✓ Ejemplos válidos: {valid_samples}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"RESUMEN DE ERRORES")
        print(f"{'='*80}")
        
        if errors_found:
            print(f"\n❌ Se encontraron {len(errors_found)} tipos de errores:")
            for err in errors_found:
                print(f"\n  • {err['campo']}: {err['error']} ({err['count']} registros)")
                print(f"    Archivos afectados:")
                for ej in err['ejemplos']:
                    print(f"      - {ej.get('source_file', 'N/A')}: {ej.get(err['campo'], 'N/A')}")
        else:
            print("\n✅ No se encontraron errores de tipo de datos")
        
        # Save error report
        if errors_found:
            with open('data/audit/error_report.json', 'w', encoding='utf-8') as f:
                json.dump(errors_found, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Reporte completo guardado en: data/audit/error_report.json")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze()
