# TicketProo 🎫

**Sistema Profesional de Gestión de Tickets, Soporte Técnico y Control Empresarial con Blog y Base de Conocimientos**

TicketProo es una plataforma web moderna desarrollada en Django que permite gestionar tickets de soporte de manera eficiente, con control de tiempo de trabajo, gestión empresarial, análisis financiero de proyectos, sistema de blog completo, glosario de conceptos públicos y formulario de contacto web. Una solución integral para empresas que buscan optimizar su soporte técnico y presencia online.

# Screenshot

![Alt text](https://github.com/falconsoft3d/ticketproo/blob/main/docs/screenshot1.png?raw=true)

![Alt text](https://github.com/falconsoft3d/ticketproo/blob/main/docs/screenshot2.png?raw=true)

## Forma de actualizar
```
source ~/bin/activate
cd ticketproo

python manage.py makemigrations
python manage.py migrate
python manage.py setup_groups

cp ~/ticketproo/ticket_system/settings.py ~/old_settings.py
cp ~/old_settings.py ~/ticketproo/ticket_system/settings.py

sudo systemctl daemon-reload
sudo systemctl restart urban-train
sudo systemctl status urban-train

python manage.py runserver 0.0.0.0:8000
```





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
- ✅ **Sistema de Blog**: Plataforma completa de blog con categorías y comentarios
- ✅ **Glosario de Conceptos**: Base de conocimiento pública con términos y definiciones
- ✅ **Formulario de Contacto Web**: Sistema de contacto público para no usuarios registrados
- ✅ **Plantillas Unificadas**: Sistema de templates reutilizable para páginas públicas
- ✅ **Navegación Consistente**: Menú unificado en todas las páginas públicas

### 📚 Sistema de Blog
- **Categorías de Blog**: Organización por categorías con colores personalizados
- **Artículos Completos**: Editor de contenido rico con imágenes destacadas
- **Estados de Publicación**: Borradores, publicados y archivados
- **Sistema de Comentarios**: Comentarios con moderación
- **SEO Optimizado**: Meta descripciones y URLs amigables
- **Tags y Etiquetas**: Sistema de etiquetado para mejor organización
- **Artículos Destacados**: Promoción de contenido importante
- **Contador de Visualizaciones**: Métricas de popularidad de artículos

### 🧠 Glosario de Conceptos Públicos
- **Base de Conocimiento**: Términos y definiciones accesibles públicamente
- **Categorización**: Organización por categorías para fácil navegación
- **Búsqueda Inteligente**: Búsqueda por términos o contenido
- **Ordenamiento Personalizable**: Control del orden de aparición
- **Gestión de Contenido**: Panel de administración para agentes
- **Acceso Público**: Disponible sin necesidad de registro

### 📞 Sistema de Contacto Web
- **Formulario Público**: Contacto sin necesidad de registro
- **Gestión Completa**: Panel de administración para contactos recibidos
- **Seguimiento de Estado**: Control de leído/no leído y respondido
- **Información de Contexto**: Captura de IP y User Agent
- **Campos Completos**: Nombre, email, teléfono, empresa, asunto y mensaje
- **Notificaciones**: Sistema de alertas para nuevos contactos
- **Estadísticas**: Métricas de contactos recibidos y estado

### 🎨 Sistema de Plantillas Unificadas
- **Plantilla Base Reutilizable**: `public_base.html` para páginas públicas
- **Componentes Modulares**: Navbar y footer como includes
- **Navegación Consistente**: Menú unificado en todas las páginas
- **Diseño Responsive**: Bootstrap 5 con diseño adaptable
- **SEO Friendly**: Estructura HTML optimizada para buscadores
- **Personalización por Página**: Hero sections y contenido personalizable

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

### BlogCategory (Categoría de Blog)
- Información básica: nombre, slug, descripción
- Color personalizado para identificación visual
- Estado activo/inactivo
- Creador y fecha de creación

### BlogPost (Artículo de Blog)
- Título, slug y contenido completo
- Imagen destacada y resumen
- Estado: borrador, publicado, archivado
- Sistema de etiquetas y SEO
- Contador de visualizaciones
- Fecha de publicación programada

### BlogComment (Comentario de Blog)
- Información del comentarista
- Contenido del comentario
- Sistema de moderación (aprobado/pendiente)
- Información de contexto (IP, fecha)

### Concept (Concepto)
- Término y definición completa
- Categoría para organización
- Orden de aparición personalizable
- Estado activo/inactivo
- Creador y fechas de gestión

### ContactoWeb (Contacto Web)
- Información de contacto: nombre, email, teléfono, empresa
- Asunto y mensaje del contacto
- Estado de seguimiento: leído, respondido
- Información de contexto: IP, User Agent
- Fecha de creación y gestión

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

## 🌐 Páginas Públicas y Arquitectura

### 📄 Páginas Públicas Disponibles
- **Home (`/`)**: Página de inicio con hero section, estadísticas y call-to-actions
- **Blog (`/blog/`)**: Lista de artículos del blog con categorías y búsqueda
- **Conceptos (`/public/concepts/`)**: Glosario público de términos y definiciones
- **Contacto (`/contacto/`)**: Formulario de contacto para usuarios no registrados
- **Login (`/login/`)**: Página de inicio de sesión
- **Registro (`/register/`)**: Página de registro de nuevos usuarios

### 🏗️ Arquitectura de Templates
```
templates/
├── public_base.html           # Plantilla base para páginas públicas
├── base.html                  # Plantilla base para páginas privadas
├── blog_base.html             # Plantilla específica para blog
├── includes/
│   ├── public_navbar.html     # Navbar unificado para páginas públicas
│   └── public_footer.html     # Footer unificado para páginas públicas
└── tickets/
    ├── home.html              # Página de inicio
    ├── contacto_web.html      # Formulario de contacto
    ├── public_concepts.html   # Glosario público
    └── blog_*.html            # Templates del blog
```

### 🎨 Diseño Unificado
- **Consistencia Visual**: Mismo diseño en todas las páginas públicas
- **Navegación Unificada**: Menú consistente con enlaces activos
- **Responsive Design**: Adaptable a todos los dispositivos
- **SEO Optimizado**: Meta tags y estructura HTML optimizada
- **Accesibilidad**: Cumple estándares de accesibilidad web

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.2.6
- **Frontend**: Bootstrap 5 + Bootstrap Icons + CSS personalizado
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Autenticación**: Sistema de usuarios de Django con roles
- **Permisos**: Django Groups (Agentes/Usuarios)
- **Formularios**: Django Forms con validaciones avanzadas
- **Archivos Estáticos**: Django Static Files + Media Files
- **SEO**: URLs amigables, meta tags y sitemap
- **Responsive Design**: Mobile-first con Bootstrap 5
- **Templates**: Sistema de herencia con componentes reutilizables

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
│   ├── public_base.html       # Plantilla base para páginas públicas
│   ├── blog_base.html         # Plantilla base para blog
│   ├── includes/              # Componentes reutilizables
│   │   ├── public_navbar.html # Navbar público unificado
│   │   └── public_footer.html # Footer público unificado
│   ├── registration/
│   └── tickets/               # Templates de la aplicación
│       ├── dashboard.html     # Dashboard principal
│       ├── ticket_*.html      # Gestión de tickets
│       ├── user_*.html        # Gestión de usuarios
│       ├── company_*.html     # Gestión de empresas
│       ├── project_*.html     # Gestión de proyectos
│       ├── time_*.html        # Control de tiempo
│       ├── config_*.html      # Configuración del sistema
│       ├── blog_*.html        # Sistema de blog
│       ├── contacto_web.html  # Formulario de contacto público
│       ├── public_concepts.html # Glosario público
│       └── home.html          # Página de inicio
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
/blog/                      # Lista de artículos del blog
/blog/category/{slug}/      # Artículos por categoría
/blog/{slug}/               # Detalle de artículo
/public/concepts/           # Glosario público de conceptos
/contacto/                  # Formulario de contacto público
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
- **Gestión de Blog**: Crear, editar y publicar artículos del blog
- **Gestión de Conceptos**: Administrar el glosario público de términos
- **Gestión de Contactos Web**: Ver y gestionar contactos recibidos por el formulario público

### 👤 Usuarios
- **Gestión Personal**: Ver y gestionar solo sus propios tickets
- **Creación de Tickets**: Crear nuevos tickets de soporte
- **Edición Limitada**: Editar sus tickets existentes
- **Gestión de Adjuntos**: Subir archivos a sus tickets
- **Dashboard Personal**: Estadísticas de sus tickets
- **Perfil de Usuario**: Actualizar información personal
- **Acceso al Blog**: Leer artículos y dejar comentarios (si está habilitado)
- **Consulta de Conceptos**: Acceder al glosario público de términos

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
- [x] **Sistema de Blog Completo**: Plataforma de blog con categorías, comentarios y SEO
- [x] **Glosario de Conceptos Públicos**: Base de conocimiento accesible públicamente
- [x] **Formulario de Contacto Web**: Sistema de contacto para usuarios no registrados
- [x] **Plantillas Unificadas**: Sistema de templates reutilizable para páginas públicas
- [x] **Navegación Consistente**: Menú unificado en todas las páginas públicas y privadas
- [x] **Diseño Responsive**: Interfaz adaptable para móviles y tablets
- [x] **SEO Optimizado**: URLs amigables y meta tags en páginas públicas

## 🚀 Próximas Características
- [ ] **Paginación Avanzada**: Paginación en todas las listas
- [ ] **API REST**: API para gestión externa de tickets
- [ ] **Notificaciones Email**: Alertas por correo electrónico
- [ ] **Reportes PDF**: Generación de reportes en PDF
- [ ] **Gráficos Avanzados**: Dashboard con gráficos interactivos
- [ ] **Integración con CRM**: Conectores con sistemas externos
- [ ] **Aplicación Móvil**: App nativa para iOS y Android
- [ ] **Chat en Tiempo Real**: Sistema de chat integrado
- [ ] **Calendario de Eventos**: Gestión de citas y reuniones
- [ ] **Sistema de Exámenes**: Evaluaciones y certificaciones online
- [ ] **Análisis de Sentimientos**: IA para análisis de comentarios
- [ ] **Búsqueda Avanzada**: Motor de búsqueda inteligente
- [ ] **Exportación de Datos**: Exportar reportes a Excel/CSV
- [ ] **Webhooks**: Integración con servicios externos
- [ ] **Modo Offline**: Funcionalidad sin conexión
- [ ] **Tema Oscuro**: Modo oscuro para la interfaz
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

**TicketProo** - *La plataforma profesional integral para gestionar tickets, controlar tiempo de trabajo, analizar la rentabilidad de tus proyectos y mantener una presencia online sólida con blog y base de conocimientos.*

> 💡 **¿Necesitas personalización?** Contacta con nosotros para adaptar TicketProo a las necesidades específicas de tu empresa.
> 
> 🚀 **Nuevas Funcionalidades**: Sistema de blog completo, glosario público de conceptos, formulario de contacto web y plantillas unificadas para una experiencia consistente.
> 
> 📱 **Acceso Público**: Tu empresa ahora puede tener presencia web completa sin necesidad de que los visitantes se registren.
