# Notas de Instalación - TicketProo

## Adaptaciones realizadas al script de instalación

### 🔧 Cambios principales respecto al script original:

#### 1. **Variables específicas del proyecto**
- **Proyecto**: `ticketproo` (en lugar de variables genéricas)
- **Directorio**: `/opt/ticketproo` (ubicación estándar para aplicaciones)
- **Usuario del sistema**: `ticketproo` (en lugar de `django`)
- **Base de datos**: `ticketproo_db` / `ticketproo_user`
- **App principal**: `ticket_system`

#### 2. **Configuración de base de datos mejorada**
- Utiliza PostgreSQL con configuración específica para TicketProo
- Variables de entorno en archivo `.env` para mayor seguridad
- Soporte para `DATABASE_URL` que detecta automáticamente el entorno

#### 3. **Reemplazo de Supervisor por systemd**
- **Antes**: Supervisor para gestión de procesos
- **Ahora**: systemd (nativo de Ubuntu) con socket activation
- Mejor integración con el sistema operativo
- Manejo automático de fallos y reinicios

#### 4. **Configuración de Redis y Celery**
- Instalación y configuración de Redis para cache y cola de tareas
- Servicio systemd para Celery worker
- Soporte para tareas asíncronas (emails, notificaciones, etc.)

#### 5. **Configuración de Nginx mejorada**
- Soporte para archivos media (uploads de documentos)
- Headers de cache para archivos estáticos
- Configuración de proxy mejorada con headers de seguridad
- Soporte para dominios y IP del servidor

#### 6. **Variables de entorno**
```bash
DEBUG=False
SECRET_KEY=<generada automáticamente>
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
```

#### 7. **Comandos de gestión específicos**
- Ejecuta `setup_groups` para crear grupos de usuarios
- Ejecuta `assign_admin_agent` para configurar roles
- Gestión automática de archivos estáticos

#### 8. **Mejoras de seguridad**
- Usuario del sistema sin privilegios sudo
- Configuración de firewall UFW
- Separación de usuarios (ticketproo vs www-data)
- Variables de entorno para credenciales

### 🚀 Ventajas del nuevo script:

1. **Específico para TicketProo**: No requiere input manual durante la instalación
2. **Más robusto**: Utiliza systemd en lugar de Supervisor
3. **Mejor rendimiento**: Redis y Celery configurados desde el inicio
4. **Más seguro**: Separación de privilegios y configuración de firewall
5. **Fácil mantenimiento**: Comandos systemctl estándar
6. **Preparado para producción**: Configuración optimizada para entorno productivo

### 📋 Servicios configurados:

- **ticketproo.socket**: Socket Unix para Gunicorn
- **ticketproo.service**: Aplicación Django con Gunicorn
- **ticketproo-celery.service**: Worker Celery para tareas asíncronas
- **nginx**: Servidor web reverso proxy
- **postgresql**: Base de datos
- **redis**: Cache y cola de mensajes

### 🔍 Comandos útiles post-instalación:

```bash
# Ver estado de todos los servicios
sudo systemctl status ticketproo.service ticketproo-celery.service nginx postgresql redis

# Logs en tiempo real
sudo journalctl -u ticketproo.service -f

# Reiniciar aplicación
sudo systemctl restart ticketproo.service

# Recargar configuración de Nginx
sudo nginx -t && sudo systemctl reload nginx

# Entrar al shell de Django
sudo -u ticketproo /opt/ticketproo/.venv/bin/python /opt/ticketproo/manage.py shell

# Crear superusuario
sudo -u ticketproo /opt/ticketproo/.venv/bin/python /opt/ticketproo/manage.py createsuperuser
```

### 🛠️ Estructura de archivos resultante:

```
/opt/ticketproo/
├── .env                    # Variables de entorno
├── .venv/                  # Entorno virtual Python
├── manage.py
├── static/                 # Archivos estáticos originales
├── staticfiles/           # Archivos estáticos recolectados
├── media/                 # Uploads de usuarios
├── templates/
├── ticket_system/         # App principal Django
├── tickets/               # App tickets
└── requirements.txt

/etc/nginx/sites-available/ticketproo    # Configuración Nginx
/etc/systemd/system/ticketproo.*          # Servicios systemd
/var/log/nginx/ticketproo_*               # Logs de Nginx
```

### ⚠️ Requisitos previos:

- Ubuntu 18.04 o superior
- Acceso root o sudo
- Puerto 80 disponible
- Memoria RAM: mínimo 1GB
- Espacio en disco: mínimo 2GB

### 🔄 Proceso de actualización:

Para futuras actualizaciones del código:

```bash
cd /opt/ticketproo
sudo -u ticketproo git pull origin main
sudo -u ticketproo .venv/bin/pip install -r requirements.txt
sudo -u ticketproo .venv/bin/python manage.py migrate
sudo -u ticketproo .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart ticketproo.service
```