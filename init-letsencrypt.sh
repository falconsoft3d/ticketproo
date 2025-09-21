#!/bin/bash

# Script para inicializar certificados SSL con Let's Encrypt
# Uso: ./init-letsencrypt.sh

set -e

# Configuración
domains=(localhost)  # Cambia por tu dominio real
rsa_key_size=4096
data_path="./certbot"
email="admin@localhost"  # Cambia por tu email real
staging=1  # Set to 1 if you're testing your setup to avoid hitting request limits

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TicketProo SSL Setup con Let's Encrypt ===${NC}"

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

# Verificar que docker-compose esté disponible
if ! command -v docker-compose &> /dev/null; then
    error "docker-compose no está instalado"
    exit 1
fi

# Verificar que el archivo docker-compose.yml existe
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml no encontrado en el directorio actual"
    exit 1
fi

# Advertencia para dominios de prueba
if [[ " ${domains[@]} " =~ " localhost " ]]; then
    warn "Estás usando 'localhost' como dominio."
    warn "Para producción, cambia 'localhost' por tu dominio real en:"
    warn "1. Este script (variable 'domains')"
    warn "2. nginx.conf (server_name)"
    warn "3. .env (ALLOWED_HOSTS)"
    echo ""
    read -p "¿Continuar con localhost para testing? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log "Iniciando configuración SSL para dominios: ${domains[*]}"

# Crear estructura de directorios
log "Creando estructura de directorios..."
mkdir -p "$data_path/conf/live"
mkdir -p "$data_path/www"

# Descargar configuración recomendada de TLS de certbot
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
    log "Descargando configuración SSL recomendada de certbot..."
    mkdir -p "$data_path/conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
fi

# Crear certificado dummy para nginx
log "Creando certificados dummy para nginx..."
path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"

docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot

# Crear chain.pem (copia de fullchain.pem para OCSP stapling)
docker-compose run --rm --entrypoint "\
  cp '$path/fullchain.pem' '$path/chain.pem'" certbot

log "Certificados dummy creados"

# Iniciar nginx
log "Iniciando nginx con certificados dummy..."
docker-compose up --force-recreate -d nginx

# Eliminar certificado dummy
log "Eliminando certificados dummy..."
docker-compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/${domains[0]} && \
  rm -Rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -Rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot

log "Certificados dummy eliminados"

# Seleccionar servidor de certificación apropiado
if [ $staging != "0" ]; then
    staging_arg="--staging"
    log "Usando servidor de staging de Let's Encrypt (para testing)"
else
    staging_arg=""
    log "Usando servidor de producción de Let's Encrypt"
fi

# Crear dominio principal
domain_args=""
for domain in "${domains[@]}"; do
    domain_args="$domain_args -d $domain"
done

# Obtener certificado
log "Solicitando certificado SSL para ${domains[*]}..."

# Solo para localhost/testing, usar certificados auto-firmados
if [[ " ${domains[@]} " =~ " localhost " ]] && [ $staging == "1" ]; then
    warn "Para localhost, creando certificados auto-firmados..."
    
    # Crear certificados auto-firmados para localhost
    path="/etc/letsencrypt/live/${domains[0]}"
    mkdir -p "$data_path/conf/live/${domains[0]}"
    
    docker-compose run --rm --entrypoint "\
      openssl req -x509 -nodes -days 365 -newkey rsa:$rsa_key_size \
        -keyout '$path/privkey.pem' \
        -out '$path/fullchain.pem' \
        -out '$path/chain.pem' \
        -subj '/C=ES/ST=Madrid/L=Madrid/O=TicketProo/OU=IT/CN=localhost'" certbot
    
    log "Certificados auto-firmados creados para localhost"
else
    # Usar Let's Encrypt para dominios reales
    docker-compose run --rm --entrypoint "\
      certbot certonly --webroot -w /var/www/certbot \
        $staging_arg \
        $domain_args \
        --email $email \
        --rsa-key-size $rsa_key_size \
        --agree-tos \
        --force-renewal" certbot
fi

# Recargar nginx
log "Recargando nginx con certificados SSL..."
docker-compose exec nginx nginx -s reload

log "¡SSL configurado exitosamente!"
echo ""
echo -e "${GREEN}=== Configuración Completada ===${NC}"
echo -e "✅ Certificados SSL: ${GREEN}Activos${NC}"
echo -e "✅ Nginx HTTPS: ${GREEN}Configurado${NC}"
echo -e "✅ Renovación automática: ${GREEN}Activada${NC}"
echo ""
echo -e "${BLUE}Accede a tu aplicación:${NC}"
echo -e "🌐 HTTPS: ${GREEN}https://${domains[0]}${NC}"
echo -e "🔒 Admin: ${GREEN}https://${domains[0]}/admin/${NC}"
echo ""

if [ $staging == "1" ]; then
    warn "Estás usando certificados de staging/testing."
    warn "Para producción:"
    warn "1. Cambia 'staging=1' a 'staging=0' en este script"
    warn "2. Cambia 'localhost' por tu dominio real"
    warn "3. Ejecuta el script nuevamente"
fi

echo -e "${YELLOW}Notas importantes:${NC}"
echo "• Los certificados se renuevan automáticamente cada 12 horas"
echo "• Para dominios reales, asegúrate de que apunten a este servidor"
echo "• Revisa los logs con: docker-compose logs nginx certbot"