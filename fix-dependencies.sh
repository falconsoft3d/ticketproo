#!/bin/bash

# Script rápido para solucionar el error de django_bootstrap5
# Uso: ./fix-dependencies.sh

echo "🔧 Solucionando problema de dependencias..."

# Verificar si django-bootstrap5 está en requirements.txt
if ! grep -q "django-bootstrap5" requirements.txt; then
    echo "➕ Agregando django-bootstrap5 a requirements.txt..."
    # Agregar después de Django
    sed -i '2i django-bootstrap5==23.3' requirements.txt
    echo "✅ django-bootstrap5 agregado"
else
    echo "✅ django-bootstrap5 ya está en requirements.txt"
fi

echo "🔨 Reconstruyendo imagen Docker..."
docker-compose build --no-cache web

echo "🚀 Reiniciando servicios..."
docker-compose restart web

echo "📊 Verificando estado..."
sleep 5
docker-compose ps

echo "📝 Ver logs:"
echo "docker-compose logs web"

echo "✅ ¡Dependencias solucionadas!"