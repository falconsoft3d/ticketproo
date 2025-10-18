# Servidor WhatsApp para TicketProo

Este servidor Node.js proporciona integración con WhatsApp Web usando `whatsapp-web.js`.

## Requisitos

- Node.js 18+ 
- npm o yarn

## Instalación

```bash
cd whatsapp_server
npm install
```

## Uso

### Iniciar el servidor

```bash
npm start
```

O para desarrollo con auto-reload:

```bash
npm run dev
```

El servidor se ejecutará en `http://localhost:3000`

## Endpoints

### `GET /health`
Verifica el estado del servidor

### `POST /connect`
Inicia una conexión de WhatsApp
```json
{
  "user_id": "1"
}
```

### `GET /status/:user_id`
Obtiene el estado de conexión y QR code

### `POST /disconnect`
Desconecta un cliente
```json
{
  "user_id": "1"
}
```

### `POST /send`
Envía un mensaje
```json
{
  "user_id": "1",
  "to": "1234567890",
  "message": "Hola desde TicketProo!"
}
```

### `GET /info/:user_id`
Obtiene información del usuario conectado

## Arquitectura

1. Django solicita conexión al servidor Node.js
2. Node.js genera QR code
3. Django muestra QR al usuario
4. Usuario escanea con WhatsApp
5. Node.js notifica conexión exitosa
6. Mensajes entrantes se envían a Django para procesar respuestas automáticas

## Datos de sesión

Las sesiones se guardan en `.wwebjs_auth/` para mantener la conexión persistente.

## Notas

- Cada usuario tiene su propia sesión independiente
- El QR expira después de cierto tiempo
- La conexión se mantiene activa incluso después de reiniciar el servidor
