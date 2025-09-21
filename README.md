# TicketProo 🎫

**Sistema Profesional de Gestión de Tickets, Soporte Técnico y Control Empresarial**

TicketProo es una plataforma web moderna desarrollada en Django que permite gestionar tickets de soporte de manera eficiente, con control de tiempo de trabajo, gestión empresarial y análisis financiero de proyectos.

## 🚀 Características Principales

### 👥 Sistema de Roles
- **Agentes**: Acceso completo a todos los tickets, gestión de usuarios y control empresarial
- **Usuarios**: Acceso solo a sus propios tickets y funcionalidades básicas

### 🎯 Funcionalidades Clave
- ✅ **Gestión Empresarial**: Sistema completo de empresas y usuarios asociados
- ✅ **Control de Horario**: Registro de entrada, salida y tiempo de trabajo por proyecto
- ✅ **Gestión de Proyectos**: Creación y seguimiento de proyectos con análisis financiero
- ✅ **Sistema de Precios**: Precio y coste por hora por empleado
- ✅ **Análisis Financiero**: Cálculo automático de costes, ventas, beneficios y márgenes
- ✅ **Autoasignación de Tickets**: Los agentes pueden asignarse tickets automáticamente
- ✅ **Gestión de Adjuntos**: Subida, descarga y eliminación de archivos adjuntos
- ✅ **Dashboard Interactivo**: Estadísticas y métricas en tiempo real con diseño minimalista
- ✅ **Filtros Avanzados**: Por estado, prioridad, asignación y búsqueda de texto
- ✅ **Gestión de Usuarios**: Creación y administración de usuarios (solo agentes)
- ✅ **Panel de Configuración**: Configuración general del sistema
- ✅ **Interfaz Responsiva**: Diseño moderno minimalista en blanco y negro

### 🏢 Gestión Empresarial
- **Empresas**: Registro completo con datos de contacto y estado
- **Usuarios por Empresa**: Asociación de usuarios a empresas específicas
- **Tickets por Empresa**: Filtrado y gestión por empresa
- **Estadísticas Empresariales**: Métricas por empresa

### ⏰ Control de Tiempo de Trabajo
- **Registro de Jornadas**: Inicio y fin de jornada laboral
- **Control por Proyecto**: Asignación de tiempo trabajado a proyectos específicos
- **Historial de Asistencia**: Registro completo de todas las jornadas
- **Cálculos Automáticos**: Duración de jornadas y tiempo total trabajado
- **Vista de Supervisión**: Control de asistencia de todos los empleados

### 📊 Proyectos y Análisis Financiero
- **Gestión de Proyectos**: Creación, edición y seguimiento de proyectos
- **Tiempo por Proyecto**: Registro de horas trabajadas en cada proyecto
- **Análisis de Costes**: Cálculo automático basado en coste/hora por empleado
- **Análisis de Ventas**: Cálculo de ingresos basado en precio/hora por empleado
- **Cálculo de Beneficios**: Diferencia entre ventas y costes
- **Margen de Beneficio**: Porcentaje de margen sobre las ventas
- **Vista de Tabla**: Listado en formato tabla con totales automáticos

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

**Estados de Proyecto:**
- 🟢 Activo
- 🟡 En Pausa
- 🔴 Finalizado

## 🗃️ Modelos de Datos Principales

### Company (Empresa)
- Información básica: nombre, descripción, email, teléfono
- Dirección completa
- Estado activo/inactivo
- Fecha de creación y actualización

### UserProfile (Perfil de Usuario)
- Extensión del modelo User de Django
- Asociación a empresa
- Precio por hora (para cálculo de ventas)
- Coste por hora (para cálculo de costes)
- Información adicional del perfil

### Project (Proyecto)
- Información del proyecto: nombre, descripción, color
- Estado del proyecto
- Usuario creador
- Fechas de creación y actualización
- Métodos para cálculos financieros

### TimeEntry (Registro de Tiempo)
- Control de entrada y salida
- Proyecto asociado
- Usuario que registra
- Duración calculada automáticamente
- Estado de la jornada

### SystemConfiguration (Configuración del Sistema)
- Configuración general del sistema
- Títulos y descripciones personalizables
- Configuraciones específicas por módulo

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.2.6
- **Frontend**: Bootstrap 5 + Bootstrap Icons
- **Base de Datos**: SQLite (desarrollo)
- **Autenticación**: Sistema de usuarios de Django
- **Permisos**: Django Groups (Agentes/Usuarios)
- **Formularios**: Django Forms con validaciones
- **Archivos Estáticos**: Django Static Files

## 📋 Requisitos

- Python 3.12+
- Django 5.2.6
- django-bootstrap5

## 🚀 Instalación y Configuración

1. **Clonar el repositorio**
```bash
git clone [url-del-repositorio]
cd ticketproo
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

5. **Crear grupos de usuarios y configuración inicial**
```bash
python manage.py setup_groups
python manage.py create_user_profiles
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
ticketproo/
├── manage.py
├── db.sqlite3
├── media/                      # Archivos subidos
│   └── ticket_attachments/     # Adjuntos de tickets
├── static/                     # Archivos estáticos
│   └── css/
│       └── style.css          # Estilos personalizados minimalistas
├── templates/                  # Templates HTML
│   ├── base.html
│   ├── registration/
│   └── tickets/               # Templates de la aplicación
│       ├── dashboard.html     # Dashboard principal
│       ├── ticket_*.html      # Gestión de tickets
│       ├── user_*.html        # Gestión de usuarios
│       ├── company_*.html     # Gestión de empresas
│       ├── project_*.html     # Gestión de proyectos
│       ├── time_*.html        # Control de tiempo
│       └── config_*.html      # Configuración del sistema
├── ticket_system/              # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── tickets/                    # App principal
    ├── models.py              # Modelos: Ticket, Company, Project, etc.
    ├── views.py               # Vistas para todas las funcionalidades
    ├── forms.py               # Formularios del sistema
    ├── urls.py                # URLs de la aplicación
    ├── admin.py               # Configuración del admin
    ├── utils.py               # Funciones auxiliares
    ├── templatetags/          # Template tags personalizados
    │   └── project_extras.py  # Filtros para cálculos financieros
    ├── management/commands/    # Comandos personalizados
    │   ├── setup_groups.py
    │   ├── assign_admin_agent.py
    │   └── create_user_profiles.py
    └── migrations/            # Migraciones de base de datos
```

## 🔧 Configuración Avanzada

### Variables de Entorno (Producción)
```bash
# .env file
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/ticketproo
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Base de Datos en Producción
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ticketproo',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Deployment con Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📊 Métricas y Monitoreo

### Dashboard de Estadísticas
- **Total de Tickets**: Contador global del sistema
- **Tickets Abiertos**: Tickets pendientes de resolución  
- **Tickets en Progreso**: Tickets siendo trabajados actualmente
- **Tickets Resueltos**: Tickets completados exitosamente
- **Sin Asignar**: Tickets que requieren asignación
- **Asignados a Mí**: Tickets del agente actual

### Análisis de Rendimiento
- **Tiempo Promedio de Resolución**: Por ticket y por agente
- **Productividad por Empleado**: Horas trabajadas vs. tickets resueltos
- **Rentabilidad por Proyecto**: Análisis de costes y beneficios
- **Eficiencia Operativa**: Métricas de tiempo y recursos

## 🧪 Testing

### Ejecutar Tests
```bash
python manage.py test
python manage.py test tickets.tests.test_models
python manage.py test tickets.tests.test_views
```

### Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📈 Performance

### Optimizaciones Implementadas
- **Select Related**: Optimización de queries en listas
- **Prefetch Related**: Carga eficiente de relaciones
- **Database Indexes**: Índices en campos frecuentemente consultados
- **Caching**: Cache de templates y queries (próximamente)

### Recomendaciones de Producción
- Usar PostgreSQL o MySQL en lugar de SQLite
- Configurar Redis para cache y sesiones
- Implementar CDN para archivos estáticos
- Configurar monitoring con Sentry o similar

## � Casos de Uso

### 🏢 Gestión Empresarial
```
1. Crear empresa "TechCorp S.L."
2. Asignar usuarios a la empresa
3. Configurar precios por empleado
4. Crear proyectos para la empresa
5. Registrar tiempo de trabajo en proyectos
6. Analizar rentabilidad
```

### ⏰ Control de Tiempo
```
1. Empleado inicia jornada → Selecciona proyecto
2. Sistema registra tiempo automáticamente
3. Empleado finaliza jornada
4. Cálculo automático de horas trabajadas
5. Asignación de costes y ventas por proyecto
```

### 📊 Análisis Financiero
```
Proyecto: "Desarrollo Web Cliente X"
- Horas trabajadas: 50h
- Empleado A (€70/h precio, €40/h coste): 30h
- Empleado B (€50/h precio, €35/h coste): 20h

Cálculos automáticos:
- Coste total: (30×€40) + (20×€35) = €1,900
- Venta total: (30×€70) + (20×€50) = €3,100
- Beneficio: €3,100 - €1,900 = €1,200
- Margen: (€1,200 / €3,100) × 100 = 38.7%
```

## 🛡️ Seguridad y Permisos

### Autenticación
- Login requerido para todas las funcionalidades
- Sesiones seguras con Django
- Logout automático por inactividad

### Autorización por Roles
```python
# Decoradores de seguridad
@login_required
@user_passes_test(is_agent, login_url='/')
def company_list_view(request):
    # Solo agentes pueden acceder
```

### Validaciones
- Archivos adjuntos: Tipos y tamaños permitidos
- Formularios: Validación de datos en backend
- CSRF: Protección en todos los formularios
- XSS: Escape automático en templates

## 📡 URLs y Navegación

### URLs Principales
```
/                           # Home/Dashboard
/tickets/                   # Lista de tickets
/tickets/create/           # Crear ticket
/tickets/{id}/             # Detalle de ticket
/users/                    # Gestión de usuarios (agentes)
/companies/                # Gestión de empresas (agentes)
/projects/                 # Gestión de proyectos (agentes)
/time-clock/               # Control de tiempo (agentes)
/config/                   # Configuración del sistema (agentes)
/admin/                    # Panel de administración Django
```

### API Endpoints (Próximamente)
```
GET    /api/tickets/           # Lista de tickets
POST   /api/tickets/           # Crear ticket
GET    /api/tickets/{id}/      # Detalle de ticket
PUT    /api/tickets/{id}/      # Actualizar ticket
DELETE /api/tickets/{id}/      # Eliminar ticket
```

## 📊 Funcionalidades por Rol

### 🛡️ Agentes
- **Gestión de Tickets**: Ver, crear, editar y eliminar cualquier ticket del sistema
- **Autoasignación**: Asignarse/desasignar tickets según disponibilidad
- **Gestión de Usuarios**: Crear, editar y administrar usuarios del sistema
- **Gestión de Empresas**: CRUD completo de empresas y asociación de usuarios
- **Control de Proyectos**: Crear y gestionar proyectos con análisis financiero
- **Control de Tiempo**: Registrar jornadas laborales y tiempo por proyecto
- **Supervisión de Asistencia**: Ver registros de tiempo de todos los empleados
- **Configuración del Sistema**: Acceso al panel de configuración general
- **Dashboard Completo**: Estadísticas globales del sistema
- **Análisis Financiero**: Ver costes, ventas, beneficios y márgenes de proyectos

### 👤 Usuarios
- **Gestión Personal**: Ver y gestionar solo sus propios tickets
- **Creación de Tickets**: Crear nuevos tickets de soporte
- **Edición Limitada**: Editar sus tickets existentes
- **Gestión de Adjuntos**: Subir archivos a sus tickets
- **Dashboard Personal**: Estadísticas de sus tickets
- **Perfil de Usuario**: Actualizar información personal

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

### `create_user_profiles`
Crea perfiles de usuario para todos los usuarios existentes que no tengan perfil.

```bash
python manage.py create_user_profiles
```

## 🎨 Interfaz de Usuario

- **Diseño Minimalista**: Paleta de colores en blanco y negro para mayor profesionalidad
- **Diseño Responsivo**: Compatible con móviles y tablets
- **Iconografía Consistente**: Bootstrap Icons en toda la aplicación
- **Navegación Intuitiva**: Menús contextuales según rol del usuario
- **Feedback Visual**: Alertas y notificaciones claras
- **Dashboard Interactivo**: Tarjetas de estadísticas con hover effects
- **Tablas Funcionales**: Ordenamiento y filtrado en tiempo real

## 💰 Sistema Financiero

### Configuración de Precios
- **Precio por Hora**: Tarifa que se cobra al cliente por el trabajo del empleado
- **Coste por Hora**: Coste interno que representa el empleado para la empresa

### Cálculos Automáticos
- **Coste Total**: `Horas trabajadas × Coste por hora del empleado`
- **Venta Total**: `Horas trabajadas × Precio por hora del empleado`
- **Beneficio**: `Venta Total - Coste Total`
- **Margen**: `(Beneficio / Venta Total) × 100`

### Análisis de Proyectos
- Vista en tabla con totales automáticos
- Filtros por estado de proyecto
- Exportación de datos (próximamente)
- Gráficos de rentabilidad (próximamente)

## 📈 Funcionalidades Implementadas

- [x] **Sistema de Tickets**: Gestión completa de tickets de soporte
- [x] **Gestión de Usuarios**: CRUD de usuarios con roles diferenciados
- [x] **Sistema de Empresas**: Gestión completa de empresas y asociación de usuarios
- [x] **Gestión de Proyectos**: CRUD de proyectos con análisis financiero
- [x] **Control de Tiempo**: Registro de jornadas laborales por proyecto
- [x] **Sistema de Precios**: Precio y coste por hora por empleado
- [x] **Análisis Financiero**: Cálculos automáticos de costes, ventas y beneficios
- [x] **Dashboard Minimalista**: Interfaz en blanco y negro con estadísticas
- [x] **Panel de Configuración**: Configuración general del sistema
- [x] **Template Tags Personalizados**: Filtros para cálculos financieros
- [x] **Categorías de Tickets**: Organización por categorías
- [x] **Secuencia de Tickets**: Numeración automática
- [x] **Mensajes entre Usuarios**: Sistema de comunicación
- [x] **Enlaces Públicos**: Compartir tickets mediante enlaces únicos
- [x] **Actualización de Perfil**: Gestión de perfil de usuario
- [x] **Notas Internas**: Sistema de notas para agentes y usuarios

## 🚀 Próximas Características
- [ ] Crear lista de publica de cursos.
- [ ] Crear lista de publica de recursos.
- [ ] **Formulario Público**: Crear tickets sin necesidad de login
- [ ] **Paginación Avanzada**: Paginación en todas las listas
- [ ] **Blog de Noticias**: Sistema de noticias y actualizaciones
- [ ] **API REST**: API para gestión externa de tickets
- [ ] **Notificaciones Email**: Alertas por correo electrónico
- [ ] **Reportes PDF**: Generación de reportes en PDF
- [ ] **Gráficos Avanzados**: Dashboard con gráficos interactivos
- [ ] **Integración con CRM**: Conectores con sistemas externos
- [ ] **Aplicación Móvil**: App nativa para iOS y Android
- [ ] **Chat en Tiempo Real**: Sistema de chat integrado
## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte y Contacto

Para soporte técnico, consultas comerciales o colaboraciones:

- 📧 **Email**: mfalconsoft@gmail.com
- 📱 **Teléfono**: +34-662-47-0645  
- 🌐 **Web**: https://ticketproo.com
- 💼 **LinkedIn**: [Marlon Falcon](https://linkedin.com/in/marlonfalcon)
- 🐙 **GitHub**: [falconsoft3d](https://github.com/falconsoft3d)

### Servicios Disponibles
- ✅ **Consultoría**: Implementación y personalización
- ✅ **Desarrollo**: Nuevas funcionalidades
- ✅ **Mantenimiento**: Soporte técnico continuo
- ✅ **Hosting**: Despliegue en servidores dedicados
- ✅ **Formación**: Capacitación para equipos

---

**TicketProo** - *La plataforma profesional para gestionar tickets, controlar tiempo de trabajo y analizar la rentabilidad de tus proyectos.*

> 💡 **¿Necesitas personalización?** Contacta con nosotros para adaptar TicketProo a las necesidades específicas de tu empresa.
