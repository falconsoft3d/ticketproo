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
