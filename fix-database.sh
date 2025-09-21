#!/bin/bash

# Script para solucionar problemas de base de datos SQLite vs PostgreSQL
# Uso: ./fix-database.sh

echo "🗄️  Solucionando problemas de configuración de base de datos..."

echo "🛑 Deteniendo todos los servicios..."
docker-compose down

echo "🧹 Limpiando volúmenes y datos antiguos..."
# Limpiar volúmenes de base de datos
docker volume ls | grep ticketproo && docker volume rm $(docker volume ls | grep ticketproo | awk '{print $2}') 2>/dev/null || true

echo "🔧 Verificando configuración de base de datos..."

# Verificar si el settings.py está configurado para PostgreSQL
if ! grep -q "DATABASE_URL" ticket_system/settings.py; then
    echo "❌ Settings.py no configurado para PostgreSQL"
    echo "🔧 Aplicando configuración automática..."
    
    # Backup del settings original
    cp ticket_system/settings.py ticket_system/settings.py.backup
    
    # Crear configuración de base de datos
    cat >> ticket_system/settings.py << 'EOF'

# === CONFIGURACIÓN AUTOMÁTICA PARA DOCKER ===
import os

# Configuración de base de datos
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
    print("🐘 Usando PostgreSQL en Docker")
else:
    print("🗃️  Usando SQLite para desarrollo local")

# Configuración de entorno
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
EOF
    
    echo "✅ Configuración de base de datos aplicada"
else
    echo "✅ Configuración de base de datos ya presente"
fi

echo "🐘 Iniciando PostgreSQL..."
docker-compose up -d db

echo "⏳ Esperando que PostgreSQL esté completamente listo..."
sleep 20

# Verificar que PostgreSQL está funcionando
echo "🔍 Verificando conexión a PostgreSQL..."
if docker-compose exec db pg_isready -U postgres; then
    echo "✅ PostgreSQL está listo"
else
    echo "❌ Problema con PostgreSQL"
    docker-compose logs db
    exit 1
fi

echo "🔨 Reconstruyendo aplicación web..."
docker-compose build --no-cache web

echo "🚀 Iniciando aplicación web..."
docker-compose up -d web

echo "⏳ Esperando inicialización de Django..."
sleep 15

echo "📊 Estado de servicios:"
docker-compose ps

echo ""
echo "🔍 Verificando logs de la aplicación..."
docker-compose logs --tail=20 web

echo ""
echo "🧪 Probando conectividad..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302"; then
    echo "✅ Aplicación respondiendo correctamente"
else
    echo "⚠️  Aplicación no responde, verificar logs"
fi

echo ""
echo "✅ Configuración de base de datos completada!"
echo ""
echo "📝 Comandos útiles:"
echo "  Acceder a PostgreSQL: docker-compose exec db psql -U postgres -d ticketproo"
echo "  Ver tablas:           docker-compose exec web python manage.py dbshell"
echo "  Crear superusuario:   docker-compose exec web python manage.py createsuperuser"
echo "  Ver logs:             docker-compose logs -f web"