#!/bin/bash

# Script para generar certificados SSL manualmente

set -e

echo "🔐 Generando certificados SSL para ticketproo.com"

# Variables
DOMAIN="ticketproo.com"
EMAIL="admin@ticketproo.com"  # Cambia por tu email

# Crear configuración temporal de nginx para verificación
cat > nginx-temp.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name ticketproo.com www.ticketproo.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 200 'OK';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Crear docker-compose temporal para certbot
cat > docker-compose-ssl.yml << 'EOF'
version: '3.8'

services:
  nginx-temp:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-temp.conf:/etc/nginx/nginx.conf
      - certbot-www:/var/www/certbot
    networks:
      - app-network

  certbot:
    image: certbot/certbot
    volumes:
      - certbot-www:/var/www/certbot
      - certbot-conf:/etc/letsencrypt
    command: certonly --webroot --webroot-path=/var/www/certbot --email admin@ticketproo.com --agree-tos --no-eff-email -d ticketproo.com -d www.ticketproo.com
    networks:
      - app-network

volumes:
  certbot-www:
  certbot-conf:

networks:
  app-network:
    driver: bridge
EOF

echo "🚀 Iniciando nginx temporal..."
docker-compose -f docker-compose-ssl.yml up -d nginx-temp

echo "⏳ Esperando 10 segundos para que nginx esté listo..."
sleep 10

echo "🔐 Generando certificados..."
docker-compose -f docker-compose-ssl.yml run --rm certbot

echo "✅ Certificados generados!"

# Copiar certificados al volumen principal
echo "📁 Copiando certificados..."
docker run --rm \
  -v $(pwd)_certbot-conf:/source \
  -v ticketproo_certbot-conf:/dest \
  alpine sh -c "cp -r /source/* /dest/"

# Limpiar
echo "🧹 Limpiando archivos temporales..."
docker-compose -f docker-compose-ssl.yml down -v
rm nginx-temp.conf docker-compose-ssl.yml

echo "🎉 ¡Certificados SSL listos!"
echo "Ahora ejecuta: docker-compose up -d"