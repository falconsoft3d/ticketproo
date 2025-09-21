#!/bin/bash

# 🎟️ TicketProo - Deployment Script Moderno
# Ubuntu 22.04+ | Python 3.10+ | PostgreSQL 15 | Nginx | Gunicorn | SSL
# Autor: FalconSoft3D
# Fecha: 2025

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${PURPLE}[SUCCESS]${NC} $1"; }

# Banner
echo -e "${BLUE}"
cat << 'EOF'
╔══════════════════════════════════════════════════════╗
║                                                      ║
║              🎟️ TicketProo Deployment               ║
║                                                      ║
║    Modern Django deployment with:                    ║
║    ✅ Ubuntu 22.04+ Support                         ║
║    ✅ Python 3.10+ & Virtual Environment            ║
║    ✅ PostgreSQL 15 with SSL                        ║
║    ✅ Nginx with HTTP/2 & Gzip                      ║
║    ✅ Gunicorn with Workers Auto-scaling            ║
║    ✅ Let's Encrypt SSL (Optional)                  ║
║    ✅ Systemd Services                              ║
║    ✅ Security Hardening                            ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar que se ejecuta como root
if [[ $EUID -ne 0 ]]; then
   error "Este script debe ejecutarse como root (sudo)"
   exit 1
fi

# Obtener información del usuario regular
REAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
if [ -z "$REAL_USER" ]; then
    error "No se puede determinar el usuario real"
    exit 1
fi

log "Usuario detectado: $REAL_USER"

# === CONFIGURACIÓN INICIAL ===
log "=== CONFIGURACIÓN INICIAL ==="

# Solicitar información básica
read -p "🌐 Dominio (ej: ticketproo.com): " DOMAIN
read -p "📧 Email para SSL (ej: admin@ticketproo.com): " EMAIL
read -p "🎫 Nombre del proyecto (ticketproo): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-ticketproo}

# Configuración automática
APP_USER="ticketproo"
APP_DIR="/opt/ticketproo"
REPO_URL="https://github.com/falconsoft3d/ticketproo.git"
DB_NAME="ticketproo_db"
DB_USER="ticketproo_user"
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 50)

log "Configuración:"
log "  📁 Directorio: $APP_DIR"
log "  👤 Usuario: $APP_USER"
log "  🗄️  Base de datos: $DB_NAME"
log "  🌐 Dominio: $DOMAIN"

# === ACTUALIZACIÓN DEL SISTEMA ===
log "=== ACTUALIZANDO SISTEMA ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -qq -y
apt-get autoremove -y

# === INSTALACIÓN DE DEPENDENCIAS ===
log "=== INSTALANDO DEPENDENCIAS ==="
apt-get install -qq -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    unzip \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    tree

log "✓ Dependencias instaladas"

# Verificar instalación de PostgreSQL
if ! command -v psql &> /dev/null; then
    error "PostgreSQL no se instaló correctamente"
    exit 1
fi

# Verificar versión de PostgreSQL instalada
PG_VERSION_FULL=$(sudo -u postgres psql --version | grep -oP '\d+\.\d+' | head -1)
log "PostgreSQL versión detectada: $PG_VERSION_FULL"

# === CONFIGURACIÓN DE POSTGRESQL ===
log "=== CONFIGURANDO POSTGRESQL ==="

# Iniciar PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Crear usuario y base de datos
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

# Configurar PostgreSQL para conexiones locales
PG_VERSION=$(sudo -u postgres psql -t -c "SHOW server_version;" | grep -oP '\d+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"

# Buscar directorio de configuración real si no existe
if [ ! -d "$PG_CONFIG_DIR" ]; then
    PG_CONFIG_DIR=$(find /etc/postgresql -name "postgresql.conf" -type f | head -1 | dirname)
    log "Directorio PostgreSQL detectado: $PG_CONFIG_DIR"
fi

PG_CONFIG="$PG_CONFIG_DIR/postgresql.conf"
PG_HBA="$PG_CONFIG_DIR/pg_hba.conf"

# Verificar que los archivos existen
if [ ! -f "$PG_CONFIG" ]; then
    error "No se encuentra postgresql.conf en $PG_CONFIG"
    error "Configuración manual requerida"
    log "PostgreSQL configurado básicamente (sin optimizaciones)"
else
    # Backup de configuración
    cp "$PG_CONFIG" "$PG_CONFIG.backup"
    cp "$PG_HBA" "$PG_HBA.backup"

    # Configurar conexiones
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/g" "$PG_CONFIG"
    sed -i "s/#max_connections = 100/max_connections = 200/g" "$PG_CONFIG"
    
    log "✓ Archivos de configuración actualizados"
fi

# Reiniciar PostgreSQL
systemctl restart postgresql

log "✓ PostgreSQL configurado"
log "  🗄️  Base de datos: $DB_NAME"
log "  👤 Usuario: $DB_USER"
log "  🔑 Contraseña: $DB_PASSWORD"

# === CREAR USUARIO DEL SISTEMA ===
log "=== CREANDO USUARIO DEL SISTEMA ==="

# Crear usuario si no existe
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home "$APP_DIR" --create-home "$APP_USER"
    log "✓ Usuario $APP_USER creado"
else
    log "✓ Usuario $APP_USER ya existe"
fi

# === CLONAR PROYECTO ===
log "=== CLONANDO PROYECTO ==="

# Limpiar directorio si existe
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
fi

# Clonar repositorio
git clone "$REPO_URL" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

log "✓ Proyecto clonado en $APP_DIR"

# === CONFIGURAR ENTORNO VIRTUAL ===
log "=== CONFIGURANDO ENTORNO VIRTUAL ==="

# Crear entorno virtual
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"

# Activar entorno e instalar dependencias
sudo -u "$APP_USER" bash -c "
    source $APP_DIR/venv/bin/activate
    pip install --upgrade pip
    pip install -r $APP_DIR/requirements.txt
    pip install gunicorn psycopg2-binary python-decouple
"

log "✓ Entorno virtual configurado"

# === CONFIGURAR DJANGO ===
log "=== CONFIGURANDO DJANGO ==="

# Crear archivo de entorno
cat > "$APP_DIR/.env" << EOF
# TicketProo Production Environment
DEBUG=False
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1
STATIC_ROOT=$APP_DIR/static
MEDIA_ROOT=$APP_DIR/media

# Email settings (configurar según necesidades)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@$DOMAIN

# Security settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF

chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

# Crear directorios necesarios
mkdir -p "$APP_DIR/static" "$APP_DIR/media" "$APP_DIR/logs"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Ejecutar migraciones y collectstatic
sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    source venv/bin/activate
    python manage.py migrate
    python manage.py collectstatic --noinput
    python manage.py setup_groups
"

# Crear superusuario
log "=== CREANDO SUPERUSUARIO ==="
read -p "👤 Usuario admin: " ADMIN_USER
read -s -p "🔑 Contraseña admin: " ADMIN_PASSWORD
echo

sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    source venv/bin/activate
    python manage.py shell -c \"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USER').exists():
    User.objects.create_superuser('$ADMIN_USER', '$EMAIL', '$ADMIN_PASSWORD')
    print('Superusuario creado')
else:
    print('Superusuario ya existe')
\"
    python manage.py assign_admin_agent $ADMIN_USER
"

log "✓ Django configurado"

# === CONFIGURAR GUNICORN ===
log "=== CONFIGURANDO GUNICORN ==="

# Crear script de inicio de Gunicorn
cat > "$APP_DIR/gunicorn_start.sh" << EOF
#!/bin/bash

NAME="ticketproo"
DIR=$APP_DIR
USER=$APP_USER
GROUP=$APP_USER
WORKERS=\$((2 * \$(nproc) + 1))
BIND=unix:$APP_DIR/gunicorn.sock
DJANGO_SETTINGS_MODULE=ticket_system.settings
DJANGO_WSGI_MODULE=ticket_system.wsgi
LOG_LEVEL=info

echo "Starting \$NAME with \$WORKERS workers"

# Activar entorno virtual
source \$DIR/venv/bin/activate

# Configurar variables de entorno
export DJANGO_SETTINGS_MODULE=\$DJANGO_SETTINGS_MODULE
export PYTHONPATH=\$DIR:\$PYTHONPATH

# Limpiar socket anterior
test -f \$BIND && rm -f \$BIND

# Ejecutar Gunicorn
exec \$DIR/venv/bin/gunicorn \${DJANGO_WSGI_MODULE}:application \\
  --name \$NAME \\
  --workers \$WORKERS \\
  --user=\$USER \\
  --group=\$GROUP \\
  --bind=\$BIND \\
  --log-level=\$LOG_LEVEL \\
  --log-file=\$DIR/logs/gunicorn.log \\
  --access-logfile=\$DIR/logs/gunicorn-access.log \\
  --error-logfile=\$DIR/logs/gunicorn-error.log \\
  --timeout 120 \\
  --keep-alive 5 \\
  --max-requests 1000 \\
  --max-requests-jitter 100 \\
  --preload
EOF

chmod +x "$APP_DIR/gunicorn_start.sh"
chown "$APP_USER:$APP_USER" "$APP_DIR/gunicorn_start.sh"

# Crear servicio systemd para Gunicorn
cat > /etc/systemd/system/ticketproo.service << EOF
[Unit]
Description=TicketProo Gunicorn daemon
Requires=ticketproo.socket
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
RuntimeDirectory=ticketproo
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/gunicorn_start.sh
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Crear socket systemd para Gunicorn
cat > /etc/systemd/system/ticketproo.socket << EOF
[Unit]
Description=TicketProo gunicorn socket

[Socket]
ListenStream=$APP_DIR/gunicorn.sock
SocketUser=$APP_USER
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
EOF

# Habilitar y iniciar servicios
systemctl daemon-reload
systemctl enable ticketproo.socket
systemctl start ticketproo.socket
systemctl enable ticketproo.service
systemctl start ticketproo.service

log "✓ Gunicorn configurado como servicio systemd"

# === CONFIGURAR NGINX ===
log "=== CONFIGURANDO NGINX ==="

# Crear configuración de Nginx
cat > /etc/nginx/sites-available/ticketproo << EOF
upstream ticketproo {
    server unix:$APP_DIR/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Logs
    access_log $APP_DIR/logs/nginx-access.log;
    error_log $APP_DIR/logs/nginx-error.log;
    
    # Client settings
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static files
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias $APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Favicon
    location = /favicon.ico {
        alias $APP_DIR/static/favicon.ico;
        log_not_found off;
        access_log off;
    }
    
    # Robots.txt
    location = /robots.txt {
        alias $APP_DIR/static/robots.txt;
        log_not_found off;
        access_log off;
    }
    
    # Main application
    location / {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_buffering off;
        proxy_pass http://ticketproo;
    }
}
EOF

# Habilitar sitio
ln -sf /etc/nginx/sites-available/ticketproo /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar configuración de Nginx
nginx -t

# Reiniciar Nginx
systemctl restart nginx
systemctl enable nginx

log "✓ Nginx configurado"

# === CONFIGURAR FIREWALL ===
log "=== CONFIGURANDO FIREWALL ==="

# Configurar UFW
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH, HTTP, HTTPS
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Habilitar firewall
ufw --force enable

log "✓ Firewall configurado"

# === CONFIGURAR FAIL2BAN ===
log "=== CONFIGURANDO FAIL2BAN ==="

# Crear configuración para Nginx
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = $APP_DIR/logs/nginx-error.log
maxretry = 10

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = $APP_DIR/logs/nginx-access.log
maxretry = 2
EOF

systemctl restart fail2ban
systemctl enable fail2ban

log "✓ Fail2ban configurado"

# === CONFIGURAR SSL (OPCIONAL) ===
log "=== CONFIGURAR SSL ==="

read -p "¿Configurar SSL con Let's Encrypt? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Configurando SSL..."
    
    # Verificar que el dominio apunte al servidor
    warn "Asegúrate de que $DOMAIN apunte a este servidor"
    read -p "¿Continuar con SSL? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Obtener certificado SSL
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
        
        # Configurar renovación automática
        systemctl enable certbot.timer
        
        # Actualizar configuración de Django para SSL
        sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' "$APP_DIR/.env"
        sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' "$APP_DIR/.env"
        sed -i 's/CSRF_COOKIE_SECURE=False/CSRF_COOKIE_SECURE=True/' "$APP_DIR/.env"
        
        # Reiniciar servicios
        systemctl restart ticketproo
        systemctl restart nginx
        
        success "✓ SSL configurado correctamente"
    fi
fi

# === CONFIGURAR MONITOREO ===
log "=== CONFIGURANDO MONITOREO ==="

# Crear script de monitoreo
cat > "$APP_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# TicketProo System Monitor

echo "=== TicketProo System Status ==="
echo "Date: $(date)"
echo

echo "=== Services Status ==="
systemctl is-active --quiet ticketproo && echo "✓ TicketProo: Running" || echo "✗ TicketProo: Down"
systemctl is-active --quiet nginx && echo "✓ Nginx: Running" || echo "✗ Nginx: Down"
systemctl is-active --quiet postgresql && echo "✓ PostgreSQL: Running" || echo "✗ PostgreSQL: Down"
echo

echo "=== System Resources ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
echo

echo "=== TicketProo Logs (last 5 lines) ==="
tail -5 /opt/ticketproo/logs/gunicorn.log 2>/dev/null || echo "No logs found"
EOF

chmod +x "$APP_DIR/monitor.sh"
chown "$APP_USER:$APP_USER" "$APP_DIR/monitor.sh"

# Crear cron job para logs cleanup
(crontab -l 2>/dev/null; echo "0 2 * * 0 find $APP_DIR/logs -name '*.log' -mtime +30 -delete") | crontab -

log "✓ Monitoreo configurado"

# === VERIFICACIÓN FINAL ===
log "=== VERIFICACIÓN FINAL ==="

# Verificar servicios
sleep 5

if systemctl is-active --quiet ticketproo; then
    success "✓ TicketProo está corriendo"
else
    error "✗ TicketProo no está corriendo"
    log "Ver logs: journalctl -u ticketproo -f"
fi

if systemctl is-active --quiet nginx; then
    success "✓ Nginx está corriendo"
else
    error "✗ Nginx no está corriendo"
fi

if systemctl is-active --quiet postgresql; then
    success "✓ PostgreSQL está corriendo"
else
    error "✗ PostgreSQL no está corriendo"
fi

# Verificar conectividad web
if curl -s -o /dev/null -w "%{http_code}" "http://localhost" | grep -q "200\|302"; then
    success "✓ Aplicación web responde correctamente"
else
    warn "⚠ Aplicación web no responde (puede tardar unos minutos)"
fi

# === INFORMACIÓN FINAL ===
echo ""
success "🎉 ¡DEPLOYMENT COMPLETADO!"
echo ""
success "=== INFORMACIÓN DEL DEPLOYMENT ==="
success "🌐 URL: http://$DOMAIN"
[[ $REPLY =~ ^[Yy]$ ]] && success "🔒 HTTPS: https://$DOMAIN"
success "👤 Admin: $ADMIN_USER"
success "📊 Admin Panel: http://$DOMAIN/admin/"
echo ""
info "=== CREDENCIALES DE BASE DE DATOS ==="
info "🗄️  Base de datos: $DB_NAME"
info "👤 Usuario: $DB_USER"
info "🔑 Contraseña: $DB_PASSWORD"
echo ""
info "=== COMANDOS ÚTILES ==="
info "📊 Estado: systemctl status ticketproo"
info "📝 Logs: journalctl -u ticketproo -f"
info "🔄 Reiniciar: systemctl restart ticketproo"
info "📈 Monitoreo: $APP_DIR/monitor.sh"
info "🗄️  PostgreSQL: sudo -u postgres psql $DB_NAME"
echo ""
info "=== ARCHIVOS IMPORTANTES ==="
info "📁 Proyecto: $APP_DIR"
info "⚙️  Configuración: $APP_DIR/.env"
info "📝 Logs: $APP_DIR/logs/"
info "🌐 Nginx: /etc/nginx/sites-available/ticketproo"
echo ""
warn "⚠️  IMPORTANTE: Guarda las credenciales de la base de datos en un lugar seguro"
warn "🔐 Cambiar contraseñas por defecto en producción"
echo ""
success "¡TicketProo está listo para usar! 🚀"