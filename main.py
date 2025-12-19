from google_sheets_client import GoogleSheetsClient
import json

def main():
    print("--- Sistema de Conexión a Google Sheets ---")
    
    # Nombre del archivo de credenciales
    CREDENTIALS_FILE = 'credentials.json'
    
    try:
        # Inicializar cliente
        client = GoogleSheetsClient(CREDENTIALS_FILE)
        
        # SOLICITAR AL USUARIO: Nombre de la hoja o URL
        # Se ha establecido un valor por defecto basado en la solicitud del usuario
        default_sheet = "https://docs.google.com/spreadsheets/d/1jJAQwS0o-iDXjMZcJhqoO50eNwwxFzjd7auk04MELxg/edit?usp=sharing"
        sheet_input = input(f"Ingresa el nombre de la Google Sheet o su URL (Enter para usar la URL por defecto): ")
        
        if not sheet_input:
            sheet_input = default_sheet

        print(f"Intentando conectar a: {sheet_input}...")
        
        data = client.get_sheet_data(sheet_input)
        
        if data:
            print(f"\nSe encontraron {len(data)} registros:")
            # Imprimir los primeros 3 registros como ejemplo
            for i, row in enumerate(data[:3]):
                print(f"Fila {i+1}: {row}")
            
            if len(data) > 3:
                print("... y más registros.")
                
            # Opcional: Guardar en un JSON local para verificar
            with open('datos_descargados.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("\nDatos completos guardados en 'datos_descargados.json'")
            
        else:
            print("\nLa hoja está vacía o no se pudieron leer datos.")
            
    except FileNotFoundError as fnf:
        print(f"\nERROR CRÍTICO: {fnf}")
        print("Por favor, sigue las instrucciones en el README.md para generar tus credenciales.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()
