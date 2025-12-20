# 📁 Estructura del Proyecto - Limpieza de Datos

## Archivos Principales

### Scripts de Limpieza (Usar en orden)

1. **`limpiar_datos_maestro.py`** ⭐

   - Normaliza EPS y municipios con listas oficiales
   - Reconstruye fechas
   - Ejecutar primero

2. **`recuperar_datos_mejorado.py`** ⭐
   - Recupera datos por cédula y nombre
   - Elimina registros sin identificación
   - Ejecutar después del anterior

### Datos Finales

**Para usar:**

- `DATA/trazabilidad_LIMPIA.json` (33,886 registros) ⭐

**Para auditoría:**

- `DATA/trazabilidad_BACKUP.json` (backup original)
- `DATA/registros_RECHAZADOS.json` (764 rechazados)
- `DATA/registros_ELIMINADOS.json` (1,501 sin ID)
- `DATA/registros_RECUPERADOS.json` (95 recuperados)

**Reportes:**

- `DATA/reporte_limpieza.json`
- `DATA/reporte_recuperacion_mejorado.json`

### Documentación

- `RESUMEN_FINAL.md` - Resumen completo
- `GUIA_LIMPIEZA_DATOS.md` - Guía de uso

### Scripts Antiguos (movidos a `scripts_limpieza/`)

Scripts de desarrollo que ya no son necesarios:

- `analyze_bad_data.py`
- `identify_masters.py`
- `clean_data.py`
- `limpiar_datos_definitivo.py`
- `recuperar_datos.py`

---

## 🚀 Uso Rápido

```bash
# 1. Limpiar datos
python limpiar_datos_maestro.py

# 2. Recuperar datos
python recuperar_datos_mejorado.py

# 3. Usar en dashboard
# Actualizar código para cargar DATA/trazabilidad_LIMPIA.json
```

---

## 📊 Resultado

- ✅ 33,886 registros válidos (93.7%)
- 16 EPS normalizadas
- 29 municipios normalizados
