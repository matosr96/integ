# 🧹 Guía de Uso - Sistema de Limpieza de Datos

## 📋 Resumen Ejecutivo

Se ha creado un sistema completo de limpieza de datos que:

✅ **Normaliza 38 EPS oficiales** de Colombia  
✅ **Normaliza 30 municipios** de Córdoba  
✅ **Reconstruye fechas** usando contexto del archivo  
✅ **Separa registros válidos e inválidos** automáticamente

### Resultados de la Última Limpieza

- **Total procesados**: 36,151 registros
- **✅ Válidos**: 33,350 (92.3%)
- **⚠️ Rechazados**: 2,801 (7.7%)
- **EPS**: 54 → 16 únicas
- **Municipios**: 82 → 29 únicos

---

## 🚀 Cómo Ejecutar la Limpieza

### Paso 1: Ejecutar el Script

```bash
cd /Users/matos/repositorios/integ
python limpiar_datos_maestro.py
```

### Paso 2: Revisar los Archivos Generados

El script genera 3 archivos principales:

1. **`DATA/trazabilidad_LIMPIA.json`** ✅

   - Contiene solo registros válidos (33,350)
   - EPS y municipios normalizados
   - Fechas reconstruidas
   - **Este es el archivo que debe usar el dashboard**

2. **`DATA/registros_RECHAZADOS.json`** ⚠️

   - Contiene 2,801 registros rechazados
   - Incluye razón del rechazo
   - Para revisión manual posterior

3. **`DATA/trazabilidad_BACKUP.json`** 💾
   - Backup del archivo original
   - Por seguridad

---

## 📊 Archivos de Análisis

### Scripts de Análisis

| Script                     | Propósito                               |
| -------------------------- | --------------------------------------- |
| `analyze_bad_data.py`      | Identifica errores en los datos         |
| `identify_masters.py`      | Lista todas las EPS y municipios únicos |
| `limpiar_datos_maestro.py` | **Script principal de limpieza**        |

### Reportes Generados

| Archivo                                | Contenido                     |
| -------------------------------------- | ----------------------------- |
| `DATA/reporte_limpieza.json`           | Estadísticas de la limpieza   |
| `DATA/error_report.json`               | Errores encontrados           |
| `DATA/master_data.json`                | Listas maestras identificadas |
| `DATA/municipios_cordoba_oficial.json` | 30 municipios oficiales       |

---

## 🔧 Integración con el Dashboard

### Opción 1: Actualizar `trazabilidad_utils.py`

Modifica la función `load_historical_data_json()` para que cargue el archivo limpio:

```python
def load_historical_data_json(json_dir):
    # Cargar archivo limpio en lugar del consolidado
    clean_file = 'DATA/trazabilidad_LIMPIA.json'

    if os.path.exists(clean_file):
        with open(clean_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)

    # Fallback al método original si no existe el limpio
    # ... código original ...
```

### Opción 2: Crear Nuevo Archivo de Carga

Crea `load_clean_data.py`:

```python
import pandas as pd
import json

def load_clean_data():
    """Carga datos limpios y normalizados"""
    with open('DATA/trazabilidad_LIMPIA.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Convertir fechas
    for col in ['fecha_ingreso', 'fecha_egreso']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df
```

---

## 📈 Verificación de Datos Limpios

### Verificar EPS

```python
import pandas as pd
import json

with open('DATA/trazabilidad_LIMPIA.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)
print("EPS únicas:", df['eps'].nunique())
print(df['eps'].value_counts())
```

**Resultado esperado**: 16 EPS únicas

### Verificar Municipios

```python
print("Municipios únicos:", df['municipio'].nunique())
print(df['municipio'].value_counts())
```

**Resultado esperado**: 29 municipios únicos (de los 30 oficiales)

---

## 🔍 Revisar Registros Rechazados

### Ver Razones de Rechazo

```python
with open('DATA/registros_RECHAZADOS.json', 'r') as f:
    rechazados = json.load(f)

# Contar por razón
razones = {}
for rec in rechazados:
    razon = rec.get('razon_rechazo', 'Desconocida')
    razones[razon] = razones.get(razon, 0) + 1

for razon, count in sorted(razones.items(), key=lambda x: x[1], reverse=True):
    print(f"{count}: {razon}")
```

### Ejemplos de Registros Rechazados

Los registros rechazados incluyen:

- Registros sin EPS válida
- Registros sin municipio válido (ej: sectores, veredas)
- Registros con datos incompletos

---

## 📝 Listas Maestras

### 16 EPS Válidas Encontradas

1. NUEVA EPS (23,425 registros)
2. MUTUAL SER (6,999 registros)
3. SALUD TOTAL (1,038 registros)
4. PROMOSALUD (786 registros)
5. SALUDVIDA (669 registros)
6. UNICOR (451 registros)
7. FOMAG (442 registros)
8. SANITAS (432 registros)
9. MEDICINA INTEGRAL (250 registros)
10. COLSANITAS (115 registros)
    11-16. Otras EPS con menor frecuencia

### 29 Municipios Válidos Encontrados

1. MONTERÍA (11,873 registros)
2. SANTA CRUZ DE LORICA (2,957 registros)
3. SAHAGÚN (2,949 registros)
4. CERETÉ (2,460 registros)
5. AYAPEL (1,997 registros)
6. COTORRA (1,262 registros)
7. TIERRALTA (986 registros)
8. PLANETA RICA (916 registros)
9. CIÉNAGA DE ORO (903 registros)
10. MONTELÍBANO (870 registros)
    11-29. Otros municipios de Córdoba

---

## ⚙️ Mantenimiento

### Agregar Nueva Variación de EPS

Edita `limpiar_datos_maestro.py`:

```python
EPS_VARIACIONES = {
    # ... existentes ...
    'NUEVA_VARIACION': 'EPS_OFICIAL',
}
```

### Agregar Nueva Variación de Municipio

```python
MUNICIPIOS_VARIACIONES = {
    # ... existentes ...
    'VARIACION': 'MUNICIPIO_OFICIAL',
}
```

### Re-ejecutar Limpieza

```bash
python limpiar_datos_maestro.py
```

---

## 🎯 Próximos Pasos

1. ✅ **Integrar con el dashboard** - Actualizar `trazabilidad_utils.py`
2. ⚠️ **Revisar rechazados** - Analizar `registros_RECHAZADOS.json`
3. 🔄 **Actualizar variaciones** - Agregar nuevos casos al diccionario
4. 📊 **Validar reportes** - Verificar que los gráficos sean correctos

---

## 📞 Soporte

Si encuentras problemas:

1. Verifica que el archivo `DATA/trazabilidad_consolidada.json` existe
2. Revisa el reporte en `DATA/reporte_limpieza.json`
3. Consulta los registros rechazados en `DATA/registros_RECHAZADOS.json`

---

## 📄 Licencia

Uso interno - Sistema de Gestión Terapéutica
