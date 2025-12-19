# Sistema de Gestión Terapéutica 🏥

Sistema web profesional para la gestión de rutas, pacientes y profesionales en servicios de terapia domiciliaria.

## 🌟 Características

### 📊 Dashboard Analítico
- Métricas clave en tiempo real (pacientes, sesiones, profesionales)
- Visualizaciones interactivas con Plotly
- Filtros por EPS, municipio y tipo de usuario
- Reportes ejecutivos en PDF

### 🚚 Gestión de Rutas
- Generación automática de hojas de ruta para profesionales
- Estadísticas detalladas por profesional:
  - Total de sesiones programadas
  - Distribución por EPS
  - Tipos de usuario (Eventos, Crónicos, Paliativos)
- Descarga individual o masiva (ZIP)
- Información completa: direcciones, teléfonos, diagnósticos

### 🔎 Explorador de Datos
- Tabla interactiva con todos los pacientes
- Filtros avanzados
- Exportación a CSV
- Reportes de facturación agrupados
- Bitácora de novedades

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- Cuenta de Google Cloud con API de Sheets habilitada
- Archivo de credenciales de servicio (`credentials.json`)

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/gestion-terapeutica.git
cd gestion-terapeutica
```

### Paso 2: Crear Entorno Virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Credenciales de Google Sheets

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto
3. Habilita la API de Google Sheets
4. Crea credenciales de cuenta de servicio
5. Descarga el archivo JSON de credenciales
6. Renómbralo a `credentials.json` y colócalo en la raíz del proyecto

**⚠️ IMPORTANTE**: El archivo `credentials.json` contiene información sensible y está excluido del control de versiones.

### Paso 5: Compartir tu Hoja de Cálculo

1. Abre el archivo `credentials.json`
2. Copia el email de la cuenta de servicio (campo `client_email`)
3. Comparte tu Google Sheet con ese email (permisos de Editor)

## 📖 Uso

### Ejecutar la Aplicación
```bash
streamlit run dashboard.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

### Configurar Origen de Datos

1. En la barra lateral, ingresa el **nombre exacto** de tu hoja de Google Sheets o la URL completa
   - Ejemplo: `01 INGRESOS TERAPIAS ENERO 2026`
   - O: `https://docs.google.com/spreadsheets/d/...`

2. El sistema cargará automáticamente los datos

### Navegar por los Módulos

Usa los botones de radio en la barra lateral para cambiar entre:
- **Dashboard Analítico**: Vista general y estadísticas
- **Gestión de Rutas**: Generación de PDFs para profesionales
- **Explorador de Datos**: Consultas y reportes detallados

## 📁 Estructura del Proyecto

```
integ/
├── dashboard.py                    # Aplicación principal
├── google_sheets_client.py         # Cliente para Google Sheets API
├── rutas_utils.py                  # Utilidades para generación de rutas
├── profesionales_component.py      # Componente de profesionales
├── consolidar_profesionales.py     # Script de consolidación de datos
├── extraer_profesionales.py        # Script de extracción
├── requirements.txt                # Dependencias
├── .gitignore                      # Archivos excluidos de Git
├── README.md                       # Este archivo
└── credentials.json               # ⚠️ NO INCLUIR EN GIT
```

## 🔒 Seguridad

### Archivos Sensibles Excluidos
El archivo `.gitignore` está configurado para excluir:
- `credentials.json` (credenciales de Google)
- Archivos de datos con información de pacientes
- Archivos temporales y caché

### Buenas Prácticas
- ✅ Nunca subas `credentials.json` a GitHub
- ✅ Usa variables de entorno para datos sensibles en producción
- ✅ Revisa los permisos de tu Google Sheet
- ✅ Mantén actualizadas las dependencias

## 🛠️ Tecnologías Utilizadas

- **Streamlit**: Framework web para Python
- **Pandas**: Manipulación de datos
- **Plotly**: Visualizaciones interactivas
- **gspread**: Cliente de Google Sheets
- **FPDF**: Generación de PDFs

## 📊 Formato de Datos Esperado

Tu Google Sheet debe contener las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| NOMBRE | Nombre del paciente |
| APELLIDOS | Apellidos del paciente |
| TIPO DE DOCUMENTO | CC, TI, etc. |
| NUMERO | Número de documento |
| EPS | Entidad promotora de salud |
| DIAGNOSTICO | Diagnóstico médico |
| MUNICIPIO | Municipio de residencia |
| TELEFONO | Teléfono de contacto |
| DIRECCION | Dirección completa |
| TIPO DE USUARIO | PERMANENTE, PALIATIVO, etc. |
| FECHA DE INGRESO | Fecha de inicio |
| FECHA DE EGRESO | Fecha de fin |
| CANTIDAD | Número de sesiones |
| TIPO DE TERAPIAS | TF, TR, TL, TO, TS |
| PROFESIONAL | Nombre del profesional asignado |
| NOVEDADES | Observaciones |

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es de uso interno. Contacta al administrador para más información.

## 📧 Contacto

Para soporte o preguntas, contacta al equipo de desarrollo.

## 🔄 Actualizaciones Recientes

### v2.2 (Diciembre 2024)
- ✨ Descarga de rutas en un solo clic
- 📊 Estadísticas detalladas por profesional
- 🎨 Rediseño completo de UI/UX
- 🗂️ Navegación modular mejorada

### v2.1
- 📈 Gráficos de distribución por EPS y tipo de usuario
- 📱 Preparación para integración WhatsApp

### v2.0
- 🚀 Nueva arquitectura modular
- 🎨 Interfaz profesional
- 📊 Dashboard analítico mejorado

## 🚧 Roadmap

- [ ] Integración con WhatsApp Business API
- [ ] Notificaciones automáticas
- [ ] Exportación a Excel con formato
- [ ] Historial de cambios
- [ ] Panel de administración de usuarios
