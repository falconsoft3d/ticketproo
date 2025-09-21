#!/bin/bash

# Script de diagnóstico y reparación SSL para TicketProo
# Uso: ./fix-ssl.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== TicketProo SSL Fix Script ===${NC}"

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Paso 1: Diagnóstico inicial
log "=== PASO 1: DIAGNÓSTICO ==="

echo "Verificando estado actual..."
docker-compose ps || warn "Docker-compose no está corriendo"

echo "Verificando certificados existentes..."
docker-compose exec certbot ls -la /etc/letsencrypt/live/ 2>/dev/null || warn "No hay certificados"

echo "Verificando configuración de nginx..."
docker-compose exec nginx nginx -t 2>/dev/null || warn "Error en configuración nginx"

# Paso 2: Detener servicios y limpiar
log "=== PASO 2: LIMPIEZA ==="

echo "Deteniendo servicios..."
docker-compose down

echo "Limpiando volúmenes de certificados..."
docker volume rm ticketproo_certbot_certs 2>/dev/null || true
docker volume rm ticketproo_certbot_www 2>/dev/null || true

# Paso 3: Crear configuración nginx temporal
log "=== PASO 3: CONFIGURACIÓN TEMPORAL ==="

echo "Creando nginx temporal sin SSL..."
cat > nginx-temp.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    
    upstream django {
        server web:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Ubicación para validación de Let's Encrypt
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
            try_files $uri $uri/ =404;
        }
        
        # Aplicación Django
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Archivos estáticos
        location /static/ {
            alias /app/staticfiles/;
        }
        
        # Archivos media
        location /media/ {
            alias /app/media/;
        }
    }
}
EOF

# Backup de configuración original
cp nginx.conf nginx.conf.backup 2>/dev/null || true
cp nginx-temp.conf nginx.conf

# Paso 4: Iniciar servicios base
log "=== PASO 4: INICIAR SERVICIOS BASE ==="

echo "Iniciando base de datos..."
docker-compose up -d db

echo "Esperando que PostgreSQL esté listo..."
sleep 10

echo "Iniciando aplicación web..."
docker-compose up -d web

echo "Esperando que Django esté listo..."
sleep 5

echo "Iniciando nginx temporal..."
docker-compose up -d nginx

# Verificar que los servicios estén funcionando
log "Verificando servicios..."
docker-compose ps

# Paso 5: Obtener dominio del usuario
log "=== PASO 5: CONFIGURACIÓN DE DOMINIO ==="

echo ""
echo -e "${YELLOW}¿Cuál es tu dominio? (ejemplo: ticketproo.com)${NC}"
read -p "Dominio: " domain

if [ -z "$domain" ]; then
    error "Debes proporcionar un dominio"
    exit 1
fi

echo ""
echo -e "${YELLOW}¿Cuál es tu email para Let's Encrypt? (ejemplo: admin@$domain)${NC}"
read -p "Email: " email

if [ -z "$email" ]; then
    email="admin@$domain"
fi

# Paso 6: Verificar que el dominio apunte al servidor
log "=== PASO 6: VERIFICACIÓN DE DOMINIO ==="

echo "Verificando que $domain apunte a este servidor..."
server_ip=$(curl -s ifconfig.me)
domain_ip=$(dig +short $domain)

echo "IP del servidor: $server_ip"
echo "IP del dominio: $domain_ip"

if [ "$server_ip" != "$domain_ip" ]; then
    warn "El dominio $domain no apunta a este servidor ($server_ip)"
    echo "Configura los DNS de tu dominio para que apunten a: $server_ip"
    echo ""
    read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Paso 7: Obtener certificados SSL
log "=== PASO 7: OBTENER CERTIFICADOS SSL ==="

echo "Obteniendo certificado SSL para $domain..."

# Crear directorio para certificados
docker-compose exec certbot mkdir -p /etc/letsencrypt/live/$domain

# Obtener certificado usando webroot
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot \
    -w /var/www/certbot \
    -d $domain \
    --email $email \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    --verbose" certbot

if [ $? -eq 0 ]; then
    log "¡Certificado SSL obtenido exitosamente!"
else
    error "Error al obtener certificado SSL"
    echo "Intentando con certificado auto-firmado para testing..."
    
    # Crear certificado auto-firmado como fallback
    docker-compose run --rm --entrypoint "\
      openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
        -keyout '/etc/letsencrypt/live/$domain/privkey.pem' \
        -out '/etc/letsencrypt/live/$domain/fullchain.pem' \
        -subj '/C=ES/ST=Madrid/L=Madrid/O=TicketProo/CN=$domain'" certbot
    
    # Crear chain.pem
    docker-compose run --rm --entrypoint "\
      cp '/etc/letsencrypt/live/$domain/fullchain.pem' '/etc/letsencrypt/live/$domain/chain.pem'" certbot
    
    warn "Se creó un certificado auto-firmado. Para usar Let's Encrypt real, verifica tu configuración DNS."
fi

# Paso 8: Configurar nginx con SSL
log "=== PASO 8: CONFIGURAR NGINX CON SSL ==="

echo "Creando configuración nginx con SSL..."
cat > nginx-ssl.conf << EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 20M;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    upstream django {
        server web:8000;
    }
    
    # Redirigir HTTP a HTTPS
    server {
        listen 80;
        server_name $domain;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://\$host\$request_uri;
        }
    }
    
    # Servidor HTTPS
    server {
        listen 443 ssl http2;
        server_name $domain;
        
        # Certificados SSL
        ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
        
        # Configuración SSL moderna
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Archivos estáticos
        location /static/ {
            alias /app/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Archivos media
        location /media/ {
            alias /app/media/;
            expires 1M;
            add_header Cache-Control "public";
        }
        
        # Aplicación Django
        location / {
            proxy_pass http://django;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

# Reemplazar configuración nginx
cp nginx-ssl.conf nginx.conf

# Paso 9: Reiniciar con SSL
log "=== PASO 9: REINICIAR CON SSL ==="

echo "Reiniciando nginx con SSL..."
docker-compose restart nginx

# Verificar configuración
echo "Verificando configuración SSL..."
docker-compose exec nginx nginx -t

if [ $? -eq 0 ]; then
    log "¡Configuración nginx válida!"
else
    error "Error en configuración nginx"
    echo "Restaurando configuración temporal..."
    cp nginx-temp.conf nginx.conf
    docker-compose restart nginx
    exit 1
fi

# Paso 10: Verificación final
log "=== PASO 10: VERIFICACIÓN FINAL ==="

echo "Estado de servicios:"
docker-compose ps

echo ""
echo "Verificando conectividad HTTPS..."
sleep 5

if curl -k -s https://$domain > /dev/null; then
    log "¡HTTPS funcionando correctamente!"
else
    warn "Problema con HTTPS, verificar logs"
fi

echo "" 
echo -e "${GREEN}=== CONFIGURACIÓN SSL COMPLETADA ===${NC}"
echo -e "✅ Dominio: ${GREEN}$domain${NC}"
echo -e "✅ HTTPS: ${GREEN}https://$domain${NC}"
echo -e "✅ Admin: ${GREEN}https://$domain/admin/${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Verificar que tu aplicación funcione en: https://$domain"
echo "2. Configurar renovación automática de certificados"
echo "3. Actualizar configuración de Django para HTTPS"
echo ""
echo -e "${BLUE}Para ver logs:${NC}"
echo "docker-compose logs nginx"
echo "docker-compose logs certbot"

# Limpiar archivos temporales
rm -f nginx-temp.conf nginx-ssl.conf