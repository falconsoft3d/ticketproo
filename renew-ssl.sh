#!/bin/bash

# Script para renovar certificados SSL manualmente
# Uso: ./renew-ssl.sh

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Renovando Certificados SSL ===${NC}"

# Renovar certificados
echo "Renovando certificados..."
docker-compose run --rm certbot renew

# Recargar nginx
echo "Recargando nginx..."
docker-compose exec nginx nginx -s reload

echo -e "${GREEN}¡Certificados renovados exitosamente!${NC}"
echo -e "${YELLOW}Próxima renovación automática en 12 horas${NC}"