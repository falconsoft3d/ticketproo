# TicketProo 🎫

**Sistema Profesional de Gestión de Tickets y Soporte Técnico**

TicketProo es una plataforma web moderna desarrollada en Django que permite gestionar tickets de soporte de manera eficiente, con roles diferenciados para agentes y usuarios.

## 🚀 Características Principales

### 👥 Sistema de Roles
- **Agentes**: Acceso completo a todos los tickets y gestión de usuarios
- **Usuarios**: Acceso solo a sus propios tickets

### 🎯 Funcionalidades Clave
- ✅ **Autoasignación de Tickets**: Los agentes pueden asignarse tickets automáticamente
- ✅ **Gestión de Adjuntos**: Subida, descarga y eliminación de archivos adjuntos
- ✅ **Dashboard Interactivo**: Estadísticas y métricas en tiempo real
- ✅ **Filtros Avanzados**: Por estado, prioridad, asignación y búsqueda de texto
- ✅ **Gestión de Usuarios**: Creación y administración de usuarios (solo agentes)
- ✅ **Interfaz Responsiva**: Diseño moderno con Bootstrap 5

### 🔧 Estados y Prioridades
**Estados de Ticket:**
- 🔵 Abierto
- 🟡 En Progreso  
- 🟢 Resuelto
- ⚫ Cerrado

**Niveles de Prioridad:**
- 🟢 Baja
- 🟡 Media
- 🔴 Alta
- ⚫ Urgente

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.2.6
- **Frontend**: Bootstrap 5 + Bootstrap Icons
- **Base de Datos**: SQLite (desarrollo)
- **Autenticación**: Sistema de usuarios de Django
- **Permisos**: Django Groups (Agentes/Usuarios)

## 📋 Requisitos

- Python 3.12+
- Django 5.2.6
- django-bootstrap5

## 🚀 Instalación y Configuración

1. **Clonar el repositorio**
```bash
git clone [url-del-repositorio]
cd demo_presupuesto_1
```

2. **Crear y activar entorno virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install django django-bootstrap5
```

4. **Configurar base de datos**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crear grupos de usuarios**
```bash
python manage.py setup_groups
```

6. **Crear superusuario**
```bash
python manage.py createsuperuser
```

7. **Asignar admin como agente**
```bash
python manage.py assign_admin_agent
```

8. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

## 👤 Usuarios de Prueba

### Superusuario (Admin/Agente)
- **Usuario**: admin
- **Contraseña**: [configurada durante setup]
- **Rol**: Agente (acceso completo)

## 📁 Estructura del Proyecto

```
demo_presupuesto_1/
├── manage.py
├── db.sqlite3
├── media/                      # Archivos subidos
├── static/                     # Archivos estáticos
├── templates/                  # Templates HTML
│   ├── base.html
│   ├── registration/
│   └── tickets/
├── ticket_system/              # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── tickets/                    # App principal
    ├── models.py              # Modelos de datos
    ├── views.py               # Lógica de vistas
    ├── forms.py               # Formularios
    ├── urls.py                # URLs de la app
    ├── admin.py               # Configuración admin
    ├── utils.py               # Funciones auxiliares
    └── management/commands/    # Comandos personalizados
```

## 🎛️ Panel de Administración

Accede al panel de administración en: `http://localhost:8000/admin/`

**Funcionalidades del Admin:**
- Gestión completa de tickets
- Administración de adjuntos
- Configuración de usuarios y grupos
- Estadísticas y reportes

## 🔒 Seguridad

- **Autenticación requerida**: Todas las vistas requieren login
- **Permisos por rol**: Acceso diferenciado según grupo
- **Validación de archivos**: Tipos y tamaños permitidos
- **Protección CSRF**: Tokens en todos los formularios

## 📊 Funcionalidades por Rol

### 🛡️ Agentes
- Ver todos los tickets del sistema
- Autoasignarse/desasignar tickets
- Crear, editar y eliminar cualquier ticket
- Gestionar usuarios (crear, editar, activar/desactivar)
- Acceso completo a adjuntos
- Dashboard con estadísticas globales

### 👤 Usuarios
- Ver solo sus propios tickets
- Crear nuevos tickets
- Editar sus tickets existentes
- Subir adjuntos a sus tickets
- Dashboard con estadísticas personales

## 📝 Comandos de Gestión Personalizados

### `setup_groups`
Crea automáticamente los grupos "Agentes" y "Usuarios" con sus permisos correspondientes.

```bash
python manage.py setup_groups
```

### `assign_admin_agent`
Asigna al usuario admin al grupo de Agentes.

```bash
python manage.py assign_admin_agent
```

## 🎨 Interfaz de Usuario

- **Diseño Responsivo**: Compatible con móviles y tablets
- **Tema Moderno**: Colores y tipografía profesional
- **Iconografía**: Bootstrap Icons para mejor UX
- **Navegación Intuitiva**: Menús contextuales según rol
- **Feedback Visual**: Alertas y notificaciones claras

## 📈 Próximas Características

- [x] Agregar Categorias de Tickets
- [x] Crear Secuencia de Tickets
- [x] Mensajes privados entre agentes y usuarios
- [x] Permitir compartir un ticket publico mediante un enlace unico.
- [ ] Permitir entrar al home agentes y usuarios logeados.
- [ ] Agregar paginacion a la lista de tickets
- [ ] Permitir actualizar el perfil de usuario
- [ ] Blog de noticias y actualizaciones
- [ ] Permitir comentarios en tickets
- [ ] Crear un api que permita gestionar los tickets
- [ ] Que el agente pueda registrar la hora de inicio y fin de atencion del trabajo, como el parte de horas.
- [ ] Permitir registrar notas internas asociada a usuarios y que sea visible solo para agentes y ese usuario. De esa forma dejamos por escrito nuestra interaccion con el cliente. ( Titulo y descripcion de la nota y Fecha de creacion)

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- 📧 Email: mfalconsoft@gmail.com
- 📱 Teléfono: +34-662-47-0645
- 🌐 Web: https://ticketproo.com

---

**TicketProo** - La plataforma profesional para gestionar tus solicitudes de soporte.
