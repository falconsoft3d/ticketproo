#!/bin/bash

# Script para solucionar problemas de archivos estáticos en Django
# Uso: ./fix-static-files.sh

echo "📁 Solucionando problemas de archivos estáticos..."

# Paso 1: Verificar configuración actual
echo "🔍 Verificando configuración actual..."
if docker-compose ps | grep -q "web.*Up"; then
    echo "✅ Servicio web está corriendo"
else
    echo "❌ Servicio web no está corriendo, iniciando..."
    docker-compose up -d db web
    sleep 5
fi

# Paso 2: Crear directorios necesarios
echo "📂 Creando directorios de archivos estáticos..."
docker-compose exec web mkdir -p /app/staticfiles
docker-compose exec web mkdir -p /app/media
docker-compose exec web mkdir -p /app/static

# Paso 3: Verificar permisos
echo "🔒 Verificando permisos..."
docker-compose exec web chown -R appuser:appuser /app/staticfiles
docker-compose exec web chown -R appuser:appuser /app/media

# Paso 4: Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
docker-compose exec web python manage.py collectstatic --noinput --clear

# Paso 5: Verificar que los archivos se crearon
echo "✅ Verificando archivos estáticos creados..."
docker-compose exec web ls -la /app/staticfiles/

# Paso 6: Reiniciar nginx si está corriendo
if docker-compose ps | grep -q "nginx.*Up"; then
    echo "🔄 Reiniciando nginx..."
    docker-compose restart nginx
fi

echo ""
echo "✅ Archivos estáticos configurados correctamente!"
echo ""
echo "📝 Para verificar:"
echo "docker-compose exec web ls -la /app/staticfiles/"
echo "docker-compose logs web"