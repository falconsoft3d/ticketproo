#!/bin/bash

# Script completo para solucionar errores de configuración Django en Docker
# Uso: ./fix-dependencies.sh

echo "🔧 Solucionando problemas de configuración Django + Docker + PostgreSQL..."

# Verificar si django-bootstrap5 está en requirements.txt
if ! grep -q "django-bootstrap5" requirements.txt; then
    echo "➕ Agregando django-bootstrap5 a requirements.txt..."
    sed -i '2i django-bootstrap5==23.3' requirements.txt
    echo "✅ django-bootstrap5 agregado"
else
    echo "✅ django-bootstrap5 ya está en requirements.txt"
fi

# Verificar configuración de STATIC_ROOT en settings.py
if ! grep -q "STATIC_ROOT" ticket_system/settings.py; then
    echo "➕ Agregando STATIC_ROOT a settings.py..."
    sed -i "/STATIC_URL = /a STATIC_ROOT = BASE_DIR / 'staticfiles'" ticket_system/settings.py
    echo "✅ STATIC_ROOT agregado"
else
    echo "✅ STATIC_ROOT ya está configurado"
fi

# Verificar si está usando configuración de entorno para base de datos
if ! grep -q "DATABASE_URL" ticket_system/settings.py; then
    echo "⚠️  Settings.py no está configurado para usar variables de entorno"
    echo "📝 Aplicando parche temporal..."
    
    # Crear un archivo de configuración temporal
    cat > docker_settings_patch.py << 'EOF'
import os
import dj_database_url

# Aplicar configuración de base de datos para Docker
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }

# Aplicar configuración de DEBUG y SECRET_KEY
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-&d)wf7xgiy_qchk2@%btib2lwdj*)n6(6u98@r&+eqr0scvtp=')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

print(f"🔧 Configuración Docker aplicada - DEBUG: {DEBUG}, DB: {DATABASE_URL is not None}")
EOF
    
    # Agregar el parche al final del settings.py
    echo "" >> ticket_system/settings.py
    echo "# === CONFIGURACIÓN DOCKER AUTOMÁTICA ===" >> ticket_system/settings.py
    cat docker_settings_patch.py >> ticket_system/settings.py
    rm docker_settings_patch.py
    
    echo "✅ Configuración Docker aplicada"
else
    echo "✅ Configuración de base de datos ya está lista"
fi

echo "🛑 Deteniendo servicios existentes..."
docker-compose down

echo "🧹 Limpiando volúmenes de base de datos SQLite conflictivos..."
docker volume ls | grep sqlite && docker volume prune -f || echo "No hay volúmenes SQLite"

echo "🔨 Reconstruyendo imagen Docker..."
docker-compose build --no-cache web

echo "�️  Iniciando PostgreSQL..."
docker-compose up -d db

echo "⏳ Esperando que PostgreSQL esté listo..."
sleep 15

echo "🚀 Iniciando aplicación web..."
docker-compose up -d web

echo "⏳ Esperando que Django inicialice..."
sleep 10

echo "🌐 Iniciando nginx..."
docker-compose up -d nginx

echo "📊 Verificando estado de servicios..."
docker-compose ps

echo ""
echo "� Verificando logs de la aplicación..."
echo "$(docker-compose logs --tail=10 web)"

echo ""
echo "✅ ¡Configuración completada!"
echo ""
echo "📝 Comandos útiles:"
echo "  Ver logs:     docker-compose logs -f web"
echo "  Ver estado:   docker-compose ps"
echo "  Acceder app:  curl -I http://localhost"
echo "  Shell Django: docker-compose exec web python manage.py shell"
echo ""
echo "🌐 Tu aplicación debería estar disponible en:"
echo "  http://localhost"
echo "  http://$(curl -s ifconfig.me 2>/dev/null || echo 'tu-ip-publica')"