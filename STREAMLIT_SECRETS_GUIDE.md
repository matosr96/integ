# Guía: Configurar Secrets en Streamlit Cloud

## Paso 1: Abrir tu archivo credentials.json local

Abre el archivo `credentials.json` que tienes en tu computadora.

## Paso 2: Convertir a formato TOML

En Streamlit Cloud, en la sección **Secrets**, pega el siguiente formato:

```toml
# Google Sheets Credentials
[gcp_service_account]
type = "service_account"
project_id = "TU_PROJECT_ID"
private_key_id = "TU_PRIVATE_KEY_ID"
private_key = """-----BEGIN PRIVATE KEY-----
TU_PRIVATE_KEY_COMPLETA_AQUI
-----END PRIVATE KEY-----
"""
client_email = "TU_SERVICE_ACCOUNT_EMAIL@TU_PROJECT.iam.gserviceaccount.com"
client_id = "TU_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "TU_CERT_URL"
```

## Paso 3: Reemplazar los valores

Copia los valores de tu `credentials.json` y reemplázalos en el formato TOML:

1. **type**: Copia el valor de `"type"` de tu JSON
2. **project_id**: Copia el valor de `"project_id"`
3. **private_key_id**: Copia el valor de `"private_key_id"`
4. **private_key**: Copia TODO el valor de `"private_key"` (incluyendo `-----BEGIN PRIVATE KEY-----` y `-----END PRIVATE KEY-----`)
   - ⚠️ **IMPORTANTE**: Usa las tres comillas `"""` para mantener los saltos de línea
5. **client_email**: Copia el valor de `"client_email"`
6. **client_id**: Copia el valor de `"client_id"`
7. **client_x509_cert_url**: Copia el valor de `"client_x509_cert_url"`

## Ejemplo Real

Si tu `credentials.json` tiene:
```json
{
  "type": "service_account",
  "project_id": "mi-proyecto-123",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n",
  "client_email": "sheets@mi-proyecto.iam.gserviceaccount.com"
}
```

En Streamlit Secrets debe quedar:
```toml
[gcp_service_account]
type = "service_account"
project_id = "mi-proyecto-123"
private_key = """-----BEGIN PRIVATE KEY-----
MIIE...
-----END PRIVATE KEY-----
"""
client_email = "sheets@mi-proyecto.iam.gserviceaccount.com"
```

## Paso 4: Guardar

Haz clic en **Save** en Streamlit Cloud. Los cambios tardan ~1 minuto en aplicarse.

## ⚠️ Importante

- **NO** incluyas comas al final de las líneas (TOML no usa comas)
- **SÍ** usa comillas triples `"""` para la private_key
- **SÍ** mantén los saltos de línea en la private_key
- **NO** compartas estos valores públicamente

## Verificación

Una vez guardado, tu app podrá acceder a las credenciales con:
```python
import streamlit as st
import json

# El código ya está preparado para leer de secrets
credentials = dict(st.secrets["gcp_service_account"])
```

---

**¿Necesitas ayuda?** Si tienes problemas, verifica que:
1. No haya comas al final de las líneas
2. La private_key esté entre comillas triples
3. Todos los campos estén presentes
