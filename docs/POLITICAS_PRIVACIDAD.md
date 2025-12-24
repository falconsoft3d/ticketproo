# Sistema de Políticas de Privacidad

## Descripción
Sistema completo para gestionar políticas de privacidad desde el módulo QA. Permite crear, editar y publicar políticas que son accesibles públicamente mediante URLs amigables.

## Características

### ✅ Panel de Administración (QA)
- **Listar políticas**: Ver todas las políticas de privacidad con filtros de búsqueda
- **Crear política**: Crear nuevas políticas con título y contenido
- **Editar política**: Modificar políticas existentes
- **Eliminar política**: Eliminar políticas (con confirmación)
- **Estado activo/inactivo**: Controlar la visibilidad pública de cada política

### ✅ Vista Pública
- **URL amigable**: Acceso público en `/privacy/<slug>/`
- **Sin autenticación**: No requiere login para ver políticas activas
- **Copiar contenido**: Botón para copiar todo el contenido al portapapeles
- **Imprimir**: Botón para imprimir la política
- **Diseño responsive**: Adaptado a dispositivos móviles

## Acceso

### Panel de Gestión (Requiere ser Agente)
- **Menú**: QA → Políticas de Privacidad
- **URL**: `/qa/privacy-policies/`

### URLs del Sistema
```
# Gestión (solo agentes)
/qa/privacy-policies/                    # Lista
/qa/privacy-policies/create/             # Crear
/qa/privacy-policies/<id>/edit/          # Editar
/qa/privacy-policies/<id>/delete/        # Eliminar

# Vista pública (sin autenticación)
/privacy/<slug>/                         # Ver política pública
```

## Uso

### 1. Crear una Política
1. Ve al menú **QA** → **Políticas de Privacidad**
2. Click en **Nueva Política**
3. Completa el formulario:
   - **Título**: Nombre descriptivo (ej: "Política de Privacidad General")
   - **Contenido**: Texto completo de la política (soporta HTML)
   - **Activa**: Marca para hacerla visible públicamente
4. Click en **Crear Política**

### 2. Ver/Editar Política
- Desde la lista, click en **Editar** en la política deseada
- Modifica los campos necesarios
- Guarda los cambios

### 3. Compartir URL Pública
- Las políticas activas muestran un botón **Copiar URL**
- La URL tiene el formato: `https://tudominio.com/privacy/titulo-de-la-politica/`
- Comparte esta URL con usuarios o úsala en tu sitio web

### 4. Vista Pública
- Los usuarios pueden acceder sin login a `/privacy/<slug>/`
- Pueden copiar el contenido completo con un click
- Pueden imprimir la política directamente

## Modelo de Datos

### PrivacyPolicy
```python
- title (CharField): Título de la política
- slug (SlugField): URL amigable (auto-generado)
- content (TextField): Contenido completo
- is_active (BooleanField): Si está visible públicamente
- created_by (ForeignKey): Usuario que creó la política
- created_at (DateTimeField): Fecha de creación
- updated_at (DateTimeField): Última actualización
```

## Ejemplos de Uso

### Ejemplo 1: Política de Privacidad de Sitio Web
```
Título: Política de Privacidad del Sitio Web
Slug: politica-de-privacidad-del-sitio-web
URL: https://tudominio.com/privacy/politica-de-privacidad-del-sitio-web/
```

### Ejemplo 2: Términos de Uso de App Móvil
```
Título: Términos de Uso App Móvil
Slug: terminos-de-uso-app-movil
URL: https://tudominio.com/privacy/terminos-de-uso-app-movil/
```

## Integración

### En tu sitio web
```html
<!-- Enlace en el footer -->
<a href="/privacy/politica-de-privacidad/">Política de Privacidad</a>

<!-- Enlace en formularios -->
<label>
  <input type="checkbox" required>
  Acepto la <a href="/privacy/terminos-y-condiciones/" target="_blank">
    Política de Privacidad
  </a>
</label>
```

## Administración Django

También puedes gestionar políticas desde el admin de Django:
- URL: `/admin/tickets/privacypolicy/`
- Mismas funcionalidades del panel QA

## Notas Técnicas

- **Slug automático**: Se genera automáticamente del título
- **Validación única**: No puede haber dos políticas con el mismo título o slug
- **Filtros**: Búsqueda por título/contenido y estado activo/inactivo
- **Permisos**: Solo usuarios con rol de agente pueden gestionar políticas
- **Vista pública**: No requiere autenticación, solo políticas activas son visibles

## Migración

La migración ya fue aplicada:
```bash
python manage.py makemigrations tickets
python manage.py migrate tickets
```

Migración creada: `tickets/migrations/0392_privacypolicy.py`
