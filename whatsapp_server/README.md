# Servidor WhatsApp para TicketProo

Este servidor Node.js proporciona integración con WhatsApp Web usando `whatsapp-web.js`.

## 📋 Requisitos

- Node.js 18+ 
- npm o yarn
- Docker (opcional, para despliegue con contenedores)

## 🚀 Instalación y Ejecución

### Opción 1: Ejecución Local (Sin Docker)

1. **Instalar dependencias:**
```bash
cd whatsapp_server
npm install
```

2. **Iniciar el servidor:**
```bash
npm start
```

O para desarrollo con auto-reload:
```bash
npm run dev
```

El servidor se ejecutará en `http://localhost:3000`

### Opción 2: Ejecución con Docker 🐳

#### A. Usando Docker Compose (Recomendado)

1. **Construir y levantar el contenedor:**
```bash
cd whatsapp_server
docker-compose up -d
```

2. **Ver logs del contenedor:**
```bash
docker-compose logs -f
```

3. **Detener el contenedor:**
```bash
docker-compose down
```

4. **Reconstruir la imagen (después de cambios):**
```bash
docker-compose up -d --build
```

#### B. Usando Docker directamente

1. **Construir la imagen:**
```bash
docker build -t ticketproo-whatsapp .
```

2. **Ejecutar el contenedor:**
```bash
docker run -d \
  --name ticketproo-whatsapp \
  -p 3000:3000 \
  -v $(pwd)/.wwebjs_auth:/app/.wwebjs_auth \
  -v $(pwd)/logs:/app/logs \
  -e DJANGO_API_URL=http://host.docker.internal:8000 \
  ticketproo-whatsapp
```

3. **Ver logs:**
```bash
docker logs -f ticketproo-whatsapp
```

4. **Detener el contenedor:**
```bash
docker stop ticketproo-whatsapp
docker rm ticketproo-whatsapp
```

### 📝 Configuración

1. **Copiar el archivo de ejemplo de variables de entorno:**
```bash
cp .env.example .env
```

2. **Editar `.env` con tu configuración:**
```env
PORT=3000
DJANGO_API_URL=http://localhost:8000
NODE_ENV=production
LOG_LEVEL=info
```

**Nota:** Si usas Docker, la URL de Django debe ser `http://host.docker.internal:8000` (en Mac/Windows) o la IP del host (en Linux)

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

## 🏗️ Arquitectura

1. Django solicita conexión al servidor Node.js
2. Node.js genera QR code
3. Django muestra QR al usuario
4. Usuario escanea con WhatsApp
5. Node.js notifica conexión exitosa
6. Mensajes entrantes se envían a Django para procesar respuestas automáticas

## 💾 Datos de Sesión

Las sesiones se guardan en `.wwebjs_auth/` para mantener la conexión persistente.

**Importante:** Este directorio se monta como volumen en Docker para que las sesiones persistan entre reinicios del contenedor.

## 🔧 Comandos Útiles de Docker

### Ver contenedores en ejecución:
```bash
docker ps
```

### Acceder al contenedor:
```bash
docker exec -it ticketproo-whatsapp bash
```

### Ver uso de recursos:
```bash
docker stats ticketproo-whatsapp
```

### Limpiar todo (contenedor, volúmenes, imágenes):
```bash
docker-compose down -v
docker rmi ticketproo-whatsapp
```

## 🐛 Troubleshooting

### Problema: El QR no se genera en Docker
**Solución:** Asegúrate de que el contenedor tiene permisos SYS_ADMIN (ya incluido en docker-compose.yml)

### Problema: La sesión no persiste después de reiniciar
**Solución:** Verifica que el volumen `.wwebjs_auth` esté correctamente montado

### Problema: No puede conectar con Django
**Solución en Docker:** 
- Mac/Windows: Usa `http://host.docker.internal:8000`
- Linux: Usa `http://172.17.0.1:8000` o la IP del host

### Problema: Error de Chrome/Chromium
**Solución:** El Dockerfile ya instala Chromium. Si falla, verifica los logs con `docker logs`

## 📊 Monitoreo

### Ver logs en tiempo real:
```bash
# Con Docker Compose
docker-compose logs -f

# Con Docker directo
docker logs -f ticketproo-whatsapp
```

### Ver solo errores:
```bash
docker logs ticketproo-whatsapp 2>&1 | grep ERROR
```

## 🔒 Seguridad

- **Nunca commitear** el directorio `.wwebjs_auth/` al repositorio (ya está en .gitignore)
- **Proteger** el puerto 3000 con firewall en producción
- **Usar HTTPS** con un proxy reverso (nginx/traefik) en producción

## 📦 Estructura de Archivos

```
whatsapp_server/
├── Dockerfile              # Definición de la imagen Docker
├── docker-compose.yml      # Orquestación de contenedores
├── .dockerignore          # Archivos a excluir de la imagen
├── .env.example           # Ejemplo de variables de entorno
├── package.json           # Dependencias de Node.js
├── server.js              # Código principal del servidor
├── .wwebjs_auth/          # Sesiones de WhatsApp (no commitable)
└── README.md              # Esta documentación
```

## 🚀 Despliegue en Producción

### Con Docker Compose (Recomendado):

1. **En el servidor, clonar el repositorio:**
```bash
git clone <tu-repo>
cd ticketproo/whatsapp_server
```

2. **Configurar variables de entorno:**
```bash
cp .env.example .env
nano .env  # Editar con valores de producción
```

3. **Levantar con docker-compose:**
```bash
docker-compose up -d
```

4. **Configurar auto-inicio (opcional):**
```bash
# Agregar al crontab
@reboot cd /path/to/whatsapp_server && docker-compose up -d
```

### Con systemd (Sin Docker):

Crear archivo `/etc/systemd/system/whatsapp-server.service`:

```ini
[Unit]
Description=WhatsApp Server for TicketProo
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/whatsapp_server
ExecStart=/usr/bin/node server.js
Restart=always
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

Habilitar y iniciar:
```bash
sudo systemctl enable whatsapp-server
sudo systemctl start whatsapp-server
sudo systemctl status whatsapp-server
```

## 📝 Notas Importantes

- Cada usuario tiene su propia sesión independiente
- El QR expira después de cierto tiempo (reescanear si es necesario)
- La conexión se mantiene activa incluso después de reiniciar el servidor
- Docker usa más recursos que la ejecución nativa, pero facilita el despliegue
- En producción, considera usar un orquestador como Kubernetes para alta disponibilidad
