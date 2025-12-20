# Guía de Configuración de Google Sheets API

Esta guía te ayudará a configurar las credenciales necesarias para que el sistema pueda acceder a tus hojas de cálculo de Google.

## Paso 1: Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Haz clic en el selector de proyectos (arriba a la izquierda)
3. Haz clic en "Nuevo Proyecto"
4. Ingresa un nombre: `Gestion-Terapeutica`
5. Haz clic en "Crear"

## Paso 2: Habilitar Google Sheets API

1. En el menú lateral, ve a "APIs y servicios" → "Biblioteca"
2. Busca "Google Sheets API"
3. Haz clic en el resultado
4. Haz clic en "Habilitar"

## Paso 3: Crear Cuenta de Servicio

1. Ve a "APIs y servicios" → "Credenciales"
2. Haz clic en "Crear credenciales" → "Cuenta de servicio"
3. Completa los campos:
   - **Nombre**: `sheets-reader`
   - **ID**: (se genera automáticamente)
   - **Descripción**: `Cuenta para leer hojas de cálculo`
4. Haz clic en "Crear y continuar"
5. En "Rol", selecciona "Editor" (opcional, puedes dejarlo vacío)
6. Haz clic en "Continuar" y luego "Listo"

## Paso 4: Generar Clave JSON

1. En la lista de cuentas de servicio, encuentra la que acabas de crear
2. Haz clic en el email de la cuenta de servicio
3. Ve a la pestaña "Claves"
4. Haz clic en "Agregar clave" → "Crear clave nueva"
5. Selecciona "JSON"
6. Haz clic en "Crear"
7. Se descargará automáticamente un archivo JSON

## Paso 5: Configurar el Proyecto

1. Renombra el archivo descargado a `credentials.json`
2. Muévelo a la carpeta raíz del proyecto (donde está `dashboard.py`)
3. **⚠️ IMPORTANTE**: Nunca subas este archivo a GitHub

## Paso 6: Compartir tu Hoja de Cálculo

1. Abre el archivo `credentials.json` con un editor de texto
2. Busca el campo `client_email`, se verá algo así:
   ```
   "client_email": "sheets-reader@gestion-terapeutica-xxxxx.iam.gserviceaccount.com"
   ```
3. Copia ese email completo
4. Abre tu Google Sheet
5. Haz clic en "Compartir" (botón verde arriba a la derecha)
6. Pega el email de la cuenta de servicio
7. Asegúrate de que tenga permisos de "Editor"
8. Desmarca "Notificar a las personas" (no es necesario)
9. Haz clic en "Compartir"

## Verificación

Para verificar que todo está configurado correctamente:

1. Ejecuta el dashboard:
   ```bash
   streamlit run dashboard.py
   ```

2. Ingresa el nombre o URL de tu hoja de cálculo

3. Si todo está bien, verás los datos cargados

## Solución de Problemas

### Error: "No se encontró el archivo de credenciales"
- Verifica que `credentials.json` esté en la carpeta raíz del proyecto
- Verifica que el nombre del archivo sea exactamente `credentials.json`

### Error: "SpreadsheetNotFound"
- Asegúrate de haber compartido la hoja con el email de la cuenta de servicio
- Verifica que el nombre o URL de la hoja sea correcto

### Error: "This operation is not supported for this document"
- Tu archivo es un Excel (.xlsx) en Drive, no una Hoja de Cálculo de Google
- Solución: Abre el archivo → "Archivo" → "Guardar como hoja de cálculo de Google"

## Seguridad

### ⚠️ Información Sensible

El archivo `credentials.json` contiene:
- Claves privadas de tu proyecto de Google Cloud
- Información de autenticación

**NUNCA**:
- ❌ Subas este archivo a GitHub
- ❌ Lo compartas públicamente
- ❌ Lo incluyas en capturas de pantalla

**SIEMPRE**:
- ✅ Mantenlo en tu máquina local
- ✅ Agrégalo a `.gitignore`
- ✅ Usa variables de entorno en producción

## Archivo de Ejemplo

Hemos incluido `credentials.json.example` como referencia de la estructura.

**NO** uses este archivo directamente, es solo un ejemplo.

## Soporte

Si tienes problemas con la configuración, verifica:
1. Que la API de Google Sheets esté habilitada
2. Que el archivo JSON esté en la ubicación correcta
3. Que la hoja esté compartida con el email correcto
4. Que tengas conexión a internet

Para más ayuda, consulta la [documentación oficial de gspread](https://docs.gspread.org/).
