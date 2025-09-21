#!/bin/bash

# Script rápido para solucionar errores comunes de Django en Docker
# Uso: ./fix-dependencies.sh

echo "🔧 Solucionando problemas de configuración Django..."

# Verificar si django-bootstrap5 está en requirements.txt
if ! grep -q "django-bootstrap5" requirements.txt; then
    echo "➕ Agregando django-bootstrap5 a requirements.txt..."
    # Agregar después de Django
    sed -i '2i django-bootstrap5==23.3' requirements.txt
    echo "✅ django-bootstrap5 agregado"
else
    echo "✅ django-bootstrap5 ya está en requirements.txt"
fi

# Verificar configuración de STATIC_ROOT en settings.py
if ! grep -q "STATIC_ROOT" ticket_system/settings.py; then
    echo "➕ Agregando STATIC_ROOT a settings.py..."
    # Buscar la línea STATIC_URL y agregar STATIC_ROOT después
    sed -i "/STATIC_URL = /a STATIC_ROOT = BASE_DIR / 'staticfiles'" ticket_system/settings.py
    echo "✅ STATIC_ROOT agregado"
else
    echo "✅ STATIC_ROOT ya está configurado"
fi

echo "🔨 Reconstruyendo imagen Docker..."
docker-compose build --no-cache web

echo "🧹 Limpiando contenedores anteriores..."
docker-compose down

echo "🚀 Iniciando servicios..."
docker-compose up -d

echo "⏳ Esperando que los servicios inicien..."
sleep 10

echo "📊 Verificando estado..."
docker-compose ps

echo ""
echo "📝 Para ver logs en tiempo real:"
echo "docker-compose logs -f web"
echo ""
echo "🌐 Para verificar la aplicación:"
echo "curl -I http://localhost"
echo ""
echo "✅ ¡Problemas solucionados!"