# Sistema de Tareas Programadas - TicketProo

## 📋 Descripción
Sistema completo de automatización que permite ejecutar código Python de forma programada usando cron del servidor.

## 🚀 Configuración del Cron

### Opción 1: Configuración Rápida (Recomendada)
```bash
cd /Users/marlonfalcon/Documents/Projects/ticketproo
./quick_cron_setup.sh
```

### Opción 2: Configuración Personalizada
```bash
cd /Users/marlonfalcon/Documents/Projects/ticketproo
./setup_cron.sh
```

### Opción 3: Configuración Manual
1. Abrir crontab: `crontab -e`
2. Agregar la línea:
```bash
* * * * * cd /Users/marlonfalcon/Documents/Projects/ticketproo && /Users/marlonfalcon/micromamba/bin/python manage.py run_scheduled_tasks >/dev/null 2>&1
```

## 🔧 Comandos de Management

### Ejecutar Todas las Tareas Pendientes
```bash
python manage.py run_scheduled_tasks
```

### Ejecutar con Información Detallada
```bash
python manage.py run_scheduled_tasks --verbose
```

### Modo Dry-Run (Ver qué se ejecutaría)
```bash
python manage.py run_scheduled_tasks --dry-run --verbose
```

### Ejecutar Tarea Específica
```bash
python manage.py run_scheduled_tasks --task-id=1 --verbose
```

### Ver Ayuda Completa
```bash
python manage.py run_scheduled_tasks --help
```

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real
```bash
tail -f /Users/marlonfalcon/Documents/Projects/ticketproo/logs/scheduled_tasks.log
```

### Ver Estado del Cron
```bash
crontab -l | grep TicketProo
```

### Verificar que Cron está Ejecutándose
```bash
sudo service cron status  # Linux
sudo launchctl list | grep cron  # macOS
```

## 🎯 Frecuencias de Ejecución

El sistema verifica cada minuto qué tareas deben ejecutarse según su configuración:

- **Minutos**: Se ejecutan cuando han pasado N minutos desde la última ejecución
- **Horas**: Se ejecutan cuando han pasado N horas desde la última ejecución  
- **Días**: Se ejecutan cuando han pasado N días desde la última ejecución
- **Meses**: Se ejecutan cuando han pasado N meses (aprox. 30 días) desde la última ejecución

## 💻 Variables Disponibles en el Código

Cuando escribas código en las tareas programadas, tienes acceso a:

```python
# Módulos de fecha y tiempo
timezone.now()          # Fecha/hora actual
datetime.datetime       # Clase datetime
timedelta(days=1)       # Diferencias de tiempo

# Modelos de Django más comunes
User.objects.all()      # Usuarios
Ticket.objects.all()    # Tickets
Contact.objects.all()   # Contactos
Company.objects.all()   # Empresas

# Logging
logger.info("mensaje")  # Para escribir logs
print("mensaje")        # También funciona

# Ejemplo de código:
current_time = timezone.now()
total_users = User.objects.count()
print(f"Reporte automático - Usuarios: {total_users} - Hora: {current_time}")
```

## 🔍 Ejemplo de Tarea

### Crear Tarea de Reporte Diario
1. Ir a: **CG → Tareas Programadas → Nueva Tarea**
2. Configurar:
   - **Nombre**: "Reporte Diario de Usuarios"
   - **Frecuencia**: 1
   - **Unidad**: Día
   - **Código**:
   ```python
   # Reporte diario automático
   from datetime import datetime
   
   total_users = User.objects.count()
   new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
   
   print(f"=== REPORTE DIARIO {timezone.now().strftime('%d/%m/%Y')} ===")
   print(f"Total usuarios: {total_users}")
   print(f"Nuevos usuarios hoy: {new_users_today}")
   print("===============================================")
   ```

## ⚠️ Consideraciones Importantes

### Rendimiento
- El cron ejecuta cada minuto, pero solo procesa tareas que realmente deben ejecutarse
- Las tareas inactivas no se procesan
- El sistema registra tiempo de ejecución para monitoreo

### Seguridad
- El código se ejecuta en un entorno controlado
- Solo se importan módulos seguros por defecto
- Los errores se capturan y registran sin afectar el sistema

### Logs y Depuración
- Todas las ejecuciones se registran en la base de datos
- Los errores se guardan para análisis posterior
- Los logs del cron se guardan en `logs/scheduled_tasks.log`

## 🛠️ Solución de Problemas

### El Cron No Ejecuta
1. Verificar que el cron está activo: `crontab -l`
2. Revisar permisos del script
3. Verificar rutas en la configuración
4. Comprobar logs: `tail -f logs/scheduled_tasks.log`

### Errores en las Tareas
1. Usar `--dry-run` para probar sin ejecutar
2. Ejecutar manualmente con `--verbose`
3. Revisar el historial en la interfaz web
4. Verificar sintaxis del código Python

### Tareas No Se Ejecutan a Tiempo
1. Verificar que la tarea está **Activa**
2. Comprobar la frecuencia configurada
3. Revisar la **fecha de última ejecución**
4. Usar `--verbose` para debug

## 📈 Mejores Prácticas

### Código Eficiente
- Mantén las tareas simples y rápidas
- Usa `try/except` para manejar errores
- Incluye mensajes informativos con `print()`

### Frecuencias Inteligentes
- **Cada minuto**: Solo para verificaciones críticas
- **Cada hora**: Para reportes y limpieza ligera
- **Diario**: Para procesos de mantenimiento
- **Mensual**: Para archivado y análisis extenso

### Monitoreo
- Revisa regularmente las estadísticas de éxito/error
- Mantén los logs limpios
- Desactiva tareas obsoletas

## 🚀 Sistema en Producción

Para usar en producción, asegúrate de:
1. Configurar el cron en el servidor
2. Ajustar las rutas en los scripts
3. Configurar rotación de logs
4. Monitorear rendimiento del servidor
5. Hacer respaldos de las tareas importantes