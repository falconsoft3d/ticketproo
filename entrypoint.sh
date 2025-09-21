#!/bin/bash

# Salir inmediatamente si algún comando falla
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== TicketProo Entrypoint Script ===${NC}"

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

# Crear directorio de logs si no existe
mkdir -p /app/logs

# Crear directorios necesarios
log "Creando directorios necesarios..."
mkdir -p /app/staticfiles /app/media

# Configurar variables de entorno por defecto
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-ticket_system.settings}
export DEBUG=${DEBUG:-False}

log "Usando configuración: $DJANGO_SETTINGS_MODULE"
log "Modo DEBUG: $DEBUG"

# Esperar a que la base de datos esté lista
log "Esperando a que PostgreSQL esté listo..."
while ! nc -z db 5432; do
    sleep 0.1
done
log "PostgreSQL está listo!"

# Aplicar migraciones
log "Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
log "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si no existe
log "Verificando superusuario..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ticketproo.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
EOF

# Configurar grupos y permisos
log "Configurando grupos y permisos..."
python manage.py setup_groups

# Asignar rol de administrador
log "Asignando roles de administrador..."
python manage.py assign_admin_agent

# Verificar configuración
log "Verificando configuración de Django..."
python manage.py check --deploy 2>/dev/null || python manage.py check

log "=== Iniciando aplicación ==="

# Ejecutar el comando pasado como argumentos
exec "$@"