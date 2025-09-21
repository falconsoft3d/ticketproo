#!/bin/bash

# Script de emergencia para configurar TicketProo sin SSL
# Uso: ./quick-start.sh

echo "🚀 TicketProo Quick Start (HTTP Only)"

# Parar servicios
echo "🛑 Deteniendo servicios existentes..."
docker-compose down 2>/dev/null || true

# Actualizar desde repositorio
echo "📥 Actualizando código..."
git pull origin main 2>/dev/null || echo "No hay repositorio git configurado"

# Crear docker-compose simplificado sin SSL
echo "📝 Creando docker-compose simplificado..."
cat > docker-compose-simple.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: ticketproo_db
    environment:
      POSTGRES_DB: ticketproo
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build: .
    container_name: ticketproo_web
    command: gunicorn ticket_system.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your-super-secret-key-change-in-production
      - DATABASE_URL=postgresql://postgres:postgres123@db:5432/ticketproo
      - ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: ticketproo_nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx-simple.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  default:
    name: ticketproo_network
EOF

# Crear nginx simple
echo "🌐 Creando configuración nginx simple..."
cat > nginx-simple.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 20M;
    
    upstream django {
        server web:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        location /static/ {
            alias /app/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        location /media/ {
            alias /app/media/;
            expires 1M;
            add_header Cache-Control "public";
        }
        
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }
    }
}
EOF

# Usar configuración simple
cp docker-compose-simple.yml docker-compose.yml

echo "🔨 Construyendo imagen..."
docker-compose build --no-cache

echo "🗄️  Iniciando PostgreSQL..."
docker-compose up -d db

echo "⏳ Esperando PostgreSQL..."
sleep 15

echo "🚀 Iniciando aplicación..."
docker-compose up -d web

echo "⏳ Esperando Django..."
sleep 10

echo "🌐 Iniciando nginx..."
docker-compose up -d nginx

echo "📊 Estado de servicios:"
docker-compose ps

# Obtener IP del servidor
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "tu-ip-del-servidor")

echo ""
echo "✅ TicketProo iniciado exitosamente!"
echo ""
echo "🌐 Acceso a la aplicación:"
echo "  • Local:    http://localhost"
echo "  • Público:  http://$SERVER_IP"
echo "  • Admin:    http://$SERVER_IP/admin/"
echo ""
echo "👤 Credenciales por defecto:"
echo "  • Usuario: admin"
echo "  • Password: admin123"
echo ""
echo "📝 Comandos útiles:"
echo "  • Ver logs:     docker-compose logs -f web"
echo "  • Ver estado:   docker-compose ps"
echo "  • Shell Django: docker-compose exec web python manage.py shell"
echo ""
echo "🔒 Para habilitar SSL más tarde:"
echo "  1. ./update-docker-compose.sh"
echo "  2. ./init-letsencrypt.sh"