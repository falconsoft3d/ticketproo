# para el server
```
source .venv/bin/activate
python manage.py runserver 8000
lsof -ti:8000
kill -9 71529 80202
lsof -ti:8000 | xargs kill -9
```

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