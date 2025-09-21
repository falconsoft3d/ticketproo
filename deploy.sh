#!/bin/bash

# Script de deployment completo para TicketPro
# Incluye configuración de base de datos, SSL y deployment

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║           TicketPro Deploy           ║"
echo "║      Deployment Automation Tool      ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ] || [ ! -f "docker-compose.yml" ]; then
    error "Este script debe ejecutarse desde el directorio raíz del proyecto TicketPro"
    error "Archivos requeridos: manage.py, docker-compose.yml"
    exit 1
fi

log "Verificando sistema..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Instálalo desde https://docker.com"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado."
    exit 1
fi

# Verificar que Docker esté corriendo
if ! docker info &> /dev/null; then
    error "Docker no está corriendo. Inicia Docker Desktop."
    exit 1
fi

log "✓ Docker está instalado y corriendo"

# Menú de opciones
echo ""
info "Selecciona el tipo de deployment:"
echo "1) Desarrollo local (HTTP, localhost)"
echo "2) Producción (HTTPS, dominio real)"
echo "3) Solo base de datos PostgreSQL"
echo "4) Verificar estado actual"
echo ""
read -p "Opción (1-4): " deploy_option

case $deploy_option in
    1)
        log "Configurando deployment de desarrollo..."
        
        # Crear archivo .env para desarrollo
        cat > .env << EOF
# Configuración de desarrollo
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://ticketproo_user:ticketproo_password@db:5432/ticketproo_db
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
EOF

        log "✓ Archivo .env creado para desarrollo"
        
        # Construir e iniciar servicios
        log "Construyendo e iniciando servicios..."
        docker-compose build
        docker-compose up -d db
        
        # Esperar a que PostgreSQL esté listo
        log "Esperando a que PostgreSQL esté listo..."
        sleep 10
        
        # Ejecutar migraciones
        log "Ejecutando migraciones de Django..."
        docker-compose run --rm web python manage.py migrate
        
        # Crear superusuario
        log "Configurando superusuario..."
        docker-compose run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin / admin123')
else:
    print('Superusuario ya existe')
"

        # Configurar grupos y permisos
        log "Configurando grupos y permisos..."
        docker-compose run --rm web python manage.py setup_groups
        docker-compose run --rm web python manage.py assign_admin_agent admin
        
        # Recopilar archivos estáticos
        log "Recopilando archivos estáticos..."
        docker-compose run --rm web python manage.py collectstatic --noinput
        
        # Iniciar todos los servicios
        log "Iniciando todos los servicios..."
        docker-compose up -d
        
        log "✅ Deployment de desarrollo completado!"
        log "🌐 Accede a: http://localhost"
        log "👤 Admin: admin / admin123"
        ;;
        
    2)
        log "Configurando deployment de producción..."
        
        # Solicitar información del dominio
        echo ""
        read -p "Ingresa tu dominio (ej: ticketpro.example.com): " domain
        read -p "Ingresa tu email para SSL (ej: admin@example.com): " email
        
        if [ -z "$domain" ] || [ -z "$email" ]; then
            error "Dominio y email son requeridos para deployment de producción"
            exit 1
        fi
        
        # Generar SECRET_KEY aleatoria
        secret_key=$(openssl rand -base64 32)
        
        # Crear archivo .env para producción
        cat > .env << EOF
# Configuración de producción
DEBUG=False
SECRET_KEY=$secret_key
DATABASE_URL=postgresql://ticketproo_user:ticketproo_password@db:5432/ticketproo_db
ALLOWED_HOSTS=$domain,www.$domain
DOMAIN=$domain
EMAIL=$email
EOF

        log "✓ Archivo .env creado para producción"
        
        # Actualizar nginx.conf con el dominio
        log "Configurando Nginx para dominio: $domain"
        sed -i.bak "s/localhost/$domain/g" nginx.conf
        
        # Construir e iniciar servicios
        log "Construyendo e iniciando servicios..."
        docker-compose build
        docker-compose up -d db
        
        # Esperar a que PostgreSQL esté listo
        log "Esperando a que PostgreSQL esté listo..."
        sleep 15
        
        # Ejecutar migraciones
        log "Ejecutando migraciones de Django..."
        docker-compose run --rm web python manage.py migrate
        
        # Crear superusuario
        echo ""
        log "Configurando superusuario para producción..."
        read -p "Usuario admin: " admin_user
        read -p "Email admin: " admin_email
        read -s -p "Contraseña admin: " admin_password
        echo ""
        
        docker-compose run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$admin_user').exists():
    User.objects.create_superuser('$admin_user', '$admin_email', '$admin_password')
    print('Superusuario creado: $admin_user')
else:
    print('Superusuario ya existe')
"

        # Configurar grupos y permisos
        log "Configurando grupos y permisos..."
        docker-compose run --rm web python manage.py setup_groups
        docker-compose run --rm web python manage.py assign_admin_agent $admin_user
        
        # Recopilar archivos estáticos
        log "Recopilando archivos estáticos..."
        docker-compose run --rm web python manage.py collectstatic --noinput
        
        # Iniciar servicios web y nginx
        log "Iniciando servicios web..."
        docker-compose up -d web nginx
        
        # Configurar SSL
        log "Configurando SSL con Let's Encrypt..."
        chmod +x init-letsencrypt.sh
        ./init-letsencrypt.sh
        
        log "✅ Deployment de producción completado!"
        log "🌐 Accede a: https://$domain"
        log "👤 Admin: $admin_user"
        ;;
        
    3)
        log "Iniciando solo PostgreSQL..."
        docker-compose up -d db
        log "✅ PostgreSQL iniciado en puerto 5432"
        log "📊 Conexión: postgresql://ticketproo_user:ticketproo_password@localhost:5432/ticketproo_db"
        ;;
        
    4)
        log "Verificando estado actual..."
        echo ""
        info "Servicios Docker:"
        docker-compose ps
        echo ""
        info "Logs recientes:"
        docker-compose logs --tail=10
        ;;
        
    *)
        error "Opción inválida"
        exit 1
        ;;
esac

echo ""
log "🎉 ¡Deployment completado!"
log "📝 Para ver logs: docker-compose logs -f"
log "🛑 Para detener: docker-compose down"
log "🔄 Para reiniciar: docker-compose restart"