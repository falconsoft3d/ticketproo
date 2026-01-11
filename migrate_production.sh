#!/bin/bash
# Script para aplicar migraciones en producción

echo "🚀 Aplicando migraciones en producción..."

# Activar virtualenv
source /home/urban/bin/activate

# Ir al directorio del proyecto
cd /home/urban/ticketproo

# Aplicar migraciones
echo "📦 Ejecutando migraciones..."
python manage.py migrate tickets

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Reiniciar servicios
echo "🔄 Reiniciando servicios..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "✅ Despliegue completado exitosamente!"
