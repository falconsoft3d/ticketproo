from django.contrib import admin
from .models import Ticket, TicketAttachment

# Configuración del sitio de administración
admin.site.site_header = "TicketProo - Administración"
admin.site.site_title = "TicketProo Admin"
admin.site.index_title = "Panel de Administración de TicketProo"

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_by', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    list_editable = ('priority', 'status')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description')
        }),
        ('Clasificación', {
            'fields': ('priority', 'status')
        }),
        ('Asignación', {
            'fields': ('created_by', 'assigned_to')
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
