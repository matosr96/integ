import gspread
import os
import json

class GoogleSheetsClient:
    def __init__(self, credentials_path='credentials.json'):
        """
        Inicializa el cliente de Google Sheets.
        Soporta tanto credenciales locales como Streamlit Cloud secrets.
        
        Args:
            credentials_path (str): Ruta al archivo JSON de credenciales de servicio.
        """
        try:
            # Intentar cargar desde Streamlit secrets (cuando está desplegado)
            import streamlit as st
            if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                credentials_dict = dict(st.secrets["gcp_service_account"])
                self.gc = gspread.service_account_from_dict(credentials_dict)
                print("Autenticación exitosa con Google Sheets (Streamlit Secrets).")
                return
        except (ImportError, KeyError, FileNotFoundError):
            pass  # Continuar con archivo local
        
        # Cargar desde archivo local (desarrollo)
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"No se encontró el archivo de credenciales en: {credentials_path}")
            
        try:
            self.gc = gspread.service_account(filename=credentials_path)
            print("Autenticación exitosa con Google Sheets (archivo local).")
        except Exception as e:
            raise Exception(f"Error al autenticar con Google Sheets: {e}")

    def get_sheet_data(self, sheet_name_or_url):
        """
        Obtiene todos los registros de una hoja de cálculo.
        
        Args:
            sheet_name_or_url (str): Nombre del archivo en Google Drive o la URL completa.
            
        Returns:
            list: Lista de diccionarios con los datos de la hoja.
        """
        try:
            # Intenta abrir por URL primero si parece una URL, si no por nombre
            if 'docs.google.com' in sheet_name_or_url:
                sh = self.gc.open_by_url(sheet_name_or_url)
            else:
                sh = self.gc.open(sheet_name_or_url)
            
            # Selecciona la primera hoja de trabajo por defecto
            worksheet = sh.sheet1
            
            # Obtiene todos los valores crudos para manejar headers duplicados o vacíos manualmente
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return []

            # Asumimos que la primera fila son los encabezados
            headers = all_values[0]
            rows = all_values[1:]
            
            # Limpiar encabezados para asegurar unicidad y que no estén vacíos
            clean_headers = []
            header_count = {}
            
            for i, h in enumerate(headers):
                h = str(h).strip()
                if not h:
                    h = f"Column_{i+1}"
                
                if h in header_count:
                    header_count[h] += 1
                    h = f"{h}_{header_count[h]}"
                else:
                    header_count[h] = 1
                clean_headers.append(h)
            
            # Construir lista de diccionarios usando los encabezados limpios
            data = []
            for row in rows:
                # Asegurarse de que la fila tenga la misma longitud que los headers
                # Rellenar con None si faltan columnas, o cortar si sobran (aunque get_all_values suele ser rectangular)
                row_data = row + [''] * (len(clean_headers) - len(row))
                record = dict(zip(clean_headers, row_data[:len(clean_headers)]))
                data.append(record)
            
            return data
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"Error: No se encontró la hoja de cálculo '{sheet_name_or_url}'.")
            print("Asegúrate de haber compartido la hoja con el email del Service Account.")
            return []
        except gspread.exceptions.APIError as api_error:
            if "This operation is not supported for this document" in str(api_error):
                print(f"\nError: El archivo '{sheet_name_or_url}' parece ser un archivo de Excel (.xlsx) alojado en Drive, no una Hoja de Cálculo de Google nativa.")
                print("SOLUCIÓN: Abre el archivo en tu navegador, ve a 'Archivo' > 'Guardar como hoja de cálculo de Google' y usa la URL del nuevo archivo.")
            else:
                print(f"Error de API de Google: {api_error}")
            return []
        except Exception as e:
            print(f"Error al leer datos: {e}")
            return []
