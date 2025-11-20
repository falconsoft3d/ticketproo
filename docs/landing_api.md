# API de Envío para Landing Pages

Endpoint seguro para crear envíos (submissions) en una landing page mediante JSON.

- URL: `POST /api/landing-pages/<pk>/submit/`
- Content-Type: `application/json`
- Autenticación: **Bearer Token requerido**. Cada landing page tiene un token único de API (`api_token`) que debe ser incluido en el header `Authorization`.

Campos aceptados (JSON):

- `nombre` (string) — requerido
- `apellido` (string) — requerido
- `email` (string) — requerido
- `telefono` o `phone` (string)
- `empresa` o `company` (string)
- `cargo` o `position` (string)
- `mensaje` o `message` (string)
- `preferred_contact_time` (string) — opcional (ej: `asap`, `monday`, `tuesday`, ...)
- `utm_source`, `utm_medium`, `utm_campaign` (string) — opcionales

## Obtener el Token de API

1. Accede al detalle de la landing page en: `/landing-pages/<id>/`
2. Copia el token desde la sección "Documentación de API"
3. Úsalo en el header `Authorization: Bearer <token>`

Ejemplo de petición con `curl`:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU-API-TOKEN-AQUI" \
  -d '{
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan@example.com",
    "telefono": "+34123456789",
    "empresa": "Mi Empresa S.A.",
    "cargo": "CTO",
    "mensaje": "Interesado en la demo",
    "utm_source": "newsletter",
    "utm_medium": "email",
    "utm_campaign": "campania_noviembre"
  }' \
  http://localhost:8000/api/landing-pages/1/submit/
```

Respuesta de éxito (JSON):

```json
{
  "success": true,
  "message": "Submission created",
  "submission_id": 123
}
```

Respuestas de error (JSON):

**401 Unauthorized** - Falta el header Authorization o está mal formado:
```json
{
  "success": false,
  "error": "Authorization header required. Format: 'Authorization: Bearer <token>'"
}
```

**403 Forbidden** - Token inválido:
```json
{
  "success": false,
  "error": "Invalid API token"
}
```

**400 Bad Request** - Faltan campos requeridos:
```json
{
  "success": false,
  "error": "Missing required fields: nombre, apellido, email"
}
```

## Notas de Seguridad

- **Token único**: Cada landing page tiene su propio token de API generado automáticamente.
- **Guarda el token de forma segura**: No lo expongas en código cliente (frontend público).
- **Usa el token solo en servidor**: Las llamadas deben hacerse desde servicios backend o server-side rendering.
- **Notificaciones automáticas**: El endpoint creará un `Contact` interno y enviará notificaciones (email/Telegram) si están configuradas.
- **Tracking**: Se guardará automáticamente la IP (`ip_address`) y el `user_agent` desde la petición.
