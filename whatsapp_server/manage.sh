#!/bin/bash

# Script de gestión del servidor WhatsApp con Docker
# Uso: ./manage.sh [comando]

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funciones
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${NC}ℹ $1${NC}"
}

# Verificar si Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado"
        exit 1
    fi
    
    print_success "Docker y Docker Compose están instalados"
}

# Comandos
cmd_build() {
    print_info "Construyendo imagen Docker..."
    docker-compose build
    print_success "Imagen construida exitosamente"
}

cmd_start() {
    print_info "Iniciando contenedor WhatsApp..."
    docker-compose up -d
    print_success "Contenedor iniciado"
    print_info "Ver logs con: ./manage.sh logs"
}

cmd_stop() {
    print_info "Deteniendo contenedor WhatsApp..."
    docker-compose down
    print_success "Contenedor detenido"
}

cmd_restart() {
    print_info "Reiniciando contenedor WhatsApp..."
    docker-compose restart
    print_success "Contenedor reiniciado"
}

cmd_logs() {
    print_info "Mostrando logs (Ctrl+C para salir)..."
    docker-compose logs -f
}

cmd_status() {
    print_info "Estado del contenedor:"
    docker-compose ps
}

cmd_shell() {
    print_info "Accediendo al shell del contenedor..."
    docker-compose exec whatsapp-server bash
}

cmd_rebuild() {
    print_info "Reconstruyendo e iniciando contenedor..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    print_success "Contenedor reconstruido e iniciado"
}

cmd_clean() {
    print_warning "¿Estás seguro de que quieres eliminar todo (contenedor, volúmenes, imágenes)? (s/n)"
    read -r response
    if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
        print_info "Limpiando..."
        docker-compose down -v
        docker rmi ticketproo-whatsapp 2>/dev/null || true
        print_success "Limpieza completada"
    else
        print_info "Operación cancelada"
    fi
}

cmd_stats() {
    print_info "Uso de recursos del contenedor:"
    docker stats ticketproo-whatsapp --no-stream
}

cmd_help() {
    cat << EOF
Gestión del Servidor WhatsApp con Docker

Uso: ./manage.sh [comando]

Comandos disponibles:
  build       Construir la imagen Docker
  start       Iniciar el contenedor
  stop        Detener el contenedor
  restart     Reiniciar el contenedor
  logs        Ver logs en tiempo real
  status      Ver estado del contenedor
  shell       Acceder al shell del contenedor
  rebuild     Reconstruir e iniciar (limpia caché)
  clean       Eliminar contenedor, volúmenes e imágenes
  stats       Ver uso de recursos
  help        Mostrar esta ayuda

Ejemplos:
  ./manage.sh start
  ./manage.sh logs
  ./manage.sh status

EOF
}

# Script principal
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            cmd_build
            ;;
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        logs)
            cmd_logs
            ;;
        status)
            cmd_status
            ;;
        shell|bash)
            cmd_shell
            ;;
        rebuild)
            cmd_rebuild
            ;;
        clean)
            cmd_clean
            ;;
        stats)
            cmd_stats
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Comando desconocido: $1"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
