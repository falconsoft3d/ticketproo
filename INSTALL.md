# 🚀 Guía de Instalación TicketProo en Ubuntu

Esta guía te llevará paso a paso para desplegar TicketProo en un servidor Ubuntu con Nginx, Gunicorn, PostgreSQL y SSL con Let's Encrypt.

## 📋 Requisitos Previos

- Servidor Ubuntu 20.04+ con acceso root
- Dominio apuntando al servidor
- Acceso SSH al servidor

---

## 🔧 Paso 1: Actualización del Sistema

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y software-properties-common curl wget git vim htop tree
```

---

## 🐍 Paso 2: Instalar Python y PostgreSQL

```bash
# Instalar Python 3.10+
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Instalar dependencias para PostgreSQL
sudo apt install -y libpq-dev build-essential

# Verificar instalaciones
python3 --version
psql --version
```

---

## 🗄️ Paso 3: Configurar PostgreSQL

```bash
# Iniciar y habilitar PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Crear usuario y base de datos
sudo -u postgres psql << EOF
CREATE USER ticketproo_user WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE ticketproo_db OWNER ticketproo_user;
GRANT ALL PRIVILEGES ON DATABASE ticketproo_db TO ticketproo_user;
ALTER USER ticketproo_user CREATEDB;
\q
EOF

# Verificar conexión
sudo -u postgres psql -c "SELECT version();"

# Configurar PostgreSQL para conexiones locales (opcional)
sudo nano /etc/postgresql/*/main/postgresql.conf
# Buscar y descomentar: listen_addresses = 'localhost'

sudo nano /etc/postgresql/*/main/pg_hba.conf  
# Verificar que existe: local all all peer

# Reiniciar PostgreSQL si hiciste cambios
sudo systemctl restart postgresql
```

---

## 👤 Paso 4: Crear Usuario del Sistema

```bash
# Crear usuario para la aplicación
sudo adduser ticketproo --disabled-password --gecos ""

# Crear directorios
sudo mkdir -p /opt/ticketproo
sudo chown ticketproo:ticketproo /opt/ticketproo
```

---

## 📂 Paso 5: Clonar y Configurar Aplicación

```bash
# Cambiar al usuario de la aplicación
sudo -u ticketproo bash

# Ir al directorio de la aplicación
cd /opt/ticketproo

# Clonar el repositorio (reemplaza con tu URL)
git clone https://github.com/falconsoft3d/ticketproo.git .

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Instalar dependencias adicionales para producción
pip install gunicorn psycopg2-binary python-decouple dj-database-url

# Salir del usuario ticketproo
exit
```

---

## ⚙️ Paso 6: Configurar Variables de Entorno

```bash
# Crear archivo de configuración con nano
sudo -u ticketproo nano /opt/ticketproo/.env
```

**Copia y pega el siguiente contenido en el archivo:**

```env
# TicketProo Production Environment
DEBUG=False
SECRET_KEY=tu_clave_secreta_generada_aqui
DATABASE_URL=postgresql://ticketproo_user:tu_password_seguro@localhost:5432/ticketproo_db
ALLOWED_HOSTS=ticketproo.com,www.ticketproo.com,localhost,127.0.0.1
STATIC_ROOT=/opt/ticketproo/staticfiles
MEDIA_ROOT=/opt/ticketproo/media

# Security settings (activar después de configurar SSL)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

**Para generar una SECRET_KEY segura, ejecuta:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Guarda el archivo con:** `Ctrl+X`, luego `Y`, luego `Enter`

```bash
# Establecer permisos seguros
sudo chown ticketproo:ticketproo /opt/ticketproo/.env
sudo chmod 600 /opt/ticketproo/.env
```

**⚠️ IMPORTANTE: Reemplaza `tu_password_seguro` con la contraseña real de PostgreSQL y `ticketproo.com` con tu dominio real.**

---

## 🔧 Paso 7: Configurar Django

```bash
# Crear settings de producción con nano
sudo -u ticketproo nano /opt/ticketproo/ticket_system/settings_production.py
```

**Copia y pega el siguiente contenido en el archivo:**

```python
from .settings import *
from decouple import config
import os

# Override settings with environment variables
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default=SECRET_KEY)

# ALLOWED_HOSTS from .env
ALLOWED_HOSTS_STR = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]

# Database configuration
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }

# Static and media paths
STATIC_ROOT = config('STATIC_ROOT', default=STATIC_ROOT)
MEDIA_ROOT = config('MEDIA_ROOT', default=MEDIA_ROOT)

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Guarda el archivo con:** `Ctrl+X`, luego `Y`, luego `Enter`

# Crear directorios necesarios
sudo -u ticketproo mkdir -p /opt/ticketproo/staticfiles /opt/ticketproo/media /opt/ticketproo/logs

# Configurar aplicación Django
sudo -u ticketproo bash -c "
cd /opt/ticketproo
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=ticket_system.settings_production

# Ejecutar migraciones
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Configurar grupos de usuarios
python manage.py setup_groups
"
```

---

## 👤 Paso 8: Crear Superusuario

```bash
# Crear superusuario de forma interactiva
sudo -u ticketproo bash -c "
cd /opt/ticketproo
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=ticket_system.settings_production
python manage.py createsuperuser
"

# O crear de forma automática (reemplaza los valores)
sudo -u ticketproo bash -c "
cd /opt/ticketproo
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=ticket_system.settings_production
python manage.py shell -c \"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ticketproo.com', 'password_seguro')
    print('Superusuario creado')
\"
python manage.py assign_admin_agent admin
"
```

---

## 🔥 Paso 9: Configurar Gunicorn

```bash
# Crear socket para Gunicorn
sudo nano /etc/systemd/system/ticketproo.socket
```

**Copia y pega el siguiente contenido:**

```ini
[Unit]
Description=TicketProo Gunicorn Socket

[Socket]
ListenStream=/run/ticketproo.sock
SocketUser=www-data

[Install]
WantedBy=sockets.target
```

**Guarda con:** `Ctrl+X`, luego `Y`, luego `Enter`

```bash
# Crear servicio de Gunicorn
sudo nano /etc/systemd/system/ticketproo.service
```

**Copia y pega el siguiente contenido:**

```ini
[Unit]
Description=TicketProo Django Application
Requires=ticketproo.socket
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=ticketproo
Group=ticketproo
WorkingDirectory=/opt/ticketproo
Environment="DJANGO_SETTINGS_MODULE=ticket_system.settings_production"
Environment="PYTHONPATH=/opt/ticketproo"
ExecStart=/opt/ticketproo/venv/bin/gunicorn --workers 3 --bind unix:/run/ticketproo.sock ticket_system.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
```

**Guarda con:** `Ctrl+X`, luego `Y`, luego `Enter`

# Habilitar y iniciar servicios
sudo systemctl daemon-reload
sudo systemctl enable ticketproo.socket
sudo systemctl start ticketproo.socket
sudo systemctl enable ticketproo.service
sudo systemctl start ticketproo.service

# Verificar estado
sudo systemctl status ticketproo.socket
sudo systemctl status ticketproo.service
```

---

## 🌐 Paso 10: Instalar y Configurar Nginx

```bash
# Instalar Nginx
sudo apt install -y nginx

# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/ticketproo
```

**Copia y pega el siguiente contenido:**

```nginx
server {
    listen 80;
    server_name ticketproo.com www.ticketproo.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Logs
    access_log /var/log/nginx/ticketproo_access.log;
    error_log /var/log/nginx/ticketproo_error.log;
    
    # Static files
    location /static/ {
        alias /opt/ticketproo/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/ticketproo/media/;
        expires 7d;
    }
    
    # Main application
    location / {
        proxy_pass http://unix:/run/ticketproo.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }
    
    # Security - block common attack patterns
    location ~ /\. {
        deny all;
    }
    
    location ~ ^/(wp-admin|wp-login|phpmyadmin|admin) {
        deny all;
    }
}
```

**Guarda con:** `Ctrl+X`, luego `Y`, luego `Enter`

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/ticketproo /etc/nginx/sites-enabled/

# Remover sitio por defecto
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Habilitar y reiniciar Nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx
```

**⚠️ IMPORTANTE: Reemplaza `ticketproo.com` con tu dominio real.**

---

## 🔐 Paso 11: Configurar SSL con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d ticketproo.com -d www.ticketproo.com --email tu_email@ejemplo.com --agree-tos --non-interactive

# Configurar renovación automática
sudo systemctl enable certbot.timer

# Verificar renovación automática
sudo certbot renew --dry-run

# Actualizar configuración de seguridad en Django
sudo -u ticketproo bash -c "
cd /opt/ticketproo
sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' .env
sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' .env
sed -i 's/CSRF_COOKIE_SECURE=False/CSRF_COOKIE_SECURE=True/' .env
"

# Reiniciar servicios
sudo systemctl restart ticketproo.service
sudo systemctl restart nginx
```

**⚠️ IMPORTANTE: Reemplaza `ticketproo.com` y `tu_email@ejemplo.com` con tus valores reales.**

---

## 🔒 Paso 12: Configurar Seguridad Adicional

```bash
# Instalar y configurar Fail2ban
sudo apt install -y fail2ban

# Configurar Fail2ban para Nginx
sudo nano /etc/fail2ban/jail.local
```

**Copia y pega el siguiente contenido:**

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true

[nginx-noproxy]
enabled = true
```

**Guarda con:** `Ctrl+X`, luego `Y`, luego `Enter`

# Configurar firewall UFW
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status

# Habilitar Fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## ✅ Paso 13: Verificación Final

```bash
# Verificar todos los servicios
echo "=== ESTADO DE SERVICIOS ==="
sudo systemctl status postgresql --no-pager
sudo systemctl status ticketproo.service --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status fail2ban --no-pager

# Verificar logs
echo "=== LOGS DE LA APLICACIÓN ==="
sudo tail -n 20 /opt/ticketproo/logs/django.log

echo "=== LOGS DE NGINX ==="
sudo tail -n 10 /var/log/nginx/ticketproo_access.log
sudo tail -n 10 /var/log/nginx/ticketproo_error.log

# Verificar conexión
echo "=== PRUEBA DE CONEXIÓN ==="
curl -I https://ticketproo.com

# Verificar certificado SSL
echo "=== INFORMACIÓN DEL CERTIFICADO ==="
sudo certbot certificates
```

---

## 🎯 Paso 14: Pruebas de Funcionalidad

```bash
# Probar la aplicación
echo "Accede a: https://ticketproo.com"
echo "Panel de administración: https://ticketproo.com/admin/"

# Crear ticket de prueba (opcional)
sudo -u ticketproo bash -c "
cd /opt/ticketproo
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=ticket_system.settings_production
python manage.py shell -c \"
from tickets.models import Ticket
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
ticket = Ticket.objects.create(
    title='Ticket de Prueba',
    description='Este es un ticket de prueba del sistema',
    created_by=admin,
    priority='media',
    status='abierto'
)
print(f'Ticket de prueba creado: #{ticket.ticket_number}')
\"
"
```

---

## 📝 Comandos Útiles para Mantenimiento

```bash
# Reiniciar la aplicación
sudo systemctl restart ticketproo.service

# Ver logs en tiempo real
sudo journalctl -u ticketproo.service -f

# Actualizar código desde Git
sudo -u ticketproo bash -c "
cd /opt/ticketproo
git pull origin main
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=ticket_system.settings_production
python manage.py migrate
python manage.py collectstatic --noinput
"
sudo systemctl restart ticketproo.service

# Backup de la base de datos
sudo -u postgres pg_dump ticketproo_db > /opt/backup_$(date +%Y%m%d_%H%M%S).sql

# Verificar espacio en disco
df -h

# Verificar uso de memoria
free -h
```

---

## 🚨 Solución de Problemas

### Si la aplicación no carga:
```bash
# Verificar logs
sudo journalctl -u ticketproo.service --no-pager
sudo tail -f /opt/ticketproo/logs/django.log
```

### Si hay errores de SSL:
```bash
# Renovar certificado
sudo certbot renew --force-renewal
sudo systemctl restart nginx
```

### Si hay problemas de permisos:
```bash
# Corregir permisos
sudo chown -R ticketproo:ticketproo /opt/ticketproo
sudo chmod -R 755 /opt/ticketproo
sudo chmod 600 /opt/ticketproo/.env
```

---

## 🎉 ¡Instalación Completada!

Tu aplicación TicketProo debería estar funcionando en:
- **URL Principal**: https://ticketproo.com
- **Panel de Admin**: https://ticketproo.com/admin/

### Credenciales por defecto:
- **Usuario**: admin
- **Contraseña**: La que configuraste en el paso 8

---

**📧 Soporte**: Si tienes problemas, revisa los logs y verifica que todos los servicios estén corriendo correctamente.