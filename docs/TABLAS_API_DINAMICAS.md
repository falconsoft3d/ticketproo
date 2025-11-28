# Sistema de Tablas API Dinámicas

## Descripción General

Sistema tipo Strapi que permite crear tablas personalizadas con sus propios campos y generar automáticamente una API REST completa con operaciones CRUD. Cada tabla tiene su propio token de seguridad para autenticación.

## Características

- ✅ Creación de tablas personalizadas sin código
- ✅ 10 tipos de campos soportados (text, textarea, number, decimal, boolean, date, datetime, email, url, json)
- ✅ API REST completa con autenticación por token
- ✅ Interfaz web para gestión de registros
- ✅ Validaciones automáticas (required, unique, max_length)
- ✅ Permisos configurables (lectura/escritura pública)
- ✅ Paginación y búsqueda en listados

---

## 1. Crear una Tabla

### Interfaz Web
1. Accede a **DC → Tablas API**
2. Click en **"Nueva Tabla"**
3. Completa el formulario:
   - **Nombre**: Identificador único (ej: `usuarios`, `comentarios`)
   - **Nombre para mostrar**: Nombre descriptivo (ej: "Tabla de Usuarios")
   - **Descripción**: Propósito de la tabla
   - **Permitir lectura pública**: ☑️ Sin autenticación para GET
   - **Permitir creación pública**: ☑️ Sin autenticación para POST

### Ejemplo: Tabla de Comentarios de Blog
```
Nombre: comentarios_blog
Nombre para mostrar: Comentarios de Blog
Descripción: Almacena comentarios de usuarios en artículos del blog
✓ Permitir lectura pública
✓ Permitir creación pública
```

### Agregar Campos
Después de crear la tabla, agrega campos:

| Campo | Tipo | Requerido | Único | Descripción |
|-------|------|-----------|-------|-------------|
| nombre | text | ✅ | ❌ | Nombre del usuario |
| email | email | ✅ | ❌ | Email del usuario |
| articulo_id | number | ✅ | ❌ | ID del artículo |
| comentario | textarea | ✅ | ❌ | Contenido del comentario |
| fecha | datetime | ❌ | ❌ | Fecha del comentario |
| aprobado | boolean | ❌ | ❌ | Estado de moderación |

---

## 2. API REST - Operaciones CRUD

### Autenticación
Todas las peticiones requieren el token de la tabla (excepto si están habilitadas las opciones públicas):

**Método 1: Header HTTP**
```bash
X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469
```

**Método 2: Query Parameter**
```bash
?token=b22752b8-0ae2-4c32-9b65-df0b2fdba469
```

### 2.1. Crear un Registro (POST)

**Endpoint:** `POST /api/dynamic-tables/{nombre_tabla}/`

**Ejemplo: Crear comentario**
```bash
curl -X POST \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "articulo_id": 42,
    "comentario": "Excelente artículo, muy informativo",
    "fecha": "2024-01-15T10:30:00",
    "aprobado": true
  }' \
  http://localhost:8000/api/dynamic-tables/comentarios_blog/
```

**Respuesta exitosa (201 Created):**
```json
{
  "success": true,
  "message": "Registro creado exitosamente",
  "id": 1,
  "data": {
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "articulo_id": 42,
    "comentario": "Excelente artículo, muy informativo",
    "fecha": "2024-01-15T10:30:00",
    "aprobado": true
  }
}
```

**Errores de validación (400 Bad Request):**
```json
{
  "success": false,
  "message": "Error de validación",
  "errors": [
    "El campo 'email' es requerido",
    "El campo 'email' debe ser un email válido",
    "El campo 'nombre' excede la longitud máxima de 100 caracteres",
    "Ya existe un registro con este valor en el campo 'email' (único)"
  ]
}
```

---

### 2.2. Leer un Registro (GET por ID)

**Endpoint:** `GET /api/dynamic-tables/{nombre_tabla}/{id}/`

**Ejemplo: Obtener comentario #1**
```bash
curl -X GET \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  http://localhost:8000/api/dynamic-tables/comentarios_blog/1/
```

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "id": 1,
  "data": {
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "articulo_id": 42,
    "comentario": "Excelente artículo, muy informativo",
    "fecha": "2024-01-15T10:30:00",
    "aprobado": true
  },
  "created_at": "2024-01-15T10:30:45.123456",
  "updated_at": "2024-01-15T10:30:45.123456"
}
```

**Registro no encontrado (404 Not Found):**
```json
{
  "success": false,
  "message": "Registro no encontrado"
}
```

---

### 2.3. Listar Todos los Registros (GET)

**Endpoint:** `GET /api/dynamic-tables/{nombre_tabla}/`

**Ejemplo básico:**
```bash
curl -X GET \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  http://localhost:8000/api/dynamic-tables/comentarios_blog/
```

**Respuesta (200 OK):**
```json
{
  "success": true,
  "table": "comentarios_blog",
  "total": 45,
  "page": 1,
  "per_page": 50,
  "data": [
    {
      "id": 1,
      "data": {
        "nombre": "Juan Pérez",
        "email": "juan@example.com",
        "articulo_id": 42,
        "comentario": "Excelente artículo",
        "fecha": "2024-01-15T10:30:00",
        "aprobado": true
      },
      "created_at": "2024-01-15T10:30:45.123456",
      "updated_at": "2024-01-15T10:30:45.123456"
    },
    {
      "id": 2,
      "data": {
        "nombre": "María García",
        "email": "maria@example.com",
        "articulo_id": 42,
        "comentario": "Me gustó mucho",
        "fecha": "2024-01-15T11:20:00",
        "aprobado": false
      },
      "created_at": "2024-01-15T11:20:12.654321",
      "updated_at": "2024-01-15T11:20:12.654321"
    }
  ]
}
```

---

### 2.4. Listar con Paginación

**Parámetros:**
- `page`: Número de página (default: 1)
- `per_page`: Registros por página (default: 50, máximo: 100)

**Ejemplo: Página 2 con 10 registros**
```bash
curl -X GET \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  "http://localhost:8000/api/dynamic-tables/comentarios_blog/?page=2&per_page=10"
```

**Respuesta:**
```json
{
  "success": true,
  "table": "comentarios_blog",
  "total": 45,
  "page": 2,
  "per_page": 10,
  "data": [ /* 10 registros de la página 2 */ ]
}
```

---

### 2.5. Listar con Búsqueda (Query)

**Parámetro:** `search`

Busca en todos los campos de tipo `text`, `textarea`, `email` y `url`.

**Ejemplo: Buscar "excelente"**
```bash
curl -X GET \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  "http://localhost:8000/api/dynamic-tables/comentarios_blog/?search=excelente"
```

**Ejemplo: Buscar por email**
```bash
curl -X GET \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  "http://localhost:8000/api/dynamic-tables/comentarios_blog/?search=juan@example.com"
```

**Respuesta:**
```json
{
  "success": true,
  "table": "comentarios_blog",
  "total": 3,
  "page": 1,
  "per_page": 50,
  "data": [ /* Solo registros que coinciden con "excelente" */ ]
}
```

**Combinar búsqueda y paginación:**
```bash
curl -X GET \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  "http://localhost:8000/api/dynamic-tables/comentarios_blog/?search=juan&page=1&per_page=20"
```

---

### 2.6. Editar un Registro (PUT)

**Endpoint:** `PUT /api/dynamic-tables/{nombre_tabla}/{id}/`

**Ejemplo: Aprobar comentario**
```bash
curl -X PUT \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "articulo_id": 42,
    "comentario": "Excelente artículo, muy informativo",
    "fecha": "2024-01-15T10:30:00",
    "aprobado": true
  }' \
  http://localhost:8000/api/dynamic-tables/comentarios_blog/1/
```

**⚠️ Importante:** PUT requiere enviar TODOS los campos (actualización completa).

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Registro actualizado exitosamente",
  "id": 1,
  "data": {
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "articulo_id": 42,
    "comentario": "Excelente artículo, muy informativo",
    "fecha": "2024-01-15T10:30:00",
    "aprobado": true
  }
}
```

---

### 2.7. Eliminar un Registro (DELETE)

**Endpoint:** `DELETE /api/dynamic-tables/{nombre_tabla}/{id}/`

**Ejemplo: Eliminar comentario #1**
```bash
curl -X DELETE \
  -H "X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469" \
  http://localhost:8000/api/dynamic-tables/comentarios_blog/1/
```

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Registro eliminado exitosamente"
}
```

**Registro no encontrado (404 Not Found):**
```json
{
  "success": false,
  "message": "Registro no encontrado"
}
```

---

## 3. Interfaz Web - Gestión de Registros

### 3.1. Ver Registros
1. Accede a **DC → Tablas API**
2. Click en **"Ver Registros"** en la tabla deseada
3. Visualiza todos los registros en formato tabla

### 3.2. Crear Registro (Web)
1. En la lista de registros, click **"Agregar Registro"**
2. Completa el formulario modal con los campos requeridos
3. Click **"Crear Registro"**

### 3.3. Editar Registro (Web)
1. En la lista de registros, click en el ícono de **lápiz** (editar)
2. Modifica los campos necesarios en el modal
3. Click **"Guardar Cambios"**

### 3.4. Ver Detalles
- Click en el ícono de **ojo** para ver todos los detalles del registro
- Incluye fechas de creación y actualización
- Muestra IP de origen

### 3.5. Eliminar Registro (Web)
1. Click en el ícono de **papelera** (eliminar)
2. Confirma la acción en el diálogo
3. El registro se elimina permanentemente

---

## 4. Tipos de Campos Soportados

| Tipo | Descripción | Validación | Ejemplo |
|------|-------------|------------|---------|
| `text` | Texto corto | max_length | "Juan Pérez" |
| `textarea` | Texto largo | max_length | "Comentario extenso..." |
| `number` | Número entero | int() | 42, -10, 0 |
| `decimal` | Número decimal | float() | 3.14, 99.99 |
| `boolean` | Verdadero/Falso | true/false | true, false |
| `date` | Fecha | YYYY-MM-DD | "2024-01-15" |
| `datetime` | Fecha y hora | ISO 8601 | "2024-01-15T10:30:00" |
| `email` | Email | formato email | "user@example.com" |
| `url` | URL | formato URL | "https://example.com" |
| `json` | Objeto JSON | json.loads() | {"key": "value"} |

---

## 5. Validaciones

### 5.1. Campo Requerido (`is_required`)
```json
// ❌ Error si falta un campo requerido
{
  "success": false,
  "errors": ["El campo 'email' es requerido"]
}
```

### 5.2. Campo Único (`is_unique`)
```json
// ❌ Error si el valor ya existe
{
  "success": false,
  "errors": ["Ya existe un registro con este valor en el campo 'email'"]
}
```

### 5.3. Longitud Máxima (`max_length`)
```json
// ❌ Error si excede max_length
{
  "success": false,
  "errors": ["El campo 'nombre' excede la longitud máxima de 100 caracteres"]
}
```

### 5.4. Tipo de Dato
```json
// ❌ Error de conversión de tipo
{
  "success": false,
  "errors": ["El campo 'articulo_id' debe ser un número entero válido"]
}
```

---

## 6. Seguridad

### 6.1. Token de API
- Cada tabla genera un UUID único como token
- El token es requerido para todas las operaciones (excepto si están habilitadas las opciones públicas)
- El token se puede regenerar desde la interfaz web

### 6.2. Permisos Públicos
- **Lectura pública**: Permite GET sin token
- **Creación pública**: Permite POST sin token
- PUT y DELETE siempre requieren token

### 6.3. Regenerar Token
1. Accede a la vista de detalle de la tabla
2. Click en **"Regenerar Token"**
3. Confirma la acción
4. ⚠️ El token anterior dejará de funcionar

### 6.4. Registro de IP
- Todas las operaciones registran la IP de origen
- Útil para auditoría y detección de abuso

---

## 7. Casos de Uso Prácticos

### 7.1. Formulario de Contacto
```
Tabla: contactos
Campos:
  - nombre (text, required)
  - email (email, required)
  - telefono (text)
  - mensaje (textarea, required)
  - fecha (datetime)
Permisos: ✓ Lectura pública, ✓ Creación pública
```

### 7.2. Sistema de Usuarios Simple
```
Tabla: usuarios
Campos:
  - username (text, required, unique)
  - password (text, required)
  - email (email, required, unique)
  - activo (boolean)
Permisos: ✗ Lectura pública, ✗ Creación pública
```

### 7.3. Registro de Eventos
```
Tabla: eventos_log
Campos:
  - evento (text, required)
  - tipo (text, required)
  - datos (json)
  - timestamp (datetime, required)
  - severidad (number)
Permisos: ✗ Lectura pública, ✓ Creación pública
```

### 7.4. Base de Datos de Productos
```
Tabla: productos
Campos:
  - codigo (text, required, unique, max_length: 50)
  - nombre (text, required, max_length: 200)
  - descripcion (textarea)
  - precio (decimal, required)
  - stock (number, required)
  - activo (boolean)
  - imagen_url (url)
Permisos: ✓ Lectura pública, ✗ Creación pública
```

---

## 8. Mejores Prácticas

### ✅ DO (Hacer)
- Usa nombres descriptivos para tablas y campos (snake_case)
- Define campos requeridos para garantizar integridad de datos
- Usa tipos de campo apropiados (email para emails, number para números)
- Activa validaciones (unique, max_length) según necesites
- Regenera tokens periódicamente para mayor seguridad
- Documenta el propósito de cada tabla en la descripción

### ❌ DON'T (No Hacer)
- No uses espacios en nombres de tablas o campos
- No almacenes contraseñas en texto plano (usa sistemas de autenticación seguros)
- No habilites permisos públicos sin necesidad
- No confíes solo en validaciones del lado del cliente
- No expongas tokens en repositorios públicos
- No uses este sistema para datos extremadamente sensibles sin encriptación adicional

---

## 9. Ejemplos de Integración

### JavaScript (Fetch API)
```javascript
// Crear registro
async function crearComentario(datos) {
  const response = await fetch('http://localhost:8000/api/dynamic-tables/comentarios_blog/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Token': 'b22752b8-0ae2-4c32-9b65-df0b2fdba469'
    },
    body: JSON.stringify(datos)
  });
  return await response.json();
}

// Listar con búsqueda
async function buscarComentarios(query) {
  const response = await fetch(
    `http://localhost:8000/api/dynamic-tables/comentarios_blog/?search=${query}`,
    {
      headers: {
        'X-API-Token': 'b22752b8-0ae2-4c32-9b65-df0b2fdba469'
      }
    }
  );
  return await response.json();
}
```

### Python (requests)
```python
import requests

API_TOKEN = 'b22752b8-0ae2-4c32-9b65-df0b2fdba469'
BASE_URL = 'http://localhost:8000/api/dynamic-tables'

# Crear registro
def crear_comentario(datos):
    response = requests.post(
        f'{BASE_URL}/comentarios_blog/',
        json=datos,
        headers={'X-API-Token': API_TOKEN}
    )
    return response.json()

# Listar todos
def listar_comentarios(page=1, per_page=50):
    response = requests.get(
        f'{BASE_URL}/comentarios_blog/',
        params={'page': page, 'per_page': per_page},
        headers={'X-API-Token': API_TOKEN}
    )
    return response.json()

# Actualizar
def actualizar_comentario(id, datos):
    response = requests.put(
        f'{BASE_URL}/comentarios_blog/{id}/',
        json=datos,
        headers={'X-API-Token': API_TOKEN}
    )
    return response.json()

# Eliminar
def eliminar_comentario(id):
    response = requests.delete(
        f'{BASE_URL}/comentarios_blog/{id}/',
        headers={'X-API-Token': API_TOKEN}
    )
    return response.json()
```

### PHP (cURL)
```php
<?php
function crearComentario($datos) {
    $ch = curl_init('http://localhost:8000/api/dynamic-tables/comentarios_blog/');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($datos));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'X-API-Token: b22752b8-0ae2-4c32-9b65-df0b2fdba469'
    ]);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    return json_decode($response, true);
}
?>
```

---

## 10. Solución de Problemas

### Error 401: Token inválido
- Verifica que el token sea correcto
- Confirma que estás usando el header `X-API-Token` o el parámetro `?token=`
- Regenera el token si es necesario

### Error 400: Validación fallida
- Lee el array `errors` en la respuesta
- Verifica que todos los campos requeridos estén presentes
- Confirma que los tipos de datos sean correctos
- Revisa las restricciones de longitud

### Error 404: Registro no encontrado
- Verifica que el ID del registro sea correcto
- Confirma que el nombre de la tabla sea exacto

### Los registros no se guardan
- Verifica que estés usando POST (no GET) para crear
- Confirma que el Content-Type sea `application/json`
- Revisa que el JSON esté bien formado

---

## 11. Límites y Consideraciones

- **Paginación máxima**: 100 registros por página
- **Paginación por defecto**: 50 registros por página
- **Nombre de tabla**: Único, sin espacios, snake_case recomendado
- **Nombre de campo**: Único por tabla, sin espacios
- **Max length por defecto**: Sin límite (configurable por campo)
- **Almacenamiento**: JSONField (flexible, sin esquema fijo)
- **Índices**: Por defecto en [table, -created_at]

---

## 12. Referencia Rápida

| Operación | Método | Endpoint | Token |
|-----------|--------|----------|-------|
| Crear | POST | `/api/dynamic-tables/{tabla}/` | ✓ |
| Leer uno | GET | `/api/dynamic-tables/{tabla}/{id}/` | ✓ |
| Listar todos | GET | `/api/dynamic-tables/{tabla}/` | ✓* |
| Buscar | GET | `/api/dynamic-tables/{tabla}/?search={query}` | ✓* |
| Paginar | GET | `/api/dynamic-tables/{tabla}/?page={n}&per_page={m}` | ✓* |
| Actualizar | PUT | `/api/dynamic-tables/{tabla}/{id}/` | ✓ |
| Eliminar | DELETE | `/api/dynamic-tables/{tabla}/{id}/` | ✓ |

*✓ = Requerido (excepto si la tabla tiene permisos públicos habilitados)

---

## Soporte

Para más información o reportar problemas:
- Interfaz web: DC → Tablas API
- Documentación en cada tabla: Click en "Ver" → sección "API"

---

**Versión**: 1.0  
**Última actualización**: 28 de noviembre de 2025
