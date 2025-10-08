# API REST - TicketProo

## Configuración

Para usar la API REST de TicketProo, necesitas:

1. **Activar la API** en tu perfil de usuario (`/profile/`)
2. **Generar un token de API** desde el mismo perfil
3. **Usar el token** en las peticiones HTTP

## Autenticación

Todas las peticiones a la API requieren autenticación mediante token Bearer:

```bash
Authorization: Bearer TU_TOKEN_AQUI
```

## Endpoints Disponibles

### Tickets

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/tickets/` | Listar tickets |
| POST | `/api/v1/tickets/` | Crear ticket |
| GET | `/api/v1/tickets/{id}/` | Ver ticket específico |
| PUT | `/api/v1/tickets/{id}/` | Actualizar ticket completo |
| PATCH | `/api/v1/tickets/{id}/` | Actualizar ticket parcial |
| DELETE | `/api/v1/tickets/{id}/` | Eliminar ticket |

### Categorías

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/categories/` | Listar categorías |
| GET | `/api/v1/categories/{id}/` | Ver categoría específica |

### Empresas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/companies/` | Listar empresas |
| GET | `/api/v1/companies/{id}/` | Ver empresa específica |

### Proyectos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/projects/` | Listar proyectos |
| GET | `/api/v1/projects/{id}/` | Ver proyecto específico |

## Filtros y Parámetros

### Listar Tickets

Puedes filtrar los tickets usando parámetros de consulta:

```bash
GET /api/v1/tickets/?status=open&priority=high&search=error&page=2
```

**Parámetros disponibles:**
- `status`: `open`, `in_progress`, `resolved`, `closed`
- `priority`: `low`, `medium`, `high`, `urgent`
- `search`: Buscar en título y descripción
- `assigned_to`: Para agentes: `me`, `unassigned`
- `page`: Número de página (paginación)

## Ejemplos de Uso

### Listar tickets

```bash
curl -H "Authorization: Bearer TU_TOKEN" \
     http://localhost:8001/api/v1/tickets/
```

### Crear un ticket

```bash
curl -X POST \
     -H "Authorization: Bearer TU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Error en login",
       "description": "No puedo iniciar sesión en la aplicación",
       "priority": "high",
       "ticket_type": "error"
     }' \
     http://localhost:8001/api/v1/tickets/
```

### Actualizar un ticket

```bash
curl -X PATCH \
     -H "Authorization: Bearer TU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "in_progress",
       "assigned_to_id": 1
     }' \
     http://localhost:8001/api/v1/tickets/1/
```

### Ver un ticket específico

```bash
curl -H "Authorization: Bearer TU_TOKEN" \
     http://localhost:8001/api/v1/tickets/1/
```

## Estructura de Datos

### Ticket

```json
{
  "id": 1,
  "ticket_number": "01-001",
  "title": "Error en login",
  "description": "No puedo iniciar sesión",
  "priority": "high",
  "status": "open",
  "ticket_type": "error",
  "hours": null,
  "is_approved": false,
  "created_at": "2025-10-08T09:00:00Z",
  "updated_at": "2025-10-08T09:30:00Z",
  "created_by": {
    "id": 1,
    "username": "usuario",
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com"
  },
  "assigned_to": null,
  "category": {
    "id": 1,
    "name": "Soporte Técnico",
    "description": "Problemas técnicos",
    "color": "#dc3545"
  },
  "company": null,
  "project": null,
  "age_in_hours": 2,
  "age_display": "2 horas",
  "priority_display": "Alta",
  "status_display": "Abierto",
  "type_display": "Error"
}
```

## Permisos

- **Usuarios regulares**: Solo pueden ver/editar sus propios tickets y tickets de su empresa
- **Agentes**: Pueden ver/editar todos los tickets del sistema

## Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Datos inválidos
- `401 Unauthorized`: Token inválido o faltante
- `403 Forbidden`: Sin permisos para el recurso
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Paginación

Los endpoints que retornan listas usan paginación automática:

```json
{
  "count": 25,
  "next": "http://localhost:8001/api/v1/tickets/?page=2",
  "previous": null,
  "results": [...]
}
```

## Casos de Uso Comunes

### 1. Integración con aplicación móvil
- Usar GET para mostrar tickets
- Usar POST para crear tickets desde la app
- Usar PATCH para actualizar estados

### 2. Dashboard personalizado
- Consultar tickets por estado/prioridad
- Mostrar estadísticas en tiempo real

### 3. Automatización
- Crear tickets automáticamente desde formularios web
- Actualizar tickets basado en eventos externos

### 4. Reportes
- Extraer datos para análisis
- Generar informes personalizados