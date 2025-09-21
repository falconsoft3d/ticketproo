#!/bin/bash

# Script de emergencia para configurar TicketProo sin SSL
# Uso: ./quick-start.sh

echo "🚀 TicketProo Quick Start (HTTP Only)"

# Parar servicios
echo "Deteniendo servicios..."
docker-compose down 2>/dev/null || true

# Crear nginx simple
echo "Creando configuración nginx simple..."
cat > nginx-simple.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    upstream django {
        server web:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        location /static/ {
            alias /app/staticfiles/;
        }
        
        location /media/ {
            alias /app/media/;
        }
        
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Backup y usar configuración simple
cp nginx.conf nginx.conf.backup 2>/dev/null || true
cp nginx-simple.conf nginx.conf

# Comentar servicio certbot en docker-compose
cp docker-compose.yml docker-compose.yml.backup
sed '/certbot:/,/restart: unless-stopped/d' docker-compose.yml.backup > docker-compose-simple.yml
sed '/certbot_certs:/d; /certbot_www:/d' docker-compose-simple.yml > docker-compose.yml

# Iniciar servicios
echo "Iniciando servicios..."
docker-compose up -d --build

echo ""
echo "✅ TicketProo iniciado en modo HTTP simple"
echo "🌐 Accede en: http://$(curl -s ifconfig.me)"
echo "🔧 Admin: http://$(curl -s ifconfig.me)/admin/"
echo ""
echo "Para restaurar SSL más tarde:"
echo "1. cp nginx.conf.backup nginx.conf"
echo "2. cp docker-compose.yml.backup docker-compose.yml"
echo "3. ./fix-ssl.sh"