#!/bin/bash

# Script de configuración para cron de tareas programadas
# Ejecutar este script para configurar el cron automáticamente

# Configuración
PROJECT_PATH="/Users/marlonfalcon/Documents/Projects/ticketproo"
PYTHON_ENV_PATH="/Users/marlonfalcon/micromamba/bin/python"
LOG_PATH="/Users/marlonfalcon/Documents/Projects/ticketproo/logs"

# Crear directorio de logs si no existe
mkdir -p "$LOG_PATH"

# Función para agregar entrada al cron
add_cron_entry() {
    local frequency="$1"
    local description="$2"
    
    echo "# $description"
    echo "$frequency cd $PROJECT_PATH && $PYTHON_ENV_PATH manage.py run_scheduled_tasks >> $LOG_PATH/scheduled_tasks.log 2>&1"
    echo ""
}

# Crear archivo de configuración de cron
cat > /tmp/ticketproo_cron << EOF
# ============================================
# TAREAS PROGRAMADAS - TICKETPROO
# ============================================
# Configuración automática para ejecutar tareas programadas
# Generado el $(date)

EOF

# Agregar diferentes frecuencias de ejecución
add_cron_entry "* * * * *" "Ejecutar cada minuto (para tareas de minutos)" >> /tmp/ticketproo_cron
add_cron_entry "0 * * * *" "Ejecutar cada hora (para tareas de horas)" >> /tmp/ticketproo_cron  
add_cron_entry "0 0 * * *" "Ejecutar cada día a medianoche (para tareas diarias)" >> /tmp/ticketproo_cron
add_cron_entry "0 0 1 * *" "Ejecutar el primer día de cada mes (para tareas mensuales)" >> /tmp/ticketproo_cron

# Agregar limpieza de logs
cat >> /tmp/ticketproo_cron << EOF
# ============================================
# LIMPIEZA DE LOGS
# ============================================
# Limpiar logs antiguos cada domingo a las 2 AM
0 2 * * 0 find $LOG_PATH -name "*.log" -mtime +30 -delete

# ============================================
# FIN CONFIGURACIÓN TICKETPROO
# ============================================
EOF

echo "============================================"
echo "CONFIGURACIÓN DE CRON PARA TAREAS PROGRAMADAS"
echo "============================================"
echo ""
echo "Se ha generado la configuración en: /tmp/ticketproo_cron"
echo ""
echo "Contenido generado:"
echo "-------------------"
cat /tmp/ticketproo_cron
echo ""
echo "============================================"
echo "OPCIONES DE INSTALACIÓN:"
echo "============================================"
echo ""
echo "1. INSTALACIÓN AUTOMÁTICA (recomendado):"
echo "   sudo bash -c 'cat /tmp/ticketproo_cron >> /etc/crontab'"
echo ""
echo "2. INSTALACIÓN MANUAL:"
echo "   a) Copiar el contenido de /tmp/ticketproo_cron"
echo "   b) Ejecutar: crontab -e"
echo "   c) Pegar el contenido al final del archivo"
echo ""
echo "3. VERIFICAR INSTALACIÓN:"
echo "   crontab -l | grep ticketproo"
echo ""
echo "============================================"
echo "COMANDOS ÚTILES:"
echo "============================================"
echo ""
echo "• Probar ejecución manual:"
echo "  cd $PROJECT_PATH && $PYTHON_ENV_PATH manage.py run_scheduled_tasks --verbose"
echo ""
echo "• Ejecutar en modo dry-run:"
echo "  cd $PROJECT_PATH && $PYTHON_ENV_PATH manage.py run_scheduled_tasks --dry-run --verbose"
echo ""
echo "• Ejecutar tarea específica:"
echo "  cd $PROJECT_PATH && $PYTHON_ENV_PATH manage.py run_scheduled_tasks --task-id=1 --verbose"
echo ""
echo "• Ver logs en tiempo real:"
echo "  tail -f $LOG_PATH/scheduled_tasks.log"
echo ""
echo "• Ver estado del cron:"
echo "  sudo service cron status"
echo ""
echo "============================================"

# Hacer el archivo ejecutable
chmod +x "$0"

echo "Configuración lista. Ejecuta uno de los comandos de instalación arriba."