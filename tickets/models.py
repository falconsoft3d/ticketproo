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
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
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
    def create_entry(cls, user, project, notas_entrada=None):
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
