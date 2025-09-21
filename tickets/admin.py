from django.contrib import admin
from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserNote, 
    TimeEntry, Project, Company, SystemConfiguration
)

# Configuración del sitio de administración
admin.site.site_header = "TicketProo - Administración"
admin.site.site_title = "TicketProo Admin"
admin.site.index_title = "Panel de Administración de TicketProo"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored_badge', 'is_active', 'ticket_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description')
        }),
        ('Configuración', {
            'fields': ('color', 'is_active')
        }),
    )
    
    def colored_badge(self, obj):
        """Muestra el nombre de la categoría con su color"""
        return f'<span style="background-color: {obj.color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;"><i class="fas fa-tag"></i> {obj.name}</span>'
    colored_badge.short_description = 'Vista Previa'
    colored_badge.allow_tags = True
    
    def ticket_count(self, obj):
        """Muestra el número de tickets en esta categoría"""
        count = obj.tickets.count()
        return f'{count} tickets'
    ticket_count.short_description = 'Tickets'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored_badge', 'status', 'is_active', 'get_total_hours', 'get_active_workers_count', 'created_by', 'created_at')
    list_filter = ('status', 'is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description', 'created_by__username')
    list_editable = ('status', 'is_active')
    ordering = ('-created_at', 'name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'get_total_hours', 'get_active_workers_count')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Configuración', {
            'fields': ('color', 'status', 'is_active')
        }),
        ('Fechas del Proyecto', {
            'fields': ('start_date', 'end_date')
        }),
        ('Estadísticas', {
            'fields': ('get_total_hours', 'get_active_workers_count'),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_badge(self, obj):
        """Muestra el nombre del proyecto con su color"""
        return f'<span style="background-color: {obj.color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;"><i class="fas fa-folder"></i> {obj.name}</span>'
    colored_badge.short_description = 'Vista Previa'
    colored_badge.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'title', 'category', 'created_by', 'priority', 'status', 'hours', 'created_at')
    list_filter = ('category', 'priority', 'status', 'created_at')
    search_fields = ('ticket_number', 'title', 'description', 'created_by__username', 'category__name')
    list_editable = ('category', 'priority', 'status', 'hours')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('ticket_number', 'title', 'description')
        }),
        ('Clasificación', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Asignación y Tiempo', {
            'fields': ('created_by', 'assigned_to', 'hours')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'ticket', 'uploaded_by', 'uploaded_at', 'get_file_size_display')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('original_filename', 'ticket__title', 'uploaded_by__username')
    ordering = ('-uploaded_at',)
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('original_filename', 'file', 'file_size')
        }),
        ('Asociación', {
            'fields': ('ticket', 'uploaded_by')
        }),
    )
    
    readonly_fields = ('file_size', 'original_filename')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.uploaded_by = request.user
            if obj.file:
                obj.original_filename = obj.file.name
                obj.file_size = obj.file.size
        super().save_model(request, obj, form, change)


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'created_at', 'content_preview')
    list_filter = ('created_at', 'user')
    search_fields = ('ticket__ticket_number', 'ticket__title', 'user__username', 'content')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Comentario', {
            'fields': ('ticket', 'user', 'content')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        """Muestra una vista previa del contenido del comentario"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = 'Vista previa'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_by', 'is_private', 'tickets_count', 'created_at')
    list_filter = ('is_private', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'user__username', 'user__first_name', 'user__last_name', 'created_by__username')
    list_editable = ('is_private',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información de la Nota', {
            'fields': ('title', 'description', 'user', 'created_by')
        }),
        ('Configuración', {
            'fields': ('is_private', 'tickets')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('tickets',)  # Para selección múltiple de tickets
    
    def tickets_count(self, obj):
        """Muestra el número de tickets relacionados"""
        count = obj.get_related_tickets_count()
        if count == 0:
            return 'Sin tickets'
        elif count == 1:
            return '1 ticket'
        else:
            return f'{count} tickets'
    tickets_count.short_description = 'Tickets Relacionados'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related y prefetch_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'created_by').prefetch_related('tickets')


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'fecha_entrada', 'fecha_salida', 'duracion_formateada', 'notas')
    list_filter = ('fecha_entrada', 'user', 'project', 'project__status')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'notas', 'project__name')
    readonly_fields = ('duracion_trabajada', 'fecha_entrada', 'fecha_salida')
    ordering = ('-fecha_entrada',)
    date_hierarchy = 'fecha_entrada'
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('user', 'project')
        }),
        ('Horarios', {
            'fields': ('fecha_entrada', 'fecha_salida', 'duracion_trabajada')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related('user', 'project')
    
    def has_change_permission(self, request, obj=None):
        """Solo permitir edición de notas, no de horarios"""
        if obj is not None:
            return obj.can_edit(request.user)
        return super().has_change_permission(request, obj)
    
    def has_view_permission(self, request, obj=None):
        if obj is not None:
            return obj.can_view(request.user)
        return super().has_view_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Solo administradores pueden eliminar registros de tiempo"""
        return request.user.is_superuser


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored_badge', 'is_active', 'tickets_count', 'users_count', 'contact_info', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'email', 'phone', 'website')
    list_editable = ('is_active',)
    ordering = ('name',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'tickets_count', 'users_count')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description')
        }),
        ('Información de Contacto', {
            'fields': ('email', 'phone', 'website', 'address')
        }),
        ('Configuración', {
            'fields': ('color', 'is_active')
        }),
        ('Estadísticas', {
            'fields': ('tickets_count', 'users_count'),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_badge(self, obj):
        """Muestra el nombre de la empresa con su color"""
        color = obj.color if obj.color else '#6c757d'
        return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;"><i class="fas fa-building"></i> {obj.name}</span>'
    colored_badge.short_description = 'Vista Previa'
    colored_badge.allow_tags = True
    
    def tickets_count(self, obj):
        """Muestra el número de tickets de la empresa"""
        count = obj.get_active_tickets_count()
        return f'{count} tickets'
    tickets_count.short_description = 'Tickets'
    
    def users_count(self, obj):
        """Muestra el número de usuarios de la empresa"""
        count = obj.get_users_count()
        return f'{count} usuarios'
    users_count.short_description = 'Usuarios'
    
    def contact_info(self, obj):
        """Muestra información de contacto resumida"""
        info = []
        if obj.email:
            info.append(f'📧 {obj.email}')
        if obj.phone:
            info.append(f'📞 {obj.phone}')
        if obj.website:
            info.append(f'🌐 {obj.website}')
        return ' | '.join(info) if info else 'Sin contacto'
    contact_info.short_description = 'Contacto'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('tickets', 'userprofile_set')


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Administración de la configuración del sistema"""
    
    list_display = ('site_name', 'registration_status', 'default_ticket_priority', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('site_name',)
        }),
        ('Configuración de Usuarios', {
            'fields': ('allow_user_registration',),
            'description': 'Controla si los usuarios pueden registrarse automáticamente'
        }),
        ('Configuración de Tickets', {
            'fields': ('default_ticket_priority',),
            'description': 'Establece la prioridad por defecto para nuevos tickets'
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def registration_status(self, obj):
        """Muestra el estado del registro de usuarios"""
        if obj.allow_user_registration:
            return '✅ Habilitado'
        return '❌ Deshabilitado'
    registration_status.short_description = 'Registro de Usuarios'
    
    def has_add_permission(self, request):
        """Solo permitir una instancia de configuración"""
        # Verificar si ya existe una configuración
        if SystemConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Asegurar que solo exista una instancia"""
        obj.pk = 1
        super().save_model(request, obj, form, change)
