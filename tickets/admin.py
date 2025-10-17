from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserNote, 
    TimeEntry, Project, Company, SystemConfiguration, Document, UserProfile,
    WorkOrder, WorkOrderAttachment, Task, Opportunity, OpportunityStatus, 
    OpportunityNote, OpportunityStatusHistory, Concept, Exam, ExamQuestion, 
    ExamAttempt, ExamAnswer, ContactoWeb, Employee, JobApplicationToken,
    LandingPage, LandingPageSubmission, WorkOrderTask, WorkOrderTaskTimeEntry,
    WorkOrderTaskTimeSession, SharedFile, SharedFileDownload, Recording, RecordingPlayback,
    PageVisit, MultipleDocumentation, MultipleDocumentationItem, MultipleDocumentationStats,
    MultipleDocumentationItemStats, MultipleDocumentationVisit, MultipleDocumentationDownload,
    TaskSchedule, ScheduleTask, ScheduleComment, TicketApproval, SatisfactionSurvey, FinancialAction,
    FinancialPriceHistory, Product, ClientProjectAccess, ClientTimeEntry, CompanyDocumentation, CompanyDocumentationURL, ContactGenerator,
    CompanyRequestGenerator, CompanyRequest, CompanyRequestComment,
    Form, FormQuestion, FormQuestionOption, FormResponse, FormAnswer, Alcance
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
    
    def colored_badge(self, obj):
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            obj.color, obj.name
        )
    colored_badge.short_description = 'Categoría'
    
    def ticket_count(self, obj):
        return obj.tickets.count()
    ticket_count.short_description = 'Tickets'


class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 1
    fields = ('question_text', 'option_a', 'option_b', 'option_c', 'correct_option', 'order')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'get_questions_count', 'is_public', 'public_token', 'passing_score', 'created_at')
    list_filter = ('is_public', 'created_by', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('public_token', 'created_at', 'updated_at')
    inlines = [ExamQuestionInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'passing_score', 'time_limit')
        }),
        ('Configuración Pública', {
            'fields': ('is_public', 'public_token'),
            'description': 'Si el examen es público, se generará automáticamente un token de acceso'
        }),
        ('Información del Sistema', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question_text_preview', 'correct_option', 'order', 'created_at')
    list_filter = ('exam', 'correct_option', 'created_at')
    search_fields = ('question_text', 'option_a', 'option_b', 'option_c')
    ordering = ('exam', 'order')
    
    def question_text_preview(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    question_text_preview.short_description = 'Pregunta'


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('participant_name', 'participant_email', 'exam', 'score', 'passed', 'completed_at')
    list_filter = ('passed', 'exam', 'completed_at')
    search_fields = ('participant_name', 'participant_email', 'exam__title')
    readonly_fields = ('score', 'total_questions', 'correct_answers', 'time_taken', 'passed', 'started_at', 'completed_at')
    ordering = ('-completed_at',)
    
    fieldsets = (
        ('Participante', {
            'fields': ('participant_name', 'participant_email', 'user')
        }),
        ('Resultados', {
            'fields': ('exam', 'score', 'total_questions', 'correct_answers', 'passed')
        }),
        ('Información de Tiempo', {
            'fields': ('started_at', 'completed_at', 'time_taken'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'is_correct')
    list_filter = ('is_correct', 'selected_option', 'attempt__exam')
    search_fields = ('attempt__participant_name', 'question__question_text')
    readonly_fields = ('is_correct',)
    
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
        ('Asignaciones', {
            'fields': ('assigned_users',),
            'description': 'Usuarios que tendrán acceso a los tickets de este proyecto'
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
    
    filter_horizontal = ('assigned_users',)
    
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
    list_display = ('ticket_number', 'title', 'category', 'ticket_type', 'created_by', 'priority', 'status', 'hours', 'created_at')
    list_filter = ('category', 'ticket_type', 'priority', 'status', 'created_at')
    search_fields = ('ticket_number', 'title', 'description', 'created_by__username', 'category__name')
    list_editable = ('category', 'ticket_type', 'priority', 'status', 'hours')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('ticket_number', 'title', 'description')
        }),
        ('Clasificación', {
            'fields': ('category', 'ticket_type', 'priority', 'status')
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
    
    list_display = ('site_name', 'registration_status', 'email_notifications_status', 'telegram_notifications_status', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('site_name', 'default_currency')
        }),
        ('Configuración de Usuarios', {
            'fields': ('allow_user_registration',),
            'description': 'Controla si los usuarios pueden registrarse automáticamente'
        }),
        ('Configuración de Tickets', {
            'fields': ('default_ticket_priority',),
            'description': 'Establece la prioridad por defecto para nuevos tickets'
        }),
        ('Configuración de IA', {
            'fields': ('ai_chat_enabled', 'openai_api_key', 'openai_model', 'ai_employee_analysis_prompt'),
            'description': 'Configuración para funcionalidades de inteligencia artificial',
            'classes': ('collapse',)
        }),
        ('Notificaciones por Email', {
            'fields': (
                'enable_email_notifications',
                'notification_emails',
                'email_host',
                'email_port',
                'email_host_user',
                'email_host_password',
                'email_use_tls',
                'email_use_ssl',
                'email_from'
            ),
            'description': 'Configuración para envío de notificaciones por email cuando se reciben contactos web'
        }),
        ('Notificaciones de Telegram', {
            'fields': ('enable_telegram_notifications', 'telegram_bot_token', 'telegram_chat_id'),
            'description': 'Configuración para envío de notificaciones a Telegram',
            'classes': ('collapse',)
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
    
    def email_notifications_status(self, obj):
        """Muestra el estado de las notificaciones por email"""
        if obj.enable_email_notifications:
            return '📧 Activo'
        return '📧 Inactivo'
    email_notifications_status.short_description = 'Notificaciones Email'
    
    def telegram_notifications_status(self, obj):
        """Muestra el estado de las notificaciones de Telegram"""
        if obj.enable_telegram_notifications:
            return '📱 Activo'
        return '📱 Inactivo'
    telegram_notifications_status.short_description = 'Notificaciones Telegram'
    
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


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Administración de documentos"""
    
    list_display = ('title', 'file_type', 'file_size_formatted', 'is_public', 'download_count', 'company', 'created_by', 'created_at')
    list_filter = ('is_public', 'file_type', 'created_at', 'company', 'created_by')
    search_fields = ('title', 'description', 'tags', 'file_type', 'created_by__username', 'company__name')
    list_editable = ('is_public',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('public_share_token', 'file_size', 'file_type', 'download_count', 'created_at', 'updated_at', 'public_url')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'file')
        }),
        ('Clasificación', {
            'fields': ('company', 'tags')
        }),
        ('Configuración de Compartir', {
            'fields': ('is_public', 'public_share_token', 'public_url')
        }),
        ('Información del Archivo', {
            'fields': ('file_type', 'file_size', 'download_count'),
            'classes': ('collapse',)
        }),
        ('Autoría y Fechas', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by', 'company')
    
    def public_url(self, obj):
        """Muestra la URL pública si está disponible"""
        if obj.is_public:
            return obj.public_url
        return 'No disponible (documento privado)'
    public_url.short_description = 'URL Pública'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'cargo', 'company', 'phone')
    list_filter = ('company', 'cargo')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'cargo', 'phone')
    raw_id_fields = ('user',)
    ordering = ('user__username',)
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user',)
        }),
        ('Información Profesional', {
            'fields': ('cargo', 'descripcion_cargo', 'company')
        }),
        ('Información de Contacto', {
            'fields': ('phone',)
        }),
        ('Información Personal', {
            'fields': ('bio',),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('notification_preferences',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company')


class WorkOrderAttachmentInline(admin.TabularInline):
    """Inline para adjuntos de órdenes de trabajo"""
    model = WorkOrderAttachment
    extra = 0
    readonly_fields = ('uploaded_at', 'file_size', 'get_file_size_display')
    fields = ('file', 'original_filename', 'uploaded_by', 'uploaded_at', 'get_file_size_display')
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()
    get_file_size_display.short_description = 'Tamaño'


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """Administrador para órdenes de trabajo"""
    list_display = ('order_number', 'title', 'company', 'status', 'priority', 'amount', 'due_date', 'created_by', 'assigned_to', 'is_public', 'created_at')
    list_filter = ('status', 'priority', 'is_public', 'created_at', 'due_date', 'company')
    search_fields = ('title', 'description', 'company__name', 'created_by__username', 'assigned_to__username')
    list_editable = ('status', 'priority', 'assigned_to')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ()
    readonly_fields = ('order_number', 'public_share_token', 'created_at', 'updated_at')
    inlines = [WorkOrderAttachmentInline]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('order_number', 'title', 'description', 'company')
        }),
        ('Estado y progreso', {
            'fields': ('status', 'priority', 'due_date', 'estimated_hours', 'amount')
        }),
        ('Asignación', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Configuración pública', {
            'fields': ('is_public', 'public_share_token'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'company', 'created_by', 'assigned_to'
        ).prefetch_related('attachments')


@admin.register(WorkOrderAttachment)
class WorkOrderAttachmentAdmin(admin.ModelAdmin):
    """Administrador para adjuntos de órdenes de trabajo"""
    list_display = ('original_filename', 'work_order', 'uploaded_by', 'get_file_size_display', 'uploaded_at')
    list_filter = ('uploaded_at', 'work_order__status')
    search_fields = ('original_filename', 'work_order__title', 'uploaded_by__username')
    readonly_fields = ('file_size', 'uploaded_at', 'get_file_size_display')
    ordering = ('-uploaded_at',)
    date_hierarchy = 'uploaded_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('work_order', 'uploaded_by')


class WorkOrderTaskTimeEntryInline(admin.TabularInline):
    model = WorkOrderTaskTimeEntry
    extra = 0
    fields = ('hours', 'description', 'date', 'created_at')
    readonly_fields = ('created_at',)


class WorkOrderTaskTimeSessionInline(admin.TabularInline):
    model = WorkOrderTaskTimeSession
    extra = 0
    fields = ('user', 'start_time', 'end_time', 'is_active', 'description')
    readonly_fields = ('start_time',)


@admin.register(WorkOrderTask)
class WorkOrderTaskAdmin(admin.ModelAdmin):
    """Administrador para tareas de órdenes de trabajo"""
    list_display = ('title', 'work_order', 'status', 'estimated_hours', 'actual_hours', 'get_progress_display', 'order')
    list_filter = ('status', 'work_order__status', 'created_at')
    search_fields = ('title', 'description', 'work_order__title', 'work_order__order_number')
    list_editable = ('status', 'order')
    ordering = ('work_order', 'order', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'completed_at')
    inlines = [WorkOrderTaskTimeEntryInline, WorkOrderTaskTimeSessionInline]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('work_order', 'title', 'description', 'order')
        }),
        ('Estado y tiempo', {
            'fields': ('status', 'estimated_hours', 'actual_hours')
        }),
        ('Fechas del sistema', {
            'fields': ('created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_progress_display(self, obj):
        """Muestra el progreso de la tarea"""
        percentage = obj.get_progress_percentage()
        if percentage > 0:
            return f"{percentage:.1f}%"
        return "0%"
    get_progress_display.short_description = 'Progreso'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('work_order')


@admin.register(WorkOrderTaskTimeEntry)
class WorkOrderTaskTimeEntryAdmin(admin.ModelAdmin):
    """Administrador para entradas de tiempo de tareas"""
    list_display = ('task', 'hours', 'date', 'get_task_work_order', 'created_at')
    list_filter = ('date', 'created_at', 'task__status')
    search_fields = ('description', 'task__title', 'task__work_order__title')
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    
    def get_task_work_order(self, obj):
        return obj.task.work_order.order_number
    get_task_work_order.short_description = 'Orden de Trabajo'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'task__work_order')


@admin.register(WorkOrderTaskTimeSession)
class WorkOrderTaskTimeSessionAdmin(admin.ModelAdmin):
    """Administrador para sesiones de tiempo de tareas"""
    list_display = ('task', 'user', 'start_time', 'end_time', 'get_duration_display', 'is_active')
    list_filter = ('is_active', 'start_time', 'user', 'task__status')
    search_fields = ('description', 'task__title', 'user__username', 'task__work_order__title')
    ordering = ('-start_time',)
    readonly_fields = ('start_time', 'get_duration_display')
    date_hierarchy = 'start_time'
    
    def get_duration_display(self, obj):
        """Muestra la duración de la sesión"""
        hours = obj.get_duration_hours()
        return f"{hours}h"
    get_duration_display.short_description = 'Duración'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'user', 'task__work_order')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Administrador para tareas"""
    list_display = ('title', 'status', 'priority', 'created_by', 'due_date', 'assigned_users_display', 'is_overdue_display', 'created_at')
    list_filter = ('status', 'priority', 'created_at', 'due_date', 'created_by')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_users__username')
    list_editable = ('status', 'priority')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    filter_horizontal = ('assigned_users',)
    
    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'description', 'created_by')
        }),
        ('Estado y prioridad', {
            'fields': ('status', 'priority', 'due_date')
        }),
        ('Asignación', {
            'fields': ('assigned_users',)
        }),
        ('Fechas del sistema', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def assigned_users_display(self, obj):
        """Muestra los usuarios asignados de forma resumida"""
        users = obj.assigned_users.all()
        if not users:
            return 'Sin asignar'
        elif len(users) <= 2:
            return ', '.join([user.username for user in users])
        else:
            return f'{users[0].username}, {users[1].username} y {len(users)-2} más'
    assigned_users_display.short_description = 'Usuarios Asignados'
    
    def is_overdue_display(self, obj):
        """Muestra si la tarea está vencida"""
        if obj.is_overdue():
            return '⚠️ Vencida'
        elif obj.due_date and obj.status not in ['completed', 'cancelled']:
            from django.utils import timezone
            days_left = (obj.due_date - timezone.now()).days
            if days_left <= 1:
                return '⏰ Próxima'
        return '✅ A tiempo'
    is_overdue_display.short_description = 'Estado de Vencimiento'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'created_by'
        ).prefetch_related('assigned_users')


# ============= ADMIN CRM =============

@admin.register(OpportunityStatus)
class OpportunityStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored_badge', 'order', 'is_final', 'is_won', 'is_active', 'opportunity_count')
    list_filter = ('is_final', 'is_won', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'name')
    
    def colored_badge(self, obj):
        return f'<span style="background-color: {obj.color}; color: white; padding: 2px 8px; border-radius: 3px;">{obj.name}</span>'
    colored_badge.short_description = 'Estado'
    colored_badge.allow_tags = True
    
    def opportunity_count(self, obj):
        return obj.opportunities.count()
    opportunity_count.short_description = 'Oportunidades'


class OpportunityNoteInline(admin.TabularInline):
    model = OpportunityNote
    extra = 0
    fields = ('content', 'is_important', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')


class OpportunityStatusHistoryInline(admin.TabularInline):
    model = OpportunityStatusHistory
    extra = 0
    fields = ('previous_status', 'new_status', 'changed_by', 'changed_at', 'comment')
    readonly_fields = ('changed_by', 'changed_at')


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'status_badge', 'value', 'probability', 'expected_close_date', 'assigned_to', 'created_by')
    list_filter = ('status', 'company', 'assigned_to', 'created_by', 'probability', 'created_at')
    search_fields = ('name', 'description', 'company__name', 'contact_name', 'contact_email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    inlines = [OpportunityNoteInline, OpportunityStatusHistoryInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'company', 'status')
        }),
        ('Contacto', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('Financiero', {
            'fields': ('value', 'probability')
        }),
        ('Fechas', {
            'fields': ('expected_close_date', 'actual_close_date', 'last_contact_date', 'next_follow_up')
        }),
        ('Asignación', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Adicional', {
            'fields': ('source',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    
    def status_badge(self, obj):
        return f'<span style="background-color: {obj.status.color}; color: white; padding: 2px 8px; border-radius: 3px;">{obj.status.name}</span>'
    status_badge.short_description = 'Estado'
    status_badge.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OpportunityNote)
class OpportunityNoteAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'content_preview', 'is_important', 'created_by', 'created_at')
    list_filter = ('is_important', 'created_by', 'created_at')
    search_fields = ('content', 'opportunity__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Contenido'


@admin.register(OpportunityStatusHistory)
class OpportunityStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'previous_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('previous_status', 'new_status', 'changed_by', 'changed_at')
    search_fields = ('opportunity__name', 'comment')
    ordering = ('-changed_at',)
    date_hierarchy = 'changed_at'
    readonly_fields = ('changed_at',)


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ('term', 'definition_preview', 'category', 'is_active', 'order', 'created_by', 'created_at')
    list_filter = ('is_active', 'category', 'created_by', 'created_at')
    search_fields = ('term', 'definition', 'category')
    list_editable = ('is_active', 'order')
    ordering = ('order', 'term')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('term', 'definition', 'category')
        }),
        ('Configuración', {
            'fields': ('is_active', 'order')
        }),
        ('Información del Sistema', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def definition_preview(self, obj):
        return obj.definition[:100] + '...' if len(obj.definition) > 100 else obj.definition
    definition_preview.short_description = 'Definición'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si estamos editando
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields


@admin.register(ContactoWeb)
class ContactoWebAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'empresa', 'asunto_short', 'fecha_creacion', 'status_badges', 'leido', 'respondido', 'ip_address')
    list_filter = ('leido', 'respondido', 'fecha_creacion', 'empresa')
    search_fields = ('nombre', 'email', 'empresa', 'asunto', 'mensaje')
    readonly_fields = ('fecha_creacion', 'ip_address', 'user_agent')
    list_editable = ('leido', 'respondido')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información del Contacto', {
            'fields': ('nombre', 'email', 'telefono', 'empresa')
        }),
        ('Mensaje', {
            'fields': ('asunto', 'mensaje')
        }),
        ('Estado', {
            'fields': ('leido', 'respondido')
        }),
        ('Información Técnica', {
            'fields': ('fecha_creacion', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def asunto_short(self, obj):
        return obj.asunto[:50] + "..." if len(obj.asunto) > 50 else obj.asunto
    asunto_short.short_description = 'Asunto'
    
    def status_badges(self, obj):
        html = ""
        if not obj.leido:
            html += '<span style="background-color: #ffc107; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">Nuevo</span>'
        if obj.respondido:
            html += '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">Respondido</span>'
        else:
            html += '<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px;">Pendiente</span>'
        return format_html(html)
    status_badges.short_description = 'Estado'
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Administrador para empleados"""
    list_display = ('get_full_name', 'email', 'position', 'salary_euros', 'status', 'ai_score', 'company', 'created_at')
    list_filter = ('status', 'company', 'created_at', 'ai_score')
    search_fields = ('first_name', 'last_name', 'email', 'position', 'description')
    list_editable = ('status',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'ai_analysis', 'ai_score')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Información Profesional', {
            'fields': ('position', 'salary_euros', 'description', 'resume_file')
        }),
        ('Análisis de IA', {
            'fields': ('ai_analysis', 'ai_score'),
            'classes': ('collapse',)
        }),
        ('Estado y Empresa', {
            'fields': ('status', 'company', 'created_by')
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')


@admin.register(JobApplicationToken)
class JobApplicationTokenAdmin(admin.ModelAdmin):
    """Administrador para tokens de aplicación de empleo"""
    list_display = ('job_title', 'proposed_salary_euros', 'company', 'is_active', 'application_count', 'max_applications', 'created_by', 'created_at')
    list_filter = ('is_active', 'company', 'created_at', 'created_by')
    search_fields = ('job_title', 'job_description', 'company__name')
    readonly_fields = ('application_token', 'application_count', 'created_at', 'get_public_url', 'get_qr_data')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Puesto', {
            'fields': ('job_title', 'job_description', 'proposed_salary_euros')
        }),
        ('Configuración', {
            'fields': ('company', 'created_by', 'is_active')
        }),
        ('Límites y Expiración', {
            'fields': ('max_applications', 'expires_at')
        }),
        ('Token y URLs', {
            'fields': ('application_token', 'get_public_url', 'get_qr_data'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('application_count',),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')


# =============================================================================
# ADMIN PARA LANDING PAGES
# =============================================================================

class LandingPageSubmissionInline(admin.TabularInline):
    model = LandingPageSubmission
    extra = 0
    readonly_fields = ('nombre', 'apellido', 'email', 'telefono', 'empresa', 'created_at', 'ip_address', 'utm_source', 'utm_medium', 'utm_campaign')
    fields = ('nombre', 'apellido', 'email', 'telefono', 'empresa', 'created_at', 'utm_source')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display = ('nombre_producto', 'slug', 'is_active', 'get_total_views', 'get_total_submissions', 'conversion_rate_display', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_by', 'created_at')
    search_fields = ('nombre_producto', 'descripcion', 'slug')
    list_editable = ('is_active',)
    readonly_fields = ('slug', 'created_at', 'updated_at', 'get_public_url')
    prepopulated_fields = {'slug': ('nombre_producto',)}
    inlines = [LandingPageSubmissionInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_producto', 'descripcion', 'imagen', 'slug', 'is_active')
        }),
        ('Configuración de Colores', {
            'fields': ('color_primario', 'color_secundario', 'color_boton'),
            'classes': ('collapse',)
        }),
        ('URL Pública', {
            'fields': ('get_public_url',),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_total_views(self, obj):
        return obj.total_views
    get_total_views.short_description = 'Vistas'
    
    def get_total_submissions(self, obj):
        return obj.total_submissions
    get_total_submissions.short_description = 'Envíos'
    
    def conversion_rate_display(self, obj):
        if obj.total_views > 0:
            rate = (obj.total_submissions / obj.total_views) * 100
            color = 'red' if rate < 2 else 'orange' if rate < 5 else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, rate
            )
        return '0%'
    conversion_rate_display.short_description = 'Tasa de Conversión'
    
    def get_public_url(self, obj):
        if obj.slug:
            from django.urls import reverse
            from django.utils.safestring import mark_safe
            url = reverse('landing_page_public', args=[obj.slug])
            return mark_safe(f'<a href="{url}" target="_blank">{url}</a>')
        return '-'
    get_public_url.short_description = 'URL Pública'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('submissions')


@admin.register(LandingPageSubmission)
class LandingPageSubmissionAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'telefono', 'empresa', 'landing_page', 'created_at', 'utm_source', 'utm_medium')
    list_filter = ('landing_page', 'created_at', 'utm_source', 'utm_medium')
    search_fields = ('nombre', 'apellido', 'email', 'telefono', 'empresa', 'landing_page__nombre_producto')
    readonly_fields = ('landing_page', 'nombre', 'apellido', 'email', 'telefono', 'empresa', 'created_at', 'ip_address', 'user_agent', 'utm_source', 'utm_medium', 'utm_campaign')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información de Contacto', {
            'fields': ('nombre', 'apellido', 'email', 'telefono', 'empresa')
        }),
        ('Landing Page', {
            'fields': ('landing_page',)
        }),
        ('Información Técnica', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Información de Campaña (UTM)', {
            'fields': ('utm_source', 'utm_medium', 'utm_campaign'),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    get_full_name.short_description = 'Nombre Completo'
    
    def has_add_permission(self, request):
        return False  # No permitir agregar desde admin
    
    def has_delete_permission(self, request, obj=None):
        return True  # Permitir eliminar
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('landing_page')


class SharedFileDownloadInline(admin.TabularInline):
    model = SharedFileDownload
    extra = 0
    readonly_fields = ('downloaded_by', 'ip_address', 'downloaded_at')
    can_delete = False


@admin.register(SharedFile)
class SharedFileAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'company', 
        'uploaded_by', 
        'file_type', 
        'get_file_size_display', 
        'download_count', 
        'is_public',
        'created_at'
    )
    list_filter = (
        'company', 
        'file_type', 
        'is_public', 
        'created_at',
        'uploaded_by'
    )
    search_fields = ('title', 'description', 'company__name', 'uploaded_by__username')
    readonly_fields = (
        'file_size', 
        'file_type', 
        'download_count', 
        'created_at', 
        'updated_at',
        'get_file_size_display'
    )
    list_per_page = 50
    date_hierarchy = 'created_at'
    inlines = [SharedFileDownloadInline]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'description', 'file')
        }),
        ('Configuración', {
            'fields': ('company', 'uploaded_by', 'is_public')
        }),
        ('Información del archivo', {
            'fields': ('file_type', 'file_size', 'get_file_size_display', 'download_count'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'uploaded_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un objeto nuevo
            if not obj.uploaded_by:
                obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SharedFileDownload)
class SharedFileDownloadAdmin(admin.ModelAdmin):
    list_display = (
        'shared_file', 
        'downloaded_by', 
        'ip_address', 
        'downloaded_at'
    )
    list_filter = (
        'downloaded_at', 
        'shared_file__company',
        'downloaded_by'
    )
    search_fields = (
        'shared_file__title', 
        'downloaded_by__username', 
        'ip_address'
    )
    readonly_fields = (
        'shared_file', 
        'downloaded_by', 
        'ip_address', 
        'user_agent', 
        'downloaded_at'
    )
    list_per_page = 100
    date_hierarchy = 'downloaded_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'shared_file', 
            'shared_file__company', 
            'downloaded_by'
        )
    
    def has_add_permission(self, request):
        return False  # No permitir agregar descargas manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # No permitir editar descargas


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'company', 
        'uploaded_by', 
        'transcription_status_badge',
        'file_size_display', 
        'duration_display',
        'playback_count',
        'is_public',
        'created_at'
    )
    list_filter = (
        'transcription_status',
        'is_public', 
        'company', 
        'created_at',
        'transcribed_at'
    )
    search_fields = (
        'title', 
        'description', 
        'transcription_text',
        'uploaded_by__username', 
        'uploaded_by__email',
        'company__name'
    )
    readonly_fields = (
        'file_size', 
        'duration_seconds',
        'transcription_status',
        'transcription_text',
        'transcription_confidence',
        'transcription_language',
        'transcribed_at',
        'created_at', 
        'updated_at',
        'playback_count_display'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'audio_file', 'company', 'uploaded_by', 'is_public')
        }),
        ('Información del Archivo', {
            'fields': ('file_size', 'duration_seconds'),
            'classes': ('collapse',)
        }),
        ('Transcripción', {
            'fields': (
                'transcription_status', 
                'transcription_text', 
                'transcription_confidence',
                'transcription_language',
                'transcribed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('playback_count_display',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    def transcription_status_badge(self, obj):
        colors = {
            'completed': 'success',
            'processing': 'warning', 
            'failed': 'danger',
            'pending': 'secondary'
        }
        color = colors.get(obj.transcription_status, 'secondary')
        status_display = obj.get_transcription_status_display()
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            status_display
        )
    transcription_status_badge.short_description = 'Estado Transcripción'
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'Tamaño'
    
    def duration_display(self, obj):
        return obj.get_duration_display()
    duration_display.short_description = 'Duración'
    
    def playback_count(self, obj):
        return obj.playbacks.count()
    playback_count.short_description = 'Reproducciones'
    
    def playback_count_display(self, obj):
        count = obj.playbacks.count()
        return f"{count} reproducciones"
    playback_count_display.short_description = 'Total de Reproducciones'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'company', 
            'uploaded_by'
        ).prefetch_related('playbacks')


@admin.register(RecordingPlayback)
class RecordingPlaybackAdmin(admin.ModelAdmin):
    list_display = (
        'recording_title',
        'played_by', 
        'played_at',
        'ip_address'
    )
    list_filter = (
        'played_at', 
        'recording__company',
        'played_by'
    )
    search_fields = (
        'recording__title',
        'played_by__username', 
        'played_by__email',
        'ip_address'
    )
    readonly_fields = (
        'recording', 
        'played_by', 
        'played_at', 
        'ip_address', 
        'user_agent'
    )
    
    date_hierarchy = 'played_at'
    
    def recording_title(self, obj):
        return obj.recording.title
    recording_title.short_description = 'Grabación'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recording', 
            'recording__company', 
            'played_by'
        )
    
    def has_add_permission(self, request):
        return False  # No permitir agregar reproducciones manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # No permitir editar reproducciones


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = (
        'visited_at',
        'page_type',
        'page_title_short',
        'ip_address',
        'location_info',
        'browser_info',
        'device_info',
        'is_bot'
    )
    list_filter = (
        'page_type',
        'visited_at',
        'country_code',
        'is_mobile',
        'is_bot',
        'browser'
    )
    search_fields = (
        'page_url',
        'page_title',
        'ip_address',
        'country',
        'city',
        'browser',
        'operating_system'
    )
    readonly_fields = (
        'page_type',
        'page_url',
        'page_title',
        'ip_address',
        'country',
        'country_code',
        'city',
        'region',
        'user_agent',
        'browser',
        'browser_version',
        'operating_system',
        'device_type',
        'is_mobile',
        'is_bot',
        'referrer',
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'session_id',
        'visited_at',
        'created_at'
    )
    
    date_hierarchy = 'visited_at'
    ordering = ('-visited_at',)
    
    fieldsets = (
        ('Información de la Página', {
            'fields': (
                'page_type',
                'page_url', 
                'page_title'
            )
        }),
        ('Información del Visitante', {
            'fields': (
                'ip_address',
                'country',
                'country_code',
                'region',
                'city'
            )
        }),
        ('Información Técnica', {
            'fields': (
                'user_agent',
                'browser',
                'browser_version',
                'operating_system',
                'device_type',
                'is_mobile',
                'is_bot'
            ),
            'classes': ('collapse',)
        }),
        ('Información de Referencia', {
            'fields': (
                'referrer',
                'utm_source',
                'utm_medium',
                'utm_campaign',
                'session_id'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'visited_at',
                'created_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def page_title_short(self, obj):
        if obj.page_title:
            return obj.page_title[:50] + '...' if len(obj.page_title) > 50 else obj.page_title
        return '(Sin título)'
    page_title_short.short_description = 'Título'
    
    def location_info(self, obj):
        return obj.location if obj.location != 'Desconocida' else '🌍 Desconocida'
    location_info.short_description = 'Ubicación'
    
    def device_info(self, obj):
        icon = '📱' if obj.is_mobile else '💻'
        return f"{icon} {obj.device_type}"
    device_info.short_description = 'Dispositivo'
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        return False  # No permitir agregar visitas manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # No permitir editar visitas (son datos de tracking)


# ==========================================
# ADMINISTRACIÓN DE DOCUMENTACIÓN MÚLTIPLE
# ==========================================

# class MultipleDocumentationItemInline(admin.TabularInline):
#     """Inline para items de documentación múltiple"""
#     model = MultipleDocumentationItem
#     extra = 0
#     fields = ('number', 'name', 'description', 'file')
#     ordering = ('number',)


# Temporalmente comentado para crear migración
# Todo el bloque de administración de documentación múltiple comentado


# ==========================================
# ADMINISTRACIÓN DE PLANIFICACIÓN DE TAREAS
# ==========================================

class ScheduleTaskInline(admin.TabularInline):
    """Inline para tareas del cronograma"""
    model = ScheduleTask
    extra = 0
    fields = ('title', 'start_date', 'end_date', 'priority', 'assigned_to', 'is_completed', 'progress_percentage')
    readonly_fields = ('completed_at',)
    ordering = ('start_date',)


@admin.register(TaskSchedule)
class TaskScheduleAdmin(admin.ModelAdmin):
    """Administración de cronogramas de tareas"""
    
    list_display = (
        'title', 
        'company', 
        'created_by', 
        'start_date', 
        'end_date',
        'progress_badge',
        'task_count',
        'is_public',
        'is_overdue_badge',
        'created_at'
    )
    
    list_filter = (
        'is_public',
        'company',
        'created_by',
        'created_at',
        'start_date',
        'end_date'
    )
    
    search_fields = (
        'title',
        'description',
        'company__name',
        'created_by__username',
        'created_by__first_name',
        'created_by__last_name'
    )
    
    readonly_fields = (
        'public_token',
        'created_at',
        'updated_at',
        'get_progress_percentage',
        'get_total_tasks',
        'get_completed_tasks',
        'get_pending_tasks',
        'get_overdue_tasks'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'company', 'created_by')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date')
        }),
        ('Configuración de Acceso', {
            'fields': ('is_public', 'public_token')
        }),
        ('Estadísticas', {
            'fields': (
                'get_progress_percentage',
                'get_total_tasks',
                'get_completed_tasks',
                'get_pending_tasks',
                'get_overdue_tasks'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ScheduleTaskInline]
    
    def progress_badge(self, obj):
        progress = obj.get_progress_percentage()
        if progress >= 75:
            color = 'success'
        elif progress >= 50:
            color = 'info'
        elif progress >= 25:
            color = 'warning'
        else:
            color = 'danger'
        
        return format_html(
            '<span class="badge badge-{}">{:.1f}%</span>',
            color, progress
        )
    progress_badge.short_description = 'Progreso'
    
    def task_count(self, obj):
        total = obj.get_total_tasks()
        completed = obj.get_completed_tasks()
        return format_html(
            '<span title="Completadas: {} / Total: {}">{} / {}</span>',
            completed, total, completed, total
        )
    task_count.short_description = 'Tareas'
    
    def is_overdue_badge(self, obj):
        if obj.is_overdue():
            return format_html('<span class="badge badge-danger">Vencido</span>')
        return format_html('<span class="badge badge-success">A tiempo</span>')
    is_overdue_badge.short_description = 'Estado'


@admin.register(ScheduleTask)
class ScheduleTaskAdmin(admin.ModelAdmin):
    """Administración de tareas del cronograma"""
    
    list_display = (
        'title',
        'schedule',
        'start_date',
        'end_date',
        'priority_badge',
        'assigned_to',
        'progress_badge',
        'is_completed',
        'is_overdue_badge',
        'dependency_count'
    )
    
    list_filter = (
        'is_completed',
        'priority',
        'schedule',
        'assigned_to',
        'start_date',
        'end_date',
        'created_at'
    )
    
    search_fields = (
        'title',
        'description',
        'schedule__title',
        'assigned_to__username',
        'assigned_to__first_name',
        'assigned_to__last_name'
    )
    
    readonly_fields = (
        'completed_at',
        'created_at',
        'updated_at',
        'is_overdue',
        'get_duration_days',
        'can_start'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('schedule', 'title', 'description')
        }),
        ('Fechas y Prioridad', {
            'fields': ('start_date', 'end_date', 'priority')
        }),
        ('Asignación y Progreso', {
            'fields': ('assigned_to', 'progress_percentage', 'is_completed', 'completed_at')
        }),
        ('Dependencias', {
            'fields': ('dependencies',)
        }),
        ('Información Adicional', {
            'fields': ('is_overdue', 'get_duration_days', 'can_start'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('dependencies',)
    
    def priority_badge(self, obj):
        colors = {
            'low': 'secondary',
            'medium': 'info',
            'high': 'warning',
            'critical': 'danger'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.priority, 'secondary'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    
    def progress_badge(self, obj):
        progress = obj.progress_percentage
        if progress >= 75:
            color = 'success'
        elif progress >= 50:
            color = 'info'
        elif progress >= 25:
            color = 'warning'
        else:
            color = 'danger'
        
        return format_html(
            '<span class="badge badge-{}">{:.0f}%</span>',
            color, progress
        )
    progress_badge.short_description = 'Progreso'
    
    def is_overdue_badge(self, obj):
        if obj.is_overdue():
            return format_html('<span class="badge badge-danger">⚠️ Vencida</span>')
        return format_html('<span class="badge badge-success">✓ A tiempo</span>')
    is_overdue_badge.short_description = 'Estado'
    
    def dependency_count(self, obj):
        count = obj.dependencies.count()
        if count > 0:
            return format_html('<span class="badge badge-info">{}</span>', count)
        return '-'
    dependency_count.short_description = 'Dependencias'


@admin.register(ScheduleComment)
class ScheduleCommentAdmin(admin.ModelAdmin):
    """Administración de comentarios de tareas"""
    
    list_display = (
        'task',
        'user',
        'comment_preview',
        'created_at'
    )
    
    list_filter = (
        'created_at',
        'user',
        'task__schedule'
    )
    
    search_fields = (
        'comment',
        'user__username',
        'user__first_name',
        'user__last_name',
        'task__title',
        'task__schedule__title'
    )
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Información del Comentario', {
            'fields': ('task', 'user', 'comment')
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def comment_preview(self, obj):
        if len(obj.comment) > 100:
            return obj.comment[:100] + '...'
        return obj.comment
    comment_preview.short_description = 'Comentario'


@admin.register(TicketApproval)
class TicketApprovalAdmin(admin.ModelAdmin):
    """Administración de aprobaciones de clientes"""
    
    list_display = (
        'ticket',
        'client_name',
        'client_email',
        'approved_at',
        'ip_address'
    )
    
    list_filter = (
        'approved_at',
        'ticket__status',
        'ticket__priority'
    )
    
    search_fields = (
        'ticket__ticket_number',
        'ticket__title',
        'client_name',
        'client_email'
    )
    
    readonly_fields = ('approved_at', 'ip_address')
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('client_name', 'client_email', 'notes')
        }),
        ('Información del Ticket', {
            'fields': ('ticket',)
        }),
        ('Metadatos', {
            'fields': ('approved_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Si el objeto ya existe, hacer todos los campos de solo lectura excepto las notas
        if obj:
            return self.readonly_fields + ('ticket', 'client_name', 'client_email')
        return self.readonly_fields


@admin.register(SatisfactionSurvey)
class SatisfactionSurveyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'client_name', 'client_email', 'overall_satisfaction', 'average_rating', 'rating_summary', 'submitted_at')
    list_filter = ('overall_satisfaction', 'resolution_quality', 'response_time', 'communication', 'would_recommend', 'submitted_at')
    search_fields = ('ticket__ticket_number', 'client_name', 'client_email', 'ticket__title')
    readonly_fields = ('submitted_at', 'ip_address', 'average_rating', 'rating_summary')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('client_name', 'client_email')
        }),
        ('Ticket', {
            'fields': ('ticket',)
        }),
        ('Calificaciones', {
            'fields': ('overall_satisfaction', 'resolution_quality', 'response_time', 'communication')
        }),
        ('Comentarios', {
            'fields': ('what_went_well', 'what_could_improve', 'additional_comments')
        }),
        ('Recomendación', {
            'fields': ('would_recommend', 'recommendation_reason')
        }),
        ('Metadatos', {
            'fields': ('submitted_at', 'ip_address', 'average_rating', 'rating_summary'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Si el objeto ya existe, hacer casi todos los campos de solo lectura
        if obj:
            return self.readonly_fields + ('ticket', 'client_name', 'client_email', 
                                         'overall_satisfaction', 'resolution_quality', 
                                         'response_time', 'communication', 'would_recommend')
        return self.readonly_fields
    
    def average_rating(self, obj):
        return f"{obj.average_rating}/5"
    average_rating.short_description = "Promedio"
    
    def rating_summary(self, obj):
        color = obj.rating_color
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.rating_summary
        )
    rating_summary.short_description = "Resumen"


@admin.register(FinancialAction)
class FinancialActionAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'currency', 'price_change_display', 'is_active', 'order', 'last_updated')
    list_filter = ('is_active', 'currency', 'created_at', 'last_updated')
    search_fields = ('symbol', 'name')
    list_editable = ('is_active', 'order', 'current_price')
    ordering = ('order', 'symbol')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('symbol', 'name', 'currency')
        }),
        ('Precios', {
            'fields': ('current_price', 'previous_price')
        }),
        ('Configuración', {
            'fields': ('is_active', 'order')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'last_updated')
    
    def price_change_display(self, obj):
        if obj.previous_price is None:
            return format_html('<span class="text-muted">Sin datos</span>')
        
        change = obj.price_change
        percent = obj.price_change_percent
        
        if obj.is_positive_change:
            icon = '▲'
            color = 'green'
        elif obj.is_negative_change:
            icon = '▼'
            color = 'red'
        else:
            icon = '●'
            color = 'gray'
        
        return format_html(
            '<span style="color: {};">{} {:+.4f} ({:+.2f}%)</span>',
            color, icon, change, percent
        )
    price_change_display.short_description = 'Cambio de Precio'
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(FinancialPriceHistory)
class FinancialPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('financial_action', 'price', 'recorded_at', 'get_action_symbol')
    list_filter = ('financial_action', 'recorded_at')
    search_fields = ('financial_action__symbol', 'financial_action__name')
    ordering = ('-recorded_at',)
    readonly_fields = ('recorded_at',)
    
    def get_action_symbol(self, obj):
        return obj.financial_action.symbol
    get_action_symbol.short_description = 'Símbolo'
    
    def has_add_permission(self, request):
        # No permitir agregar manualmente, solo desde la API
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_formatted_price_display', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('name', 'price', 'description', 'is_active')
        }),
        ('Información del Sistema', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_formatted_price_display(self, obj):
        """Muestra el precio formateado con moneda en el admin"""
        return obj.get_formatted_price()
    get_formatted_price_display.short_description = 'Precio'
    get_formatted_price_display.admin_order_field = 'price'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============= ADMINISTRACIÓN DE ASISTENCIA DE CLIENTE =============

@admin.register(ClientProjectAccess)
class ClientProjectAccessAdmin(admin.ModelAdmin):
    list_display = ('project', 'is_active_badge', 'max_entries_per_day', 'categories_list', 'entries_count', 'created_at')
    list_filter = ('is_active', 'requires_phone', 'created_at')
    search_fields = ('project__name', 'public_token')
    ordering = ('-created_at',)
    readonly_fields = ('public_token', 'created_at', 'updated_at', 'public_url_display')
    
    fieldsets = (
        ('Configuración del Proyecto', {
            'fields': ('project', 'is_active', 'public_token', 'public_url_display')
        }),
        ('Límites y Restricciones', {
            'fields': ('max_entries_per_day', 'requires_phone', 'allowed_categories')
        }),
        ('Información Adicional', {
            'fields': ('instructions',),
            'classes': ('wide',)
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        """Muestra un badge de estado"""
        if obj.is_active:
            return format_html('<span class="badge bg-success">Activo</span>')
        return format_html('<span class="badge bg-danger">Inactivo</span>')
    is_active_badge.short_description = 'Estado'
    
    def categories_list(self, obj):
        """Muestra las categorías permitidas"""
        if obj.allowed_categories:
            categories = [cat.title() for cat in obj.allowed_categories]
            return ', '.join(categories)
        return 'Ninguna'
    categories_list.short_description = 'Categorías'
    
    def entries_count(self, obj):
        """Muestra el conteo de entradas"""
        count = obj.project.client_time_entries.count()
        return format_html('<span class="badge bg-info">{}</span>', count)
    entries_count.short_description = 'Entradas'
    
    def public_url_display(self, obj):
        """Muestra la URL pública para copiar"""
        if obj.public_token:
            from django.urls import reverse
            from django.contrib.sites.models import Site
            try:
                current_site = Site.objects.get_current()
                url = f"http://{current_site.domain}{reverse('client_time_entry_form', kwargs={'token': obj.public_token})}"
                return format_html('<a href="{}" target="_blank">{}</a>', url, url)
            except:
                return f"/client-hours/{obj.public_token}/"
        return "Token no generado"
    public_url_display.short_description = 'URL Pública'


@admin.register(ClientTimeEntry)
class ClientTimeEntryAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_email', 'project', 'hours_badge', 'category_badge', 'entry_date', 'created_at', 'client_location')
    list_filter = ('category', 'project', 'entry_date', 'created_at')
    search_fields = ('client_name', 'client_email', 'client_phone', 'project__name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('client_ip', 'user_agent', 'created_at', 'updated_at')
    date_hierarchy = 'entry_date'
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('client_name', 'client_email', 'client_phone')
        }),
        ('Información del Registro', {
            'fields': ('project', 'hours', 'category', 'entry_date', 'description')
        }),
        ('Información Técnica', {
            'fields': ('client_ip', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def hours_badge(self, obj):
        """Muestra las horas como badge"""
        return format_html('<span class="badge bg-primary">{}</span>', obj.get_formatted_hours())
    hours_badge.short_description = 'Horas'
    hours_badge.admin_order_field = 'hours'
    
    def category_badge(self, obj):
        """Muestra la categoría como badge"""
        colors = {
            'capacitacion': 'bg-info',
            'pruebas': 'bg-warning',
            'uso': 'bg-success'
        }
        color = colors.get(obj.category, 'bg-secondary')
        return format_html('<span class="badge {}">{}</span>', color, obj.get_category_display())
    category_badge.short_description = 'Categoría'
    category_badge.admin_order_field = 'category'
    
    def client_location(self, obj):
        """Muestra información de ubicación del cliente"""
        info = []
        if obj.client_ip:
            info.append(f"IP: {obj.client_ip}")
        if obj.user_agent:
            if 'Mobile' in obj.user_agent:
                info.append("📱 Móvil")
            elif 'Chrome' in obj.user_agent:
                info.append("🌐 Chrome")
            elif 'Safari' in obj.user_agent:
                info.append("🌐 Safari")
            elif 'Firefox' in obj.user_agent:
                info.append("🌐 Firefox")
        return ' | '.join(info) if info else 'No disponible'
    client_location.short_description = 'Ubicación/Navegador'



# ============= ADMIN PARA DOCUMENTACIONES DE EMPRESAS =============

class CompanyDocumentationURLInline(admin.TabularInline):
    model = CompanyDocumentationURL
    extra = 1
    fields = ['title', 'url', 'description', 'username', 'password', 'is_active', 'order']

@admin.register(CompanyDocumentation)
class CompanyDocumentationAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'is_public', 'created_by', 'created_at', 'url_count']
    list_filter = ['is_public', 'company', 'created_at']
    search_fields = ['title', 'description', 'company__name']
    inlines = [CompanyDocumentationURLInline]
    readonly_fields = ['public_token', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'company', 'created_by')
        }),
        ('Configuración', {
            'fields': ('is_public', 'public_token')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def url_count(self, obj):
        return obj.urls.count()
    url_count.short_description = 'URLs'
    
    def get_public_url(self, obj):
        if obj.is_public:
            return format_html('<a href="{}" target="_blank">Ver público</a>', obj.get_public_url())
        return "No público"
    get_public_url.short_description = 'Enlace público'

@admin.register(CompanyDocumentationURL)
class CompanyDocumentationURLAdmin(admin.ModelAdmin):
    list_display = ['title', 'documentation', 'url', 'has_credentials', 'is_active', 'order']
    list_filter = ['is_active', 'documentation__company']
    search_fields = ['title', 'url', 'description', 'documentation__title']
    list_editable = ['is_active', 'order']
    
    def has_credentials(self, obj):
        return obj.has_credentials()
    has_credentials.boolean = True
    has_credentials.short_description = 'Tiene credenciales'


@admin.register(ContactGenerator)
class ContactGeneratorAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'is_active', 'contacts_count', 'created_by', 'created_at']
    list_filter = ['is_active', 'company', 'collect_phone', 'collect_company', 'collect_position', 'collect_notes']
    search_fields = ['title', 'description', 'company__name']
    list_editable = ['is_active']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'company', 'is_active')
        }),
        ('Configuración de Campos', {
            'fields': ('collect_phone', 'collect_company', 'collect_position', 'collect_notes')
        }),
        ('Mensajes', {
            'fields': ('welcome_message', 'success_message')
        }),
        ('Diseño', {
            'fields': ('background_color',)
        }),
        ('Sistema', {
            'fields': ('public_token', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['public_token', 'created_by']
    
    def contacts_count(self, obj):
        return obj.get_contacts_count()
    contacts_count.short_description = 'Contactos Generados'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un objeto nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CompanyRequestGenerator)
class CompanyRequestGeneratorAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'is_active', 'requests_count', 'created_by', 'created_at']
    list_filter = ['is_active', 'company']
    search_fields = ['title', 'description', 'company__name']
    list_editable = ['is_active']
    ordering = ['-created_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'company', 'is_active')
        }),
        ('Secuencia', {
            'fields': ('sequence_prefix', 'next_sequence')
        }),
        ('Configuración de Campos', {
            'fields': ('collect_date', 'collect_text', 'collect_url')
        }),
        ('Mensajes', {
            'fields': ('welcome_message', 'success_message')
        }),
        ('Sistema', {
            'fields': ('public_token', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['public_token', 'created_by']

    def requests_count(self, obj):
        return obj.get_requests_count()
    requests_count.short_description = 'Solicitudes Enviadas'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CompanyRequest)
class CompanyRequestAdmin(admin.ModelAdmin):
    list_display = ['sequence', 'generator', 'status', 'request_date', 'executed_at', 'executed_by', 'created_at']
    list_filter = ['status', 'generator__company', 'executed_by']
    search_fields = ['sequence', 'text', 'generator__title']
    readonly_fields = ['executed_at', 'executed_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('sequence', 'generator', 'text', 'url', 'status')
        }),
        ('Fechas', {
            'fields': ('request_date', 'created_at', 'updated_at')
        }),
        ('Ejecución', {
            'fields': ('executed_at', 'executed_by'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )


@admin.register(CompanyRequestComment)
class CompanyRequestCommentAdmin(admin.ModelAdmin):
    list_display = ['request', 'user', 'created_at']
    search_fields = ['request__sequence', 'user__username', 'content']


# ============= ADMIN PARA SISTEMA DE FORMULARIOS =============

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'is_active', 'questions_count', 'responses_count', 'average_score', 'created_at']
    list_filter = ['is_active', 'company', 'created_at', 'created_by']
    search_fields = ['title', 'description', 'company__name']
    readonly_fields = ['public_token', 'created_by', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('title', 'description', 'company', 'is_active')
        }),
        ('Sistema', {
            'fields': ('public_token', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Preguntas'

    def responses_count(self, obj):
        return obj.get_total_responses()
    responses_count.short_description = 'Respuestas'

    def average_score(self, obj):
        return obj.get_average_score()
    average_score.short_description = 'Puntuación Promedio'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class FormQuestionOptionInline(admin.TabularInline):
    model = FormQuestionOption
    extra = 0
    fields = ['option_text', 'score', 'order']


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    list_display = ['form', 'question_text_short', 'question_type', 'is_required', 'order', 'options_count']
    list_filter = ['question_type', 'is_required', 'form__company']
    search_fields = ['question_text', 'form__title']
    ordering = ['form', 'order']
    inlines = [FormQuestionOptionInline]
    
    fieldsets = (
        ('Pregunta', {
            'fields': ('form', 'question_text', 'question_type', 'is_required', 'order')
        }),
    )

    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Pregunta'

    def options_count(self, obj):
        return obj.options.count() if obj.question_type == 'multiple_choice' else '-'
    options_count.short_description = 'Opciones'


@admin.register(FormQuestionOption)
class FormQuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['question_short', 'option_text', 'score', 'order']
    list_filter = ['question__question_type', 'question__form__company']
    search_fields = ['option_text', 'question__question_text', 'question__form__title']
    ordering = ['question', 'order']
    
    def question_short(self, obj):
        return obj.question.question_text[:30] + '...' if len(obj.question.question_text) > 30 else obj.question.question_text
    question_short.short_description = 'Pregunta'


class FormAnswerInline(admin.TabularInline):
    model = FormAnswer
    extra = 0
    readonly_fields = ['question', 'text_answer', 'number_answer', 'selected_option']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ['form', 'respondent_name', 'respondent_email', 'total_score', 'response_date']
    list_filter = ['form__company', 'form', 'response_date']
    search_fields = ['respondent_name', 'respondent_email', 'form__title']
    readonly_fields = ['form', 'total_score', 'response_date']
    ordering = ['-response_date']
    inlines = [FormAnswerInline]
    
    fieldsets = (
        ('Información del Encuestado', {
            'fields': ('respondent_name', 'respondent_email')
        }),
        ('Respuesta', {
            'fields': ('form', 'total_score', 'response_date')
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(FormAnswer)
class FormAnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question_short', 'answer_display', 'score_earned']
    list_filter = ['question__question_type', 'response__form__company']
    search_fields = ['response__respondent_name', 'question__question_text', 'text_answer']
    readonly_fields = ['response', 'question', 'text_answer', 'number_answer', 'selected_option']
    ordering = ['-response__response_date']

    def question_short(self, obj):
        return obj.question.question_text[:30] + '...' if len(obj.question.question_text) > 30 else obj.question.question_text
    question_short.short_description = 'Pregunta'

    def answer_display(self, obj):
        return obj.get_answer_display()
    answer_display.short_description = 'Respuesta'

    def score_earned(self, obj):
        return obj.selected_option.score if obj.selected_option else 0
    score_earned.short_description = 'Puntos'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Alcance)
class AlcanceAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'publico', 'creado_por', 'creado_en']
    list_filter = ['publico', 'categoria', 'creado_en']
    search_fields = ['titulo', 'categoria', 'descripcion']
    readonly_fields = ['creado_en', 'actualizado_en', 'creado_por']
    ordering = ['-creado_en']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'categoria', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('publico',)
        }),
        ('Metadata', {
            'fields': ('creado_por', 'creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

