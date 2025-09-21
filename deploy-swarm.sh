#!/bin/bash

# 🚀 TicketProo - One Click Deploy
# Deploy profesional con Ansible + Docker Swarm + Traefik

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${PURPLE}[SUCCESS]${NC} $1"; }

# Banner
echo -e "${BLUE}"
cat << 'EOF'
╔══════════════════════════════════════════════════════╗
║                                                      ║
║              🚀 TicketProo Swarm Deploy             ║
║                                                      ║
║    Professional deployment with:                     ║
║    ✅ Docker Swarm (High Availability)              ║
║    ✅ Traefik (Auto SSL + Load Balancing)           ║
║    ✅ Ansible (Infrastructure as Code)              ║
║    ✅ PostgreSQL (Clustered Database)               ║
║    ✅ Redis (Cache + Sessions)                      ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar requisitos
log "Verificando requisitos..."

if ! command -v ansible-playbook &> /dev/null; then
    error "Ansible no está instalado."
    info "Instalar con: pip install ansible"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    error "Docker no está instalado."
    info "Instalar desde: https://docs.docker.com/get-docker/"
    exit 1
fi

log "✓ Todos los requisitos están instalados"

# Configuración interactiva
echo ""
info "=== CONFIGURACIÓN DE DEPLOYMENT ==="

# Verificar si existe inventario
if [ ! -f "ansible/inventory/hosts.yml" ]; then
    error "Archivo de inventario no encontrado: ansible/inventory/hosts.yml"
    exit 1
fi

# Leer configuración del inventario
DOMAIN=$(grep "domain_name:" ansible/inventory/hosts.yml | awk '{print $2}' || echo "")
SERVER_IP=$(grep "ansible_host:" ansible/inventory/hosts.yml | awk '{print $2}' || echo "")

if [ -z "$DOMAIN" ] || [ -z "$SERVER_IP" ]; then
    warn "Configuración incompleta en hosts.yml"
    read -p "Ingresa tu dominio (ej: ticketproo.com): " DOMAIN
    read -p "Ingresa IP del servidor: " SERVER_IP
    read -p "Ingresa tu email para SSL: " EMAIL
    
    # Actualizar inventario
    sed -i.bak "s/domain_name:.*/domain_name: $DOMAIN/" ansible/inventory/hosts.yml
    sed -i.bak "s/ansible_host:.*/ansible_host: $SERVER_IP/" ansible/inventory/hosts.yml
    sed -i.bak "s/email:.*/email: $EMAIL/" ansible/inventory/hosts.yml
fi

log "Configuración:"
log "  🌐 Dominio: $DOMAIN"
log "  🖥️  Servidor: $SERVER_IP"

# Verificar conectividad
echo ""
log "Verificando conectividad con el servidor..."
if ! ansible ticketproo -i ansible/inventory/hosts.yml -m ping; then
    error "No se puede conectar al servidor. Verifica:"
    error "  1. IP del servidor correcta"
    error "  2. SSH key configurada"
    error "  3. Usuario root tiene acceso"
    exit 1
fi

success "✓ Conectividad con servidor OK"

# Verificar DNS
echo ""
log "Verificando configuración DNS..."
RESOLVED_IP=$(nslookup $DOMAIN | grep "Address" | tail -1 | awk '{print $2}' || echo "")
if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
    warn "⚠️  DNS no apunta al servidor correcto"
    warn "   Dominio $DOMAIN resuelve a: $RESOLVED_IP"
    warn "   Debería resolver a: $SERVER_IP"
    echo ""
    read -p "¿Continuar de cualquier manera? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Configura tu DNS primero:"
        info "  1. Crear registro A: $DOMAIN -> $SERVER_IP"
        info "  2. Crear registro A: www.$DOMAIN -> $SERVER_IP"
        info "  3. Esperar propagación (5-60 min)"
        exit 1
    fi
else
    success "✓ DNS configurado correctamente"
fi

# Menú de opciones
echo ""
info "=== OPCIONES DE DEPLOYMENT ==="
echo "1) 🚀 Deploy completo (Recomendado)"
echo "2) 🔧 Solo setup inicial del servidor"
echo "3) 📊 Deploy solo TicketProo (servidor ya configurado)"
echo "4) 🔍 Verificar estado actual"
echo "5) 📋 Ver logs de servicios"
echo ""
read -p "Selecciona una opción (1-5): " OPTION

case $OPTION in
    1)
        log "🚀 Iniciando deployment completo..."
        
        log "📦 Paso 1: Configurando servidor..."
        ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-ticketproo.yml --tags "setup"
        
        log "🐳 Paso 2: Deploying aplicación..."
        ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-ticketproo.yml
        
        success "🎉 ¡Deployment completo exitoso!"
        ;;
        
    2)
        log "🔧 Configurando servidor..."
        ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-ticketproo.yml --tags "setup"
        success "✓ Servidor configurado"
        ;;
        
    3)
        log "📊 Deploying solo aplicación..."
        ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-ticketproo.yml --skip-tags "setup"
        success "✓ Aplicación deployada"
        ;;
        
    4)
        log "🔍 Verificando estado..."
        ansible ticketproo -i ansible/inventory/hosts.yml -a "docker stack ls"
        ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service ls"
        ;;
        
    5)
        log "📋 Mostrando logs..."
        echo "Selecciona servicio:"
        echo "1) TicketProo Web"
        echo "2) Traefik"
        echo "3) PostgreSQL"
        echo "4) Redis"
        read -p "Opción: " SERVICE_OPTION
        
        case $SERVICE_OPTION in
            1) SERVICE="ticketproo_web" ;;
            2) SERVICE="traefik_traefik" ;;
            3) SERVICE="ticketproo_db" ;;
            4) SERVICE="ticketproo_redis" ;;
            *) SERVICE="ticketproo_web" ;;
        esac
        
        ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service logs $SERVICE --tail 50"
        ;;
        
    *)
        error "Opción inválida"
        exit 1
        ;;
esac

# Post-deployment info
echo ""
success "=== INFORMACIÓN DEL DEPLOYMENT ==="
success "🌐 Aplicación: https://$DOMAIN"
success "📊 Traefik Dashboard: https://traefik.$DOMAIN"
success "🔧 Comandos útiles:"
echo "   • Ver servicios: ansible ticketproo -i ansible/inventory/hosts.yml -a 'docker stack ls'"
echo "   • Ver logs: ansible ticketproo -i ansible/inventory/hosts.yml -a 'docker service logs ticketproo_web'"
echo "   • Escalar servicios: ansible ticketproo -i ansible/inventory/hosts.yml -a 'docker service scale ticketproo_web=5'"
echo "   • Rolling update: ansible ticketproo -i ansible/inventory/hosts.yml -a 'docker service update --image ticketproo:latest ticketproo_web'"

echo ""
success "🎊 ¡TicketProo está corriendo en producción!"
log "⏰ El deployment puede tomar 2-5 minutos en estar completamente listo"
log "🔒 Los certificados SSL se generarán automáticamente"