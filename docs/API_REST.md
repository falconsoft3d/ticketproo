# Documentación de la API REST

## Introducción

Esta API REST permite interactuar con el sistema de tickets de forma programática. Puedes autenticarte, consultar tickets, crear nuevos tickets y mucho más.

**URL Base:** `http://localhost:8000/api/` (desarrollo) o `https://tu-dominio.com/api/` (producción)

## Autenticación

La API utiliza autenticación basada en tokens. Debes incluir el token en el header `Authorization` de cada petición.

### 1. Login - Obtener Token de API

Autentica un usuario y obtiene su token de API.

**Endpoint:** `POST /api/auth/login/`

**Permisos:** Público (no requiere autenticación)

**Request Body:**
```json
{
  "username": "tu_usuario",
  "password": "tu_contraseña"
}
```

**Respuesta Exitosa (200):**
```json
{
  "token": "12345678-1234-1234-1234-123456789abc",
  "user": {
    "id": 1,
    "username": "tu_usuario",
    "email": "tu@email.com",
    "first_name": "Tu",
    "last_name": "Nombre"
  },
  "message": "Login exitoso"
}
```

**Respuestas de Error:**
- `400 Bad Request`: Falta username o password
- `401 Unauthorized`: Credenciales inválidas o usuario inactivo

**Ejemplo con cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"tu_usuario","password":"tu_contraseña"}'
```

**Ejemplo con Python:**
```python
import requests

url = "http://localhost:8000/api/auth/login/"
data = {
    "username": "tu_usuario",
    "password": "tu_contraseña"
}

response = requests.post(url, json=data)
result = response.json()
token = result.get('token')
print(f"Token obtenido: {token}")
```

---

## Uso del Token

Una vez obtenido el token, debes incluirlo en todas las peticiones autenticadas:

**Header:**
```
Authorization: Bearer 12345678-1234-1234-1234-123456789abc
```

**Ejemplo con cURL:**
```bash
curl -X GET http://localhost:8000/api/tickets/ \
  -H "Authorization: Bearer tu-token-aqui"
```

**Ejemplo con Python:**
```python
import requests

token = "tu-token-aqui"
headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get("http://localhost:8000/api/tickets/", headers=headers)
tickets = response.json()
```

---

## Endpoints de Tickets

### 2. Listar Tickets

Obtiene una lista de todos los tickets accesibles por el usuario.

**Endpoint:** `GET /api/tickets/`

**Permisos:** Requiere autenticación

**Query Parameters (opcionales):**
- `status`: Filtrar por estado (`open`, `in_progress`, `resolved`, `closed`)
- `priority`: Filtrar por prioridad (`low`, `medium`, `high`, `urgent`)
- `search`: Buscar en título y descripción
- `assigned_to`: Filtrar por asignación (`me`, `unassigned`, o ID de usuario) - solo para agentes

**Respuesta Exitosa (200):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/tickets/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "ticket_number": "01-001",
      "title": "Error en el login",
      "priority": "high",
      "status": "open",
      "ticket_type": "error",
      "created_at": "2024-12-01T10:30:00Z",
      "updated_at": "2024-12-01T10:30:00Z",
      "created_by_name": "juan",
      "assigned_to_name": "maria",
      "category_name": "Soporte",
      "company_name": "Empresa ABC",
      "age_in_hours": 24,
      "is_approved": false
    }
  ]
}
```

**Ejemplos:**

```bash
# Listar todos los tickets
curl -X GET http://localhost:8000/api/tickets/ \
  -H "Authorization: Bearer tu-token"

# Filtrar tickets abiertos
curl -X GET "http://localhost:8000/api/tickets/?status=open" \
  -H "Authorization: Bearer tu-token"

# Buscar tickets
curl -X GET "http://localhost:8000/api/tickets/?search=login" \
  -H "Authorization: Bearer tu-token"
```

### 3. Obtener un Ticket Específico

Obtiene los detalles completos de un ticket.

**Endpoint:** `GET /api/tickets/{id}/`

**Permisos:** Requiere autenticación

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "ticket_number": "01-001",
  "title": "Error en el login",
  "description": "Los usuarios no pueden iniciar sesión desde el navegador Chrome.",
  "priority": "high",
  "status": "open",
  "ticket_type": "error",
  "hours": 2.5,
  "is_approved": false,
  "created_at": "2024-12-01T10:30:00Z",
  "updated_at": "2024-12-01T10:30:00Z",
  "created_by": {
    "id": 1,
    "username": "juan",
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com"
  },
  "assigned_to": {
    "id": 2,
    "username": "maria",
    "first_name": "María",
    "last_name": "García",
    "email": "maria@example.com"
  },
  "category": {
    "id": 1,
    "name": "Soporte",
    "description": "Tickets de soporte técnico",
    "color": "#007bff"
  },
  "company": {
    "id": 1,
    "name": "Empresa ABC",
    "description": "Cliente principal",
    "color": "#28a745"
  },
  "project": null,
  "age_in_hours": 24,
  "age_display": "1 día",
  "priority_display": "Alta",
  "status_display": "Abierto",
  "type_display": "Error"
}
```

**Ejemplo:**
```bash
curl -X GET http://localhost:8000/api/tickets/1/ \
  -H "Authorization: Bearer tu-token"
```

**Ejemplo con Python:**
```python
import requests

token = "tu-token-aqui"
ticket_id = 1

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    f"http://localhost:8000/api/tickets/{ticket_id}/",
    headers=headers
)

if response.status_code == 200:
    ticket = response.json()
    print(f"Ticket: {ticket['title']}")
    print(f"Estado: {ticket['status_display']}")
else:
    print(f"Error: {response.status_code}")
```

### 4. Crear un Ticket

Crea un nuevo ticket en el sistema.

**Endpoint:** `POST /api/tickets/`

**Permisos:** Requiere autenticación

**Request Body:**
```json
{
  "title": "Título del ticket",
  "description": "Descripción detallada del problema o solicitud",
  "priority": "medium",
  "ticket_type": "desarrollo",
  "hours": 3.0,
  "category_id": 1,
  "company_id": 1,
  "project_id": null
}
```

**Campos:**
- `title` (requerido): Título del ticket
- `description` (requerido): Descripción detallada
- `priority` (opcional): `low`, `medium` (default), `high`, `urgent`
- `ticket_type` (opcional): `desarrollo` (default), `error`
- `hours` (opcional): Horas estimadas/trabajadas
- `category_id` (opcional): ID de la categoría
- `company_id` (opcional): ID de la empresa/cliente
- `project_id` (opcional): ID del proyecto

**Respuesta Exitosa (201):**
```json
{
  "id": 25,
  "ticket_number": "01-025",
  "title": "Título del ticket",
  "description": "Descripción detallada del problema o solicitud",
  "priority": "medium",
  "status": "open",
  "ticket_type": "desarrollo",
  "hours": 3.0,
  "is_approved": false,
  "created_at": "2024-12-24T15:30:00Z",
  "updated_at": "2024-12-24T15:30:00Z",
  "created_by": {
    "id": 1,
    "username": "juan",
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan@example.com"
  },
  "assigned_to": null,
  "category": {
    "id": 1,
    "name": "Soporte",
    "description": "Tickets de soporte técnico",
    "color": "#007bff"
  },
  "company": {
    "id": 1,
    "name": "Empresa ABC",
    "description": "Cliente principal",
    "color": "#28a745"
  },
  "project": null,
  "age_in_hours": 0,
  "age_display": "Reciente",
  "priority_display": "Media",
  "status_display": "Abierto",
  "type_display": "Desarrollo"
}
```

**Ejemplo con cURL:**
```bash
curl -X POST http://localhost:8000/api/tickets/ \
  -H "Authorization: Bearer tu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implementar nueva funcionalidad",
    "description": "Necesitamos agregar un módulo de reportes",
    "priority": "high",
    "ticket_type": "desarrollo",
    "hours": 8.0,
    "category_id": 2,
    "company_id": 1
  }'
```

**Ejemplo con Python:**
```python
import requests

token = "tu-token-aqui"
url = "http://localhost:8000/api/tickets/"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "title": "Implementar nueva funcionalidad",
    "description": "Necesitamos agregar un módulo de reportes",
    "priority": "high",
    "ticket_type": "desarrollo",
    "hours": 8.0,
    "category_id": 2,
    "company_id": 1
}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 201:
    ticket = response.json()
    print(f"Ticket creado: {ticket['ticket_number']}")
    print(f"ID: {ticket['id']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### 5. Actualizar un Ticket

Actualiza un ticket existente.

**Endpoint:** `PUT /api/tickets/{id}/` o `PATCH /api/tickets/{id}/`

**Permisos:** Requiere autenticación

**Nota:** Usa `PUT` para actualización completa o `PATCH` para actualización parcial.

**Request Body (PATCH - ejemplo):**
```json
{
  "status": "in_progress",
  "priority": "urgent"
}
```

**Respuesta:** Similar a la respuesta de obtener un ticket.

**Ejemplo con cURL:**
```bash
# Actualización parcial con PATCH
curl -X PATCH http://localhost:8000/api/tickets/1/ \
  -H "Authorization: Bearer tu-token" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Ejemplo con Python:**
```python
import requests

token = "tu-token-aqui"
ticket_id = 1

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "status": "resolved",
    "hours": 5.5
}

response = requests.patch(
    f"http://localhost:8000/api/tickets/{ticket_id}/",
    json=data,
    headers=headers
)

if response.status_code == 200:
    ticket = response.json()
    print(f"Ticket actualizado: {ticket['status_display']}")
else:
    print(f"Error: {response.status_code}")
```

### 6. Eliminar un Ticket

Elimina un ticket del sistema.

**Endpoint:** `DELETE /api/tickets/{id}/`

**Permisos:** Requiere autenticación (solo agentes o creador)

**Respuesta Exitosa:** `204 No Content`

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/api/tickets/1/ \
  -H "Authorization: Bearer tu-token"
```

---

## Endpoints Auxiliares

### 7. Listar Categorías

Obtiene todas las categorías activas.

**Endpoint:** `GET /api/categories/`

**Respuesta:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Soporte",
      "description": "Tickets de soporte técnico",
      "color": "#007bff"
    }
  ]
}
```

### 8. Listar Empresas

Obtiene todas las empresas activas.

**Endpoint:** `GET /api/companies/`

**Respuesta:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Empresa ABC",
      "description": "Cliente principal",
      "color": "#28a745"
    }
  ]
}
```

### 9. Listar Proyectos

Obtiene proyectos accesibles por el usuario.

**Endpoint:** `GET /api/projects/`

**Respuesta:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Proyecto Alpha",
      "description": "Desarrollo del sitio web",
      "color": "#ffc107",
      "status": "active"
    }
  ]
}
```

---

## Códigos de Estado HTTP

- `200 OK`: Solicitud exitosa
- `201 Created`: Recurso creado exitosamente
- `204 No Content`: Recurso eliminado exitosamente
- `400 Bad Request`: Datos inválidos en la solicitud
- `401 Unauthorized`: Token inválido o no proporcionado
- `403 Forbidden`: Sin permisos para realizar la acción
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

---

## Permisos y Reglas de Acceso

### Usuarios Regulares
- Pueden ver sus propios tickets
- Pueden ver tickets de su empresa (si tienen empresa asignada)
- Pueden ver tickets asignados a ellos
- Pueden crear tickets
- Pueden actualizar/eliminar solo sus propios tickets

### Agentes (Staff)
- Pueden ver todos los tickets
- Pueden crear, actualizar y eliminar cualquier ticket
- Pueden asignar tickets a otros usuarios
- Tienen acceso a filtros adicionales

---

## Ejemplos de Flujos Completos

### Flujo 1: Login y Listar Tickets

```python
import requests

# 1. Hacer login
login_url = "http://localhost:8000/api/auth/login/"
login_data = {
    "username": "mi_usuario",
    "password": "mi_contraseña"
}

response = requests.post(login_url, json=login_data)
token = response.json().get('token')

# 2. Listar tickets
headers = {"Authorization": f"Bearer {token}"}
tickets_url = "http://localhost:8000/api/tickets/"

response = requests.get(tickets_url, headers=headers)
tickets = response.json()

print(f"Total de tickets: {tickets['count']}")
for ticket in tickets['results']:
    print(f"- {ticket['ticket_number']}: {ticket['title']} ({ticket['status_display']})")
```

### Flujo 2: Crear y Actualizar un Ticket

```python
import requests

token = "tu-token-aqui"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Crear ticket
create_url = "http://localhost:8000/api/tickets/"
new_ticket = {
    "title": "Bug en el formulario de contacto",
    "description": "El botón enviar no funciona en mobile",
    "priority": "high",
    "ticket_type": "error",
    "category_id": 1
}

response = requests.post(create_url, json=new_ticket, headers=headers)
ticket = response.json()
ticket_id = ticket['id']

print(f"Ticket creado: {ticket['ticket_number']}")

# 2. Actualizar el ticket
update_url = f"http://localhost:8000/api/tickets/{ticket_id}/"
update_data = {
    "status": "in_progress",
    "hours": 2.0
}

response = requests.patch(update_url, json=update_data, headers=headers)
updated_ticket = response.json()

print(f"Ticket actualizado: {updated_ticket['status_display']}")
```

### Flujo 3: Obtener Detalles de un Ticket Específico

```python
import requests

token = "tu-token-aqui"
ticket_id = 5  # ID del ticket que quieres consultar

headers = {"Authorization": f"Bearer {token}"}
url = f"http://localhost:8000/api/tickets/{ticket_id}/"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    ticket = response.json()
    
    print(f"Ticket #{ticket['ticket_number']}")
    print(f"Título: {ticket['title']}")
    print(f"Estado: {ticket['status_display']}")
    print(f"Prioridad: {ticket['priority_display']}")
    print(f"Creado por: {ticket['created_by']['username']}")
    
    if ticket['assigned_to']:
        print(f"Asignado a: {ticket['assigned_to']['username']}")
    
    if ticket['company']:
        print(f"Empresa: {ticket['company']['name']}")
        
elif response.status_code == 404:
    print("Ticket no encontrado")
elif response.status_code == 403:
    print("No tienes permiso para ver este ticket")
else:
    print(f"Error: {response.status_code}")
```

---

## 5. Listar Categorías de Tickets

Obtiene la lista de categorías de tickets activas disponibles en el sistema.

**Endpoint:** `GET /api/categories/`

**Autenticación:** Requerida (Bearer Token)

**Permisos:** Usuario autenticado

**Query Parameters:** Ninguno

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "name": "Soporte Técnico",
    "description": "Problemas técnicos y de configuración",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Consulta General",
    "description": "Preguntas y consultas generales",
    "is_active": true
  },
  {
    "id": 3,
    "name": "Desarrollo",
    "description": "Nuevas funcionalidades y mejoras",
    "is_active": true
  }
]
```

**Nota:** Solo devuelve categorías activas (`is_active=True`).

**Ejemplo con cURL:**
```bash
curl -X GET http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer tu-token-aqui" \
  -H "Content-Type: application/json"
```

**Ejemplo con Python:**
```python
import requests

url = "http://localhost:8000/api/categories/"
headers = {
    "Authorization": "Bearer tu-token-aqui",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    categories = response.json()
    print("Categorías disponibles:")
    for cat in categories:
        print(f"- {cat['name']}: {cat['description']}")
else:
    print(f"Error {response.status_code}: {response.text}")
```

**Respuestas de Error:**
- `401 Unauthorized`: Token no válido o no proporcionado
- `403 Forbidden`: Sin permisos para acceder a las categorías

---

## Manejo de Errores

Siempre verifica el código de estado de la respuesta:

```python
import requests

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    # Procesar datos
elif response.status_code == 401:
    print("Token inválido o expirado. Vuelve a hacer login.")
elif response.status_code == 403:
    print("No tienes permisos para esta acción.")
elif response.status_code == 404:
    print("Recurso no encontrado.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

---

## Notas Adicionales

1. **Paginación:** Las listas de tickets están paginadas. Usa los campos `next` y `previous` para navegar entre páginas.

2. **Timestamps:** Todas las fechas están en formato ISO 8601 con zona horaria UTC.

3. **Seguridad:** 
   - Nunca compartas tu token de API
   - Usa HTTPS en producción
   - Los tokens no expiran automáticamente, pero puedes regenerarlos desde tu perfil

4. **Rate Limiting:** Actualmente no hay límites de tasa, pero se recomienda no hacer más de 100 peticiones por minuto.

5. **Formato de Respuesta:** Todas las respuestas son en formato JSON.

---

## Soporte

Si tienes problemas con la API, contacta al administrador del sistema o revisa los logs del servidor.

**Versión:** 1.0  
**Última actualización:** Diciembre 2024
