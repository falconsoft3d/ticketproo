# 🚀 Guía de Deploy de TicketProo - Paso a Paso

Esta guía detalla el proceso completo de deploy de TicketProo desde la actualización del código hasta la puesta en producción.

## 📋 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Proceso de Deploy con Docker](#proceso-de-deploy-con-docker)
4. [Deploy Manual (Sin Docker)](#deploy-manual-sin-docker)
5. [Configuración de Nginx](#configuración-de-nginx)
6. [Configuración SSL](#configuración-ssl)
7. [Variables de Entorno](#variables-de-entorno)
8. [Verificación Post-Deploy](#verificación-post-deploy)
9. [Rollback](#rollback)
10. [Monitoring y Logs](#monitoring-y-logs)

---

## 🔧 Pre-requisitos

### Servidor de Producción
- **Sistema Operativo**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: Mínimo 2GB (Recomendado 4GB+)
- **Almacenamiento**: Mínimo 20GB SSD
- **CPU**: 2 cores mínimo

### Software Requerido
- **Docker & Docker Compose** (Deploy con Docker)
- **Python 3.11+** (Deploy manual)
- **PostgreSQL 15+** (Recomendado)
- **Nginx** (Proxy reverso)
- **Git** (Control de versiones)

### Accesos Necesarios
- SSH al servidor de producción
- Acceso a la base de datos
- Dominio configurado (opcional para SSL)

---

## 🛠️ Preparación del Entorno

### 1. Actualizar el Sistema
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Instalar Docker (Opción Recomendada)
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Añadir usuario al grupo docker
sudo usermod -aG docker $USER
```

### 3. Crear Estructura de Directorios
```bash
# Crear directorios principales
sudo mkdir -p /opt/ticketproo
sudo mkdir -p /opt/ticketproo/docker/nginx/conf.d
sudo mkdir -p /opt/ticketproo/docker/postgres
sudo mkdir -p /opt/ticketproo/docker/certbot/{conf,www}
sudo mkdir -p /opt/ticketproo/{staticfiles,media,logs}

# Asignar permisos
sudo chown -R $USER:$USER /opt/ticketproo
```

---

## 🐳 Proceso de Deploy con Docker

### 1. Clonar/Actualizar el Repositorio
```bash
# Primera vez
cd /opt
git clone https://github.com/falconsoft3d/ticketproo.git
cd ticketproo

# Actualizaciones posteriores
cd /opt/ticketproo
git fetch origin
git checkout main
git pull origin main
```

### 2. Configurar Variables de Entorno
```bash
# Crear archivo .env
cp .env.example .env
nano .env
```

### 3. Crear Archivo .env
```bash
# .env - Configuración de Producción
DEBUG=False
SECRET_KEY=tu-clave-secreta-super-segura-aqui-min-50-chars
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,localhost,127.0.0.1

# Base de Datos PostgreSQL
DATABASE_URL=postgresql://ticketproo_user:ticketproo_pass@db:5432/ticketproo_db

# Redis
REDIS_URL=redis://redis:6379/0

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-aplicacion
EMAIL_USE_TLS=True

# Configuración adicional
TIME_ZONE=Europe/Madrid
LANGUAGE_CODE=es-es
```

### 4. Configurar Nginx
```bash
# Crear configuración de Nginx
nano docker/nginx/conf.d/ticketproo.conf
```

```nginx
# docker/nginx/conf.d/ticketproo.conf
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirección SSL (comentar si no usas SSL)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # Configuración SSL (comentar si no usas SSL)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración de seguridad SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Tamaño máximo de archivo
    client_max_body_size 50M;

    # Archivos estáticos
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Archivos de media
    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    # Proxy a Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
```

### 5. Ejecutar el Deploy
```bash
# Detener servicios anteriores (si existen)
docker-compose down

# Construir y levantar servicios
docker-compose up -d --build

# Verificar estado de los contenedores
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f web
```

### 6. Configurar Datos Iniciales
```bash
# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Ejecutar comandos de configuración inicial
docker-compose exec web python manage.py setup_groups
docker-compose exec web python manage.py assign_admin_agent
docker-compose exec web python manage.py create_user_profiles
```

---

## 🔧 Deploy Manual (Sin Docker)

### 1. Instalar Dependencias del Sistema
```bash
# Ubuntu/Debian
sudo apt install -y python3.11 python3.11-pip python3.11-venv postgresql postgresql-contrib nginx git

# CentOS/RHEL
sudo yum install -y python3.11 python3.11-pip postgresql-server postgresql-contrib nginx git
```

### 2. Configurar PostgreSQL
```bash
# Inicializar PostgreSQL (CentOS)
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Crear usuario y base de datos
sudo -u postgres psql
```

```sql
-- En la consola de PostgreSQL
CREATE USER ticketproo_user WITH PASSWORD 'ticketproo_pass';
CREATE DATABASE ticketproo_db OWNER ticketproo_user;
GRANT ALL PRIVILEGES ON DATABASE ticketproo_db TO ticketproo_user;
\q
```

### 3. Configurar la Aplicación
```bash
# Clonar repositorio
cd /opt
git clone https://github.com/falconsoft3d/ticketproo.git
cd ticketproo

# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env
```

### 4. Configurar Django
```bash
# Activar entorno virtual
source .venv/bin/activate

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario
python manage.py createsuperuser

# Configurar grupos y permisos
python manage.py setup_groups
python manage.py assign_admin_agent
python manage.py create_user_profiles
```

### 5. Configurar Gunicorn
```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/ticketproo.service
```

```ini
[Unit]
Description=TicketProo Django Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/ticketproo
Environment="PATH=/opt/ticketproo/.venv/bin"
ExecStart=/opt/ticketproo/.venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    ticket_system.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Activar y iniciar servicio
sudo systemctl enable ticketproo
sudo systemctl start ticketproo
sudo systemctl status ticketproo
```

### 6. Configurar Nginx (Deploy Manual)
```bash
# Crear configuración
sudo nano /etc/nginx/sites-available/ticketproo
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    client_max_body_size 50M;

    location /static/ {
        alias /opt/ticketproo/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/ticketproo/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

```bash
# Activar sitio
sudo ln -s /etc/nginx/sites-available/ticketproo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 Configuración SSL con Let's Encrypt

### Con Docker
```bash
# Obtener certificado SSL
docker-compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email tu-email@dominio.com \
    --agree-tos \
    --no-eff-email \
    -d tu-dominio.com \
    -d www.tu-dominio.com

# Reiniciar nginx para aplicar SSL
docker-compose restart nginx
```

### Sin Docker
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Configurar renovación automática
sudo crontab -e
# Añadir línea:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔄 Proceso de Actualización

### Con Docker
```bash
# 1. Backup de la base de datos
docker-compose exec db pg_dump -U ticketproo_user ticketproo_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Actualizar código
cd /opt/ticketproo
git pull origin main

# 3. Reconstruir y redesplegar
docker-compose down
docker-compose up -d --build

# 4. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 5. Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

### Sin Docker
```bash
# 1. Backup de la base de datos
pg_dump -U ticketproo_user -h localhost ticketproo_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Actualizar código
cd /opt/ticketproo
git pull origin main

# 3. Activar entorno virtual
source .venv/bin/activate

# 4. Actualizar dependencias
pip install -r requirements.txt

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Recopilar archivos estáticos
python manage.py collectstatic --noinput

# 7. Reiniciar servicios
sudo systemctl restart ticketproo
sudo systemctl reload nginx
```

---

## ✅ Verificación Post-Deploy

### 1. Verificar Servicios
```bash
# Con Docker
docker-compose ps
docker-compose logs web

# Sin Docker
sudo systemctl status ticketproo
sudo systemctl status nginx
sudo systemctl status postgresql
```

### 2. Verificar Aplicación
```bash
# Verificar conectividad
curl -I http://tu-dominio.com

# Verificar SSL (si aplica)
curl -I https://tu-dominio.com

# Verificar base de datos
# Con Docker
docker-compose exec web python manage.py dbshell

# Sin Docker
source .venv/bin/activate
python manage.py dbshell
```

### 3. Tests Funcionales
- [ ] Login de administrador funciona
- [ ] Creación de tickets funciona
- [ ] Subida de archivos funciona
- [ ] Dashboard carga correctamente
- [ ] Emails se envían (si configurado)

---

## 🔙 Rollback

### En caso de problemas, realizar rollback:

```bash
# 1. Volver a la versión anterior
git log --oneline -10  # Ver últimos commits
git checkout <commit-anterior>

# 2. Con Docker
docker-compose down
docker-compose up -d --build

# 3. Sin Docker
source .venv/bin/activate
python manage.py migrate
sudo systemctl restart ticketproo

# 4. Restaurar base de datos (si necesario)
# Con Docker
cat backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U ticketproo_user ticketproo_db

# Sin Docker
psql -U ticketproo_user -h localhost ticketproo_db < backup_YYYYMMDD_HHMMSS.sql
```

---

## 📊 Monitoring y Logs

### Ubicación de Logs
```bash
# Con Docker
docker-compose logs web
docker-compose logs nginx
docker-compose logs db

# Sin Docker
sudo journalctl -u ticketproo -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitoreo de Recursos
```bash
# Uso de CPU y memoria
htop

# Espacio en disco
df -h

# Conexiones de red
netstat -tulpn | grep :80
netstat -tulpn | grep :443
```

### Scripts de Monitoreo
```bash
# Crear script de health check
nano /opt/ticketproo/scripts/health_check.sh
```

```bash
#!/bin/bash
# health_check.sh

# Verificar respuesta HTTP
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)

if [ $HTTP_CODE -eq 200 ]; then
    echo "$(date): TicketProo está funcionando correctamente"
else
    echo "$(date): ERROR - TicketProo no responde (HTTP $HTTP_CODE)"
    # Aquí puedes añadir notificaciones por email o Slack
fi

# Verificar uso de disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): ADVERTENCIA - Uso de disco alto: ${DISK_USAGE}%"
fi
```

```bash
# Hacer ejecutable y programar
chmod +x /opt/ticketproo/scripts/health_check.sh

# Añadir a crontab
crontab -e
# Añadir línea para ejecutar cada 5 minutos:
*/5 * * * * /opt/ticketproo/scripts/health_check.sh >> /var/log/ticketproo_health.log 2>&1
```

---

## 📝 Checklist de Deploy

### Pre-Deploy
- [ ] Backup de base de datos realizado
- [ ] Variables de entorno configuradas
- [ ] Certificados SSL válidos (si aplica)
- [ ] Espacio en disco suficiente
- [ ] Notificación a usuarios (si aplica)

### Durante el Deploy
- [ ] Código actualizado desde repositorio
- [ ] Dependencias instaladas/actualizadas
- [ ] Migraciones ejecutadas
- [ ] Archivos estáticos recopilados
- [ ] Servicios reiniciados

### Post-Deploy
- [ ] Servicios corriendo correctamente
- [ ] Aplicación accesible
- [ ] Funcionalidades principales verificadas
- [ ] Logs sin errores críticos
- [ ] Performance dentro de parámetros normales

---

## 🆘 Solución de Problemas Comunes

### Error: Puerto 8000 ya en uso
```bash
# Encontrar proceso usando el puerto
sudo lsof -i :8000

# Matar proceso
sudo kill -9 <PID>
```

### Error: Permisos de archivos
```bash
# Corregir permisos
sudo chown -R www-data:www-data /opt/ticketproo
chmod -R 755 /opt/ticketproo
```

### Error: Base de datos no conecta
```bash
# Verificar estado de PostgreSQL
sudo systemctl status postgresql

# Verificar configuración
sudo -u postgres psql -c "\l"
```

### Error: SSL no funciona
```bash
# Verificar certificados
sudo certbot certificates

# Renovar si es necesario
sudo certbot renew --dry-run
```

---

## 📞 Soporte

Para asistencia técnica durante el deploy:

- 📧 **Email**: mfalconsoft@gmail.com
- 📱 **Teléfono**: +34-662-47-0645
- 🌐 **Web**: https://ticketproo.com

---

**¡Deploy completado exitosamente! 🚀**

> **Nota**: Guarda este archivo y actualízalo según evolucione tu infraestructura y proceso de deploy.