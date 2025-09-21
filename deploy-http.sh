#!/bin/bash

# Script para deployment rápido sin SSL inicialmente

echo "🚀 Deployment rápido - HTTP primero, SSL después"

# Detener todo
docker-compose down -v

# Crear configuración nginx temporal (solo HTTP)
cp nginx.conf nginx.conf.backup

cat > nginx-http.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name ticketproo.com www.ticketproo.com;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/staticfiles/;
        }

        location /media/ {
            alias /app/media/;
        }
    }
}
EOF

# Usar configuración HTTP temporal
mv nginx.conf nginx-ssl.conf
mv nginx-http.conf nginx.conf

# Iniciar servicios
echo "📊 Iniciando base de datos..."
docker-compose up -d db

echo "⏳ Esperando PostgreSQL..."
sleep 15

echo "🌐 Iniciando aplicación web..."
docker-compose up -d web

echo "🔄 Ejecutando migraciones..."
docker-compose exec web python manage.py migrate

echo "👤 Configurando usuarios..."
docker-compose exec web python manage.py setup_groups
docker-compose exec web python manage.py assign_admin_agent admin

echo "📁 Archivos estáticos..."
docker-compose exec web python manage.py collectstatic --noinput

echo "🌍 Iniciando Nginx..."
docker-compose up -d nginx

echo "✅ ¡Aplicación funcionando en HTTP!"
echo "🌐 Visita: http://ticketproo.com"
echo ""
echo "Para habilitar SSL después:"
echo "1. mv nginx-ssl.conf nginx.conf"
echo "2. ./init-letsencrypt.sh"
echo "3. docker-compose restart nginx"