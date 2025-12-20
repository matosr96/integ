import pandas as pd
import sqlite3
import os
from trazabilidad_utils import scan_trazabilidades

def main():
    print("Iniciando consolidación de trazabilidades...")
    base_path = os.path.join("DATA", "TRAZABILIDADES")
    
    # 1. Obtener datos consolidados usando la lógica existente
    # Nota: scan_trazabilidades ya maneja la recursividad y normalización de columnas
    try:
        df = scan_trazabilidades(base_path)
    except Exception as e:
        print(f"Error al escanear los archivos: {e}")
        return

    if df.empty:
        print("No se encontraron registros para consolidar.")
        return

    print(f"Se han procesado {len(df)} registros.")

    # 2. Exportar a CSV (Para Excel)
    csv_path = os.path.join("DATA", "trazabilidad_historica_consolidada.csv")
    print(f"Guardando CSV en: {csv_path}")
    try:
        # Usamos utf-8-sig para que Excel abra correctamente los caracteres latinos
        df.to_csv(csv_path, index=False, encoding='utf-8-sig', sep=';')
        print("CSV guardado exitosamente.")
    except Exception as e:
        print(f"Error guardando CSV: {e}")

    # 3. Exportar a SQLite (Para el Sistema/Dashboard)
    db_path = os.path.join("DATA", "trazabilidad.db")
    print(f"Guardando Base de Datos en: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        # Convertir fechas a string para SQLite (manejo robusto)
        df_sql = df.copy()
        
        # 1. Convertir explícitamente columnas conocidas de fecha
        date_cols = ['FECHA_INICIO', 'FECHA_EGRESO']
        for col in date_cols:
            if col in df_sql.columns:
                df_sql[col] = df_sql[col].astype(str)

        # 2. Convertir cualquier otra columna datetime detectada
        for col in df_sql.columns:
            if pd.api.types.is_datetime64_any_dtype(df_sql[col]):
               df_sql[col] = df_sql[col].astype(str)
            # También verificar objetos que podrían ser timestamps
            elif df_sql[col].dtype == 'object':
               try:
                   # Intentar convertir una muestra
                   if not df_sql[col].empty and isinstance(df_sql[col].iloc[0], (pd.Timestamp, datetime.datetime)):
                       df_sql[col] = df_sql[col].astype(str)
               except:
                   pass
            
        # Reemplazamos la tabla si existe
        df_sql.to_sql('trazabilidad', conn, if_exists='replace', index=False)
        conn.close()
        print("Base de datos creada exitosamente.")
    except Exception as e:
        print(f"Error guardando DB: {e}")

    print("\nProceso finalizado.")
    print("-" * 30)
    print(f"Total Registros: {len(df)}")
    print(f"Ubicación CSV: {os.path.abspath(csv_path)}")
    print(f"Ubicación DB: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    main()
