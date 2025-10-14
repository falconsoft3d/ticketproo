# para el server
```
# CONFIGURACIÓN DEL CRON JOB EN PRODUCCIÓN
# 1. Editar el crontab del usuario
crontab -e

# 2. Añadir esta línea para ejecutar todos los días a las 10:00 AM:
0 10 * * * cd /home/urban/ticketproo && source /home/urban/bin/activate && python manage.py run_ai_blog_generators >> /home/urban/logs/ai_blog_cron.log 2>&1

# 3. OPCIONES ADICIONALES DE HORARIOS:
# Ejecutar cada 6 horas:
# 0 */6 * * * cd /home/urban/ticketproo && source /home/urban/bin/activate && python manage.py run_ai_blog_generators >> /home/urban/logs/ai_blog_cron.log 2>&1

# Ejecutar todos los días a las 8:00 AM y 6:00 PM:
# 0 8,18 * * * cd /home/urban/ticketproo && source /home/urban/bin/activate && python manage.py run_ai_blog_generators >> /home/urban/logs/ai_blog_cron.log 2>&1

# Ejecutar solo de lunes a viernes a las 9:00 AM:
# 0 9 * * 1-5 cd /home/urban/ticketproo && source /home/urban/bin/activate && python manage.py run_ai_blog_generators >> /home/urban/logs/ai_blog_cron.log 2>&1

# 4. Verificar que el cron está configurado:
crontab -l

# 5. Para revisar los logs del cron:
tail -f /home/urban/logs/ai_blog_cron.log

# 6. Crear el directorio de logs si no existe:
mkdir -p /home/urban/logs

# 7. Comandos de monitoreo:
# Ver errores específicos:
grep -i error /home/urban/logs/ai_blog_cron.log
# Ver ejecuciones exitosas:
grep -i "Ejecución completada" /home/urban/logs/ai_blog_cron.log
# Ver últimas 50 líneas:
tail -50 /home/urban/logs/ai_blog_cron.log

# COMANDOS LOCALES DE DESARROLLO:
source .venv/bin/activate
python manage.py runserver 8000
lsof -ti:8000
kill -9 71529 80202
lsof -ti:8000 | xargs kill -9

# Comandos del generador de blogs con IA
python manage.py run_ai_blog_generators --force  # Ejecutar manualmente todos los configuradores
python manage.py run_ai_blog_generators --configurator-id=1 --force  # Ejecutar configurador específico
python manage.py run_ai_blog_generators --dry-run  # Ver qué se ejecutaría sin ejecutar
python manage.py run_ai_blog_generators  # Ejecutar solo los que están programados

# COMANDOS DE ACCIONES FINANCIERAS CON API EXTERNA
# Actualizar todas las acciones financieras desde APIs externas
python manage.py update_financial_prices

# Actualizar una acción específica
python manage.py update_financial_prices --symbol EUR/USD
python manage.py update_financial_prices --symbol AAPL
python manage.py update_financial_prices --symbol BTC/USD

# Forzar actualización incluso si fue actualizada recientemente
python manage.py update_financial_prices --force

# AUTOMATIZACIÓN DE ACTUALIZACIONES (CRON):
# Actualizar precios cada 15 minutos en horario de mercado (9 AM - 6 PM)
# */15 9-18 * * 1-5 cd /home/urban/ticketproo && source /home/urban/bin/activate && python manage.py update_financial_prices >> /home/urban/logs/financial_updates.log 2>&1

# Actualizar precios cada hora fuera del horario de mercado
# 0 */1 * * * cd /home/urban/ticketproo && source /home/urban/bin/activate && python manage.py update_financial_prices >> /home/urban/logs/financial_updates.log 2>&1

# TIPOS DE ACTIVOS SOPORTADOS:
# - Divisas (Forex): EUR/USD, GBP/USD, USD/JPY, etc.
# - Acciones: AAPL, GOOGL, MSFT, TSLA, etc.
# - Criptomonedas: BTC/USD, ETH/USD, etc.

# APIS UTILIZADAS:
# - Divisas: exchangerate-api.com (gratuita)
# - Acciones: Yahoo Finance API (gratuita)
# - Criptomonedas: CoinGecko API (gratuita)

# Verificar posts generados y evitar duplicados
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()
from tickets.models import BlogPost
posts = BlogPost.objects.order_by('-id')[:10]
print('=== ÚLTIMOS POSTS GENERADOS ===')
for post in posts:
    print(f'ID: {post.id} - \"{post.title}\" - {post.created_at.strftime(\"%d/%m/%Y %H:%M\")}')
"

# Ejecución desde interfaz web:
# - Ir a /ai-blog-configurators/
# - Hacer clic en "Ejecutar Ahora" (ignora frecuencia programada)
# - Ver logs en "Ver Logs" para revisar resultados
# - También disponible botón "Ejecutar Ahora" en la página de logs
# - NUEVO: Sistema evita títulos duplicados automáticamente usando IA
```

## 🚀 Proyecto de Código Abierto

### TicketProo - Sistema de Gestión Empresarial
**TicketProo** es un sistema completo de gestión empresarial desarrollado en Django, diseñado para modernizar y automatizar los procesos de soporte, recursos humanos, capacitación y administración de empresas.

### 📋 Información del Repositorio
- **URL del Repositorio**: [https://github.com/falconsoft3d/ticketproo](https://github.com/falconsoft3d/ticketproo)
- **Licencia**: Código Abierto (Open Source)
- **Tecnología**: Django 4.2.20 + Python 3.9+
- **Base de Datos**: SQLite / PostgreSQL / MySQL
- **Frontend**: Bootstrap 5 + JavaScript

### 🔧 Comandos Git Útiles
```bash
# Clonar el repositorio
git clone https://github.com/falconsoft3d/ticketproo.git

# Actualizar desde el repositorio remoto
git pull origin main

# Ver estado de cambios
git status

# Agregar cambios
git add .

# Crear commit
git commit -m "Descripción de cambios"

# Subir cambios
git push origin main
```

### 🌟 Características del Proyecto
- ✅ **100% Código Abierto**: Libre para usar, modificar y distribuir
- ✅ **Modular**: Arquitectura por módulos independientes
- ✅ **Escalable**: Diseñado para crecer con tu empresa
- ✅ **Responsive**: Interfaz adaptativa para móviles y desktop
- ✅ **API REST**: Integración con sistemas externos
- ✅ **Seguridad**: Autenticación robusta y permisos granulares

### 🤝 Contribuir al Proyecto
```bash
# Fork del repositorio en GitHub
# Crear rama para nueva funcionalidad
git checkout -b feature/nueva-funcionalidad

# Desarrollar y hacer commits
git commit -m "feat: nueva funcionalidad implementada"

# Push de la rama
git push origin feature/nueva-funcionalidad

# Crear Pull Request en GitHub
```

### 📞 Soporte y Comunidad
- **Issues**: [GitHub Issues](https://github.com/falconsoft3d/ticketproo/issues)
- **Documentación**: [Wiki del Proyecto](https://github.com/falconsoft3d/ticketproo/wiki)
- **Desarrollador**: [@falconsoft3d](https://github.com/falconsoft3d)

---

## Funcionalidades Implementadas

### Sistema de Roles
- **Agentes**: Gestión completa del sistema
- **Profesores**: Gestión de cursos y exámenes (crear, editar, eliminar)
- **Usuarios Regulares**: Acceso a cursos y exámenes públicos (solo lectura)

### URLs Públicas para Cursos
- Generar tokens de registro público para cursos
- Configurar límites de tiempo y cantidad de registros
- Formularios de registro optimizados para móvil
- QR codes para compartir fácilmente

### URLs Públicas para Documentos
- Subida de fotos desde móviles sin autenticación
- Sistema de tokens con expiración y límites de uso
- Interfaz optimizada para cámara móvil

### Acceso al Menú Capacitación
- **TODOS** los usuarios autenticados ven el menú "Capacitación"
- Usuarios regulares pueden ver y tomar cursos/exámenes
- Solo Agentes y Profesores ven opciones de gestión (crear, editar)
- Permisos granulares por tipo de usuario

## Forma de actualizar
```
source ~/bin/activate
cd ticketproo

python manage.py makemigrations
python manage.py migrate
python manage.py manage_roles setup
python manage.py setup_groups

cp ~/ticketproo/ticket_system/settings.py ~/old_settings.py
cp ~/old_settings.py ~/ticketproo/ticket_system/settings.py

sudo systemctl daemon-reload
sudo systemctl restart urban-train
sudo systemctl status urban-train

python manage.py runserver 0.0.0.0:8000
```

## Comandos de Gestión de Roles
```
# Listar usuarios por rol
python manage.py manage_roles list

# Asignar rol profesor a un usuario
python manage.py manage_roles assign <username> profesor

# Asignar rol agente a un usuario
python manage.py manage_roles assign <username> agente
```


```
python manage.py shell
from tickets.models import Agreement
agreements = Agreement.objects.all()
for a in agreements: print(f'ID: {a.id}, Título: {a.title}, Estado: {a.status}, Token: {a.public_token}')
```