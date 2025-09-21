#!/bin/bash

# Script para aplicar fix rápido en el servidor

echo "🔧 Aplicando fix rápido para el deployment..."

# Detener servicios
echo "Deteniendo servicios..."
docker-compose down

# Reconstruir imagen web
echo "Reconstruyendo imagen web..."
docker-compose build web

# Reiniciar servicios
echo "Iniciando servicios..."
docker-compose up -d db
sleep 10
docker-compose up -d web

echo "✅ Fix aplicado! Verifica los logs con: docker-compose logs web"