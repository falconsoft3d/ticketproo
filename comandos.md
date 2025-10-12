# para el server
```
crontab -e
# Añadir esta línea:
0 10 * * * cd /ruta/a/tu/proyecto && python manage.py run_ai_blog_generators
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