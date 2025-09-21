from django.contrib import admin
from .models import Ticket, TicketAttachment, Category, TicketComment

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
