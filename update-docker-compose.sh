#!/bin/bash

# Script para actualizar docker-compose.yml con soporte SSL automático
# Uso: ./update-docker-compose.sh

echo "🔧 Actualizando docker-compose.yml para soporte SSL..."

# Backup del archivo actual
cp docker-compose.yml docker-compose.yml.backup 2>/dev/null || true

# Crear docker-compose.yml completo con SSL
cat > docker-compose.yml << 'EOF'
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
      - ./db_backup:/docker-entrypoint-initdb.d
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
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - certbot_certs:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    depends_on:
      - web
    restart: unless-stopped
    command: '/bin/sh -c ''while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g "daemon off;"'''

  certbot:
    image: certbot/certbot
    container_name: ticketproo_certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
  certbot_certs:
  certbot_www:

networks:
  default:
    name: ticketproo_network
EOF

echo "✅ docker-compose.yml actualizado con soporte SSL"

# Verificar la sintaxis
if docker-compose config > /dev/null 2>&1; then
    echo "✅ Sintaxis de docker-compose.yml válida"
else
    echo "❌ Error en sintaxis de docker-compose.yml"
    echo "🔄 Restaurando backup..."
    cp docker-compose.yml.backup docker-compose.yml 2>/dev/null || true
    exit 1
fi

echo "🚀 Reconstruyendo servicios..."
docker-compose down
docker-compose build --no-cache

echo "✅ Servicios actualizados!"
echo ""
echo "📝 Próximos pasos:"
echo "1. ./fix-dependencies.sh  # Solucionar dependencias"
echo "2. ./init-letsencrypt.sh   # Configurar SSL"
echo ""
echo "🌐 O para inicio rápido sin SSL:"
echo "./quick-start.sh"