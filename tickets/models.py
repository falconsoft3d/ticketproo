from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text='Color en formato hexadecimal (ej: #007bff)',
        verbose_name='Color'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
    
    def __str__(self):
        return self.name


class Company(models.Model):
    """Modelo para gestionar empresas/clientes"""
    
    name = models.CharField(
        max_length=200, 
        unique=True, 
        verbose_name='Nombre de la Empresa'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Descripción',
        help_text='Descripción opcional de la empresa'
    )
    address = models.CharField(
        max_length=300, 
        blank=True, 
        verbose_name='Dirección'
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='Teléfono'
    )
    email = models.EmailField(
        blank=True, 
        verbose_name='Email de contacto'
    )
    website = models.URLField(
        blank=True, 
        verbose_name='Sitio web'
    )
    color = models.CharField(
        max_length=7, 
        default='#28a745',
        help_text='Color en formato hexadecimal (ej: #28a745)',
        verbose_name='Color identificativo'
    )
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        verbose_name='Logo de la empresa',
        help_text='Logo de la empresa (opcional)'
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name='Empresa activa'
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Última actualización'
    )
    public_token = models.UUIDField(
        null=True,
        blank=True,
        editable=True,
        verbose_name='Token público',
        help_text='Token único para acceso público a estadísticas'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.name
    
    def get_active_tickets_count(self):
        """Obtiene el número de tickets activos de la empresa"""
        return self.tickets.exclude(status='closed').count()
    
    def get_total_tickets_count(self):
        """Obtiene el total de tickets de la empresa"""
        return self.tickets.count()
    
    def get_users_count(self):
        """Obtiene el número de usuarios asociados a la empresa"""
        return self.users.count()
    
    def get_public_stats(self):
        """Obtiene estadísticas públicas de la empresa"""
        from django.db.models import Count, Q
        
        tickets = self.tickets.all()
        
        return {
            'total_tickets': tickets.count(),
            'open_tickets': tickets.filter(status='open').count(),
            'in_progress_tickets': tickets.filter(status='in_progress').count(),
            'closed_tickets': tickets.filter(status='closed').count(),
            'high_priority': tickets.filter(priority='high').count(),
            'medium_priority': tickets.filter(priority='medium').count(),
            'low_priority': tickets.filter(priority='low').count(),
            'users_count': self.get_users_count(),
            'last_ticket_date': tickets.order_by('-created_at').first().created_at if tickets.exists() else None,
        }
    
    def regenerate_public_token(self):
        """Regenera el token público para acceso a estadísticas"""
        self.public_token = uuid.uuid4()
        self.save()
        return self.public_token


class Project(models.Model):
    """Modelo para gestionar proyectos de trabajo"""
    
    STATUS_CHOICES = [
        ('planning', 'Planificación'),
        ('active', 'Activo'),
        ('on_hold', 'En Pausa'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    name = models.CharField(max_length=200, unique=True, verbose_name='Nombre del Proyecto')
    description = models.TextField(blank=True, verbose_name='Descripción')
    color = models.CharField(
        max_length=7, 
        default='#28a745',
        help_text='Color en formato hexadecimal (ej: #28a745)',
        verbose_name='Color'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active', 
        verbose_name='Estado'
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='Fecha de Inicio')
    end_date = models.DateField(null=True, blank=True, verbose_name='Fecha de Fin')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_projects',
        verbose_name='Creado por'
    )
    assigned_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='assigned_projects',
        verbose_name='Usuarios Asignados',
        help_text='Usuarios que tienen acceso a este proyecto'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    public_share_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Token de Compartir Público',
        help_text='Token único para compartir información del proyecto públicamente'
    )
    
    class Meta:
        ordering = ['-created_at', 'name']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
    
    def __str__(self):
        return self.name
    
    def get_total_hours(self):
        """Obtiene el total de horas trabajadas en este proyecto"""
        from django.db.models import F, Sum, Case, When, Value
        from django.db.models.functions import Extract
        
        # Calcular la duración en segundos para cada entrada
        total_seconds = 0
        
        for entry in self.time_entries.all():
            if entry.fecha_salida:
                # Entrada completada
                duration = (entry.fecha_salida - entry.fecha_entrada).total_seconds()
            else:
                # Entrada activa
                duration = (timezone.now() - entry.fecha_entrada).total_seconds()
            total_seconds += duration
        
        # Convertir a horas y redondear
        return round(total_seconds / 3600, 2)
    
    def get_active_workers_count(self):
        """Obtiene el número de trabajadores actualmente trabajando en este proyecto"""
        return self.time_entries.filter(fecha_salida__isnull=True).count()
    
    def can_edit(self, user):
        """Verifica si el usuario puede editar este proyecto"""
        from .utils import is_agent
        return is_agent(user) or user == self.created_by
    
    def can_delete(self, user):
        """Verifica si el usuario puede eliminar este proyecto"""
        from .utils import is_agent
        return is_agent(user) or user == self.created_by
    
    def generate_public_share_token(self):
        """Genera un token único para compartir el proyecto públicamente"""
        if not self.public_share_token:
            import secrets
            self.public_share_token = secrets.token_urlsafe(32)
            self.save()
        return self.public_share_token
    
    def get_public_share_url(self):
        """Obtiene la URL pública para compartir el proyecto"""
        if not self.public_share_token:
            self.generate_public_share_token()
        return f"/public/project/{self.public_share_token}/"
    
    def get_tickets_count(self):
        """Obtiene el total de tickets relacionados con este proyecto"""
        from django.db.models import Q
        
        # Usar Q objects para obtener tickets únicos (directamente asignados O en time_entries)
        tickets_ids = set()
        
        # Tickets directamente asignados al proyecto
        direct_tickets = self.tickets.values_list('id', flat=True)
        tickets_ids.update(direct_tickets)
        
        # Tickets de time_entries
        time_entry_tickets = self.time_entries.filter(
            ticket__isnull=False
        ).values_list('ticket_id', flat=True)
        tickets_ids.update(time_entry_tickets)
        
        return len(tickets_ids)
    
    def get_resolved_tickets_count(self):
        """Obtiene el total de tickets resueltos relacionados con este proyecto"""
        from django.db.models import Q
        
        # Usar Q objects para obtener tickets únicos resueltos
        resolved_tickets_ids = set()
        
        # Tickets directamente asignados y resueltos
        direct_resolved = self.tickets.filter(
            status__in=['resolved', 'closed']
        ).values_list('id', flat=True)
        resolved_tickets_ids.update(direct_resolved)
        
        # Tickets resueltos de time_entries
        time_entry_resolved = self.time_entries.filter(
            ticket__isnull=False,
            ticket__status__in=['resolved', 'closed']
        ).values_list('ticket_id', flat=True)
        resolved_tickets_ids.update(time_entry_resolved)
        
        return len(resolved_tickets_ids)
    
    def get_completed_work_orders_count(self):
        """Obtiene el total de órdenes de trabajo completadas relacionadas con este proyecto"""
        # Contar órdenes directamente asignadas y completadas
        direct_completed = self.work_orders.filter(status='finished').count()
        
        # Contar órdenes completadas de time_entries
        time_entry_completed = self.time_entries.filter(
            work_order__isnull=False,
            work_order__status='finished'
        ).values('work_order').distinct().count()
        
        # Usar set para eliminar duplicados
        completed_orders_ids = set()
        
        # Órdenes directamente asignadas y completadas
        direct_orders = self.work_orders.filter(
            status='finished'
        ).values_list('id', flat=True)
        completed_orders_ids.update(direct_orders)
        
        # Órdenes completadas de time_entries
        time_entry_orders = self.time_entries.filter(
            work_order__isnull=False,
            work_order__status='finished'
        ).values_list('work_order_id', flat=True)
        completed_orders_ids.update(time_entry_orders)
        
        return len(completed_orders_ids)
    
    def get_project_workers(self):
        """Obtiene los usuarios que han trabajado en este proyecto con sus datos de contacto"""
        from django.db.models import Q
        workers = User.objects.filter(
            time_entries__project=self
        ).distinct().select_related('profile')
        
        return workers
    
    def get_total_cost(self):
        """Calcula el coste total del proyecto basado en las horas trabajadas y el coste por hora de cada empleado"""
        from decimal import Decimal
        total_cost = Decimal('0.00')
        
        for entry in self.time_entries.all():
            hours_worked = entry.horas_trabajadas
            if hours_worked and entry.user and hasattr(entry.user, 'profile'):
                coste_hora = entry.user.profile.coste_hora
                total_cost += Decimal(str(hours_worked)) * coste_hora
        
        return total_cost
    
    def get_total_revenue(self):
        """Calcula el total de venta del proyecto basado en las horas trabajadas y el precio por hora de cada empleado"""
        from decimal import Decimal
        total_revenue = Decimal('0.00')
        
        for entry in self.time_entries.all():
            hours_worked = entry.horas_trabajadas
            if hours_worked and entry.user and hasattr(entry.user, 'profile'):
                precio_hora = entry.user.profile.precio_hora
                total_revenue += Decimal(str(hours_worked)) * precio_hora
        
        return total_revenue
    
    def get_profit(self):
        """Calcula el beneficio del proyecto (venta - coste)"""
        return self.get_total_revenue() - self.get_total_cost()
    
    def get_profit_margin(self):
        """Calcula el margen de beneficio como porcentaje"""
        revenue = self.get_total_revenue()
        if revenue > 0:
            return (self.get_profit() / revenue) * 100
        return 0


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('in_progress', 'En Progreso'),
        ('resolved', 'Resuelto'),
        ('closed', 'Cerrado'),
    ]
    
    TYPE_CHOICES = [
        ('desarrollo', 'Desarrollo'),
        ('error', 'Error'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título')
    ticket_number = models.CharField(
        max_length=10, 
        unique=True,
        blank=True,
        verbose_name='Número de Ticket',
        help_text='Formato: XX-XXX (ID Usuario-Secuencia)'
    )
    description = models.TextField(verbose_name='Descripción')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='Categoría'
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='Empresa/Cliente',
        help_text='Empresa o cliente asociado al ticket'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='Proyecto',
        help_text='Proyecto asociado al ticket (opcional)'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name='Prioridad'
    )
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='open',
        verbose_name='Estado'
    )
    ticket_type = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default='desarrollo',
        verbose_name='Tipo'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tickets',
        verbose_name='Creado por'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tickets',
        verbose_name='Asignado a'
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Horas estimadas/trabajadas',
        help_text='Cantidad de horas estimadas o trabajadas en el ticket'
    )
    # Campo para enlace único público
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de compartir',
        help_text='Token único para compartir el ticket públicamente'
    )
    is_public_shareable = models.BooleanField(
        default=False,
        verbose_name='Compartir públicamente',
        help_text='Permite que este ticket sea visible mediante un enlace público'
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name='Aprobado',
        help_text='Indica si el ticket ha sido aprobado por el cliente'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tickets',
        verbose_name='Aprobado por',
        help_text='Usuario que aprobó el ticket'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación',
        help_text='Fecha y hora en que fue aprobado el ticket'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
    
    def generate_ticket_number(self):
        """Genera un número de ticket único con formato XX-XXX"""
        if self.ticket_number:
            return self.ticket_number
            
        # Formatear ID del usuario con ceros a la izquierda (2 dígitos)
        user_id_formatted = f"{self.created_by.id:02d}"
        
        # Buscar el último ticket creado por este usuario
        last_ticket = Ticket.objects.filter(
            created_by=self.created_by,
            ticket_number__startswith=f"{user_id_formatted}-"
        ).exclude(id=self.id).order_by('-ticket_number').first()
        
        if last_ticket and last_ticket.ticket_number:
            # Extraer el número de secuencia del último ticket
            try:
                last_sequence = int(last_ticket.ticket_number.split('-')[1])
                new_sequence = last_sequence + 1
            except (IndexError, ValueError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Formatear secuencia con ceros a la izquierda (3 dígitos)
        sequence_formatted = f"{new_sequence:03d}"
        
        return f"{user_id_formatted}-{sequence_formatted}"
    
    def save(self, *args, **kwargs):
        """Override del método save para generar número de ticket automáticamente"""
        is_new_ticket = self.pk is None
        
        if not self.ticket_number:
            # Usar transacción para evitar condiciones de carrera
            with transaction.atomic():
                self.ticket_number = self.generate_ticket_number()
                # Verificar que el número sea único (por si acaso)
                counter = 1
                original_number = self.ticket_number
                while Ticket.objects.filter(ticket_number=self.ticket_number).exists():
                    user_id_formatted = f"{self.created_by.id:02d}"
                    sequence_num = int(original_number.split('-')[1]) + counter
                    self.ticket_number = f"{user_id_formatted}-{sequence_num:03d}"
                    counter += 1
        
        super().save(*args, **kwargs)
        
        # Enviar notificación de Telegram solo para tickets nuevos
        if is_new_ticket:
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Ticket nuevo creado: {self.ticket_number}, iniciando notificación Telegram")
                
                from .telegram_utils import notify_ticket_created
                result = notify_ticket_created(self)
                logger.info(f"Resultado notificación Telegram: {result}")
            except Exception as e:
                # No queremos que falle la creación del ticket si falla la notificación
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al enviar notificación de Telegram para ticket {self.ticket_number}: {e}")
                import traceback
                logger.error(f"Traceback completo: {traceback.format_exc()}")
    
    def __str__(self):
        if self.ticket_number:
            return f"{self.ticket_number} - {self.title}"
        return f"#{self.id} - {self.title}"
    
    def get_priority_badge_class(self):
        """Retorna la clase CSS para el badge de prioridad"""
        priority_classes = {
            'low': 'bg-success',
            'medium': 'bg-warning',
            'high': 'bg-danger',
            'urgent': 'bg-dark',
        }
        return priority_classes.get(self.priority, 'bg-secondary')
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            'open': 'bg-primary',
            'in_progress': 'bg-warning',
            'resolved': 'bg-success',
            'closed': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_type_badge_class(self):
        """Retorna la clase CSS para el badge de tipo"""
        type_classes = {
            'desarrollo': 'bg-info',
            'error': 'bg-danger',
        }
        return type_classes.get(self.ticket_type, 'bg-secondary')
    
    def get_age_in_hours(self):
        """Retorna la antigüedad del ticket en horas"""
        from django.utils import timezone
        now = timezone.now()
        time_diff = now - self.created_at
        return time_diff.total_seconds() / 3600
    
    def get_age_badge_class(self):
        """Retorna la clase CSS para el badge de antigüedad según las horas"""
        hours = self.get_age_in_hours()
        if hours < 72:  # Menos de 72 horas - Verde
            return 'bg-success'
        elif hours <= 140:  # Entre 72 y 140 horas - Naranja
            return 'bg-warning'
        else:  # Más de 140 horas - Rojo
            return 'bg-danger'
    
    def get_age_display(self):
        """Retorna la antigüedad formateada para mostrar"""
        hours = self.get_age_in_hours()
        if hours < 24:
            return f"{int(hours)}h"
        elif hours < 72:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            if remaining_hours > 0:
                return f"{days}d {remaining_hours}h"
            else:
                return f"{days}d"
        else:
            days = int(hours / 24)
            return f"{days}d"
    
    def get_public_url(self):
        """Retorna la URL pública del ticket si está habilitado para compartir"""
        if self.is_public_shareable:
            from django.urls import reverse
            return reverse('tickets:public_ticket', kwargs={'token': self.public_share_token})
        return None
    
    def regenerate_public_token(self):
        """Regenera el token público del ticket"""
        self.public_share_token = uuid.uuid4()
        self.save(update_fields=['public_share_token'])
    
    def approve_ticket(self, user):
        """Aprobar el ticket por un usuario"""
        from django.utils import timezone
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])
    
    def unapprove_ticket(self):
        """Quitar la aprobación del ticket"""
        self.is_approved = False
        self.approved_by = None
        self.approved_at = None
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])


def ticket_attachment_upload_path(instance, filename):
    """Función para determinar dónde subir los adjuntos"""
    return f'ticket_attachments/ticket_{instance.ticket.id}/{filename}'


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(
        Ticket, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name='Ticket'
    )
    file = models.FileField(
        upload_to=ticket_attachment_upload_path,
        verbose_name='Archivo'
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name='Nombre original'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Subido por'
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de subida'
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='Tamaño del archivo (bytes)'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Adjunto'
        verbose_name_plural = 'Adjuntos'
    
    def __str__(self):
        return f"{self.original_filename} - Ticket #{self.ticket.id}"
    
    def get_file_size_display(self):
        """Retorna el tamaño del archivo en formato legible"""
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def get_file_extension(self):
        """Retorna la extensión del archivo"""
        return os.path.splitext(self.original_filename)[1].lower()
    
    def delete(self, *args, **kwargs):
        """Elimina el archivo físico cuando se elimina el registro"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class TicketComment(models.Model):
    """Modelo para comentarios en tickets"""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Ticket'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    content = models.TextField(
        verbose_name='Comentario',
        help_text='Escribe tu comentario aquí'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
    
    def __str__(self):
        return f"Comentario de {self.user.username} en Ticket #{self.ticket.ticket_number}"
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar este comentario"""
        # Solo el autor del comentario o un agente puede editarlo
        from .utils import is_agent
        return self.user == user or is_agent(user)
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar este comentario"""
        # Solo el autor del comentario o un agente puede eliminarlo
        from .utils import is_agent
        return self.user == user or is_agent(user)


class UserProfile(models.Model):
    """Modelo para extender la información del usuario"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono',
        help_text='Número de teléfono de contacto'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biografía',
        help_text='Descripción corta del usuario'
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cargo',
        help_text='Cargo o posición del usuario en la empresa'
    )
    descripcion_cargo = models.TextField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name='Descripción del Cargo',
        help_text='Descripción detallada de las responsabilidades del cargo'
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Preferencias de notificación',
        help_text='Configuración de notificaciones del usuario'
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Empresa',
        help_text='Empresa a la que pertenece el usuario'
    )
    
    # Campos de facturación
    precio_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Precio por hora',
        help_text='Precio de venta por hora de trabajo (€)'
    )
    coste_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Coste por hora',
        help_text='Coste interno por hora de trabajo (€)'
    )
    
    # Token para acceso público a tareas
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name='Token público',
        help_text='Token único para acceso público a tareas'
    )
    
    # Formulario de contacto público
    enable_public_contact_form = models.BooleanField(
        default=False,
        verbose_name='Activar formulario de contacto público',
        help_text='Permite que visitantes envíen formularios de contacto para crear empresas'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    def get_total_hours(self):
        """Retorna el total de horas trabajadas por el usuario"""
        from datetime import timedelta
        total_minutes = 0
        for entry in self.user.time_entries.filter(fecha_salida__isnull=False):
            total_minutes += entry.duracion_trabajada
        return round(total_minutes / 60, 1)
    
    def get_monthly_hours(self):
        """Retorna las horas trabajadas en el mes actual"""
        from datetime import datetime, timedelta
        now = timezone.now()
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_minutes = 0
        entries = self.user.time_entries.filter(
            fecha_entrada__gte=start_month,
            fecha_salida__isnull=False
        )
        for entry in entries:
            total_minutes += entry.duracion_trabajada
        return round(total_minutes / 60, 1)
    
    def get_weekly_hours(self):
        """Retorna las horas trabajadas en esta semana"""
        from datetime import datetime, timedelta
        now = timezone.now()
        # Calcular el inicio de la semana (lunes)
        start_week = now - timedelta(days=now.weekday())
        start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_minutes = 0
        entries = self.user.time_entries.filter(
            fecha_entrada__gte=start_week,
            fecha_salida__isnull=False
        )
        for entry in entries:
            total_minutes += entry.duracion_trabajada
        return round(total_minutes / 60, 1)
    
    def get_daily_hours(self):
        """Retorna las horas trabajadas hoy"""
        from datetime import datetime
        today = timezone.now().date()
        
        total_minutes = 0
        entries = self.user.time_entries.filter(
            fecha_entrada__date=today,
            fecha_salida__isnull=False
        )
        for entry in entries:
            total_minutes += entry.duracion_trabajada
            
        # También incluir sesión activa si existe
        active_entry = self.user.time_entries.filter(
            fecha_entrada__date=today,
            fecha_salida__isnull=True
        ).first()
        
        if active_entry:
            total_minutes += active_entry.duracion_trabajada
            
        return round(total_minutes / 60, 1)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        elif self.user.first_name:
            return self.user.first_name
        else:
            return self.user.username

    def regenerate_token(self):
        """Regenera el token público"""
        self.public_token = uuid.uuid4()
        self.save()
        return self.public_token


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


class UserNote(models.Model):
    """Modelo para notas internas asociadas a usuarios"""
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo de la nota'
    )
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Contenido detallado de la nota'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Usuario asociado',
        help_text='Usuario al que está asociada esta nota'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_notes',
        verbose_name='Creado por',
        help_text='Agente que creó la nota'
    )
    tickets = models.ManyToManyField(
        Ticket,
        blank=True,
        related_name='notes',
        verbose_name='Tickets relacionados',
        help_text='Tickets asociados a esta nota'
    )
    is_private = models.BooleanField(
        default=True,
        verbose_name='Nota privada',
        help_text='Si está marcada, solo será visible para agentes'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nota de Usuario'
        verbose_name_plural = 'Notas de Usuario'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def can_view(self, user):
        """Verifica si un usuario puede ver esta nota"""
        from .utils import is_agent
        # Los agentes pueden ver todas las notas
        if is_agent(user):
            return True
        # Si la nota no es privada, el usuario asociado puede verla
        if not self.is_private and self.user == user:
            return True
        return False
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar esta nota"""
        from .utils import is_agent
        # Solo los agentes pueden crear/editar notas
        return is_agent(user)
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar esta nota"""
        from .utils import is_agent
        # Solo los agentes pueden eliminar notas
        return is_agent(user)
    
    def get_related_tickets_count(self):
        """Retorna el número de tickets relacionados"""
        return self.tickets.count()
    
    def get_tickets_summary(self):
        """Retorna un resumen de los tickets relacionados"""
        tickets = self.tickets.all()[:3]  # Mostrar máximo 3 tickets
        if tickets:
            summary = ', '.join([f"#{ticket.ticket_number}" for ticket in tickets])
            remaining = self.tickets.count() - 3
            if remaining > 0:
                summary += f" y {remaining} más"
            return summary
        return "Sin tickets asociados"


class TimeEntry(models.Model):
    """Modelo para registrar entrada y salida de trabajo de empleados (agentes)"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Empleado'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Proyecto',
        null=True,
        blank=True
    )
    ticket = models.ForeignKey(
        'Ticket',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Ticket',
        null=True,
        blank=True,
        help_text='Ticket en el que se trabajará (opcional)'
    )
    work_order = models.ForeignKey(
        'WorkOrder',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Orden de Trabajo',
        null=True,
        blank=True,
        help_text='Orden de trabajo en la que se trabajará (opcional)'
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Tarea',
        null=True,
        blank=True,
        help_text='Tarea en la que se trabajará (opcional)'
    )
    fecha_entrada = models.DateTimeField(
        verbose_name='Fecha y hora de entrada'
    )
    fecha_salida = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha y hora de salida'
    )
    notas = models.TextField(
        blank=True,
        max_length=500,
        verbose_name='Notas',
        help_text='Comentarios opcionales sobre la jornada'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Registrado el'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-fecha_entrada']
        verbose_name = 'Registro de Horario'
        verbose_name_plural = 'Registros de Horario'
        unique_together = ['user', 'fecha_entrada']
    
    def __str__(self):
        fecha = self.fecha_entrada.strftime('%d/%m/%Y')
        estado = "Activo" if not self.fecha_salida else "Completado"
        return f"{self.user.username} - {fecha} ({estado})"
    
    @property
    def is_active(self):
        """Verifica si el registro está activo (sin fecha de salida)"""
        return self.fecha_salida is None
    
    @property
    def duracion_trabajada(self):
        """Calcula la duración trabajada en minutos"""
        if not self.fecha_salida:
            # Si aún está trabajando, calcular desde entrada hasta ahora
            return int((timezone.now() - self.fecha_entrada).total_seconds() / 60)
        return int((self.fecha_salida - self.fecha_entrada).total_seconds() / 60)
    
    @property
    def duracion_formateada(self):
        """Retorna la duración en formato HH:MM"""
        minutos = self.duracion_trabajada
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas:02d}:{mins:02d}"
    
    @property
    def horas_trabajadas(self):
        """Retorna las horas trabajadas como decimal"""
        return round(self.duracion_trabajada / 60, 2)
    
    def can_view(self, user):
        """Verifica si un usuario puede ver este registro"""
        from .utils import is_agent
        # Solo los agentes pueden ver registros de horario
        if not is_agent(user):
            return False
        # Los agentes pueden ver solo sus propios registros
        return self.user == user
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar este registro"""
        from .utils import is_agent
        # Solo el propietario del registro puede editarlo
        return is_agent(user) and self.user == user
    
    def finalizar_jornada(self, notas_salida=None):
        """Marca la salida de la jornada laboral"""
        if self.fecha_salida:
            raise ValueError("Esta jornada ya ha sido finalizada")
        
        self.fecha_salida = timezone.now()
        if notas_salida:
            self.notas = notas_salida
        self.save()
        return self
    
    @classmethod
    def get_active_entry(cls, user):
        """Obtiene el registro activo (sin salida) de un usuario"""
        from .utils import is_agent
        if not is_agent(user):
            return None
        return cls.objects.filter(user=user, fecha_salida__isnull=True).first()
    
    @classmethod
    def create_entry(cls, user, project=None, ticket=None, work_order=None, task=None, notas_entrada=None):
        """Crea un nuevo registro de entrada"""
        from .utils import is_agent
        if not is_agent(user):
            raise ValueError("Solo los agentes pueden registrar horarios")
        
        # Verificar que no haya una entrada activa
        active_entry = cls.get_active_entry(user)
        if active_entry:
            raise ValueError("Ya tienes una jornada activa. Finalízala antes de crear una nueva.")
        
        return cls.objects.create(
            user=user,
            project=project,
            ticket=ticket,
            work_order=work_order,
            task=task,
            fecha_entrada=timezone.now(),
            notas=notas_entrada or ''
        )


class SystemConfiguration(models.Model):
    """Modelo para configuraciones generales del sistema"""
    
    # Configuración de registro de usuarios
    allow_user_registration = models.BooleanField(
        default=True,
        verbose_name='Permitir registro de usuarios',
        help_text='Permite que nuevos usuarios se registren en el sistema'
    )
    
    # Configuraciones adicionales que se pueden agregar en el futuro
    site_name = models.CharField(
        max_length=100,
        default='TicketPro',
        verbose_name='Nombre del sitio',
        help_text='Nombre que aparece en el encabezado del sistema'
    )
    
    # Configuraciones de tickets
    default_ticket_priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente')
        ],
        default='medium',
        verbose_name='Prioridad por defecto de tickets',
        help_text='Prioridad asignada automáticamente a nuevos tickets'
    )
    
    # Configuración de moneda
    default_currency = models.CharField(
        max_length=10,
        choices=[
            ('EUR', 'Euro (€)'),
            ('USD', 'Dólar Americano ($)'),
            ('GBP', 'Libra Esterlina (£)'),
            ('JPY', 'Yen Japonés (¥)'),
            ('CAD', 'Dólar Canadiense (C$)'),
            ('AUD', 'Dólar Australiano (A$)'),
            ('CHF', 'Franco Suizo (CHF)'),
            ('CNY', 'Yuan Chino (¥)'),
            ('MXN', 'Peso Mexicano ($)'),
            ('COP', 'Peso Colombiano ($)'),
        ],
        default='EUR',
        verbose_name='Moneda por defecto',
        help_text='Moneda utilizada para mostrar valores en el sistema'
    )
    
    # Configuración de Chat IA
    openai_api_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='API Key de OpenAI',
        help_text='Clave de API para conectar con ChatGPT'
    )
    
    openai_model = models.CharField(
        max_length=50,
        default='gpt-4o',
        verbose_name='Modelo de OpenAI',
        help_text='Modelo de IA a utilizar por defecto (ej: gpt-4o, gpt-3.5-turbo)'
    )
    
    ai_chat_enabled = models.BooleanField(
        default=False,
        verbose_name='Chat IA habilitado',
        help_text='Habilita o deshabilita la funcionalidad de chat con IA'
    )
    
    # Configuración de análisis de empleados con IA
    ai_employee_analysis_prompt = models.TextField(
        default='Analiza el siguiente perfil de candidato y dame un resumen profesional y una puntuación del 1 al 10 para el cargo solicitado. Considera experiencia, formación, habilidades y adecuación al puesto.\n\nDatos del candidato:\n{datos}\n\nPor favor, responde en este formato:\nResumen: [Aquí tu análisis profesional del candidato]\nPuntuación: [Número del 1 al 10]',
        verbose_name='Prompt para análisis de empleados',
        help_text='Plantilla del prompt que se enviará a la IA para analizar candidatos. Usa {datos} donde se insertarán los datos del candidato.'
    )
    
    # Configuración de Telegram
    enable_telegram_notifications = models.BooleanField(
        default=False,
        verbose_name='Activar notificaciones de Telegram',
        help_text='Envía notificaciones a un grupo de Telegram cuando se crean tickets'
    )
    telegram_bot_token = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Token del Bot de Telegram',
        help_text='Token del bot de Telegram proporcionado por @BotFather'
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID del Chat/Grupo de Telegram',
        help_text='ID del grupo o chat donde enviar las notificaciones (ej: -100123456789)'
    )
    
    # Configuración de Email
    enable_email_notifications = models.BooleanField(
        default=False,
        verbose_name='Activar notificaciones por email',
        help_text='Envía notificaciones por email cuando se reciben contactos desde la web'
    )
    email_host = models.CharField(
        max_length=255,
        blank=True,
        default='smtp.gmail.com',
        verbose_name='Servidor SMTP',
        help_text='Servidor de correo saliente (ej: smtp.gmail.com, mail.tu-dominio.com)'
    )
    email_port = models.IntegerField(
        blank=True,
        null=True,
        default=587,
        verbose_name='Puerto SMTP',
        help_text='Puerto del servidor SMTP (587 para TLS, 465 para SSL, 25 para sin cifrado)'
    )
    email_host_user = models.EmailField(
        blank=True,
        verbose_name='Usuario SMTP',
        help_text='Dirección de email para autenticación SMTP'
    )
    email_host_password = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Contraseña SMTP',
        help_text='Contraseña o token de aplicación para SMTP'
    )
    email_use_tls = models.BooleanField(
        default=True,
        verbose_name='Usar TLS',
        help_text='Activar cifrado TLS (recomendado para puerto 587)'
    )
    email_use_ssl = models.BooleanField(
        default=False,
        verbose_name='Usar SSL',
        help_text='Activar cifrado SSL (para puerto 465)'
    )
    email_from = models.EmailField(
        blank=True,
        verbose_name='Email remitente',
        help_text='Dirección de email que aparecerá como remitente'
    )
    notification_emails = models.TextField(
        blank=True,
        verbose_name='Emails de notificación',
        help_text='Direcciones de email donde enviar notificaciones (una por línea)'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuración del Sistema'
    
    def __str__(self):
        return f'Configuración del Sistema - {self.site_name}'
    
    @classmethod
    def get_config(cls):
        """Obtener la configuración del sistema (singleton)"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def get_currency_symbol(self):
        """Obtener el símbolo de la moneda configurada"""
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'CAD': 'C$',
            'AUD': 'A$',
            'CHF': 'CHF',
            'CNY': '¥',
            'MXN': '$',
            'COP': '$',
        }
        return currency_symbols.get(self.default_currency, '€')
    
    def format_currency(self, amount):
        """Formatear un monto con la moneda configurada"""
        if self.default_currency in ['EUR', 'GBP']:
            return f"{self.get_currency_symbol()}{amount:,.2f}"
        else:
            return f"{amount:,.2f} {self.get_currency_symbol()}"
    
    def save(self, *args, **kwargs):
        # Asegurar que solo exista una instancia de configuración
        self.pk = 1
        super().save(*args, **kwargs)


class Document(models.Model):
    """Modelo para archivos de documentación compartibles públicamente"""
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Nombre descriptivo del documento'
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción opcional del contenido del documento'
    )
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name='Archivo',
        help_text='Archivo de documentación (PDF, DOC, DOCX, TXT, etc.)'
    )
    file_size = models.PositiveIntegerField(
        verbose_name='Tamaño del archivo (bytes)',
        editable=False
    )
    file_type = models.CharField(
        max_length=100,
        verbose_name='Tipo de archivo',
        editable=False
    )
    
    # Sistema de compartir público (como en tickets)
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de compartir público',
        help_text='Token único para compartir el documento públicamente'
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Disponible públicamente',
        help_text='Si está marcado, el documento puede ser accedido sin autenticación'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Número de descargas',
        help_text='Contador de veces que se ha descargado el documento'
    )
    
    # Metadatos del documento
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_documents',
        verbose_name='Creado por'
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name='Empresa/Cliente',
        help_text='Empresa o cliente asociado al documento'
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Etiquetas',
        help_text='Etiquetas separadas por comas para categorizar el documento'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].upper() if '.' in self.file.name else 'UNKNOWN'
        super().save(*args, **kwargs)
    
    @property
    def file_size_formatted(self):
        """Retorna el tamaño del archivo en formato legible"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    @property
    def public_url(self):
        """URL pública para compartir el documento"""
        from django.urls import reverse
        return reverse('document_public', kwargs={'token': self.public_share_token})
    
    def increment_download_count(self):
        """Incrementa el contador de descargas"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def get_tags_list(self):
        """Retorna las etiquetas como lista"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []


class UrlManager(models.Model):
    """Modelo para gestionar URLs con credenciales encriptadas"""
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Nombre descriptivo para la URL'
    )
    url = models.URLField(
        max_length=500,
        verbose_name='URL',
        help_text='Dirección web completa (incluye http:// o https://)'
    )
    username = models.CharField(
        max_length=100,
        verbose_name='Usuario',
        help_text='Nombre de usuario para acceder'
    )
    encrypted_password = models.TextField(
        verbose_name='Contraseña encriptada',
        help_text='Contraseña almacenada de forma segura'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción',
        help_text='Información adicional sobre esta URL'
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Categoría',
        help_text='Ej: Servidor, Base de datos, Servicio web, etc.'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si la URL está activa o no'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_urls',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    last_accessed = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Último acceso'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gestor de URL'
        verbose_name_plural = 'Gestores de URLs'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['created_by', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.url}"
    
    def set_password(self, raw_password):
        """Encripta y guarda la contraseña"""
        from cryptography.fernet import Fernet
        from django.conf import settings
        import base64
        
        # Generar una clave de encriptación basada en SECRET_KEY
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
        fernet = Fernet(key)
        
        # Encriptar la contraseña
        encrypted_password = fernet.encrypt(raw_password.encode())
        self.encrypted_password = base64.urlsafe_b64encode(encrypted_password).decode()
    
    def get_password(self):
        """Desencripta y retorna la contraseña"""
        from cryptography.fernet import Fernet
        from django.conf import settings
        import base64
        
        try:
            # Generar la misma clave de encriptación
            key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
            fernet = Fernet(key)
            
            # Desencriptar la contraseña
            encrypted_data = base64.urlsafe_b64decode(self.encrypted_password.encode())
            decrypted_password = fernet.decrypt(encrypted_data)
            return decrypted_password.decode()
        except Exception as e:
            return f"Error al desencriptar: {str(e)}"
    
    def can_view(self, user):
        """Verifica si un usuario puede ver esta URL"""
        from .utils import is_agent
        # Solo los agentes pueden ver las URLs
        return is_agent(user)
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar esta URL"""
        from .utils import is_agent
        # Solo los agentes pueden editar URLs
        return is_agent(user)
    
    def mark_accessed(self):
        """Marca la URL como accedida recientemente"""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])
    
    @property
    def domain(self):
        """Extrae el dominio de la URL"""
        from urllib.parse import urlparse
        try:
            return urlparse(self.url).netloc
        except:
            return 'URL inválida'
    
    @property
    def status_display(self):
        """Retorna el estado en formato display"""
        return "Activo" if self.is_active else "Inactivo"


class WorkOrder(models.Model):
    """Modelo para gestionar órdenes de trabajo"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('accepted', 'Aceptado'),
        ('finished', 'Terminado'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo de la orden de trabajo'
    )
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada del trabajo a realizar'
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='work_orders',
        verbose_name='Empresa',
        help_text='Empresa a la que se dirige la orden de trabajo'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        verbose_name='Proyecto',
        help_text='Proyecto asociado a la orden de trabajo (opcional)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Estado',
        help_text='Estado actual de la orden de trabajo'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de entrega',
        help_text='Fecha límite para completar la orden (opcional)'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Publicar públicamente',
        help_text='Permite que esta orden sea visible públicamente'
    )
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de compartir público',
        help_text='Token único para compartir la orden públicamente'
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Horas estimadas',
        help_text='Tiempo estimado para completar la orden'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Importe',
        help_text='Precio o costo de la orden de trabajo'
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        default='medium',
        verbose_name='Prioridad'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_work_orders',
        verbose_name='Creado por'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders',
        verbose_name='Asignado a',
        help_text='Usuario responsable de la orden'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de finalización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Orden de Trabajo'
        verbose_name_plural = 'Órdenes de Trabajo'
        indexes = [
            models.Index(fields=['status', 'company']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"OT-{self.id:04d} - {self.title}"
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            'draft': 'bg-secondary',
            'accepted': 'bg-primary',
            'finished': 'bg-success',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_priority_badge_class(self):
        """Retorna la clase CSS para el badge de prioridad"""
        priority_classes = {
            'low': 'bg-success',
            'medium': 'bg-warning',
            'high': 'bg-danger',
            'urgent': 'bg-dark',
        }
        return priority_classes.get(self.priority, 'bg-secondary')
    
    def get_public_url(self):
        """Retorna la URL pública de la orden si está habilitada para compartir"""
        if self.is_public:
            from django.urls import reverse
            return reverse('public_work_order', kwargs={'token': self.public_share_token})
        return None
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar esta orden"""
        from .utils import is_agent
        return is_agent(user) or user == self.created_by
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar esta orden"""
        from .utils import is_agent
        # Solo se puede eliminar si está en borrador
        return (is_agent(user) or user == self.created_by) and self.status == 'draft'
    
    def mark_as_finished(self):
        """Marca la orden como terminada"""
        self.status = 'finished'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def is_overdue(self):
        """Verifica si la orden está vencida"""
        if self.status == 'finished' or not self.due_date:
            return False
        return timezone.now().date() > self.due_date
    
    def days_until_due(self):
        """Retorna los días hasta la fecha de entrega"""
        if self.status == 'finished' or not self.due_date:
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    def get_amount_display(self):
        """Retorna el importe formateado"""
        if self.amount:
            return f"${self.amount:,.2f}"
        return "No especificado"
    
    @property
    def order_number(self):
        """Retorna el número de orden formateado"""
        return f"OT-{self.id:04d}"
    
    def get_tasks_summary(self):
        """Retorna un resumen de las tareas"""
        tasks = self.tasks.all()
        total_tasks = tasks.count()
        pending_tasks = tasks.filter(status='pending').count()
        in_progress_tasks = tasks.filter(status='in_progress').count()
        completed_tasks = tasks.filter(status='completed').count()
        
        return {
            'total': total_tasks,
            'pending': pending_tasks,
            'in_progress': in_progress_tasks,
            'completed': completed_tasks,
            'progress_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    def get_total_actual_hours(self):
        """Retorna el total de horas reales trabajadas en todas las tareas"""
        return self.tasks.aggregate(
            total=models.Sum('actual_hours')
        )['total'] or 0
    
    def get_total_estimated_hours(self):
        """Retorna el total de horas estimadas de todas las tareas"""
        return self.tasks.aggregate(
            total=models.Sum('estimated_hours')
        )['total'] or 0
    
    def get_completion_percentage(self):
        """Retorna el porcentaje de completitud basado en tareas"""
        summary = self.get_tasks_summary()
        return summary['progress_percentage']
    
    def get_total_hours_logged(self):
        """Retorna el total de horas trabajadas en todas las tareas"""
        from django.db.models import Sum
        from decimal import Decimal
        
        total_hours = Decimal('0')
        task_details = []
        
        for task in self.tasks.all():
            task_total = task.time_entries.aggregate(
                total_hours=Sum('hours')
            )['total_hours']
            
            task_hours = task_total if task_total else Decimal('0')
            total_hours += task_hours
            task_details.append(f"Task {task.id} ({task.title}): {task_hours}h")
        
        # Debug: Imprimir detalles para troubleshooting
        print(f"WorkOrder {self.id} total hours calculation:")
        for detail in task_details:
            print(f"  - {detail}")
        print(f"  Total: {total_hours}h")
        
        return float(total_hours)
    
    def get_progress_percentage(self):
        """Retorna el porcentaje de progreso basado en tareas completadas"""
        total_tasks = self.get_total_tasks()
        if total_tasks == 0:
            return 0
        
        completed_tasks = self.get_completed_tasks()
        progress = round((completed_tasks / total_tasks) * 100, 1)
        
        # Debug: Imprimir los valores para troubleshooting
        print(f"WorkOrder {self.id}: total_tasks={total_tasks}, completed_tasks={completed_tasks}, progress={progress}")
        
        return progress
    
    def get_total_tasks(self):
        """Retorna el número total de tareas"""
        return self.tasks.count()
    
    def get_pending_tasks(self):
        """Retorna el número de tareas pendientes"""
        return self.tasks.filter(status='pending').count()
    
    def get_in_progress_tasks(self):
        """Retorna el número de tareas en progreso"""
        return self.tasks.filter(status='in_progress').count()
    
    def get_completed_tasks(self):
        """Retorna el número de tareas completadas"""
        return self.tasks.filter(status='completed').count()
    
    def update_actual_hours(self):
        """Actualiza las horas reales basándose en las entradas de tiempo de todas las tareas"""
        from decimal import Decimal
        
        total_hours = Decimal('0.00')
        for task in self.tasks.all():
            task.update_actual_hours()
            if task.actual_hours:
                total_hours += task.actual_hours
        
        self.actual_hours = total_hours
        self.save(update_fields=['actual_hours'])
        return total_hours


def work_order_attachment_upload_path(instance, filename):
    """Función para determinar dónde subir los adjuntos de órdenes de trabajo"""
    return f'work_order_attachments/work_order_{instance.work_order.id}/{filename}'


class WorkOrderAttachment(models.Model):
    """Modelo para adjuntos de órdenes de trabajo"""
    work_order = models.ForeignKey(
        WorkOrder, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name='Orden de Trabajo'
    )
    file = models.FileField(
        upload_to=work_order_attachment_upload_path,
        verbose_name='Archivo'
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name='Nombre original'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Subido por'
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de subida'
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='Tamaño del archivo (bytes)'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Adjunto de Orden de Trabajo'
        verbose_name_plural = 'Adjuntos de Órdenes de Trabajo'
    
    def __str__(self):
        return f'Adjunto: {self.original_filename} - OT: {self.work_order.title}'
    
    def get_file_size_display(self):
        """Retorna el tamaño del archivo en formato legible"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class WorkOrderTask(models.Model):
    """Modelo para gestionar tareas específicas de órdenes de trabajo"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
    ]
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Orden de Trabajo'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Título de la Tarea'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de la tarea (opcional)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición de la tarea'
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Horas Estimadas',
        help_text='Tiempo estimado para completar la tarea'
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Horas Reales',
        help_text='Tiempo real trabajado en la tarea'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Iniciado en'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completado en'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Tarea de Orden de Trabajo'
        verbose_name_plural = 'Tareas de Órdenes de Trabajo'
        indexes = [
            models.Index(fields=['work_order', 'status']),
            models.Index(fields=['work_order', 'order']),
        ]
    
    def __str__(self):
        return f"{self.work_order.order_number} - {self.title}"
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            'pending': 'bg-secondary',
            'in_progress': 'bg-primary',
            'completed': 'bg-success',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_status_icon(self):
        """Retorna el icono para el estado"""
        status_icons = {
            'pending': 'fas fa-clock',
            'in_progress': 'fas fa-play-circle',
            'completed': 'fas fa-check-circle',
        }
        return status_icons.get(self.status, 'fas fa-question')
    
    def start_task(self):
        """Marca la tarea como iniciada"""
        if self.status == 'pending':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at'])
    
    def complete_task(self):
        """Marca la tarea como completada"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at'])
    
    def get_duration(self):
        """Retorna la duración de la tarea si está completada"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return None
    
    def update_actual_hours(self):
        """Actualiza las horas reales basado en los time entries"""
        total_hours = self.time_entries.aggregate(
            total=models.Sum('hours')
        )['total'] or 0
        
        self.actual_hours = total_hours
        self.save(update_fields=['actual_hours'])
        return total_hours
    
    def has_active_time_entry(self):
        """Verifica si la tarea tiene una sesión de tiempo activa"""
        return self.active_sessions.filter(is_active=True).exists()
    
    def get_active_time_session(self, user=None):
        """Obtiene la sesión de tiempo activa para un usuario"""
        if user:
            return self.active_sessions.filter(is_active=True, user=user).first()
        return self.active_sessions.filter(is_active=True).first()
    
    def get_total_time_logged(self):
        """Retorna el total de horas registradas en time entries"""
        total = self.time_entries.aggregate(
            total=models.Sum('hours')
        )['total'] or 0
        return float(total)
    
    def get_progress_percentage(self):
        """Calcula el porcentaje de progreso basado en horas estimadas vs trabajadas"""
        if not self.estimated_hours or self.estimated_hours == 0:
            return 0
        
        total_logged = self.get_total_time_logged()
        percentage = (total_logged / float(self.estimated_hours)) * 100
        return min(percentage, 100)  # No más del 100%


class WorkOrderTaskTimeEntry(models.Model):
    """Modelo para registrar tiempo trabajado en tareas de órdenes de trabajo"""
    
    task = models.ForeignKey(
        WorkOrderTask,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name='Tarea'
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Horas Trabajadas'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción del Trabajo',
        help_text='Descripción opcional del trabajo realizado'
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Registrado en'
    )
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Registro de Tiempo de Tarea'
        verbose_name_plural = 'Registros de Tiempo de Tareas'
        indexes = [
            models.Index(fields=['task', 'date']),
        ]
    
    def __str__(self):
        return f"{self.task} - {self.hours}h ({self.date})"


class WorkOrderTaskTimeSession(models.Model):
    """Modelo para gestionar sesiones de tiempo activas"""
    
    task = models.ForeignKey(
        WorkOrderTask,
        on_delete=models.CASCADE,
        related_name='active_sessions',
        verbose_name='Tarea'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario que inició la sesión (puede ser vacío para sesiones públicas)'
    )
    start_time = models.DateTimeField(
        default=timezone.now,
        verbose_name='Inicio'
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fin'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción del trabajo realizado'
    )
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Sesión de Tiempo de Tarea'
        verbose_name_plural = 'Sesiones de Tiempo de Tareas'
        indexes = [
            models.Index(fields=['task', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        status = "Activa" if self.is_active else "Finalizada"
        username = self.user.username if self.user else "Público"
        return f"{self.task} - {username} ({status})"
    
    def get_duration_hours(self):
        """Retorna la duración en horas"""
        if self.end_time:
            delta = self.end_time - self.start_time
        else:
            delta = timezone.now() - self.start_time
        
        hours = delta.total_seconds() / 3600
        return round(hours, 2)
    
    def stop_session(self, description=""):
        """Detiene la sesión y crea una entrada de tiempo"""
        if self.is_active:
            self.end_time = timezone.now()
            self.is_active = False
            self.description = description
            self.save()
            
            # Crear entrada de tiempo
            hours = self.get_duration_hours()
            time_entry = WorkOrderTaskTimeEntry.objects.create(
                task=self.task,
                hours=hours,
                description=description,
                date=self.start_time.date()
            )
            
            # Actualizar horas reales de la tarea
            self.task.update_actual_hours()
            
            return time_entry
        return None


class Task(models.Model):
    """Modelo para gestionar tareas que pueden ser asignadas a múltiples usuarios"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    description = models.TextField(
        verbose_name='Descripción'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Prioridad'
    )
    assigned_users = models.ManyToManyField(
        User,
        related_name='assigned_tasks',
        blank=True,
        verbose_name='Usuarios Asignados'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name='Creado por'
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de vencimiento'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de finalización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
    
    def __str__(self):
        return f'{self.title} - {self.get_status_display()}'
    
    def get_priority_color(self):
        """Retorna el color CSS según la prioridad"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'urgent': 'dark'
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        """Retorna el color CSS según el estado"""
        colors = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return colors.get(self.status, 'secondary')
    
    def mark_as_completed(self):
        """Marca la tarea como completada"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def is_overdue(self):
        """Verifica si la tarea está vencida"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False


class DailyTaskSession(models.Model):
    """Modelo para gestionar sesiones diarias de tareas por usuario"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_task_sessions',
        verbose_name='Usuario'
    )
    date = models.DateField(
        verbose_name='Fecha de la sesión'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas del día',
        help_text='Notas generales sobre el plan del día'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Creado en'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado en'
    )
    
    class Meta:
        ordering = ['-created_at', '-date']
        verbose_name = 'Gestión de Tareas'
        verbose_name_plural = 'Gestiones de Tareas'
    
    def __str__(self):
        return f'{self.user.username} - {self.date} ({self.created_at.strftime("%H:%M")})'
    
    def get_total_tasks(self):
        """Retorna el total de tareas en esta sesión"""
        return self.daily_task_items.count()
    
    def get_completed_tasks(self):
        """Retorna las tareas completadas en esta sesión"""
        return self.daily_task_items.filter(completed=True).count()
    
    def get_pending_tasks(self):
        """Retorna las tareas pendientes en esta sesión"""
        return self.daily_task_items.filter(completed=False).count()
    
    def get_completion_percentage(self):
        """Retorna el porcentaje de completitud"""
        total = self.get_total_tasks()
        if total == 0:
            return 0
        return round((self.get_completed_tasks() / total) * 100, 1)


class DailyTaskItem(models.Model):
    """Modelo para items de tareas dentro de una sesión diaria"""
    
    session = models.ForeignKey(
        DailyTaskSession,
        on_delete=models.CASCADE,
        related_name='daily_task_items',
        verbose_name='Sesión diaria'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='daily_items',
        verbose_name='Tarea'
    )
    completed = models.BooleanField(
        default=False,
        verbose_name='Completada'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completada en'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas específicas',
        help_text='Notas específicas sobre el trabajo en esta tarea'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )
    
    class Meta:
        ordering = ['order', 'task__priority']
        unique_together = ['session', 'task']
        verbose_name = 'Item de Tarea Diaria'
        verbose_name_plural = 'Items de Tareas Diarias'
    
    def __str__(self):
        status = "✓" if self.completed else "○"
        return f'{status} {self.task.title} - {self.session.date}'
    
    def mark_completed(self):
        """Marca el item como completado"""
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def mark_pending(self):
        """Marca el item como pendiente"""
        self.completed = False
        self.completed_at = None
        self.save()


class ChatRoom(models.Model):
    """Modelo para las salas de chat entre usuarios"""
    name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre de la sala'
    )
    participants = models.ManyToManyField(
        User,
        related_name='chat_rooms',
        verbose_name='Participantes'
    )
    is_group = models.BooleanField(
        default=False,
        verbose_name='Es grupo',
        help_text='True para chats grupales, False para chats 1:1'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    last_activity = models.DateTimeField(
        default=timezone.now,
        verbose_name='Última actividad'
    )
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'Sala de Chat'
        verbose_name_plural = 'Salas de Chat'
    
    def __str__(self):
        if self.is_group and self.name:
            return self.name
        elif not self.is_group:
            participants = list(self.participants.all())
            if len(participants) == 2:
                return f"{participants[0].get_full_name() or participants[0].username} & {participants[1].get_full_name() or participants[1].username}"
        return f"Chat {self.id}"
    
    def get_other_participant(self, user):
        """Para chats 1:1, obtiene el otro participante"""
        if not self.is_group:
            return self.participants.exclude(id=user.id).first()
        return None
    
    def get_last_message(self):
        """Obtiene el último mensaje de la sala"""
        return self.messages.order_by('-created_at').first()
    
    def mark_as_read_for_user(self, user):
        """Marca todos los mensajes como leídos para un usuario"""
        unread_messages = self.messages.filter(read_by__isnull=True).exclude(sender=user)
        for message in unread_messages:
            message.read_by.add(user)
    
    def get_unread_count_for_user(self, user):
        """Obtiene el número de mensajes no leídos para un usuario"""
        return self.messages.exclude(sender=user).exclude(read_by=user).count()


class ChatMessage(models.Model):
    """Modelo para los mensajes del chat"""
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Sala de chat'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name='Remitente'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Mensaje'
    )
    attachment = models.FileField(
        upload_to='chat_attachments/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Archivo adjunto'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de envío'
    )
    read_by = models.ManyToManyField(
        User,
        blank=True,
        related_name='read_messages',
        verbose_name='Leído por'
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
    
    def __str__(self):
        if self.message:
            preview = self.message[:50] + "..." if len(self.message) > 50 else self.message
            return f"{self.sender.username}: {preview}"
        elif self.attachment:
            return f"{self.sender.username}: [Archivo adjunto]"
        return f"Mensaje {self.id}"
    
    def is_read_by_user(self, user):
        """Verifica si el mensaje ha sido leído por un usuario específico"""
        return self.read_by.filter(id=user.id).exists()
    
    def get_attachment_name(self):
        """Obtiene el nombre del archivo adjunto"""
        if self.attachment:
            return os.path.basename(self.attachment.name)
        return None
    
    def get_attachment_size(self):
        """Obtiene el tamaño del archivo adjunto en formato legible"""
        if self.attachment:
            try:
                size = self.attachment.size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "Tamaño desconocido"
        return None


class Command(models.Model):
    """Modelo para gestionar biblioteca de comandos"""
    
    CATEGORY_CHOICES = [
        ('linux', 'Linux/Unix'),
        ('windows', 'Windows'),
        ('docker', 'Docker'),
        ('git', 'Git'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('database', 'Base de Datos'),
        ('network', 'Redes'),
        ('security', 'Seguridad'),
        ('devops', 'DevOps'),
        ('web', 'Desarrollo Web'),
        ('mobile', 'Desarrollo Móvil'),
        ('other', 'Otros'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo del comando'
    )
    command = models.TextField(
        verbose_name='Comando',
        help_text='El comando completo con sus parámetros'
    )
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada de lo que hace el comando'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='Categoría'
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Etiquetas',
        help_text='Etiquetas separadas por comas para facilitar la búsqueda'
    )
    example_usage = models.TextField(
        blank=True,
        verbose_name='Ejemplo de uso',
        help_text='Ejemplo práctico de cómo usar el comando'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales',
        help_text='Notas importantes, advertencias o tips'
    )
    is_dangerous = models.BooleanField(
        default=False,
        verbose_name='Comando peligroso',
        help_text='Marcar si el comando puede ser destructivo o peligroso'
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name='Favorito',
        help_text='Marcar como comando favorito'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Veces usado',
        help_text='Contador de cuántas veces se ha copiado/usado este comando'
    )
    
    class Meta:
        ordering = ['-is_favorite', '-usage_count', '-created_at']
        verbose_name = 'Comando'
        verbose_name_plural = 'Comandos'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_favorite']),
            models.Index(fields=['created_by']),
            models.Index(fields=['title']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_category_display_with_icon(self):
        """Retorna la categoría con su icono correspondiente"""
        icons = {
            'linux': 'bi-terminal',
            'windows': 'bi-windows',
            'docker': 'bi-box',
            'git': 'bi-git',
            'python': 'bi-code-slash',
            'javascript': 'bi-braces',
            'database': 'bi-database',
            'network': 'bi-wifi',
            'security': 'bi-shield-check',
            'devops': 'bi-gear',
            'web': 'bi-globe',
            'mobile': 'bi-phone',
            'other': 'bi-three-dots',
        }
        return {
            'name': self.get_category_display(),
            'icon': icons.get(self.category, 'bi-three-dots')
        }
    
    def get_tags_list(self):
        """Retorna las etiquetas como lista"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_usage(self):
        """Incrementa el contador de uso"""
        self.usage_count = models.F('usage_count') + 1
        self.save(update_fields=['usage_count'])
        self.refresh_from_db()
    
    def get_short_description(self, max_length=100):
        """Retorna una versión corta de la descripción"""
        if len(self.description) <= max_length:
            return self.description
        return self.description[:max_length] + '...'


class ContactFormSubmission(models.Model):
    """Modelo para gestionar formularios de contacto público"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('company_created', 'Empresa Creada'),
    ]
    
    # Información del formulario de contacto
    company_name = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Empresa'
    )
    contact_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del Contacto'
    )
    email = models.EmailField(
        verbose_name='Correo Electrónico'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Sitio Web'
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Dirección'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Mensaje Adicional',
        help_text='Información adicional sobre la empresa o servicios requeridos'
    )
    
    # Metadatos del formulario
    submitted_by_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contact_form_owner',
        verbose_name='Propietario del formulario',
        help_text='Usuario que tiene activado el formulario de contacto'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    # Información de seguimiento
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # Empresa creada (si se aprueba)
    created_company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empresa Creada'
    )
    
    # Fechas
    submitted_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Envío'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Procesamiento'
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_contact_forms',
        verbose_name='Procesado por'
    )
    
    # Notas internas
    admin_notes = models.TextField(
        blank=True,
        verbose_name='Notas del Administrador',
        help_text='Notas internas para el seguimiento de la solicitud'
    )
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Formulario de Contacto'
        verbose_name_plural = 'Formularios de Contacto'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['submitted_by_user']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.contact_name} ({self.get_status_display()})"
    
    def mark_as_processed(self, user, status, company=None):
        """Marca el formulario como procesado"""
        self.status = status
        self.processed_by = user
        self.processed_at = timezone.now()
        if company:
            self.created_company = company
        self.save()
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge del estado"""
        status_classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'company_created': 'bg-primary',
        }
        return status_classes.get(self.status, 'bg-secondary')


# ============= MODELOS CRM =============

class OpportunityStatus(models.Model):
    """Estados configurables para las oportunidades CRM"""
    
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Nombre del Estado'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Descripción'
    )
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text='Color en formato hexadecimal (ej: #007bff)',
        verbose_name='Color'
    )
    is_final = models.BooleanField(
        default=False,
        verbose_name='Estado Final',
        help_text='Indica si este estado representa el cierre de la oportunidad'
    )
    is_won = models.BooleanField(
        default=False,
        verbose_name='Estado Ganado',
        help_text='Indica si este estado representa una venta exitosa'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el pipeline'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name='Creado por'
    )
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Estado de Oportunidad'
        verbose_name_plural = 'Estados de Oportunidad'
    
    def __str__(self):
        return self.name


class Opportunity(models.Model):
    """Modelo para gestionar oportunidades CRM"""
    
    PROBABILITY_CHOICES = [
        (0, '0%'),
        (10, '10%'),
        (20, '20%'),
        (30, '30%'),
        (40, '40%'),
        (50, '50%'),
        (60, '60%'),
        (70, '70%'),
        (80, '80%'),
        (90, '90%'),
        (100, '100%'),
    ]
    
    name = models.CharField(
        max_length=200, 
        verbose_name='Nombre de la Oportunidad'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Descripción'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='opportunities',
        verbose_name='Empresa'
    )
    contact_name = models.CharField(
        max_length=200,
        verbose_name='Contacto Principal'
    )
    contact_position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cargo del Contacto',
        help_text='Posición o cargo del contacto en la empresa'
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name='Email de Contacto'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono de Contacto'
    )
    value = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name='Valor Estimado',
        help_text='Valor estimado de la oportunidad'
    )
    probability = models.IntegerField(
        choices=PROBABILITY_CHOICES,
        default=20,
        verbose_name='Probabilidad de Cierre (%)'
    )
    status = models.ForeignKey(
        OpportunityStatus,
        on_delete=models.PROTECT,
        related_name='opportunities',
        verbose_name='Estado'
    )
    expected_close_date = models.DateField(
        verbose_name='Fecha Estimada de Cierre'
    )
    actual_close_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha Real de Cierre'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_opportunities',
        verbose_name='Asignado a'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_opportunities',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    # Campos de seguimiento
    last_contact_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Último Contacto'
    )
    next_follow_up = models.DateField(
        blank=True,
        null=True,
        verbose_name='Próximo Seguimiento'
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Fuente',
        help_text='¿Cómo se originó esta oportunidad?'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Oportunidad'
        verbose_name_plural = 'Oportunidades'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['company']),
            models.Index(fields=['expected_close_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    @property
    def expected_value(self):
        """Calcula el valor esperado basado en la probabilidad"""
        return (self.value * self.probability) / 100
    
    @property
    def is_overdue(self):
        """Verifica si la oportunidad está vencida"""
        if self.expected_close_date and not self.status.is_final:
            return self.expected_close_date < timezone.now().date()
        return False
    
    @property
    def days_to_close(self):
        """Calcula los días hasta el cierre esperado"""
        if self.expected_close_date:
            delta = self.expected_close_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def days_overdue(self):
        """Calcula los días vencidos (número positivo)"""
        if self.is_overdue and self.expected_close_date:
            delta = timezone.now().date() - self.expected_close_date
            return delta.days
        return 0
    
    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar esta oportunidad"""
        from .utils import is_agent
        return is_agent(user) or user == self.created_by or user == self.assigned_to


class OpportunityNote(models.Model):
    """Notas y seguimiento de oportunidades"""
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Oportunidad'
    )
    content = models.TextField(verbose_name='Contenido')
    is_important = models.BooleanField(
        default=False,
        verbose_name='Importante',
        help_text='Marcar como nota importante'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nota de Oportunidad'
        verbose_name_plural = 'Notas de Oportunidad'
    
    def __str__(self):
        return f"Nota para {self.opportunity.name} - {self.created_at.strftime('%d/%m/%Y')}"


class OpportunityStatusHistory(models.Model):
    """Historial de cambios de estado de las oportunidades"""
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Oportunidad'
    )
    previous_status = models.ForeignKey(
        OpportunityStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_changes',
        verbose_name='Estado Anterior'
    )
    new_status = models.ForeignKey(
        OpportunityStatus,
        on_delete=models.CASCADE,
        related_name='new_changes',
        verbose_name='Nuevo Estado'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Cambiado por'
    )
    changed_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha del cambio')
    comment = models.TextField(
        blank=True,
        verbose_name='Comentario',
        help_text='Razón del cambio de estado'
    )
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historial de Estados'
    
    def __str__(self):
        return f"{self.opportunity.name}: {self.previous_status} → {self.new_status}"


class OpportunityActivity(models.Model):
    """Modelo para actividades de seguimiento de oportunidades"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('call', 'Llamada'),
        ('meeting', 'Reunión'),
        ('email', 'Correo Electrónico'),
        ('task', 'Tarea'),
        ('demo', 'Demostración'),
        ('proposal', 'Propuesta'),
        ('follow_up', 'Seguimiento'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
        ('overdue', 'Vencida'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Oportunidad'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Título de la Actividad'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES,
        default='task',
        verbose_name='Tipo de Actividad'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Prioridad'
    )
    scheduled_date = models.DateTimeField(
        verbose_name='Fecha Programada',
        help_text='Fecha y hora cuando debe realizarse la actividad'
    )
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Completado'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_activities',
        verbose_name='Asignado a'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_activities',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    # Campos adicionales
    result = models.TextField(
        blank=True,
        verbose_name='Resultado',
        help_text='Resultado o notas de la actividad completada'
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duración (minutos)',
        help_text='Duración estimada o real de la actividad'
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Ubicación',
        help_text='Lugar donde se realizará la actividad'
    )
    
    class Meta:
        ordering = ['scheduled_date', '-priority']
        verbose_name = 'Actividad de Oportunidad'
        verbose_name_plural = 'Actividades de Oportunidades'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.opportunity.name}"
    
    @property
    def is_overdue(self):
        """Verifica si la actividad está vencida"""
        if self.status in ['pending', 'in_progress'] and self.scheduled_date:
            return self.scheduled_date < timezone.now()
        return False
    
    @property
    def days_until_due(self):
        """Calcula los días hasta el vencimiento"""
        if self.scheduled_date:
            delta = self.scheduled_date.date() - timezone.now().date()
            return delta.days
        return None
    
    @property
    def is_due_today(self):
        """Verifica si la actividad vence hoy"""
        if self.scheduled_date:
            return self.scheduled_date.date() == timezone.now().date()
        return False
    
    @property
    def is_due_soon(self):
        """Verifica si la actividad vence en los próximos 3 días"""
        days_until = self.days_until_due
        return days_until is not None and 0 <= days_until <= 3
    
    def mark_completed(self, result=None, user=None):
        """Marca la actividad como completada"""
        self.status = 'completed'
        self.completed_date = timezone.now()
        if result:
            self.result = result
        self.save()
    
    def get_priority_color(self):
        """Retorna el color para la prioridad"""
        colors = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'danger',
            'urgent': 'dark'
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        """Retorna el color para el estado"""
        colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'completed': 'success',
            'cancelled': 'secondary',
            'overdue': 'danger'
        }
        return colors.get(self.status, 'secondary')


class Meeting(models.Model):
    """Modelo para gestionar reuniones"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('in_progress', 'En progreso'),
        ('finished', 'Finalizada'),
        ('cancelled', 'Cancelada'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título de la reunión')
    description = models.TextField(blank=True, verbose_name='Descripción')
    spin_methodology = models.TextField(
        blank=True, 
        verbose_name='Metodología SPIN',
        help_text='Preguntas generadas automáticamente usando la metodología SPIN de ventas'
    )
    date = models.DateTimeField(verbose_name='Fecha y hora')
    duration = models.IntegerField(default=60, verbose_name='Duración (minutos)')
    location = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='scheduled',
        verbose_name='Estado'
    )
    
    # Organizador
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_meetings',
        verbose_name='Organizador'
    )
    
    # Empresa (opcional para uso interno)
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empresa',
        help_text='Empresa relacionada con la reunión (opcional)'
    )
    
    # Producto relacionado con la reunión
    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Producto',
        help_text='Producto principal que se discutirá en la reunión'
    )
    
    # Link público único
    public_token = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Token público'
    )
    
    # Configuración
    allow_questions = models.BooleanField(default=True, verbose_name='Permitir preguntas')
    require_email = models.BooleanField(default=False, verbose_name='Requerir email')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Creada el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Reunión'
        verbose_name_plural = 'Reuniones'
    
    def __str__(self):
        return f"{self.title} - {self.date.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        if not self.public_token:
            import uuid
            self.public_token = str(uuid.uuid4())
        super().save(*args, **kwargs)
    
    def get_public_url(self):
        """Retorna la URL pública para registro de asistentes"""
        return f"/meetings/public/{self.public_token}/"
    
    def get_questions_url(self):
        """Retorna la URL pública para hacer preguntas"""
        return f"/meetings/public/{self.public_token}/questions/"
    
    def get_attendees_count(self):
        """Retorna el total de asistentes registrados"""
        return self.meetingattendee_set.count()
    
    def get_questions_count(self):
        """Retorna el total de preguntas"""
        return self.meetingquestion_set.count()


class MeetingAttendee(models.Model):
    """Modelo para asistentes a reuniones"""
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name='Reunión')
    name = models.CharField(max_length=100, verbose_name='Nombre')
    email = models.EmailField(blank=True, verbose_name='Email')
    company = models.CharField(max_length=100, blank=True, verbose_name='Empresa')
    registered_at = models.DateTimeField(default=timezone.now, verbose_name='Registrado el')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    
    class Meta:
        ordering = ['registered_at']
        verbose_name = 'Asistente'
        verbose_name_plural = 'Asistentes'
        # Removido unique_together para permitir múltiples registros
    
    def __str__(self):
        return f"{self.name} - {self.meeting.title}"


class MeetingQuestion(models.Model):
    """Modelo para preguntas en reuniones"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('answered', 'Respondida'),
        ('ignored', 'Ignorada'),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name='Reunión')
    attendee = models.ForeignKey(
        MeetingAttendee, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name='Asistente'
    )
    question = models.TextField(verbose_name='Pregunta')
    answer = models.TextField(blank=True, verbose_name='Respuesta')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Estado'
    )
    
    # Datos del preguntante (por si no está registrado como asistente)
    asker_name = models.CharField(max_length=100, blank=True, verbose_name='Nombre del preguntante')
    asker_email = models.EmailField(blank=True, verbose_name='Email del preguntante')
    
    # Metadata
    asked_at = models.DateTimeField(default=timezone.now, verbose_name='Preguntado el')
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='Respondido el')
    answered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Respondido por'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    
    class Meta:
        ordering = ['asked_at']
        verbose_name = 'Pregunta de reunión'
        verbose_name_plural = 'Preguntas de reuniones'
    
    def __str__(self):
        return f"Pregunta en {self.meeting.title}: {self.question[:50]}..."
    
    def get_asker_display_name(self):
        """Retorna el nombre del preguntante"""
        if self.attendee:
            return self.attendee.name
        return self.asker_name or "Anónimo"


class Course(models.Model):
    """Modelo para gestionar cursos de capacitación"""
    
    title = models.CharField(max_length=200, verbose_name='Título del Curso')
    description = models.TextField(blank=True, verbose_name='Descripción')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Creado por'
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Empresa',
        help_text='Si se selecciona una empresa, solo los usuarios de esa empresa podrán ver este curso'
    )
    public_token = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='Token público',
        help_text='Token para acceso público al curso sin autenticación'
    )
    is_public_enabled = models.BooleanField(
        default=False,
        verbose_name='Acceso público habilitado',
        help_text='Permite que el curso sea accesible públicamente mediante un enlace'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
    
    def __str__(self):
        return self.title
    
    def get_classes_count(self):
        """Retorna el número de clases en el curso"""
        return self.classes.count()
    
    def generate_public_token(self):
        """Genera un nuevo token público para el curso"""
        import uuid
        self.public_token = uuid.uuid4()
        self.is_public_enabled = True
        self.save()
        return self.public_token
    
    def disable_public_access(self):
        """Deshabilita el acceso público al curso"""
        self.is_public_enabled = False
        self.save()
    
    def get_public_url(self, request=None):
        """Retorna la URL pública del curso si está habilitada"""
        if self.is_public_enabled and self.public_token:
            from django.urls import reverse
            if request:
                return request.build_absolute_uri(
                    reverse('course_public', kwargs={'token': self.public_token})
                )
            return reverse('course_public', kwargs={'token': self.public_token})
        return None
    
    def can_user_access(self, user):
        """Verifica si un usuario puede acceder a este curso"""
        if not user.is_authenticated:
            return False
            
        # Si el curso no tiene empresa asignada, todos pueden verlo
        if not self.company:
            return True
            
        # Si el curso tiene empresa, verificar que el usuario pertenezca a esa empresa
        try:
            # Intentar obtener o crear el UserProfile si no existe
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            return user_profile.company == self.company
        except Exception as e:
            return False
    
    def is_public(self):
        """Retorna True si el curso es público (sin empresa asignada)"""
        return self.company is None


class CourseRegistrationToken(models.Model):
    """Modelo para gestionar tokens de registro público para cursos"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='registration_tokens',
        verbose_name='Curso'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Token'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Creado por'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de expiración',
        help_text='Dejar vacío para que no expire'
    )
    max_registrations = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Máximo de registros',
        help_text='Número máximo de usuarios que pueden registrarse con este token'
    )
    registration_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Registros realizados'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Token de Registro de Curso'
        verbose_name_plural = 'Tokens de Registro de Curso'
    
    def __str__(self):
        return f"Token para {self.course.title} - {self.token}"
    
    def is_valid(self):
        """Verifica si el token es válido para registro"""
        if not self.is_active:
            return False, "El token no está activo"
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False, "El token ha expirado"
        
        if self.max_registrations and self.registration_count >= self.max_registrations:
            return False, "Se ha alcanzado el límite máximo de registros"
        
        return True, "Token válido"
    
    def increment_registration_count(self):
        """Incrementa el contador de registros"""
        self.registration_count += 1
        self.save(update_fields=['registration_count'])
    
    def get_registration_url(self):
        """Retorna la URL completa para registro público"""
        from django.urls import reverse
        return reverse('course_public_register', kwargs={'token': self.token})


class CourseClass(models.Model):
    """Modelo para gestionar clases dentro de un curso"""
    
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='classes',
        verbose_name='Curso'
    )
    title = models.CharField(max_length=200, verbose_name='Título de la Clase')
    description = models.TextField(blank=True, verbose_name='Descripción')
    video_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name='URL del Video',
        help_text='URL del video de la clase (YouTube, Vimeo, etc.)'
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name='Orden',
        help_text='Orden de la clase dentro del curso'
    )
    duration_minutes = models.PositiveIntegerField(
        blank=True, 
        null=True,
        verbose_name='Duración (minutos)',
        help_text='Duración estimada de la clase en minutos'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        ordering = ['course', 'order', 'title']
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def has_video(self):
        """Verifica si la clase tiene video"""
        return bool(self.video_url)
    
    def get_view_count(self):
        """Retorna el número de usuarios que han visto esta clase"""
        return self.views.count()
    
    def is_viewed_by_user(self, user):
        """Verifica si un usuario específico ha visto esta clase"""
        if not user.is_authenticated:
            return False
        return self.views.filter(user=user).exists()


class CourseClassView(models.Model):
    """Modelo para rastrear qué usuarios han visto qué clases"""
    
    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Clase'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Visto el'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    
    class Meta:
        unique_together = ['course_class', 'user']
        ordering = ['-viewed_at']
        verbose_name = 'Visualización de Clase'
        verbose_name_plural = 'Visualizaciones de Clases'
    
    def __str__(self):
        return f"{self.user.username} vio {self.course_class.title}"


class Contact(models.Model):
    """Modelo para gestionar contactos de ventas"""
    
    STATUS_CHOICES = [
        ('positive', 'Positivo'),
        ('negative', 'Negativo'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cargo'
    )
    company = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Empresa'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='positive',
        verbose_name='Estado'
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Fuente',
        help_text='¿De dónde obtuviste este contacto?'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas',
        help_text='Notas adicionales sobre el contacto'
    )
    contact_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Contacto'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts_created',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-contact_date']
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    def get_status_color(self):
        """Retorna el color del estado"""
        return 'success' if self.status == 'positive' else 'danger'
    
    def get_status_icon(self):
        """Retorna el icono del estado"""
        return 'bi-check-circle' if self.status == 'positive' else 'bi-x-circle'


class BlogCategory(models.Model):
    """Categorías para los artículos del blog"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug URL'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name='Color',
        help_text='Color en formato hexadecimal (ej: #007bff)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Creado por'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Categoría de Blog'
        verbose_name_plural = 'Categorías de Blog'
    
    def __str__(self):
        return self.name


class BlogPost(models.Model):
    """Artículos del blog"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicado'),
        ('archived', 'Archivado'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug URL'
    )
    excerpt = models.TextField(
        max_length=300,
        verbose_name='Resumen',
        help_text='Breve descripción del artículo (máx. 300 caracteres)'
    )
    content = models.TextField(
        verbose_name='Contenido'
    )
    featured_image = models.ImageField(
        upload_to='blog/images/',
        blank=True,
        null=True,
        verbose_name='Imagen Principal'
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name='Categoría'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Estado'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Etiquetas',
        help_text='Etiquetas separadas por comas'
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Meta Descripción',
        help_text='Descripción para SEO (máx. 160 caracteres)'
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Número de visualizaciones'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Artículo Destacado'
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de publicación'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name='Creado por'
    )
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Artículo de Blog'
        verbose_name_plural = 'Artículos de Blog'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generar slug si no existe
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        
        # Establecer fecha de publicación cuando se publica
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog_post_detail', kwargs={'slug': self.slug})
    
    def get_tags_list(self):
        """Retorna las etiquetas como lista"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def increment_views(self):
        """Incrementa el contador de visualizaciones"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def get_pending_comments_count(self):
        """Retorna el número de comentarios pendientes de aprobación"""
        return self.comments.filter(is_approved=False).count()
    
    def get_approved_comments_count(self):
        """Retorna el número de comentarios aprobados"""
        return self.comments.filter(is_approved=True).count()


class BlogComment(models.Model):
    """Comentarios de los artículos del blog"""
    
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Artículo'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Sitio Web'
    )
    content = models.TextField(
        verbose_name='Comentario'
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name='Aprobado'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comentario de Blog'
        verbose_name_plural = 'Comentarios de Blog'
    
    def __str__(self):
        return f"{self.name} en {self.post.title}"


class AIChatSession(models.Model):
    """Modelo para sesiones de chat con IA"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_chat_sessions',
        verbose_name='Usuario'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Título de la conversación',
        help_text='Título descriptivo de la conversación'
    )
    ai_model = models.CharField(
        max_length=50,
        default='gpt-4o',
        verbose_name='Modelo de IA',
        help_text='Modelo utilizado para esta conversación'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Sesión activa'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Sesión de Chat IA'
        verbose_name_plural = 'Sesiones de Chat IA'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_message_count(self):
        """Retorna el número de mensajes en esta sesión"""
        return self.messages.count()
    
    def get_last_message(self):
        """Retorna el último mensaje de la sesión"""
        return self.messages.order_by('-created_at').first()


class AIChatMessage(models.Model):
    """Modelo para mensajes individuales del chat con IA"""
    
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'IA'),
        ('system', 'Sistema'),
    ]
    
    session = models.ForeignKey(
        AIChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Sesión'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name='Rol'
    )
    content = models.TextField(
        verbose_name='Contenido del mensaje'
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name='Tokens utilizados',
        help_text='Número de tokens consumidos para este mensaje'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensaje de Chat IA'
        verbose_name_plural = 'Mensajes de Chat IA'
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."
    
    def is_from_user(self):
        """Verifica si el mensaje es del usuario"""
        return self.role == 'user'
    
    def is_from_ai(self):
        """Verifica si el mensaje es de la IA"""
        return self.role == 'assistant'


class Concept(models.Model):
    """Modelo para gestionar conceptos y definiciones que se muestran en el home"""
    
    term = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Término',
        help_text='El concepto o término a definir'
    )
    definition = models.TextField(
        verbose_name='Definición',
        help_text='Explicación del concepto'
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Categoría',
        help_text='Categoría del concepto (opcional)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si el concepto debe mostrarse en el home'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición (menor número aparece primero)'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='concepts_created',
        verbose_name='Creado por'
    )
    
    class Meta:
        ordering = ['order', 'term']
        verbose_name = 'Concepto'
        verbose_name_plural = 'Conceptos'
    
    def __str__(self):
        return f"{self.term}: {self.definition[:50]}..."


class Exam(models.Model):
    """Modelo para los exámenes"""
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título del Examen'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Creado por'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='¿Es público?'
    )
    public_token = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Token público'
    )
    passing_score = models.IntegerField(
        default=70,
        verbose_name='Puntuación mínima para aprobar (%)'
    )
    time_limit = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Tiempo límite (minutos)',
        help_text='Dejar vacío para sin límite de tiempo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Examen'
        verbose_name_plural = 'Exámenes'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_public and not self.public_token:
            import uuid
            self.public_token = str(uuid.uuid4())[:8]
        elif not self.is_public:
            self.public_token = None
        super().save(*args, **kwargs)
    
    def get_questions_count(self):
        return self.questions.count()
    
    def get_total_attempts(self):
        return self.attempts.count()


class ExamQuestion(models.Model):
    """Modelo para las preguntas del examen"""
    
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Examen'
    )
    question_text = models.TextField(
        verbose_name='Pregunta'
    )
    option_a = models.CharField(
        max_length=500,
        verbose_name='Opción A'
    )
    option_b = models.CharField(
        max_length=500,
        verbose_name='Opción B'
    )
    option_c = models.CharField(
        max_length=500,
        verbose_name='Opción C'
    )
    correct_option = models.CharField(
        max_length=1,
        choices=[('A', 'Opción A'), ('B', 'Opción B'), ('C', 'Opción C')],
        verbose_name='Opción correcta'
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name='Orden'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pregunta del Examen'
        verbose_name_plural = 'Preguntas del Examen'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.exam.title} - Pregunta {self.order}"


class ExamAttempt(models.Model):
    """Modelo para los intentos de examen"""
    
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Examen'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Usuario'
    )
    participant_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del participante'
    )
    participant_email = models.EmailField(
        verbose_name='Email del participante'
    )
    score = models.FloatField(
        verbose_name='Puntuación (%)'
    )
    total_questions = models.IntegerField(
        verbose_name='Total de preguntas'
    )
    correct_answers = models.IntegerField(
        verbose_name='Respuestas correctas'
    )
    started_at = models.DateTimeField(
        verbose_name='Iniciado en'
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Completado en'
    )
    time_taken = models.IntegerField(
        verbose_name='Tiempo tomado (segundos)'
    )
    passed = models.BooleanField(
        default=False,
        verbose_name='¿Aprobado?'
    )
    certificate_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Token del certificado'
    )
    certificate_generated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Certificado generado en'
    )
    
    class Meta:
        verbose_name = 'Intento de Examen'
        verbose_name_plural = 'Intentos de Examen'
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.participant_name} - {self.exam.title} ({self.score}%)"
    
    @property
    def time_taken_display(self):
        """Retorna el tiempo tomado en formato legible"""
        if not self.time_taken:
            return "No disponible"
        
        if self.time_taken < 60:
            return f"{self.time_taken} segundos"
        elif self.time_taken < 3600:
            minutes = self.time_taken // 60
            seconds = self.time_taken % 60
            return f"{minutes} min {seconds} seg"
        else:
            hours = self.time_taken // 3600
            minutes = (self.time_taken % 3600) // 60
            seconds = self.time_taken % 60
            return f"{hours}h {minutes}m {seconds}s"
    
    @property
    def incorrect_answers(self):
        """Retorna el número de respuestas incorrectas"""
        return self.total_questions - self.correct_answers
    
    def generate_certificate_token(self):
        """Genera un token único para el certificado"""
        if not self.certificate_token and self.passed:
            import uuid
            from django.utils import timezone
            self.certificate_token = str(uuid.uuid4())
            self.certificate_generated_at = timezone.now()
            self.save(update_fields=['certificate_token', 'certificate_generated_at'])
        return self.certificate_token
    
    def save(self, *args, **kwargs):
        # Generar token del certificado automáticamente si pasa el examen
        if self.passed and not self.certificate_token:
            import uuid
            self.certificate_token = str(uuid.uuid4())
            if not self.certificate_generated_at:
                from django.utils import timezone
                self.certificate_generated_at = timezone.now()
        super().save(*args, **kwargs)


class ExamAnswer(models.Model):
    """Modelo para las respuestas del examen"""
    
    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Intento'
    )
    question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        verbose_name='Pregunta'
    )
    selected_option = models.CharField(
        max_length=1,
        choices=[('A', 'Opción A'), ('B', 'Opción B'), ('C', 'Opción C')],
        verbose_name='Opción seleccionada'
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='¿Es correcta?'
    )
    
    class Meta:
        verbose_name = 'Respuesta del Examen'
        verbose_name_plural = 'Respuestas del Examen'
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.participant_name} - {self.question.question_text[:50]}..."


class ContactoWeb(models.Model):
    """Modelo para gestionar contactos desde la web pública"""
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre completo'
    )
    email = models.EmailField(
        verbose_name='Correo electrónico'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    empresa = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Empresa'
    )
    asunto = models.CharField(
        max_length=200,
        verbose_name='Asunto'
    )
    mensaje = models.TextField(
        verbose_name='Mensaje'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    leido = models.BooleanField(
        default=False,
        verbose_name='Leído'
    )
    respondido = models.BooleanField(
        default=False,
        verbose_name='Respondido'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        verbose_name = 'Contacto Web'
        verbose_name_plural = 'Contactos Web'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.asunto}"


class PublicDocumentUpload(models.Model):
    """Modelo para URLs públicas de subida de documentos"""
    
    # Token único para la URL pública
    upload_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de subida',
        help_text='Token único para la URL pública de subida'
    )
    
    # Configuración de la URL
    title = models.CharField(
        max_length=200,
        verbose_name='Título de la subida',
        help_text='Descripción de qué tipo de documentos se esperan'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Instrucciones',
        help_text='Instrucciones para quien vaya a subir el documento'
    )
    
    # Usuario que creó la URL
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='public_upload_urls',
        verbose_name='Creado por'
    )
    
    # Empresa asociada (opcional)
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='public_upload_urls',
        verbose_name='Empresa/Cliente',
        help_text='Empresa o cliente para el cual se subirán los documentos'
    )
    
    # Configuración de expiración
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de expiración',
        help_text='Opcional: fecha límite para usar esta URL'
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Si está desactivada, no se pueden subir más documentos'
    )
    
    # Configuración de límites
    max_uploads = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Máximo de subidas',
        help_text='Opcional: límite de documentos que se pueden subir'
    )
    upload_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Documentos subidos',
        help_text='Contador de documentos subidos usando esta URL'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último uso'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'URL Pública de Subida'
        verbose_name_plural = 'URLs Públicas de Subida'
    
    def __str__(self):
        return f"{self.title} - {self.upload_token}"
    
    def is_valid(self):
        """Verifica si la URL está válida para usarse"""
        if not self.is_active:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        if self.max_uploads and self.upload_count >= self.max_uploads:
            return False
        
        return True
    
    def get_public_url(self):
        """Devuelve la URL pública para subir documentos"""
        from django.urls import reverse
        return reverse('public_document_upload', kwargs={'token': self.upload_token})


class Employee(models.Model):
    """Modelo para gestionar empleados de la empresa"""
    
    # Información personal básica
    first_name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Apellidos'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Correo electrónico'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    
    # Información profesional
    position = models.CharField(
        max_length=150,
        verbose_name='Cargo'
    )
    salary_euros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Salario (EUR)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción/Experiencia'
    )
    
    # Currículo
    resume_file = models.FileField(
        upload_to='resumes/',
        null=True,
        blank=True,
        verbose_name='Archivo de currículo'
    )
    
    # Análisis de IA
    ai_analysis = models.TextField(
        blank=True,
        verbose_name='Análisis de IA',
        help_text='Resumen automático generado por IA'
    )
    ai_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Puntuación IA (1-10)',
        help_text='Puntuación automática del candidato'
    )
    
    # Opinión de reunión de contratación
    hiring_meeting_opinion = models.TextField(
        blank=True,
        verbose_name='Opinión de reunión de contratación',
        help_text='Comentarios y evaluación de la reunión/entrevista de contratación'
    )
    
    # Relaciones
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name='Empresa'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_employees',
        verbose_name='Creado por'
    )
    
    # Estados
    STATUS_CHOICES = [
        ('candidate', 'Candidato'),
        ('in_process', 'En trámites'),
        ('employee', 'Empleado'),
        ('not_employee', 'No empleado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='candidate',
        verbose_name='Estado'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de aplicación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_candidate(self):
        return self.status == 'candidate'
    
    def is_in_process(self):
        return self.status == 'in_process'
    
    def is_employee(self):
        return self.status == 'employee'
    
    def is_not_employee(self):
        return self.status == 'not_employee'
    
    def get_status_color(self):
        """Devuelve el color para el badge según el estado"""
        colors = {
            'candidate': 'primary',
            'in_process': 'warning',
            'employee': 'success',
            'not_employee': 'danger',
        }
        return colors.get(self.status, 'secondary')


class EmployeePayroll(models.Model):
    """Modelo para gestionar nóminas de empleados"""
    
    # Relación con el empleado
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name='Empleado'
    )
    
    # Información de la nómina
    period_month = models.PositiveIntegerField(
        verbose_name='Mes',
        help_text='Mes de la nómina (1-12)'
    )
    period_year = models.PositiveIntegerField(
        verbose_name='Año',
        help_text='Año de la nómina'
    )
    
    # Archivos
    payroll_pdf = models.FileField(
        upload_to='payrolls/',
        verbose_name='Nómina (PDF)',
        help_text='Archivo PDF de la nómina'
    )
    payment_receipt = models.FileField(
        upload_to='payment_receipts/',
        null=True,
        blank=True,
        verbose_name='Comprobante de pago',
        help_text='Archivo del comprobante de pago (opcional)'
    )
    
    # Información adicional
    gross_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Salario bruto'
    )
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Salario neto'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas',
        help_text='Notas adicionales sobre esta nómina'
    )
    
    # Control
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_payrolls',
        verbose_name='Creado por'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de registro'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-period_year', '-period_month', '-created_at']
        verbose_name = 'Nómina de Empleado'
        verbose_name_plural = 'Nóminas de Empleados'
        unique_together = ['employee', 'period_month', 'period_year']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_period_display()}"
    
    def get_period_display(self):
        """Devuelve el período en formato legible"""
        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return f"{months.get(self.period_month, self.period_month)}/{self.period_year}"
    
    def has_payment_receipt(self):
        """Verifica si tiene comprobante de pago"""
        return bool(self.payment_receipt)


class JobApplicationToken(models.Model):
    """Modelo para gestionar tokens de aplicación pública a empleos"""
    
    # Token único
    application_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de aplicación'
    )
    
    # Información del puesto
    job_title = models.CharField(
        max_length=150,
        verbose_name='Título del puesto'
    )
    job_description = models.TextField(
        verbose_name='Descripción del puesto'
    )
    proposed_salary_euros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Salario propuesto (EUR)',
        help_text='Salario que la empresa está dispuesta a pagar'
    )
    
    # Configuración
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='job_application_tokens',
        verbose_name='Empresa'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_job_tokens',
        verbose_name='Creado por'
    )
    
    # Estado y expiración
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de expiración'
    )
    max_applications = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Máximo de aplicaciones'
    )
    application_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Aplicaciones recibidas'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Token de Aplicación de Empleo'
        verbose_name_plural = 'Tokens de Aplicación de Empleo'
    
    def __str__(self):
        return f"{self.job_title} - {self.application_token}"
    
    def is_valid(self):
        """Verifica si el token está válido para aplicaciones"""
        if not self.is_active:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        if self.max_applications and self.application_count >= self.max_applications:
            return False
        
        return True
    
    def get_public_url(self, request=None):
        """Devuelve la URL pública para aplicar al empleo"""
        from django.urls import reverse
        url = reverse('public_job_application', kwargs={'token': self.application_token})
        if request:
            return request.build_absolute_uri(url)
        return url
    
    def get_qr_data(self):
        """Datos para generar código QR"""
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}{self.get_public_url()}"


class Agreement(models.Model):
    """Modelo para gestionar acuerdos/contratos con firma digital"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicado'),
        ('signed', 'Firmado'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Información básica del acuerdo
    title = models.CharField(
        max_length=200,
        verbose_name='Título del Acuerdo'
    )
    body = models.TextField(
        verbose_name='Cuerpo del Acuerdo',
        help_text='Contenido completo del acuerdo/contrato'
    )
    
    # Control de estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Estado'
    )
    
    # URLs y tokens
    public_token = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Token Público'
    )
    
    # Metadatos
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Empresa'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_agreements',
        verbose_name='Creado por'
    )
    
    # Control de fechas
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de publicación'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de expiración'
    )
    
    # Configuración
    max_signers = models.PositiveIntegerField(
        default=10,
        verbose_name='Máximo de firmantes',
        help_text='Número máximo de personas que pueden firmar este acuerdo'
    )
    requires_approval = models.BooleanField(
        default=False,
        verbose_name='Requiere aprobación',
        help_text='Las firmas requieren aprobación antes de ser válidas'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Acuerdo'
        verbose_name_plural = 'Acuerdos'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.public_token:
            import secrets
            self.public_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    @property
    def is_editable(self):
        """Un acuerdo es editable si no tiene firmas válidas"""
        return not self.signatures.filter(is_valid=True).exists()
    
    @property
    def signature_count(self):
        """Número de firmas válidas"""
        return self.signatures.filter(is_valid=True).count()
    
    @property
    def is_expired(self):
        """Verifica si el acuerdo ha expirado"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def can_be_signed(self):
        """Verifica si el acuerdo puede ser firmado"""
        if self.status != 'published':
            return False
        if self.is_expired:
            return False
        if self.max_signers and self.signature_count >= self.max_signers:
            return False
        return True
    
    def get_public_url(self, request=None):
        """URL pública para firmar el acuerdo"""
        from django.urls import reverse
        url = reverse('public_agreement_sign', kwargs={'token': self.public_token})
        if request:
            return request.build_absolute_uri(url)
        return url
    
    def generate_ai_content(self, prompt_addition=""):
        """Generar contenido del acuerdo con IA basado en el título"""
        from tickets.models import SystemConfiguration
        
        config = SystemConfiguration.objects.first()
        if not config or not config.ai_chat_enabled or not config.openai_api_key:
            return None
            
        try:
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            base_prompt = f"""
Genera el contenido completo de un acuerdo/contrato profesional con el título: "{self.title}"

El acuerdo debe incluir:
1. Introducción y propósito
2. Términos y condiciones principales
3. Derechos y obligaciones de las partes
4. Cláusulas de cumplimiento
5. Términos de vigencia
6. Cláusulas de resolución de conflictos
7. Firmas y fecha

Haz que sea profesional, claro y legalmente sólido.
Usa un lenguaje formal pero comprensible.
Incluye espacios para nombres y firmas al final.

{prompt_addition}
"""
            
            response = client.chat.completions.create(
                model=config.openai_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto abogado especializado en redacción de contratos y acuerdos legales."},
                    {"role": "user", "content": base_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generando contenido IA: {e}")
            return None


class AgreementSignature(models.Model):
    """Modelo para las firmas de acuerdos"""
    
    # Relación con el acuerdo
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name='signatures',
        verbose_name='Acuerdo'
    )
    
    # Información del firmante
    signer_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del firmante'
    )
    signer_email = models.EmailField(
        verbose_name='Email del firmante'
    )
    signature_data = models.TextField(
        verbose_name='Datos de la firma',
        help_text='Datos de la firma digital (base64)'
    )
    
    # Control de firma
    signed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de firma'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    
    # Estado de la firma
    is_valid = models.BooleanField(
        default=True,
        verbose_name='Firma válida'
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name='Firma aprobada'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_signatures',
        verbose_name='Aprobado por'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación'
    )
    
    # Descarga del PDF
    pdf_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='PDF descargado en'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Veces descargado'
    )
    
    class Meta:
        ordering = ['-signed_at']
        verbose_name = 'Firma de Acuerdo'
        verbose_name_plural = 'Firmas de Acuerdos'
        unique_together = ['agreement', 'signer_email']
    
    def __str__(self):
        return f"{self.signer_name} - {self.agreement.title}"
    
    def get_download_url(self, request=None):
        """URL para descargar el PDF firmado"""
        from django.urls import reverse
        url = reverse('download_signed_agreement', kwargs={
            'agreement_token': self.agreement.public_token,
            'signature_id': self.pk
        })
        if request:
            return request.build_absolute_uri(url)
        return url


class LandingPage(models.Model):
    """Modelo para Landing Pages de campañas de marketing"""
    
    # Información básica
    nombre_producto = models.CharField(
        max_length=200,
        verbose_name='Nombre del Producto'
    )
    descripcion = models.TextField(
        verbose_name='Descripción del Producto',
        help_text='Descripción que aparecerá en la landing page'
    )
    imagen = models.ImageField(
        upload_to='landing_pages/',
        blank=True,
        null=True,
        verbose_name='Imagen del Producto',
        help_text='Imagen principal de la landing page'
    )
    
    # Configuración de URL pública
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL de la Landing Page',
        help_text='URL única para acceder a la landing page (ej: mi-producto)'
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name='Página Activa',
        help_text='Si está activa, la landing page será accesible públicamente'
    )
    
    # Configuración de diseño
    color_principal = models.CharField(
        max_length=7,
        default='#00A651',
        verbose_name='Color Principal',
        help_text='Color principal de la landing page (formato HEX: #00A651)'
    )
    color_secundario = models.CharField(
        max_length=7,
        default='#E8F5E8',
        verbose_name='Color Secundario',
        help_text='Color secundario para fondos (formato HEX: #E8F5E8)'
    )
    
    # Configuración del formulario
    titulo_formulario = models.CharField(
        max_length=200,
        default='VEA TODAS LAS DEMOSTRACIONES',
        verbose_name='Título del Formulario'
    )
    subtitulo_formulario = models.TextField(
        default='Salesforce acerca a las empresas con sus clientes. Vea nuestras demostraciones gratuitas y obtenga más información sobre cómo podemos ayudar a su negocio.',
        verbose_name='Subtítulo del Formulario'
    )
    
    # Configuración de empresa/campaña
    empresa_campana = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Empresa de la Campaña',
        help_text='Nombre de la empresa que ejecuta la campaña'
    )
    
    # Configuración de Telegram
    telegram_bot_token = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Bot Token de Telegram',
        help_text='Token del bot de Telegram para enviar notificaciones (ej: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)'
    )
    telegram_chat_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Chat ID de Telegram',
        help_text='ID del chat o canal donde enviar las notificaciones (ej: -1001234567890 o @mi_canal)'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # Estadísticas
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Número de visitas'
    )
    submissions_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Formularios enviados'
    )
    
    class Meta:
        verbose_name = 'Landing Page'
        verbose_name_plural = 'Landing Pages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre_producto} - {self.slug}"
    
    def get_public_url(self):
        """URL pública de la landing page"""
        from django.urls import reverse
        return reverse('landing_page_public', kwargs={'slug': self.slug})
    
    def get_absolute_url(self):
        """URL para el detalle de la landing page en admin"""
        from django.urls import reverse
        return reverse('landing_page_detail', kwargs={'pk': self.pk})
    
    def increment_views(self):
        """Incrementar contador de visitas"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_submissions(self):
        """Incrementar contador de envíos"""
        self.submissions_count += 1
        self.save(update_fields=['submissions_count'])
    
    @property
    def total_views(self):
        """Total de vistas de la landing page"""
        return self.views_count
    
    @property
    def total_submissions(self):
        """Total de envíos de la landing page"""
        return self.submissions_count
    
    @property
    def conversion_rate(self):
        """Tasa de conversión en porcentaje"""
        if self.views_count > 0:
            return round((self.submissions_count / self.views_count) * 100, 1)
        return 0


class LandingPageSubmission(models.Model):
    """Modelo para los envíos de formularios de landing pages"""
    
    landing_page = models.ForeignKey(
        LandingPage,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Landing Page'
    )
    
    # Datos del formulario
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    apellido = models.CharField(
        max_length=100,
        verbose_name='Apellido'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    empresa = models.CharField(
        max_length=200,
        verbose_name='Empresa'
    )
    mensaje = models.TextField(
        blank=True,
        verbose_name='Mensaje o comentarios',
        help_text='Cuéntanos más sobre tus necesidades o proyecto'
    )
    
    # Metadatos de seguimiento
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name='User Agent'
    )
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Source'
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Medium'
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Campaign'
    )
    
    # Estado
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de envío'
    )
    processed = models.BooleanField(
        default=False,
        verbose_name='Procesado'
    )
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de procesamiento'
    )
    processed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='processed_submissions',
        verbose_name='Procesado por'
    )
    
    # Evaluación de IA
    ai_evaluated = models.BooleanField(
        default=False,
        verbose_name='Evaluado por IA'
    )
    ai_evaluation_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de evaluación IA'
    )
    ai_company_score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Puntuación Empresa (1-10)',
        help_text='Evaluación de la calidad/seriedad de la empresa'
    )
    ai_contact_score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Puntuación Contacto (1-10)',
        help_text='Evaluación de la calidad del contacto'
    )
    ai_project_score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Puntuación Proyecto (1-10)',
        help_text='Evaluación del potencial del proyecto'
    )
    ai_overall_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Puntuación General',
        help_text='Puntuación promedio general'
    )
    ai_evaluation_summary = models.TextField(
        blank=True,
        verbose_name='Resumen de Evaluación IA',
        help_text='Resumen detallado de la evaluación'
    )
    ai_recommendations = models.TextField(
        blank=True,
        verbose_name='Recomendaciones IA',
        help_text='Recomendaciones de seguimiento'
    )
    ai_priority_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        blank=True,
        verbose_name='Nivel de Prioridad IA'
    )
    
    class Meta:
        verbose_name = 'Envío de Landing Page'
        verbose_name_plural = 'Envíos de Landing Pages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.landing_page.nombre_producto}"
    
    def evaluate_with_ai(self):
        """Evalúa el envío usando IA"""
        from .ai_landing_evaluator import evaluate_landing_submission
        
        try:
            result = evaluate_landing_submission(self)
            
            # Guardar resultados
            self.ai_evaluated = True
            self.ai_evaluation_date = timezone.now()
            self.ai_company_score = result.get('company_score')
            self.ai_contact_score = result.get('contact_score')
            self.ai_project_score = result.get('project_score')
            self.ai_overall_score = result.get('overall_score')
            self.ai_evaluation_summary = result.get('summary')
            self.ai_recommendations = result.get('recommendations')
            self.ai_priority_level = result.get('priority_level')
            
            self.save()
            return True
            
        except Exception as e:
            print(f"Error evaluando con IA: {e}")
            return False


class SharedFile(models.Model):
    """Modelo para gestionar archivos compartidos"""
    
    title = models.CharField(
        max_length=200, 
        verbose_name='Título del Archivo'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Descripción',
        help_text='Descripción opcional del archivo'
    )
    file = models.FileField(
        upload_to='shared_files/%Y/%m/',
        verbose_name='Archivo'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='shared_files',
        verbose_name='Empresa',
        null=True,
        blank=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name='Subido por',
        null=True,
        blank=True
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Público',
        help_text='Si está marcado, todos los usuarios de la empresa pueden ver este archivo'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tamaño del archivo (bytes)'
    )
    file_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de archivo'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Número de descargas'
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Última actualización'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Archivo Compartido'
        verbose_name_plural = 'Archivos Compartidos'
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    def get_file_size_display(self):
        """Convierte el tamaño del archivo a formato legible"""
        if not self.file_size:
            return "Desconocido"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_file_extension(self):
        """Obtiene la extensión del archivo"""
        if self.file:
            return os.path.splitext(self.file.name)[1][1:].upper()
        return ""
    
    def save(self, *args, **kwargs):
        if self.file:
            # Obtener tamaño del archivo
            self.file_size = self.file.size
            
            # Obtener tipo de archivo basado en la extensión
            ext = self.get_file_extension().lower()
            file_type_map = {
                'pdf': 'PDF Document',
                'doc': 'Word Document',
                'docx': 'Word Document',
                'xls': 'Excel Spreadsheet',
                'xlsx': 'Excel Spreadsheet',
                'ppt': 'PowerPoint Presentation',
                'pptx': 'PowerPoint Presentation',
                'txt': 'Text File',
                'jpg': 'Image',
                'jpeg': 'Image',
                'png': 'Image',
                'gif': 'Image',
                'zip': 'Archive',
                'rar': 'Archive',
                '7z': 'Archive',
            }
            self.file_type = file_type_map.get(ext, 'Archivo')
        
        super().save(*args, **kwargs)


class SharedFileDownload(models.Model):
    """Modelo para rastrear descargas de archivos compartidos"""
    
    shared_file = models.ForeignKey(
        SharedFile,
        on_delete=models.CASCADE,
        related_name='downloads',
        verbose_name='Archivo Compartido'
    )
    downloaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='file_downloads',
        verbose_name='Descargado por',
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    downloaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de descarga'
    )
    
    class Meta:
        ordering = ['-downloaded_at']
        verbose_name = 'Descarga de Archivo'
        verbose_name_plural = 'Descargas de Archivos'
    
    def __str__(self):
        user = self.downloaded_by.username if self.downloaded_by else 'Anónimo'
        return f"{self.shared_file.title} - {user} - {self.downloaded_at}"


class Recording(models.Model):
    """Modelo para gestionar grabaciones de audio con transcripción IA"""
    
    TRANSCRIPTION_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completada'),
        ('failed', 'Fallida'),
    ]
    
    title = models.CharField(
        max_length=200, 
        verbose_name='Título de la grabación'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Descripción',
        help_text='Descripción opcional de la grabación'
    )
    audio_file = models.FileField(
        upload_to='recordings/%Y/%m/',
        verbose_name='Archivo de audio'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='recordings',
        verbose_name='Empresa',
        null=True,
        blank=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_recordings',
        verbose_name='Subido por',
        null=True,
        blank=True
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Público',
        help_text='Si está marcado, todos los usuarios de la empresa pueden ver esta grabación'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tamaño del archivo (bytes)'
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duración en segundos'
    )
    
    # Campos de transcripción
    transcription_status = models.CharField(
        max_length=20,
        choices=TRANSCRIPTION_STATUS_CHOICES,
        default='pending',
        verbose_name='Estado de transcripción'
    )
    transcription_text = models.TextField(
        blank=True,
        verbose_name='Texto transcrito'
    )
    transcription_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Confianza de transcripción (%)',
        help_text='Porcentaje de confianza de la transcripción'
    )
    transcription_language = models.CharField(
        max_length=10,
        default='es',
        verbose_name='Idioma detectado'
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Última actualización'
    )
    transcribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de transcripción'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Grabación'
        verbose_name_plural = 'Grabaciones'
    
    def __str__(self):
        company_name = self.company.name if self.company else 'Sin empresa'
        return f"{self.title} - {company_name}"
    
    def get_file_size_display(self):
        """Convierte el tamaño del archivo a formato legible"""
        if not self.file_size:
            return "Desconocido"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_duration_display(self):
        """Convierte la duración a formato legible"""
        if not self.duration_seconds:
            return "Desconocida"
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_audio_extension(self):
        """Obtiene la extensión del archivo de audio"""
        if self.audio_file:
            return os.path.splitext(self.audio_file.name)[1][1:].upper()
        return ""
    
    def save(self, *args, **kwargs):
        if self.audio_file:
            # Obtener tamaño del archivo
            self.file_size = self.audio_file.size
        
        super().save(*args, **kwargs)


class RecordingPlayback(models.Model):
    """Modelo para rastrear reproducciones de grabaciones"""
    
    recording = models.ForeignKey(
        Recording,
        on_delete=models.CASCADE,
        related_name='playbacks',
        verbose_name='Grabación'
    )
    played_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recording_playbacks',
        verbose_name='Reproducido por',
        null=True,
        blank=True
    )
    played_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de reproducción'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        ordering = ['-played_at']
        verbose_name = 'Reproducción'
        verbose_name_plural = 'Reproducciones'
    
    def __str__(self):
        user = self.played_by.username if self.played_by else 'Anónimo'
        return f"{self.recording.title} - {user} - {self.played_at}"


class PageVisit(models.Model):
    """Modelo para registrar visitas a páginas públicas"""
    
    PAGE_CHOICES = [
        ('home', 'Página de Inicio'),
        ('blog', 'Blog'),
        ('blog_post', 'Artículo de Blog'),
        ('conceptos', 'Conceptos Públicos'),
        ('contact', 'Contacto'),
        ('landing', 'Landing Page'),
        ('course_public', 'Curso Público'),
        ('ticket_public', 'Ticket Público'),
        ('other', 'Otra'),
    ]
    
    # Información de la página visitada
    page_type = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        verbose_name='Tipo de Página'
    )
    page_url = models.URLField(
        max_length=500,
        verbose_name='URL Visitada'
    )
    page_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Título de la Página'
    )
    
    # Información del visitante
    ip_address = models.GenericIPAddressField(
        verbose_name='Dirección IP'
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='País'
    )
    country_code = models.CharField(
        max_length=2,
        blank=True,
        verbose_name='Código de País'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Región/Estado'
    )
    
    # Información técnica
    user_agent = models.TextField(
        verbose_name='User Agent'
    )
    browser = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Navegador'
    )
    browser_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Versión del Navegador'
    )
    operating_system = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Sistema Operativo'
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Tipo de Dispositivo'
    )
    is_mobile = models.BooleanField(
        default=False,
        verbose_name='Es Móvil'
    )
    is_bot = models.BooleanField(
        default=False,
        verbose_name='Es Bot'
    )
    
    # Información de referencia
    referrer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Página de Referencia'
    )
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Source'
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Medium'
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='UTM Campaign'
    )
    
    # Información de sesión
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID de Sesión'
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duración en Segundos'
    )
    
    # Metadatos
    visited_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Visita'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        ordering = ['-visited_at']
        verbose_name = 'Visita a Página'
        verbose_name_plural = 'Visitas a Páginas'
        indexes = [
            models.Index(fields=['page_type', 'visited_at']),
            models.Index(fields=['ip_address', 'visited_at']),
            models.Index(fields=['country_code']),
            models.Index(fields=['is_bot']),
        ]
    
    def __str__(self):
        return f"{self.get_page_type_display()} - {self.ip_address} - {self.visited_at}"
    
    @property
    def location(self):
        """Devuelve una representación legible de la ubicación"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts) if parts else 'Desconocida'
    
    @property
    def browser_info(self):
        """Devuelve información del navegador formateada"""
        if self.browser and self.browser_version:
            return f"{self.browser} {self.browser_version}"
        elif self.browser:
            return self.browser
        return 'Desconocido'


class AIBlogConfigurator(models.Model):
    """Configurador de IA para generar contenido de blog automáticamente"""
    
    # Información básica
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre del Configurador',
        help_text='Nombre descriptivo para identificar este configurador'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción opcional de qué tipo de contenido genera'
    )
    
    # Configuración de palabras clave
    keywords = models.TextField(
        verbose_name='Palabras Clave',
        help_text='Palabras clave separadas por comas para generar contenido (ej: tecnología, desarrollo, python)'
    )
    
    # Configuración de generación
    topic_template = models.TextField(
        default='Escribe un artículo completo sobre {keyword} con ejemplos prácticos y consejos útiles.',
        verbose_name='Plantilla de Tema',
        help_text='Plantilla para generar el prompt. Usa {keyword} donde quieras insertar la palabra clave'
    )
    
    content_length = models.CharField(
        max_length=50,
        choices=[
            ('short', 'Corto (500-800 palabras)'),
            ('medium', 'Medio (800-1200 palabras)'),
            ('long', 'Largo (1200-2000 palabras)'),
        ],
        default='medium',
        verbose_name='Longitud del Contenido'
    )
    
    content_style = models.CharField(
        max_length=50,
        choices=[
            ('professional', 'Profesional'),
            ('casual', 'Casual'),
            ('technical', 'Técnico'),
            ('educational', 'Educativo'),
            ('news', 'Noticia'),
        ],
        default='professional',
        verbose_name='Estilo del Contenido'
    )
    
    # Configuración de programación
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo, el configurador puede generar contenido automáticamente'
    )
    
    schedule_time = models.TimeField(
        default='10:00',
        verbose_name='Hora de Ejecución',
        help_text='Hora del día para ejecutar la generación automática (formato 24h)'
    )
    
    frequency_days = models.PositiveIntegerField(
        default=1,
        verbose_name='Frecuencia (días)',
        help_text='Cada cuántos días ejecutar (1 = diario, 7 = semanal, etc.)'
    )
    
    max_posts_per_run = models.PositiveIntegerField(
        default=1,
        verbose_name='Máximo Posts por Ejecución',
        help_text='Número máximo de posts a generar en cada ejecución'
    )
    
    # Configuración de categoría
    default_category = models.ForeignKey(
        'BlogCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Categoría por Defecto',
        help_text='Categoría a asignar a los posts generados'
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Ejecución'
    )
    total_posts_generated = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Posts Generados'
    )
    
    class Meta:
        verbose_name = 'Configurador de IA para Blog'
        verbose_name_plural = 'Configuradores de IA para Blog'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {'Activo' if self.is_active else 'Inactivo'}"
    
    @property
    def keywords_list(self):
        """Devuelve las palabras clave como lista"""
        return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
    
    @property
    def next_run_time(self):
        """Calcula la próxima fecha de ejecución"""
        from datetime import datetime, timedelta
        if not self.last_run:
            # Si nunca se ha ejecutado, usar hoy
            today = datetime.now().date()
            return datetime.combine(today, self.schedule_time)
        
        # Calcular próxima ejecución basada en frecuencia
        next_date = self.last_run.date() + timedelta(days=self.frequency_days)
        return datetime.combine(next_date, self.schedule_time)
    
    def should_run(self):
        """Determina si el configurador debe ejecutarse ahora"""
        if not self.is_active:
            return False
        
        from datetime import datetime
        now = datetime.now()
        
        # Si nunca se ha ejecutado, puede ejecutarse
        if not self.last_run:
            return True
        
        # Verificar si ha pasado el tiempo suficiente según la frecuencia
        next_run = self.next_run_time
        return now >= next_run
    
    def should_run_now(self):
        """Verifica si debe ejecutarse ahora"""
        if not self.is_active:
            return False
        
        from django.utils import timezone
        now = timezone.now()
        next_run = self.next_run_time
        
        # Permitir un margen de 5 minutos
        return now >= next_run and now <= next_run + timedelta(minutes=5)


class AIBlogGenerationLog(models.Model):
    """Log de generaciones de contenido por IA"""
    
    configurator = models.ForeignKey(
        AIBlogConfigurator,
        on_delete=models.CASCADE,
        related_name='generation_logs',
        verbose_name='Configurador'
    )
    
    keyword_used = models.CharField(
        max_length=200,
        verbose_name='Palabra Clave Utilizada'
    )
    
    generated_post = models.ForeignKey(
        'BlogPost',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Post Generado'
    )
    
    prompt_used = models.TextField(
        verbose_name='Prompt Utilizado'
    )
    
    generation_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Exitoso'),
            ('error', 'Error'),
            ('pending', 'Pendiente'),
        ],
        default='pending',
        verbose_name='Estado de Generación'
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de Error'
    )
    
    execution_time_seconds = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Tiempo de Ejecución (segundos)'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Log de Generación IA'
        verbose_name_plural = 'Logs de Generación IA'
        ordering = ['-created_at']
    
    def __str__(self):
        status_icon = '✅' if self.generation_status == 'success' else '❌' if self.generation_status == 'error' else '⏳'
        return f"{status_icon} {self.configurator.name} - {self.keyword_used} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"


class MultipleDocumentation(models.Model):
    """Modelo para gestionar documentación múltiple en una sola URL pública"""
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título de la Documentación'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción de qué contiene esta documentación'
    )
    
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name='Token Público',
        help_text='Token único para acceso público'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo, se puede acceder públicamente'
    )
    
    # Protección con contraseña
    password_protected = models.BooleanField(
        default=False,
        verbose_name='Protegido con contraseña',
        help_text='Si está marcado, se requerirá una contraseña para acceder'
    )
    access_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Contraseña de acceso',
        help_text='Contraseña requerida para acceder a la documentación pública'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Creado por'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    class Meta:
        verbose_name = 'Documentación Múltiple'
        verbose_name_plural = 'Documentaciones Múltiples'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_public_url(self):
        """Obtiene la URL pública para compartir"""
        from django.urls import reverse
        return reverse('multiple_documentation_public', kwargs={'token': self.public_token})


class MultipleDocumentationItem(models.Model):
    """Modelo para cada archivo dentro de una documentación múltiple"""
    
    documentation = models.ForeignKey(
        MultipleDocumentation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Documentación'
    )
    
    number = models.PositiveIntegerField(
        verbose_name='Número',
        help_text='Número de orden del documento'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre del Documento'
    )
    
    file = models.FileField(
        upload_to='multiple_documentation/',
        verbose_name='Archivo',
        help_text='Archivo a compartir'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción del archivo'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Item de Documentación'
        verbose_name_plural = 'Items de Documentación'
        ordering = ['number']
        unique_together = ['documentation', 'number']
    
    def __str__(self):
        return f"{self.number}. {self.name}"
    
    def get_file_size(self):
        """Obtiene el tamaño del archivo en formato legible"""
        try:
            size = self.file.size
            for unit in ['bytes', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "N/A"
    
    def get_file_extension(self):
        """Obtiene la extensión del archivo"""
        import os
        return os.path.splitext(self.file.name)[1].lower() if self.file else ""


class MultipleDocumentationStats(models.Model):
    """Modelo para estadísticas de documentación múltiple"""
    
    documentation = models.ForeignKey(
        MultipleDocumentation,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='Documentación'
    )
    
    # Estadísticas de página
    page_views = models.PositiveIntegerField(
        default=0,
        verbose_name='Visualizaciones de Página',
        help_text='Número total de veces que se ha visitado la página pública'
    )
    
    unique_visitors = models.PositiveIntegerField(
        default=0,
        verbose_name='Visitantes Únicos',
        help_text='Número de visitantes únicos (basado en IP)'
    )
    
    # Estadísticas de descargas
    total_downloads = models.PositiveIntegerField(
        default=0,
        verbose_name='Descargas Totales',
        help_text='Número total de archivos descargados'
    )
    
    # Fechas de seguimiento
    first_view_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Primera Visualización'
    )
    
    last_view_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Visualización'
    )
    
    last_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Descarga'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    class Meta:
        verbose_name = 'Estadística de Documentación'
        verbose_name_plural = 'Estadísticas de Documentación'
        unique_together = ['documentation']
    
    def __str__(self):
        return f"Stats: {self.documentation.title}"
    
    def get_average_downloads_per_day(self):
        """Calcula el promedio de descargas por día"""
        if not self.first_view_date or self.total_downloads == 0:
            return 0
        
        days = (timezone.now() - self.first_view_date).days
        if days == 0:
            return self.total_downloads
        return round(self.total_downloads / days, 2)
    
    def get_conversion_rate(self):
        """Calcula la tasa de conversión (descargas/visualizaciones)"""
        if self.page_views == 0:
            return 0
        return round((self.total_downloads / self.page_views) * 100, 2)


class MultipleDocumentationItemStats(models.Model):
    """Modelo para estadísticas de archivos individuales"""
    
    item = models.OneToOneField(
        MultipleDocumentationItem,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='Archivo'
    )
    
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Número de Descargas'
    )
    
    unique_downloaders = models.PositiveIntegerField(
        default=0,
        verbose_name='Descargadores Únicos',
        help_text='Número de IPs únicas que han descargado este archivo'
    )
    
    first_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Primera Descarga'
    )
    
    last_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Descarga'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    class Meta:
        verbose_name = 'Estadística de Archivo'
        verbose_name_plural = 'Estadísticas de Archivos'
    
    def __str__(self):
        return f"Stats: {self.item.name} ({self.download_count} descargas)"
    
    def get_popularity_percentage(self):
        """Calcula el porcentaje de popularidad respecto a otros archivos de la misma documentación"""
        documentation_stats = self.item.documentation.stats.first()
        if not documentation_stats or documentation_stats.total_downloads == 0:
            return 0
        return round((self.download_count / documentation_stats.total_downloads) * 100, 2)


class MultipleDocumentationVisit(models.Model):
    """Modelo para trackear visitas individuales"""
    
    documentation = models.ForeignKey(
        MultipleDocumentation,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name='Documentación'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='Dirección IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    referer = models.URLField(
        blank=True,
        null=True,
        verbose_name='Referente'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora'
    )
    
    class Meta:
        verbose_name = 'Visita a Documentación'
        verbose_name_plural = 'Visitas a Documentación'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ip_address} - {self.documentation.title} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class MultipleDocumentationDownload(models.Model):
    """Modelo para trackear descargas individuales"""
    
    item = models.ForeignKey(
        MultipleDocumentationItem,
        on_delete=models.CASCADE,
        related_name='downloads',
        verbose_name='Archivo'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='Dirección IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    referer = models.URLField(
        blank=True,
        null=True,
        verbose_name='Referente'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora'
    )
    
    class Meta:
        verbose_name = 'Descarga de Archivo'
        verbose_name_plural = 'Descargas de Archivos'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ip_address} - {self.item.name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class TaskSchedule(models.Model):
    """Modelo para gestionar cronogramas de tareas con vista Gantt"""
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título del Cronograma'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='task_schedules',
        verbose_name='Empresa'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_schedules',
        verbose_name='Creado Por'
    )
    
    start_date = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    
    end_date = models.DateField(
        verbose_name='Fecha de Fin'
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name='Público',
        help_text='Si está activo, el cronograma será accesible públicamente'
    )
    
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token Público'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Cronograma de Tareas'
        verbose_name_plural = 'Cronogramas de Tareas'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_progress_percentage(self):
        """Calcula el porcentaje de progreso del cronograma"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(is_completed=True).count()
        return round((completed_tasks / total_tasks) * 100, 2)
    
    def get_total_tasks(self):
        """Retorna el total de tareas"""
        return self.tasks.count()
    
    def get_completed_tasks(self):
        """Retorna el total de tareas completadas"""
        return self.tasks.filter(is_completed=True).count()
    
    def get_pending_tasks(self):
        """Retorna el total de tareas pendientes"""
        return self.tasks.filter(is_completed=False).count()
    
    def get_overdue_tasks(self):
        """Retorna las tareas vencidas"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.tasks.filter(
            is_completed=False,
            end_date__lt=today
        ).count()
    
    def get_on_time_completion_rate(self):
        """Calcula el porcentaje de tareas completadas a tiempo"""
        completed_tasks = self.tasks.filter(is_completed=True)
        if completed_tasks.count() == 0:
            return 0
        on_time_tasks = completed_tasks.filter(
            completed_at__lte=models.F('end_date')
        ).count()
        return round((on_time_tasks / completed_tasks.count()) * 100, 2)
    
    def is_overdue(self):
        """Verifica si el cronograma está vencido"""
        from django.utils import timezone
        today = timezone.now().date()
        return today > self.end_date and self.get_progress_percentage() < 100
    
    def calculate_auto_dates(self):
        """Calcula automáticamente las fechas de inicio y fin basándose en las tareas"""
        tasks = self.tasks.all()
        if tasks.exists():
            # Fecha de inicio: la fecha más temprana de todas las tareas
            earliest_start = tasks.order_by('start_date').first().start_date
            # Fecha de fin: la fecha más tardía de todas las tareas
            latest_end = tasks.order_by('-end_date').first().end_date
            return earliest_start, latest_end
        return None, None
    
    def update_auto_dates(self):
        """Actualiza automáticamente las fechas del cronograma basándose en las tareas"""
        start_date, end_date = self.calculate_auto_dates()
        if start_date and end_date:
            self.start_date = start_date
            self.end_date = end_date
            self.save(update_fields=['start_date', 'end_date'])
    
    def get_total_days(self):
        """Calcula la duración total del cronograma en días laborables (excluyendo sábados y domingos)"""
        if not self.start_date or not self.end_date:
            return 0
        
        # Importar datetime para cálculos de días laborables
        from datetime import timedelta
        
        current_date = self.start_date
        business_days = 0
        
        while current_date <= self.end_date:
            # 0=Lunes, 1=Martes, ..., 6=Domingo
            # Solo contar lunes a viernes (0-4)
            if current_date.weekday() < 5:
                business_days += 1
            current_date += timedelta(days=1)
        
        return business_days
    
    def get_total_task_days(self):
        """Calcula la suma total de días de todas las tareas"""
        return sum(task.get_duration_days() for task in self.tasks.all())
    
    def get_total_task_hours(self):
        """Calcula la suma total de horas de todas las tareas (8 horas por día)"""
        return self.get_total_task_days() * 8
    
    def get_total_work_weeks(self):
        """Calcula la suma total de semanas de trabajo (40 horas por semana)"""
        total_hours = self.get_total_task_hours()
        if total_hours == 0:
            return 0
        return round(total_hours / 40, 1)


class ScheduleTask(models.Model):
    """Modelo para las tareas individuales del cronograma"""
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    schedule = models.ForeignKey(
        TaskSchedule,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Cronograma'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título de la Tarea'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    start_date = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    
    end_date = models.DateField(
        verbose_name='Fecha de Fin'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Prioridad'
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_tasks_assigned',
        verbose_name='Asignado A'
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Completada'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completada el'
    )
    
    progress_percentage = models.IntegerField(
        default=0,
        verbose_name='Porcentaje de Progreso',
        help_text='Progreso de 0 a 100'
    )
    
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_tasks',
        verbose_name='Dependencias'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Tarea del Cronograma'
        verbose_name_plural = 'Tareas del Cronograma'
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.schedule.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Si la tarea se marca como completada, establecer la fecha de completado
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
            self.progress_percentage = 100
        elif not self.is_completed:
            self.completed_at = None
        
        # Guardar la tarea primero
        super().save(*args, **kwargs)
        
        # Actualizar las fechas del cronograma automáticamente
        self.schedule.update_auto_dates()
    
    def is_overdue(self):
        """Verifica si la tarea está vencida"""
        from django.utils import timezone
        today = timezone.now().date()
        return not self.is_completed and today > self.end_date
    
    def get_duration_days(self):
        """Calcula la duración de la tarea en días laborables (excluyendo sábados y domingos)"""
        if not self.start_date or not self.end_date:
            return 0
        
        # Importar datetime para cálculos de días laborables
        from datetime import timedelta
        
        current_date = self.start_date
        business_days = 0
        
        while current_date <= self.end_date:
            # 0=Lunes, 1=Martes, ..., 6=Domingo
            # Solo contar lunes a viernes (0-4)
            if current_date.weekday() < 5:
                business_days += 1
            current_date += timedelta(days=1)
        
        return business_days
    
    def can_start(self):
        """Verifica si la tarea puede iniciar (todas sus dependencias completadas)"""
        return all(dep.is_completed for dep in self.dependencies.all())


class ScheduleComment(models.Model):
    """Modelo para comentarios en las tareas"""
    
    task = models.ForeignKey(
        ScheduleTask,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Tarea'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    
    comment = models.TextField(
        verbose_name='Comentario'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Comentario de Tarea'
        verbose_name_plural = 'Comentarios de Tareas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title}"


class TicketApproval(models.Model):
    """Modelo para aprobaciones de clientes en tickets públicos"""
    
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='client_approval',
        verbose_name='Ticket'
    )
    
    client_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del Cliente'
    )
    
    client_email = models.EmailField(
        verbose_name='Correo del Cliente'
    )
    
    approved_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Aprobación'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Notas Adicionales',
        help_text='Comentarios adicionales del cliente'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='Dirección IP',
        help_text='IP desde donde se realizó la aprobación'
    )
    
    class Meta:
        verbose_name = 'Aprobación de Cliente'
        verbose_name_plural = 'Aprobaciones de Clientes'
        ordering = ['-approved_at']
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - Aprobado por {self.client_name}"


class SatisfactionSurvey(models.Model):
    """Modelo para encuestas de satisfacción de clientes"""
    
    RATING_CHOICES = [
        (1, '1 - Muy Insatisfecho'),
        (2, '2 - Insatisfecho'),
        (3, '3 - Neutral'),
        (4, '4 - Satisfecho'),
        (5, '5 - Muy Satisfecho'),
    ]
    
    RESOLUTION_QUALITY_CHOICES = [
        (1, '1 - Muy Mala'),
        (2, '2 - Mala'),
        (3, '3 - Regular'),
        (4, '4 - Buena'),
        (5, '5 - Excelente'),
    ]
    
    RESPONSE_TIME_CHOICES = [
        (1, '1 - Muy Lento'),
        (2, '2 - Lento'),
        (3, '3 - Aceptable'),
        (4, '4 - Rápido'),
        (5, '5 - Muy Rápido'),
    ]
    
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='satisfaction_survey',
        verbose_name='Ticket'
    )
    
    client_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del Cliente'
    )
    
    client_email = models.EmailField(
        verbose_name='Correo del Cliente'
    )
    
    # Calificaciones
    overall_satisfaction = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name='Satisfacción General',
        help_text="¿Qué tan satisfecho está con el servicio general?"
    )
    
    resolution_quality = models.IntegerField(
        choices=RESOLUTION_QUALITY_CHOICES,
        verbose_name='Calidad de la Solución',
        help_text="¿Cómo califica la calidad de la solución proporcionada?"
    )
    
    response_time = models.IntegerField(
        choices=RESPONSE_TIME_CHOICES,
        verbose_name='Tiempo de Respuesta',
        help_text="¿Cómo califica nuestro tiempo de respuesta?"
    )
    
    communication = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name='Calidad de la Comunicación',
        help_text="¿Cómo califica la comunicación durante el proceso?"
    )
    
    # Comentarios
    what_went_well = models.TextField(
        blank=True,
        null=True,
        verbose_name='¿Qué funcionó bien?',
        help_text='Describa los aspectos positivos de nuestro servicio'
    )
    
    what_could_improve = models.TextField(
        blank=True,
        null=True,
        verbose_name='¿Qué se podría mejorar?',
        help_text='Sugerencias para mejorar nuestro servicio'
    )
    
    additional_comments = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentarios Adicionales',
        help_text='Cualquier otro comentario que desee compartir'
    )
    
    # Recomendación
    would_recommend = models.BooleanField(
        default=True,
        verbose_name='¿Recomendaría nuestros servicios?',
        help_text="¿Recomendaría nuestros servicios a otros?"
    )
    
    recommendation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Razón de recomendación',
        help_text='¿Por qué sí o por qué no recomendaría nuestros servicios?'
    )
    
    # Metadatos
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Envío'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='IP desde donde se realizó la encuesta'
    )
    
    class Meta:
        verbose_name = "Encuesta de Satisfacción"
        verbose_name_plural = "Encuestas de Satisfacción"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Encuesta de {self.client_name} para ticket #{self.ticket.id} - {self.overall_satisfaction}/5"
    
    @property
    def average_rating(self):
        """Calcula el promedio de todas las calificaciones"""
        ratings = [
            self.overall_satisfaction,
            self.resolution_quality,
            self.response_time,
            self.communication
        ]
        return round(sum(ratings) / len(ratings), 1)
    
    @property
    def rating_summary(self):
        """Devuelve un resumen de las calificaciones"""
        avg = self.average_rating
        if avg >= 4.5:
            return "Excelente"
        elif avg >= 3.5:
            return "Bueno"
        elif avg >= 2.5:
            return "Regular"
        else:
            return "Necesita Mejora"
    
    @property
    def rating_color(self):
        """Devuelve el color Bootstrap según la calificación"""
        avg = self.average_rating
        if avg >= 4.5:
            return "success"
        elif avg >= 3.5:
            return "primary"
        elif avg >= 2.5:
            return "warning"
        else:
            return "danger"


# Señales para actualizar automáticamente las fechas del cronograma
@receiver(post_save, sender=ScheduleTask)
def update_schedule_dates_on_task_save(sender, instance, **kwargs):
    """Actualiza las fechas del cronograma cuando se guarda una tarea"""
    instance.schedule.update_auto_dates()


@receiver(models.signals.post_delete, sender=ScheduleTask)
def update_schedule_dates_on_task_delete(sender, instance, **kwargs):
    """Actualiza las fechas del cronograma cuando se elimina una tarea"""
    instance.schedule.update_auto_dates()


class FinancialAction(models.Model):
    """Modelo para gestionar acciones financieras que se muestran en el ticker"""
    
    symbol = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Símbolo',
        help_text='Símbolo de la acción (ej: EUR/USD, AAPL, GOOGL)'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre',
        help_text='Nombre completo de la acción o par de divisas'
    )
    
    current_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Precio Actual',
        help_text='Se actualiza automáticamente desde APIs externas'
    )
    
    previous_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Precio Anterior',
        help_text='Se actualiza automáticamente desde APIs externas'
    )
    
    currency = models.CharField(
        max_length=10,
        default='USD',
        verbose_name='Moneda',
        help_text='Moneda en la que se cotiza (USD, EUR, etc.)'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Si está activa se muestra en el ticker'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el ticker (menor número = primera)'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        ordering = ['order', 'symbol']
        verbose_name = 'Acción Financiera'
        verbose_name_plural = 'Acciones Financieras'
    
    def __str__(self):
        price_display = self.current_price if self.current_price is not None else "N/A"
        return f"{self.symbol} - {price_display} {self.currency}"
    
    @property
    def price_change(self):
        """Calcula el cambio de precio"""
        if self.previous_price and self.current_price is not None:
            return self.current_price - self.previous_price
        return 0
    
    @property
    def price_change_percent(self):
        """Calcula el porcentaje de cambio"""
        if self.previous_price and self.previous_price != 0 and self.current_price is not None:
            return ((self.current_price - self.previous_price) / self.previous_price) * 100
        return 0
    
    @property
    def is_positive_change(self):
        """Determina si el cambio es positivo"""
        return self.price_change > 0
    
    @property
    def is_negative_change(self):
        """Determina si el cambio es negativo"""
        return self.price_change < 0
    
    @property
    def change_color_class(self):
        """Devuelve la clase CSS según el cambio"""
        if self.is_positive_change:
            return 'text-success'
        elif self.is_negative_change:
            return 'text-danger'
        return 'text-muted'
    
    def get_price_from_yesterday(self):
        """Obtiene el precio del día anterior a la misma hora aproximada"""
        from datetime import datetime, timedelta
        
        # Calcular la fecha y hora del día anterior
        yesterday = timezone.now() - timedelta(days=1)
        
        # Buscar el precio más cercano a la misma hora del día anterior
        # Con una ventana de +/- 2 horas
        start_time = yesterday - timedelta(hours=2)
        end_time = yesterday + timedelta(hours=2)
        
        history_record = self.price_history.filter(
            recorded_at__range=[start_time, end_time]
        ).order_by('recorded_at').first()
        
        if history_record:
            return history_record.price
        
        # Si no hay registro del día anterior, usar el previous_price actual
        return self.previous_price
    
    def save_price_history(self):
        """Guarda el precio actual en el historial"""
        FinancialPriceHistory.objects.create(
            financial_action=self,
            price=self.current_price
        )


class FinancialPriceHistory(models.Model):
    """Modelo para almacenar el historial de precios de las acciones financieras"""
    
    financial_action = models.ForeignKey(
        FinancialAction,
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name='Acción Financiera'
    )
    
    price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Precio'
    )
    
    recorded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Registro'
    )
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name = 'Historial de Precio'
        verbose_name_plural = 'Historiales de Precios'
        unique_together = ['financial_action', 'recorded_at']
    
    def __str__(self):
        return f"{self.financial_action.symbol} - {self.price} - {self.recorded_at}"


class Product(models.Model):
    """
    Modelo para gestionar productos
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre del Producto'
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio',
        help_text='Precio del producto'
    )
    
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada del producto'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está marcado, el producto estará disponible'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_products',
        verbose_name='Creado por'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return self.name
    
    def get_currency_symbol(self):
        """Obtiene el símbolo de la moneda configurada en el sistema"""
        config = SystemConfiguration.objects.first()
        if not config:
            return '€'  # Por defecto EUR
        
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'CAD': 'C$',
            'AUD': 'A$',
            'CHF': 'CHF',
            'CNY': '¥',
            'MXN': '$',
            'COP': '$',
        }
        return currency_symbols.get(config.default_currency, '€')
    
    def get_currency_code(self):
        """Obtiene el código de la moneda configurada en el sistema"""
        config = SystemConfiguration.objects.first()
        if not config:
            return 'EUR'
        return config.default_currency
    
    def get_formatted_price(self):
        """Obtiene el precio formateado con la moneda del sistema"""
        symbol = self.get_currency_symbol()
        return f"{symbol}{self.price:,.2f}"
    
    @property
    def price_with_currency(self):
        """Propiedad para obtener el precio con moneda fácilmente"""
        return self.get_formatted_price()


class ClientProjectAccess(models.Model):
    """Modelo para configurar el acceso público a proyectos para imputación de horas por clientes"""
    
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='client_access',
        verbose_name='Proyecto'
    )
    public_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='Token Público',
        help_text='Token único para acceso público al formulario de horas'
    )
    dashboard_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Token Dashboard Público',
        help_text='Token único para acceso público al dashboard de estadísticas'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está desactivado, el enlace público no funcionará'
    )
    max_entries_per_day = models.PositiveIntegerField(
        default=50,
        verbose_name='Máximo de entradas por día',
        help_text='Límite de entradas de tiempo que se pueden crear por día'
    )
    requires_phone = models.BooleanField(
        default=True,
        verbose_name='Requiere teléfono',
        help_text='Si es obligatorio que el cliente proporcione su teléfono'
    )
    allowed_categories = models.JSONField(
        default=list,
        verbose_name='Categorías permitidas',
        help_text='Lista de categorías que el cliente puede seleccionar'
    )
    instructions = models.TextField(
        blank=True,
        verbose_name='Instrucciones',
        help_text='Instrucciones que verá el cliente en el formulario'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        verbose_name = 'Acceso Público de Cliente'
        verbose_name_plural = 'Accesos Públicos de Clientes'
    
    def __str__(self):
        return f"Acceso público para {self.project.name}"
    
    def save(self, *args, **kwargs):
        if not self.public_token:
            self.public_token = self.generate_token()
        if not self.dashboard_token:
            self.dashboard_token = self.generate_token()
        if not self.allowed_categories:
            self.allowed_categories = ['capacitacion', 'pruebas', 'uso']
        super().save(*args, **kwargs)
    
    def generate_token(self):
        """Genera un token único"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def get_public_url(self):
        """Obtiene la URL pública para el formulario"""
        from django.urls import reverse
        return reverse('client_time_entry_form', kwargs={'token': self.public_token})
    
    def get_dashboard_url(self):
        """Obtiene la URL pública para el dashboard"""
        from django.urls import reverse
        return reverse('client_dashboard_public', kwargs={'token': self.dashboard_token})
    
    def can_accept_entries_today(self):
        """Verifica si se pueden aceptar más entradas hoy"""
        from django.utils import timezone
        today = timezone.now().date()
        today_entries = ClientTimeEntry.objects.filter(
            project=self.project,
            created_at__date=today
        ).count()
        return today_entries < self.max_entries_per_day


class ClientTimeEntry(models.Model):
    """Modelo para almacenar las entradas de tiempo de clientes"""
    
    CATEGORY_CHOICES = [
        ('capacitacion', 'Capacitación'),
        ('pruebas', 'Pruebas'),
        ('uso', 'Uso'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='client_time_entries',
        verbose_name='Proyecto'
    )
    client_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del Cliente',
        help_text='Nombre completo del cliente'
    )
    client_email = models.EmailField(
        verbose_name='Correo del Cliente',
        help_text='Correo electrónico del cliente'
    )
    client_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono del Cliente',
        help_text='Número de teléfono del cliente (opcional)'
    )
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Horas',
        help_text='Cantidad de horas a imputar (ej: 2.5)'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoría',
        help_text='Categoría de las horas imputadas'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción opcional del trabajo realizado'
    )
    entry_date = models.DateField(
        default=timezone.now,
        verbose_name='Fecha de las horas',
        help_text='Fecha cuando se realizaron las horas de trabajo'
    )
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP del Cliente',
        help_text='Dirección IP desde donde se registró la entrada'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
        help_text='Información del navegador del cliente'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        verbose_name = 'Entrada de Tiempo de Cliente'
        verbose_name_plural = 'Entradas de Tiempo de Clientes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client_name} ({self.client_email}) - {self.hours}h en {self.project.name} ({self.get_category_display()})"
    
    def get_formatted_hours(self):
        """Retorna las horas formateadas"""
        if self.hours == int(self.hours):
            return f"{int(self.hours)}h"
        return f"{self.hours}h"
