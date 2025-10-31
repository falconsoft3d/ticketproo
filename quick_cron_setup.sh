#!/bin/bash

# Script rápido para instalar cron de tareas programadas
# Ejecutar con: ./quick_cron_setup.sh

PROJECT_PATH="/Users/marlonfalcon/Documents/Projects/ticketproo"
PYTHON_PATH="/Users/marlonfalcon/micromamba/bin/python"

echo "Configurando cron para TicketProo..."

# Crear entrada de cron que ejecuta cada minuto
(crontab -l 2>/dev/null; echo "# TicketProo - Tareas Programadas (cada minuto)") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * cd $PROJECT_PATH && $PYTHON_PATH manage.py run_scheduled_tasks >/dev/null 2>&1") | crontab -

echo "¡Cron configurado exitosamente!"
echo ""
echo "Verificación:"
crontab -l | grep -A1 "TicketProo"
echo ""
echo "Para ver logs de ejecución:"
echo "tail -f $PROJECT_PATH/logs/scheduled_tasks.log"