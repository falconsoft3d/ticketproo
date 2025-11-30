# Sistema Odoo RPC - Documentación

## Descripción General

Sistema completo de integración con Odoo mediante XML-RPC que permite:
- Configurar múltiples conexiones a instancias de Odoo
- Definir tablas (modelos de Odoo) a sincronizar
- Mapear campos con tipos de datos
- Exportar plantillas Excel para importación masiva
- Importar datos desde Excel con validación
- Insertar datos masivamente en Odoo

## Componentes Implementados

### 1. Modelos (tickets/models.py)
- **OdooConnection**: Configuración de conexiones (URL, puerto, BD, credenciales)
- **OdooRPCTable**: Definición de tablas/modelos Odoo a sincronizar
- **OdooRPCField**: Mapeo de campos con 11 tipos de datos
- **OdooRPCData**: Área de staging para datos importados

### 2. Funciones Auxiliares (tickets/odoo_rpc.py)
- `test_connection()`: Prueba de conexión a Odoo
- `authenticate()`: Autenticación XML-RPC
- `search_records()`: Búsqueda de registros
- `read_records()`: Lectura de registros
- `create_record()`: Creación de registros
- `write_record()`: Actualización de registros
- `get_model_fields()`: Obtención de campos disponibles

### 3. Vistas (tickets/views.py)

#### Gestión de Conexiones
- `odoo_connection_list`: Lista de conexiones
- `odoo_connection_create`: Crear conexión
- `odoo_connection_edit`: Editar conexión
- `odoo_connection_delete`: Eliminar conexión
- `odoo_connection_test`: Probar conexión (AJAX)

#### Gestión de Tablas
- `odoo_rpc_table_list`: Lista de tablas por conexión
- `odoo_rpc_table_create`: Crear tabla
- `odoo_rpc_table_detail`: Detalle con estadísticas
- `odoo_rpc_table_edit`: Editar tabla
- `odoo_rpc_table_delete`: Eliminar tabla

#### Gestión de Campos
- `odoo_rpc_field_create`: Crear campo
- `odoo_rpc_field_edit`: Editar campo
- `odoo_rpc_field_delete`: Eliminar campo

#### Operaciones de Datos
- `odoo_rpc_table_export_template`: Exportar plantilla Excel
- `odoo_rpc_table_import_data`: Importar desde Excel
- `odoo_rpc_data_execute`: Ejecutar inserción masiva a Odoo
- `odoo_rpc_data_list`: Ver datos importados

### 4. URLs (tickets/urls.py)
Todas las rutas bajo el prefijo `odoo-rpc/`:
- Conexiones: `/odoo-rpc/connections/`
- Tablas: `/odoo-rpc/connections/<id>/tables/`
- Campos: `/odoo-rpc/tables/<id>/fields/create/`
- Operaciones: `/odoo-rpc/tables/<id>/export-template/`, `import-data/`, `execute/`

### 5. Templates
- **Lista de conexiones**: `odoo_connection_list.html`
- **Formulario de conexión**: `odoo_connection_form.html`
- **Eliminar conexión**: `odoo_connection_delete.html`
- **Lista de tablas**: `odoo_rpc_table_list.html`
- **Detalle de tabla**: `odoo_rpc_table_detail.html` (con estadísticas)
- **Formularios de tabla**: `odoo_rpc_table_form.html`, `delete.html`
- **Formularios de campo**: `odoo_rpc_field_form.html`, `delete.html`
- **Importar datos**: `odoo_rpc_table_import.html`
- **Lista de datos**: `odoo_rpc_data_list.html`

### 6. Admin (tickets/admin.py)
Todos los modelos registrados con interfaces completas:
- OdooConnectionAdmin
- OdooRPCTableAdmin (con inline de campos)
- OdooRPCFieldAdmin
- OdooRPCDataAdmin (con visualización JSON)

### 7. Menú
Agregado en el menú **CAP** en `base.html`:
- Icono: `bi-cloud-upload`
- Texto: "Odoo RPC"
- URL: `/odoo-rpc/connections/`

## Flujo de Uso

1. **Configurar Conexión**
   - Ir a CAP → Odoo RPC
   - Crear nueva conexión con URL, puerto, BD, usuario, contraseña
   - Probar conexión para verificar

2. **Definir Tabla**
   - Seleccionar conexión
   - Crear tabla especificando modelo Odoo (ej: `product.product`)
   - Agregar campos mapeando con nombres técnicos de Odoo

3. **Exportar Plantilla**
   - Descargar plantilla Excel con estructura de campos
   - La plantilla incluye:
     - Fila 1: Nombres descriptivos (headers)
     - Fila 2: Nombres técnicos de Odoo
     - Fila 3: Tipos y ayuda

4. **Importar Datos**
   - Completar plantilla con datos
   - Subir archivo Excel
   - Sistema valida datos según tipos y campos requeridos
   - Datos quedan en estado "Pendiente"

5. **Ejecutar Inserción**
   - Revisar datos pendientes
   - Ejecutar inserción masiva a Odoo
   - Sistema actualiza estados: success/failed
   - Ver reporte de ejecución

## Características Técnicas

### Tipos de Campos Soportados
- char, text
- integer, float
- boolean
- date, datetime
- selection
- many2one, one2many, many2many

### Validaciones
- Campos requeridos
- Tipos de datos
- Duplicados (unique constraint en tabla+modelo)
- Formato de archivo Excel

### Seguridad
- Contraseñas almacenadas de forma segura
- Solo usuarios autenticados
- Filtrado por usuario creador
- Validación de permisos en cascada

### Excel
- Librería: openpyxl
- Formatos: .xlsx, .xls
- Estilos: Headers con colores, fuentes, alineación
- Lectura: read_only mode para eficiencia

## Dependencias

```python
# Ya instaladas
openpyxl==3.1.5  # Para manejo de Excel
xmlrpc.client    # Librería estándar de Python
```

## Base de Datos

Migración aplicada: `0346_odooconnection_odoorpctable_odoorpcdata_odoorpcfield.py`

Tablas creadas:
- tickets_odooconnection
- tickets_odoorpctable
- tickets_odoorpcfield
- tickets_odoorpcdata

## Estado del Sistema

✅ **Completamente Funcional**
- Todos los modelos creados y migrados
- Todas las vistas implementadas
- Todos los templates creados
- URLs configuradas
- Admin registrado
- Menú agregado
- Servidor corriendo sin errores

## Testing Manual

Para probar el sistema:
1. Acceder a http://127.0.0.1:8000
2. Login con usuario admin
3. CAP → Odoo RPC
4. Crear conexión de prueba
5. Probar conexión
6. Crear tabla
7. Agregar campos
8. Exportar plantilla
9. Importar datos
10. Ejecutar inserción

## Próximas Mejoras Posibles

- Descubrimiento automático de campos desde Odoo
- Sincronización bidireccional (pull from Odoo)
- Programación de sincronizaciones automáticas (Celery)
- Mapeos de campos como plantillas reutilizables
- Procesamiento en lotes para datasets grandes
- WebSocket para progreso en tiempo real
- Manejo de relaciones many2one con lookup
- Validación de datos contra modelo Odoo antes de insertar
