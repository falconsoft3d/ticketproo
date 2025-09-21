#!/bin/bash

# Script de entrada simplificado para debug

echo "=== TicketProo Entrypoint (Debug) ==="

# Verificar permisos
whoami
id

# Crear directorios básicos
mkdir -p /app/staticfiles /app/media /app/logs

# Esperar PostgreSQL
echo "Esperando PostgreSQL..."
while ! nc -z db 5432; do
    sleep 1
done
echo "PostgreSQL listo!"

# Ejecutar migraciones básicas
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Archivos estáticos
echo "Archivos estáticos..."
python manage.py collectstatic --noinput

echo "=== Iniciando aplicación ==="
exec "$@"