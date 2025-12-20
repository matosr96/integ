# Despliegue en Streamlit Cloud

## Pasos Rápidos

### 1. Subir código a GitHub
```bash
git add .
git commit -m "Preparado para Streamlit Cloud"
git push origin master
```

### 2. Ir a Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con GitHub
3. Haz clic en "New app"

### 3. Configurar la App
- **Repository**: Selecciona tu repositorio
- **Branch**: `master` (o `main`)
- **Main file path**: `dashboard.py`

### 4. Configurar Secrets

En la sección **Advanced settings** → **Secrets**, pega tu configuración en formato TOML.

**Sigue la guía en**: `STREAMLIT_SECRETS_GUIDE.md`

### 5. Deploy!

Haz clic en **Deploy**. La app estará lista en 2-3 minutos.

## URL de tu App

Una vez desplegada, tendrás una URL como:
```
https://tu-usuario-gestion-terapeutica.streamlit.app
```

## Actualizar la App

Cada vez que hagas `git push`, Streamlit Cloud actualizará automáticamente tu app.

## Solución de Problemas

### Error: "No module named 'gspread'"
- Verifica que `requirements.txt` esté en el repositorio
- Streamlit Cloud instala automáticamente las dependencias

### Error: "FileNotFoundError: credentials.json"
- Asegúrate de haber configurado los Secrets correctamente
- Verifica que el formato TOML sea correcto

### Error: "SpreadsheetNotFound"
- Verifica que hayas compartido la hoja con el email de la cuenta de servicio
- El email está en `client_email` de tus credenciales

## Hacer la App Privada

Por defecto, la app es pública. Para hacerla privada:

1. Ve a la configuración de tu app en Streamlit Cloud
2. En **Sharing**, selecciona "Private"
3. Solo tú y las personas que invites podrán acceder

## Agregar Autenticación (Opcional)

Si quieres agregar login, puedes usar:
- `streamlit-authenticator`
- Google OAuth
- Auth0

¿Necesitas ayuda con autenticación? Avísame.
