# Instrucciones para Compartir la Hoja de Google Sheets

Para que el script pueda acceder a la hoja de cálculo, necesitas compartirla con la cuenta de servicio.

## Pasos:

1. **Abre la hoja de Google Sheets** en tu navegador:
   https://docs.google.com/spreadsheets/d/1cVVkrEbiN-enP6VGvAkrjhiqqGMDrPD87qEKQQvBojU/edit?usp=sharing

2. **Haz clic en el botón "Compartir"** (esquina superior derecha)

3. **Agrega este email** en el campo de compartir:
   ```
   sheets-reader@peerless-summit-480818-a2.iam.gserviceaccount.com
   ```

4. **Selecciona el permiso**: "Lector" (Viewer) es suficiente

5. **Haz clic en "Enviar"** o "Compartir"

6. **Ejecuta el script** nuevamente:
   ```
   python extraer_profesionales.py
   ```

## Nota:
Una vez que hayas compartido la hoja, el script podrá acceder a los datos y extraerlos automáticamente.
