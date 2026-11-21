from django.utils.translation import gettext_lazy
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
import os
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=gettext_lazy('Nombre'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text=gettext_lazy('Color en formato hexadecimal (ej: #007bff)'),
        verbose_name=gettext_lazy('Color')
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activa'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    
    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Categoría')
        verbose_name_plural = gettext_lazy('Categorías')
    
    def __str__(self):
        return self.name


class Company(models.Model):
    """Modelo para gestionar empresas/clientes"""
    
    name = models.CharField(
        max_length=200, 
        unique=True, 
        verbose_name=gettext_lazy('Nombre de la Empresa')
    )
    description = models.TextField(
        blank=True, 
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional de la empresa')
    )
    address = models.CharField(
        max_length=300, 
        blank=True, 
        verbose_name=gettext_lazy('Dirección')
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name=gettext_lazy('Teléfono')
    )
    email = models.EmailField(
        blank=True, 
        verbose_name=gettext_lazy('Email de contacto')
    )
    website = models.URLField(
        blank=True, 
        verbose_name=gettext_lazy('Sitio web')
    )
    color = models.CharField(
        max_length=7, 
        default='#28a745',
        help_text=gettext_lazy('Color en formato hexadecimal (ej: #28a745)'),
        verbose_name=gettext_lazy('Color identificativo')
    )
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Logo de la empresa'),
        help_text=gettext_lazy('Logo de la empresa (opcional)')
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name=gettext_lazy('Empresa activa')
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=gettext_lazy('Última actualización')
    )
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        null=True,
        blank=True,
        editable=True,
        verbose_name=gettext_lazy('Token público'),
        help_text=gettext_lazy('Token único para acceso público a estadísticas')
    )
    client_requests_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token de Solicitudes'),
        help_text=gettext_lazy('Token único para que los clientes accedan a sus solicitudes')
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('UUID público'),
        help_text=gettext_lazy('Identificador único para URLs públicas')
    )
    business_objectives = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Objetivos Empresariales'),
        help_text=gettext_lazy('Objetivos, metas y KPIs estratégicos de la empresa. Estos serán considerados en los resúmenes ejecutivos generados por IA.')
    )
    
    # Información fiscal y de ubicación
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('NIF/CIF/Tax ID'),
        help_text=gettext_lazy('Número de identificación fiscal')
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Ciudad'),
        help_text=gettext_lazy('Ciudad de la empresa')
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Estado/Provincia'),
        help_text=gettext_lazy('Estado o provincia de la empresa')
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Código Postal'),
        help_text=gettext_lazy('Código postal')
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('País'),
        help_text=gettext_lazy('País de la empresa')
    )
    
    # Información bancaria
    bank_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre del Banco'),
        help_text=gettext_lazy('Nombre del banco')
    )
    bank_url = models.URLField(
        blank=True,
        verbose_name=gettext_lazy('URL del Banco'),
        help_text=gettext_lazy('Sitio web del banco')
    )
    bank_account_holder = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Titular de la Cuenta'),
        help_text=gettext_lazy('Nombre del titular de la cuenta bancaria')
    )
    bank_account = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Número de Cuenta'),
        help_text=gettext_lazy('IBAN o número de cuenta bancaria')
    )
    bank_swift = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('SWIFT/BIC'),
        help_text=gettext_lazy('Código SWIFT o BIC del banco')
    )
    
    # Condiciones de pago
    payment_terms = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Condiciones de Pago'),
        help_text=gettext_lazy('Términos y condiciones de pago (se mostrarán en las cotizaciones)')
    )
    payment_terms_description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción de Condiciones de Pago'),
        help_text=gettext_lazy('Descripción detallada de las condiciones de pago para las cotizaciones')
    )
    quotation_general_description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción General de Cotizaciones'),
        help_text=gettext_lazy('Descripción general que aparecerá en todas las cotizaciones de esta empresa')
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Empresa')
        verbose_name_plural = gettext_lazy('Empresas')
    
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
    
    def get_client_requests_url(self):
        """Obtiene la URL pública para que el cliente vea sus solicitudes"""
        from django.urls import reverse
        return reverse('public_client_requests', kwargs={'token': self.client_requests_token})
    
    def regenerate_client_requests_token(self):
        """Regenera el token para solicitudes de cliente"""
        self.client_requests_token = uuid.uuid4()
        self.save()
        return self.client_requests_token


class Project(models.Model):
    """Modelo para gestionar proyectos de trabajo"""
    
    STATUS_CHOICES = [
        ('planning', gettext_lazy('Planificación')),
        ('active', gettext_lazy('Activo')),
        ('on_hold', gettext_lazy('En Pausa')),
        ('completed', gettext_lazy('Completado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    name = models.CharField(max_length=200, unique=True, verbose_name=gettext_lazy('Nombre del Proyecto'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    color = models.CharField(
        max_length=7, 
        default='#28a745',
        help_text=gettext_lazy('Color en formato hexadecimal (ej: #28a745)'),
        verbose_name=gettext_lazy('Color')
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active', 
        verbose_name=gettext_lazy('Estado')
    )
    start_date = models.DateField(null=True, blank=True, verbose_name=gettext_lazy('Fecha de Inicio'))
    end_date = models.DateField(null=True, blank=True, verbose_name=gettext_lazy('Fecha de Fin'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_projects',
        verbose_name=gettext_lazy('Creado por')
    )
    assigned_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='assigned_projects',
        verbose_name=gettext_lazy('Usuarios Asignados'),
        help_text=gettext_lazy('Usuarios que tienen acceso a este proyecto')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    public_share_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token de Compartir Público'),
        help_text=gettext_lazy('Token único para compartir información del proyecto públicamente')
    )
    
    class Meta:
        ordering = ['-created_at', 'name']
        verbose_name = gettext_lazy('Proyecto')
        verbose_name_plural = gettext_lazy('Proyectos')
    
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
        """Genera un token unico para compartir el proyecto publicamente"""
        if not self.public_share_token:
            import secrets
            self.public_share_token = secrets.token_urlsafe(32)
            self.save()
        return self.public_share_token
    
    def get_public_share_url(self):
        if not self.public_share_token:
            self.generate_public_share_token()
        return "/public/project/" + str(self.public_share_token) + "/"
    
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
        ('low', gettext_lazy('Baja')),
        ('medium', gettext_lazy('Media')),
        ('high', gettext_lazy('Alta')),
        ('urgent', gettext_lazy('Urgente')),
    ]
    
    STATUS_CHOICES = [
        ('open', gettext_lazy('Abierto')),
        ('working', gettext_lazy('Trabajando')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('resolved', gettext_lazy('Resuelto')),
        ('closed', gettext_lazy('Cerrado')),
    ]
    
    TYPE_CHOICES = [
        ('desarrollo', gettext_lazy('Desarrollo')),
        ('error', gettext_lazy('Error')),
    ]
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título'))
    ticket_number = models.CharField(
        max_length=10, 
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Número de Ticket'),
        help_text=gettext_lazy('Formato: XX-XXX (ID Usuario-Secuencia)')
    )
    description = models.TextField(verbose_name=gettext_lazy('Descripción'))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=gettext_lazy('Categoría')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=gettext_lazy('Empresa/Cliente'),
        help_text=gettext_lazy('Empresa o cliente asociado al ticket')
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=gettext_lazy('Proyecto'),
        help_text=gettext_lazy('Proyecto asociado al ticket (opcional)')
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='open',
        verbose_name=gettext_lazy('Estado')
    )
    ticket_type = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default='desarrollo',
        verbose_name=gettext_lazy('Tipo')
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tickets',
        verbose_name=gettext_lazy('Creado por')
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tickets',
        verbose_name=gettext_lazy('Asignado a')
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Horas estimadas/trabajadas'),
        help_text=gettext_lazy('Cantidad de horas estimadas o trabajadas en el ticket')
    )
    # Campo para enlace único público
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token de compartir'),
        help_text=gettext_lazy('Token único para compartir el ticket públicamente')
    )
    is_public_shareable = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Compartir públicamente'),
        help_text=gettext_lazy('Permite que este ticket sea visible mediante un enlace público')
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Aprobado'),
        help_text=gettext_lazy('Indica si el ticket ha sido aprobado por el cliente')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tickets',
        verbose_name=gettext_lazy('Aprobado por'),
        help_text=gettext_lazy('Usuario que aprobó el ticket')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de aprobación'),
        help_text=gettext_lazy('Fecha y hora en que fue aprobado el ticket')
    )
    commit = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Commit'),
        help_text=gettext_lazy('Hash, URL o referencia del commit relacionado')
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Calificación'),
        help_text=gettext_lazy('Calificación del ticket de 1 a 5 estrellas')
    )
    source_survey_line = models.ForeignKey(
        'ProcessSurveyLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=gettext_lazy('Línea de levantamiento origen'),
        help_text=gettext_lazy('Línea de levantamiento de procesos a partir de la cual se generó este ticket'),
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Ticket')
        verbose_name_plural = gettext_lazy('Tickets')
    
    def generate_ticket_number(self):
        """Genera un numero de ticket unico con formato XX-XXX"""
        if self.ticket_number:
            return self.ticket_number
            
        # Formatear ID del usuario con ceros a la izquierda (2 digitos)
        user_id_formatted = "{:02d}".format(self.created_by.id)
        
        # Buscar el ultimo ticket creado por este usuario
        last_ticket = Ticket.objects.filter(
            created_by=self.created_by,
            ticket_number__startswith=user_id_formatted + "-"
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
            'working': 'bg-info text-dark',
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
        verbose_name=gettext_lazy('Ticket')
    )
    file = models.FileField(
        upload_to=ticket_attachment_upload_path,
        verbose_name=gettext_lazy('Archivo')
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre original')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Subido por')
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de subida')
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = gettext_lazy('Adjunto')
        verbose_name_plural = gettext_lazy('Adjuntos')
    
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
        verbose_name=gettext_lazy('Ticket')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Usuario')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Comentario'),
        help_text=gettext_lazy('Escribe tu comentario aquí')
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Mensaje del sistema'),
        help_text=gettext_lazy('Comentario generado automáticamente por el sistema')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Comentario')
        verbose_name_plural = gettext_lazy('Comentarios')
    
    def __str__(self):
        return f"Comentario de {self.user.username} en Ticket #{self.ticket.ticket_number}"
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar este comentario"""
        # Solo el autor del comentario (si es agente) puede editarlo
        from .utils import is_agent
        return self.user == user and is_agent(user)
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar este comentario"""
        # Los agentes pueden eliminar cualquier comentario
        from .utils import is_agent
        return is_agent(user)


class TicketHourLine(models.Model):
    """Modelo para registrar líneas de horas trabajadas en un ticket"""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='hour_lines',
        verbose_name=gettext_lazy('Ticket')
    )
    description = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción de la tarea o actividad realizada')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_hour_lines',
        verbose_name=gettext_lazy('Usuario')
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=gettext_lazy('Horas'),
        help_text=gettext_lazy('Cantidad de horas trabajadas en esta actividad')
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_hour_lines',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )

    class Meta:
        ordering = ['date', 'created_at']
        verbose_name = gettext_lazy('Línea de Horas')
        verbose_name_plural = gettext_lazy('Líneas de Horas')

    def __str__(self):
        return f"{self.description} - {self.user.get_full_name() or self.user.username} - {self.hours}h ({self.date})"


class UserProfile(models.Model):
    """Modelo para extender la información del usuario"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=gettext_lazy('Usuario')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Teléfono'),
        help_text=gettext_lazy('Número de teléfono de contacto')
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Biografía'),
        help_text=gettext_lazy('Descripción corta del usuario')
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Cargo'),
        help_text=gettext_lazy('Cargo o posición del usuario en la empresa')
    )
    descripcion_cargo = models.TextField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Descripción del Cargo'),
        help_text=gettext_lazy('Descripción detallada de las responsabilidades del cargo')
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=gettext_lazy('Preferencias de notificación'),
        help_text=gettext_lazy('Configuración de notificaciones del usuario')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa a la que pertenece el usuario')
    )
    
    # Campos de facturación
    precio_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=gettext_lazy('Precio por hora'),
        help_text=gettext_lazy('Precio de venta por hora de trabajo (€)')
    )
    coste_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=gettext_lazy('Coste por hora'),
        help_text=gettext_lazy('Coste interno por hora de trabajo (€)')
    )
    
    # Token para acceso público a tareas
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=gettext_lazy('Token público'),
        help_text=gettext_lazy('Token único para acceso público a tareas')
    )
    
    # Formulario de contacto público
    enable_public_contact_form = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Activar formulario de contacto público'),
        help_text=gettext_lazy('Permite que visitantes envíen formularios de contacto para crear empresas')
    )
    
    # Configuración de ubicación para el clima
    city = models.CharField(
        max_length=100,
        default='Valencia',
        verbose_name=gettext_lazy('Ciudad'),
        help_text=gettext_lazy('Ciudad para mostrar información del clima')
    )
    country = models.CharField(
        max_length=100,
        default='España',
        verbose_name=gettext_lazy('País'),
        help_text=gettext_lazy('País para mostrar información del clima')
    )
    country_code = models.CharField(
        max_length=2,
        default='ES',
        verbose_name=gettext_lazy('Código de país'),
        help_text=gettext_lazy('Código ISO de 2 letras del país (ej: ES, US, FR)')
    )
    
    # Fecha de cumpleaños
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de cumpleaños'),
        help_text=gettext_lazy('Fecha de nacimiento del usuario')
    )
    
    # Términos y condiciones para cotizaciones
    quote_terms_conditions = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Términos y Condiciones de Cotizaciones'),
        help_text=gettext_lazy('Términos y condiciones que se mostrarán en las cotizaciones rápidas')
    )
    
    # Permisos de visibilidad de contactos
    can_see_all_contacts = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Ver todos los contactos'),
        help_text=gettext_lazy('Si está activo, el usuario puede ver todos los contactos. Si no, solo ve los que creó o tiene asignados.')
    )

    # Campos para API REST
    enable_api_access = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Habilitar acceso a la API'),
        help_text=gettext_lazy('Permite que este usuario utilice la API REST del sistema')
    )
    api_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=gettext_lazy('Token de API'),
        help_text=gettext_lazy('Token único para autenticación en la API REST')
    )
    
    # Configuración de secuencia de facturas
    invoice_sequence_prefix = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Prefijo de Secuencia de Factura'),
        help_text=gettext_lazy('Prefijo para la secuencia de facturas (ej: MCVARQ/2025/)')
    )
    invoice_next_number = models.IntegerField(
        default=1,
        verbose_name=gettext_lazy('Próximo Número de Factura'),
        help_text=gettext_lazy('Próximo número secuencial para la factura')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
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
        verbose_name = gettext_lazy('Perfil de Usuario')
        verbose_name_plural = gettext_lazy('Perfiles de Usuario')
    
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

    # Firma digital del usuario (para contratos y documentos)
    signature_image = models.ImageField(
        upload_to='user_signatures/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Firma digital'),
        help_text=gettext_lazy('Imagen de la firma que se usará en contratos y documentos'),
    )

    # Bloqueo de acceso con error 401
    error_401 = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Error 401'),
        help_text=gettext_lazy('Si está activo, el usuario no podrá iniciar sesión y verá un mensaje de error 401')
    )

    def regenerate_api_token(self):
        """Regenera el token de API"""
        self.api_token = uuid.uuid4()
        self.save()
        return self.api_token


class BlockedLoginAttempt(models.Model):
    """Registro de intentos de login bloqueados por error 401"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_login_attempts',
        verbose_name=gettext_lazy('Usuario')
    )
    attempted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha y hora del intento')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Agente de usuario')
    )

    class Meta:
        verbose_name = gettext_lazy('Intento de login bloqueado')
        verbose_name_plural = gettext_lazy('Intentos de login bloqueados')
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.user.username} - {self.attempted_at.strftime('%d/%m/%Y %H:%M:%S')}"


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
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo de la nota')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Contenido detallado de la nota')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=gettext_lazy('Usuario asociado'),
        help_text=gettext_lazy('Usuario al que está asociada esta nota')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_notes',
        verbose_name=gettext_lazy('Creado por'),
        help_text=gettext_lazy('Agente que creó la nota')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa asociada a esta nota')
    )
    tickets = models.ManyToManyField(
        Ticket,
        blank=True,
        related_name='notes',
        verbose_name=gettext_lazy('Tickets relacionados'),
        help_text=gettext_lazy('Tickets asociados a esta nota')
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Nota privada'),
        help_text=gettext_lazy('Si está marcada, solo tú podrás ver, editar y eliminar esta nota')
    )
    share_token = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name=gettext_lazy('Token de compartir'),
        help_text=gettext_lazy('Token único para compartir la nota públicamente')
    )
    is_shareable = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Compartible públicamente'),
        help_text=gettext_lazy('Si la nota puede ser compartida mediante un enlace público')
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de visualizaciones'),
        help_text=gettext_lazy('Veces que la nota ha sido vista mediante enlace público')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Nota de Usuario')
        verbose_name_plural = gettext_lazy('Notas de Usuario')
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def can_view(self, user):
        """Verifica si un usuario puede ver esta nota"""
        from .utils import is_agent
        
        # Si la nota es privada, solo el creador puede verla
        if self.is_private and self.created_by != user:
            return False
            
        # Los agentes pueden ver notas públicas
        if is_agent(user):
            return True
            
        # El creador puede ver sus propias notas (privadas y públicas)
        if self.created_by == user:
            return True
            
        # Si la nota no es privada, el usuario asociado puede verla
        if not self.is_private and self.user == user:
            return True
            
        return False
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar esta nota"""
        from .utils import is_agent
        
        # Si la nota es privada, solo el creador puede editarla
        if self.is_private and self.created_by != user:
            return False
            
        # Solo los agentes pueden crear/editar notas (para notas públicas)
        # O el creador puede editar sus propias notas privadas
        return is_agent(user) or (self.is_private and self.created_by == user)
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar esta nota"""
        from .utils import is_agent
        
        # Si la nota es privada, solo el creador puede eliminarla
        if self.is_private and self.created_by != user:
            return False
            
        # Solo los agentes pueden eliminar notas (para notas públicas)
        # O el creador puede eliminar sus propias notas privadas
        return is_agent(user) or (self.is_private and self.created_by == user)
    
    def generate_share_token(self):
        """Genera un token único para compartir la nota"""
        import uuid
        self.share_token = str(uuid.uuid4())[:12]
        self.is_shareable = True
        self.save()
        return self.share_token
    
    def get_public_url(self, request=None):
        """Obtiene la URL pública de la nota si es compartible"""
        if not self.is_shareable or not self.share_token:
            return None
        
        if request:
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            return f"{protocol}://{domain}/shared/note/{self.share_token}/"
        else:
            return f"/shared/note/{self.share_token}/"
    
    def disable_sharing(self):
        """Deshabilita el compartir público de la nota"""
        self.is_shareable = False
        self.save()
    
    def increment_view_count(self):
        """Incrementa el contador de visualizaciones"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
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
    
    END_REASON_CHOICES = [
        ('comer', gettext_lazy('Comer')),
        ('fin_jornada', gettext_lazy('Fin de Jornada')),
        ('otro', gettext_lazy('Otro')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name=gettext_lazy('Empleado')
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name=gettext_lazy('Proyecto'),
        null=True,
        blank=True
    )
    ticket = models.ForeignKey(
        'Ticket',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name=gettext_lazy('Ticket'),
        null=True,
        blank=True,
        help_text=gettext_lazy('Ticket en el que se trabajará (opcional)')
    )
    work_order = models.ForeignKey(
        'WorkOrder',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name=gettext_lazy('Orden de Trabajo'),
        null=True,
        blank=True,
        help_text=gettext_lazy('Orden de trabajo en la que se trabajará (opcional)')
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='time_entries',
        verbose_name=gettext_lazy('Tarea'),
        null=True,
        blank=True,
        help_text=gettext_lazy('Tarea en la que se trabajará (opcional)')
    )
    fecha_entrada = models.DateTimeField(
        verbose_name=gettext_lazy('Fecha y hora de entrada')
    )
    fecha_salida = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha y hora de salida')
    )
    end_reason = models.CharField(
        max_length=20,
        choices=END_REASON_CHOICES,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Causa de finalización'),
        help_text=gettext_lazy('Motivo por el cual se finaliza la jornada')
    )
    notas = models.TextField(
        blank=True,
        max_length=500,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Comentarios opcionales sobre la jornada')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Registrado el')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-fecha_entrada']
        verbose_name = gettext_lazy('Registro de Horario')
        verbose_name_plural = gettext_lazy('Registros de Horario')
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
        return cls.objects.filter(user=user, fecha_salida__isnull=True).first()
    
    @classmethod
    def get_active_entry_for_agent(cls, user):
        """Obtiene el registro activo (sin salida) de un agente"""
        from .utils import is_agent
        if not is_agent(user):
            return None
        return cls.objects.filter(user=user, fecha_salida__isnull=True).first()
    
    @classmethod
    def create_entry(cls, user, project=None, ticket=None, work_order=None, task=None, notas_entrada=None):
        """Crea un nuevo registro de entrada (para agentes)"""
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
    
    @classmethod
    def create_public_entry(cls, user, notas_entrada=None):
        """Crea un nuevo registro de entrada para acceso público (sin restricción de agente)"""
        # Verificar que no haya una entrada activa
        active_entry = cls.get_active_entry(user)
        if active_entry:
            raise ValueError("Ya tienes una jornada activa. Finalízala antes de crear una nueva.")
        
        return cls.objects.create(
            user=user,
            project=None,
            ticket=None,
            work_order=None,
            task=None,
            fecha_entrada=timezone.now(),
            notas=notas_entrada or ''
        )


class TimeEntryAuditLog(models.Model):
    """Modelo para auditar cambios en registros de tiempo"""
    
    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=gettext_lazy('Registro de Tiempo')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario que modificó')
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha y hora de modificación')
    )
    field_name = models.CharField(
        max_length=50,
        verbose_name=gettext_lazy('Campo modificado')
    )
    old_value = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor anterior')
    )
    new_value = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor nuevo')
    )
    change_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Razón del cambio')
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = gettext_lazy('Log de Auditoría de Tiempo')
        verbose_name_plural = gettext_lazy('Logs de Auditoría de Tiempo')
    
    def __str__(self):
        return f"{self.time_entry} - {self.field_name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class PublicTimeAccess(models.Model):
    """Modelo para gestionar acceso público al control de horario"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='public_time_access',
        verbose_name=gettext_lazy('Usuario')
    )
    token = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Token de Acceso'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está activo, el usuario puede usar el acceso público')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Creado el')
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Último uso')
    )
    
    # Configuraciones adicionales
    require_location = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Requiere ubicación'),
        help_text=gettext_lazy('Si está activado, registrará la ubicación GPS al marcar entrada/salida')
    )
    allowed_ip_addresses = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('IPs permitidas'),
        help_text=gettext_lazy('Lista de IPs permitidas separadas por comas (opcional)')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Acceso Público de Horario')
        verbose_name_plural = gettext_lazy('Accesos Públicos de Horario')
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Activo" if self.is_active else "Inactivo"
        return f"{self.user.get_full_name() or self.user.username} - {status}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    @property
    def public_url(self):
        """Genera la URL pública para el acceso al control de horario"""
        from django.urls import reverse
        return reverse('public_time_clock', kwargs={'token': self.token})
    
    def is_ip_allowed(self, ip_address):
        """Verifica si una IP está permitida"""
        if not self.allowed_ip_addresses:
            return True
        
        allowed_ips = [ip.strip() for ip in self.allowed_ip_addresses.split(',')]
        return ip_address in allowed_ips
    
    def update_last_used(self):
        """Actualiza la fecha de último uso"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class SystemConfiguration(models.Model):
    """Modelo para configuraciones generales del sistema"""
    
    # Configuración de registro de usuarios
    allow_user_registration = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Permitir registro de usuarios'),
        help_text=gettext_lazy('Permite que nuevos usuarios se registren en el sistema')
    )
    
    # Configuraciones adicionales que se pueden agregar en el futuro
    site_name = models.CharField(
        max_length=100,
        default='TicketPro',
        verbose_name=gettext_lazy('Nombre del sitio'),
        help_text=gettext_lazy('Nombre que aparece en el encabezado del sistema')
    )
    
    # Configuraciones de tickets
    default_ticket_priority = models.CharField(
        max_length=20,
        choices=[
            ('low', gettext_lazy('Baja')),
            ('medium', gettext_lazy('Media')),
            ('high', gettext_lazy('Alta')),
            ('urgent', gettext_lazy('Urgente'))
        ],
        default='medium',
        verbose_name=gettext_lazy('Prioridad por defecto de tickets'),
        help_text=gettext_lazy('Prioridad asignada automáticamente a nuevos tickets')
    )
    
    # Configuración de moneda
    default_currency = models.CharField(
        max_length=10,
        choices=[
            ('EUR', gettext_lazy('Euro (€)')),
            ('USD', gettext_lazy('Dólar Americano ($)')),
            ('GBP', gettext_lazy('Libra Esterlina (£)')),
            ('JPY', gettext_lazy('Yen Japonés (¥)')),
            ('CAD', gettext_lazy('Dólar Canadiense (C$)')),
            ('AUD', gettext_lazy('Dólar Australiano (A$)')),
            ('CHF', gettext_lazy('Franco Suizo (CHF)')),
            ('CNY', gettext_lazy('Yuan Chino (¥)')),
            ('MXN', gettext_lazy('Peso Mexicano ($)')),
            ('COP', gettext_lazy('Peso Colombiano ($)')),
        ],
        default='EUR',
        verbose_name=gettext_lazy('Moneda por defecto'),
        help_text=gettext_lazy('Moneda utilizada para mostrar valores en el sistema')
    )
    
    # Configuración de Chat IA
    openai_api_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('API Key de OpenAI'),
        help_text=gettext_lazy('Clave de API para conectar con ChatGPT')
    )
    
    openai_model = models.CharField(
        max_length=50,
        default='gpt-4o',
        verbose_name=gettext_lazy('Modelo de OpenAI'),
        help_text=gettext_lazy('Modelo de IA a utilizar por defecto (ej: gpt-4o, gpt-3.5-turbo)')
    )
    
    ai_chat_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Chat IA habilitado'),
        help_text=gettext_lazy('Habilita o deshabilita la funcionalidad de chat con IA')
    )
    
    # Configuración de análisis de empleados con IA
    ai_employee_analysis_prompt = models.TextField(
        default='Analiza el siguiente perfil de candidato y dame un resumen profesional y una puntuación del 1 al 10 para el cargo solicitado. Considera experiencia, formación, habilidades y adecuación al puesto.\n\nDatos del candidato:\n{datos}\n\nPor favor, responde en este formato:\nResumen: [Aquí tu análisis profesional del candidato]\nPuntuación: [Número del 1 al 10]',
        verbose_name=gettext_lazy('Prompt para análisis de empleados'),
        help_text=gettext_lazy('Plantilla del prompt que se enviará a la IA para analizar candidatos. Usa {datos} donde se insertarán los datos del candidato.')
    )
    
    # Configuración de Telegram
    enable_telegram_notifications = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Activar notificaciones de Telegram'),
        help_text=gettext_lazy('Envía notificaciones a un grupo de Telegram cuando se crean tickets')
    )
    telegram_bot_token = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token del Bot de Telegram'),
        help_text=gettext_lazy('Token del bot de Telegram proporcionado por @BotFather')
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('ID del Chat/Grupo de Telegram'),
        help_text=gettext_lazy('ID del grupo o chat donde enviar las notificaciones (ej: -100123456789)')
    )
    
    # Configuración de OCR Facturas - Enlace Público
    ocr_public_upload_enabled = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Habilitar enlace público para subir facturas'),
        help_text=gettext_lazy('Permite activar o desactivar el enlace público para que usuarios suban facturas')
    )
    ocr_public_upload_token = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        verbose_name=gettext_lazy('Token del enlace público'),
        help_text=gettext_lazy('Token autogenerado para acceso a la API de listado de facturas')
    )
    
    # Configuración de Email
    enable_email_notifications = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Activar notificaciones por email'),
        help_text=gettext_lazy('Envía notificaciones por email cuando se reciben contactos desde la web')
    )
    email_host = models.CharField(
        max_length=255,
        blank=True,
        default='smtp.gmail.com',
        verbose_name=gettext_lazy('Servidor SMTP'),
        help_text=gettext_lazy('Servidor de correo saliente (ej: smtp.gmail.com, mail.tu-dominio.com)')
    )
    email_port = models.IntegerField(
        blank=True,
        null=True,
        default=587,
        verbose_name=gettext_lazy('Puerto SMTP'),
        help_text=gettext_lazy('Puerto del servidor SMTP (587 para TLS, 465 para SSL, 25 para sin cifrado)')
    )
    email_host_user = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Usuario SMTP'),
        help_text=gettext_lazy('Dirección de email para autenticación SMTP')
    )
    email_host_password = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=gettext_lazy('Contraseña SMTP'),
        help_text=gettext_lazy('Contraseña o token de aplicación para SMTP')
    )
    email_use_tls = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Usar TLS'),
        help_text=gettext_lazy('Activar cifrado TLS (recomendado para puerto 587)')
    )
    email_use_ssl = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Usar SSL'),
        help_text=gettext_lazy('Activar cifrado SSL (para puerto 465)')
    )
    email_from = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email remitente'),
        help_text=gettext_lazy('Dirección de email que aparecerá como remitente')
    )
    notification_emails = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Emails de notificación'),
        help_text=gettext_lazy('Direcciones de email donde enviar notificaciones (una por línea)')
    )
    
    # Configuración de PayPal
    paypal_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('PayPal habilitado'),
        help_text=gettext_lazy('Habilita o deshabilita los pagos con PayPal')
    )
    paypal_mode = models.CharField(
        max_length=20,
        choices=[
            ('sandbox', gettext_lazy('Sandbox (Pruebas)')),
            ('live', gettext_lazy('Live (Producción)'))
        ],
        default='sandbox',
        verbose_name=gettext_lazy('Modo de PayPal'),
        help_text=gettext_lazy('Modo de operación de PayPal')
    )
    paypal_client_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('PayPal Client ID'),
        help_text=gettext_lazy('Client ID de la aplicación PayPal')
    )
    paypal_client_secret = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('PayPal Client Secret'),
        help_text=gettext_lazy('Client Secret de la aplicación PayPal')
    )
    paypal_webhook_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('PayPal Webhook ID'),
        help_text=gettext_lazy('ID del webhook configurado en PayPal para recibir notificaciones de pagos')
    )
    
    # Token público para catálogo de productos
    products_catalog_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=gettext_lazy('Token del Catálogo Público'),
        help_text=gettext_lazy('Token único para acceso público al catálogo de productos')
    )

    # Datos de contacto para cotizaciones
    contact_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Nombre de contacto'),
        help_text=gettext_lazy('Nombre que aparece en la página de cotización para enviar comprobante de pago')
    )
    contact_email = models.EmailField(
        blank=True,
        default='',
        verbose_name=gettext_lazy('Email de contacto'),
        help_text=gettext_lazy('Correo al que los clientes deben enviar el comprobante de pago')
    )
    paypal_payment_email = models.EmailField(
        blank=True,
        default='',
        verbose_name=gettext_lazy('Email de PayPal para pagos'),
        help_text=gettext_lazy('Cuenta de PayPal a la que los clientes pueden enviar el pago de su cotización')
    )

    forma_trabajo_url = models.URLField(
        blank=True,
        default='',
        verbose_name=gettext_lazy('URL Forma de trabajo'),
        help_text=gettext_lazy('Enlace al documento o página que describe tu forma de trabajo (se mostrará en el formulario ¿Quién eres?)')
    )

    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    class Meta:
        verbose_name = gettext_lazy('Configuración del Sistema')
        verbose_name_plural = gettext_lazy('Configuración del Sistema')
    
    def __str__(self):
        return f'Configuración del Sistema - {self.site_name}'
    
    def save(self, *args, **kwargs):
        """Autogenerar token para OCR si no existe"""
        if not self.ocr_public_upload_token:
            import secrets
            self.ocr_public_upload_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
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
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre descriptivo del documento')
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional del contenido del documento')
    )
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name=gettext_lazy('Archivo'),
        help_text=gettext_lazy('Archivo de documentación (PDF, DOC, DOCX, TXT, etc.)')
    )
    file_size = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)'),
        editable=False
    )
    file_type = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Tipo de archivo'),
        editable=False
    )
    
    # Sistema de compartir público (como en tickets)
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token de compartir público'),
        help_text=gettext_lazy('Token único para compartir el documento públicamente')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Disponible públicamente'),
        help_text=gettext_lazy('Si está marcado, el documento puede ser accedido sin autenticación')
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de descargas'),
        help_text=gettext_lazy('Contador de veces que se ha descargado el documento')
    )
    
    # Metadatos del documento
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_documents',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=gettext_lazy('Empresa/Cliente'),
        help_text=gettext_lazy('Empresa o cliente asociado al documento')
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por comas para categorizar el documento')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Documento')
        verbose_name_plural = gettext_lazy('Documentos')
    
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
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre descriptivo para la URL')
    )
    url = models.URLField(
        max_length=500,
        verbose_name=gettext_lazy('URL'),
        help_text=gettext_lazy('Dirección web completa (incluye http:// o https://)')
    )
    username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Usuario'),
        help_text=gettext_lazy('Nombre de usuario para acceder')
    )
    encrypted_password = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Contraseña encriptada'),
        help_text=gettext_lazy('Contraseña almacenada de forma segura')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Información adicional sobre esta URL')
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Categoría'),
        help_text=gettext_lazy('Ej: Servidor, Base de datos, Servicio web, etc.')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Indica si la URL está activa o no')
    )
    is_principal = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('URL Principal'),
        help_text=gettext_lazy('Marcar como URL principal para mostrar en el dashboard')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_urls',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    last_accessed = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Último acceso')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Gestor de URL')
        verbose_name_plural = gettext_lazy('Gestores de URLs')
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['created_by', 'is_active']),
            models.Index(fields=['is_principal', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.url}"
    
    def set_password(self, raw_password):
        """Encripta y guarda la contraseña"""
        if not raw_password:
            self.encrypted_password = None
            return
            
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
        if not self.encrypted_password:
            return ""
            
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


class ApiEndpoint(models.Model):
    """Modelo para generar mini-APIs consultables vía GET a partir de un registro"""
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre'),
        help_text=gettext_lazy('Nombre descriptivo de la API')
    )
    value = models.BooleanField(
        default=True,
        choices=[(True, gettext_lazy('Verdadero')), (False, gettext_lazy('Falso'))],
        verbose_name=gettext_lazy('Valor'),
        help_text=gettext_lazy('Valor booleano que devolverá la API')
    )
    text = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Texto'),
        help_text=gettext_lazy('Contenido de texto largo que devolverá la API')
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está desactivada, la API dejará de responder')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_api_endpoints',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('API')
        verbose_name_plural = gettext_lazy('APIs')

    def __str__(self):
        return self.name

    def get_api_url(self):
        from django.urls import reverse
        return reverse('api_endpoint_public', kwargs={'token': self.token})

    def get_absolute_api_url(self, request=None):
        path = self.get_api_url()
        if request is not None:
            return request.build_absolute_uri(path)
        return path


class WorkOrder(models.Model):
    """Modelo para gestionar órdenes de trabajo"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('accepted', gettext_lazy('Aceptado')),
        ('finished', gettext_lazy('Terminado')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo de la orden de trabajo')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del trabajo a realizar')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='work_orders',
        verbose_name=gettext_lazy('Empresa'),
        null=True,
        blank=True,
        help_text=gettext_lazy('Empresa a la que se dirige la orden de trabajo')
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        verbose_name=gettext_lazy('Proyecto'),
        help_text=gettext_lazy('Proyecto asociado a la orden de trabajo (opcional)')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado'),
        help_text=gettext_lazy('Estado actual de la orden de trabajo')
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de entrega'),
        help_text=gettext_lazy('Fecha límite para completar la orden (opcional)')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Publicar públicamente'),
        help_text=gettext_lazy('Permite que esta orden sea visible públicamente')
    )
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token de compartir público'),
        help_text=gettext_lazy('Token único para compartir la orden públicamente')
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Horas estimadas'),
        help_text=gettext_lazy('Tiempo estimado para completar la orden')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Importe'),
        help_text=gettext_lazy('Precio o costo de la orden de trabajo')
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', gettext_lazy('Baja')),
            ('medium', gettext_lazy('Media')),
            ('high', gettext_lazy('Alta')),
            ('urgent', gettext_lazy('Urgente')),
        ],
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_work_orders',
        verbose_name=gettext_lazy('Creado por')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders',
        verbose_name=gettext_lazy('Asignado a'),
        help_text=gettext_lazy('Usuario responsable de la orden')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de finalización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Orden de Trabajo')
        verbose_name_plural = gettext_lazy('Órdenes de Trabajo')
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
        verbose_name=gettext_lazy('Orden de Trabajo')
    )
    file = models.FileField(
        upload_to=work_order_attachment_upload_path,
        verbose_name=gettext_lazy('Archivo')
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre original')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Subido por')
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de subida')
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = gettext_lazy('Adjunto de Orden de Trabajo')
        verbose_name_plural = gettext_lazy('Adjuntos de Órdenes de Trabajo')
    
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
        ('pending', gettext_lazy('Pendiente')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('completed', gettext_lazy('Completada')),
    ]
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=gettext_lazy('Orden de Trabajo')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la Tarea')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada de la tarea (opcional)')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición de la tarea')
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Horas Estimadas'),
        help_text=gettext_lazy('Tiempo estimado para completar la tarea')
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Horas Reales'),
        help_text=gettext_lazy('Tiempo real trabajado en la tarea')
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Iniciado en')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Completado en')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = gettext_lazy('Tarea de Orden de Trabajo')
        verbose_name_plural = gettext_lazy('Tareas de Órdenes de Trabajo')
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
        verbose_name=gettext_lazy('Tarea')
    )
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=gettext_lazy('Horas Trabajadas')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción del Trabajo'),
        help_text=gettext_lazy('Descripción opcional del trabajo realizado')
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Registrado en')
    )
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = gettext_lazy('Registro de Tiempo de Tarea')
        verbose_name_plural = gettext_lazy('Registros de Tiempo de Tareas')
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
        verbose_name=gettext_lazy('Tarea')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Usuario'),
        help_text=gettext_lazy('Usuario que inició la sesión (puede ser vacío para sesiones públicas)')
    )
    start_time = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Inicio')
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fin')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción del trabajo realizado')
    )
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = gettext_lazy('Sesión de Tiempo de Tarea')
        verbose_name_plural = gettext_lazy('Sesiones de Tiempo de Tareas')
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


class WorkOrderRating(models.Model):
    """Modelo para calificaciones de órdenes de trabajo desde clientes"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name=gettext_lazy('Orden de Trabajo')
    )
    rating = models.IntegerField(
        verbose_name=gettext_lazy('Calificación'),
        help_text=gettext_lazy('Calificación de 1 a 5 estrellas'),
        choices=[(1, gettext_lazy('1 estrella')), (2, gettext_lazy('2 estrellas')), (3, gettext_lazy('3 estrellas')), (4, gettext_lazy('4 estrellas')), (5, gettext_lazy('5 estrellas'))]
    )
    comment = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentario'),
        help_text=gettext_lazy('Comentario opcional sobre el servicio')
    )
    rated_by_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre'),
        help_text=gettext_lazy('Nombre de quien califica')
    )
    rated_by_email = models.EmailField(
        verbose_name=gettext_lazy('Email'),
        help_text=gettext_lazy('Email de quien califica')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de calificación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Calificación de Orden de Trabajo')
        verbose_name_plural = gettext_lazy('Calificaciones de Órdenes de Trabajo')
    
    def __str__(self):
        return f"{self.work_order} - {self.rating} estrellas por {self.rated_by_name}"


class WorkOrderComment(models.Model):
    """Modelo para comentarios públicos en órdenes de trabajo"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='public_comments',
        verbose_name=gettext_lazy('Orden de Trabajo')
    )
    comment = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    author_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del autor')
    )
    author_email = models.EmailField(
        verbose_name=gettext_lazy('Email del autor')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Visible públicamente'),
        help_text=gettext_lazy('Si está marcado, el comentario será visible en la vista pública')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Comentario de Orden de Trabajo')
        verbose_name_plural = gettext_lazy('Comentarios de Órdenes de Trabajo')
    
    def __str__(self):
        return f"{self.work_order} - {self.author_name} ({self.created_at.strftime('%d/%m/%Y')})"


class Task(models.Model):
    """Modelo para gestionar tareas que pueden ser asignadas a múltiples usuarios"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('completed', gettext_lazy('Completada')),
        ('cancelled', gettext_lazy('Cancelada')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', gettext_lazy('Baja')),
        ('medium', gettext_lazy('Media')),
        ('high', gettext_lazy('Alta')),
        ('urgent', gettext_lazy('Urgente')),
    ]
    
    task_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Número de Tarea'),
        null=True,
        blank=True
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    assigned_users = models.ManyToManyField(
        User,
        related_name='assigned_tasks',
        blank=True,
        verbose_name=gettext_lazy('Usuarios Asignados')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name=gettext_lazy('Creado por')
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de vencimiento')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de finalización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Tarea')
        verbose_name_plural = gettext_lazy('Tareas')
    
    def save(self, *args, **kwargs):
        if not self.task_number:
            from django.db import transaction
            with transaction.atomic():
                # Obtener el último número de tarea con bloqueo
                last_task = Task.objects.select_for_update().order_by('-id').first()
                if last_task and last_task.task_number:
                    try:
                        last_number = int(last_task.task_number.split('-')[1])
                        new_number = last_number + 1
                    except (IndexError, ValueError):
                        new_number = 1
                else:
                    new_number = 1
                
                # Verificar que el número no exista
                while Task.objects.filter(task_number=f'TASK-{new_number:04d}').exists():
                    new_number += 1
                
                self.task_number = f'TASK-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.task_number:
            return f'{self.task_number} - {self.title}'
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
        verbose_name=gettext_lazy('Usuario')
    )
    date = models.DateField(
        verbose_name=gettext_lazy('Fecha de la sesión')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas del día'),
        help_text=gettext_lazy('Notas generales sobre el plan del día')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Creado en')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Actualizado en')
    )
    
    class Meta:
        ordering = ['-created_at', '-date']
        verbose_name = gettext_lazy('Gestión de Tareas')
        verbose_name_plural = gettext_lazy('Gestiones de Tareas')
    
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
        verbose_name=gettext_lazy('Sesión diaria')
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='daily_items',
        verbose_name=gettext_lazy('Tarea')
    )
    completed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Completada')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Completada en')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas específicas'),
        help_text=gettext_lazy('Notas específicas sobre el trabajo en esta tarea')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden')
    )
    
    class Meta:
        ordering = ['order', 'task__priority']
        unique_together = ['session', 'task']
        verbose_name = gettext_lazy('Item de Tarea Diaria')
        verbose_name_plural = gettext_lazy('Items de Tareas Diarias')
    
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
        verbose_name=gettext_lazy('Nombre de la sala')
    )
    participants = models.ManyToManyField(
        User,
        related_name='chat_rooms',
        verbose_name=gettext_lazy('Participantes')
    )
    is_group = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Es grupo'),
        help_text=gettext_lazy('True para chats grupales, False para chats 1:1')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    last_activity = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Última actividad')
    )
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = gettext_lazy('Sala de Chat')
        verbose_name_plural = gettext_lazy('Salas de Chat')
    
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
        verbose_name=gettext_lazy('Sala de chat')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name=gettext_lazy('Remitente')
    )
    message = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Mensaje')
    )
    attachment = models.FileField(
        upload_to='chat_attachments/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Archivo adjunto')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de envío')
    )
    read_by = models.ManyToManyField(
        User,
        blank=True,
        related_name='read_messages',
        verbose_name=gettext_lazy('Leído por')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Mensaje de Chat')
        verbose_name_plural = gettext_lazy('Mensajes de Chat')
    
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
        ('linux', gettext_lazy('Linux/Unix')),
        ('windows', gettext_lazy('Windows')),
        ('docker', gettext_lazy('Docker')),
        ('git', gettext_lazy('Git')),
        ('python', gettext_lazy('Python')),
        ('javascript', gettext_lazy('JavaScript')),
        ('database', gettext_lazy('Base de Datos')),
        ('network', gettext_lazy('Redes')),
        ('security', gettext_lazy('Seguridad')),
        ('devops', gettext_lazy('DevOps')),
        ('web', gettext_lazy('Desarrollo Web')),
        ('mobile', gettext_lazy('Desarrollo Móvil')),
        ('other', gettext_lazy('Otros')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo del comando')
    )
    command = models.TextField(
        verbose_name=gettext_lazy('Comando'),
        help_text=gettext_lazy('El comando completo con sus parámetros')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada de lo que hace el comando')
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name=gettext_lazy('Categoría')
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por comas para facilitar la búsqueda')
    )
    example_usage = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Ejemplo de uso'),
        help_text=gettext_lazy('Ejemplo práctico de cómo usar el comando')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas adicionales'),
        help_text=gettext_lazy('Notas importantes, advertencias o tips')
    )
    is_dangerous = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Comando peligroso'),
        help_text=gettext_lazy('Marcar si el comando puede ser destructivo o peligroso')
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Favorito'),
        help_text=gettext_lazy('Marcar como comando favorito')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Veces usado'),
        help_text=gettext_lazy('Contador de cuántas veces se ha copiado/usado este comando')
    )
    
    class Meta:
        ordering = ['-is_favorite', '-usage_count', '-created_at']
        verbose_name = gettext_lazy('Comando')
        verbose_name_plural = gettext_lazy('Comandos')
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
        ('pending', gettext_lazy('Pendiente')),
        ('approved', gettext_lazy('Aprobada')),
        ('rejected', gettext_lazy('Rechazada')),
        ('company_created', gettext_lazy('Empresa Creada')),
    ]
    
    # Información del formulario de contacto
    company_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Empresa')
    )
    contact_name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre del Contacto')
    )
    email = models.EmailField(
        verbose_name=gettext_lazy('Correo Electrónico')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Teléfono')
    )
    website = models.URLField(
        blank=True,
        verbose_name=gettext_lazy('Sitio Web')
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Dirección')
    )
    message = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Mensaje Adicional'),
        help_text=gettext_lazy('Información adicional sobre la empresa o servicios requeridos')
    )
    
    # Metadatos del formulario
    submitted_by_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contact_form_owner',
        verbose_name=gettext_lazy('Propietario del formulario'),
        help_text=gettext_lazy('Usuario que tiene activado el formulario de contacto')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Información de seguimiento
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    # Empresa creada (si se aprueba)
    created_company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Empresa Creada')
    )
    
    # Fechas
    submitted_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Envío')
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Procesamiento')
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_contact_forms',
        verbose_name=gettext_lazy('Procesado por')
    )
    
    # Notas internas
    admin_notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas del Administrador'),
        help_text=gettext_lazy('Notas internas para el seguimiento de la solicitud')
    )
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = gettext_lazy('Formulario de Contacto')
        verbose_name_plural = gettext_lazy('Formularios de Contacto')
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
        verbose_name=gettext_lazy('Nombre del Estado')
    )
    description = models.TextField(
        blank=True, 
        verbose_name=gettext_lazy('Descripción')
    )
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text=gettext_lazy('Color en formato hexadecimal (ej: #007bff)'),
        verbose_name=gettext_lazy('Color')
    )
    is_final = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Estado Final'),
        help_text=gettext_lazy('Indica si este estado representa el cierre de la oportunidad')
    )
    is_won = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Estado Ganado'),
        help_text=gettext_lazy('Indica si este estado representa una venta exitosa')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en el pipeline')
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = gettext_lazy('Estado de Oportunidad')
        verbose_name_plural = gettext_lazy('Estados de Oportunidad')
    
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
        verbose_name=gettext_lazy('Nombre de la Oportunidad')
    )
    description = models.TextField(
        blank=True, 
        verbose_name=gettext_lazy('Descripción')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='opportunities',
        verbose_name=gettext_lazy('Empresa')
    )
    contact_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Contacto Principal')
    )
    contact_position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Cargo del Contacto'),
        help_text=gettext_lazy('Posición o cargo del contacto en la empresa')
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email de Contacto')
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Teléfono de Contacto')
    )
    value = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name=gettext_lazy('Valor Estimado'),
        help_text=gettext_lazy('Valor estimado de la oportunidad')
    )
    probability = models.IntegerField(
        choices=PROBABILITY_CHOICES,
        default=20,
        verbose_name=gettext_lazy('Probabilidad de Cierre (%)')
    )
    status = models.ForeignKey(
        OpportunityStatus,
        on_delete=models.PROTECT,
        related_name='opportunities',
        verbose_name=gettext_lazy('Estado')
    )
    expected_close_date = models.DateField(
        verbose_name=gettext_lazy('Fecha Estimada de Cierre')
    )
    actual_close_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha Real de Cierre')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_opportunities',
        verbose_name=gettext_lazy('Asignado a')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_opportunities',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    # Campos de seguimiento
    last_contact_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Último Contacto')
    )
    next_follow_up = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Próximo Seguimiento')
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Fuente'),
        help_text=gettext_lazy('¿Cómo se originó esta oportunidad?')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Oportunidad')
        verbose_name_plural = gettext_lazy('Oportunidades')
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
        verbose_name=gettext_lazy('Oportunidad')
    )
    content = models.TextField(verbose_name=gettext_lazy('Contenido'))
    is_important = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Importante'),
        help_text=gettext_lazy('Marcar como nota importante')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Nota de Oportunidad')
        verbose_name_plural = gettext_lazy('Notas de Oportunidad')
    
    def __str__(self):
        return f"Nota para {self.opportunity.name} - {self.created_at.strftime('%d/%m/%Y')}"


class OpportunityStatusHistory(models.Model):
    """Historial de cambios de estado de las oportunidades"""
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=gettext_lazy('Oportunidad')
    )
    previous_status = models.ForeignKey(
        OpportunityStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_changes',
        verbose_name=gettext_lazy('Estado Anterior')
    )
    new_status = models.ForeignKey(
        OpportunityStatus,
        on_delete=models.CASCADE,
        related_name='new_changes',
        verbose_name=gettext_lazy('Nuevo Estado')
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Cambiado por')
    )
    changed_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha del cambio'))
    comment = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentario'),
        help_text=gettext_lazy('Razón del cambio de estado')
    )
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = gettext_lazy('Historial de Estado')
        verbose_name_plural = gettext_lazy('Historial de Estados')
    
    def __str__(self):
        return f"{self.opportunity.name}: {self.previous_status} → {self.new_status}"


class OpportunityActivity(models.Model):
    """Modelo para actividades de seguimiento de oportunidades"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('call', gettext_lazy('Llamada')),
        ('meeting', gettext_lazy('Reunión')),
        ('email', gettext_lazy('Correo Electrónico')),
        ('task', gettext_lazy('Tarea')),
        ('demo', gettext_lazy('Demostración')),
        ('proposal', gettext_lazy('Propuesta')),
        ('follow_up', gettext_lazy('Seguimiento')),
        ('other', gettext_lazy('Otro')),
    ]
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('completed', gettext_lazy('Completada')),
        ('cancelled', gettext_lazy('Cancelada')),
        ('overdue', gettext_lazy('Vencida')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', gettext_lazy('Baja')),
        ('medium', gettext_lazy('Media')),
        ('high', gettext_lazy('Alta')),
        ('urgent', gettext_lazy('Urgente')),
    ]
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=gettext_lazy('Oportunidad'),
        null=True,
        blank=True
    )
    contact = models.ForeignKey(
        'Contact',
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=gettext_lazy('Contacto'),
        null=True,
        blank=True,
        help_text=gettext_lazy('Contacto relacionado con esta actividad')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la Actividad')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPE_CHOICES,
        default='task',
        verbose_name=gettext_lazy('Tipo de Actividad')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    scheduled_date = models.DateTimeField(
        verbose_name=gettext_lazy('Fecha Programada'),
        help_text=gettext_lazy('Fecha y hora cuando debe realizarse la actividad')
    )
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Completado')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_activities',
        verbose_name=gettext_lazy('Asignado a')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_activities',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    # Campos adicionales
    result = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Resultado'),
        help_text=gettext_lazy('Resultado o notas de la actividad completada')
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Duración (minutos)'),
        help_text=gettext_lazy('Duración estimada o real de la actividad')
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Ubicación'),
        help_text=gettext_lazy('Lugar donde se realizará la actividad')
    )
    
    class Meta:
        ordering = ['scheduled_date', '-priority']
        verbose_name = gettext_lazy('Actividad de Oportunidad')
        verbose_name_plural = gettext_lazy('Actividades de Oportunidades')
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
        ('scheduled', gettext_lazy('Programada')),
        ('in_progress', gettext_lazy('En progreso')),
        ('finished', gettext_lazy('Finalizada')),
        ('cancelled', gettext_lazy('Cancelada')),
    ]
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título de la reunión'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    spin_methodology = models.TextField(
        blank=True, 
        verbose_name=gettext_lazy('Metodología SPIN'),
        help_text=gettext_lazy('Preguntas generadas automáticamente usando la metodología SPIN de ventas')
    )
    date = models.DateTimeField(verbose_name=gettext_lazy('Fecha y hora'))
    duration = models.IntegerField(default=60, verbose_name=gettext_lazy('Duración (minutos)'))
    location = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Ubicación'))
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='scheduled',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Organizador
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_meetings',
        verbose_name=gettext_lazy('Organizador')
    )
    
    # Empresa (opcional para uso interno)
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa relacionada con la reunión (opcional)')
    )
    
    # Producto relacionado con la reunión
    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Producto'),
        help_text=gettext_lazy('Producto principal que se discutirá en la reunión')
    )
    
    # Link público único
    public_token = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name=gettext_lazy('Token público')
    )
    
    # Configuración
    allow_questions = models.BooleanField(default=True, verbose_name=gettext_lazy('Permitir preguntas'))
    require_email = models.BooleanField(default=False, verbose_name=gettext_lazy('Requerir email'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activa'))
    
    # Estadísticas
    public_views_count = models.IntegerField(default=0, verbose_name=gettext_lazy('Vistas del enlace público'))
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Creada el'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Actualizada el'))
    
    class Meta:
        ordering = ['-date']
        verbose_name = gettext_lazy('Reunión')
        verbose_name_plural = gettext_lazy('Reuniones')
    
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
    
    RESPONSE_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('accepted', gettext_lazy('Aceptada')),
        ('declined', gettext_lazy('Rechazada')),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=gettext_lazy('Reunión'))
    name = models.CharField(max_length=100, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email'))
    company = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Empresa'))
    registered_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Registrado el'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))
    response_status = models.CharField(
        max_length=20, 
        choices=RESPONSE_CHOICES, 
        default='pending',
        verbose_name=gettext_lazy('Estado de respuesta')
    )
    response_date = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Fecha de respuesta'))
    
    class Meta:
        ordering = ['registered_at']
        verbose_name = gettext_lazy('Asistente')
        verbose_name_plural = gettext_lazy('Asistentes')
        # Removido unique_together para permitir múltiples registros
    
    def __str__(self):
        return f"{self.name} - {self.meeting.title}"


class MeetingQuestion(models.Model):
    """Modelo para preguntas en reuniones"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('answered', gettext_lazy('Respondida')),
        ('ignored', gettext_lazy('Ignorada')),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=gettext_lazy('Reunión'))
    attendee = models.ForeignKey(
        MeetingAttendee, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=gettext_lazy('Asistente')
    )
    question = models.TextField(verbose_name=gettext_lazy('Pregunta'))
    answer = models.TextField(blank=True, verbose_name=gettext_lazy('Respuesta'))
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Datos del preguntante (por si no está registrado como asistente)
    asker_name = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Nombre del preguntante'))
    asker_email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email del preguntante'))
    
    # Metadata
    asked_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Preguntado el'))
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Respondido el'))
    answered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=gettext_lazy('Respondido por')
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))
    
    class Meta:
        ordering = ['asked_at']
        verbose_name = gettext_lazy('Pregunta de reunión')
        verbose_name_plural = gettext_lazy('Preguntas de reuniones')
    
    def __str__(self):
        return f"Pregunta en {self.meeting.title}: {self.question[:50]}..."
    
    def get_asker_display_name(self):
        """Retorna el nombre del preguntante"""
        if self.attendee:
            return self.attendee.name
        return self.asker_name or "Anónimo"


class MeetingRating(models.Model):
    """Modelo para calificaciones de reuniones con caras (triste, neutro, feliz)"""
    
    RATING_CHOICES = [
        ('sad', gettext_lazy('😞 Triste')),
        ('neutral', gettext_lazy('😐 Neutro')),
        ('happy', gettext_lazy('😊 Feliz')),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=gettext_lazy('Reunión'), related_name='ratings')
    attendee = models.ForeignKey(
        MeetingAttendee, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Asistente')
    )
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        verbose_name=gettext_lazy('Calificación')
    )
    comment = models.TextField(blank=True, verbose_name=gettext_lazy('Comentario'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de evaluación'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Evaluación de reunión')
        verbose_name_plural = gettext_lazy('Evaluaciones de reuniones')
        # Un asistente puede evaluar solo una vez
        unique_together = ['meeting', 'attendee']
    
    def __str__(self):
        return f"Evaluación de {self.meeting.title}: {self.get_rating_display()}"


class MeetingAccessLog(models.Model):
    """Modelo para registrar estadísticas de acceso al enlace público de reuniones"""
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=gettext_lazy('Reunión'), related_name='access_logs')
    ip_address = models.GenericIPAddressField(verbose_name=gettext_lazy('Dirección IP'))
    user_agent = models.TextField(blank=True, verbose_name=gettext_lazy('User Agent'))
    device_type = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Tipo de Dispositivo'))  # mobile, tablet, desktop
    browser = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Navegador'))
    os = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Sistema Operativo'))
    country = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('País'))
    city = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Ciudad'))
    accessed_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha y hora de acceso'))
    
    class Meta:
        ordering = ['-accessed_at']
        verbose_name = gettext_lazy('Registro de acceso')
        verbose_name_plural = gettext_lazy('Registros de acceso')
        indexes = [
            models.Index(fields=['meeting', '-accessed_at']),
            models.Index(fields=['country']),
            models.Index(fields=['device_type']),
        ]
    
    def __str__(self):
        return f"{self.meeting.title} - {self.country} - {self.device_type} - {self.accessed_at.strftime('%d/%m/%Y %H:%M')}"


class MeetingLink(models.Model):
    """Modelo para gestionar enlaces relacionados con reuniones"""
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=gettext_lazy('Reunión'), related_name='links')
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del enlace'))
    url = models.URLField(max_length=500, verbose_name=gettext_lazy('URL'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Creado el'))
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Enlace de reunión')
        verbose_name_plural = gettext_lazy('Enlaces de reunión')
    
    def __str__(self):
        return f"{self.meeting.title} - {self.title}"


class Course(models.Model):
    """Modelo para gestionar cursos de capacitación"""
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del Curso'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Si se selecciona una empresa, solo los usuarios de esa empresa podrán ver este curso')
    )
    public_token = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Token público'),
        help_text=gettext_lazy('Token para acceso público al curso sin autenticación')
    )
    is_public_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Acceso público habilitado'),
        help_text=gettext_lazy('Permite que el curso sea accesible públicamente mediante un enlace')
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    view_count = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Número de visitas'))
    
    # Campos de acceso
    access_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('URL de acceso'),
        help_text=gettext_lazy('URL donde se accede al curso (opcional)')
    )
    access_username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Usuario de acceso'),
        help_text=gettext_lazy('Usuario para acceder al curso (opcional)')
    )
    access_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Contraseña de acceso'),
        help_text=gettext_lazy('Contraseña para acceder al curso (opcional)')
    )
    
    # Campos de aprobación
    APPROVAL_CHOICES = [
        ('pendiente', gettext_lazy('Pendiente')),
        ('aprobado', gettext_lazy('Aprobado')),
        ('desaprobado', gettext_lazy('Desaprobado')),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default='pendiente',
        verbose_name=gettext_lazy('Estado de aprobación')
    )
    approved_by_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Aprobado por (nombre)'),
        help_text=gettext_lazy('Nombre de la persona que aprobó/desaprobó')
    )
    approved_by_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Aprobado por (correo)'),
        help_text=gettext_lazy('Correo de la persona que aprobó/desaprobó')
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de aprobación')
    )
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Curso')
        verbose_name_plural = gettext_lazy('Cursos')
    
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


class CourseApproval(models.Model):
    """Modelo para registrar aprobaciones/desaprobaciones de cursos"""
    
    APPROVAL_CHOICES = [
        ('aprobado', gettext_lazy('Aprobado')),
        ('desaprobado', gettext_lazy('Desaprobado')),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name=gettext_lazy('Curso')
    )
    status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        verbose_name=gettext_lazy('Estado')
    )
    approved_by_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre')
    )
    approved_by_email = models.EmailField(
        verbose_name=gettext_lazy('Correo electrónico')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de aprobación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Aprobación de Curso')
        verbose_name_plural = gettext_lazy('Aprobaciones de Cursos')
    
    def __str__(self):
        return f"{self.course.title} - {self.status} por {self.approved_by_name}"


class CourseRegistrationToken(models.Model):
    """Modelo para gestionar tokens de registro público para cursos"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='registration_tokens',
        verbose_name=gettext_lazy('Curso')
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración'),
        help_text=gettext_lazy('Dejar vacío para que no expire')
    )
    max_registrations = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Máximo de registros'),
        help_text=gettext_lazy('Número máximo de usuarios que pueden registrarse con este token')
    )
    registration_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Registros realizados')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Token de Registro de Curso')
        verbose_name_plural = gettext_lazy('Tokens de Registro de Curso')
    
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
        verbose_name=gettext_lazy('Curso')
    )
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título de la Clase'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    video_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name=gettext_lazy('URL del Video'),
        help_text=gettext_lazy('URL del video de la clase (YouTube, Vimeo, etc.)')
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de la clase dentro del curso')
    )
    duration_minutes = models.PositiveIntegerField(
        blank=True, 
        null=True,
        verbose_name=gettext_lazy('Duración (minutos)'),
        help_text=gettext_lazy('Duración estimada de la clase en minutos')
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activa'))
    link_copy_count = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Veces copiado el link'))
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    class Meta:
        ordering = ['course', 'order', 'title']
        verbose_name = gettext_lazy('Clase')
        verbose_name_plural = gettext_lazy('Clases')
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
        verbose_name=gettext_lazy('Clase')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario')
    )
    viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Visto el')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    class Meta:
        unique_together = ['course_class', 'user']
        ordering = ['-viewed_at']
        verbose_name = gettext_lazy('Visualización de Clase')
        verbose_name_plural = gettext_lazy('Visualizaciones de Clases')
    
    def __str__(self):
        return f"{self.user.username} vio {self.course_class.title}"


class CourseComment(models.Model):
    """Modelo para comentarios en clases de cursos públicos"""
    
    STATUS_CHOICES = [
        ('creado', gettext_lazy('Creado')),
        ('resuelto', gettext_lazy('Resuelto')),
    ]
    
    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Clase')
    )
    name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(verbose_name=gettext_lazy('Email'))
    comment = models.TextField(verbose_name=gettext_lazy('Comentario'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='creado',
        verbose_name=gettext_lazy('Estado')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Resuelto el'))
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Resuelto por')
    )
    solution_link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Link de solución')
    )
    solution_note = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Nota de solución')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Comentario de Clase')
        verbose_name_plural = gettext_lazy('Comentarios de Clases')
    
    def __str__(self):
        return f"Comentario de {self.name} en {self.course_class.title}"


class ContactTag(models.Model):
    """Etiquetas para categorizar contactos"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=gettext_lazy('Nombre')
    )
    
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color en formato hexadecimal (ej: #FF5733)')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Etiqueta de Contacto')
        verbose_name_plural = gettext_lazy('Etiquetas de Contacto')
    
    def __str__(self):
        return self.name


class Contact(models.Model):
    """Modelo para gestionar contactos de ventas"""
    
    STATUS_CHOICES = [
        ('positive', gettext_lazy('Positivo')),
        ('neutral', gettext_lazy('Neutral')),
        ('negative', gettext_lazy('Negativo')),
        ('not_now', gettext_lazy('No ahora')),
        ('do_not_contact', gettext_lazy('No Contactar')),
        ('won', gettext_lazy('Ganado')),
    ]
    
    COMPANY_SIZE_CHOICES = [
        ('small', gettext_lazy('Pequeña (Menos de 10 empleados)')),
        ('medium', gettext_lazy('Mediana (10 a 50 empleados)')),
        ('large', gettext_lazy('Grande (Más de 50 empleados)')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre')
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Email')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Teléfono')
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Cargo')
    )
    company = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa')
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('País'),
        help_text=gettext_lazy('País del contacto')
    )
    erp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('ERP'),
        help_text=gettext_lazy('Sistema ERP actual del contacto')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='negative',
        verbose_name=gettext_lazy('Estado')
    )
    
    STAGE_CHOICES = [
        ('stage_1', gettext_lazy('1er contacto - Presentación, apertura')),
        ('stage_2', gettext_lazy('2do contacto - Necesidades reales, diagnóstico')),
        ('stage_3', gettext_lazy('3er contacto - Demo o propuesta inicial')),
        ('stage_4', gettext_lazy('4to contacto - Ajustes, dudas, objeciones')),
        ('stage_5', gettext_lazy('5to contacto - Negociación y cierre')),
        ('stage_6', gettext_lazy('6to contacto - Negociación y cierre')),
        ('stage_7', gettext_lazy('7mo contacto - Negociación y cierre')),
        ('stage_8', gettext_lazy('8vo contacto - Negociación y cierre')),
    ]
    
    stage = models.CharField(
        max_length=10,
        choices=STAGE_CHOICES,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Etapa'),
        help_text=gettext_lazy('Etapa del proceso de ventas')
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fuente'),
        help_text=gettext_lazy('¿De dónde obtuviste este contacto?')
    )
    company_size = models.CharField(
        max_length=10,
        choices=COMPANY_SIZE_CHOICES,
        default='small',
        verbose_name=gettext_lazy('Tamaño de Empresa'),
        help_text=gettext_lazy('Tamaño de la empresa del contacto')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el contacto')
    )
    
    # Seguimiento de contacto
    contacted_by_phone = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Contactado por telefono'),
        help_text=gettext_lazy('Marcar si se contacto al cliente por telefono')
    )
    contacted_by_web = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Contactado por web/email'),
        help_text=gettext_lazy('Marcar si se contacto al cliente por web o email')
    )
    had_meeting = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Reunion realizada'),
        help_text=gettext_lazy('Marcar si se tuvo una reunion con este contacto')
    )
    meeting_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de reunion'),
        help_text=gettext_lazy('Fecha en la que se realizo la reunion')
    )
    contact_tracking_notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas de seguimiento'),
        help_text=gettext_lazy('Notas sobre los contactos realizados')
    )
    last_contact_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha del ultimo contacto'),
        help_text=gettext_lazy('Fecha del ultimo contacto realizado')
    )
    
    # Redes sociales y web
    website = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Sitio Web'),
        help_text=gettext_lazy('Sitio web de la empresa o contacto')
    )
    facebook_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Facebook'),
        help_text=gettext_lazy('URL del perfil de Facebook')
    )
    linkedin_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('LinkedIn'),
        help_text=gettext_lazy('URL del perfil de LinkedIn')
    )
    twitter_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Twitter/X'),
        help_text=gettext_lazy('URL del perfil de Twitter/X')
    )
    instagram_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Instagram'),
        help_text=gettext_lazy('URL del perfil de Instagram')
    )
    youtube_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('YouTube'),
        help_text=gettext_lazy('URL del canal de YouTube')
    )
    tiktok_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('TikTok'),
        help_text=gettext_lazy('URL del perfil de TikTok')
    )
    
    contact_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Contacto')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts_created',
        verbose_name=gettext_lazy('Creado por')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_assigned',
        verbose_name=gettext_lazy('Asignado a')
    )
    
    linked_company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        verbose_name=gettext_lazy('Empresa vinculada'),
        help_text=gettext_lazy('Empresa creada a partir de este contacto')
    )
    
    tags = models.ManyToManyField(
        ContactTag,
        blank=True,
        related_name='contacts',
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas para categorizar este contacto')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-contact_date']
        verbose_name = gettext_lazy('Contacto')
        verbose_name_plural = gettext_lazy('Contactos')
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    def get_status_color(self):
        """Retorna el color del estado"""
        if self.status == 'positive':
            return 'success'
        elif self.status == 'neutral':
            return 'primary'
        elif self.status == 'not_now':
            return 'warning'
        elif self.status == 'do_not_contact':
            return 'dark'
        elif self.status == 'won':
            return 'success'
        else:
            return 'danger'
    
    def get_status_icon(self):
        """Retorna el icono del estado"""
        if self.status == 'positive':
            return 'bi-check-circle'
        elif self.status == 'neutral':
            return 'bi-dash-circle'
        elif self.status == 'not_now':
            return 'bi-clock'
        elif self.status == 'do_not_contact':
            return 'bi-slash-circle'
        elif self.status == 'won':
            return 'bi-trophy-fill'
        else:
            return 'bi-x-circle'


def contact_attachment_upload_path(instance, filename):
    """Ruta de subida para adjuntos de contactos"""
    return f'contact_attachments/contact_{instance.contact.id}/{filename}'


class ContactComment(models.Model):
    """Modelo para comentarios en contactos"""
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Contacto')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Comentario'),
        help_text=gettext_lazy('Escribe tu comentario aquí')
    )
    stage = models.CharField(
        max_length=20,
        choices=Contact.STAGE_CHOICES,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Etapa'),
        help_text=gettext_lazy('Etapa del contacto asociada a este comentario')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Comentario de Contacto')
        verbose_name_plural = gettext_lazy('Comentarios de Contacto')
    
    def __str__(self):
        return f"Comentario de {self.user.username} en Contacto {self.contact.name}"
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar este comentario"""
        from .utils import is_agent
        return self.user == user or is_agent(user)
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar este comentario"""
        from .utils import is_agent
        return self.user == user or is_agent(user)


class ContactAttachment(models.Model):
    """Modelo para adjuntos en contactos"""
    contact = models.ForeignKey(
        Contact, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name=gettext_lazy('Contacto')
    )
    file = models.FileField(
        upload_to=contact_attachment_upload_path,
        verbose_name=gettext_lazy('Archivo')
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre original')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Subido por')
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de subida')
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional del adjunto')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = gettext_lazy('Adjunto de Contacto')
        verbose_name_plural = gettext_lazy('Adjuntos de Contacto')
    
    def __str__(self):
        return f"{self.original_filename} - Contacto {self.contact.name}"
    
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


class SalesPlan(models.Model):
    """Modelo para plan de ventas mensual de usuarios"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sales_plans',
        verbose_name=gettext_lazy('Usuario')
    )
    monthly_contact_goal = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Objetivo de contactos al mes'),
        help_text=gettext_lazy('Número de contactos nuevos que debe crear al mes')
    )
    monthly_positive_contact_goal = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Objetivo de contactos positivos al mes'),
        help_text=gettext_lazy('Número de contactos positivos que debe conseguir al mes')
    )
    monthly_meeting_goal = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Objetivo de reuniones mensuales'),
        help_text=gettext_lazy('Número de reuniones que debe realizar al mes')
    )
    monthly_won_goal = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Objetivo de ganados al mes'),
        help_text=gettext_lazy('Número de contactos ganados que debe conseguir al mes')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Plan activo')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Plan de Venta')
        verbose_name_plural = gettext_lazy('Planes de Venta')
    
    def __str__(self):
        return f"Plan de {self.user.get_full_name() or self.user.username}"
    
    def get_monthly_progress(self):
        """Calcula el progreso del mes actual"""
        from django.db.models import Count, Q
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular el mismo día del mes pasado
        last_month = now - relativedelta(months=1)
        last_month_start = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_same_day = last_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Contactos creados este mes
        contacts_created = Contact.objects.filter(
            created_by=self.user,
            created_at__gte=month_start,
            created_at__lte=now
        ).count()
        
        # Contactos del mismo día del mes pasado
        contacts_last_month = Contact.objects.filter(
            created_by=self.user,
            created_at__gte=last_month_start,
            created_at__lte=last_month_same_day
        ).count()
        
        # Contactos positivos este mes
        positive_contacts = Contact.objects.filter(
            created_by=self.user,
            status='positive',
            created_at__gte=month_start,
            created_at__lte=now
        ).count()
        
        # Positivos del mes pasado
        positive_last_month = Contact.objects.filter(
            created_by=self.user,
            status='positive',
            created_at__gte=last_month_start,
            created_at__lte=last_month_same_day
        ).count()
        
        # Reuniones este mes
        meetings_held = Contact.objects.filter(
            created_by=self.user,
            had_meeting=True,
            meeting_date__gte=month_start.date(),
            meeting_date__lte=now.date()
        ).count()
        
        # Reuniones del mes pasado
        meetings_last_month = Contact.objects.filter(
            created_by=self.user,
            had_meeting=True,
            meeting_date__gte=last_month_start.date(),
            meeting_date__lte=last_month_same_day.date()
        ).count()
        
        # Contactos ganados este mes
        won_contacts = Contact.objects.filter(
            created_by=self.user,
            status='won',
            created_at__gte=month_start,
            created_at__lte=now
        ).count()
        
        # Ganados del mes pasado
        won_last_month = Contact.objects.filter(
            created_by=self.user,
            status='won',
            created_at__gte=last_month_start,
            created_at__lte=last_month_same_day
        ).count()
        
        # Calcular diferencias
        contacts_diff = contacts_created - contacts_last_month
        positive_diff = positive_contacts - positive_last_month
        meetings_diff = meetings_held - meetings_last_month
        won_diff = won_contacts - won_last_month
        
        # Calcular porcentajes
        contact_percentage = (contacts_created / self.monthly_contact_goal * 100) if self.monthly_contact_goal > 0 else 0
        positive_percentage = (positive_contacts / self.monthly_positive_contact_goal * 100) if self.monthly_positive_contact_goal > 0 else 0
        meeting_percentage = (meetings_held / self.monthly_meeting_goal * 100) if self.monthly_meeting_goal > 0 else 0
        won_percentage = (won_contacts / self.monthly_won_goal * 100) if self.monthly_won_goal > 0 else 0
        
        # Promedio general
        overall_percentage = (contact_percentage + positive_percentage + meeting_percentage + won_percentage) / 4
        
        return {
            'contacts_created': contacts_created,
            'contacts_goal': self.monthly_contact_goal,
            'contact_percentage': round(contact_percentage, 1),
            'contacts_last_month': contacts_last_month,
            'contacts_diff': contacts_diff,
            'positive_contacts': positive_contacts,
            'positive_goal': self.monthly_positive_contact_goal,
            'positive_percentage': round(positive_percentage, 1),
            'positive_last_month': positive_last_month,
            'positive_diff': positive_diff,
            'meetings_held': meetings_held,
            'meeting_goal': self.monthly_meeting_goal,
            'meeting_percentage': round(meeting_percentage, 1),
            'meetings_last_month': meetings_last_month,
            'meetings_diff': meetings_diff,
            'won_contacts': won_contacts,
            'won_goal': self.monthly_won_goal,
            'won_percentage': round(won_percentage, 1),
            'won_last_month': won_last_month,
            'won_diff': won_diff,
            'overall_percentage': round(overall_percentage, 1)
        }


class BlogCategory(models.Model):
    """Categorías para los artículos del blog"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Nombre')
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Slug URL')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color en formato hexadecimal (ej: #007bff)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Categoría de Blog')
        verbose_name_plural = gettext_lazy('Categorías de Blog')
    
    def __str__(self):
        return self.name


class BlogPost(models.Model):
    """Artículos del blog"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('published', gettext_lazy('Publicado')),
        ('archived', gettext_lazy('Archivado')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=gettext_lazy('Slug URL')
    )
    excerpt = models.TextField(
        max_length=300,
        verbose_name=gettext_lazy('Resumen'),
        help_text=gettext_lazy('Breve descripción del artículo (máx. 300 caracteres)')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Contenido')
    )
    featured_image = models.ImageField(
        upload_to='blog/images/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Imagen Principal')
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name=gettext_lazy('Categoría')
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por comas')
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=gettext_lazy('Meta Descripción'),
        help_text=gettext_lazy('Descripción para SEO (máx. 160 caracteres)')
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de visualizaciones')
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Artículo Destacado')
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de publicación')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = gettext_lazy('Artículo de Blog')
        verbose_name_plural = gettext_lazy('Artículos de Blog')
    
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
        verbose_name=gettext_lazy('Artículo')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre')
    )
    email = models.EmailField(
        verbose_name=gettext_lazy('Email')
    )
    website = models.URLField(
        blank=True,
        verbose_name=gettext_lazy('Sitio Web')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Aprobado')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Comentario de Blog')
        verbose_name_plural = gettext_lazy('Comentarios de Blog')
    
    def __str__(self):
        return f"{self.name} en {self.post.title}"


class AIChatSession(models.Model):
    """Modelo para sesiones de chat con IA"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_chat_sessions',
        verbose_name=gettext_lazy('Usuario')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la conversación'),
        help_text=gettext_lazy('Título descriptivo de la conversación')
    )
    ai_model = models.CharField(
        max_length=50,
        default='gpt-4o',
        verbose_name=gettext_lazy('Modelo de IA'),
        help_text=gettext_lazy('Modelo utilizado para esta conversación')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Sesión activa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = gettext_lazy('Sesión de Chat IA')
        verbose_name_plural = gettext_lazy('Sesiones de Chat IA')
    
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
        ('user', gettext_lazy('Usuario')),
        ('assistant', gettext_lazy('IA')),
        ('system', gettext_lazy('Sistema')),
    ]
    
    session = models.ForeignKey(
        AIChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=gettext_lazy('Sesión')
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name=gettext_lazy('Rol')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Contenido del mensaje')
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Tokens utilizados'),
        help_text=gettext_lazy('Número de tokens consumidos para este mensaje')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Mensaje de Chat IA')
        verbose_name_plural = gettext_lazy('Mensajes de Chat IA')
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."
    
    def is_from_user(self):
        """Verifica si el mensaje es del usuario"""
        return self.role == 'user'
    
    def is_from_ai(self):
        """Verifica si el mensaje es de la IA"""
        return self.role == 'assistant'


class SharedAIChatMessage(models.Model):
    """DEPRECATED - Usar PublicAIMessageShare en su lugar"""
    
    message = models.ForeignKey(
        'AIChatMessage',
        on_delete=models.CASCADE,
        related_name='shared_instances_old',
        verbose_name=gettext_lazy('Mensaje')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shared_ai_messages_old',
        verbose_name=gettext_lazy('Usuario que compartió')
    )
    share_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=gettext_lazy('Token de compartición'),
        help_text=gettext_lazy('Token único para acceder al mensaje compartido')
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Título público'),
        help_text=gettext_lazy('Título opcional para el mensaje compartido')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Compartición activa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de compartición')
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de vistas')
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración'),
        help_text=gettext_lazy('Fecha en que expira el enlace compartido (opcional)')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Mensaje IA Compartido (Deprecated)')
        verbose_name_plural = gettext_lazy('Mensajes IA Compartidos (Deprecated)')
        db_table = 'tickets_sharedaichatmessage_old'
    
    def __str__(self):
        title = self.title or f"Mensaje de {self.user.username}"
        return f"{title} - {self.share_token[:8]}..."
    
    def get_public_url(self):
        """Retorna la URL pública del mensaje compartido"""
        from django.urls import reverse
        return reverse('shared_ai_message_view', kwargs={'token': self.share_token})
    
    def is_expired(self):
        """Verifica si el enlace ha expirado"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def increment_views(self):
        """Incrementa el contador de vistas"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class PublicAIMessageShare(models.Model):
    """Modelo nuevo para mensajes de chat IA compartidos públicamente"""
    
    chat_message = models.ForeignKey(
        'AIChatMessage',
        on_delete=models.CASCADE,
        related_name='public_shares',
        verbose_name=gettext_lazy('Mensaje de Chat')
    )
    shared_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_message_shares',
        verbose_name=gettext_lazy('Compartido por')
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name=gettext_lazy('Token de compartición'),
        help_text=gettext_lazy('Token único para acceder al mensaje compartido')
    )
    public_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Título público'),
        help_text=gettext_lazy('Título opcional para el mensaje compartido')
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=gettext_lazy('Compartición activa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name=gettext_lazy('Fecha de compartición')
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de vistas')
    )
    expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración'),
        help_text=gettext_lazy('Fecha en que expira el enlace compartido (opcional)')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Compartición de Mensaje IA')
        verbose_name_plural = gettext_lazy('Comparticiones de Mensajes IA')
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['shared_by', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        title = self.public_title or f"Mensaje de {self.shared_by.username}"
        return f"{title} - {self.token[:8]}..."
    
    def get_public_url(self):
        """Retorna la URL pública del mensaje compartido"""
        from django.urls import reverse
        return reverse('shared_ai_message_view', kwargs={'token': self.token})
    
    def is_expired(self):
        """Verifica si el enlace ha expirado"""
        if not self.expiration_date:
            return False
        return timezone.now() > self.expiration_date
    
    def increment_views(self):
        """Incrementa el contador de vistas de forma atómica"""
        from django.db.models import F
        PublicAIMessageShare.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)
        self.refresh_from_db()


class Concept(models.Model):
    """Modelo para gestionar conceptos y definiciones que se muestran en el home"""
    
    term = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=gettext_lazy('Término'),
        help_text=gettext_lazy('El concepto o término a definir')
    )
    definition = models.TextField(
        verbose_name=gettext_lazy('Definición'),
        help_text=gettext_lazy('Explicación del concepto')
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Categoría'),
        help_text=gettext_lazy('Categoría del concepto (opcional)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si el concepto debe mostrarse en el home')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición (menor número aparece primero)')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='concepts_created',
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['order', 'term']
        verbose_name = gettext_lazy('Concepto')
        verbose_name_plural = gettext_lazy('Conceptos')
    
    def __str__(self):
        return f"{self.term}: {self.definition[:50]}..."


class Exam(models.Model):
    """Modelo para los exámenes"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Examen')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('¿Es público?')
    )
    public_token = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token público')
    )
    passing_score = models.IntegerField(
        default=70,
        verbose_name=gettext_lazy('Puntuación mínima para aprobar (%)')
    )
    time_limit = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Tiempo límite (minutos)'),
        help_text=gettext_lazy('Dejar vacío para sin límite de tiempo')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = gettext_lazy('Examen')
        verbose_name_plural = gettext_lazy('Exámenes')
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
        verbose_name=gettext_lazy('Examen')
    )
    question_text = models.TextField(
        verbose_name=gettext_lazy('Pregunta')
    )
    option_a = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Opción A')
    )
    option_b = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Opción B')
    )
    option_c = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Opción C')
    )
    correct_option = models.CharField(
        max_length=1,
        choices=[('A', gettext_lazy('Opción A')), ('B', gettext_lazy('Opción B')), ('C', gettext_lazy('Opción C'))],
        verbose_name=gettext_lazy('Opción correcta')
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name=gettext_lazy('Orden')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = gettext_lazy('Pregunta del Examen')
        verbose_name_plural = gettext_lazy('Preguntas del Examen')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.exam.title} - Pregunta {self.order}"


class ExamAttempt(models.Model):
    """Modelo para los intentos de examen"""
    
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=gettext_lazy('Examen')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Usuario')
    )
    participant_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del participante')
    )
    participant_email = models.EmailField(
        verbose_name=gettext_lazy('Email del participante')
    )
    score = models.FloatField(
        verbose_name=gettext_lazy('Puntuación (%)')
    )
    total_questions = models.IntegerField(
        verbose_name=gettext_lazy('Total de preguntas')
    )
    correct_answers = models.IntegerField(
        verbose_name=gettext_lazy('Respuestas correctas')
    )
    started_at = models.DateTimeField(
        verbose_name=gettext_lazy('Iniciado en')
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Completado en')
    )
    time_taken = models.IntegerField(
        verbose_name=gettext_lazy('Tiempo tomado (segundos)')
    )
    passed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('¿Aprobado?')
    )
    certificate_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token del certificado')
    )
    certificate_generated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Certificado generado en')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Intento de Examen')
        verbose_name_plural = gettext_lazy('Intentos de Examen')
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
        verbose_name=gettext_lazy('Intento')
    )
    question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Pregunta')
    )
    selected_option = models.CharField(
        max_length=1,
        choices=[('A', gettext_lazy('Opción A')), ('B', gettext_lazy('Opción B')), ('C', gettext_lazy('Opción C'))],
        verbose_name=gettext_lazy('Opción seleccionada')
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('¿Es correcta?')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Respuesta del Examen')
        verbose_name_plural = gettext_lazy('Respuestas del Examen')
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.participant_name} - {self.question.question_text[:50]}..."


class ContactoWeb(models.Model):
    """Modelo para gestionar contactos desde la web pública"""
    
    nombre = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre completo')
    )
    email = models.EmailField(
        verbose_name=gettext_lazy('Correo electrónico')
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Teléfono')
    )
    empresa = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa')
    )
    asunto = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Asunto')
    )
    mensaje = models.TextField(
        verbose_name=gettext_lazy('Mensaje')
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    leido = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Leído')
    )
    respondido = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Respondido')
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Contacto Web')
        verbose_name_plural = gettext_lazy('Contactos Web')
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
        verbose_name=gettext_lazy('Token de subida'),
        help_text=gettext_lazy('Token único para la URL pública de subida')
    )
    
    # Configuración de la URL
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la subida'),
        help_text=gettext_lazy('Descripción de qué tipo de documentos se esperan')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Instrucciones'),
        help_text=gettext_lazy('Instrucciones para quien vaya a subir el documento')
    )
    
    # Usuario que creó la URL
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='public_upload_urls',
        verbose_name=gettext_lazy('Creado por')
    )
    
    # Empresa asociada (opcional)
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='public_upload_urls',
        verbose_name=gettext_lazy('Empresa/Cliente'),
        help_text=gettext_lazy('Empresa o cliente para el cual se subirán los documentos')
    )
    
    # Configuración de expiración
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración'),
        help_text=gettext_lazy('Opcional: fecha límite para usar esta URL')
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Si está desactivada, no se pueden subir más documentos')
    )
    
    # Configuración de límites
    max_uploads = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Máximo de subidas'),
        help_text=gettext_lazy('Opcional: límite de documentos que se pueden subir')
    )
    upload_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Documentos subidos'),
        help_text=gettext_lazy('Contador de documentos subidos usando esta URL')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Último uso')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('URL Pública de Subida')
        verbose_name_plural = gettext_lazy('URLs Públicas de Subida')
    
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
        verbose_name=gettext_lazy('Nombre')
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Apellidos')
    )
    email = models.EmailField(
        unique=True,
        verbose_name=gettext_lazy('Correo electrónico')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Teléfono')
    )
    
    # Información profesional
    position = models.CharField(
        max_length=150,
        verbose_name=gettext_lazy('Cargo')
    )
    salary_euros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Salario (EUR)')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción/Experiencia')
    )
    
    # Currículo
    resume_file = models.FileField(
        upload_to='resumes/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Archivo de currículo')
    )
    
    # Análisis de IA
    ai_analysis = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Análisis de IA'),
        help_text=gettext_lazy('Resumen automático generado por IA')
    )
    ai_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Puntuación IA (1-10)'),
        help_text=gettext_lazy('Puntuación automática del candidato')
    )
    
    # Opinión de reunión de contratación
    hiring_meeting_opinion = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Opinión de reunión de contratación'),
        help_text=gettext_lazy('Comentarios y evaluación de la reunión/entrevista de contratación')
    )
    
    # Relaciones
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name=gettext_lazy('Empresa')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_employees',
        verbose_name=gettext_lazy('Creado por')
    )
    
    # Estados
    STATUS_CHOICES = [
        ('candidate', gettext_lazy('Candidato')),
        ('in_process', gettext_lazy('En trámites')),
        ('employee', gettext_lazy('Empleado')),
        ('not_employee', gettext_lazy('No empleado')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='candidate',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de aplicación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Empleado')
        verbose_name_plural = gettext_lazy('Empleados')
    
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
        verbose_name=gettext_lazy('Empleado')
    )
    
    # Información de la nómina
    period_month = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Mes'),
        help_text=gettext_lazy('Mes de la nómina (1-12)')
    )
    period_year = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Año'),
        help_text=gettext_lazy('Año de la nómina')
    )
    
    # Archivos
    payroll_pdf = models.FileField(
        upload_to='payrolls/',
        verbose_name=gettext_lazy('Nómina (PDF)'),
        help_text=gettext_lazy('Archivo PDF de la nómina')
    )
    payment_receipt = models.FileField(
        upload_to='payment_receipts/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Comprobante de pago'),
        help_text=gettext_lazy('Archivo del comprobante de pago (opcional)')
    )
    
    # Información adicional
    gross_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Salario bruto')
    )
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Salario neto')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre esta nómina')
    )
    
    # Control
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_payrolls',
        verbose_name=gettext_lazy('Creado por')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de registro')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-period_year', '-period_month', '-created_at']
        verbose_name = gettext_lazy('Nómina de Empleado')
        verbose_name_plural = gettext_lazy('Nóminas de Empleados')
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
        verbose_name=gettext_lazy('Token de aplicación')
    )
    
    # Información del puesto
    job_title = models.CharField(
        max_length=150,
        verbose_name=gettext_lazy('Título del puesto')
    )
    job_description = models.TextField(
        verbose_name=gettext_lazy('Descripción del puesto')
    )
    proposed_salary_euros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Salario propuesto (EUR)'),
        help_text=gettext_lazy('Salario que la empresa está dispuesta a pagar')
    )
    
    # Configuración
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='job_application_tokens',
        verbose_name=gettext_lazy('Empresa')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_job_tokens',
        verbose_name=gettext_lazy('Creado por')
    )
    
    # Estado y expiración
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración')
    )
    max_applications = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Máximo de aplicaciones')
    )
    application_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Aplicaciones recibidas')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Token de Aplicación de Empleo')
        verbose_name_plural = gettext_lazy('Tokens de Aplicación de Empleo')
    
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
        ('draft', gettext_lazy('Borrador')),
        ('published', gettext_lazy('Publicado')),
        ('signed', gettext_lazy('Firmado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    # Información básica del acuerdo
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Acuerdo')
    )
    body = models.TextField(
        verbose_name=gettext_lazy('Cuerpo del Acuerdo'),
        help_text=gettext_lazy('Contenido completo del acuerdo/contrato')
    )
    
    # Control de estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    
    # URLs y tokens
    public_token = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Token Público')
    )
    
    # Metadatos
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Empresa')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_agreements',
        verbose_name=gettext_lazy('Creado por')
    )
    
    # Control de fechas
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de publicación')
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración')
    )
    
    # Configuración
    max_signers = models.PositiveIntegerField(
        default=10,
        verbose_name=gettext_lazy('Máximo de firmantes'),
        help_text=gettext_lazy('Número máximo de personas que pueden firmar este acuerdo')
    )
    requires_approval = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Requiere aprobación'),
        help_text=gettext_lazy('Las firmas requieren aprobación antes de ser válidas')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Acuerdo')
        verbose_name_plural = gettext_lazy('Acuerdos')
    
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
        verbose_name=gettext_lazy('Acuerdo')
    )
    
    # Información del firmante
    signer_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del firmante')
    )
    signer_email = models.EmailField(
        verbose_name=gettext_lazy('Email del firmante')
    )
    signature_data = models.TextField(
        verbose_name=gettext_lazy('Datos de la firma'),
        help_text=gettext_lazy('Datos de la firma digital (base64)')
    )
    
    # Control de firma
    signed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de firma')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    # Estado de la firma
    is_valid = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Firma válida')
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Firma aprobada')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_signatures',
        verbose_name=gettext_lazy('Aprobado por')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de aprobación')
    )
    
    # Descarga del PDF
    pdf_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('PDF descargado en')
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Veces descargado')
    )
    
    class Meta:
        ordering = ['-signed_at']
        verbose_name = gettext_lazy('Firma de Acuerdo')
        verbose_name_plural = gettext_lazy('Firmas de Acuerdos')
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
        verbose_name=gettext_lazy('Nombre del Producto')
    )
    descripcion = models.TextField(
        verbose_name=gettext_lazy('Descripción del Producto'),
        help_text=gettext_lazy('Descripción que aparecerá en la landing page')
    )
    imagen = models.ImageField(
        upload_to='landing_pages/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Imagen del Producto'),
        help_text=gettext_lazy('Imagen principal de la landing page')
    )
    
    # Configuración de URL pública
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=gettext_lazy('URL de la Landing Page'),
        help_text=gettext_lazy('URL única para acceder a la landing page (ej: mi-producto)')
    )
    
    # Token de API para seguridad
    api_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token de API'),
        help_text=gettext_lazy('Token único para autenticar llamadas a la API de esta landing page')
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Página Activa'),
        help_text=gettext_lazy('Si está activa, la landing page será accesible públicamente')
    )
    
    # Configuración de diseño
    color_principal = models.CharField(
        max_length=7,
        default='#00A651',
        verbose_name=gettext_lazy('Color Principal'),
        help_text=gettext_lazy('Color principal de la landing page (formato HEX: #00A651)')
    )
    color_secundario = models.CharField(
        max_length=7,
        default='#E8F5E8',
        verbose_name=gettext_lazy('Color Secundario'),
        help_text=gettext_lazy('Color secundario para fondos (formato HEX: #E8F5E8)')
    )
    
    # Configuración del formulario
    titulo_formulario = models.CharField(
        max_length=200,
        default='VEA TODAS LAS DEMOSTRACIONES',
        verbose_name=gettext_lazy('Título del Formulario')
    )
    subtitulo_formulario = models.TextField(
        default='Salesforce acerca a las empresas con sus clientes. Vea nuestras demostraciones gratuitas y obtenga más información sobre cómo podemos ayudar a su negocio.',
        verbose_name=gettext_lazy('Subtítulo del Formulario')
    )
    
    # Configuración de empresa/campaña
    empresa_campana = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Empresa de la Campaña'),
        help_text=gettext_lazy('Nombre de la empresa que ejecuta la campaña')
    )
    
    # Configuración de Telegram
    telegram_bot_token = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Bot Token de Telegram'),
        help_text=gettext_lazy('Token del bot de Telegram para enviar notificaciones (ej: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)')
    )
    telegram_chat_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Chat ID de Telegram'),
        help_text=gettext_lazy('ID del chat o canal donde enviar las notificaciones (ej: -1001234567890 o @mi_canal)')
    )
    
    # URL de reunión
    meeting_url = models.URLField(
        blank=True,
        verbose_name=gettext_lazy('URL de Reunión'),
        help_text=gettext_lazy('URL para planificar reuniones (ej: Calendly, Google Meet, Zoom, etc.)')
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Estadísticas
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de visitas')
    )
    submissions_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Formularios enviados')
    )
    meeting_button_clicks = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Clics en "Planificar Reunión"')
    )
    contact_button_clicks = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Clics en "Contactar"')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Landing Page')
        verbose_name_plural = gettext_lazy('Landing Pages')
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
        verbose_name=gettext_lazy('Landing Page')
    )
    
    # Datos del formulario
    nombre = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre')
    )
    apellido = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Apellido')
    )
    email = models.EmailField(
        verbose_name=gettext_lazy('Email')
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name=gettext_lazy('Teléfono')
    )
    empresa = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Empresa')
    )
    cargo = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Cargo')
    )
    mensaje = models.TextField(
        verbose_name=gettext_lazy('Mensaje o comentarios'),
        help_text=gettext_lazy('Cuéntanos más sobre tus necesidades o proyecto')
    )
    
    # Preferencias de contacto
    preferred_contact_time = models.CharField(
        max_length=20,
        choices=[
            ('asap', gettext_lazy('Lo antes posible')),
            ('monday', gettext_lazy('El próximo lunes')),
            ('tuesday', gettext_lazy('El próximo martes')),
            ('wednesday', gettext_lazy('El próximo miércoles')),
            ('thursday', gettext_lazy('El próximo jueves')),
            ('friday', gettext_lazy('El próximo viernes')),
            ('next_week', gettext_lazy('La próxima semana')),
            ('flexible', gettext_lazy('Horario flexible')),
        ],
        default='asap',
        verbose_name=gettext_lazy('Cuándo prefieres que te contactemos')
    )
    
    # Metadatos de seguimiento
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('User Agent')
    )
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('UTM Source')
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('UTM Medium')
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('UTM Campaign')
    )
    
    # Estado
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de envío')
    )
    processed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Procesado')
    )
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de procesamiento')
    )
    processed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='processed_submissions',
        verbose_name=gettext_lazy('Procesado por')
    )
    
    # Evaluación de IA
    ai_evaluated = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Evaluado por IA')
    )
    ai_evaluation_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de evaluación IA')
    )
    ai_company_score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Puntuación Empresa (1-10)'),
        help_text=gettext_lazy('Evaluación de la calidad/seriedad de la empresa')
    )
    ai_contact_score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Puntuación Contacto (1-10)'),
        help_text=gettext_lazy('Evaluación de la calidad del contacto')
    )
    ai_project_score = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Puntuación Proyecto (1-10)'),
        help_text=gettext_lazy('Evaluación del potencial del proyecto')
    )
    ai_overall_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Puntuación General'),
        help_text=gettext_lazy('Puntuación promedio general')
    )
    ai_evaluation_summary = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Resumen de Evaluación IA'),
        help_text=gettext_lazy('Resumen detallado de la evaluación')
    )
    ai_recommendations = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Recomendaciones IA'),
        help_text=gettext_lazy('Recomendaciones de seguimiento')
    )
    ai_priority_level = models.CharField(
        max_length=20,
        choices=[
            ('low', gettext_lazy('Baja')),
            ('medium', gettext_lazy('Media')),
            ('high', gettext_lazy('Alta')),
            ('urgent', gettext_lazy('Urgente')),
        ],
        blank=True,
        verbose_name=gettext_lazy('Nivel de Prioridad IA')
    )

    # Detección de spam
    is_spam = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Es Spam')
    )
    spam_reason = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Motivo de Spam')
    )

    class Meta:
        verbose_name = gettext_lazy('Envío de Landing Page')
        verbose_name_plural = gettext_lazy('Envíos de Landing Pages')
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


class RegistroEntrada(models.Model):
    """Registro de visitas/entradas al local o empresa"""

    DOCUMENTO_CHOICES = [
        ('dni', gettext_lazy('DNI')),
        ('nie', gettext_lazy('NIE')),
        ('pasaporte', gettext_lazy('Pasaporte')),
        ('otro', gettext_lazy('Otro')),
    ]

    nombre = models.CharField(max_length=100, verbose_name=gettext_lazy('Nombre'))
    apellido = models.CharField(max_length=100, verbose_name=gettext_lazy('Apellido'))
    tipo_documento = models.CharField(
        max_length=20,
        choices=DOCUMENTO_CHOICES,
        default='dni',
        verbose_name=gettext_lazy('Tipo de Documento')
    )
    numero_documento = models.CharField(
        max_length=50,
        verbose_name=gettext_lazy('Número de Documento')
    )
    que_hara = models.TextField(verbose_name=gettext_lazy('¿Qué hará?'))
    telefono = models.CharField(max_length=20, verbose_name=gettext_lazy('Teléfono'))
    direccion = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Dirección')
    )
    fecha = models.DateField(auto_now_add=True, verbose_name=gettext_lazy('Fecha'))
    hora = models.TimeField(auto_now_add=True, verbose_name=gettext_lazy('Hora'))
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, verbose_name=gettext_lazy('IP')
    )

    class Meta:
        verbose_name = gettext_lazy('Registro de Entrada')
        verbose_name_plural = gettext_lazy('Registros de Entrada')
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"{self.nombre} {self.apellido} — {self.fecha}"


class RegistroEntradaConfig(models.Model):
    """Configuración global del Registro de Entrada (token público, singleton)"""

    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=gettext_lazy('Token Público')
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = gettext_lazy('Configuración Registro de Entrada')
        verbose_name_plural = gettext_lazy('Configuración Registro de Entrada')

    def __str__(self):
        return f"Token: {self.public_token}"

    @classmethod
    def get_or_create_config(cls):
        """Devuelve la configuración única, creándola si no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def regenerate_token(self):
        self.public_token = uuid.uuid4()
        self.save(update_fields=['public_token', 'updated_at'])
        return self.public_token


class SharedFile(models.Model):
    """Modelo para gestionar archivos compartidos"""

    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Archivo')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional del archivo')
    )
    file = models.FileField(
        upload_to='shared_files/%Y/%m/',
        verbose_name=gettext_lazy('Archivo')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='shared_files',
        verbose_name=gettext_lazy('Empresa'),
        null=True,
        blank=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name=gettext_lazy('Subido por'),
        null=True,
        blank=True
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Público'),
        help_text=gettext_lazy('Si está marcado, todos los usuarios de la empresa pueden ver este archivo')
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    file_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Tipo de archivo')
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de descargas')
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Archivo Compartido')
        verbose_name_plural = gettext_lazy('Archivos Compartidos')
    
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
        verbose_name=gettext_lazy('Archivo Compartido')
    )
    downloaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='file_downloads',
        verbose_name=gettext_lazy('Descargado por'),
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    downloaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de descarga')
    )
    
    class Meta:
        ordering = ['-downloaded_at']
        verbose_name = gettext_lazy('Descarga de Archivo')
        verbose_name_plural = gettext_lazy('Descargas de Archivos')
    
    def __str__(self):
        user = self.downloaded_by.username if self.downloaded_by else 'Anónimo'
        return f"{self.shared_file.title} - {user} - {self.downloaded_at}"


class Recording(models.Model):
    """Modelo para gestionar grabaciones de audio con transcripción IA"""
    
    TRANSCRIPTION_STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('processing', gettext_lazy('Procesando')),
        ('completed', gettext_lazy('Completada')),
        ('failed', gettext_lazy('Fallida')),
    ]
    
    title = models.CharField(
        max_length=200, 
        verbose_name=gettext_lazy('Título de la grabación')
    )
    description = models.TextField(
        blank=True, 
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional de la grabación')
    )
    audio_file = models.FileField(
        upload_to='recordings/%Y/%m/',
        verbose_name=gettext_lazy('Archivo de audio')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='recordings',
        verbose_name=gettext_lazy('Empresa'),
        null=True,
        blank=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_recordings',
        verbose_name=gettext_lazy('Subido por'),
        null=True,
        blank=True
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Público'),
        help_text=gettext_lazy('Si está marcado, todos los usuarios de la empresa pueden ver esta grabación')
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Duración en segundos')
    )
    
    # Campos de transcripción
    transcription_status = models.CharField(
        max_length=20,
        choices=TRANSCRIPTION_STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado de transcripción')
    )
    transcription_text = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Texto transcrito')
    )
    transcription_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Confianza de transcripción (%)'),
        help_text=gettext_lazy('Porcentaje de confianza de la transcripción')
    )
    transcription_language = models.CharField(
        max_length=10,
        default='es',
        verbose_name=gettext_lazy('Idioma detectado')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=gettext_lazy('Última actualización')
    )
    transcribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de transcripción')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Grabación')
        verbose_name_plural = gettext_lazy('Grabaciones')
    
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
        verbose_name=gettext_lazy('Grabación')
    )
    played_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recording_playbacks',
        verbose_name=gettext_lazy('Reproducido por'),
        null=True,
        blank=True
    )
    played_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de reproducción')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    class Meta:
        ordering = ['-played_at']
        verbose_name = gettext_lazy('Reproducción')
        verbose_name_plural = gettext_lazy('Reproducciones')
    
    def __str__(self):
        user = self.played_by.username if self.played_by else 'Anónimo'
        return f"{self.recording.title} - {user} - {self.played_at}"


class PageVisit(models.Model):
    """Modelo para registrar visitas a páginas públicas"""
    
    PAGE_CHOICES = [
        ('home', gettext_lazy('Página de Inicio')),
        ('blog', gettext_lazy('Blog')),
        ('blog_post', gettext_lazy('Artículo de Blog')),
        ('conceptos', gettext_lazy('Conceptos Públicos')),
        ('contact', gettext_lazy('Contacto')),
        ('landing', gettext_lazy('Landing Page')),
        ('course_public', gettext_lazy('Curso Público')),
        ('ticket_public', gettext_lazy('Ticket Público')),
        ('other', gettext_lazy('Otra')),
    ]
    
    # Información de la página visitada
    page_type = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        verbose_name=gettext_lazy('Tipo de Página')
    )
    page_url = models.URLField(
        max_length=500,
        verbose_name=gettext_lazy('URL Visitada')
    )
    page_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Título de la Página')
    )
    
    # Información del visitante
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Dirección IP')
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('País')
    )
    country_code = models.CharField(
        max_length=2,
        blank=True,
        verbose_name=gettext_lazy('Código de País')
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Ciudad')
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Región/Estado')
    )
    
    # Información técnica
    user_agent = models.TextField(
        verbose_name=gettext_lazy('User Agent')
    )
    browser = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Navegador')
    )
    browser_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Versión del Navegador')
    )
    operating_system = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Sistema Operativo')
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Tipo de Dispositivo')
    )
    is_mobile = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Es Móvil')
    )
    is_bot = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Es Bot')
    )
    
    # Información de referencia
    referrer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Página de Referencia')
    )
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('UTM Source')
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('UTM Medium')
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('UTM Campaign')
    )
    
    # Información de sesión
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('ID de Sesión')
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Duración en Segundos')
    )
    
    # Metadatos
    visited_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Visita')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        ordering = ['-visited_at']
        verbose_name = gettext_lazy('Visita a Página')
        verbose_name_plural = gettext_lazy('Visitas a Páginas')
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
        verbose_name=gettext_lazy('Nombre del Configurador'),
        help_text=gettext_lazy('Nombre descriptivo para identificar este configurador')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional de qué tipo de contenido genera')
    )
    
    # Configuración de palabras clave
    keywords = models.TextField(
        verbose_name=gettext_lazy('Palabras Clave'),
        help_text=gettext_lazy('Palabras clave separadas por comas para generar contenido (ej: tecnología, desarrollo, python)')
    )
    
    # Configuración de generación
    topic_template = models.TextField(
        default='Escribe un artículo completo sobre {keyword} con ejemplos prácticos y consejos útiles.',
        verbose_name=gettext_lazy('Plantilla de Tema'),
        help_text=gettext_lazy('Plantilla para generar el prompt. Usa {keyword} donde quieras insertar la palabra clave')
    )
    
    content_length = models.CharField(
        max_length=50,
        choices=[
            ('short', gettext_lazy('Corto (500-800 palabras)')),
            ('medium', gettext_lazy('Medio (800-1200 palabras)')),
            ('long', gettext_lazy('Largo (1200-2000 palabras)')),
        ],
        default='medium',
        verbose_name=gettext_lazy('Longitud del Contenido')
    )
    
    content_style = models.CharField(
        max_length=50,
        choices=[
            ('professional', gettext_lazy('Profesional')),
            ('casual', gettext_lazy('Casual')),
            ('technical', gettext_lazy('Técnico')),
            ('educational', gettext_lazy('Educativo')),
            ('news', gettext_lazy('Noticia')),
        ],
        default='professional',
        verbose_name=gettext_lazy('Estilo del Contenido')
    )
    
    # Configuración de programación
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está activo, el configurador puede generar contenido automáticamente')
    )
    
    schedule_time = models.TimeField(
        default='10:00',
        verbose_name=gettext_lazy('Hora de Ejecución'),
        help_text=gettext_lazy('Hora del día para ejecutar la generación automática (formato 24h)')
    )
    
    frequency_days = models.PositiveIntegerField(
        default=1,
        verbose_name=gettext_lazy('Frecuencia (días)'),
        help_text=gettext_lazy('Cada cuántos días ejecutar (1 = diario, 7 = semanal, etc.)')
    )
    
    max_posts_per_run = models.PositiveIntegerField(
        default=1,
        verbose_name=gettext_lazy('Máximo Posts por Ejecución'),
        help_text=gettext_lazy('Número máximo de posts a generar en cada ejecución')
    )
    
    # Configuración de categoría
    default_category = models.ForeignKey(
        'BlogCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Categoría por Defecto'),
        help_text=gettext_lazy('Categoría a asignar a los posts generados')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última Ejecución')
    )
    total_posts_generated = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Total Posts Generados')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Configurador de IA para Blog')
        verbose_name_plural = gettext_lazy('Configuradores de IA para Blog')
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
        verbose_name=gettext_lazy('Configurador')
    )
    
    keyword_used = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Palabra Clave Utilizada')
    )
    
    generated_post = models.ForeignKey(
        'BlogPost',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Post Generado')
    )
    
    prompt_used = models.TextField(
        verbose_name=gettext_lazy('Prompt Utilizado')
    )
    
    generation_status = models.CharField(
        max_length=20,
        choices=[
            ('success', gettext_lazy('Exitoso')),
            ('error', gettext_lazy('Error')),
            ('pending', gettext_lazy('Pendiente')),
        ],
        default='pending',
        verbose_name=gettext_lazy('Estado de Generación')
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Mensaje de Error')
    )
    
    execution_time_seconds = models.FloatField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tiempo de Ejecución (segundos)')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Log de Generación IA')
        verbose_name_plural = gettext_lazy('Logs de Generación IA')
        ordering = ['-created_at']
    
    def __str__(self):
        status_icon = '✅' if self.generation_status == 'success' else '❌' if self.generation_status == 'error' else '⏳'
        return f"{status_icon} {self.configurator.name} - {self.keyword_used} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"


class MultipleDocumentation(models.Model):
    """Modelo para gestionar documentación múltiple en una sola URL pública"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la Documentación')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción de qué contiene esta documentación')
    )
    
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está activo, se puede acceder públicamente')
    )
    
    # Protección con contraseña
    password_protected = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Protegido con contraseña'),
        help_text=gettext_lazy('Si está marcado, se requerirá una contraseña para acceder')
    )
    access_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Contraseña de acceso'),
        help_text=gettext_lazy('Contraseña requerida para acceder a la documentación pública')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Documentación Múltiple')
        verbose_name_plural = gettext_lazy('Documentaciones Múltiples')
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
        verbose_name=gettext_lazy('Documentación')
    )
    
    number = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Número'),
        help_text=gettext_lazy('Número de orden del documento')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Documento')
    )
    
    file = models.FileField(
        upload_to='multiple_documentation/',
        verbose_name=gettext_lazy('Archivo'),
        help_text=gettext_lazy('Archivo a compartir')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción del archivo')
    )
    
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Contador de Descargas'),
        help_text=gettext_lazy('Número de veces que se ha descargado este archivo')
    )
    
    expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Vencimiento'),
        help_text=gettext_lazy('Fecha de vencimiento del documento (opcional)')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Item de Documentación')
        verbose_name_plural = gettext_lazy('Items de Documentación')
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
    
    def is_expired(self):
        """Verifica si el documento está vencido"""
        if not self.expiration_date:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.expiration_date
    
    def days_until_expiration(self):
        """Calcula los días hasta el vencimiento"""
        if not self.expiration_date:
            return None
        from django.utils import timezone
        delta = self.expiration_date - timezone.now().date()
        return delta.days


class MultipleDocumentationStats(models.Model):
    """Modelo para estadísticas de documentación múltiple"""
    
    documentation = models.ForeignKey(
        MultipleDocumentation,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name=gettext_lazy('Documentación')
    )
    
    # Estadísticas de página
    page_views = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Visualizaciones de Página'),
        help_text=gettext_lazy('Número total de veces que se ha visitado la página pública')
    )
    
    unique_visitors = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Visitantes Únicos'),
        help_text=gettext_lazy('Número de visitantes únicos (basado en IP)')
    )
    
    # Estadísticas de descargas
    total_downloads = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Descargas Totales'),
        help_text=gettext_lazy('Número total de archivos descargados')
    )
    
    # Fechas de seguimiento
    first_view_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Primera Visualización')
    )
    
    last_view_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última Visualización')
    )
    
    last_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última Descarga')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Estadística de Documentación')
        verbose_name_plural = gettext_lazy('Estadísticas de Documentación')
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
        verbose_name=gettext_lazy('Archivo')
    )
    
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de Descargas')
    )
    
    unique_downloaders = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Descargadores Únicos'),
        help_text=gettext_lazy('Número de IPs únicas que han descargado este archivo')
    )
    
    first_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Primera Descarga')
    )
    
    last_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última Descarga')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Estadística de Archivo')
        verbose_name_plural = gettext_lazy('Estadísticas de Archivos')
    
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
        verbose_name=gettext_lazy('Documentación')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    referer = models.URLField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Referente')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha y Hora')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Visita a Documentación')
        verbose_name_plural = gettext_lazy('Visitas a Documentación')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ip_address} - {self.documentation.title} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class MultipleDocumentationDownload(models.Model):
    """Modelo para trackear descargas individuales"""
    
    item = models.ForeignKey(
        MultipleDocumentationItem,
        on_delete=models.CASCADE,
        related_name='downloads',
        verbose_name=gettext_lazy('Archivo')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    referer = models.URLField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Referente')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha y Hora')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Descarga de Archivo')
        verbose_name_plural = gettext_lazy('Descargas de Archivos')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ip_address} - {self.item.name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class TaskSchedule(models.Model):
    """Modelo para gestionar cronogramas de tareas con vista Gantt"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Cronograma')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='task_schedules',
        verbose_name=gettext_lazy('Empresa')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_schedules',
        verbose_name=gettext_lazy('Creado Por')
    )
    
    start_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Inicio')
    )
    
    end_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Fin')
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Público'),
        help_text=gettext_lazy('Si está activo, el cronograma será accesible públicamente')
    )
    
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token Público')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Cronograma de Tareas')
        verbose_name_plural = gettext_lazy('Cronogramas de Tareas')
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
        ('low', gettext_lazy('Baja')),
        ('medium', gettext_lazy('Media')),
        ('high', gettext_lazy('Alta')),
        ('critical', gettext_lazy('Crítica')),
    ]
    
    schedule = models.ForeignKey(
        TaskSchedule,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=gettext_lazy('Cronograma')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la Tarea')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    start_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Inicio')
    )
    
    end_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Fin')
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_tasks_assigned',
        verbose_name=gettext_lazy('Asignado A')
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Completada')
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Completada el')
    )
    
    progress_percentage = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Porcentaje de Progreso'),
        help_text=gettext_lazy('Progreso de 0 a 100')
    )
    
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_tasks',
        verbose_name=gettext_lazy('Dependencias')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Tarea del Cronograma')
        verbose_name_plural = gettext_lazy('Tareas del Cronograma')
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
        verbose_name=gettext_lazy('Tarea')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario')
    )
    
    comment = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Comentario de Tarea')
        verbose_name_plural = gettext_lazy('Comentarios de Tareas')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title}"


class TicketApproval(models.Model):
    """Modelo para aprobaciones de clientes en tickets públicos"""
    
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='client_approval',
        verbose_name=gettext_lazy('Ticket')
    )
    
    client_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Cliente')
    )
    
    client_email = models.EmailField(
        verbose_name=gettext_lazy('Correo del Cliente')
    )
    
    approved_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Aprobación')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas Adicionales'),
        help_text=gettext_lazy('Comentarios adicionales del cliente')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Dirección IP'),
        help_text=gettext_lazy('IP desde donde se realizó la aprobación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Aprobación de Cliente')
        verbose_name_plural = gettext_lazy('Aprobaciones de Clientes')
        ordering = ['-approved_at']
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - Aprobado por {self.client_name}"


class SatisfactionSurvey(models.Model):
    """Modelo para encuestas de satisfacción de clientes"""
    
    RATING_CHOICES = [
        (1, gettext_lazy('1 - Muy Insatisfecho')),
        (2, gettext_lazy('2 - Insatisfecho')),
        (3, gettext_lazy('3 - Neutral')),
        (4, gettext_lazy('4 - Satisfecho')),
        (5, gettext_lazy('5 - Muy Satisfecho')),
    ]
    
    RESOLUTION_QUALITY_CHOICES = [
        (1, gettext_lazy('1 - Muy Mala')),
        (2, gettext_lazy('2 - Mala')),
        (3, gettext_lazy('3 - Regular')),
        (4, gettext_lazy('4 - Buena')),
        (5, gettext_lazy('5 - Excelente')),
    ]
    
    RESPONSE_TIME_CHOICES = [
        (1, gettext_lazy('1 - Muy Lento')),
        (2, gettext_lazy('2 - Lento')),
        (3, gettext_lazy('3 - Aceptable')),
        (4, gettext_lazy('4 - Rápido')),
        (5, gettext_lazy('5 - Muy Rápido')),
    ]
    
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='satisfaction_survey',
        verbose_name=gettext_lazy('Ticket')
    )
    
    client_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Cliente')
    )
    
    client_email = models.EmailField(
        verbose_name=gettext_lazy('Correo del Cliente')
    )
    
    # Calificaciones
    overall_satisfaction = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name=gettext_lazy('Satisfacción General'),
        help_text=gettext_lazy("¿Qué tan satisfecho está con el servicio general?")
    )
    
    resolution_quality = models.IntegerField(
        choices=RESOLUTION_QUALITY_CHOICES,
        verbose_name=gettext_lazy('Calidad de la Solución'),
        help_text=gettext_lazy("¿Cómo califica la calidad de la solución proporcionada?")
    )
    
    response_time = models.IntegerField(
        choices=RESPONSE_TIME_CHOICES,
        verbose_name=gettext_lazy('Tiempo de Respuesta'),
        help_text=gettext_lazy("¿Cómo califica nuestro tiempo de respuesta?")
    )
    
    communication = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name=gettext_lazy('Calidad de la Comunicación'),
        help_text=gettext_lazy("¿Cómo califica la comunicación durante el proceso?")
    )
    
    # Comentarios
    what_went_well = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('¿Qué funcionó bien?'),
        help_text=gettext_lazy('Describa los aspectos positivos de nuestro servicio')
    )
    
    what_could_improve = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('¿Qué se podría mejorar?'),
        help_text=gettext_lazy('Sugerencias para mejorar nuestro servicio')
    )
    
    additional_comments = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Comentarios Adicionales'),
        help_text=gettext_lazy('Cualquier otro comentario que desee compartir')
    )
    
    # Recomendación
    would_recommend = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('¿Recomendaría nuestros servicios?'),
        help_text=gettext_lazy("¿Recomendaría nuestros servicios a otros?")
    )
    
    recommendation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Razón de recomendación'),
        help_text=gettext_lazy('¿Por qué sí o por qué no recomendaría nuestros servicios?')
    )
    
    # Metadatos
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Envío')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP'),
        help_text=gettext_lazy('IP desde donde se realizó la encuesta')
    )
    
    class Meta:
        verbose_name = gettext_lazy("Encuesta de Satisfacción")
        verbose_name_plural = gettext_lazy("Encuestas de Satisfacción")
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
        verbose_name=gettext_lazy('Símbolo'),
        help_text=gettext_lazy('Símbolo de la acción (ej: EUR/USD, AAPL, GOOGL)')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre'),
        help_text=gettext_lazy('Nombre completo de la acción o par de divisas')
    )
    
    current_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Precio Actual'),
        help_text=gettext_lazy('Se actualiza automáticamente desde APIs externas')
    )
    
    previous_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Precio Anterior'),
        help_text=gettext_lazy('Se actualiza automáticamente desde APIs externas')
    )
    
    currency = models.CharField(
        max_length=10,
        default='USD',
        verbose_name=gettext_lazy('Moneda'),
        help_text=gettext_lazy('Moneda en la que se cotiza (USD, EUR, etc.)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Si está activa se muestra en el ticker')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en el ticker (menor número = primera)')
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        ordering = ['order', 'symbol']
        verbose_name = gettext_lazy('Acción Financiera')
        verbose_name_plural = gettext_lazy('Acciones Financieras')
    
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
        verbose_name=gettext_lazy('Acción Financiera')
    )
    
    price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Precio')
    )
    
    recorded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Registro')
    )
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name = gettext_lazy('Historial de Precio')
        verbose_name_plural = gettext_lazy('Historiales de Precios')
        unique_together = ['financial_action', 'recorded_at']
    
    def __str__(self):
        return f"{self.financial_action.symbol} - {self.price} - {self.recorded_at}"


class ProductCategory(models.Model):
    """Categoría de producto"""
    name = models.CharField(max_length=100, verbose_name=gettext_lazy('Nombre'), unique=True)
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    color = models.CharField(
        max_length=7, default='#0d6efd', verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color en formato hexadecimal, ej: #ff5733')
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Categoría de Producto')
        verbose_name_plural = gettext_lazy('Categorías de Producto')

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Modelo para gestionar productos
    """
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Producto')
    )

    technical_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre Técnico'),
        help_text=gettext_lazy('Nombre técnico o código interno del producto')
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Precio'),
        help_text=gettext_lazy('Precio del producto')
    )
    
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del producto')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de Actualización')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está marcado, el producto estará disponible')
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Visible en catálogo público'),
        help_text=gettext_lazy('Si está marcado, este producto podrá verse en los catálogos públicos')
    )

    view_count = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Vistas del producto'))

    category = models.ForeignKey(
        'ProductCategory',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
        verbose_name=gettext_lazy('Categoría')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_products',
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Producto')
        verbose_name_plural = gettext_lazy('Productos')
    
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


class ProductVideo(models.Model):
    """URLs de video asociadas a un producto"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name=gettext_lazy('Producto')
    )
    title = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Título'))
    url = models.URLField(max_length=500, verbose_name=gettext_lazy('URL del Video'))
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Video de Producto')
        verbose_name_plural = gettext_lazy('Videos de Producto')

    def __str__(self):
        return f"{self.product.name} — {self.title or self.url}"

    def _get_youtube_id(self):
        import re
        url = self.url
        yt = re.match(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)', url)
        if yt:
            return yt.group(1)
        yt_short = re.match(r'(?:https?://)?youtu\.be/([\w-]+)', url)
        if yt_short:
            return yt_short.group(1)
        return None

    def get_embed_url(self):
        """Convierte URLs de YouTube/Vimeo a embed, el resto se deja igual"""
        import re
        url = self.url
        yt_id = self._get_youtube_id()
        if yt_id:
            return f"https://www.youtube.com/embed/{yt_id}"
        # Vimeo
        vimeo = re.match(r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)', url)
        if vimeo:
            return f"https://player.vimeo.com/video/{vimeo.group(1)}"
        return None

    def get_thumbnail_url(self):
        """Devuelve la URL de la miniatura del vídeo (YouTube: hqdefault)"""
        yt_id = self._get_youtube_id()
        if yt_id:
            return f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
        return None


class AppCatalog(models.Model):
    """Catálogo de Apps: agrupa productos en una colección presentable"""
    name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre del Catálogo'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    is_public = models.BooleanField(default=False, verbose_name=gettext_lazy('Público'), help_text=gettext_lazy('Si está marcado, aparecerá en la página pública de catálogos'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_catalogs',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    view_count = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Vistas del catálogo'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Catálogo de Apps')
        verbose_name_plural = gettext_lazy('Catálogos de Apps')

    def __str__(self):
        return self.name

    def get_total_products(self):
        return self.lines.count()


class AppCatalogLine(models.Model):
    """Línea de un catálogo: referencia a un producto existente con cantidad y nota opcional"""
    catalog = models.ForeignKey(
        AppCatalog,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=gettext_lazy('Catálogo')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='catalog_lines',
        verbose_name=gettext_lazy('Producto')
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=gettext_lazy('Cantidad'))
    notes = models.TextField(blank=True, verbose_name=gettext_lazy('Notas'))
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Línea de Catálogo')
        verbose_name_plural = gettext_lazy('Líneas de Catálogo')

    def __str__(self):
        return f"{self.catalog.name} — {self.product.name}"

    def get_subtotal(self):
        return self.product.price * self.quantity


class ClientProjectAccess(models.Model):
    """Modelo para configurar el acceso público a proyectos para imputación de horas por clientes"""
    
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='client_access',
        verbose_name=gettext_lazy('Proyecto')
    )
    public_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para acceso público al formulario de horas')
    )
    dashboard_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token Dashboard Público'),
        help_text=gettext_lazy('Token único para acceso público al dashboard de estadísticas')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está desactivado, el enlace público no funcionará')
    )
    max_entries_per_day = models.PositiveIntegerField(
        default=50,
        verbose_name=gettext_lazy('Máximo de entradas por día'),
        help_text=gettext_lazy('Límite de entradas de tiempo que se pueden crear por día')
    )
    requires_phone = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Requiere teléfono'),
        help_text=gettext_lazy('Si es obligatorio que el cliente proporcione su teléfono')
    )
    allowed_categories = models.JSONField(
        default=list,
        verbose_name=gettext_lazy('Categorías permitidas'),
        help_text=gettext_lazy('Lista de categorías que el cliente puede seleccionar')
    )
    instructions = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Instrucciones'),
        help_text=gettext_lazy('Instrucciones que verá el cliente en el formulario')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    class Meta:
        verbose_name = gettext_lazy('Acceso Público de Cliente')
        verbose_name_plural = gettext_lazy('Accesos Públicos de Clientes')
    
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
        ('capacitacion', gettext_lazy('Capacitación')),
        ('pruebas', gettext_lazy('Pruebas')),
        ('uso', gettext_lazy('Uso')),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='client_time_entries',
        verbose_name=gettext_lazy('Proyecto')
    )
    client_name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre del Cliente'),
        help_text=gettext_lazy('Nombre completo del cliente')
    )
    client_email = models.EmailField(
        verbose_name=gettext_lazy('Correo del Cliente'),
        help_text=gettext_lazy('Correo electrónico del cliente')
    )
    client_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Teléfono del Cliente'),
        help_text=gettext_lazy('Número de teléfono del cliente (opcional)')
    )
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=gettext_lazy('Horas'),
        help_text=gettext_lazy('Cantidad de horas a imputar (ej: 2.5)')
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=gettext_lazy('Categoría'),
        help_text=gettext_lazy('Categoría de las horas imputadas')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional del trabajo realizado')
    )
    entry_date = models.DateField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de las horas'),
        help_text=gettext_lazy('Fecha cuando se realizaron las horas de trabajo')
    )
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('IP del Cliente'),
        help_text=gettext_lazy('Dirección IP desde donde se registró la entrada')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent'),
        help_text=gettext_lazy('Información del navegador del cliente')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))
    
    class Meta:
        verbose_name = gettext_lazy('Entrada de Tiempo de Cliente')
        verbose_name_plural = gettext_lazy('Entradas de Tiempo de Clientes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client_name} ({self.client_email}) - {self.hours}h en {self.project.name} ({self.get_category_display()})"
    
    def get_formatted_hours(self):
        """Retorna las horas formateadas"""
        if self.hours == int(self.hours):
            return f"{int(self.hours)}h"
        return f"{self.hours}h"


class ShortUrl(models.Model):
    """Modelo para el acortador de URLs"""
    
    original_url = models.URLField(
        max_length=2000,
        verbose_name=gettext_lazy('URL Original'),
        help_text=gettext_lazy('La URL larga que se quiere acortar')
    )
    short_code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=gettext_lazy('Código Corto'),
        help_text=gettext_lazy('Código único para la URL corta')
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo opcional para la URL')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional de la URL')
    )
    clicks = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Clics'),
        help_text=gettext_lazy('Número de veces que se ha accedido a la URL corta')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Si la URL corta está activa o deshabilitada')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por'),
        help_text=gettext_lazy('Usuario que creó la URL corta')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración'),
        help_text=gettext_lazy('Fecha opcional cuando expira la URL corta')
    )
    is_sales_kpi = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('KPI de Ventas'),
        help_text=gettext_lazy('Marcar si esta URL es parte del seguimiento de KPIs de ventas')
    )
    
    class Meta:
        verbose_name = gettext_lazy('URL Corta')
        verbose_name_plural = gettext_lazy('URLs Cortas')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.short_code} → {self.original_url[:50]}..."
    
    def get_short_url(self, request=None):
        """Retorna la URL corta completa"""
        from django.conf import settings
        
        # Si se proporciona request, usar su dominio
        if request:
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
        else:
            # Usar configuración del settings
            domain = getattr(settings, 'SITE_DOMAIN', 'ticketproo.com')
            protocol = 'https' if not settings.DEBUG else 'http'
        
        return f"{protocol}://{domain}/s/{self.short_code}"
    
    def is_expired(self):
        """Verifica si la URL ha expirado"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def increment_clicks(self):
        """Incrementa el contador de clics"""
        self.clicks += 1
        self.save(update_fields=['clicks'])
    
    @staticmethod
    def generate_short_code():
        """Genera un código corto único"""
        import random
        import string
        
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(6))
            if not ShortUrl.objects.filter(short_code=code).exists():
                return code


class ShortUrlClick(models.Model):
    """Modelo para rastrear cada clic en una URL corta"""
    
    short_url = models.ForeignKey(
        ShortUrl,
        on_delete=models.CASCADE,
        related_name='click_records',
        verbose_name=gettext_lazy('URL Corta')
    )
    clicked_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha del clic'),
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('País'),
        db_index=True
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Ciudad')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    referer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Referer')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Clic de URL Corta')
        verbose_name_plural = gettext_lazy('Clics de URLs Cortas')
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['short_url', '-clicked_at']),
            models.Index(fields=['country', '-clicked_at']),
        ]
    
    def __str__(self):
        return f"Clic en {self.short_url.short_code} - {self.clicked_at}"


class ClientRequest(models.Model):
    """Modelo para solicitudes al cliente"""
    
    sequence = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=gettext_lazy('Secuencia'),
        help_text=gettext_lazy('Número de secuencia único de la solicitud')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción de lo que se solicita')
    )
    requested_to = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Solicitado a'),
        help_text=gettext_lazy('Nombre de la persona a quien se solicita')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_requests_created',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa asociada a la solicitud')
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', gettext_lazy('Pendiente')),
            ('in_progress', gettext_lazy('En Progreso')),
            ('completed', gettext_lazy('Completada')),
            ('cancelled', gettext_lazy('Cancelada'))
        ],
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    attachment = models.FileField(
        upload_to='client_request_attachments/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Archivo adjunto'),
        help_text=gettext_lazy('Documento o archivo de referencia para el cliente')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Solicitud al Cliente')
        verbose_name_plural = gettext_lazy('Solicitudes a Clientes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sequence']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['company', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sequence} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.sequence and self.company:
            # Generar secuencia automática por empresa: REQ-{company_id}-{número}
            last_request = ClientRequest.objects.filter(company=self.company).order_by('-id').first()
            if last_request and last_request.sequence:
                try:
                    # Extraer el último número de la secuencia REQ-XX-YYYY
                    parts = last_request.sequence.split('-')
                    last_num = int(parts[-1])
                    self.sequence = f"REQ-{self.company.id:02d}-{last_num + 1:04d}"
                except:
                    self.sequence = f"REQ-{self.company.id:02d}-0001"
            else:
                self.sequence = f"REQ-{self.company.id:02d}-0001"
        elif not self.sequence:
            # Fallback si no hay empresa
            self.sequence = f"REQ-00-0001"
        super().save(*args, **kwargs)


class ClientRequestResponse(models.Model):
    """Modelo para respuestas del cliente a las solicitudes"""
    
    request = models.OneToOneField(
        ClientRequest,
        on_delete=models.CASCADE,
        related_name='response',
        verbose_name=gettext_lazy('Solicitud')
    )
    response_text = models.TextField(
        verbose_name=gettext_lazy('Respuesta'),
        help_text=gettext_lazy('Texto de la respuesta del cliente')
    )
    attachment = models.FileField(
        upload_to='client_request_attachments/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Adjunto')
    )
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Respondido por')
    )
    responded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de respuesta')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Respuesta de Solicitud')
        verbose_name_plural = gettext_lazy('Respuestas de Solicitudes')
        ordering = ['-responded_at']
    
    def __str__(self):
        return f"Respuesta a {self.request.sequence}"


class ClientRequestTemplate(models.Model):
    """Modelo para plantillas de solicitudes al cliente"""
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Plantilla'),
        help_text=gettext_lazy('Nombre descriptivo para identificar este conjunto de solicitudes')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        blank=True,
        help_text=gettext_lazy('Descripción de para qué sirve esta plantilla')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_request_templates',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Si está activa, se puede usar para crear solicitudes')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Plantilla de Solicitud')
        verbose_name_plural = gettext_lazy('Plantillas de Solicitudes')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ClientRequestTemplateItem(models.Model):
    """Modelo para ítems individuales dentro de una plantilla"""
    
    template = models.ForeignKey(
        ClientRequestTemplate,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=gettext_lazy('Plantilla')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción')
    )
    requested_to = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Solicitado a'),
        help_text=gettext_lazy('Nombre de la persona a quien se solicita')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en la lista')
    )
    attachment = models.FileField(
        upload_to='client_request_template_attachments/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Archivo adjunto'),
        help_text=gettext_lazy('Documento de referencia para esta solicitud')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Item de Plantilla')
        verbose_name_plural = gettext_lazy('Items de Plantilla')
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.template.name} - {self.title}"


class ProductSet(models.Model):
    """Modelo para conjuntos de productos"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre del conjunto de productos')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del conjunto de productos')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Público'),
        help_text=gettext_lazy('Si está marcado, los clientes podrán ver este conjunto')
    )
    public_token = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por'),
        help_text=gettext_lazy('Usuario que creó el conjunto')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Campos de estadísticas
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Vistas'),
        help_text=gettext_lazy('Número de veces que se ha visto el conjunto público')
    )
    last_viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última vista'),
        help_text=gettext_lazy('Fecha y hora de la última vista pública')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Conjunto de Productos')
        verbose_name_plural = gettext_lazy('Conjuntos de Productos')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generar token público si no existe
        if not self.public_token:
            import uuid
            self.public_token = str(uuid.uuid4()).replace('-', '')[:16]
        super().save(*args, **kwargs)
    
    def get_public_url(self):
        """Retorna la URL pública del conjunto"""
        from django.urls import reverse
        return reverse('product_set_public', kwargs={'token': self.public_token})
    
    def increment_views(self):
        """Incrementa el contador de vistas y actualiza la fecha de última vista"""
        from django.utils import timezone
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])
    
    @property
    def product_count(self):
        """Retorna el número de productos en el conjunto"""
        return self.products.count()


class ProductItem(models.Model):
    """Modelo para productos individuales dentro de un conjunto"""
    
    product_set = models.ForeignKey(
        ProductSet,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=gettext_lazy('Conjunto de Productos')
    )
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Producto'),
        help_text=gettext_lazy('Nombre descriptivo del producto')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del producto')
    )
    video_link = models.URLField(
        blank=True,
        verbose_name=gettext_lazy('Link del Video'),
        help_text=gettext_lazy('URL del video demostrativo (opcional)')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en la lista')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=gettext_lazy('Precio'),
        help_text=gettext_lazy('Precio del producto individual')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Producto')
        verbose_name_plural = gettext_lazy('Productos')
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.product_set.title} - {self.name}"
    
    @property
    def product_code(self):
        """Genera el código único del producto"""
        return f"PRO{str(self.id).zfill(3)}"
    
    def get_formatted_price(self):
        """Retorna el precio formateado con la moneda del sistema"""
        if self.price > 0:
            try:
                config = SystemConfiguration.objects.get(pk=1)
                return config.format_currency(self.price)
            except SystemConfiguration.DoesNotExist:
                return f"€{self.price:,.2f}"  # Fallback
        return None


class Precotizador(models.Model):
    """Modelo para el sistema de precotizador con IA"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Precotizador'),
        help_text=gettext_lazy('Nombre descriptivo del precotizador')
    )
    client_description = models.TextField(
        verbose_name=gettext_lazy('Descripción del Cliente'),
        help_text=gettext_lazy('Descripción detallada del tipo de cliente y sus necesidades')
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Precio por Hora'),
        help_text=gettext_lazy('Tu tarifa por hora para este tipo de trabajo')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por'),
        help_text=gettext_lazy('Usuario que creó el precotizador')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Campos para enlace público de solicitud
    public_request_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name=gettext_lazy('Token de Solicitud Pública'),
        help_text=gettext_lazy('Token único para el enlace público donde clientes pueden solicitar cotizaciones')
    )
    allow_public_requests = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Permitir Solicitudes Públicas'),
        help_text=gettext_lazy('Permite que los clientes soliciten cotizaciones a través de un enlace público')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Precotizador')
        verbose_name_plural = gettext_lazy('Precotizadores')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_formatted_hourly_rate(self):
        """Retorna la tarifa por hora formateada con la moneda del sistema"""
        try:
            config = SystemConfiguration.objects.get(pk=1)
            return config.format_currency(self.hourly_rate)
        except SystemConfiguration.DoesNotExist:
            return f"€{self.hourly_rate:,.2f}"  # Fallback
    
    def generate_public_request_token(self):
        """Genera un token único para solicitudes públicas"""
        import uuid
        if not self.public_request_token:
            self.public_request_token = str(uuid.uuid4())
            self.save(update_fields=['public_request_token'])
        return self.public_request_token
    
    def get_public_request_url(self):
        """Retorna la URL pública para solicitar cotizaciones"""
        from django.urls import reverse
        if self.public_request_token:
            return reverse('precotizador_public_request', kwargs={'token': self.public_request_token})
        return None
    
    def toggle_public_requests(self):
        """Activa/desactiva las solicitudes públicas"""
        self.allow_public_requests = not self.allow_public_requests
        if self.allow_public_requests and not self.public_request_token:
            self.generate_public_request_token()
        self.save(update_fields=['allow_public_requests', 'public_request_token'])
        return self.allow_public_requests


class PrecotizadorExample(models.Model):
    """Modelo para los ejemplos de casos del precotizador"""
    
    precotizador = models.ForeignKey(
        Precotizador,
        on_delete=models.CASCADE,
        related_name='examples',
        verbose_name=gettext_lazy('Precotizador')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción del Caso'),
        help_text=gettext_lazy('Descripción detallada del trabajo a realizar')
    )
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=gettext_lazy('Horas Estimadas'),
        help_text=gettext_lazy('Número de horas estimadas para completar el trabajo')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en la lista')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Ejemplo de Caso')
        verbose_name_plural = gettext_lazy('Ejemplos de Casos')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.precotizador.title} - Caso {self.order + 1}"
    
    def get_estimated_cost(self):
        """Calcula el costo estimado basado en las horas y tarifa del precotizador"""
        return self.estimated_hours * self.precotizador.hourly_rate
    
    def get_formatted_cost(self):
        """Retorna el costo estimado formateado con la moneda del sistema"""
        cost = self.get_estimated_cost()
        try:
            config = SystemConfiguration.objects.get(pk=1)
            return config.format_currency(cost)
        except SystemConfiguration.DoesNotExist:
            return f"€{cost:,.2f}"  # Fallback


class PrecotizadorQuote(models.Model):
    """Modelo para las cotizaciones generadas por IA"""
    
    precotizador = models.ForeignKey(
        Precotizador,
        on_delete=models.CASCADE,
        related_name='quotes',
        verbose_name=gettext_lazy('Precotizador')
    )
    client_request = models.TextField(
        verbose_name=gettext_lazy('Solicitud del Cliente'),
        help_text=gettext_lazy('Descripción del trabajo solicitado por el cliente')
    )
    ai_estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=gettext_lazy('Horas Estimadas por IA'),
        help_text=gettext_lazy('Número de horas estimadas por la IA')
    )
    ai_detailed_description = models.TextField(
        verbose_name=gettext_lazy('Descripción Detallada por IA'),
        help_text=gettext_lazy('Descripción detallada del trabajo generada por la IA')
    )
    ai_reasoning = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Razonamiento de la IA'),
        help_text=gettext_lazy('Explicación del razonamiento de la IA para la estimación')
    )
    ai_full_response = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Respuesta Completa de la IA'),
        help_text=gettext_lazy('Respuesta completa de la IA en formato texto plano')
    )
    
    # Campos para compartir públicamente
    public_share_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token de Compartir Público'),
        help_text=gettext_lazy('Token único para compartir la cotización públicamente')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Es Público'),
        help_text=gettext_lazy('Si la cotización puede ser vista públicamente')
    )
    
    # Estado de la cotización
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('accepted', gettext_lazy('Aceptada por el Cliente')),
        ('rejected', gettext_lazy('Rechazada por el Cliente')),
        ('expired', gettext_lazy('Expirada')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado'),
        help_text=gettext_lazy('Estado actual de la cotización')
    )
    
    # Información del cliente
    client_response_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de Respuesta del Cliente'),
        help_text=gettext_lazy('Fecha en que el cliente respondió')
    )
    client_comments = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentarios del Cliente'),
        help_text=gettext_lazy('Comentarios adicionales del cliente')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Cotización IA')
        verbose_name_plural = gettext_lazy('Cotizaciones IA')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cotización {self.id} - {self.precotizador.title}"
    
    def get_formatted_cost(self):
        """Retorna el costo formateado con la moneda del sistema"""
        from decimal import Decimal
        # Convertir a Decimal para evitar errores de tipos
        hours = Decimal(str(self.ai_estimated_hours))
        total_cost = hours * self.precotizador.hourly_rate
        try:
            config = SystemConfiguration.objects.get(pk=1)
            return config.format_currency(total_cost)
        except SystemConfiguration.DoesNotExist:
            return f"€{total_cost:,.2f}"  # Fallback
    
    def generate_public_token(self):
        """Genera un token único para compartir públicamente"""
        import uuid
        if not self.public_share_token:
            self.public_share_token = str(uuid.uuid4())
            self.save(update_fields=['public_share_token'])
        return self.public_share_token
    
    def get_public_url(self):
        """Retorna la URL pública para compartir"""
        from django.urls import reverse
        if self.public_share_token:
            return reverse('precotizador_quote_public', kwargs={'token': self.public_share_token})
        return None
    
    def can_be_responded(self):
        """Verifica si la cotización puede ser respondida por el cliente"""
        return self.status == 'pending' and self.is_public
    
    def accept(self, client_comments=''):
        """Acepta la cotización"""
        if self.status != 'pending':
            raise ValueError(f"No se puede aceptar una cotización que ya está {self.get_status_display().lower()}")
        
        self.status = 'accepted'
        self.client_comments = client_comments
        self.client_response_date = timezone.now()
        self.save(update_fields=['status', 'client_comments', 'client_response_date'])
    
    def reject(self, client_comments=''):
        """Rechaza la cotización"""
        if self.status != 'pending':
            raise ValueError(f"No se puede rechazar una cotización que ya está {self.get_status_display().lower()}")
        
        self.status = 'rejected'
        self.client_comments = client_comments
        self.client_response_date = timezone.now()
        self.save(update_fields=['status', 'client_comments', 'client_response_date'])
    
    def get_status_color(self):
        """Retorna el color Bootstrap para el estado"""
        colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'expired': 'secondary',
        }
        return colors.get(self.status, 'primary')
    
    def get_response_time_info(self):
        """Retorna información sobre el tiempo de respuesta del cliente"""
        if not self.client_response_date:
            return None
        
        from django.utils import timezone
        time_diff = self.client_response_date - self.created_at
        
        if time_diff.days > 0:
            return f"Respondió en {time_diff.days} día{'s' if time_diff.days > 1 else ''}"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"Respondió en {hours} hora{'s' if hours > 1 else ''}"
        else:
            minutes = time_diff.seconds // 60
            return f"Respondió en {minutes} minuto{'s' if minutes > 1 else ''}"
    
    def is_recently_responded(self):
        """Verifica si el cliente respondió recientemente (últimas 24 horas)"""
        if not self.client_response_date:
            return False
        
        from django.utils import timezone
        from datetime import timedelta
        
        return timezone.now() - self.client_response_date <= timedelta(hours=24)
    
    def get_estimated_cost(self):
        """Calcula el costo estimado basado en las horas y tarifa del precotizador"""
        return self.ai_estimated_hours * self.precotizador.hourly_rate
    
    def get_formatted_cost(self):
        """Retorna el costo estimado formateado con la moneda del sistema"""
        cost = self.get_estimated_cost()
        try:
            config = SystemConfiguration.objects.get(pk=1)
            return config.format_currency(cost)
        except SystemConfiguration.DoesNotExist:
            return f"€{cost:,.2f}"  # Fallback


class CompanyDocumentation(models.Model):
    """Documentación múltiple para empresas con URLs y contraseñas"""
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy("Título"))
    description = models.TextField(blank=True, verbose_name=gettext_lazy("Descripción"))
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name='documentations',
        verbose_name=gettext_lazy("Empresa")
    )
    is_public = models.BooleanField(default=False, verbose_name=gettext_lazy("Es público"))
    public_token = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        verbose_name=gettext_lazy("Token público")
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Creado por")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy("Fecha de actualización"))
    
    class Meta:
        verbose_name = gettext_lazy("Documentación de Empresa")
        verbose_name_plural = gettext_lazy("Documentaciones de Empresas")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('company_documentation_detail', kwargs={'pk': self.pk})
    
    def get_public_url(self):
        from django.urls import reverse
        return reverse('company_documentation_public', kwargs={'token': self.public_token})


class CompanyDocumentationURL(models.Model):
    """URLs asociadas a documentaciones de empresas"""
    
    documentation = models.ForeignKey(
        CompanyDocumentation,
        on_delete=models.CASCADE,
        related_name='urls',
        verbose_name=gettext_lazy("Documentación")
    )
    title = models.CharField(max_length=200, verbose_name=gettext_lazy("Título del enlace"))
    url = models.URLField(verbose_name=gettext_lazy("URL"))
    description = models.TextField(blank=True, verbose_name=gettext_lazy("Descripción"))
    username = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy("Usuario"))
    password = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy("Contraseña"))
    notes = models.TextField(blank=True, verbose_name=gettext_lazy("Notas adicionales"))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy("Está activo"))
    order = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy("Orden"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de creación"))
    
    class Meta:
        verbose_name = gettext_lazy("URL de Documentación")
        verbose_name_plural = gettext_lazy("URLs de Documentación")
        ordering = ['order', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.documentation.title}"
    
    def has_credentials(self):
        """Verifica si tiene credenciales (usuario y/o contraseña)"""
        return bool(self.username or self.password)


class TermsOfUse(models.Model):
    """Condiciones de uso de la aplicación"""
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy("Título"))
    content = models.TextField(verbose_name=gettext_lazy("Contenido"))
    effective_date = models.DateField(verbose_name=gettext_lazy("Fecha de vigencia"))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy("Está activo"))
    version = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy("Versión"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='terms_created',
        verbose_name=gettext_lazy("Creado por")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy("Última actualización"))
    
    class Meta:
        verbose_name = gettext_lazy("Condición de Uso")
        verbose_name_plural = gettext_lazy("Condiciones de Uso")
        ordering = ['-effective_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.effective_date}"
    
    def save(self, *args, **kwargs):
        # Si se marca como activo, desactivar las demás
        if self.is_active:
            TermsOfUse.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ContactGenerator(models.Model):
    """Generador de contactos con URL pública"""
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy("Título"))
    description = models.TextField(blank=True, verbose_name=gettext_lazy("Descripción"))
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name='contact_generators',
        verbose_name=gettext_lazy("Empresa")
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy("Está activo"))
    public_token = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        verbose_name=gettext_lazy("Token público")
    )
    
    # Campos personalizables del formulario
    collect_phone = models.BooleanField(default=False, verbose_name=gettext_lazy("Recopilar teléfono"))
    collect_company = models.BooleanField(default=True, verbose_name=gettext_lazy("Recopilar empresa"))
    collect_position = models.BooleanField(default=True, verbose_name=gettext_lazy("Recopilar cargo"))
    collect_notes = models.BooleanField(default=False, verbose_name=gettext_lazy("Recopilar notas"))
    
    # Mensajes personalizables
    welcome_message = models.TextField(
        default="¡Gracias por tu interés! Por favor, completa la siguiente información para que podamos contactarte.",
        verbose_name=gettext_lazy("Mensaje de bienvenida")
    )
    success_message = models.TextField(
        default="¡Gracias! Hemos recibido tu información y nos pondremos en contacto contigo pronto.",
        verbose_name=gettext_lazy("Mensaje de éxito")
    )
    
    # Configuración de diseño
    background_color = models.CharField(
        max_length=7, 
        default="#007bff", 
        verbose_name=gettext_lazy("Color de fondo"),
        help_text=gettext_lazy("Color en formato hexadecimal (ej: #007bff)")
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Creado por")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy("Fecha de actualización"))
    
    class Meta:
        verbose_name = gettext_lazy("Generador de Contactos")
        verbose_name_plural = gettext_lazy("Generadores de Contactos")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('contact_generator_detail', kwargs={'pk': self.pk})
    
    def get_public_url(self):
        from django.urls import reverse
        return reverse('contact_generator_public', kwargs={'token': self.public_token})
    
    def get_contacts_count(self):
        """Retorna el número de contactos generados por este generador"""
        return Contact.objects.filter(
            source=f"Generador: {self.title}",
            created_by=self.created_by
        ).count()


class CompanyRequestGenerator(models.Model):
    """Generador de formularios de Solicitudes de Empresas"""

    title = models.CharField(max_length=200, verbose_name=gettext_lazy("Título"))
    description = models.TextField(blank=True, verbose_name=gettext_lazy("Descripción"))
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_request_generators',
        verbose_name=gettext_lazy("Empresa")
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy("Está activo"))
    public_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy("Token público")
    )

    # Secuencia y prefijo
    sequence_prefix = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Prefijo de Secuencia'),
        help_text=gettext_lazy('Prefijo que se antepone al número de solicitud (ej: SR-)')
    )
    next_sequence = models.PositiveIntegerField(
        default=1,
        verbose_name=gettext_lazy('Siguiente secuencia'),
        help_text=gettext_lazy('Número secuencial que se incrementa por cada solicitud')
    )

    # Campos personalizables del formulario
    collect_date = models.BooleanField(default=True, verbose_name=gettext_lazy("Incluir fecha"))
    collect_text = models.BooleanField(default=True, verbose_name=gettext_lazy("Incluir texto de solicitud"))
    collect_url = models.BooleanField(default=False, verbose_name=gettext_lazy("Incluir URL relacionada"))

    # Mensajes personalizables
    welcome_message = models.TextField(
        default="Por favor, envía tu solicitud y nuestro equipo la revisará.",
        verbose_name=gettext_lazy("Mensaje de bienvenida")
    )
    success_message = models.TextField(
        default="Solicitud recibida. Te contactaremos pronto.",
        verbose_name=gettext_lazy("Mensaje de éxito")
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Creado por")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy("Fecha de actualización"))

    class Meta:
        verbose_name = gettext_lazy("Generador de Solicitudes Empresa")
        verbose_name_plural = gettext_lazy("Generadores de Solicitudes Empresas")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('company_request_generator_detail', kwargs={'pk': self.pk})

    def get_public_url(self):
        from django.urls import reverse
        return reverse('company_request_public', kwargs={'token': self.public_token})

    def generate_sequence(self):
        """Retorna la secuencia completa y la incrementa de forma atómica"""
        from django.db import transaction
        with transaction.atomic():
            seq = self.next_sequence
            full = f"{self.sequence_prefix}{seq:04d}" if self.sequence_prefix else f"{seq:04d}"
            self.next_sequence = seq + 1
            self.save(update_fields=['next_sequence'])
            return full

    def get_requests_count(self):
        return CompanyRequest.objects.filter(generator=self).count()

    def get_recent_requests(self, limit=10):
        return CompanyRequest.objects.filter(generator=self).order_by('-created_at')[:limit]


class CompanyRequest(models.Model):
    """Registro de una solicitud enviada mediante un generador"""

    STATUS_CHOICES = [
        ('new', gettext_lazy('Nueva')),
        ('review', gettext_lazy('En revisión')),
        ('accepted', gettext_lazy('Aceptada')),
        ('executed', gettext_lazy('Ejecutada')),
        ('rejected', gettext_lazy('Rechazada')),
        ('closed', gettext_lazy('Cerrada')),
    ]

    sequence = models.CharField(max_length=50, verbose_name=gettext_lazy('Número de solicitud'), unique=True)
    generator = models.ForeignKey(
        CompanyRequestGenerator,
        on_delete=models.CASCADE,
        related_name='requests',
        verbose_name=gettext_lazy('Generador')
    )
    request_date = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de solicitud'))
    text = models.TextField(blank=True, verbose_name=gettext_lazy('Texto de la solicitud'))
    url = models.URLField(blank=True, verbose_name=gettext_lazy('URL relacionada'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=gettext_lazy('Estado'))
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Fecha de ejecución'))
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_company_requests',
        verbose_name=gettext_lazy('Ejecutado por')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Solicitud de Empresa')
        verbose_name_plural = gettext_lazy('Solicitudes de Empresas')

    def __str__(self):
        return f"{self.sequence} - {self.generator.title}"

    def get_identifier(self):
        return self.sequence


class CompanyRequestComment(models.Model):
    """Comentarios internos para una CompanyRequest"""

    request = models.ForeignKey(
        CompanyRequest,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Solicitud')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=gettext_lazy('Usuario'))
    content = models.TextField(verbose_name=gettext_lazy('Comentario'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Comentario de Solicitud')
        verbose_name_plural = gettext_lazy('Comentarios de Solicitudes')

    def __str__(self):
        return f"Comentario de {self.user.username} en {self.request.sequence}"


# ============= SISTEMA DE FORMULARIOS =============

class Form(models.Model):
    """Formulario con múltiples preguntas"""
    
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del formulario'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    theme = models.CharField(
        max_length=20,
        choices=[
            ('blue', gettext_lazy('Azul Clásico')),
            ('green', gettext_lazy('Verde Moderno')),
            ('sunset', gettext_lazy('Sunset')),
            ('ocean', gettext_lazy('Océano')),
            ('purple', gettext_lazy('Púrpura')),
            ('pink', gettext_lazy('Rosa')),
            ('minimal', gettext_lazy('Minimal')),
        ],
        default='blue',
        verbose_name=gettext_lazy('Tema visual')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='forms',
        verbose_name=gettext_lazy('Empresa')
    )
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    public_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forms_created',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Formulario')
        verbose_name_plural = gettext_lazy('Formularios')

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def get_public_url(self):
        """Retorna la URL pública del formulario"""
        return f"/form/{self.public_token}/"

    def get_total_responses(self):
        """Retorna el total de respuestas del formulario"""
        return self.responses.count()

    def get_average_score(self):
        """Retorna el promedio de puntuación del formulario"""
        responses = self.responses.all()
        if not responses:
            return 0
        
        total_score = sum(response.total_score for response in responses)
        return round(total_score / len(responses), 2)


class FormQuestion(models.Model):
    """Pregunta de un formulario"""
    
    QUESTION_TYPES = [
        ('number', 'Cantidad (Número)'),
        ('multiple_choice', 'Selección múltiple'),
        ('text', 'Texto libre'),
    ]
    
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=gettext_lazy('Formulario')
    )
    question_text = models.TextField(verbose_name=gettext_lazy('Texto de la pregunta'))
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        verbose_name=gettext_lazy('Tipo de pregunta')
    )
    is_required = models.BooleanField(default=True, verbose_name=gettext_lazy('Obligatoria'))
    order = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Pregunta')
        verbose_name_plural = gettext_lazy('Preguntas')

    def __str__(self):
        return f"{self.form.title} - {self.question_text[:50]}..."


class FormQuestionOption(models.Model):
    """Opciones para preguntas de selección múltiple"""
    
    question = models.ForeignKey(
        FormQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=gettext_lazy('Pregunta')
    )
    option_text = models.CharField(max_length=200, verbose_name=gettext_lazy('Texto de la opción'))
    score = models.IntegerField(default=0, verbose_name=gettext_lazy('Puntuación'))
    order = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))

    class Meta:
        ordering = ['order']
        verbose_name = gettext_lazy('Opción de Pregunta')
        verbose_name_plural = gettext_lazy('Opciones de Preguntas')

    def __str__(self):
        return f"{self.option_text} ({self.score} pts)"


class FormResponse(models.Model):
    """Respuesta completa a un formulario"""
    
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=gettext_lazy('Formulario')
    )
    respondent_name = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Nombre del encuestado'))
    respondent_email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email del encuestado'))
    total_score = models.IntegerField(default=0, verbose_name=gettext_lazy('Puntuación total'))
    response_date = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de respuesta'))

    class Meta:
        ordering = ['-response_date']
        verbose_name = gettext_lazy('Respuesta al Formulario')
        verbose_name_plural = gettext_lazy('Respuestas a Formularios')

    def __str__(self):
        return f"Respuesta de {self.respondent_name or 'Anónimo'} - {self.form.title}"

    def calculate_total_score(self):
        """Calcula y actualiza la puntuación total"""
        total = 0
        for answer in self.answers.all():
            if answer.selected_option:
                total += answer.selected_option.score
        self.total_score = total
        self.save()
        return total


class FormAnswer(models.Model):
    """Respuesta individual a una pregunta"""
    
    response = models.ForeignKey(
        FormResponse,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=gettext_lazy('Respuesta al formulario')
    )
    question = models.ForeignKey(
        FormQuestion,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Pregunta')
    )
    # Para preguntas de texto
    text_answer = models.TextField(blank=True, verbose_name=gettext_lazy('Respuesta de texto'))
    # Para preguntas de número
    number_answer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Respuesta numérica')
    )
    # Para preguntas de selección múltiple
    selected_option = models.ForeignKey(
        FormQuestionOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Opción seleccionada')
    )

    class Meta:
        unique_together = ('response', 'question')
        verbose_name = gettext_lazy('Respuesta Individual')
        verbose_name_plural = gettext_lazy('Respuestas Individuales')

    def __str__(self):
        return f"Respuesta a: {self.question.question_text[:30]}..."

    def get_answer_display(self):
        """Retorna la respuesta en formato legible"""
        if self.question.question_type == 'text':
            return self.text_answer
        elif self.question.question_type == 'number':
            return str(self.number_answer) if self.number_answer is not None else ''
        elif self.question.question_type == 'multiple_choice':
            return self.selected_option.option_text if self.selected_option else ''
        return ''


class FormAIAnalysis(models.Model):
    """Análisis de IA para formularios"""
    
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name='ai_analyses',
        verbose_name=gettext_lazy('Formulario')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de análisis')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Analizado por')
    )
    
    # Campos del análisis
    overall_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name=gettext_lazy('Puntuación general')
    )
    problems = models.JSONField(
        default=list,
        verbose_name=gettext_lazy('Problemas identificados'),
        help_text=gettext_lazy('Lista de problemas encontrados en formato JSON')
    )
    improvements = models.JSONField(
        default=list,
        verbose_name=gettext_lazy('Mejoras sugeridas'),
        help_text=gettext_lazy('Lista de mejoras sugeridas en formato JSON')
    )
    strengths = models.JSONField(
        default=list,
        verbose_name=gettext_lazy('Fortalezas'),
        help_text=gettext_lazy('Lista de fortalezas identificadas')
    )
    main_recommendation = models.TextField(
        verbose_name=gettext_lazy('Recomendación principal')
    )
    
    # Metadatos del análisis
    total_responses = models.IntegerField(
        verbose_name=gettext_lazy('Total de respuestas analizadas')
    )
    analysis_version = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name=gettext_lazy('Versión del análisis')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Análisis de IA')
        verbose_name_plural = gettext_lazy('Análisis de IA')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Análisis de {self.form.title} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    def get_problems_count(self):
        """Retorna el número de problemas identificados"""
        return len(self.problems) if self.problems else 0
    
    def get_improvements_count(self):
        """Retorna el número de mejoras sugeridas"""
        return len(self.improvements) if self.improvements else 0
    
    def get_score_color(self):
        """Retorna el color basado en la puntuación"""
        if self.overall_score >= 8:
            return 'success'
        elif self.overall_score >= 6:
            return 'warning'
        else:
            return 'danger'


# Modelo de Alcance
class Alcance(models.Model):
    titulo = models.CharField(max_length=200, verbose_name=gettext_lazy('Título'))
    categoria = models.CharField(max_length=100, verbose_name=gettext_lazy('Categoría'))
    descripcion = models.TextField(verbose_name=gettext_lazy('Descripción'))
    url = models.URLField(max_length=500, blank=True, null=True, verbose_name=gettext_lazy('URL del artículo relacionado'))
    publico = models.BooleanField(default=True, verbose_name=gettext_lazy('¿Es público?'))
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Creado por')
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))

    class Meta:
        verbose_name = gettext_lazy('Alcance')
        verbose_name_plural = gettext_lazy('Alcances')
        ordering = ['-creado_en']

    def __str__(self):
        return self.titulo


# ==================== MODELO DE CONTROL DE LICENCIAS ====================

class License(models.Model):
    """Modelo para gestionar licencias de productos"""
    
    STATUS_CHOICES = [
        ('active', gettext_lazy('Activa')),
        ('expired', gettext_lazy('Expirada')),
        ('suspended', gettext_lazy('Suspendida')),
        ('revoked', gettext_lazy('Revocada')),
    ]
    
    license_key = models.CharField(
        max_length=12,
        unique=True,
        verbose_name=gettext_lazy('Clave de Licencia'),
        help_text=gettext_lazy('Clave alfanumérica de 12 caracteres en mayúsculas')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Empresa'),
        related_name='licenses'
    )
    product = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Producto')
    )
    start_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Inicio')
    )
    end_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Vencimiento')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=gettext_lazy('Estado')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre la licencia')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Creado por'),
        related_name='created_licenses'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # UUID para acceso público
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('UUID Público')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Licencia')
        verbose_name_plural = gettext_lazy('Licencias')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.license_key} - {self.product} ({self.company.name})"
    
    def save(self, *args, **kwargs):
        # Generar clave automáticamente si no existe
        if not self.license_key:
            self.license_key = self.generate_license_key()
        # Asegurar que la clave esté en mayúsculas
        self.license_key = self.license_key.upper()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_license_key():
        """Genera una clave de licencia de 12 caracteres alfanuméricos"""
        import string
        import secrets
        alphabet = string.ascii_uppercase + string.digits
        while True:
            key = ''.join(secrets.choice(alphabet) for _ in range(12))
            # Verificar que no exista ya
            if not License.objects.filter(license_key=key).exists():
                return key
    
    def is_active(self):
        """Verifica si la licencia está activa y no ha expirado"""
        from django.utils import timezone
        today = timezone.now().date()
        return (
            self.status == 'active' and 
            self.start_date <= today <= self.end_date
        )
    
    def is_expired(self):
        """Verifica si la licencia ha expirado"""
        from django.utils import timezone
        today = timezone.now().date()
        return today > self.end_date
    
    def days_until_expiry(self):
        """Calcula los días restantes hasta el vencimiento"""
        from django.utils import timezone
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days
    
    def get_status_display_color(self):
        """Retorna el color para mostrar el estado"""
        if self.is_expired():
            return 'danger'
        elif self.status == 'active':
            days_left = self.days_until_expiry()
            if days_left <= 30:
                return 'warning'
            return 'success'
        elif self.status == 'suspended':
            return 'warning'
        else:
            return 'danger'
    
    def get_qr_data(self):
        """Retorna los datos para el código QR"""
        from django.urls import reverse
        from django.conf import settings
        
        # Usar localhost en desarrollo o el dominio configurado en producción
        if settings.DEBUG:
            domain = "http://localhost:8000"
        else:
            # En producción, usar el primer host permitido o localhost como fallback
            domain = "http://localhost:8000"
            if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
                for host in settings.ALLOWED_HOSTS:
                    if host != '*' and host != '' and host != 'localhost':
                        domain = f"https://{host}"
                        break
            
        public_url = f"{domain}{reverse('license_public', kwargs={'uuid': self.public_uuid})}"
        return public_url


# ==================== MODELOS DE WHATSAPP ====================

class WhatsAppConnection(models.Model):
    """Modelo para gestionar la conexión de WhatsApp"""
    STATUS_CHOICES = [
        ('disconnected', gettext_lazy('Desconectado')),
        ('connecting', gettext_lazy('Conectando')),
        ('connected', gettext_lazy('Conectado')),
        ('qr_pending', gettext_lazy('QR Pendiente')),
        ('error', gettext_lazy('Error')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='disconnected',
        verbose_name=gettext_lazy('Estado')
    )
    qr_code = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Código QR')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Número de teléfono')
    )
    session_data = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Datos de sesión')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    last_connected = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Última conexión')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )

    class Meta:
        verbose_name = gettext_lazy('Conexión WhatsApp')
        verbose_name_plural = gettext_lazy('Conexiones WhatsApp')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


class WhatsAppKeyword(models.Model):
    """Modelo para palabras clave y respuestas automáticas"""
    connection = models.ForeignKey(
        WhatsAppConnection,
        on_delete=models.CASCADE,
        related_name='keywords',
        verbose_name=gettext_lazy('Conexión')
    )
    keyword = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Palabra clave')
    )
    response = models.TextField(
        verbose_name=gettext_lazy('Respuesta')
    )
    is_exact_match = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Coincidencia exacta'),
        help_text=gettext_lazy('Si es verdadero, debe coincidir exactamente. Si es falso, busca la palabra en el mensaje.')
    )
    is_case_sensitive = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Sensible a mayúsculas')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    priority = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Prioridad'),
        help_text=gettext_lazy('Mayor número = mayor prioridad')
    )
    use_count = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Veces usado')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )

    class Meta:
        verbose_name = gettext_lazy('Palabra Clave WhatsApp')
        verbose_name_plural = gettext_lazy('Palabras Clave WhatsApp')
        ordering = ['-priority', 'keyword']
        unique_together = ['connection', 'keyword']

    def __str__(self):
        return f"{self.keyword} → {self.response[:50]}..."

    def increment_use_count(self):
        """Incrementa el contador de uso"""
        self.use_count += 1
        self.save(update_fields=['use_count'])


class WhatsAppMessage(models.Model):
    """Modelo para registrar mensajes de WhatsApp"""
    MESSAGE_TYPE_CHOICES = [
        ('received', gettext_lazy('Recibido')),
        ('sent', gettext_lazy('Enviado')),
        ('auto_reply', gettext_lazy('Respuesta Automática')),
    ]
    
    connection = models.ForeignKey(
        WhatsAppConnection,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=gettext_lazy('Conexión')
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        verbose_name=gettext_lazy('Tipo de mensaje')
    )
    from_number = models.CharField(
        max_length=50,
        verbose_name=gettext_lazy('De')
    )
    to_number = models.CharField(
        max_length=50,
        verbose_name=gettext_lazy('Para')
    )
    message_text = models.TextField(
        verbose_name=gettext_lazy('Mensaje')
    )
    keyword_matched = models.ForeignKey(
        WhatsAppKeyword,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Palabra clave coincidente')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha y hora')
    )

    class Meta:
        verbose_name = gettext_lazy('Mensaje WhatsApp')
        verbose_name_plural = gettext_lazy('Mensajes WhatsApp')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_message_type_display()} - {self.from_number} → {self.to_number}"


# ==================== MODELO IMAGE TO PROMPT ====================

class ImagePrompt(models.Model):
    """Modelo para guardar imágenes y sus prompts generados por IA"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='image_prompts',
        verbose_name=gettext_lazy('Usuario')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo para identificar esta imagen')
    )
    image = models.ImageField(
        upload_to='image_prompts/%Y/%m/',
        verbose_name=gettext_lazy('Imagen'),
        help_text=gettext_lazy('Sube una imagen para generar un prompt')
    )
    generated_prompt = models.TextField(
        verbose_name=gettext_lazy('Prompt Generado'),
        blank=True,
        help_text=gettext_lazy('Prompt generado automáticamente por IA')
    )
    custom_prompt = models.TextField(
        verbose_name=gettext_lazy('Prompt Personalizado'),
        blank=True,
        null=True,
        help_text=gettext_lazy('Prompt editado manualmente por el usuario')
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por comas para organizar')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('¿Es público?'),
        help_text=gettext_lazy('Si está marcado, otros usuarios pueden ver este prompt')
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tokens usados'),
        help_text=gettext_lazy('Cantidad de tokens de IA utilizados')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )

    class Meta:
        verbose_name = gettext_lazy('Image to Prompt')
        verbose_name_plural = gettext_lazy('Image to Prompts')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_final_prompt(self):
        """Retorna el prompt personalizado si existe, sino el generado"""
        return self.custom_prompt if self.custom_prompt else self.generated_prompt
    
    def delete(self, *args, **kwargs):
        """Elimina la imagen del sistema de archivos antes de eliminar el objeto"""
        # Eliminar el archivo de imagen si existe
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


class AIManager(models.Model):
    """Modelo para Gerentes de IA por empresa"""
    CATEGORY_CHOICES = [
        ('ventas', gettext_lazy('Ventas')),
        ('compras', gettext_lazy('Compras')),
        ('contabilidad', gettext_lazy('Contabilidad')),
        ('crm', gettext_lazy('CRM')),
        ('inventario', gettext_lazy('Inventario')),
        ('rrhh', gettext_lazy('Recursos Humanos')),
        ('marketing', gettext_lazy('Marketing')),
        ('operaciones', gettext_lazy('Operaciones')),
        ('finanzas', gettext_lazy('Finanzas')),
        ('ti', gettext_lazy('Tecnología')),
        ('otro', gettext_lazy('Otro')),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='ai_managers',
        verbose_name=gettext_lazy('Empresa')
    )
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Gerente IA'),
        help_text=gettext_lazy('Ejemplo: Gerente de Ventas IA')
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='otro',
        verbose_name=gettext_lazy('Categoría')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Describe el rol y responsabilidades de este gerente IA')
    )
    instructions = models.TextField(
        verbose_name=gettext_lazy('Instrucciones para la IA'),
        help_text=gettext_lazy('Contexto y personalidad del gerente IA'),
        default='Eres un gerente experimentado y empático. Tu objetivo es ayudar al equipo a mejorar.'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    # Integración con Telegram
    telegram_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Telegram Habilitado'),
        help_text=gettext_lazy('Enviar resúmenes automáticamente por Telegram')
    )
    telegram_bot_token = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Token del Bot de Telegram'),
        help_text=gettext_lazy('Token único del bot de Telegram para este gerente')
    )
    telegram_chat_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Chat ID de Telegram'),
        help_text=gettext_lazy('ID del chat o canal donde se enviarán los resúmenes')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ai_managers',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Gerente IA')
        verbose_name_plural = gettext_lazy('Gerentes IA')
        ordering = ['company', 'category', 'name']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    def get_total_meetings(self):
        """Retorna el total de reuniones de este gerente"""
        return self.meetings.count()
    
    def get_active_users(self):
        """Retorna usuarios únicos que han tenido reuniones"""
        return User.objects.filter(ai_manager_meetings__ai_manager=self).distinct().count()


class AIManagerMeeting(models.Model):
    """Modelo para reuniones entre usuarios y gerentes IA"""
    INPUT_TYPE_CHOICES = [
        ('text', gettext_lazy('Texto')),
        ('audio', gettext_lazy('Audio')),
    ]
    
    ai_manager = models.ForeignKey(
        AIManager,
        on_delete=models.CASCADE,
        related_name='meetings',
        verbose_name=gettext_lazy('Gerente IA')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_manager_meetings',
        verbose_name=gettext_lazy('Usuario')
    )
    title = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Resumen breve de la reunión')
    )
    input_type = models.CharField(
        max_length=10,
        choices=INPUT_TYPE_CHOICES,
        default='text',
        verbose_name=gettext_lazy('Tipo de entrada')
    )
    user_input = models.TextField(
        verbose_name=gettext_lazy('Entrada del usuario'),
        help_text=gettext_lazy('Lo que el usuario escribió o transcripción del audio')
    )
    audio_file = models.FileField(
        upload_to='ai_manager_meetings/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Archivo de audio')
    )
    ai_response = models.TextField(
        verbose_name=gettext_lazy('Respuesta de la IA'),
        help_text=gettext_lazy('Análisis y recomendaciones del gerente IA')
    )
    ai_summary = models.TextField(
        verbose_name=gettext_lazy('Resumen de la IA'),
        help_text=gettext_lazy('Resumen corto de la reunión')
    )
    improvement_areas = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Áreas de mejora'),
        help_text=gettext_lazy('Áreas identificadas para mejorar')
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tokens usados')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de reunión')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Reunión con Gerente IA')
        verbose_name_plural = gettext_lazy('Reuniones con Gerentes IA')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username} con {self.ai_manager.name}"
    
    def delete(self, *args, **kwargs):
        """Elimina el archivo de audio si existe"""
        if self.audio_file:
            if os.path.isfile(self.audio_file.path):
                os.remove(self.audio_file.path)
        super().delete(*args, **kwargs)


class AIManagerMeetingAttachment(models.Model):
    """Modelo para adjuntos de reuniones con gerentes IA"""
    meeting = models.ForeignKey(
        AIManagerMeeting,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=gettext_lazy('Reunión')
    )
    file = models.FileField(
        upload_to='ai_manager_meeting_attachments/%Y/%m/',
        verbose_name=gettext_lazy('Archivo adjunto'),
        help_text=gettext_lazy('Documentos, imágenes, PDFs que el gerente debe considerar')
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre del archivo')
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Tipo de archivo')
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de carga')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Adjunto de Reunión IA')
        verbose_name_plural = gettext_lazy('Adjuntos de Reuniones IA')
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.meeting.title}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_type = self.file.content_type if hasattr(self.file, 'content_type') else ''
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Eliminar el archivo físico al borrar el registro
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
    
    def get_file_size_display(self):
        """Retorna el tamaño en formato legible"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class AIManagerSummary(models.Model):
    """Modelo para resúmenes generales del gerente IA"""
    ai_manager = models.ForeignKey(
        AIManager,
        on_delete=models.CASCADE,
        related_name='summaries',
        verbose_name=gettext_lazy('Gerente IA')
    )
    period_start = models.DateField(
        verbose_name=gettext_lazy('Inicio del período')
    )
    period_end = models.DateField(
        verbose_name=gettext_lazy('Fin del período')
    )
    summary_text = models.TextField(
        verbose_name=gettext_lazy('Resumen general'),
        help_text=gettext_lazy('Resumen de todas las reuniones del período')
    )
    key_insights = models.TextField(
        verbose_name=gettext_lazy('Insights clave'),
        help_text=gettext_lazy('Puntos clave identificados')
    )
    recommendations = models.TextField(
        verbose_name=gettext_lazy('Recomendaciones'),
        help_text=gettext_lazy('Recomendaciones para la empresa')
    )
    total_meetings = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de reuniones')
    )
    participants_count = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Participantes únicos')
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tokens usados')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Resumen del Gerente IA')
        verbose_name_plural = gettext_lazy('Resúmenes del Gerente IA')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Resumen {self.ai_manager.name} - {self.period_start} a {self.period_end}"


class CompanyAISummary(models.Model):
    """Modelo para resúmenes empresariales generales (todos los gerentes)"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='ai_summaries',
        verbose_name=gettext_lazy('Empresa')
    )
    period_start = models.DateField(
        verbose_name=gettext_lazy('Inicio del período')
    )
    period_end = models.DateField(
        verbose_name=gettext_lazy('Fin del período')
    )
    executive_summary = models.TextField(
        verbose_name=gettext_lazy('Resumen ejecutivo'),
        help_text=gettext_lazy('Resumen general de toda la empresa')
    )
    key_metrics = models.TextField(
        verbose_name=gettext_lazy('Métricas clave'),
        help_text=gettext_lazy('KPIs y métricas importantes')
    )
    department_highlights = models.TextField(
        verbose_name=gettext_lazy('Destacados por departamento'),
        help_text=gettext_lazy('Logros por área/gerente')
    )
    challenges = models.TextField(
        verbose_name=gettext_lazy('Desafíos identificados'),
        help_text=gettext_lazy('Principales retos de la empresa')
    )
    strategic_recommendations = models.TextField(
        verbose_name=gettext_lazy('Recomendaciones estratégicas'),
        help_text=gettext_lazy('Acciones recomendadas para la dirección')
    )
    total_managers = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de gerentes')
    )
    total_meetings = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de reuniones')
    )
    total_participants = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de participantes')
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tokens usados')
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=gettext_lazy('Generado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Resumen Empresarial IA')
        verbose_name_plural = gettext_lazy('Resúmenes Empresariales IA')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Resumen {self.company.name} - {self.period_start} a {self.period_end}"


class UserAIPerformanceEvaluation(models.Model):
    """Modelo para evaluaciones de desempeño de usuarios con IA"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_performance_evaluations',
        verbose_name=gettext_lazy('Usuario')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='user_evaluations',
        verbose_name=gettext_lazy('Empresa'),
        null=True,
        blank=True
    )
    evaluation_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de evaluación')
    )
    overall_score = models.IntegerField(
        verbose_name=gettext_lazy('Puntuación general (1-100)'),
        help_text=gettext_lazy('Calificación automática generada por IA')
    )
    productivity_score = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Productividad (1-100)')
    )
    communication_score = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Comunicación (1-100)')
    )
    goal_achievement_score = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Logro de objetivos (1-100)')
    )
    consistency_score = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Consistencia (1-100)')
    )
    improvement_areas = models.TextField(
        verbose_name=gettext_lazy('Áreas de mejora'),
        help_text=gettext_lazy('Áreas identificadas que necesitan mejora')
    )
    training_recommendations = models.TextField(
        verbose_name=gettext_lazy('Recomendaciones de capacitación'),
        help_text=gettext_lazy('Cursos o entrenamientos sugeridos')
    )
    strengths = models.TextField(
        verbose_name=gettext_lazy('Fortalezas identificadas'),
        help_text=gettext_lazy('Puntos fuertes del usuario')
    )
    meetings_analyzed = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Reuniones analizadas')
    )
    period_start = models.DateField(
        verbose_name=gettext_lazy('Inicio del período'),
        null=True,
        blank=True
    )
    period_end = models.DateField(
        verbose_name=gettext_lazy('Fin del período'),
        null=True,
        blank=True
    )
    ai_summary = models.TextField(
        verbose_name=gettext_lazy('Resumen IA'),
        help_text=gettext_lazy('Resumen narrativo generado por IA'),
        blank=True
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tokens usados')
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_evaluations',
        verbose_name=gettext_lazy('Generado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Evaluación de Desempeño IA')
        verbose_name_plural = gettext_lazy('Evaluaciones de Desempeño IA')
        ordering = ['-evaluation_date', '-created_at']
        unique_together = ['user', 'evaluation_date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.evaluation_date} - {self.overall_score}/100"
    
    def get_score_color(self):
        """Retorna el color según la puntuación"""
        if self.overall_score >= 90:
            return 'success'
        elif self.overall_score >= 75:
            return 'info'
        elif self.overall_score >= 60:
            return 'warning'
        else:
            return 'danger'
    
    def get_performance_level(self):
        """Retorna el nivel de desempeño"""
        if self.overall_score >= 90:
            return 'Excelente'
        elif self.overall_score >= 75:
            return 'Bueno'
        elif self.overall_score >= 60:
            return 'Regular'
        else:
            return 'Necesita Mejora'


class WebsiteTracker(models.Model):
    """Modelo para rastrear y analizar sitios web/IPs"""
    
    # Información básica
    target = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('URL o IP'),
        help_text=gettext_lazy('URL completa (https://ejemplo.com) o dirección IP')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='website_trackers',
        verbose_name=gettext_lazy('Usuario')
    )
    
    # Información de conectividad
    is_active = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Está activo')
    )
    ping_response_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tiempo de respuesta (ms)'),
        help_text=gettext_lazy('Tiempo de respuesta del ping en milisegundos')
    )
    
    # Información de DNS
    ip_address = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    cname_records = models.JSONField(
        default=list,
        blank=True,
        verbose_name=gettext_lazy('Registros CNAME')
    )
    txt_records = models.JSONField(
        default=list,
        blank=True,
        verbose_name=gettext_lazy('Registros TXT')
    )
    mx_records = models.JSONField(
        default=list,
        blank=True,
        verbose_name=gettext_lazy('Registros MX')
    )
    ns_records = models.JSONField(
        default=list,
        blank=True,
        verbose_name=gettext_lazy('Registros NS')
    )
    
    # Información HTTP
    http_status_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Código de estado HTTP')
    )
    http_headers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=gettext_lazy('Headers HTTP')
    )
    redirect_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('URL de redirección')
    )
    
    # Información del servidor
    server_software = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Software del servidor')
    )
    technologies = models.JSONField(
        default=list,
        blank=True,
        verbose_name=gettext_lazy('Tecnologías detectadas'),
        help_text=gettext_lazy('Frameworks, CMS, librerías detectadas')
    )
    
    # Información de seguridad
    ssl_valid = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('SSL válido')
    )
    ssl_issuer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Emisor del certificado SSL')
    )
    ssl_expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de expiración SSL')
    )
    
    # Información de contenido
    page_title = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Título de la página')
    )
    meta_description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Meta descripción')
    )
    page_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tamaño de página (bytes)')
    )
    load_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tiempo de carga (s)')
    )
    
    # Información adicional
    whois_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=gettext_lazy('Datos WHOIS')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Mensaje de error'),
        help_text=gettext_lazy('Si ocurre algún error durante el rastreo')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de rastreo')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Rastreador Web')
        verbose_name_plural = gettext_lazy('Rastreadores Web')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.target} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    def get_status_badge(self):
        """Retorna el color del badge según el estado"""
        if self.is_active:
            return 'success'
        elif self.error_message:
            return 'danger'
        else:
            return 'secondary'
    
    def get_status_text(self):
        """Retorna el texto del estado"""
        if self.is_active:
            return 'Activo'
        elif self.error_message:
            return 'Error'
        else:
            return 'Inactivo'


class LegalContract(models.Model):
    """Modelo para contratos legales generados con IA"""
    
    # Información básica
    name = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre del contrato'),
        help_text=gettext_lazy('Ej: Contrato de Soporte de Software')
    )
    contract_type = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Tipo de contrato'),
        help_text=gettext_lazy('Ej: Soporte de software, Desarrollo, Consultoría, etc.')
    )
    
    # Partes del contrato
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='legal_contracts_as_provider',
        verbose_name=gettext_lazy('Empresa proveedora'),
        help_text=gettext_lazy('Tu empresa que provee el servicio')
    )
    client_company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='legal_contracts_as_client',
        verbose_name=gettext_lazy('Empresa cliente'),
        help_text=gettext_lazy('La empresa que contrata el servicio')
    )
    
    # Prompt y generación
    objective_prompt = models.TextField(
        verbose_name=gettext_lazy('Objetivo del contrato'),
        help_text=gettext_lazy('Describe el objetivo y alcance del contrato. Ej: Soporte técnico 24/7 para sistema ERP')
    )
    generated_content = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Contenido generado'),
        help_text=gettext_lazy('Contenido del contrato generado por IA')
    )
    
    # Detalles del contrato
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de inicio')
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de finalización')
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Monto del contrato'),
        help_text=gettext_lazy('Valor económico del contrato')
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name=gettext_lazy('Moneda'),
        help_text=gettext_lazy('Código de moneda (USD, EUR, MXN, etc.)')
    )
    
    # Control de acceso
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='legal_contracts',
        verbose_name=gettext_lazy('Creado por')
    )
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token público'),
        help_text=gettext_lazy('Token único para compartir el contrato públicamente')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Público'),
        help_text=gettext_lazy('Si está marcado, el contrato se puede ver públicamente con el enlace')
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', gettext_lazy('Borrador')),
            ('generated', gettext_lazy('Generado')),
            ('sent', gettext_lazy('Enviado')),
            ('signed', gettext_lazy('Firmado')),
            ('active', gettext_lazy('Activo')),
            ('completed', gettext_lazy('Completado')),
            ('cancelled', gettext_lazy('Cancelado')),
        ],
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    generated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de generación'),
        help_text=gettext_lazy('Cuándo se generó el contenido con IA')
    )
    
    # Configuración adicional
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas internas'),
        help_text=gettext_lazy('Notas privadas sobre el contrato')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Contrato Legal')
        verbose_name_plural = gettext_lazy('Contratos Legales')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['public_token']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company.name} / {self.client_company.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('legal_contract_detail', kwargs={'pk': self.pk})
    
    def get_public_url(self):
        from django.urls import reverse
        return reverse('legal_contract_public', kwargs={'token': self.public_token})
    
    def get_status_badge(self):
        """Retorna el color del badge según el estado"""
        status_colors = {
            'draft': 'secondary',
            'generated': 'info',
            'sent': 'warning',
            'signed': 'primary',
            'active': 'success',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_status_display_with_icon(self):
        """Retorna el estado con icono"""
        status_icons = {
            'draft': 'bi-pencil',
            'generated': 'bi-magic',
            'sent': 'bi-send',
            'signed': 'bi-pen',
            'active': 'bi-check-circle',
            'completed': 'bi-check-circle-fill',
            'cancelled': 'bi-x-circle',
        }
        icon = status_icons.get(self.status, 'bi-circle')
        return f'<i class="bi {icon}"></i> {self.get_status_display()}'
    
    def generate_with_ai(self):
        """Genera el contenido del contrato usando OpenAI"""
        from tickets.models import SystemConfiguration
        import re
        
        def remove_markdown_formatting(text):
            """Elimina formato Markdown y devuelve texto plano"""
            # Eliminar negritas **texto** y dejar solo texto
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            # Eliminar cursivas *texto* y dejar solo texto
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            # Eliminar títulos ## y # y dejar solo el texto
            text = re.sub(r'^#{1,6}\s*(.*?)$', r'\1', text, flags=re.MULTILINE)
            return text
        
        config = SystemConfiguration.objects.first()
        if not config or not config.ai_chat_enabled or not config.openai_api_key:
            raise Exception("OpenAI no está configurado. Por favor configura la API key en Configuración del Sistema.")
        
        try:
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            prompt = f"""
            Genera un contrato legal profesional y detallado con los siguientes datos:
            
            TIPO DE CONTRATO: {self.contract_type}
            OBJETIVO: {self.objective_prompt}
            
            EMPRESA PROVEEDORA:
            - Nombre: {self.company.name}
            - Dirección: {self.company.address}
            - Teléfono: {self.company.phone}
            - Email: {self.company.email}
            
            EMPRESA CLIENTE:
            - Nombre: {self.client_company.name}
            - Dirección: {self.client_company.address}
            - Teléfono: {self.client_company.phone}
            - Email: {self.client_company.email}
            
            DETALLES ADICIONALES:
            - Fecha de inicio: {self.start_date if self.start_date else 'No especificada'}
            - Fecha de finalización: {self.end_date if self.end_date else 'No especificada'}
            - Monto: {f'{self.amount} {self.currency}' if self.amount else 'No especificado'}
            
            El contrato debe incluir:
            1. Encabezado con las partes contratantes
            2. Antecedentes y objeto del contrato
            3. Obligaciones de cada parte
            4. Términos y condiciones
            5. Duración y vigencia
            6. Aspectos económicos
            7. Cláusulas de confidencialidad
            8. Causas de rescisión
            9. Solución de controversias
            10. Firmas y datos de contacto
            
            Usa un lenguaje legal formal pero comprensible. Incluye cláusulas estándar para este tipo de contrato.
            NO uses formato Markdown. Usa texto plano con saltos de línea para separar secciones.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un abogado experto en redacción de contratos legales comerciales. Generas contratos profesionales, detallados y legalmente sólidos. NO uses formato Markdown en tus respuestas, solo texto plano con saltos de línea."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            generated_content = response.choices[0].message.content
            # Limpiar cualquier formato Markdown y devolver texto plano
            self.generated_content = remove_markdown_formatting(generated_content)
            self.generated_at = timezone.now()
            self.status = 'generated'
            self.save()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error al generar contrato: {str(e)}")
    
class SupplierContractReview(models.Model):
    """Modelo para revisar contratos de proveedores con IA"""
    
    REVIEW_STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('reviewed', gettext_lazy('Revisado')),
        ('approved', gettext_lazy('Aprobado')),
        ('rejected', gettext_lazy('Rechazado')),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', gettext_lazy('Bajo')),
        ('medium', gettext_lazy('Medio')),
        ('high', gettext_lazy('Alto')),
        ('critical', gettext_lazy('Crítico')),
    ]
    
    # Información básica
    name = models.CharField(max_length=200, verbose_name=gettext_lazy("Nombre del Contrato"))
    supplier_name = models.CharField(max_length=200, verbose_name=gettext_lazy("Nombre del Proveedor"))
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_contract_reviews', verbose_name=gettext_lazy("Empresa Revisora"))
    
    # Contenido del contrato
    contract_text = models.TextField(verbose_name=gettext_lazy("Texto del Contrato"), help_text=gettext_lazy("Pegue aquí el texto del contrato o déjelo vacío si subirá un archivo"))
    contract_file = models.FileField(upload_to='contract_reviews/%Y/%m/', blank=True, null=True, verbose_name=gettext_lazy("Archivo del Contrato"))
    
    # Análisis de IA
    ai_review = models.TextField(blank=True, verbose_name=gettext_lazy("Revisión de IA"), help_text=gettext_lazy("Análisis generado por IA"))
    risk_assessment = models.TextField(blank=True, verbose_name=gettext_lazy("Evaluación de Riesgos"))
    key_clauses = models.TextField(blank=True, verbose_name=gettext_lazy("Cláusulas Clave Identificadas"))
    recommendations = models.TextField(blank=True, verbose_name=gettext_lazy("Recomendaciones"))
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium', verbose_name=gettext_lazy("Nivel de Riesgo"))
    
    # Estado y seguimiento
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending', verbose_name=gettext_lazy("Estado"))
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy("Fecha de Revisión"))
    
    # Notas internas
    internal_notes = models.TextField(blank=True, verbose_name=gettext_lazy("Notas Internas"))
    
    # Metadatos
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=gettext_lazy("Usuario"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de Creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy("Última Actualización"))
    
    class Meta:
        verbose_name = gettext_lazy("Revisión de Contrato de Proveedor")
        verbose_name_plural = gettext_lazy("Revisiones de Contratos de Proveedores")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.supplier_name}"
    
    def get_status_badge(self):
        """Retorna el badge HTML para el estado"""
        badges = {
            'pending': '<span class="badge bg-warning">Pendiente</span>',
            'reviewed': '<span class="badge bg-info">Revisado</span>',
            'approved': '<span class="badge bg-success">Aprobado</span>',
            'rejected': '<span class="badge bg-danger">Rechazado</span>',
        }
        return badges.get(self.status, '<span class="badge bg-secondary">Desconocido</span>')
    
    def get_risk_badge(self):
        """Retorna el badge HTML para el nivel de riesgo"""
        badges = {
            'low': '<span class="badge bg-success"><i class="bi bi-shield-check"></i> Bajo</span>',
            'medium': '<span class="badge bg-warning"><i class="bi bi-shield-exclamation"></i> Medio</span>',
            'high': '<span class="badge bg-danger"><i class="bi bi-shield-x"></i> Alto</span>',
            'critical': '<span class="badge bg-dark"><i class="bi bi-shield-fill-x"></i> Crítico</span>',
        }
        return badges.get(self.risk_level, '<span class="badge bg-secondary">N/A</span>')
    
    def get_contract_content(self):
        """Obtiene el contenido del contrato, ya sea del texto o del archivo"""
        if self.contract_text:
            return self.contract_text
        
        if self.contract_file:
            try:
                file_extension = self.contract_file.name.split('.')[-1].lower()
                
                if file_extension == 'pdf':
                    # Extraer texto de PDF
                    import PyPDF2
                    with self.contract_file.open('rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text()
                        return text
                
                elif file_extension in ['doc', 'docx']:
                    # Extraer texto de Word
                    import docx
                    doc = docx.Document(self.contract_file.path)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    return text
                
                elif file_extension == 'txt':
                    # Leer archivo de texto
                    with self.contract_file.open('r', encoding='utf-8') as file:
                        return file.read()
                
                else:
                    return "Formato de archivo no soportado. Use PDF, DOCX o TXT."
            
            except Exception as e:
                return f"Error al extraer texto del archivo: {str(e)}"
        
        return "No hay contenido disponible"
    
    def review_with_ai(self):
        """Revisa el contrato usando IA"""
        from django.utils import timezone
        
        # Verificar configuración de OpenAI
        config = SystemConfiguration.objects.first()
        if not config or not config.ai_chat_enabled or not config.openai_api_key:
            raise Exception("OpenAI no está configurado. Por favor configura la API key en Configuración del Sistema.")
        
        try:
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            # Obtener el contenido del contrato
            contract_content = self.get_contract_content()
            
            if not contract_content or contract_content.startswith("Error") or contract_content == "No hay contenido disponible":
                raise Exception("No se puede obtener el contenido del contrato para revisar")
            
            prompt = f"""
            Eres un abogado experto en revisión de contratos comerciales con proveedores. 
            Analiza el siguiente contrato de proveedor de manera exhaustiva y profesional.
            
            PROVEEDOR: {self.supplier_name}
            EMPRESA REVISORA: {self.company.name}
            
            CONTRATO:
            {contract_content[:15000]}  # Limitar a 15000 caracteres para no exceder tokens
            
            Proporciona un análisis detallado en el siguiente formato:
            
            ## RESUMEN EJECUTIVO
            [Resumen breve del contrato y su propósito]
            
            ## ANÁLISIS DETALLADO
            [Análisis completo del contrato, términos principales, obligaciones de cada parte]
            
            ## CLÁUSULAS CLAVE
            [Lista numerada de las cláusulas más importantes y su implicación]
            
            ## EVALUACIÓN DE RIESGOS
            [Identificación de riesgos potenciales, cláusulas problemáticas, términos desfavorables]
            
            ## NIVEL DE RIESGO GENERAL
            [Indica: BAJO, MEDIO, ALTO o CRÍTICO]
            
            ## RECOMENDACIONES
            [Lista de recomendaciones específicas: qué negociar, qué cláusulas modificar, qué aclaraciones solicitar]
            
            ## PUNTOS A NEGOCIAR
            [Lista de puntos específicos que deberían negociarse antes de firmar]
            
            Sé específico, profesional y enfócate en proteger los intereses de {self.company.name}.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un abogado corporativo experto en revisión de contratos con proveedores. Tu objetivo es identificar riesgos, proteger los intereses del cliente y proporcionar recomendaciones prácticas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            full_review = response.choices[0].message.content
            
            # Extraer información estructurada
            self.ai_review = full_review
            
            # Extraer cláusulas clave
            if "## CLÁUSULAS CLAVE" in full_review:
                clauses_section = full_review.split("## CLÁUSULAS CLAVE")[1].split("##")[0]
                self.key_clauses = clauses_section.strip()
            
            # Extraer evaluación de riesgos
            if "## EVALUACIÓN DE RIESGOS" in full_review:
                risk_section = full_review.split("## EVALUACIÓN DE RIESGOS")[1].split("##")[0]
                self.risk_assessment = risk_section.strip()
            
            # Extraer recomendaciones
            if "## RECOMENDACIONES" in full_review:
                recommendations_section = full_review.split("## RECOMENDACIONES")[1].split("##")[0]
                self.recommendations = recommendations_section.strip()
            
            # Determinar nivel de riesgo
            if "## NIVEL DE RIESGO GENERAL" in full_review:
                risk_level_section = full_review.split("## NIVEL DE RIESGO GENERAL")[1].split("##")[0].strip().lower()
                if "crítico" in risk_level_section or "critical" in risk_level_section:
                    self.risk_level = 'critical'
                elif "alto" in risk_level_section or "high" in risk_level_section:
                    self.risk_level = 'high'
                elif "medio" in risk_level_section or "medium" in risk_level_section:
                    self.risk_level = 'medium'
                else:
                    self.risk_level = 'low'
            
            self.status = 'reviewed'
            self.reviewed_at = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error al revisar contrato: {str(e)}")


class PayPalPaymentLink(models.Model):
    """Modelo para enlaces de pago de PayPal"""
    
    STATUS_CHOICES = [
        ('active', gettext_lazy('Activo')),
        ('paid', gettext_lazy('Pagado')),
        ('expired', gettext_lazy('Expirado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    # Información básica
    product_name = models.CharField(max_length=200, verbose_name=gettext_lazy("Nombre del Producto/Servicio"))
    description = models.TextField(blank=True, verbose_name=gettext_lazy("Descripción"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=gettext_lazy("Importe (EUR)"))
    
    # Archivo adjunto
    attachment = models.FileField(
        upload_to='paypal_attachments/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy("Archivo Adjunto"),
        help_text=gettext_lazy("Archivo que el cliente podrá descargar después del pago")
    )
    attachment_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy("Nombre del archivo"),
        help_text=gettext_lazy("Nombre descriptivo del archivo adjunto")
    )
    
    # URL y token
    public_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy("Token Público")
    )
    public_url = models.URLField(blank=True, verbose_name=gettext_lazy("URL Pública"))
    
    # Información del pago
    paypal_order_id = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy("ID de Orden PayPal"))
    paypal_payer_id = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy("ID del Pagador"))
    paypal_payer_email = models.EmailField(blank=True, verbose_name=gettext_lazy("Email del Pagador"))
    paypal_payer_name = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy("Nombre del Pagador"))
    paypal_payment_status = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy("Estado del Pago PayPal"))
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy("Fecha de Pago"))
    
    # Estado y seguimiento
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=gettext_lazy("Estado")
    )
    download_count = models.IntegerField(default=0, verbose_name=gettext_lazy("Número de Descargas"))
    
    # Token temporal de descarga (válido por 72 horas después del pago)
    download_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy("Token de Descarga Temporal")
    )
    download_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy("Fecha de Expiración del Token de Descarga")
    )
    
    # Metadatos
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=gettext_lazy("Usuario Creador"))
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy("Empresa"),
        help_text=gettext_lazy("Empresa asociada (opcional)")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy("Fecha de Creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy("Última Actualización"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy("Fecha de Expiración"))
    
    # Notas internas
    notes = models.TextField(blank=True, verbose_name=gettext_lazy("Notas Internas"))
    
    class Meta:
        verbose_name = gettext_lazy("Enlace de Pago PayPal")
        verbose_name_plural = gettext_lazy("Enlaces de Pago PayPal")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product_name} - €{self.amount}"
    
    def save(self, *args, **kwargs):
        # Generar URL pública si no existe
        if not self.public_url:
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            self.public_url = f"{base_url}/paypal-payment/{self.public_token}/"
        
        # Establecer nombre del archivo si no existe
        if self.attachment and not self.attachment_name:
            self.attachment_name = self.attachment.name.split('/')[-1]
        
        super().save(*args, **kwargs)
    
    def get_status_badge(self):
        """Retorna el badge HTML para el estado"""
        badges = {
            'active': '<span class="badge bg-primary">Activo</span>',
            'paid': '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Pagado</span>',
            'expired': '<span class="badge bg-secondary">Expirado</span>',
            'cancelled': '<span class="badge bg-danger">Cancelado</span>',
        }
        return badges.get(self.status, '<span class="badge bg-secondary">Desconocido</span>')
    
    def is_paid(self):
        """Verifica si el enlace ha sido pagado"""
        return self.status == 'paid'
    
    def is_active(self):
        """Verifica si el enlace está activo (solo verifica expiración por fecha)"""
        from django.utils import timezone
        # Solo verificar expiración por fecha - los enlaces son reutilizables
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
    
    def mark_as_paid(self, order_id, payer_info):
        """Marca el enlace como pagado con información del pagador"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.status = 'paid'
        self.payment_date = timezone.now()
        self.paypal_order_id = order_id
        
        # Establecer token de descarga válido por 72 horas
        self.download_token = uuid.uuid4()
        self.download_token_expires_at = timezone.now() + timedelta(hours=72)
        
        if payer_info:
            self.paypal_payer_id = payer_info.get('payer_id', '')
            self.paypal_payer_email = payer_info.get('email_address', '')
            name_info = payer_info.get('name', {})
            given_name = name_info.get('given_name', '') if isinstance(name_info, dict) else ''
            surname = name_info.get('surname', '') if isinstance(name_info, dict) else ''
            self.paypal_payer_name = f"{given_name} {surname}".strip()
        
        self.save()
    
    def increment_download(self):
        """Incrementa el contador de descargas"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def is_download_token_valid(self):
        """Verifica si el token de descarga aún es válido (72 horas)"""
        from django.utils import timezone
        if not self.is_paid():
            return False
        if not self.download_token_expires_at:
            return False
        return self.download_token_expires_at > timezone.now()
    
    def get_download_url(self):
        """Retorna la URL de descarga temporal"""
        if self.is_download_token_valid() and self.attachment:
            from django.urls import reverse
            return reverse('paypal_download_with_token', kwargs={'token': self.download_token})
        return None
    
    def get_order_summary_url(self):
        """Retorna la URL del resumen de orden"""
        if self.is_paid():
            from django.urls import reverse
            return reverse('paypal_order_summary', kwargs={'token': self.public_token})
        return None
    
    def get_hours_until_download_expires(self):
        """Retorna las horas restantes hasta que expire el token de descarga"""
        from django.utils import timezone
        if not self.download_token_expires_at:
            return 0
        time_diff = self.download_token_expires_at - timezone.now()
        hours = time_diff.total_seconds() / 3600
        return max(0, round(hours, 1))
    
    def get_total_orders_count(self):
        """Retorna el número total de órdenes/pagos completados para este enlace"""
        return self.orders.filter(status='paid').count()
    
    def get_total_revenue(self):
        """Retorna el total de ingresos generados por este enlace"""
        from django.db.models import Sum
        total = self.orders.filter(status='paid').aggregate(total=Sum('amount'))['total']
        return total or 0


class PayPalOrder(models.Model):
    """Modelo para órdenes individuales de pago (cada compra genera una orden)"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('paid', gettext_lazy('Pagado')),
        ('failed', gettext_lazy('Fallido')),
        ('refunded', gettext_lazy('Reembolsado')),
    ]
    
    # Relación con el enlace de pago original (plantilla)
    payment_link = models.ForeignKey(
        PayPalPaymentLink,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=gettext_lazy('Enlace de Pago'),
        help_text=gettext_lazy('Enlace de pago desde el cual se generó esta orden')
    )
    
    # Token único para esta orden
    order_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token de Orden'),
        help_text=gettext_lazy('Token único para acceder a esta orden específica')
    )
    
    # Información del producto (copiada del enlace al momento de la compra)
    product_name = models.CharField(max_length=200, verbose_name=gettext_lazy('Producto'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=gettext_lazy('Importe (EUR)'))
    
    # Información del pago
    paypal_order_id = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=gettext_lazy('ID de Orden PayPal')
    )
    paypal_payer_id = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('ID del Pagador'))
    paypal_payer_email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email del Pagador'))
    paypal_payer_name = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Nombre del Pagador'))
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Fecha de Pago'))
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Token de descarga temporal (válido 72 horas)
    download_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token de Descarga')
    )
    download_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Expiración Token de Descarga')
    )
    download_count = models.IntegerField(default=0, verbose_name=gettext_lazy('Número de Descargas'))
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última Actualización'))
    
    class Meta:
        verbose_name = gettext_lazy('Orden de Pago PayPal')
        verbose_name_plural = gettext_lazy('Órdenes de Pago PayPal')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['paypal_order_id']),
            models.Index(fields=['order_token']),
            models.Index(fields=['download_token']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Orden #{self.id:05d} - {self.product_name} - {self.get_status_display()}"
    
    def is_paid(self):
        """Verifica si la orden ha sido pagada"""
        return self.status == 'paid'
    
    def mark_as_paid(self, payer_info):
        """Marca la orden como pagada"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.status = 'paid'
        self.payment_date = timezone.now()
        
        # Establecer token de descarga válido por 72 horas
        self.download_token = uuid.uuid4()
        self.download_token_expires_at = timezone.now() + timedelta(hours=72)
        
        if payer_info:
            self.paypal_payer_id = payer_info.get('payer_id', '')
            self.paypal_payer_email = payer_info.get('email_address', '')
            name_info = payer_info.get('name', {})
            given_name = name_info.get('given_name', '') if isinstance(name_info, dict) else ''
            surname = name_info.get('surname', '') if isinstance(name_info, dict) else ''
            self.paypal_payer_name = f"{given_name} {surname}".strip()
        
        self.save()
    
    def increment_download(self):
        """Incrementa el contador de descargas"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def is_download_token_valid(self):
        """Verifica si el token de descarga aún es válido"""
        from django.utils import timezone
        if not self.is_paid():
            return False
        if not self.download_token_expires_at:
            return False
        return self.download_token_expires_at > timezone.now()
    
    def get_hours_until_download_expires(self):
        """Retorna las horas restantes hasta que expire el token"""
        from django.utils import timezone
        if not self.download_token_expires_at:
            return 0
        time_diff = self.download_token_expires_at - timezone.now()
        hours = time_diff.total_seconds() / 3600
        return max(0, round(hours, 1))
    
    def get_download_url(self):
        """Retorna la URL de descarga temporal"""
        if self.is_download_token_valid() and self.payment_link.attachment:
            from django.urls import reverse
            return reverse('paypal_order_download', kwargs={'token': self.download_token})
        return None
    
    def get_order_summary_url(self):
        """Retorna la URL del resumen de orden"""
        from django.urls import reverse
        return reverse('paypal_order_detail', kwargs={'token': self.order_token})
    
    def get_status_badge(self):
        """Retorna el badge HTML para el estado"""
        badges = {
            'pending': '<span class="badge bg-warning">Pendiente</span>',
            'paid': '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Pagado</span>',
            'failed': '<span class="badge bg-danger">Fallido</span>',
            'refunded': '<span class="badge bg-secondary">Reembolsado</span>',
        }
        return badges.get(self.status, '<span class="badge bg-secondary">Desconocido</span>')


class TodoItem(models.Model):
    """Modelo para items de TODO list en tickets"""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='todo_items',
        verbose_name=gettext_lazy('Ticket')
    )
    text = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Tarea')
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Completada')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='todo_items_created',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de completado')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden')
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Item de TODO')
        verbose_name_plural = gettext_lazy('Items de TODO')
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.text[:50]}"
    
    def toggle_completed(self):
        """Alterna el estado de completado"""
        self.is_completed = not self.is_completed
        if self.is_completed:
            self.completed_at = timezone.now()
        else:
            self.completed_at = None
        self.save()


class AIBook(models.Model):
    """Modelo para libros generados con IA"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('chapters_proposed', gettext_lazy('Capítulos Propuestos')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('completed', gettext_lazy('Completado')),
    ]
    
    title = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Título del Libro')
    )
    author = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Autor'),
        help_text=gettext_lazy('Nombre del autor del libro')
    )
    topic = models.TextField(
        verbose_name=gettext_lazy('Tema/Descripción'),
        help_text=gettext_lazy('Describe de qué quieres que trate el libro')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_books',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_books',
        verbose_name=gettext_lazy('Empresa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Libro IA')
        verbose_name_plural = gettext_lazy('Libros IA')
    
    def __str__(self):
        return self.title
    
    def get_status_badge_class(self):
        """Retorna la clase Bootstrap del badge según el estado"""
        badges = {
            'draft': 'bg-secondary',
            'chapters_proposed': 'bg-info',
            'in_progress': 'bg-warning',
            'completed': 'bg-success',
        }
        return badges.get(self.status, 'bg-secondary')
    
    def get_total_chapters(self):
        """Retorna el total de capítulos"""
        return self.chapters.count()
    
    def get_completed_chapters(self):
        """Retorna el número de capítulos completados (con contenido generado)"""
        return self.chapters.filter(status__in=['content_generated', 'completed']).count()
    
    def get_progress_percentage(self):
        """Retorna el porcentaje de progreso"""
        total = self.get_total_chapters()
        if total == 0:
            return 0
        completed = self.get_completed_chapters()
        return int((completed / total) * 100)
    
    def get_total_words(self):
        """Retorna el total de palabras de todos los capítulos"""
        from django.db.models import Sum
        result = self.chapters.aggregate(total=Sum('word_count'))
        return result['total'] or 0


class AIBookChapter(models.Model):
    """Modelo para capítulos de libros generados con IA"""
    
    STATUS_CHOICES = [
        ('proposed', gettext_lazy('Propuesto')),
        ('summary_created', gettext_lazy('Resumen Creado')),
        ('content_generated', gettext_lazy('Contenido Generado')),
        ('completed', gettext_lazy('Completado')),
    ]
    
    book = models.ForeignKey(
        AIBook,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name=gettext_lazy('Libro')
    )
    title = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Título del Capítulo')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden')
    )
    summary = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Resumen del Capítulo'),
        help_text=gettext_lazy('Resumen breve de lo que tratará el capítulo')
    )
    content = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Contenido del Capítulo'),
        help_text=gettext_lazy('Contenido completo en texto plano (sin formato Markdown)')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='proposed',
        verbose_name=gettext_lazy('Estado')
    )
    word_count = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Conteo de Palabras')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['book', 'order']
        verbose_name = gettext_lazy('Capítulo de Libro IA')
        verbose_name_plural = gettext_lazy('Capítulos de Libros IA')
    
    def __str__(self):
        return f"{self.book.title} - Cap. {self.order}: {self.title}"
    
    def get_status_badge_class(self):
        """Retorna la clase Bootstrap del badge según el estado"""
        badges = {
            'proposed': 'bg-secondary',
            'summary_created': 'bg-info',
            'content_generated': 'bg-primary',
            'completed': 'bg-success',
        }
        return badges.get(self.status, 'bg-secondary')
    
    def update_word_count(self):
        """Actualiza el conteo de palabras del contenido"""
        if self.content:
            self.word_count = len(self.content.split())
        else:
            self.word_count = 0
        self.save(update_fields=['word_count'])
    
    def save(self, *args, **kwargs):
        """Override save para actualizar automáticamente el conteo de palabras"""
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


class AIArticleProject(models.Model):
    """Modelo para proyectos de generación de artículos con IA"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('articles_proposed', gettext_lazy('Artículos Propuestos')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('completed', gettext_lazy('Completado')),
    ]
    
    FORMAT_CHOICES = [
        ('plain', gettext_lazy('Texto Plano')),
        ('markdown', gettext_lazy('Markdown')),
    ]
    
    title = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Título del Proyecto')
    )
    main_topic = models.TextField(
        verbose_name=gettext_lazy('Tema Principal'),
        help_text=gettext_lazy('Describe el tema principal sobre el cual quieres generar artículos')
    )
    content_format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='plain',
        verbose_name=gettext_lazy('Formato de Contenido'),
        help_text=gettext_lazy('Formato en el que se generará el contenido de los artículos')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_article_projects',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_article_projects',
        verbose_name=gettext_lazy('Empresa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Proyecto de Artículos IA')
        verbose_name_plural = gettext_lazy('Proyectos de Artículos IA')
    
    def __str__(self):
        return self.title
    
    def get_status_badge_class(self):
        """Retorna la clase Bootstrap del badge según el estado"""
        badges = {
            'draft': 'bg-secondary',
            'articles_proposed': 'bg-info',
            'in_progress': 'bg-warning',
            'completed': 'bg-success',
        }
        return badges.get(self.status, 'bg-secondary')
    
    def get_total_articles(self):
        """Retorna el total de artículos"""
        return self.articles.count()
    
    def get_completed_articles(self):
        """Retorna el número de artículos completados (con contenido generado)"""
        return self.articles.filter(status__in=['content_generated', 'completed']).count()
    
    def get_progress_percentage(self):
        """Retorna el porcentaje de progreso"""
        total = self.get_total_articles()
        if total == 0:
            return 0
        completed = self.get_completed_articles()
        return int((completed / total) * 100)
    
    def get_total_words(self):
        """Retorna el total de palabras de todos los artículos"""
        from django.db.models import Sum
        result = self.articles.aggregate(total=Sum('word_count'))
        return result['total'] or 0


class AIArticle(models.Model):
    """Modelo para artículos individuales generados con IA"""
    
    STATUS_CHOICES = [
        ('proposed', gettext_lazy('Propuesto')),
        ('content_generated', gettext_lazy('Contenido Generado')),
        ('completed', gettext_lazy('Completado')),
    ]
    
    project = models.ForeignKey(
        AIArticleProject,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name=gettext_lazy('Proyecto')
    )
    title = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Título del Artículo')
    )
    keywords = models.CharField(
        max_length=1000,
        blank=True,
        verbose_name=gettext_lazy('Palabras Clave'),
        help_text=gettext_lazy('Palabras clave separadas por comas')
    )
    content = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Contenido del Artículo'),
        help_text=gettext_lazy('Contenido completo en texto plano')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='proposed',
        verbose_name=gettext_lazy('Estado')
    )
    word_count = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Conteo de Palabras')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['project', 'order']
        verbose_name = gettext_lazy('Artículo IA')
        verbose_name_plural = gettext_lazy('Artículos IA')
    
    def __str__(self):
        return f"{self.project.title} - {self.title}"
    
    def get_status_badge_class(self):
        """Retorna la clase Bootstrap del badge según el estado"""
        badges = {
            'proposed': 'bg-secondary',
            'content_generated': 'bg-primary',
            'completed': 'bg-success',
        }
        return badges.get(self.status, 'bg-secondary')
    
    def get_keywords_list(self):
        """Retorna las palabras clave como lista"""
        if self.keywords:
            return [k.strip() for k in self.keywords.split(',') if k.strip()]
        return []
    
    def save(self, *args, **kwargs):
        """Override save para actualizar automáticamente el conteo de palabras"""
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)


class EmployeeRequest(models.Model):
    """Modelo para las solicitudes de empleados"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('approved', gettext_lazy('Aprobada')),
        ('rejected', gettext_lazy('Rechazada')),
    ]
    
    sequence = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Secuencia'),
        help_text=gettext_lazy('Número de secuencia de la solicitud')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título de la solicitud')
    )
    
    text = models.TextField(
        verbose_name=gettext_lazy('Texto'),
        help_text=gettext_lazy('Descripción detallada de la solicitud')
    )
    
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha'),
        help_text=gettext_lazy('Fecha de creación de la solicitud')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado'),
        help_text=gettext_lazy('Estado actual de la solicitud')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employee_requests',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Solicitud de Empleado')
        verbose_name_plural = gettext_lazy('Solicitudes de Empleados')
        ordering = ['-sequence', '-created_at']
        unique_together = ['sequence']
    
    def __str__(self):
        return f"Solicitud #{self.sequence} - {self.title}"
    
    def get_status_display_class(self):
        """Retorna la clase CSS para el estado"""
        classes = {
            'draft': 'badge bg-secondary',
            'approved': 'badge bg-success',
            'rejected': 'badge bg-danger',
        }
        return classes.get(self.status, 'badge bg-secondary')
    
    def get_status_icon(self):
        """Retorna el ícono para el estado"""
        icons = {
            'draft': 'bi bi-file-earmark-text',
            'approved': 'bi bi-check-circle',
            'rejected': 'bi bi-x-circle',
        }
        return icons.get(self.status, 'bi bi-file-earmark-text')
    
    def save(self, *args, **kwargs):
        """Override save para generar automáticamente la secuencia"""
        if not self.sequence:
            # Obtener el último número de secuencia y agregar 1
            last_request = EmployeeRequest.objects.order_by('-sequence').first()
            self.sequence = (last_request.sequence + 1) if last_request else 1
        super().save(*args, **kwargs)


class InternalAgreement(models.Model):
    """Modelo para gestionar acuerdos internos de la empresa"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('review', gettext_lazy('En Revisión')),
        ('approved', gettext_lazy('Aprobado')),
        ('rejected', gettext_lazy('Rechazado')),
        ('active', gettext_lazy('Activo')),
        ('expired', gettext_lazy('Expirado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    TYPE_CHOICES = [
        ('policy', gettext_lazy('Política')),
        ('procedure', gettext_lazy('Procedimiento')),
        ('contract', gettext_lazy('Contrato')),
        ('guideline', gettext_lazy('Directriz')),
        ('agreement', gettext_lazy('Acuerdo')),
        ('regulation', gettext_lazy('Reglamento')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', gettext_lazy('Baja')),
        ('medium', gettext_lazy('Media')),
        ('high', gettext_lazy('Alta')),
        ('critical', gettext_lazy('Crítica')),
    ]
    
    sequence = models.PositiveIntegerField(
        unique=True,
        verbose_name=gettext_lazy('Número de Secuencia'),
        help_text=gettext_lazy('Número único auto-generado')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo del acuerdo interno')
    )
    
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del acuerdo interno')
    )
    
    content = models.TextField(
        verbose_name=gettext_lazy('Contenido'),
        help_text=gettext_lazy('Contenido completo del acuerdo interno')
    )
    
    agreement_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='agreement',
        verbose_name=gettext_lazy('Tipo de Acuerdo')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    
    effective_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Vigencia'),
        help_text=gettext_lazy('Fecha en que el acuerdo entra en vigencia')
    )
    
    expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Expiración'),
        help_text=gettext_lazy('Fecha en que el acuerdo expira (opcional)')
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Departamento'),
        help_text=gettext_lazy('Departamento al que aplica el acuerdo')
    )
    
    applies_to_all = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Aplica a Todos'),
        help_text=gettext_lazy('Si el acuerdo aplica a todos los empleados')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='internal_agreements_created',
        verbose_name=gettext_lazy('Creado por')
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='internal_agreements_approved',
        verbose_name=gettext_lazy('Aprobado por')
    )
    
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Aprobación')
    )
    
    # Campos para firmantes del acuerdo
    signer_1 = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='internal_agreements_signed_1',
        verbose_name=gettext_lazy('Primer Firmante'),
        help_text=gettext_lazy('Usuario que firma el acuerdo como primer firmante')
    )
    
    signer_1_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Firma 1'),
        help_text=gettext_lazy('Fecha en que el primer firmante firmó el acuerdo')
    )
    
    signer_2 = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='internal_agreements_signed_2',
        verbose_name=gettext_lazy('Segundo Firmante'),
        help_text=gettext_lazy('Usuario que firma el acuerdo como segundo firmante')
    )
    
    signer_2_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Firma 2'),
        help_text=gettext_lazy('Fecha en que el segundo firmante firmó el acuerdo')
    )
    
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por comas para facilitar búsquedas')
    )
    
    version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name=gettext_lazy('Versión'),
        help_text=gettext_lazy('Versión del acuerdo')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Acuerdo Interno')
        verbose_name_plural = gettext_lazy('Acuerdos Internos')
        indexes = [
            models.Index(fields=['status', 'agreement_type']),
            models.Index(fields=['effective_date', 'expiration_date']),
        ]
    
    def __str__(self):
        return f"#{self.sequence} - {self.title}"
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge del estado"""
        classes = {
            'draft': 'badge bg-secondary',
            'review': 'badge bg-warning',
            'approved': 'badge bg-info',
            'rejected': 'badge bg-danger',
            'active': 'badge bg-success',
            'expired': 'badge bg-dark',
            'cancelled': 'badge bg-light text-dark',
        }
        return classes.get(self.status, 'badge bg-secondary')
    
    def get_status_icon(self):
        """Retorna el ícono para el estado"""
        icons = {
            'draft': 'bi bi-file-earmark-text',
            'review': 'bi bi-eye',
            'approved': 'bi bi-check-circle-fill',
            'rejected': 'bi bi-x-circle-fill',
            'active': 'bi bi-check-circle',
            'expired': 'bi bi-clock-history',
            'cancelled': 'bi bi-x-circle',
        }
        return icons.get(self.status, 'bi bi-file-earmark-text')
    
    def get_type_icon(self):
        """Retorna el ícono para el tipo de acuerdo"""
        icons = {
            'policy': 'bi bi-shield-check',
            'procedure': 'bi bi-list-check',
            'contract': 'bi bi-file-earmark-text',
            'guideline': 'bi bi-signpost',
            'agreement': 'bi bi-handshake',
            'regulation': 'bi bi-bookmark-check',
        }
        return icons.get(self.agreement_type, 'bi bi-file-earmark-check')
    
    def get_priority_badge_class(self):
        """Retorna la clase CSS para el badge de prioridad"""
        classes = {
            'low': 'badge bg-light text-dark',
            'medium': 'badge bg-info',
            'high': 'badge bg-warning text-dark',
            'critical': 'badge bg-danger',
        }
        return classes.get(self.priority, 'badge bg-info')
    
    def is_active(self):
        """Verifica si el acuerdo está activo y vigente"""
        if self.status != 'active':
            return False
        
        today = timezone.now().date()
        
        if self.effective_date and self.effective_date > today:
            return False
        
        if self.expiration_date and self.expiration_date < today:
            return False
        
        return True
    
    def can_edit(self, user):
        """Verifica si el usuario puede editar el acuerdo"""
        from .utils import is_agent
        return is_agent(user) or user.is_staff or user == self.created_by
    
    def can_delete(self, user):
        """Verifica si el usuario puede eliminar el acuerdo"""
        from .utils import is_agent
        return (is_agent(user) or user.is_staff or user == self.created_by) and self.status == 'draft'
    
    def is_signed_by(self, user):
        """Verifica si el usuario ya firmó el acuerdo"""
        return (self.signer_1 == user and self.signer_1_date) or \
               (self.signer_2 == user and self.signer_2_date)
    
    def can_sign(self, user, signer_number=None):
        """Verifica si el usuario puede firmar el acuerdo"""
        # Solo se puede firmar si está activo o aprobado y el usuario no ha firmado ya
        if self.status not in ['active', 'approved']:
            return False
        
        # Si ya firmó, no puede firmar de nuevo
        if self.is_signed_by(user):
            return False
        
        # Si se especifica número de firmante, verificar específicamente
        if signer_number is not None:
            if signer_number == 1:
                return user == self.signer_1 and not self.signer_1_date
            elif signer_number == 2:
                return user == self.signer_2 and not self.signer_2_date
            return False
        
        # Si no hay firmantes asignados, cualquier usuario autorizado puede firmar
        if not self.signer_1 and not self.signer_2:
            from .utils import is_agent
            return is_agent(user) or user.is_staff
        
        # Si hay firmantes asignados, solo ellos pueden firmar
        return user == self.signer_1 or user == self.signer_2
    
    def sign_agreement(self, user, signer_number=None):
        """Firma el acuerdo con el usuario especificado"""
        if signer_number is not None:
            # Firmar como un número específico de firmante
            if not self.can_sign(user, signer_number):
                return False
            
            from django.utils import timezone
            current_time = timezone.now()
            
            if signer_number == 1:
                self.signer_1_date = current_time
            elif signer_number == 2:
                self.signer_2_date = current_time
            else:
                return False
            
            self.save()
            return True
        else:
            # Lógica original para compatibilidad
            if not self.can_sign(user):
                return False
            
            from django.utils import timezone
            current_time = timezone.now()
            
            # Firmar en el primer slot disponible
            if not self.signer_1 or (self.signer_1 == user and not self.signer_1_date):
                self.signer_1 = user
                self.signer_1_date = current_time
            elif not self.signer_2 or (self.signer_2 == user and not self.signer_2_date):
                self.signer_2 = user
                self.signer_2_date = current_time
            else:
                return False
            
            self.save()
            return True
    
    def is_fully_signed(self):
        """Verifica si el acuerdo está completamente firmado"""
        return (self.signer_1 and self.signer_1_date and 
                self.signer_2 and self.signer_2_date)
    
    def get_signature_status(self):
        """Retorna el estado de las firmas"""
        if self.is_fully_signed():
            return "Completamente firmado"
        elif self.signer_1_date or self.signer_2_date:
            return "Parcialmente firmado"
        elif self.signer_1 or self.signer_2:
            return "Pendiente de firma"
        else:
            return "Sin firmantes asignados"
    
    def save(self, *args, **kwargs):
        """Override save para generar automáticamente la secuencia"""
        if not self.sequence:
            # Obtener el último número de secuencia y agregar 1
            last_agreement = InternalAgreement.objects.order_by('-sequence').first()
            self.sequence = (last_agreement.sequence + 1) if last_agreement else 1
        super().save(*args, **kwargs)


class TrainingPlan(models.Model):
    """Plan de Capacitación"""
    sequence = models.PositiveIntegerField(unique=True, verbose_name=gettext_lazy('Secuencia'))
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del Plan'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Fecha de actualización'))
    created_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=gettext_lazy('Creado por'))

    class Meta:
        verbose_name = gettext_lazy('Plan de Capacitación')
        verbose_name_plural = gettext_lazy('Planes de Capacitación')
        ordering = ['sequence']

    def __str__(self):
        return f"Plan #{self.sequence}: {self.title}"

    def get_total_links(self):
        """Retorna el total de enlaces en este plan"""
        return self.links.count()

    def get_progress_for_user(self, user):
        """Retorna el progreso del usuario en este plan"""
        total_links = self.get_total_links()
        if total_links == 0:
            return 0
        
        # Contar directamente los EmployeeLinkProgress del usuario para este plan
        from .models import EmployeeLinkProgress
        completed_links = EmployeeLinkProgress.objects.filter(
            employee=user,
            link__plan=self
        ).count()
        
        return (completed_links / total_links) * 100

    def is_completed_by_user(self, user):
        """Verifica si el usuario completó todo el plan"""
        try:
            progress = EmployeeTrainingProgress.objects.get(employee=user, plan=self)
            return progress.status == 'completed'
        except EmployeeTrainingProgress.DoesNotExist:
            return False


class TrainingLink(models.Model):
    """Enlace de Capacitación"""
    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name='links', verbose_name=gettext_lazy('Plan de Capacitación'))
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del Enlace'))
    url = models.URLField(verbose_name=gettext_lazy('URL'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    order = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    is_required = models.BooleanField(default=True, verbose_name=gettext_lazy('Requerido'))
    estimated_hours = models.PositiveIntegerField(default=1, verbose_name=gettext_lazy('Horas estimadas'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        verbose_name = gettext_lazy('Enlace de Capacitación')
        verbose_name_plural = gettext_lazy('Enlaces de Capacitación')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.plan.title} - {self.title}"

    def is_completed_by_user(self, user):
        """Verifica si el usuario completó este enlace"""
        return EmployeeLinkProgress.objects.filter(employee=user, link=self).exists()


class EmployeeTrainingProgress(models.Model):
    """Progreso de Capacitación por Empleado"""
    STATUS_CHOICES = [
        ('not_started', gettext_lazy('No iniciado')),
        ('in_progress', gettext_lazy('En progreso')),
        ('completed', gettext_lazy('Completado')),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_progress', verbose_name=gettext_lazy('Empleado'))
    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name='employee_progress', verbose_name=gettext_lazy('Plan de Capacitación'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name=gettext_lazy('Estado'))
    started_at = models.DateTimeField(blank=True, null=True, verbose_name=gettext_lazy('Iniciado el'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=gettext_lazy('Completado el'))
    notes = models.TextField(blank=True, verbose_name=gettext_lazy('Notas'))

    class Meta:
        verbose_name = gettext_lazy('Progreso de Capacitación')
        verbose_name_plural = gettext_lazy('Progreso de Capacitaciones')
        unique_together = ('employee', 'plan')

    def __str__(self):
        return f"{self.employee.username} - {self.plan.title} ({self.get_status_display()})"

    def get_completion_percentage(self):
        """Calcula el porcentaje de completado"""
        total_links = self.plan.get_total_links()
        if total_links == 0:
            return 0
        completed_links = self.completed_links.count()
        return (completed_links / total_links) * 100

    def update_status(self):
        """Actualiza el estado basado en los enlaces completados"""
        total_links = self.plan.get_total_links()
        completed_links = self.completed_links.count()
        
        if completed_links == 0:
            self.status = 'not_started'
            self.started_at = None
            self.completed_at = None
        elif completed_links == total_links:
            self.status = 'completed'
            if not self.completed_at:
                from django.utils import timezone
                self.completed_at = timezone.now()
        else:
            self.status = 'in_progress'
            if not self.started_at:
                from django.utils import timezone
                self.started_at = timezone.now()
            self.completed_at = None
        
        self.save()


class EmployeeLinkProgress(models.Model):
    """Progreso individual de cada enlace por empleado"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=gettext_lazy('Empleado'))
    link = models.ForeignKey(TrainingLink, on_delete=models.CASCADE, related_name='employee_progress', verbose_name=gettext_lazy('Enlace'))
    training_progress = models.ForeignKey(EmployeeTrainingProgress, on_delete=models.CASCADE, related_name='completed_links', verbose_name=gettext_lazy('Progreso de Capacitación'))
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Completado el'))
    time_spent_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name=gettext_lazy('Tiempo invertido (horas)'))
    notes = models.TextField(blank=True, verbose_name=gettext_lazy('Notas'))

    class Meta:
        verbose_name = gettext_lazy('Progreso de Enlace')
        verbose_name_plural = gettext_lazy('Progreso de Enlaces')
        unique_together = ('employee', 'link')

    def __str__(self):
        return f"{self.employee.username} - {self.link.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el estado del progreso general del entrenamiento
        self.training_progress.update_status()


# ========== MODELOS DE RECOMENDACIONES IA ==========

class AIRecommendation(models.Model):
    """Modelo para gestionar recomendaciones de IA para respuestas políticamente correctas"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo de la recomendación')
    )
    context_text = models.TextField(
        verbose_name=gettext_lazy('Texto de Contexto'),
        help_text=gettext_lazy('Contexto base que usará la IA para generar respuestas')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Si está activa, podrá ser usada para generar respuestas')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_recommendations',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Recomendación IA')
        verbose_name_plural = gettext_lazy('Recomendaciones IA')
    
    def __str__(self):
        return self.title
    
    def get_usage_count(self):
        """Retorna el número de veces que se ha usado esta recomendación"""
        return self.usage_logs.count()


class AIRecommendationUsage(models.Model):
    """Modelo para registrar el uso de recomendaciones IA"""
    
    recommendation = models.ForeignKey(
        AIRecommendation,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        verbose_name=gettext_lazy('Recomendación')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_recommendation_usage',
        verbose_name=gettext_lazy('Usuario')
    )
    client_case = models.TextField(
        verbose_name=gettext_lazy('Caso del Cliente'),
        help_text=gettext_lazy('Caso específico o situación del cliente enviada para análisis')
    )
    ai_response = models.TextField(
        verbose_name=gettext_lazy('Respuesta de IA'),
        help_text=gettext_lazy('Respuesta generada por la IA basada en el contexto y caso')
    )
    is_helpful = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('¿Fue útil?'),
        help_text=gettext_lazy('Calificación de utilidad de la respuesta')
    )
    feedback = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentarios'),
        help_text=gettext_lazy('Comentarios adicionales del usuario sobre la respuesta')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de uso')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Uso de Recomendación IA')
        verbose_name_plural = gettext_lazy('Usos de Recomendaciones IA')
    
    def __str__(self):
        return f"{self.recommendation.title} - {self.user.username} ({self.created_at.strftime('%d/%m/%Y')})"


# ========== MODELOS DE AUSENCIAS DE EMPLEADOS ==========

class AbsenceType(models.Model):
    """Tipos de ausencias disponibles"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Nombre del Tipo'),
        help_text=gettext_lazy('Ej: Vacaciones, Enfermedad, Permiso Personal')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del tipo de ausencia')
    )
    requires_documentation = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Requiere Documentación'),
        help_text=gettext_lazy('Si se requiere documentación de respaldo (ej: certificado médico)')
    )
    is_paid = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Es Remunerado'),
        help_text=gettext_lazy('Si la ausencia es con goce de sueldo')
    )
    max_days_per_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Máximo Días por Año'),
        help_text=gettext_lazy('Límite anual de días para este tipo de ausencia (opcional)')
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color para mostrar en el calendario (formato hex: #RRGGBB)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si este tipo de ausencia está disponible para uso')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Tipo de Ausencia')
        verbose_name_plural = gettext_lazy('Tipos de Ausencias')
    
    def __str__(self):
        return self.name
    
    def get_usage_count(self):
        """Retorna el número de ausencias registradas de este tipo"""
        return self.absences.count()


class EmployeeAbsence(models.Model):
    """Registro de ausencias de empleados"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('approved', gettext_lazy('Aprobada')),
        ('rejected', gettext_lazy('Rechazada')),
        ('cancelled', gettext_lazy('Cancelada')),
    ]
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='absences',
        verbose_name=gettext_lazy('Empleado')
    )
    absence_type = models.ForeignKey(
        AbsenceType,
        on_delete=models.CASCADE,
        related_name='absences',
        verbose_name=gettext_lazy('Tipo de Ausencia')
    )
    start_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Inicio'),
        help_text=gettext_lazy('Primer día de ausencia')
    )
    end_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Fin'),
        help_text=gettext_lazy('Último día de ausencia')
    )
    lost_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=gettext_lazy('Horas Perdidas'),
        help_text=gettext_lazy('Total de horas laborales perdidas por la ausencia')
    )
    reason = models.TextField(
        verbose_name=gettext_lazy('Motivo'),
        help_text=gettext_lazy('Explicación detallada del motivo de la ausencia')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    documentation_file = models.FileField(
        upload_to='absence_documentation/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Documentación'),
        help_text=gettext_lazy('Archivo de respaldo (certificado médico, etc.)')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_absences',
        verbose_name=gettext_lazy('Aprobado por')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de aprobación')
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Motivo de rechazo'),
        help_text=gettext_lazy('Razón por la cual se rechazó la ausencia')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas adicionales'),
        help_text=gettext_lazy('Comentarios internos sobre la ausencia')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de solicitud')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-start_date', '-created_at']
        verbose_name = gettext_lazy('Ausencia de Empleado')
        verbose_name_plural = gettext_lazy('Ausencias de Empleados')
    
    def __str__(self):
        return f"{self.employee.get_full_name() or self.employee.username} - {self.absence_type.name} ({self.start_date} a {self.end_date})"
    
    def clean(self):
        """Validación personalizada"""
        from django.core.exceptions import ValidationError
        
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_duration_days(self):
        """Retorna la duración en días de la ausencia"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def calculate_lost_hours(self, hours_per_day=8):
        """Calcula las horas perdidas basado en los días de ausencia"""
        duration_days = self.get_duration_days()
        return duration_days * hours_per_day
    
    def get_lost_hours_display(self):
        """Retorna las horas perdidas formateadas"""
        if self.lost_hours:
            return f"{self.lost_hours} horas"
        return "0 horas"
    
    def get_average_hours_per_day(self):
        """Retorna el promedio de horas perdidas por día"""
        duration_days = self.get_duration_days()
        if duration_days > 0 and self.lost_hours:
            return round(float(self.lost_hours) / duration_days, 1)
        return 0.0
    
    def get_status_display_class(self):
        """Retorna la clase CSS para el estado"""
        status_classes = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary',
        }
        return status_classes.get(self.status, 'secondary')
    
    def is_current(self):
        """Verifica si la ausencia está actualmente en curso"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status == 'approved'
    
    def approve(self, approved_by_user):
        """Aprueba la ausencia"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, reason, rejected_by_user):
        """Rechaza la ausencia"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.save()


class CompanyProtocol(models.Model):
    """Modelo para gestionar protocolos de empresa"""
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='protocols',
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa a la que pertenece este protocolo'),
        null=True,
        blank=True
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Protocolo'),
        help_text=gettext_lazy('Título descriptivo del protocolo empresarial')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Contenido del Protocolo'),
        help_text=gettext_lazy('Contenido completo del protocolo. Puedes usar formato básico.')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_protocols',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Indica si el protocolo está activo y disponible')
    )
    version = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name=gettext_lazy('Versión'),
        help_text=gettext_lazy('Versión del protocolo (ej: 1.0, 1.1, 2.0)')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Compartir públicamente'),
        help_text=gettext_lazy('Permite que este protocolo sea accesible públicamente sin autenticación')
    )
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=gettext_lazy('UUID público'),
        help_text=gettext_lazy('Identificador único para acceso público')
    )
    public_shared_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Compartido públicamente en'),
        help_text=gettext_lazy('Fecha cuando se compartió públicamente por primera vez')
    )
    public_views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Vistas públicas'),
        help_text=gettext_lazy('Número de veces que se ha visto públicamente este protocolo')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Protocolo de Empresa')
        verbose_name_plural = gettext_lazy('Protocolos de Empresa')
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def get_short_content(self, max_length=100):
        """Retorna una versión truncada del contenido"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + '...'
    
    def get_word_count(self):
        """Retorna el número de palabras en el contenido"""
        return len(self.content.split())
    
    def increment_version(self):
        """Incrementa automáticamente la versión del protocolo"""
        try:
            version_parts = self.version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            minor += 1
            if minor >= 10:
                major += 1
                minor = 0
            self.version = f"{major}.{minor}"
        except (ValueError, IndexError):
            self.version = "1.0"
    
    def make_public(self):
        """Hace el protocolo público y registra la fecha"""
        if not self.is_public:
            self.is_public = True
            self.public_shared_at = timezone.now()
            self.save()
    
    def make_private(self):
        """Hace el protocolo privado"""
        self.is_public = False
        self.save()
    
    def get_public_url(self):
        """Retorna la URL pública del protocolo"""
        if self.is_public:
            return f"/public/protocols/{self.public_uuid}/"
        return None
    
    def increment_public_views(self):
        """Incrementa el contador de vistas públicas"""
        self.public_views_count += 1
        self.save(update_fields=['public_views_count'])
    
    def get_public_stats(self):
        """Retorna estadísticas de visualización pública"""
        return {
            'total_views': self.public_views_count,
            'is_public': self.is_public,
            'shared_date': self.public_shared_at,
            'public_url': self.get_public_url()
        }
    
    def generate_ai_content(self, content_type="comprehensive"):
        """Genera contenido automático del protocolo usando IA"""
        from tickets.models import SystemConfiguration
        import re
        
        def remove_markdown_formatting(text):
            """Elimina formato Markdown y devuelve texto plano"""
            # Eliminar negritas **texto** y dejar solo texto
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            # Eliminar cursivas *texto* y dejar solo texto
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            # Eliminar títulos ## y # y dejar solo el texto
            text = re.sub(r'^#{1,6}\s*(.*?)$', r'\1', text, flags=re.MULTILINE)
            # Eliminar listas numeradas 1. y dejar solo el texto
            text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
            # Eliminar listas con viñetas - y * y dejar solo el texto
            text = re.sub(r'^[-*]\s*', '', text, flags=re.MULTILINE)
            return text
            text = re.sub(r'\n(\d+)\.\s+', r'</p><ol><li>', text)
            # Convertir listas con viñetas
            text = re.sub(r'\n[-*]\s+', r'</p><ul><li>', text)
            # Limpiar párrafos vacíos
            text = re.sub(r'<p>\s*</p>', '', text)
            return text
        
        config = SystemConfiguration.objects.first()
        if not config or not config.ai_chat_enabled or not config.openai_api_key:
            return {"success": False, "error": "OpenAI no está configurado en el sistema"}
        
        try:
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            company_context = f" para la empresa {self.company.name}" if self.company else ""
            
            prompts = {
                "comprehensive": f"""
                Genera un protocolo empresarial completo y profesional con el título: "{self.title}"{company_context}.
                
                El protocolo debe incluir:
                1. Introducción y propósito
                2. Alcance y aplicabilidad
                3. Responsabilidades
                4. Procedimientos detallados paso a paso
                5. Requisitos y estándares
                6. Medidas de seguridad (si aplica)
                7. Documentación y registros
                8. Revisión y actualización
                
                Escribe en español, usando un lenguaje profesional y claro. El protocolo debe ser práctico y actionable.
                NO uses formato Markdown (**, *, etc.). Usa texto plano con saltos de línea para separar secciones.
                """,
                "summary": f"""
                Basándote en el título "{self.title}"{company_context}, genera un resumen ejecutivo y puntos clave 
                para un protocolo empresarial. Incluye objetivos principales, beneficios esperados y requisitos básicos.
                Máximo 500 palabras.
                NO uses formato Markdown. Usa texto plano con saltos de línea.
                """,
                "checklist": f"""
                Crea una lista de verificación (checklist) detallada para el protocolo "{self.title}"{company_context}.
                Incluye todos los pasos necesarios, verificaciones de seguridad, y puntos de control de calidad.
                Formato de lista numerada y clara.
                NO uses formato Markdown. Usa texto plano con numeración simple.
                """
            }
            
            response = client.chat.completions.create(
                model=config.openai_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto consultor empresarial especializado en crear protocolos y procedimientos corporativos de alta calidad. NO uses formato Markdown en tus respuestas, solo texto plano con saltos de línea."},
                    {"role": "user", "content": prompts.get(content_type, prompts["comprehensive"])}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            generated_content = response.choices[0].message.content.strip()
            # Limpiar cualquier formato Markdown y devolver texto plano
            generated_content = remove_markdown_formatting(generated_content)
            
            return {
                "success": True,
                "content": generated_content,
                "word_count": len(generated_content.split()),
                "content_type": content_type
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error generando contenido: {str(e)}"}
    
    def analyze_readability(self):
        """Analiza la legibilidad del protocolo"""
        import re
        
        try:
            text = self.content
            if not text:
                return {"success": False, "error": "No hay contenido para analizar"}
            
            # Métricas básicas
            word_count = len(text.split())
            sentence_count = len(re.split(r'[.!?]+', text))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            # Promedio de palabras por oración
            avg_words_per_sentence = word_count / max(sentence_count, 1)
            
            # Promedio de oraciones por párrafo
            avg_sentences_per_paragraph = sentence_count / max(paragraph_count, 1)
            
            # Análisis de complejidad
            complex_words = len([word for word in text.split() if len(word) > 6])
            complexity_ratio = complex_words / max(word_count, 1) * 100
            
            # Puntuación de legibilidad (escala 1-10)
            readability_score = 10
            
            if avg_words_per_sentence > 20:
                readability_score -= 2
            elif avg_words_per_sentence > 15:
                readability_score -= 1
                
            if complexity_ratio > 30:
                readability_score -= 2
            elif complexity_ratio > 20:
                readability_score -= 1
                
            if avg_sentences_per_paragraph > 8:
                readability_score -= 1
            
            readability_score = max(1, readability_score)
            
            # Nivel de legibilidad
            if readability_score >= 8:
                level = "Excelente"
                color = "success"
            elif readability_score >= 6:
                level = "Bueno"
                color = "info"
            elif readability_score >= 4:
                level = "Regular"
                color = "warning"
            else:
                level = "Difícil"
                color = "danger"
            
            return {
                "success": True,
                "score": readability_score,
                "level": level,
                "color": color,
                "metrics": {
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "paragraph_count": paragraph_count,
                    "avg_words_per_sentence": round(avg_words_per_sentence, 1),
                    "avg_sentences_per_paragraph": round(avg_sentences_per_paragraph, 1),
                    "complexity_ratio": round(complexity_ratio, 1)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error analizando legibilidad: {str(e)}"}
    
    def get_ai_suggestions(self):
        """Genera sugerencias de mejora usando IA"""
        from tickets.models import SystemConfiguration
        import re
        
        def remove_markdown_formatting(text):
            """Elimina formato Markdown y devuelve texto plano"""
            # Eliminar negritas **texto** y dejar solo texto
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            # Eliminar cursivas *texto* y dejar solo texto
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            # Eliminar títulos ## y # y dejar solo el texto
            text = re.sub(r'^#{1,6}\s*(.*?)$', r'\1', text, flags=re.MULTILINE)
            # Eliminar listas numeradas 1. y dejar solo el texto
            text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
            # Eliminar listas con viñetas - y * y dejar solo el texto
            text = re.sub(r'^[-*]\s*', '', text, flags=re.MULTILINE)
            return text
            return text
        
        config = SystemConfiguration.objects.first()
        if not config or not config.ai_chat_enabled or not config.openai_api_key:
            return {"success": False, "error": "OpenAI no está configurado en el sistema"}
        
        try:
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            # Análisis de legibilidad primero
            readability = self.analyze_readability()
            
            prompt = f"""
            Analiza el siguiente protocolo empresarial y proporciona sugerencias específicas de mejora:
            
            TÍTULO: {self.title}
            EMPRESA: {self.company.name if self.company else 'No especificada'}
            
            CONTENIDO:
            {self.content[:1500]}...
            
            Proporciona sugerencias en las siguientes categorías:
            1. CLARIDAD: Cómo mejorar la claridad del lenguaje
            2. ESTRUCTURA: Sugerencias de organización del contenido
            3. COMPLETITUD: Qué elementos podrían estar faltando
            4. PROFESIONALISMO: Cómo hacer el protocolo más profesional
            5. ACCIONABILIDAD: Cómo hacer las instrucciones más específicas
            
            Proporciona máximo 3 sugerencias por categoría, sean concretas y actionables.
            NO uses formato Markdown. Usa texto plano con saltos de línea.
            """
            
            response = client.chat.completions.create(
                model=config.openai_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un consultor experto en documentación empresarial y mejora de procesos corporativos. NO uses formato Markdown en tus respuestas, solo texto plano con saltos de línea."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.6
            )
            
            suggestions = response.choices[0].message.content.strip()
            # Limpiar cualquier formato Markdown y devolver texto plano
            suggestions = remove_markdown_formatting(suggestions)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "readability_info": readability if readability["success"] else None
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error generando sugerencias: {str(e)}"}
    
    def generate_executive_summary(self):
        """Genera un resumen ejecutivo del protocolo"""
        from tickets.models import SystemConfiguration
        import re
        
        def remove_markdown_formatting(text):
            """Elimina formato Markdown y devuelve texto plano"""
            # Eliminar negritas **texto** y dejar solo texto
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            # Eliminar cursivas *texto* y dejar solo texto
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            # Eliminar títulos ## y # y dejar solo el texto
            text = re.sub(r'^#{1,6}\s*(.*?)$', r'\1', text, flags=re.MULTILINE)
            # Eliminar listas numeradas 1. y dejar solo el texto
            text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
            # Eliminar listas con viñetas - y * y dejar solo el texto
            text = re.sub(r'^[-*]\s*', '', text, flags=re.MULTILINE)
            return text
        
        config = SystemConfiguration.objects.first()
        if not config or not config.ai_chat_enabled or not config.openai_api_key:
            return {"success": False, "error": "OpenAI no está configurado en el sistema"}
        
        try:
            import openai
            client = openai.OpenAI(api_key=config.openai_api_key)
            
            prompt = f"""
            Crea un resumen ejecutivo profesional del siguiente protocolo:
            
            TÍTULO: {self.title}
            EMPRESA: {self.company.name if self.company else 'No especificada'}
            
            CONTENIDO:
            {self.content}
            
            El resumen ejecutivo debe incluir:
            1. Propósito y objetivos principales
            2. Beneficios clave
            3. Impacto en la organización
            4. Recursos necesarios
            5. Cronograma de implementación (si aplica)
            
            Máximo 300 palabras, lenguaje ejecutivo y persuasivo.
            NO uses formato Markdown. Usa texto plano con saltos de línea.
            """
            
            response = client.chat.completions.create(
                model=config.openai_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un director ejecutivo escribiendo resúmenes para la junta directiva. NO uses formato Markdown en tus respuestas, solo texto plano con saltos de línea."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            # Limpiar cualquier formato Markdown y devolver texto plano
            summary = remove_markdown_formatting(summary)
            
            return {
                "success": True,
                "summary": summary,
                "word_count": len(summary.split())
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error generando resumen: {str(e)}"}


class QAComplaint(models.Model):
    """Modelo para gestionar quejas y sugerencias de QA asociadas a empresas"""
    
    TYPE_CHOICES = [
        ('complaint', gettext_lazy('Queja')),
        ('suggestion', gettext_lazy('Sugerencia')),
        ('feedback', gettext_lazy('Retroalimentación')),
        ('improvement', gettext_lazy('Mejora')),
        ('quality_issue', gettext_lazy('Problema de Calidad')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', gettext_lazy('Baja')),
        ('medium', gettext_lazy('Media')),
        ('high', gettext_lazy('Alta')),
        ('critical', gettext_lazy('Crítica')),
    ]
    
    STATUS_CHOICES = [
        ('open', gettext_lazy('Abierto')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('pending_review', gettext_lazy('Pendiente de Revisión')),
        ('resolved', gettext_lazy('Resuelto')),
        ('closed', gettext_lazy('Cerrado')),
        ('rejected', gettext_lazy('Rechazado')),
    ]
    
    # Campos principales
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo de la queja o sugerencia')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del problema o sugerencia')
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='complaint',
        verbose_name=gettext_lazy('Tipo'),
        help_text=gettext_lazy('Tipo de reporte: queja, sugerencia, etc.')
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=gettext_lazy('Prioridad'),
        help_text=gettext_lazy('Nivel de prioridad del reporte')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name=gettext_lazy('Estado'),
        help_text=gettext_lazy('Estado actual del reporte')
    )
    
    # Relaciones
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='qa_complaints',
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa asociada a esta queja o sugerencia')
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_complaints',
        verbose_name=gettext_lazy('Reportado por'),
        help_text=gettext_lazy('Usuario que reportó la queja o sugerencia')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        verbose_name=gettext_lazy('Asignado a'),
        help_text=gettext_lazy('Usuario responsable de resolver la queja')
    )
    
    # Campos adicionales
    contact_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email de contacto'),
        help_text=gettext_lazy('Email del cliente o usuario que reporta (opcional)')
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Teléfono de contacto'),
        help_text=gettext_lazy('Teléfono del cliente o usuario que reporta (opcional)')
    )
    
    # Campos de seguimiento
    resolution = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Resolución'),
        help_text=gettext_lazy('Descripción de cómo se resolvió la queja o implementó la sugerencia')
    )
    resolution_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de resolución')
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_complaints',
        verbose_name=gettext_lazy('Resuelto por'),
        help_text=gettext_lazy('Usuario que resolvió la queja')
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Campos de archivo
    attachment = models.FileField(
        upload_to='qa_complaints/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Archivo adjunto'),
        help_text=gettext_lazy('Imagen, documento o archivo relacionado con la queja')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Queja/Sugerencia QA')
        verbose_name_plural = gettext_lazy('Quejas/Sugerencias QA')
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.title} ({self.company.name})"
    
    def get_status_color(self):
        """Retorna el color Bootstrap para el estado"""
        colors = {
            'open': 'danger',
            'in_progress': 'warning',
            'pending_review': 'info',
            'resolved': 'success',
            'closed': 'secondary',
            'rejected': 'dark',
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Retorna el color Bootstrap para la prioridad"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        return colors.get(self.priority, 'secondary')
    
    def get_type_icon(self):
        """Retorna el ícono Bootstrap para el tipo"""
        icons = {
            'complaint': 'exclamation-triangle',
            'suggestion': 'lightbulb',
            'feedback': 'chat-dots',
            'improvement': 'arrow-up-circle',
            'quality_issue': 'bug',
        }
        return icons.get(self.type, 'file-text')
    
    def is_overdue(self):
        """Verifica si la queja está vencida (más de 7 días sin resolver)"""
        if self.status in ['resolved', 'closed']:
            return False
        
        from datetime import timedelta
        overdue_date = self.created_at + timedelta(days=7)
        return timezone.now() > overdue_date
    
    def get_age_days(self):
        """Retorna la antigüedad en días"""
        return (timezone.now() - self.created_at).days
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar esta queja"""
        from .utils import is_agent
        return (
            user.is_staff or 
            user.is_superuser or 
            user == self.reported_by or 
            user == self.assigned_to or
            is_agent(user)
        )
    
    def can_resolve(self, user):
        """Verifica si un usuario puede resolver esta queja"""
        from .utils import is_agent
        return (
            user.is_staff or 
            user.is_superuser or 
            user == self.assigned_to or
            is_agent(user)
        )
    
    def resolve(self, resolution_text, resolved_by):
        """Marca la queja como resuelta"""
        self.status = 'resolved'
        self.resolution = resolution_text
        self.resolution_date = timezone.now()
        self.resolved_by = resolved_by
        if not self.assigned_to:
            self.assigned_to = resolved_by
        self.save()
    
    def assign_to(self, user):
        """Asigna la queja a un usuario"""
        self.assigned_to = user
        if self.status == 'open':
            self.status = 'in_progress'
        self.save()


class QAComplaintComment(models.Model):
    """Modelo para comentarios en quejas y sugerencias QA"""
    
    complaint = models.ForeignKey(
        QAComplaint,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Queja/Sugerencia')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Autor')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Comentario'),
        help_text=gettext_lazy('Contenido del comentario o nota')
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Comentario interno'),
        help_text=gettext_lazy('Marca si es un comentario interno (no visible para el cliente)')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Comentario QA')
        verbose_name_plural = gettext_lazy('Comentarios QA')
    
    def __str__(self):
        return f"Comentario de {self.author.username} en {self.complaint.title[:50]}"


# ==================== MODELOS DE CONTROL DE ACTIVOS ====================

class Asset(models.Model):
    """Modelo para gestionar activos de la empresa"""
    STATUS_CHOICES = [
        ('available', gettext_lazy('Disponible')),
        ('assigned', gettext_lazy('Asignado')),
        ('maintenance', gettext_lazy('En Mantenimiento')),
        ('retired', gettext_lazy('Dado de Baja')),
        ('lost', gettext_lazy('Perdido')),
        ('damaged', gettext_lazy('Dañado')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Activo'),
        help_text=gettext_lazy('Nombre descriptivo del activo')
    )
    manufacturer = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Fabricante'),
        help_text=gettext_lazy('Marca o fabricante del activo')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del activo')
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Número de Serie'),
        help_text=gettext_lazy('Número de serie único del activo')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name=gettext_lazy('Estado')
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets',
        verbose_name=gettext_lazy('Asignado a')
    )
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Compra')
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Precio de Compra')
    )
    warranty_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Vencimiento de Garantía')
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Ubicación'),
        help_text=gettext_lazy('Ubicación física del activo')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el activo')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assets',
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Activo')
        verbose_name_plural = gettext_lazy('Activos')
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.serial_number})"
    
    def get_status_display_color(self):
        """Retorna el color CSS para el estado"""
        colors = {
            'available': 'success',
            'assigned': 'primary',
            'maintenance': 'warning',
            'retired': 'secondary',
            'lost': 'danger',
            'damaged': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def is_available(self):
        """Verifica si el activo está disponible para asignación"""
        return self.status == 'available'
    
    def can_be_assigned(self):
        """Verifica si el activo puede ser asignado"""
        return self.status in ['available', 'assigned']
    
    def save(self, *args, **kwargs):
        """Override save para actualizar estado automáticamente"""
        # Si se está asignando a un usuario y el estado es 'available'
        if self.assigned_to and self.status == 'available':
            self.status = 'assigned'
        # Si se desasigna (assigned_to = None) y el estado es 'assigned'
        elif not self.assigned_to and self.status == 'assigned':
            self.status = 'available'
        
        super().save(*args, **kwargs)


class AssetHistory(models.Model):
    """Modelo para el historial de asignaciones de activos"""
    ACTION_CHOICES = [
        ('created', gettext_lazy('Creado')),
        ('assigned', gettext_lazy('Asignado')),
        ('unassigned', gettext_lazy('Desasignado')),
        ('transferred', gettext_lazy('Transferido')),
        ('maintenance', gettext_lazy('Enviado a Mantenimiento')),
        ('returned', gettext_lazy('Devuelto de Mantenimiento')),
        ('retired', gettext_lazy('Dado de Baja')),
        ('status_changed', gettext_lazy('Cambio de Estado')),
    ]
    
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=gettext_lazy('Activo')
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=gettext_lazy('Acción')
    )
    previous_employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_history_previous',
        verbose_name=gettext_lazy('Usuario Anterior')
    )
    new_employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_history_new',
        verbose_name=gettext_lazy('Nuevo Usuario')
    )
    previous_status = models.CharField(
        max_length=20,
        choices=Asset.STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Estado Anterior')
    )
    new_status = models.CharField(
        max_length=20,
        choices=Asset.STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Nuevo Estado')
    )
    reason = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Motivo'),
        help_text=gettext_lazy('Motivo del cambio o acción')
    )
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha')
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='asset_actions',
        verbose_name=gettext_lazy('Realizado por')
    )
    
    class Meta:
        ordering = ['-date']
        verbose_name = gettext_lazy('Historial de Activo')
        verbose_name_plural = gettext_lazy('Historiales de Activos')
        indexes = [
            models.Index(fields=['asset', '-date']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.asset.name} - {self.get_action_display()} ({self.date.strftime('%d/%m/%Y')})"
    
    def get_action_display_color(self):
        """Retorna el color CSS para la acción"""
        colors = {
            'created': 'success',
            'assigned': 'primary',
            'unassigned': 'warning',
            'transferred': 'info',
            'maintenance': 'warning',
            'returned': 'success',
            'retired': 'secondary',
            'status_changed': 'info',
        }
        return colors.get(self.action, 'secondary')


# ==========================================
# MODELOS PARA TUTOR IA
# ==========================================

class AITutor(models.Model):
    """Modelo para el sistema de Tutor IA"""
    
    STATUS_CHOICES = [
        ('active', gettext_lazy('Activo')),
        ('completed', gettext_lazy('Completado')),
        ('paused', gettext_lazy('Pausado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Objetivo'),
        help_text=gettext_lazy('Título descriptivo de lo que quieres lograr')
    )
    
    objective = models.TextField(
        verbose_name=gettext_lazy('Objetivo'),
        help_text=gettext_lazy('Describe claramente qué quieres lograr')
    )
    
    current_state = models.TextField(
        verbose_name=gettext_lazy('Estado Actual'),
        help_text=gettext_lazy('Describe dónde estás ahora en relación a tu objetivo')
    )
    
    context = models.TextField(
        verbose_name=gettext_lazy('Contexto'),
        help_text=gettext_lazy('Proporciona contexto adicional relevante (experiencia, recursos, limitaciones, etc.)')
    )
    
    tutor_persona = models.TextField(
        verbose_name=gettext_lazy('Personalidad del Tutor'),
        help_text=gettext_lazy('Describe qué tipo de tutor quieres (ej: un experimentado profesor de Django, un mentor de carrera, etc.)'),
        default='Un experimentado mentor y profesor'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=gettext_lazy('Estado')
    )
    
    is_private = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Privado'),
        help_text=gettext_lazy('Si está marcado, solo tú podrás ver este tutor')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_tutors',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Tutor IA')
        verbose_name_plural = gettext_lazy('Tutores IA')
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['status']),
            models.Index(fields=['is_private']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.created_by.username}"
    
    def get_status_display_color(self):
        """Retorna el color CSS para el estado"""
        colors = {
            'active': 'success',
            'completed': 'primary',
            'paused': 'warning',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def get_progress_count(self):
        """Retorna el número de reportes de progreso"""
        return self.progress_reports.count()


class AITutorProgressReport(models.Model):
    """Modelo para reportar avances al Tutor IA"""
    
    tutor = models.ForeignKey(
        AITutor,
        on_delete=models.CASCADE,
        related_name='progress_reports',
        verbose_name=gettext_lazy('Tutor IA')
    )
    
    progress_description = models.TextField(
        verbose_name=gettext_lazy('Descripción del Avance'),
        help_text=gettext_lazy('Describe qué has logrado desde tu último reporte')
    )
    
    challenges = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Desafíos Encontrados'),
        help_text=gettext_lazy('Describe los obstáculos o dificultades que has enfrentado (opcional)')
    )
    
    ai_feedback = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Retroalimentación de la IA'),
        help_text=gettext_lazy('Recomendaciones y consejos generados por la IA')
    )
    
    ai_recommendations = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Recomendaciones de Mejora'),
        help_text=gettext_lazy('Sugerencias específicas para mejorar')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutor_progress_reports',
        verbose_name=gettext_lazy('Reportado por')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha del Reporte')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Reporte de Progreso')
        verbose_name_plural = gettext_lazy('Reportes de Progreso')
        indexes = [
            models.Index(fields=['tutor']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"Reporte {self.pk} - {self.tutor.title}"


class AITutorAttachment(models.Model):
    """Modelo para adjuntos del Tutor IA"""
    
    tutor = models.ForeignKey(
        AITutor,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=gettext_lazy('Tutor IA'),
        null=True,
        blank=True
    )
    
    progress_report = models.ForeignKey(
        AITutorProgressReport,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=gettext_lazy('Reporte de Progreso'),
        null=True,
        blank=True
    )
    
    file = models.FileField(
        upload_to='tutor_attachments/%Y/%m/',
        verbose_name=gettext_lazy('Archivo')
    )
    
    original_filename = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre Original')
    )
    
    file_size = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Tamaño del Archivo'),
        help_text=gettext_lazy('Tamaño en bytes')
    )
    
    file_type = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Tipo de Archivo')
    )
    
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional del archivo')
    )
    
    ai_analysis = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Análisis de la IA'),
        help_text=gettext_lazy('Análisis del archivo generado por la IA')
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutor_attachments',
        verbose_name=gettext_lazy('Subido por')
    )
    
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Subida')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = gettext_lazy('Adjunto del Tutor')
        verbose_name_plural = gettext_lazy('Adjuntos del Tutor')
        indexes = [
            models.Index(fields=['tutor']),
            models.Index(fields=['progress_report']),
            models.Index(fields=['uploaded_by']),
        ]
    
    def __str__(self):
        return f"{self.original_filename}"
    
    def get_file_size_display(self):
        """Formato legible del tamaño del archivo"""
        size_bytes = self.file_size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower() if '.' in self.file.name else 'unknown'
        super().save(*args, **kwargs)


class ExpenseReport(models.Model):
    """Modelo para rendición de gastos de empleados"""
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('submitted', gettext_lazy('Enviado')),
        ('approved', gettext_lazy('Aprobado')),
        ('rejected', gettext_lazy('Rechazado')),
        ('paid', gettext_lazy('Pagado')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la rendición'),
        help_text=gettext_lazy('Título descriptivo de la rendición de gastos')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción general de los gastos')
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expense_reports',
        verbose_name=gettext_lazy('Empleado')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='expense_reports',
        verbose_name=gettext_lazy('Empresa'),
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    start_date = models.DateField(
        verbose_name=gettext_lazy('Fecha inicio'),
        help_text=gettext_lazy('Fecha de inicio del período de gastos')
    )
    end_date = models.DateField(
        verbose_name=gettext_lazy('Fecha fin'),
        help_text=gettext_lazy('Fecha de fin del período de gastos')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Monto total')
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name=gettext_lazy('Moneda')
    )
    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de envío')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_expense_reports',
        verbose_name=gettext_lazy('Aprobado por')
    )
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de aprobación')
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Motivo de rechazo')
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Referencia de pago')
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de pago')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Rendición de Gastos')
        verbose_name_plural = gettext_lazy('Rendiciones de Gastos')
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.employee.get_full_name() or self.employee.username}"
    
    def can_edit(self):
        """Verifica si la rendición puede ser editada"""
        return self.status in ['draft', 'rejected']
    
    def can_submit(self):
        """Verifica si la rendición puede ser enviada"""
        return self.status == 'draft' and self.expense_items.exists()
    
    def can_approve(self):
        """Verifica si la rendición puede ser aprobada"""
        return self.status == 'submitted'
    
    def calculate_total(self):
        """Calcula el total de todos los gastos"""
        total = self.expense_items.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return total
    
    def save(self, *args, **kwargs):
        # Actualizar total automáticamente
        super().save(*args, **kwargs)
        self.total_amount = self.calculate_total()
        if self.total_amount != 0:
            super().save(update_fields=['total_amount'])


class ExpenseItem(models.Model):
    """Modelo para items individuales de gastos"""
    CATEGORY_CHOICES = [
        ('food', gettext_lazy('Comida')),
        ('transport', gettext_lazy('Transporte')),
        ('hotel', gettext_lazy('Hotel/Alojamiento')),
        ('fuel', gettext_lazy('Combustible')),
        ('materials', gettext_lazy('Materiales')),
        ('entertainment', gettext_lazy('Entretenimiento')),
        ('communication', gettext_lazy('Comunicaciones')),
        ('office', gettext_lazy('Oficina/Suministros')),
        ('medical', gettext_lazy('Gastos médicos')),
        ('training', gettext_lazy('Capacitación')),
        ('direct_salary', gettext_lazy('Salarios Directos')),
        ('indirect_salary', gettext_lazy('Salarios Indirectos')),
        ('asset_purchase', gettext_lazy('Compra de Activos')),
        ('marketing', gettext_lazy('Marketing')),
        ('software', gettext_lazy('Software')),
        ('other', gettext_lazy('Otros')),
    ]
    
    expense_report = models.ForeignKey(
        ExpenseReport,
        on_delete=models.CASCADE,
        related_name='expense_items',
        verbose_name=gettext_lazy('Rendición de gastos')
    )
    date = models.DateField(
        verbose_name=gettext_lazy('Fecha del gasto')
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=gettext_lazy('Categoría')
    )
    description = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Descripción del gasto')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Monto')
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name=gettext_lazy('Moneda')
    )
    vendor = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Proveedor/Comercio')
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Ubicación')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Notas adicionales')
    )
    receipt_file = models.FileField(
        upload_to='expense_receipts/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Comprobante/Recibo')
    )
    is_reimbursable = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Reembolsable'),
        help_text=gettext_lazy('Marcar si este gasto debe ser reembolsado')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = gettext_lazy('Item de Gasto')
        verbose_name_plural = gettext_lazy('Items de Gastos')
        indexes = [
            models.Index(fields=['expense_report', 'category']),
            models.Index(fields=['date', 'category']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"
    
    def get_category_display_icon(self):
        """Retorna el icono correspondiente a la categoría"""
        icons = {
            'food': 'bi-cup-hot',
            'transport': 'bi-bus-front',
            'hotel': 'bi-building',
            'fuel': 'bi-fuel-pump',
            'materials': 'bi-tools',
            'entertainment': 'bi-music-note',
            'communication': 'bi-telephone',
            'office': 'bi-file-text',
            'medical': 'bi-heart-pulse',
            'training': 'bi-book',
            'direct_salary': 'bi-person-badge',
            'indirect_salary': 'bi-people',
            'asset_purchase': 'bi-box-seam',
            'marketing': 'bi-megaphone',
            'software': 'bi-code-square',
            'other': 'bi-three-dots',
        }
        return icons.get(self.category, 'bi-receipt')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el total de la rendición
        if self.expense_report:
            self.expense_report.save()


class ExpenseComment(models.Model):
    """Modelo para comentarios en rendiciones de gastos"""
    expense_report = models.ForeignKey(
        ExpenseReport,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Rendición de gastos')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario')
    )
    comment = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Comentario interno'),
        help_text=gettext_lazy('Solo visible para administradores')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Comentario de Gasto')
        verbose_name_plural = gettext_lazy('Comentarios de Gastos')
    
    def __str__(self):
        return f"Comentario de {self.user.get_full_name() or self.user.username} - {self.created_at.strftime('%d/%m/%Y')}"


class ExpenseFund(models.Model):
    """Modelo para registrar el dinero disponible/asignado a una rendición de gastos"""
    SOURCE_CHOICES = [
        ('cash', gettext_lazy('Efectivo')),
        ('bank_transfer', gettext_lazy('Transferencia Bancaria')),
        ('corporate_card', gettext_lazy('Tarjeta Corporativa')),
        ('advance', gettext_lazy('Anticipo de Viaje')),
        ('other', gettext_lazy('Otro')),
    ]

    expense_report = models.ForeignKey(
        ExpenseReport,
        on_delete=models.CASCADE,
        related_name='funds',
        verbose_name=gettext_lazy('Rendición de gastos')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Monto')
    )
    source_name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Fuente / Banco'),
        help_text=gettext_lazy('Ej: BBVA, efectivo, tarjeta corporativa…')
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='bank_transfer',
        verbose_name=gettext_lazy('Tipo de fuente')
    )
    invoice_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Referencia de factura / comprobante'),
        help_text=gettext_lazy('Número de factura, transferencia o comprobante')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Notas')
    )
    received_at = models.DateField(
        verbose_name=gettext_lazy('Fecha de recepción')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )

    class Meta:
        ordering = ['-received_at', '-created_at']
        verbose_name = gettext_lazy('Fondo de Rendición')
        verbose_name_plural = gettext_lazy('Fondos de Rendición')

    def __str__(self):
        return f"{self.amount} de {self.source_name} ({self.expense_report.title})"


class VideoMeeting(models.Model):
    """Modelo para gestionar reuniones de video y transcripciones"""
    MEETING_STATUS_CHOICES = [
        ('scheduled', gettext_lazy('Programada')),
        ('in_progress', gettext_lazy('En progreso')),
        ('completed', gettext_lazy('Completada')),
        ('cancelled', gettext_lazy('Cancelada')),
    ]
    
    TRANSCRIPTION_STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('processing', gettext_lazy('Procesando')),
        ('completed', gettext_lazy('Completada')),
        ('failed', gettext_lazy('Falló')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título de la reunión')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Descripción')
    )
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_video_meetings',
        verbose_name=gettext_lazy('Organizador')
    )
    participants = models.ManyToManyField(
        User,
        related_name='attended_meetings',
        blank=True,
        verbose_name=gettext_lazy('Participantes')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa')
    )
    scheduled_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha programada')
    )
    duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Duración en minutos')
    )
    status = models.CharField(
        max_length=20,
        choices=MEETING_STATUS_CHOICES,
        default='scheduled',
        verbose_name=gettext_lazy('Estado')
    )
    meeting_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('URL de la reunión')
    )
    
    # Archivo de video/audio
    recording_file = models.FileField(
        upload_to='meeting_recordings/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Archivo de grabación'),
        help_text=gettext_lazy('Formatos soportados: MP4, AVI, MOV, MP3, WAV, M4A, WebM')
    )
    
    # Transcripción
    transcription_status = models.CharField(
        max_length=20,
        choices=TRANSCRIPTION_STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado de transcripción')
    )
    transcription_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Transcripción')
    )
    transcription_confidence = models.FloatField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Confianza de transcripción (%)')
    )
    transcription_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de transcripción')
    )
    
    # Resumen automático generado por IA
    transcription_summary = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Resumen de transcripción')
    )
    
    # Resumen automático generado por IA
    ai_summary = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Resumen generado por IA')
    )
    
    # Puntos clave extraídos por IA
    key_points = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Puntos clave')
    )
    
    # Acciones identificadas por IA
    action_items = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Elementos de acción')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    
    class Meta:
        ordering = ['-scheduled_date', '-created_at']
        verbose_name = gettext_lazy('Reunión de Video')
        verbose_name_plural = gettext_lazy('Reuniones de Video')
    
    def __str__(self):
        return f"{self.title} - {self.organizer.get_full_name() or self.organizer.username}"
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            'scheduled': 'bg-primary',
            'in_progress': 'bg-warning',
            'completed': 'bg-success',
            'cancelled': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_status_color(self):
        """Retorna el color del badge para Bootstrap"""
        color_map = {
            'scheduled': 'primary',
            'in_progress': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return color_map.get(self.status, 'secondary')
    
    def get_transcription_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado de transcripción"""
        status_classes = {
            'pending': 'bg-secondary',
            'processing': 'bg-warning',
            'completed': 'bg-success',
            'failed': 'bg-danger',
        }
        return status_classes.get(self.transcription_status, 'bg-secondary')
    
    def can_edit(self):
        """Verifica si la reunión puede ser editada"""
        return self.status in ['scheduled', 'in_progress']
    
    def get_file_size_display(self):
        """Retorna el tamaño del archivo en formato legible"""
        if self.recording_file:
            try:
                size = self.recording_file.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    return f"{size / (1024 * 1024):.1f} MB"
                else:
                    return f"{size / (1024 * 1024 * 1024):.1f} GB"
            except:
                return "Tamaño desconocido"
        return None
    
    def get_duration_display(self):
        """Retorna la duración en formato legible"""
        if self.duration_minutes:
            hours = self.duration_minutes // 60
            minutes = self.duration_minutes % 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "Sin duración especificada"


class MeetingNote(models.Model):
    """Modelo para notas adicionales de reuniones"""
    meeting = models.ForeignKey(
        VideoMeeting,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=gettext_lazy('Reunión')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Contenido de la nota')
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Nota privada'),
        help_text=gettext_lazy('Solo visible para el autor')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Nota de Reunión')
        verbose_name_plural = gettext_lazy('Notas de Reunión')
    
    def __str__(self):
        return f"Nota de {self.user.get_full_name() or self.user.username} - {self.meeting.title}"


class MeetingAttachment(models.Model):
    """Modelo para archivos adjuntos de reuniones"""
    meeting = models.ForeignKey(
        VideoMeeting,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=gettext_lazy('Reunión')
    )
    file = models.FileField(
        upload_to='meeting_recordings/',
        verbose_name=gettext_lazy('Archivo adjunto')
    )
    filename = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre del archivo')
    )
    file_size = models.BigIntegerField(
        default=0,
        verbose_name=gettext_lazy('Tamaño del archivo (bytes)')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=gettext_lazy('Subido por')
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de subida')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = gettext_lazy('Adjunto de Reunión')
        verbose_name_plural = gettext_lazy('Adjuntos de Reunión')
    
    def __str__(self):
        return f"{self.filename} - {self.meeting.title}"
    
    def get_file_size_display(self):
        """Retorna el tamaño del archivo en formato legible"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class QuoteGenerator(models.Model):
    """Modelo para generar citas temáticas con IA"""
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del generador')
    )
    topic = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Tema de las citas'),
        help_text=gettext_lazy('Ej: "citas de Einstein sobre el amor", "frases motivacionales de líderes", etc.')
    )
    generated_quotes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Citas generadas (JSON)'),
        help_text=gettext_lazy('Almacena las citas en formato JSON')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está activo, las citas aparecerán en el dashboard')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Generador de Citas')
        verbose_name_plural = gettext_lazy('Generadores de Citas')
    
    def __str__(self):
        return f"{self.title} - {self.topic[:50]}"
    
    def get_quotes_list(self):
        """Obtiene las citas como lista de Python"""
        if self.generated_quotes:
            try:
                import json
                return json.loads(self.generated_quotes)
            except:
                return []
        return []
    
    def set_quotes_list(self, quotes_list):
        """Guarda las citas como JSON"""
        import json
        self.generated_quotes = json.dumps(quotes_list, ensure_ascii=False)


class CountdownTimer(models.Model):
    """Modelo para gestionar cuentas regresivas"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre descriptivo para la cuenta regresiva')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional del evento')
    )
    target_date = models.DateTimeField(
        verbose_name=gettext_lazy('Fecha objetivo'),
        help_text=gettext_lazy('Fecha y hora del evento')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está activo, la cuenta regresiva será visible')
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Privada'),
        help_text=gettext_lazy('Si está marcada como privada, solo el creador podrá verla')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    
    class Meta:
        ordering = ['target_date']
        verbose_name = gettext_lazy('Cuenta Regresiva')
        verbose_name_plural = gettext_lazy('Cuentas Regresivas')
    
    def __str__(self):
        return f"{self.title} - {self.target_date.strftime('%d/%m/%Y')}"
    
    def days_remaining(self):
        """Calcula los días restantes hasta la fecha objetivo"""
        from datetime import datetime
        now = timezone.now()
        if self.target_date > now:
            delta = self.target_date - now
            return delta.days
        else:
            return 0
    
    def is_expired(self):
        """Verifica si la fecha objetivo ya pasó"""
        return timezone.now() > self.target_date
    
    def time_remaining(self):
        """Retorna un diccionario con días, horas, minutos y segundos restantes"""
        from datetime import datetime
        now = timezone.now()
        if self.target_date > now:
            delta = self.target_date - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return {
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'total_seconds': delta.total_seconds()
            }
        else:
            return {
                'days': 0,
                'hours': 0,
                'minutes': 0,
                'seconds': 0,
                'total_seconds': 0
            }


class Procedure(models.Model):
    """Modelo para gestionar procedimientos/documentos de procesos"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo del procedimiento')
    )
    url = models.URLField(
        blank=True,
        verbose_name=gettext_lazy('URL'),
        help_text=gettext_lazy('Enlace externo relacionado al procedimiento (opcional)')
    )
    attachment = models.FileField(
        upload_to='procedures/',
        blank=True,
        verbose_name=gettext_lazy('Adjunto'),
        help_text=gettext_lazy('Archivo del procedimiento (PDF, DOC, etc.) - Opcional')
    )
    sequence = models.PositiveIntegerField(
        default=1,
        verbose_name=gettext_lazy('Secuencia'),
        help_text=gettext_lazy('Orden de visualización del procedimiento')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del procedimiento')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa a la que pertenece el procedimiento (opcional)'),
        related_name='procedures'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si está marcado, el procedimiento será visible')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por'),
        related_name='created_procedures'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de actualización')
    )
    
    class Meta:
        ordering = ['sequence', 'title']
        verbose_name = gettext_lazy('Procedimiento')
        verbose_name_plural = gettext_lazy('Procedimientos')
    
    def __str__(self):
        return f"{self.sequence}. {self.title}"
    
    def get_file_extension(self):
        """Retorna la extensión del archivo adjunto"""
        if self.attachment:
            return os.path.splitext(self.attachment.name)[1].lower()
        return ''
    
    def get_file_icon(self):
        """Retorna el icono apropiado según el tipo de archivo"""
        if not self.attachment:
            return 'bi-file-earmark'
        
        extension = self.get_file_extension()
        icons = {
            '.pdf': 'bi-file-earmark-pdf',
            '.doc': 'bi-file-earmark-word',
            '.docx': 'bi-file-earmark-word',
            '.xls': 'bi-file-earmark-excel',
            '.xlsx': 'bi-file-earmark-excel',
            '.ppt': 'bi-file-earmark-ppt',
            '.pptx': 'bi-file-earmark-ppt',
            '.txt': 'bi-file-earmark-text',
            '.jpg': 'bi-file-earmark-image',
            '.jpeg': 'bi-file-earmark-image',
            '.png': 'bi-file-earmark-image',
            '.gif': 'bi-file-earmark-image',
        }
        return icons.get(extension, 'bi-file-earmark')
    
    def get_file_size(self):
        """Retorna el tamaño del archivo en formato legible"""
        if not self.attachment:
            return "Sin archivo"
        
        if hasattr(self.attachment, 'size'):
            size = self.attachment.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "N/A"


class MonthlyCumplimiento(models.Model):
    """Modelo para gestionar metas de cumplimiento mensual"""
    FREQUENCY_CHOICES = [
        ('daily', gettext_lazy('Todos los días')),
        ('specific', gettext_lazy('Número específico de días')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la meta'),
        help_text=gettext_lazy('Ejemplo: Ejercicio diario, Lectura, Meditación')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario'),
        help_text=gettext_lazy('Usuario que debe cumplir esta meta'),
        related_name='monthly_cumplimientos'
    )
    frequency_type = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='daily',
        verbose_name=gettext_lazy('Tipo de frecuencia')
    )
    target_days = models.PositiveIntegerField(
        default=30,
        verbose_name=gettext_lazy('Días objetivo'),
        help_text=gettext_lazy('Número de días que debe cumplir en el mes (solo para tipo específico)')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada de la meta')
    )
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=gettext_lazy('ID público'),
        help_text=gettext_lazy('ID único para acceso público')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Cumplimiento Mensual')
        verbose_name_plural = gettext_lazy('Cumplimientos Mensuales')
        indexes = [
            models.Index(fields=['public_uuid']),
            models.Index(fields=['created_by', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user}"
    
    def get_public_url(self):
        """Retorna la URL pública para este cumplimiento"""
        from django.urls import reverse
        return reverse('monthly_cumplimiento_public', kwargs={'uuid': self.public_uuid})
    
    def get_current_month_progress(self):
        """Retorna el progreso del mes actual"""
        from datetime import date, timedelta
        today = date.today()
        current_month_start = today.replace(day=1)
        
        # Obtener cumplimientos del mes actual
        cumplimientos = self.daily_cumplimientos.filter(
            date__gte=current_month_start,
            date__year=today.year,
            date__month=today.month
        )
        
        completed_days = cumplimientos.filter(completed=True).count()
        
        # Calcular días transcurridos del mes (hasta hoy)
        days_elapsed = today.day
        
        # Total de días en el mes
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        
        total_days_in_month = (next_month - timedelta(days=1)).day
        
        # Meta de días (depende del tipo de frecuencia)
        if self.frequency_type == 'daily':
            target_days = days_elapsed  # Días transcurridos hasta hoy
            progress_base = days_elapsed  # Progreso basado en días transcurridos
        else:
            target_days = self.target_days  # Número específico de días
            progress_base = min(target_days, days_elapsed)  # Lo que menor sea
        
        # Calcular porcentaje de progreso
        if progress_base > 0:
            percentage = (completed_days / progress_base) * 100
        else:
            percentage = 0
        
        # Limitar el porcentaje al 100%
        percentage = min(percentage, 100)
        
        return {
            'completed_days': completed_days,
            'total_days_in_month': total_days_in_month,
            'days_elapsed': days_elapsed,
            'target_days': target_days,
            'remaining_days': max(target_days - completed_days, 0),
            'percentage': percentage
        }


class DailyCumplimiento(models.Model):
    """Modelo para registrar el cumplimiento diario"""
    monthly_cumplimiento = models.ForeignKey(
        MonthlyCumplimiento,
        on_delete=models.CASCADE,
        related_name='daily_cumplimientos',
        verbose_name=gettext_lazy('Cumplimiento mensual')
    )
    date = models.DateField(
        verbose_name=gettext_lazy('Fecha')
    )
    completed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Cumplido')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el cumplimiento de este día')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Registrado el')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Actualizado el')
    )
    
    class Meta:
        ordering = ['-date']
        verbose_name = gettext_lazy('Cumplimiento Diario')
        verbose_name_plural = gettext_lazy('Cumplimientos Diarios')
        unique_together = ['monthly_cumplimiento', 'date']
        indexes = [
            models.Index(fields=['monthly_cumplimiento', 'date']),
            models.Index(fields=['date', 'completed']),
        ]


class QRCode(models.Model):
    """Modelo para generar y almacenar códigos QR"""
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título'))
    content = models.TextField(verbose_name=gettext_lazy('Contenido'), help_text=gettext_lazy('URL, texto o datos para generar el QR'))
    description = models.TextField(blank=True, null=True, verbose_name=gettext_lazy('Descripción'))
    qr_type = models.CharField(
        max_length=20,
        choices=[
            ('url', gettext_lazy('URL/Enlace')),
            ('text', gettext_lazy('Texto')),
            ('email', gettext_lazy('Email')),
            ('phone', gettext_lazy('Teléfono')),
            ('sms', gettext_lazy('SMS')),
            ('wifi', gettext_lazy('WiFi')),
            ('vcard', gettext_lazy('Tarjeta de Contacto')),
        ],
        default='text',
        verbose_name=gettext_lazy('Tipo de QR')
    )
    size = models.IntegerField(default=256, verbose_name=gettext_lazy('Tamaño (px)'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=gettext_lazy('Creado por'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    
    # Campos para URL pública
    is_public = models.BooleanField(default=False, verbose_name=gettext_lazy('Público'))
    public_uuid = models.UUIDField(default=uuid.uuid4, null=True, blank=True, verbose_name=gettext_lazy('UUID público'))
    public_token = models.CharField(max_length=32, null=True, blank=True, unique=True, verbose_name=gettext_lazy('Token público'))
    public_views = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Vistas públicas'))

    def __str__(self):
        return f"{self.title} ({self.qr_type})"

    def get_formatted_content(self):
        """Retorna el contenido formateado según el tipo"""
        if self.qr_type == 'email':
            return f"mailto:{self.content}"
        elif self.qr_type == 'phone':
            return f"tel:{self.content}"
        elif self.qr_type == 'sms':
            return f"sms:{self.content}"
        elif self.qr_type == 'wifi':
            # Formato: WIFI:T:WPA;S:SSID;P:password;;
            return self.content
        else:
            return self.content
    
    def save(self, *args, **kwargs):
        # Generar token si se activa como público y no tiene token
        if self.is_public and not self.public_token:
            self.generate_public_token()
        # Limpiar token si se desactiva como público
        elif not self.is_public and self.public_token:
            self.public_token = None
        super().save(*args, **kwargs)
    
    def generate_public_token(self):
        """Genera un token único para acceso público"""
        import secrets
        import string
        
        while True:
            # Generar token de 16 caracteres alfanuméricos
            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            # Verificar que no existe otro token igual
            if not QRCode.objects.filter(public_token=token).exists():
                self.public_token = token
                break
        return token
    
    def get_public_url(self):
        """Retorna la URL pública para mostrar este QR"""
        from django.urls import reverse
        if self.is_public and self.public_token:
            return reverse('qr_public', kwargs={'token': self.public_token})
        return None

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Código QR')
        verbose_name_plural = gettext_lazy('Códigos QR')


class QuickTodo(models.Model):
    """Modelo para tareas rápidas (TODO list simple)"""
    text = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Tarea')
    )
    completed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Completada')
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['completed', '-created_at']
        verbose_name = gettext_lazy('Tarea Rápida')
        verbose_name_plural = gettext_lazy('Tareas Rápidas')
        indexes = [
            models.Index(fields=['created_by', 'completed']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.completed else "○"
        return f"{status} {self.text[:50]}..."


class Quotation(models.Model):
    """Modelo para gestionar cotizaciones"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('sent', gettext_lazy('Enviada')),
        ('approved', gettext_lazy('Aprobada')),
        ('rejected', gettext_lazy('Rechazada')),
        ('expired', gettext_lazy('Expirada')),
    ]
    
    # Secuencia automática
    sequence = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,
        verbose_name=gettext_lazy('Secuencia')
    )
    
    # Empresa cliente
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Empresa'),
        related_name='quotations'
    )
    
    # Vendedor (usuario)
    salesperson = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Vendedor'),
        related_name='quotations'
    )
    
    # Fecha de cotización
    date = models.DateField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha')
    )
    
    # Fecha de vencimiento (por defecto 30 días después de la fecha de cotización)
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de Vencimiento'),
        help_text=gettext_lazy('Fecha límite para aceptar esta cotización')
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Campos adicionales
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    # Fechas del servicio (opcional para servicios con duración específica)
    service_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de Inicio del Servicio'),
        help_text=gettext_lazy('Fecha en que comenzará el servicio (opcional)')
    )
    
    service_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de Fin del Servicio'), 
        help_text=gettext_lazy('Fecha estimada de finalización del servicio (opcional)')
    )
    
    # Token para acceso público
    public_token = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para compartir la cotización públicamente')
    )
    
    # Estado del cliente (respuesta pública)
    CLIENT_STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente de Respuesta')),
        ('accepted', gettext_lazy('Aceptada por Cliente')),
        ('rejected', gettext_lazy('Rechazada por Cliente')),
    ]
    
    client_status = models.CharField(
        max_length=20,
        choices=CLIENT_STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado del Cliente'),
        help_text=gettext_lazy('Estado de la respuesta del cliente a la cotización')
    )
    
    # Información de respuesta del cliente
    client_response_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre del Cliente'),
        help_text=gettext_lazy('Nombre de quien respondió a la cotización')
    )
    
    client_response_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email del Cliente'),
        help_text=gettext_lazy('Email de quien respondió a la cotización')
    )
    
    client_response_comments = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentarios del Cliente'),
        help_text=gettext_lazy('Comentarios adicionales del cliente')
    )
    
    client_response_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de Respuesta del Cliente'),
        help_text=gettext_lazy('Fecha y hora en que el cliente respondió')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Cotización')
        verbose_name_plural = gettext_lazy('Cotizaciones')
        indexes = [
            models.Index(fields=['sequence']),
            models.Index(fields=['company']),
            models.Index(fields=['salesperson']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.sequence:
            # Generar secuencia automática
            current_year = timezone.now().year
            last_quotation = Quotation.objects.filter(
                sequence__startswith=f'COT-{current_year}'
            ).order_by('-sequence').first()
            
            if last_quotation:
                last_number = int(last_quotation.sequence.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.sequence = f'COT-{current_year}-{new_number:04d}'
        
        # Calcular fecha de vencimiento si no está establecida
        if not self.expiry_date and self.date:
            from datetime import timedelta, datetime
            # Convertir self.date a objeto date si es string
            if isinstance(self.date, str):
                date_obj = datetime.strptime(self.date, '%Y-%m-%d').date()
            else:
                date_obj = self.date
            self.expiry_date = date_obj + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sequence} - {self.company.name}"
    
    def get_status_display_badge(self):
        """Retorna el estado con el badge HTML correspondiente"""
        badge_colors = {
            'draft': 'secondary',
            'sent': 'primary', 
            'approved': 'success',
            'rejected': 'danger',
            'expired': 'warning'
        }
        color = badge_colors.get(self.status, 'secondary')
        return f'<span class="badge bg-{color}">{self.get_status_display()}</span>'
    
    def get_total_amount(self):
        """Calcula el total de la cotización sumando todas las líneas"""
        total = self.lines.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total']
        return total or 0
    
    def get_lines_count(self):
        """Retorna el número de líneas de la cotización"""
        return self.lines.count()
    
    def generate_public_token(self):
        """Genera un token único para acceso público"""
        import uuid
        import hashlib
        
        if not self.public_token:
            # Generar token único basado en UUID y timestamp
            unique_string = f"{self.id}-{self.sequence}-{timezone.now().timestamp()}"
            token = hashlib.md5(unique_string.encode()).hexdigest()[:32]
            self.public_token = token
            self.save(update_fields=['public_token'])
        return self.public_token
    
    def get_public_url(self, request=None):
        """Retorna la URL pública de la cotización"""
        if not self.public_token:
            self.generate_public_token()
        
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(
                reverse('quotation_public_view', kwargs={'token': self.public_token})
            )
        return f"/quotations/public/{self.public_token}/"
    
    def can_be_responded(self):
        """Verifica si la cotización puede ser respondida (aceptada/rechazada)"""
        # Si el estado del cliente es 'pending', siempre se permite responder
        # independientemente del estado interno
        return self.client_status == 'pending' and not self.is_expired()
    
    def is_expired(self):
        """Verifica si la cotización está vencida"""
        if not self.expiry_date:
            return False
        from datetime import date
        return date.today() > self.expiry_date
    
    def get_days_until_expiry(self):
        """Retorna los días restantes hasta el vencimiento"""
        if not self.expiry_date:
            return None
        from datetime import date
        days_left = (self.expiry_date - date.today()).days
        return days_left if days_left >= 0 else 0
    
    def get_expiry_status_display(self):
        """Retorna el estado de vencimiento con formato"""
        if not self.expiry_date:
            return "Sin fecha de vencimiento"
        
        days_left = self.get_days_until_expiry()
        if days_left is None:
            return "Sin fecha de vencimiento"
        elif days_left == 0:
            return "Vence hoy"
        elif days_left < 0:
            return f"Vencida hace {abs(days_left)} días"
        elif days_left <= 3:
            return f"Vence en {days_left} días (¡Urgente!)"
        elif days_left <= 7:
            return f"Vence en {days_left} días"
        else:
            return f"Vence en {days_left} días"
    
    def get_client_status_display_badge(self):
        """Retorna el estado del cliente con el badge HTML correspondiente"""
        badge_colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger'
        }
        color = badge_colors.get(self.client_status, 'secondary')
        return f'<span class="badge bg-{color}">{self.get_client_status_display()}</span>'


class QuotationView(models.Model):
    """Modelo para registrar las visitas a las cotizaciones publicas"""
    
    quotation = models.ForeignKey(
        'Quotation',
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Cotizacion'),
        related_name='views'
    )
    
    viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Visita')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Direccion IP'),
        null=True,
        blank=True
    )
    
    country = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Pais'),
        blank=True,
        help_text=gettext_lazy('Pais desde donde se accedio')
    )
    
    country_code = models.CharField(
        max_length=2,
        verbose_name=gettext_lazy('Codigo de Pais'),
        blank=True,
        help_text=gettext_lazy('Codigo ISO del pais (ej: US, MX, ES)')
    )
    
    user_agent = models.TextField(
        verbose_name=gettext_lazy('Navegador/Dispositivo'),
        blank=True
    )
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = gettext_lazy('Visita a Cotizacion')
        verbose_name_plural = gettext_lazy('Visitas a Cotizaciones')
        indexes = [
            models.Index(fields=['quotation']),
            models.Index(fields=['viewed_at']),
            models.Index(fields=['country']),
        ]
    
    def __str__(self):
        return f"{self.quotation.sequence} - {self.viewed_at.strftime('%Y-%m-%d %H:%M')} - {self.country or 'Desconocido'}"


class QuotationLine(models.Model):
    """Modelo para las líneas de productos en una cotización"""
    
    quotation = models.ForeignKey(
        'Quotation',
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Cotización'),
        related_name='lines'
    )
    
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Producto')
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name=gettext_lazy('Cantidad')
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Precio Unitario')
    )
    
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Descuento (%)'),
        help_text=gettext_lazy('Porcentaje de descuento sobre el precio unitario')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción adicional o personalizada del producto')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['id']
        verbose_name = gettext_lazy('Línea de Cotización')
        verbose_name_plural = gettext_lazy('Líneas de Cotización')
        indexes = [
            models.Index(fields=['quotation']),
            models.Index(fields=['product']),
        ]
    
    def save(self, *args, **kwargs):
        # Si no se ha establecido el precio unitario, usar el precio del producto
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
    
    def get_subtotal(self):
        """Calcula el subtotal de la línea (cantidad × precio unitario)"""
        return self.quantity * self.unit_price
    
    def get_discount_amount(self):
        """Calcula el monto del descuento"""
        return self.get_subtotal() * (self.discount_percentage / 100)
    
    def get_total(self):
        """Calcula el total de la línea (subtotal - descuento)"""
        return self.get_subtotal() - self.get_discount_amount()
    
    def __str__(self):
        return f"{self.quotation.sequence} - {self.product.name} (x{self.quantity})"


class QuotationTemplate(models.Model):
    """Modelo para plantillas de cotización que se pueden compartir públicamente"""
    
    # Cotización base que sirve como plantilla
    template_quotation = models.ForeignKey(
        'Quotation',
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Cotización Plantilla'),
        related_name='public_templates'
    )
    
    # Token público único para acceder al formulario
    public_token = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para el enlace público')
    )
    
    # Información del enlace
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Enlace'),
        help_text=gettext_lazy('Título descriptivo para el cliente')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción que verá el cliente al acceder al enlace')
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo'),
        help_text=gettext_lazy('Si el enlace está activo y acepta nuevas solicitudes')
    )
    
    # Estadísticas
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de Vistas'),
        help_text=gettext_lazy('Cuántas veces se ha visitado el enlace')
    )
    
    conversions_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Conversiones'),
        help_text=gettext_lazy('Cuántas cotizaciones se han generado desde este enlace')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por'),
        related_name='quotation_templates'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Plantilla de Cotización Pública')
        verbose_name_plural = gettext_lazy('Plantillas de Cotización Públicas')
        indexes = [
            models.Index(fields=['public_token']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.public_token:
            # Generar token único
            import uuid
            import hashlib
            unique_string = f"{self.template_quotation.id}-{self.title}-{timezone.now().timestamp()}"
            token = hashlib.md5(unique_string.encode()).hexdigest()[:32]
            self.public_token = token
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.template_quotation.sequence}"
    
    def get_public_url(self, request=None):
        """Retorna la URL pública del formulario"""
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(
                reverse('quotation_template_public_form', kwargs={'token': self.public_token})
            )
        return f"/quotations/template/{self.public_token}/"
    
    def increment_views(self):
        """Incrementa el contador de vistas"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_conversions(self):
        """Incrementa el contador de conversiones"""
        self.conversions_count += 1
        self.save(update_fields=['conversions_count'])


class QuotationTemplateRequest(models.Model):
    """Solicitudes generadas desde plantillas públicas"""
    
    # Plantilla que generó esta solicitud
    template = models.ForeignKey(
        'QuotationTemplate',
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Plantilla'),
        related_name='requests'
    )
    
    # Datos del cliente
    client_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Cliente')
    )
    
    client_email = models.EmailField(
        verbose_name=gettext_lazy('Email del Cliente')
    )
    
    client_phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Teléfono del Cliente')
    )
    
    client_company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Empresa del Cliente')
    )
    
    # Comentarios del cliente
    client_comments = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentarios del Cliente')
    )
    
    # Cotización generada
    generated_quotation = models.ForeignKey(
        'Quotation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Cotización Generada'),
        related_name='template_requests'
    )
    
    # Estado
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('processed', gettext_lazy('Procesada')),
        ('quoted', gettext_lazy('Cotizada')),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de solicitud')
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de procesamiento')
    )
    
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Procesado por'),
        related_name='processed_template_requests'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Solicitud de Plantilla')
        verbose_name_plural = gettext_lazy('Solicitudes de Plantillas')
        indexes = [
            models.Index(fields=['template']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.client_name} - {self.template.title}"
    
    def process_request(self, processed_by_user):
        """Procesa la solicitud creando una cotización personalizada"""
        try:
            # Crear la empresa del cliente si no existe, o actualizar contacto si existe
            from .models import Company
            
            company, created = Company.objects.get_or_create(
                email=self.client_email,
                defaults={
                    'name': self.client_company or f"Empresa de {self.client_name}",
                    'phone': self.client_phone or '',
                    'address': '',
                    'description': f'Cliente generado automáticamente desde plantilla: {self.template.title}. Contacto: {self.client_name}',
                    'is_active': True,
                }
            )
            
            # Si la empresa ya existía, actualizar datos de contacto
            if not created:
                if self.client_phone:
                    company.phone = self.client_phone
                if self.client_company:
                    company.name = self.client_company
                # Actualizar descripción para incluir el nuevo contacto
                company.description = f'Cliente generado automáticamente desde plantilla: {self.template.title}. Contacto: {self.client_name}'
                company.save()
            
            # Crear la nueva cotización basada en la plantilla
            template_quotation = self.template.template_quotation
            new_quotation = Quotation.objects.create(
                company=company,
                salesperson=processed_by_user,
                date=timezone.now().date(),
                status='sent',  # La enviamos directamente
                client_status='pending',  # Pendiente de respuesta del cliente
                description=f"Cotización generada automáticamente para {self.client_name}\n\nComentarios del cliente:\n{self.client_comments}" if self.client_comments else f"Cotización generada automáticamente para {self.client_name}",
            )
            
            # Copiar las líneas de la plantilla
            for line in template_quotation.lines.all():
                new_quotation.lines.create(
                    product=line.product,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    discount_percentage=line.discount_percentage,
                    description=line.description
                )
            
            # Generar token público para la nueva cotización
            new_quotation.generate_public_token()
            
            # Actualizar esta solicitud
            self.generated_quotation = new_quotation
            self.status = 'quoted'
            self.processed_at = timezone.now()
            self.processed_by = processed_by_user
            self.save()
            
            # Incrementar contador de conversiones
            self.template.increment_conversions()
            
            return new_quotation
            
        except Exception as e:
            # Marcar como procesada con error
            self.status = 'processed'
            self.processed_at = timezone.now()
            self.processed_by = processed_by_user
            self.save()
            raise e


class CrmQuestion(models.Model):
    """Modelo para gestionar preguntas del CRM"""
    
    sequence = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Secuencia'),
        help_text=gettext_lazy('Número de secuencia de la pregunta')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='crm_questions',
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa asociada a la pregunta')
    )
    question = models.TextField(
        verbose_name=gettext_lazy('Pregunta'),
        help_text=gettext_lazy('Contenido de la pregunta')
    )
    answer = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Respuesta'),
        help_text=gettext_lazy('Respuesta a la pregunta')
    )
    person_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la persona'),
        help_text=gettext_lazy('Nombre completo de quien hace la pregunta')
    )
    person_email = models.EmailField(
        verbose_name=gettext_lazy('Email de la persona'),
        help_text=gettext_lazy('Correo electrónico de quien hace la pregunta')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='crm_questions_created',
        verbose_name=gettext_lazy('Creado por'),
        help_text=gettext_lazy('Usuario que creó la pregunta (NULL para preguntas públicas)')
    )
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_questions_answered',
        verbose_name=gettext_lazy('Respondido por')
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de respuesta')
    )
    
    class Meta:
        ordering = ['sequence', '-created_at']
        verbose_name = gettext_lazy('Pregunta CRM')
        verbose_name_plural = gettext_lazy('Preguntas CRM')
        unique_together = [['company', 'sequence']]
    
    def __str__(self):
        return f"#{self.sequence} - {self.person_name} ({self.company.name})"
    
    def save(self, *args, **kwargs):
        # Auto-asignar secuencia si no está definida
        if not self.sequence:
            last_question = CrmQuestion.objects.filter(company=self.company).order_by('-sequence').first()
            self.sequence = (last_question.sequence + 1) if last_question else 1
        
        # Manejar el estado de la respuesta automáticamente
        if self.answer and self.answer.strip():
            # Si hay respuesta y no estaba respondida antes
            if not self.answered_at:
                self.answered_at = timezone.now()
            # Si no hay usuario que respondió asignado, mantener el que ya estaba
            # (esto se manejará en las vistas para asignar el usuario correcto)
        else:
            # Si se borra la respuesta, limpiar campos relacionados
            self.answered_at = None
            self.answered_by = None
        
        super().save(*args, **kwargs)
    
    @property
    def is_answered(self):
        """Retorna True si la pregunta ya fue respondida"""
        return bool(self.answer and self.answer.strip())
    
    @property
    def is_public_question(self):
        """Retorna True si es una pregunta pública (sin usuario creador)"""
        return self.created_by is None
    
    def get_creator_display(self):
        """Retorna información sobre quién creó la pregunta"""
        if self.is_public_question:
            return "Pregunta Pública"
        else:
            if self.created_by:
                return self.created_by.get_full_name() or self.created_by.username
            return "Usuario no disponible"
    
    def get_origin_badge_class(self):
        """Retorna la clase CSS para el badge de origen"""
        return "bg-success" if self.is_public_question else "bg-primary"
    
    def get_origin_icon(self):
        """Retorna el icono para el origen de la pregunta"""
        return "fas fa-globe" if self.is_public_question else "fas fa-user-tie"
    
    def get_answered_by_display(self):
        """Retorna información sobre quién respondió la pregunta"""
        if not self.answered_by:
            return "Usuario no disponible"
        return self.answered_by.get_full_name() or self.answered_by.username
    
    def mark_as_answered(self, user, answer_text):
        """Marca la pregunta como respondida con el texto y usuario especificado"""
        self.answer = answer_text
        self.answered_by = user
        self.answered_at = timezone.now()
        self.save()
    
    def mark_as_pending(self):
        """Marca la pregunta como pendiente (sin respuesta)"""
        self.answer = None
        self.answered_by = None
        self.answered_at = None
        self.save()
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        return "bg-success" if self.is_answered else "bg-warning"
    
    def get_status_icon(self):
        """Retorna el icono FontAwesome para el estado"""
        return "fas fa-check" if self.is_answered else "fas fa-clock"
    
    @property
    def status_display(self):
        """Retorna el estado de la pregunta para mostrar"""
        return "Respondida" if self.is_answered else "Pendiente"
    
    @property
    def status_color(self):
        """Retorna el color del estado para la UI"""
        return "success" if self.is_answered else "warning"


class SupportMeeting(models.Model):
    """Modelo para gestionar reuniones de soporte"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa para la cual se realiza la reunión')
    )
    sequence = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Secuencia'),
        help_text=gettext_lazy('Número secuencial de la reunión')
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha'),
        help_text=gettext_lazy('Fecha de la reunión')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por'),
        help_text=gettext_lazy('Usuario que creó la reunión')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción de lo que se vio en la reunión')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['company', '-sequence']
        verbose_name = gettext_lazy('Reunión de Soporte')
        verbose_name_plural = gettext_lazy('Reuniones de Soporte')
        unique_together = [['company', 'sequence']]
    
    def __str__(self):
        return f"#{self.sequence} - {self.company.name} ({self.date})"
    
    def save(self, *args, **kwargs):
        # Auto-asignar secuencia si no está definida
        if not self.sequence:
            last_meeting = SupportMeeting.objects.filter(company=self.company).order_by('-sequence').first()
            self.sequence = (last_meeting.sequence + 1) if last_meeting else 1
        
        super().save(*args, **kwargs)
    
    @property
    def points_count(self):
        """Retorna el número total de puntos de la reunión"""
        return self.support_meeting_points.count()
    
    @property
    def selected_points_count(self):
        """Retorna el número de puntos seleccionados"""
        return self.support_meeting_points.filter(is_selected=True).count()


class SupportMeetingPoint(models.Model):
    """Modelo para los puntos de las reuniones de soporte"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('completed', gettext_lazy('Completado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    meeting = models.ForeignKey(
        SupportMeeting,
        on_delete=models.CASCADE,
        related_name='support_meeting_points',
        verbose_name=gettext_lazy('Reunión')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción del punto'),
        help_text=gettext_lazy('Descripción detallada del punto')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado'),
        help_text=gettext_lazy('Estado actual del punto')
    )
    is_selected = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Seleccionado'),
        help_text=gettext_lazy('Marcar para crear como ticket')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Punto de Reunión')
        verbose_name_plural = gettext_lazy('Puntos de Reunión')
    
    def __str__(self):
        return f"{self.meeting} - {self.description[:50]}..."
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge del estado"""
        status_classes = {
            'pending': 'bg-secondary',
            'in_progress': 'bg-warning',
            'completed': 'bg-success',
            'cancelled': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')


class SupportMeetingPublicLink(models.Model):
    """Modelo para enlaces públicos de reuniones de soporte"""
    
    meeting = models.OneToOneField(
        SupportMeeting,
        on_delete=models.CASCADE,
        related_name='public_link',
        verbose_name=gettext_lazy('Reunión')
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=gettext_lazy('Token de acceso')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    show_company_meetings = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Mostrar otras reuniones de la empresa'),
        help_text=gettext_lazy('Si está marcado, se mostrarán todas las reuniones públicas de la empresa')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Creado por')
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Último acceso')
    )
    access_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Número de accesos')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Enlace Público de Reunión')
        verbose_name_plural = gettext_lazy('Enlaces Públicos de Reuniones')
    
    def __str__(self):
        return f"Enlace público - {self.meeting}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def get_public_url(self, request=None):
        """Obtener URL pública completa"""
        from django.urls import reverse
        from django.conf import settings
        
        if request:
            # Si tenemos request, usar el host actual
            base_url = f"{request.scheme}://{request.get_host()}"
        else:
            # Fallback para cuando no hay request
            base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        
        path = reverse('support_meeting_public', kwargs={'token': self.token})
        return f"{base_url}{path}"
    
    def register_access(self):
        """Registrar un acceso al enlace"""
        from django.utils import timezone
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])


class EmailTemplate(models.Model):
    """Modelo para plantillas de correo electrónico"""
    
    CATEGORY_CHOICES = [
        ('general', gettext_lazy('General')),
        ('ventas', gettext_lazy('Ventas')),
        ('soporte', gettext_lazy('Soporte')),
        ('marketing', gettext_lazy('Marketing')),
        ('seguimiento', gettext_lazy('Seguimiento')),
        ('recordatorio', gettext_lazy('Recordatorio')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título descriptivo de la plantilla')
    )
    body = models.TextField(
        verbose_name=gettext_lazy('Cuerpo del mensaje'),
        help_text=gettext_lazy('Contenido del correo electrónico')
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name=gettext_lazy('Categoría')
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de visualización (menor número = mayor prioridad)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_email_templates',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = gettext_lazy('Plantilla de Correo')
        verbose_name_plural = gettext_lazy('Plantillas de Correo')
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class EmailTemplateHistory(models.Model):
    """Modelo para historial de cambios de plantillas de correo"""
    
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=gettext_lazy('Plantilla')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    body = models.TextField(
        verbose_name=gettext_lazy('Cuerpo del mensaje')
    )
    category = models.CharField(
        max_length=50,
        verbose_name=gettext_lazy('Categoría')
    )
    order = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Orden')
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Modificado por')
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de modificación')
    )
    change_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Motivo del cambio')
    )
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = gettext_lazy('Historial de Plantilla')
        verbose_name_plural = gettext_lazy('Historiales de Plantillas')
    
    def __str__(self):
        return f"{self.template.title} - {self.changed_at.strftime('%d/%m/%Y %H:%M')}"


class Counter(models.Model):
    """Modelo para contadores diarios"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre del contador')
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Valor'),
        help_text=gettext_lazy('Valor del contador')
    )
    date = models.DateField(
        verbose_name=gettext_lazy('Fecha'),
        help_text=gettext_lazy('Fecha del contador')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='counters',
        verbose_name=gettext_lazy('Usuario')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales (opcional)')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-date', 'title']
        verbose_name = gettext_lazy('Contador')
        verbose_name_plural = gettext_lazy('Contadores')
        unique_together = ['title', 'date', 'user']
    
    def __str__(self):
        return f"{self.title} - {self.value} ({self.date.strftime('%d/%m/%Y')})"


class CounterHistory(models.Model):
    """Modelo para historial de cambios en contadores"""
    
    counter = models.ForeignKey(
        Counter,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=gettext_lazy('Contador')
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=gettext_lazy('Valor'),
        help_text=gettext_lazy('Valor ingresado')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas sobre este cambio (opcional)')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='counter_history',
        verbose_name=gettext_lazy('Usuario'),
        help_text=gettext_lazy('Usuario que realizó el cambio')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha y hora')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Historial de Contador')
        verbose_name_plural = gettext_lazy('Historiales de Contadores')
    
    def __str__(self):
        return f"{self.counter.title} - {self.value} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"


class OCRInvoice(models.Model):
    """Modelo para facturas procesadas con OCR"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('scanned', gettext_lazy('Escaneado')),
        ('downloaded', gettext_lazy('Descargada')),
    ]
    
    sequence_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=gettext_lazy('Número de Secuencia'),
        help_text=gettext_lazy('Número de secuencia interno autogenerado')
    )
    number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Número de Factura'),
        help_text=gettext_lazy('Número de la factura (se extrae automáticamente del OCR)')
    )
    supplier = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Proveedor'),
        help_text=gettext_lazy('Nombre del proveedor (se extrae automáticamente del OCR)')
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        verbose_name=gettext_lazy('Importe'),
        help_text=gettext_lazy('Importe total de la factura (se extrae automáticamente del OCR)')
    )
    neto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        verbose_name=gettext_lazy('Neto'),
        help_text=gettext_lazy('Importe neto sin impuestos')
    )
    impuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        verbose_name=gettext_lazy('Impuesto'),
        help_text=gettext_lazy('Importe del impuesto (IVA, etc.)')
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        verbose_name=gettext_lazy('Total'),
        help_text=gettext_lazy('Importe total con impuestos')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    image = models.ImageField(
        upload_to='invoices/%Y/%m/',
        verbose_name=gettext_lazy('Imagen de la factura'),
        help_text=gettext_lazy('Imagen escaneada de la factura')
    )
    json_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Datos OCR'),
        help_text=gettext_lazy('Datos extraídos por OCR en formato JSON')
    )
    public_token = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Token público'),
        help_text=gettext_lazy('Token para acceso público y API')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_invoices',
        verbose_name=gettext_lazy('Subido por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    downloaded = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Descargada'),
        help_text=gettext_lazy('Indica si la factura ha sido descargada vía API')
    )
    downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de descarga'),
        help_text=gettext_lazy('Fecha y hora en que se descargó la factura por primera vez')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Factura OCR')
        verbose_name_plural = gettext_lazy('Facturas OCR')
    
    def __str__(self):
        number = self.number or 'Sin número'
        supplier = self.supplier or 'Sin proveedor'
        total = self.total or self.amount or 0
        return f"{number} - {supplier} - ${total}"
    
    def save(self, *args, **kwargs):
        # Generar token público si no existe
        if not self.public_token:
            import secrets
            self.public_token = secrets.token_urlsafe(32)
        
        # Generar número de secuencia si no existe
        if not self.sequence_number:
            # Obtener el último número de secuencia
            last_invoice = OCRInvoice.objects.order_by('-id').first()
            
            if last_invoice and last_invoice.id:
                new_num = last_invoice.id + 1
            else:
                new_num = 1
            
            self.sequence_number = str(new_num)
        
        super().save(*args, **kwargs)
    
    def get_public_url(self):
        """Retorna la URL pública para subir facturas"""
        from django.urls import reverse
        return reverse('ocr_invoice_public_upload', kwargs={'token': self.public_token})
    
    def get_api_url(self):
        """Retorna la URL de la API para consumir la factura"""
        from django.urls import reverse
        return reverse('ocr_invoice_api', kwargs={'token': self.public_token})


class ScheduledTask(models.Model):
    """Modelo para tareas programadas"""
    
    FREQUENCY_UNIT_CHOICES = [
        ('minute', gettext_lazy('Minuto')),
        ('hour', gettext_lazy('Hora')),  
        ('day', gettext_lazy('Día')),
        ('month', gettext_lazy('Mes')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Tarea')
    )
    frequency = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Frecuencia'),
        help_text=gettext_lazy('Cada cuántas unidades de tiempo se ejecuta')
    )
    frequency_unit = models.CharField(
        max_length=10,
        choices=FREQUENCY_UNIT_CHOICES,
        default='hour',
        verbose_name=gettext_lazy('Unidad de Frecuencia')
    )
    code = models.TextField(
        verbose_name=gettext_lazy('Código a Ejecutar'),
        help_text=gettext_lazy('Código Python que se ejecutará en cada iteración')
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Activo')
    )
    last_execution = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última Ejecución')
    )
    last_result = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Último Resultado'),
        help_text=gettext_lazy('Resultado de la última ejecución')
    )
    success_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Ejecuciones Exitosas')
    )
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Ejecuciones con Error')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_scheduled_tasks',
        verbose_name=gettext_lazy('Creado por')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Tarea Programada')
        verbose_name_plural = gettext_lazy('Tareas Programadas')
    
    def __str__(self):
        return f"{self.name} (cada {self.frequency} {self.get_frequency_unit_display().lower()})"
    
    def get_next_execution(self):
        """Calcula cuándo debe ejecutarse la próxima vez"""
        if not self.last_execution:
            return timezone.now()
        
        if self.frequency_unit == 'minute':
            delta = timedelta(minutes=self.frequency)
        elif self.frequency_unit == 'hour':
            delta = timedelta(hours=self.frequency)
        elif self.frequency_unit == 'day':
            delta = timedelta(days=self.frequency)
        elif self.frequency_unit == 'month':
            delta = timedelta(days=self.frequency * 30)  # Aproximado
        else:
            delta = timedelta(hours=1)
            
        return self.last_execution + delta
    
    def should_execute(self):
        """Verifica si la tarea debe ejecutarse"""
        if not self.is_active:
            return False
        return timezone.now() >= self.get_next_execution()


class ScheduledTaskExecution(models.Model):
    """Historial de ejecuciones de tareas programadas"""
    
    STATUS_CHOICES = [
        ('success', gettext_lazy('Exitosa')),
        ('error', gettext_lazy('Error')),
        ('timeout', gettext_lazy('Timeout')),
    ]
    
    task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name=gettext_lazy('Tarea')
    )
    executed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Ejecutado en')
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name=gettext_lazy('Estado')
    )
    result = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Resultado')
    )
    execution_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Tiempo de Ejecución (segundos)')
    )
    
    class Meta:
        ordering = ['-executed_at']
        verbose_name = gettext_lazy('Ejecución de Tarea')
        verbose_name_plural = gettext_lazy('Ejecuciones de Tareas')
    
    def __str__(self):
        return f"{self.task.name} - {self.executed_at.strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"


class CourseRating(models.Model):
    """Modelo para calificaciones de cursos con caras (triste, neutro, feliz)"""
    
    RATING_CHOICES = [
        ('sad', gettext_lazy('😞 Triste')),
        ('neutral', gettext_lazy('😐 Neutro')),
        ('happy', gettext_lazy('😊 Feliz')),
    ]
    
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name=gettext_lazy('Curso')
    )
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        verbose_name=gettext_lazy('Calificación')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Calificación de Curso')
        verbose_name_plural = gettext_lazy('Calificaciones de Cursos')
    
    def __str__(self):
        return f"{self.get_rating_display()} - {self.course.title}"


class QARating(models.Model):
    """Modelo para calificaciones de QA con caras (triste, neutro, feliz)"""
    
    RATING_CHOICES = [
        ('sad', gettext_lazy('😞 Triste')),
        ('neutral', gettext_lazy('😐 Neutro')),
        ('happy', gettext_lazy('😊 Feliz')),
    ]
    
    # Calificación principal
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        verbose_name=gettext_lazy('Calificación'),
        help_text=gettext_lazy('Calificación: triste, neutro o feliz')
    )
    
    # Opinión
    opinion = models.TextField(
        verbose_name=gettext_lazy('Opinión'),
        help_text=gettext_lazy('Tu opinión sobre el servicio de QA')
    )
    
    # Información opcional del usuario
    name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre'),
        help_text=gettext_lazy('Tu nombre (opcional)')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Correo electrónico'),
        help_text=gettext_lazy('Tu correo electrónico (opcional)')
    )
    
    # Relación opcional con empresa
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qa_ratings',
        verbose_name=gettext_lazy('Empresa'),
        help_text=gettext_lazy('Empresa asociada a esta calificación (opcional)')
    )
    
    # Usuario registrado (si aplica)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qa_ratings',
        verbose_name=gettext_lazy('Usuario'),
        help_text=gettext_lazy('Usuario registrado que dejó la calificación')
    )
    
    # Metadatos
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP'),
        help_text=gettext_lazy('IP desde donde se realizó la calificación')
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('User Agent'),
        help_text=gettext_lazy('Información del navegador')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Visible públicamente'),
        help_text=gettext_lazy('Si la calificación puede mostrarse públicamente')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Calificación QA')
        verbose_name_plural = gettext_lazy('Calificaciones QA')
    
    def __str__(self):
        name_display = self.name or self.email or 'Anónimo'
        return f"{name_display} - {self.get_rating_display()} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def get_rating_emoji(self):
        """Devuelve el emoji correspondiente a la calificación"""
        emojis = {
            'sad': '😞',
            'neutral': '😐',
            'happy': '😊',
        }
        return emojis.get(self.rating, '😐')
    
    def get_rating_color(self):
        """Devuelve el color correspondiente a la calificación"""
        colors = {
            'sad': '#dc3545',      # Rojo
            'neutral': '#ffc107',  # Amarillo
            'happy': '#28a745',    # Verde
        }
        return colors.get(self.rating, '#6c757d')


class GameCounter(models.Model):
    """Modelo para contador de juegos de pádel"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('finished', gettext_lazy('Finalizado')),
    ]
    
    # Información del juego
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Juego'),
        help_text=gettext_lazy('Nombre descriptivo del juego (ej: Final Torneo 2025)')
    )
    player1_name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Jugador 1'),
        help_text=gettext_lazy('Nombre del primer jugador')
    )
    player2_name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Jugador 2'),
        help_text=gettext_lazy('Nombre del segundo jugador')
    )
    
    # Puntuación
    player1_score = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Puntos Jugador 1')
    )
    player2_score = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Puntos Jugador 2')
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado del Juego')
    )
    
    # URL pública
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('UUID Público'),
        help_text=gettext_lazy('Identificador único para acceso público')
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_games',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='games',
        verbose_name=gettext_lazy('Empresa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de inicio')
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de finalización')
    )
    
    # Configuración opcional
    max_points = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Puntos máximos'),
        help_text=gettext_lazy('0 = sin límite')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el juego')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Contador de Juego')
        verbose_name_plural = gettext_lazy('Contadores de Juegos')
    
    def __str__(self):
        return f"{self.name} - {self.player1_name} vs {self.player2_name}"
    
    def get_public_url(self):
        """Devuelve la URL pública del juego"""
        from django.urls import reverse
        return reverse('game_counter_public', kwargs={'uuid': self.public_uuid})
    
    def start_game(self):
        """Inicia el juego"""
        if self.status == 'pending':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()
    
    def finish_game(self):
        """Finaliza el juego"""
        if self.status == 'in_progress':
            self.status = 'finished'
            self.finished_at = timezone.now()
            self.save()
    
    def add_point_player1(self):
        """Añade un punto al jugador 1"""
        self.player1_score += 1
        self.save()
        
        # Auto-finalizar si alcanza max_points
        if self.max_points > 0 and self.player1_score >= self.max_points:
            self.finish_game()
    
    def add_point_player2(self):
        """Añade un punto al jugador 2"""
        self.player2_score += 1
        self.save()
        
        # Auto-finalizar si alcanza max_points
        if self.max_points > 0 and self.player2_score >= self.max_points:
            self.finish_game()
    
    def get_winner(self):
        """Devuelve el nombre del ganador si el juego ha terminado"""
        if self.status == 'finished':
            if self.player1_score > self.player2_score:
                return self.player1_name
            elif self.player2_score > self.player1_score:
                return self.player2_name
            else:
                return 'Empate'
        return None
    
    def get_duration(self):
        """Devuelve la duración del juego si ha terminado"""
        if self.started_at and self.finished_at:
            duration = self.finished_at - self.started_at
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return None


class ExerciseCounter(models.Model):
    """Modelo para contador de ejercicios deportivos"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('in_progress', gettext_lazy('En Progreso')),
        ('paused', gettext_lazy('Pausado')),
        ('finished', gettext_lazy('Finalizado')),
    ]
    
    # Información del ejercicio
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre del ejercicio (ej: Rutina de Flexiones)')
    )
    
    # Contadores
    sets_target = models.IntegerField(
        verbose_name=gettext_lazy('Tandas Objetivo'),
        help_text=gettext_lazy('Número de tandas objetivo')
    )
    reps_target = models.IntegerField(
        verbose_name=gettext_lazy('Repeticiones Objetivo'),
        help_text=gettext_lazy('Número de repeticiones objetivo por tanda')
    )
    
    current_sets = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tandas Actuales')
    )
    current_reps = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Repeticiones Actuales')
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    # URL pública
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('UUID Público'),
        help_text=gettext_lazy('Identificador único para acceso público')
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_exercises',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercises',
        verbose_name=gettext_lazy('Empresa')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de inicio')
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de finalización')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el ejercicio')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Contador de Ejercicio')
        verbose_name_plural = gettext_lazy('Contadores de Ejercicios')
    
    def __str__(self):
        return f"{self.title} - {self.current_sets}/{self.sets_target} tandas"
    
    def get_public_url(self):
        """Devuelve la URL pública del ejercicio"""
        from django.urls import reverse
        return reverse('exercise_counter_public', kwargs={'uuid': self.public_uuid})
    
    def start_exercise(self):
        """Inicia el ejercicio"""
        if self.status == 'pending':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()
    
    def pause_exercise(self):
        """Pausa el ejercicio"""
        if self.status == 'in_progress':
            self.status = 'paused'
            self.save()
    
    def resume_exercise(self):
        """Reanuda el ejercicio"""
        if self.status == 'paused':
            self.status = 'in_progress'
            self.save()
    
    def finish_exercise(self):
        """Finaliza el ejercicio"""
        if self.status in ['in_progress', 'paused']:
            self.status = 'finished'
            self.finished_at = timezone.now()
            self.save()
    
    def add_set(self):
        """Añade una tanda"""
        self.current_sets += 1
        self.current_reps = 0  # Resetear repeticiones al completar una tanda
        self.save()
        
        # Auto-finalizar si alcanza las tandas objetivo
        if self.current_sets >= self.sets_target:
            self.finish_exercise()
    
    def add_rep(self):
        """Añade una repetición"""
        self.current_reps += 1
        self.save()
        
        # Auto-pasar a siguiente tanda si alcanza repeticiones objetivo
        if self.current_reps >= self.reps_target:
            self.add_set()
    
    def get_progress(self):
        """Devuelve el progreso en porcentaje"""
        total_reps_target = self.sets_target * self.reps_target
        total_reps_current = (self.current_sets * self.reps_target) + self.current_reps
        if total_reps_target > 0:
            return int((total_reps_current / total_reps_target) * 100)
        return 0
    
    def get_duration(self):
        """Devuelve la duración del ejercicio si ha terminado"""
        if self.started_at and self.finished_at:
            duration = self.finished_at - self.started_at
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            seconds = duration.seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return None


class SportGoal(models.Model):
    """Modelo para objetivos deportivos con seguimiento de tiempo y distancia"""
    
    # Información del objetivo
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Objetivo'),
        help_text=gettext_lazy('Nombre del objetivo deportivo (ej: Correr 5K en menos de 30 minutos)')
    )
    
    player_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Jugador'),
        help_text=gettext_lazy('Nombre de la persona que realizará el objetivo')
    )
    
    # Objetivos
    target_time = models.IntegerField(
        verbose_name=gettext_lazy('Tiempo Objetivo (segundos)'),
        help_text=gettext_lazy('Tiempo objetivo en segundos para completar el objetivo'),
        null=True,
        blank=True
    )
    
    target_distance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Distancia Objetivo (km)'),
        help_text=gettext_lazy('Distancia objetivo en kilómetros'),
        null=True,
        blank=True
    )
    
    # URL pública
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('UUID Público'),
        help_text=gettext_lazy('Identificador único para acceso público')
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sport_goals',
        verbose_name=gettext_lazy('Creado por')
    )
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sport_goals',
        verbose_name=gettext_lazy('Empresa')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el objetivo')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Objetivo Deportivo')
        verbose_name_plural = gettext_lazy('Objetivos Deportivos')
    
    def __str__(self):
        return f"{self.title} - {self.player_name}"
    
    def get_records(self):
        """Retorna todos los registros del objetivo"""
        return self.records.all().order_by('recorded_at')
    
    def get_best_time(self):
        """Retorna el mejor tiempo registrado"""
        best = self.records.filter(actual_time__isnull=False).order_by('actual_time').first()
        return best.actual_time if best else None
    
    def get_best_distance(self):
        """Retorna la mejor distancia registrada"""
        best = self.records.filter(actual_distance__isnull=False).order_by('-actual_distance').first()
        return best.actual_distance if best else None
    
    def get_progress_percentage(self):
        """Calcula el porcentaje de progreso basado en el mejor registro"""
        if self.target_time and self.get_best_time():
            # Para tiempo: menor es mejor, entonces invertimos el cálculo
            if self.get_best_time() <= self.target_time:
                return 100
            else:
                return min(100, (self.target_time / self.get_best_time()) * 100)
        
        if self.target_distance and self.get_best_distance():
            # Para distancia: mayor es mejor
            return min(100, (float(self.get_best_distance()) / float(self.target_distance)) * 100)
        
        return 0
    
    def format_target_time(self):
        """Formatea el tiempo objetivo"""
        if not self.target_time:
            return "N/A"
        hours = self.target_time // 3600
        minutes = (self.target_time % 3600) // 60
        seconds = self.target_time % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class SportGoalRecord(models.Model):
    """Modelo para registros de intentos de objetivos deportivos"""
    
    sport_goal = models.ForeignKey(
        SportGoal,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name=gettext_lazy('Objetivo Deportivo')
    )
    
    # Registros reales
    actual_time = models.IntegerField(
        verbose_name=gettext_lazy('Tiempo Real (segundos)'),
        help_text=gettext_lazy('Tiempo real en segundos que tomó completar'),
        null=True,
        blank=True
    )
    
    actual_distance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Distancia Real (km)'),
        help_text=gettext_lazy('Distancia real recorrida en kilómetros'),
        null=True,
        blank=True
    )
    
    # Metadatos
    recorded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de registro')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas sobre este intento específico')
    )
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name = gettext_lazy('Registro de Objetivo')
        verbose_name_plural = gettext_lazy('Registros de Objetivos')
    
    def __str__(self):
        return f"{self.sport_goal.title} - {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def format_actual_time(self):
        """Formatea el tiempo real"""
        if not self.actual_time:
            return "N/A"
        hours = self.actual_time // 3600
        minutes = (self.actual_time % 3600) // 60
        seconds = self.actual_time % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def is_goal_achieved(self):
        """Verifica si se alcanzó el objetivo en este registro"""
        goal = self.sport_goal
        
        # Verificar tiempo
        if goal.target_time and self.actual_time:
            if self.actual_time > goal.target_time:
                return False
        
        # Verificar distancia
        if goal.target_distance and self.actual_distance:
            if self.actual_distance < goal.target_distance:
                return False
        
        return True


class Event(models.Model):
    """Modelo para gestionar eventos del calendario"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título del evento')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del evento')
    )
    
    event_date = models.DateTimeField(
        verbose_name=gettext_lazy('Fecha y Hora'),
        help_text=gettext_lazy('Fecha y hora del evento')
    )
    
    location = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Ubicación'),
        help_text=gettext_lazy('Lugar donde se realizará el evento')
    )
    
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color del evento en el calendario (formato hexadecimal)')
    )
    
    is_all_day = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Todo el día'),
        help_text=gettext_lazy('Marcar si el evento dura todo el día')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['event_date']
        verbose_name = gettext_lazy('Evento')
        verbose_name_plural = gettext_lazy('Eventos')
    
    def __str__(self):
        return f"{self.title} - {self.event_date.strftime('%Y-%m-%d %H:%M')}"


class Trip(models.Model):
    """Modelo para gestionar viajes"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Viaje')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    destination = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Destino Principal')
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Inicio')
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Fin')
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Público'),
        help_text=gettext_lazy('Permitir que el viaje sea visible públicamente')
    )
    
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token para compartir el viaje públicamente')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trips',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Viaje')
        verbose_name_plural = gettext_lazy('Viajes')
    
    def __str__(self):
        return f"{self.title} - {self.destination}"
    
    def get_public_url(self):
        """Obtener URL pública del viaje"""
        from django.urls import reverse
        return reverse('trip_public', kwargs={'token': self.public_token})


class TripStop(models.Model):
    """Modelo para puntos de interés en un viaje"""
    
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='stops',
        verbose_name=gettext_lazy('Viaje')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Lugar')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Dirección')
    )
    
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Latitud')
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Longitud')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de visita en el itinerario')
    )
    
    visit_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Visita')
    )
    
    visit_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Hora de Visita')
    )
    
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Duración (minutos)'),
        help_text=gettext_lazy('Tiempo estimado de visita en minutos')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas adicionales sobre el lugar')
    )
    
    historical_info = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Información Histórica'),
        help_text=gettext_lazy('Historia e información interesante sobre el lugar (aprox. 200 palabras)')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['trip', 'order']
        verbose_name = gettext_lazy('Parada de Viaje')
        verbose_name_plural = gettext_lazy('Paradas de Viaje')
    
    def __str__(self):
        return f"{self.order}. {self.name} - {self.trip.title}"
    
    def get_google_maps_url(self):
        """Generar URL de Google Maps"""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        elif self.address:
            import urllib.parse
            query = urllib.parse.quote(self.address)
            return f"https://www.google.com/maps/search/?api=1&query={query}"
        return None


class WebCounter(models.Model):
    """Contador web para rastrear visitas en sitios externos"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy('Usuario'),
        related_name='web_counters'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Contador')
    )
    
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=gettext_lazy('Token'),
        help_text=gettext_lazy('Token único para identificar este contador')
    )
    
    domain = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=gettext_lazy('Dominio'),
        help_text=gettext_lazy('Dominio donde se instalará el contador (opcional)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    total_visits = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de Visitas')
    )
    
    total_page_views = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de Páginas Vistas')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Contador Web')
        verbose_name_plural = gettext_lazy('Contadores Web')
    
    def __str__(self):
        return f"{self.title} ({self.token})"
    
    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def get_script_html(self, request=None):
        """Generar el script HTML para insertar en sitios web"""
        from django.conf import settings
        
        # Usar configuración del settings o detectar automáticamente
        if request:
            base_url = request.build_absolute_uri('/').rstrip('/')
        else:
            # En producción usar el dominio configurado en settings
            base_url = getattr(settings, 'WEB_COUNTER_BASE_URL', 'https://ticketproo.com')
        
        script = f'''<!-- TicketProo Counter -->
<script type="text/javascript">
!function(){{var t="{self.token}",e="{base_url}/api/web-counter/track/";function n(){{fetch(e,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{token:t,url:window.location.href,referrer:document.referrer,user_agent:navigator.userAgent,screen_resolution:window.screen.width+"x"+window.screen.height,language:navigator.language}})}}).catch(function(){{}});}}"loading"===document.readyState?document.addEventListener("DOMContentLoaded",n):n();}}();
</script>'''
        return script


class WebCounterVisit(models.Model):
    """Registro de visitas del contador web"""
    counter = models.ForeignKey(
        WebCounter,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name=gettext_lazy('Contador')
    )
    
    url = models.CharField(
        max_length=2048,
        verbose_name=gettext_lazy('URL Visitada')
    )
    
    referrer = models.CharField(
        max_length=2048,
        blank=True,
        verbose_name=gettext_lazy('Referrer')
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('IP')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('País')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Ciudad')
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    browser = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Navegador')
    )
    
    os = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Sistema Operativo')
    )
    
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Tipo de Dispositivo'),
        help_text=gettext_lazy('mobile, tablet, desktop')
    )
    
    screen_resolution = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Resolución de Pantalla')
    )
    
    language = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=gettext_lazy('Idioma')
    )
    
    session_id = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=gettext_lazy('ID de Sesión')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Visita'),
        db_index=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Visita de Contador Web')
        verbose_name_plural = gettext_lazy('Visitas de Contadores Web')
        indexes = [
            models.Index(fields=['-created_at', 'counter']),
            models.Index(fields=['counter', 'session_id']),
        ]
    
    def __str__(self):
        return f"{self.counter.title} - {self.url} ({self.created_at})"


class QuickQuote(models.Model):
    """Modelo para cotizaciones rápidas"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('accepted', gettext_lazy('Aceptado')),
        ('rejected', gettext_lazy('Rechazado')),
        ('expired', gettext_lazy('Expirado')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quick_quotes',
        verbose_name=gettext_lazy('Usuario')
    )
    
    sequence_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Número de Secuencia'),
        help_text=gettext_lazy('Formato: CR-YYYY-XX')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    
    hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Cantidad de Horas')
    )
    
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Costo por Hora')
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Importe Total'),
        editable=False
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    valid_until = models.DateTimeField(
        verbose_name=gettext_lazy('Válido Hasta')
    )
    
    public_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quick_quotes',
        verbose_name=gettext_lazy('Empresa')
    )
    
    client_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre del Cliente')
    )
    
    client_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email del Cliente')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas')
    )
    
    response_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Respuesta')
    )
    
    response_notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas de Respuesta del Cliente')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Cotización Rápida')
        verbose_name_plural = gettext_lazy('Cotizaciones Rápidas')
    
    def save(self, *args, **kwargs):
        # Calcular el total automáticamente
        from decimal import Decimal
        self.total_amount = Decimal(str(self.hours)) * Decimal(str(self.hourly_rate))
        
        # Generar token público si no existe
        if not self.public_token:
            import secrets
            self.public_token = secrets.token_urlsafe(32)
        
        # Establecer fecha de vencimiento si no existe
        if not self.valid_until:
            from datetime import timedelta
            self.valid_until = timezone.now() + timedelta(days=7)
        
        # Generar número de secuencia si no existe
        if not self.sequence_number:
            year = timezone.now().year
            # Obtener el último número del año actual
            last_quote = QuickQuote.objects.filter(
                sequence_number__startswith=f'CR-{year}-'
            ).order_by('-sequence_number').first()
            
            if last_quote and last_quote.sequence_number:
                try:
                    last_num = int(last_quote.sequence_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.sequence_number = f'CR-{year}-{new_num:02d}'
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Verifica si la cotización ha expirado"""
        return timezone.now() > self.valid_until and self.status == 'pending'
    
    def get_public_url(self, request=None):
        """Retorna la URL pública para que el cliente responda"""
        from django.urls import reverse
        path = reverse('quick_quote_public', kwargs={'token': self.public_token})
        if request:
            return request.build_absolute_uri(path)
        from django.conf import settings
        base_url = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        protocol = 'https' if 'localhost' not in base_url else 'http'
        return f"{protocol}://{base_url}{path}"
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()} - ${self.total_amount}"


class QuickQuoteComment(models.Model):
    """Modelo para comentarios públicos en cotizaciones"""
    
    quote = models.ForeignKey(
        QuickQuote,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Cotización')
    )
    
    author_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre')
    )
    
    author_email = models.EmailField(
        verbose_name=gettext_lazy('Email')
    )
    
    comment = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Comentario de Cotización')
        verbose_name_plural = gettext_lazy('Comentarios de Cotizaciones')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.author_name} - {self.quote.sequence_number}"


class QuickQuoteView(models.Model):
    """Modelo para registrar visualizaciones de cotizaciones públicas"""
    
    quote = models.ForeignKey(
        QuickQuote,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=gettext_lazy('Cotización')
    )
    
    viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Visualización')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('País')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Ciudad')
    )
    
    browser = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Navegador')
    )
    
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Tipo de Dispositivo')
    )
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = gettext_lazy('Visualización de Cotización')
        verbose_name_plural = gettext_lazy('Visualizaciones de Cotizaciones')
    
    def __str__(self):
        return f"Vista de {self.quote.title} - {self.viewed_at.strftime('%d/%m/%Y %H:%M')}"


class SupportContract(models.Model):
    """Modelo para contratos de soporte"""
    
    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('pending', gettext_lazy('Pendiente de Firma')),
        ('signed', gettext_lazy('Firmado')),
        ('active', gettext_lazy('Activo')),
        ('expired', gettext_lazy('Expirado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_contracts',
        verbose_name=gettext_lazy('Usuario')
    )
    
    sequence_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Número de Secuencia'),
        help_text=gettext_lazy('Formato: CS-YYYY-XX')
    )
    
    provider_company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='provided_support_contracts',
        verbose_name=gettext_lazy('Compañía Proveedora'),
        help_text=gettext_lazy('Compañía que ofrece el servicio'),
        null=True,
        blank=True
    )
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='support_contracts',
        verbose_name=gettext_lazy('Cliente'),
        help_text=gettext_lazy('Empresa cliente del servicio')
    )
    
    start_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Inicio')
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Fin')
    )
    
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Monto Total')
    )
    
    payment_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', gettext_lazy('Mensual')),
            ('quarterly', gettext_lazy('Trimestral')),
            ('biannual', gettext_lazy('Semestral')),
            ('annual', gettext_lazy('Anual')),
        ],
        default='monthly',
        verbose_name=gettext_lazy('Frecuencia de Pago')
    )
    
    number_of_payments = models.IntegerField(
        verbose_name=gettext_lazy('Número de Cuotas'),
        default=12
    )
    
    public_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    
    # Campos de firma
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Firma')
    )
    
    signed_by_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Firmado por (Nombre)')
    )
    
    signed_by_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Firmado por (Email)')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Fecha de Actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Contrato de Soporte')
        verbose_name_plural = gettext_lazy('Contratos de Soporte')
    
    def save(self, *args, **kwargs):
        # Generar token público si no existe
        if not self.public_token:
            import secrets
            self.public_token = secrets.token_urlsafe(48)
        
        # Generar número de secuencia si no existe
        if not self.sequence_number:
            from django.utils import timezone
            year = timezone.now().year
            last_contract = SupportContract.objects.filter(
                sequence_number__startswith=f'CS-{year}-'
            ).order_by('-sequence_number').first()
            
            if last_contract:
                try:
                    last_num = int(last_contract.sequence_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.sequence_number = f'CS-{year}-{new_num:02d}'
        
        super().save(*args, **kwargs)
    
    def get_public_url(self, request=None):
        """Retorna la URL pública para que el cliente firme"""
        from django.urls import reverse
        path = reverse('support_contract_public', kwargs={'token': self.public_token})
        if request:
            return request.build_absolute_uri(path)
        from django.conf import settings
        base_url = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        protocol = 'https' if 'localhost' not in base_url else 'http'
        return f"{protocol}://{base_url}{path}"
    
    def is_signed(self):
        """Verifica si el contrato está firmado"""
        return self.status == 'signed' or self.status == 'active'
    
    def __str__(self):
        return f"{self.sequence_number} - {self.company.name}"


class SupportContractPayment(models.Model):
    """Modelo para las cuotas/pagos de los contratos de soporte"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('paid', gettext_lazy('Pagado')),
        ('overdue', gettext_lazy('Vencido')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]
    
    contract = models.ForeignKey(
        SupportContract,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=gettext_lazy('Contrato')
    )
    
    payment_number = models.IntegerField(
        verbose_name=gettext_lazy('Número de Cuota')
    )
    
    due_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Vencimiento')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Monto')
    )
    
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Pago')
    )
    
    payment_method = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Método de Pago')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        ordering = ['due_date', 'payment_number']
        verbose_name = gettext_lazy('Pago de Contrato')
        verbose_name_plural = gettext_lazy('Pagos de Contratos')
    
    def is_overdue(self):
        """Verifica si el pago está vencido"""
        from django.utils import timezone
        return self.status == 'pending' and timezone.now().date() > self.due_date
    
    def __str__(self):
        return f"{self.contract.sequence_number} - Cuota {self.payment_number} - €{self.amount}"


class MultiMeasurement(models.Model):
    """Modelo para mediciones múltiples"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='multi_measurements',
        verbose_name=gettext_lazy('Usuario')
    )
    
    sequence_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('Número de Secuencia'),
        help_text=gettext_lazy('Formato: MM-YYYY-XX')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    
    public_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=gettext_lazy('Token Público'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    # Etiquetas para las 5 mediciones
    label_1 = models.CharField(
        max_length=100,
        default='Medición 1',
        verbose_name=gettext_lazy('Etiqueta Medición 1')
    )
    
    label_2 = models.CharField(
        max_length=100,
        default='Medición 2',
        verbose_name=gettext_lazy('Etiqueta Medición 2')
    )
    
    label_3 = models.CharField(
        max_length=100,
        default='Medición 3',
        verbose_name=gettext_lazy('Etiqueta Medición 3')
    )
    
    label_4 = models.CharField(
        max_length=100,
        default='Medición 4',
        verbose_name=gettext_lazy('Etiqueta Medición 4')
    )
    
    label_5 = models.CharField(
        max_length=100,
        default='Medición 5',
        verbose_name=gettext_lazy('Etiqueta Medición 5')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Medición Múltiple')
        verbose_name_plural = gettext_lazy('Mediciones Múltiples')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Generar token público si no existe
        if not self.public_token:
            import secrets
            self.public_token = secrets.token_urlsafe(32)
        
        # Generar número de secuencia si no existe
        if not self.sequence_number:
            year = timezone.now().year
            # Obtener el último número del año actual
            last_measurement = MultiMeasurement.objects.filter(
                sequence_number__startswith=f'MM-{year}-'
            ).order_by('-sequence_number').first()
            
            if last_measurement and last_measurement.sequence_number:
                try:
                    last_num = int(last_measurement.sequence_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.sequence_number = f'MM-{year}-{new_num:02d}'
        
        super().save(*args, **kwargs)
    
    def get_public_url(self, request=None):
        """Retorna la URL pública para cargar mediciones"""
        from django.urls import reverse
        path = reverse('multi_measurement_public', kwargs={'token': self.public_token})
        if request:
            return request.build_absolute_uri(path)
        from django.conf import settings
        base_url = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        protocol = 'https' if 'localhost' not in base_url else 'http'
        return f"{protocol}://{base_url}{path}"
    
    def __str__(self):
        return f"{self.sequence_number} - {self.title}"


class MultiMeasurementRecord(models.Model):
    """Modelo para registros diarios de mediciones"""
    
    measurement = models.ForeignKey(
        MultiMeasurement,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name=gettext_lazy('Medición')
    )
    
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha y Hora')
    )
    
    value_1 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor 1')
    )
    
    value_2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor 2')
    )
    
    value_3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor 3')
    )
    
    value_4 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor 4')
    )
    
    value_5 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Valor 5')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Registro de Medición')
        verbose_name_plural = gettext_lazy('Registros de Mediciones')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.measurement.sequence_number} - {self.date.strftime('%d/%m/%Y %H:%M')}"


class PersonalBudget(models.Model):
    """Modelo para presupuestos personales anuales"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='personal_budgets',
        verbose_name=gettext_lazy('Usuario')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Presupuesto')
    )
    
    year = models.IntegerField(
        verbose_name=gettext_lazy('Año')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    is_private = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Privado'),
        help_text=gettext_lazy('Si está marcado, solo el creador puede ver este presupuesto')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Presupuesto Personal')
        verbose_name_plural = gettext_lazy('Presupuestos Personales')
        ordering = ['-year', 'name']
        unique_together = ['user', 'name', 'year']
    
    def __str__(self):
        return f"{self.name} - {self.year}"
    
    def get_month_display(self):
        """Retorna el nombre del mes"""
        months = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return months[1]  # Placeholder, no se usa más
    
    def get_total_income_budget(self, month=None):
        """Total presupuestado de ingresos (mensual o anual)"""
        from decimal import Decimal
        total_monthly = self.income_items.aggregate(total=models.Sum('budgeted_amount'))['total'] or Decimal('0')
        # Si se pide vista mensual, retornar el total mensual; si es anual, multiplicar por 12
        return total_monthly if month else total_monthly * Decimal('12')
    
    def get_total_expense_budget(self, month=None):
        """Total presupuestado de egresos (mensual o anual)"""
        from decimal import Decimal
        total_monthly = self.expense_items.aggregate(total=models.Sum('budgeted_amount'))['total'] or Decimal('0')
        # Si se pide vista mensual, retornar el total mensual; si es anual, multiplicar por 12
        return total_monthly if month else total_monthly * Decimal('12')
    
    def get_total_income_actual(self, month=None):
        """Total real de ingresos (filtrado por mes si se especifica)"""
        from decimal import Decimal
        qs = self.transactions.filter(transaction_type='income')
        if month:
            qs = qs.filter(month=month, year=self.year)
        return qs.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    def get_total_expense_actual(self, month=None):
        """Total real de egresos (filtrado por mes si se especifica)"""
        from decimal import Decimal
        qs = self.transactions.filter(transaction_type='expense')
        if month:
            qs = qs.filter(month=month, year=self.year)
        return qs.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')


class BudgetIncomeItem(models.Model):
    """Partidas de ingresos del presupuesto"""
    
    budget = models.ForeignKey(
        PersonalBudget,
        on_delete=models.CASCADE,
        related_name='income_items',
        verbose_name=gettext_lazy('Presupuesto')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Partida')
    )
    
    budgeted_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Monto Presupuestado Mensual (€)'),
        help_text=gettext_lazy('Monto mensual en euros para esta partida')
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Partida de Ingreso')
        verbose_name_plural = gettext_lazy('Partidas de Ingresos')
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.budget} - {self.name}"
    
    def get_actual_amount(self, month=None, year=None):
        """Monto real de transacciones de ingreso (filtrado por mes/año si se especifica)"""
        from decimal import Decimal
        qs = self.transactions.all()
        if month and year:
            qs = qs.filter(month=month, year=year)
        return qs.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    def get_percentage_budget(self):
        """Porcentaje respecto al presupuesto total de ingresos"""
        total = self.budget.get_total_income_budget()
        if total > 0:
            return (float(self.budgeted_amount) / float(total)) * 100
        return 0
    
    def get_percentage_actual(self):
        """Porcentaje real respecto al total real de ingresos"""
        total = self.budget.get_total_income_actual()
        if total > 0:
            return (float(self.get_actual_amount()) / float(total)) * 100
        return 0


class BudgetExpenseItem(models.Model):
    """Partidas de egresos del presupuesto"""
    
    budget = models.ForeignKey(
        PersonalBudget,
        on_delete=models.CASCADE,
        related_name='expense_items',
        verbose_name=gettext_lazy('Presupuesto')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Partida')
    )
    
    budgeted_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Monto Presupuestado Mensual (€)'),
        help_text=gettext_lazy('Monto mensual en euros para esta partida')
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Partida de Egreso')
        verbose_name_plural = gettext_lazy('Partidas de Egresos')
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.budget} - {self.name}"
    
    def get_actual_amount(self, month=None, year=None):
        """Monto real de transacciones de egreso (filtrado por mes/año si se especifica)"""
        from decimal import Decimal
        qs = self.transactions.all()
        if month and year:
            qs = qs.filter(month=month, year=year)
        return qs.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    def get_percentage_budget(self):
        """Porcentaje respecto al presupuesto total de egresos"""
        total = self.budget.get_total_expense_budget()
        if total > 0:
            return (float(self.budgeted_amount) / float(total)) * 100
        return 0
    
    def get_percentage_actual(self):
        """Porcentaje real respecto al total real de egresos"""
        total = self.budget.get_total_expense_actual()
        if total > 0:
            return (float(self.get_actual_amount()) / float(total)) * 100
        return 0


class BudgetTransaction(models.Model):
    """Transacciones (ingresos o egresos) del presupuesto"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('income', gettext_lazy('Ingreso')),
        ('expense', gettext_lazy('Egreso')),
    ]
    
    budget = models.ForeignKey(
        PersonalBudget,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=gettext_lazy('Presupuesto')
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name=gettext_lazy('Tipo')
    )
    
    income_item = models.ForeignKey(
        BudgetIncomeItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=gettext_lazy('Partida de Ingreso')
    )
    
    expense_item = models.ForeignKey(
        BudgetExpenseItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=gettext_lazy('Partida de Egreso')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=gettext_lazy('Monto')
    )
    
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    
    transaction_date = models.DateField(
        verbose_name=gettext_lazy('Fecha de Transacción')
    )
    
    month = models.IntegerField(
        default=1,
        verbose_name=gettext_lazy('Mes'),
        help_text=gettext_lazy('Mes de la transacción (1-12)')
    )
    
    year = models.IntegerField(
        default=2025,
        verbose_name=gettext_lazy('Año'),
        help_text=gettext_lazy('Año de la transacción')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Registro')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Transacción')
        verbose_name_plural = gettext_lazy('Transacciones')
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.transaction_date}"
    
    def save(self, *args, **kwargs):
        # Extraer mes y año de la fecha de transacción
        if self.transaction_date:
            self.month = self.transaction_date.month
            self.year = self.transaction_date.year
        super().save(*args, **kwargs)


# Añadir campos Many-to-Many al modelo PersonalBudget
PersonalBudget.add_to_class('income_transactions', 
    models.ManyToManyField(BudgetTransaction, related_name='income_budgets', blank=True))
PersonalBudget.add_to_class('expense_transactions', 
    models.ManyToManyField(BudgetTransaction, related_name='expense_budgets', blank=True))


# ============= MODELOS PARA TABLAS DINÁMICAS API =============

class DynamicTable(models.Model):
    """Modelo para definir tablas dinámicas con API CRUD"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=gettext_lazy('Nombre de la tabla'),
        help_text=gettext_lazy('Nombre único de la tabla (ej: usuarios, comentarios)')
    )
    display_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de visualización'),
        help_text=gettext_lazy('Nombre amigable para mostrar')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción del propósito de la tabla')
    )
    api_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token de API'),
        help_text=gettext_lazy('Token de seguridad para acceder a la API de esta tabla')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Si la tabla y su API están activas')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dynamic_tables_created',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Configuración de permisos
    allow_public_read = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Permitir lectura pública'),
        help_text=gettext_lazy('Permitir GET sin autenticación')
    )
    allow_public_create = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Permitir creación pública'),
        help_text=gettext_lazy('Permitir POST sin autenticación')
    )
    
    # Configuración de formulario público móvil
    public_form_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Formulario público habilitado'),
        help_text=gettext_lazy('Habilitar formulario web público para crear registros')
    )
    public_form_token = models.UUIDField(
        default=uuid.uuid4,
        null=True,
        blank=True,
        unique=True,
        verbose_name=gettext_lazy('Token del formulario público'),
        help_text=gettext_lazy('Token único para acceder al formulario público')
    )
    public_form_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Contraseña del formulario'),
        help_text=gettext_lazy('Contraseña opcional para proteger el formulario público')
    )
    public_form_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Título del formulario'),
        help_text=gettext_lazy('Título personalizado para el formulario público')
    )
    public_form_description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción del formulario'),
        help_text=gettext_lazy('Texto descriptivo que se muestra en el formulario')
    )
    public_form_success_message = models.CharField(
        max_length=500,
        default='¡Gracias! Tu información ha sido registrada correctamente.',
        verbose_name=gettext_lazy('Mensaje de éxito'),
        help_text=gettext_lazy('Mensaje que se muestra después de enviar el formulario')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Tabla Dinámica')
        verbose_name_plural = gettext_lazy('Tablas Dinámicas')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.display_name
    
    def get_api_url(self):
        """Retorna la URL base de la API para esta tabla"""
        return f'/api/dynamic-tables/{self.name}/'
    
    def regenerate_token(self):
        """Regenera el token de API"""
        self.api_token = uuid.uuid4()
        self.save()
        return self.api_token
    
    def get_public_form_url(self):
        """Retorna la URL del formulario público"""
        return f'/public-form/{self.public_form_token}/'
    
    def regenerate_public_form_token(self):
        """Regenera el token del formulario público"""
        self.public_form_token = uuid.uuid4()
        self.save()
        return self.public_form_token


class DynamicTableField(models.Model):
    """Modelo para definir campos de una tabla dinámica"""
    
    FIELD_TYPES = [
        ('text', 'Texto corto'),
        ('textarea', 'Texto largo'),
        ('number', 'Número'),
        ('decimal', 'Decimal'),
        ('boolean', 'Verdadero/Falso'),
        ('date', 'Fecha'),
        ('datetime', 'Fecha y hora'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('json', 'JSON'),
    ]
    
    table = models.ForeignKey(
        DynamicTable,
        on_delete=models.CASCADE,
        related_name='fields',
        verbose_name=gettext_lazy('Tabla')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre del campo'),
        help_text=gettext_lazy('Nombre del campo (ej: titulo, email, contenido)')
    )
    display_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de visualización'),
        help_text=gettext_lazy('Nombre amigable para mostrar')
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        default='text',
        verbose_name=gettext_lazy('Tipo de campo')
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Requerido'),
        help_text=gettext_lazy('Si el campo es obligatorio')
    )
    default_value = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Valor por defecto'),
        help_text=gettext_lazy('Valor por defecto del campo')
    )
    max_length = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Longitud máxima'),
        help_text=gettext_lazy('Longitud máxima para campos de texto')
    )
    help_text = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Texto de ayuda'),
        help_text=gettext_lazy('Descripción o ayuda del campo')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de visualización del campo')
    )
    is_unique = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Único'),
        help_text=gettext_lazy('Si el valor debe ser único en la tabla')
    )
    is_indexed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Indexado'),
        help_text=gettext_lazy('Si el campo debe ser indexado para búsquedas rápidas')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Campo de Tabla')
        verbose_name_plural = gettext_lazy('Campos de Tablas')
        ordering = ['table', 'order', 'id']
        unique_together = [['table', 'name']]
    
    def __str__(self):
        return f'{self.table.name}.{self.name}'


class DynamicTableRecord(models.Model):
    """Modelo para almacenar registros de tablas dinámicas"""
    
    table = models.ForeignKey(
        DynamicTable,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name=gettext_lazy('Tabla')
    )
    data = models.JSONField(
        verbose_name=gettext_lazy('Datos'),
        help_text=gettext_lazy('Datos del registro en formato JSON')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    created_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('IP de creación'),
        help_text=gettext_lazy('Dirección IP desde donde se creó el registro')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Registro de Tabla')
        verbose_name_plural = gettext_lazy('Registros de Tablas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['table', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.table.name} #{self.id}'


class SavedApiRequest(models.Model):
    """Modelo para guardar configuraciones de peticiones API"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Nombre descriptivo para identificar esta petición')
    )
    url = models.URLField(
        max_length=500,
        verbose_name=gettext_lazy('URL'),
        help_text=gettext_lazy('URL completa del endpoint')
    )
    method = models.CharField(
        max_length=10,
        choices=[
            ('GET', gettext_lazy('GET')),
            ('POST', gettext_lazy('POST')),
            ('PUT', gettext_lazy('PUT')),
            ('PATCH', gettext_lazy('PATCH')),
            ('DELETE', gettext_lazy('DELETE')),
        ],
        default='GET',
        verbose_name=gettext_lazy('Método HTTP')
    )
    headers = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Headers'),
        help_text=gettext_lazy('Headers personalizados (formato: Name: Value, uno por línea)')
    )
    body = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Body'),
        help_text=gettext_lazy('Cuerpo de la petición (JSON)')
    )
    token = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Token'),
        help_text=gettext_lazy('Token de autenticación (Bearer, API Key, etc.)')
    )
    api_type = models.CharField(
        max_length=20,
        choices=[
            ('internal', gettext_lazy('API Interna')),
            ('external', gettext_lazy('API Externa')),
        ],
        default='external',
        verbose_name=gettext_lazy('Tipo de API')
    )
    dynamic_table = models.ForeignKey(
        DynamicTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saved_requests',
        verbose_name=gettext_lazy('Tabla Dinámica'),
        help_text=gettext_lazy('Solo si es API interna')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Notas sobre esta petición')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_api_requests',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Favorito'),
        help_text=gettext_lazy('Marcar como favorito para acceso rápido')
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Último uso'),
        help_text=gettext_lazy('Última vez que se ejecutó esta petición')
    )
    
    class Meta:
        verbose_name = gettext_lazy('API Guardada')
        verbose_name_plural = gettext_lazy('APIs Guardadas')
        ordering = ['-is_favorite', '-last_used', '-created_at']
        indexes = [
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['created_by', 'is_favorite']),
        ]
    
    def __str__(self):
        return self.title
    
    def mark_as_used(self):
        """Actualiza el timestamp de último uso"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class SocialPost(models.Model):
    """Publicación en la red social interna"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_posts',
        verbose_name=gettext_lazy('Usuario')
    )
    content = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Contenido'),
        help_text=gettext_lazy('Texto de la publicación')
    )
    image = models.ImageField(
        upload_to='social_posts/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Imagen'),
        help_text=gettext_lazy('Imagen de la publicación')
    )
    youtube_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('URL de YouTube'),
        help_text=gettext_lazy('URL del video de YouTube')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Privado'),
        help_text=gettext_lazy('Solo visible para el creador')
    )
    share_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name=gettext_lazy('Token de compartir'),
        help_text=gettext_lazy('Token único para compartir públicamente')
    )
    company_only = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Solo mi empresa'),
        help_text=gettext_lazy('Si está marcado, solo los usuarios de la misma empresa pueden ver esta publicación')
    )
    public_views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Vistas públicas'),
        help_text=gettext_lazy('Número de veces que se ha visto la publicación pública')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Publicación Social')
        verbose_name_plural = gettext_lazy('Publicaciones Sociales')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['share_token']),
            models.Index(fields=['company_only', '-created_at']),
        ]
    
    def __str__(self):
        content_preview = self.content[:50] if self.content else 'Sin texto'
        return f'{self.user.username} - {content_preview}'
    
    def get_likes_count(self):
        """Retorna el número de me gusta"""
        return self.likes.filter(reaction_type='like').count()
    
    def get_loves_count(self):
        """Retorna el número de me encanta"""
        return self.likes.filter(reaction_type='love').count()
    
    def get_dislikes_count(self):
        """Retorna el número de no me gusta"""
        return self.likes.filter(reaction_type='dislike').count()
    
    def get_comments_count(self):
        """Retorna el número de comentarios"""
        return self.comments.filter(is_active=True).count()
    
    def user_has_liked(self, user):
        """Verifica si un usuario ha dado like"""
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()
    
    def get_youtube_embed_url(self):
        """Convierte URL de YouTube a URL embebida"""
        if not self.youtube_url:
            return None
        
        import re
        # Patrones para diferentes formatos de URL de YouTube
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([\w-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                video_id = match.group(1)
                return f'https://www.youtube.com/embed/{video_id}'
        
        return None
    
    def generate_share_token(self):
        """Genera un token único para compartir"""
        import uuid
        if not self.share_token:
            self.share_token = str(uuid.uuid4())
            self.save()
        return self.share_token
    
    def get_public_share_url(self):
        """Obtiene la URL pública para compartir"""
        if not self.share_token:
            return None
        from django.urls import reverse
        return reverse('social_post_public', kwargs={'token': self.share_token})


class SocialPostLike(models.Model):
    """Reacción en una publicación"""
    
    REACTION_CHOICES = [
        ('like', gettext_lazy('Me gusta')),
        ('love', gettext_lazy('Me encanta')),
        ('dislike', gettext_lazy('No me gusta')),
    ]
    
    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=gettext_lazy('Publicación')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_likes',
        verbose_name=gettext_lazy('Usuario')
    )
    reaction_type = models.CharField(
        max_length=10,
        choices=REACTION_CHOICES,
        default='like',
        verbose_name=gettext_lazy('Tipo de reacción')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Like')
        verbose_name_plural = gettext_lazy('Likes')
        unique_together = ('post', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'user']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - Post #{self.post.id}'


class SocialPostComment(models.Model):
    """Comentario en una publicación"""
    
    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Publicación')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_comments',
        verbose_name=gettext_lazy('Usuario'),
        blank=True,
        null=True
    )
    # Campos para usuarios anónimos (comentarios públicos)
    guest_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Nombre del invitado')
    )
    guest_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Email del invitado')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Comentario')
        verbose_name_plural = gettext_lazy('Comentarios')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]
    
    def __str__(self):
        content_preview = self.content[:50]
        username = self.user.username if self.user else self.guest_name or 'Anónimo'
        return f'{username} - {content_preview}'
    
    def get_display_name(self):
        """Retorna el nombre a mostrar (usuario o invitado)"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name or 'Anónimo'
    
    def get_likes_count(self):
        """Retorna el número de me gusta en el comentario"""
        return self.comment_reactions.filter(reaction_type='like').count()
    
    def get_loves_count(self):
        """Retorna el número de me encanta en el comentario"""
        return self.comment_reactions.filter(reaction_type='love').count()
    
    def get_dislikes_count(self):
        """Retorna el número de no me gusta en el comentario"""
        return self.comment_reactions.filter(reaction_type='dislike').count()


class SocialCommentReaction(models.Model):
    """Reacción en un comentario"""
    
    REACTION_CHOICES = [
        ('like', gettext_lazy('Me gusta')),
        ('love', gettext_lazy('Me encanta')),
        ('dislike', gettext_lazy('No me gusta')),
    ]
    
    comment = models.ForeignKey(
        SocialPostComment,
        on_delete=models.CASCADE,
        related_name='comment_reactions',
        verbose_name=gettext_lazy('Comentario')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_comment_reactions',
        verbose_name=gettext_lazy('Usuario')
    )
    reaction_type = models.CharField(
        max_length=10,
        choices=REACTION_CHOICES,
        default='like',
        verbose_name=gettext_lazy('Tipo de reacción')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Reacción de Comentario')
        verbose_name_plural = gettext_lazy('Reacciones de Comentarios')
        unique_together = ('comment', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['comment', 'user']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - {self.reaction_type} - Comment #{self.comment.id}'


class SocialPostFavorite(models.Model):
    """Publicación marcada como favorita por un usuario"""
    
    post = models.ForeignKey(
        SocialPost,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=gettext_lazy('Publicación')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_posts',
        verbose_name=gettext_lazy('Usuario')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha')
    )
    
    class Meta:
        verbose_name = gettext_lazy('Favorito')
        verbose_name_plural = gettext_lazy('Favoritos')
        unique_together = ('post', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['post', 'user']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - Post #{self.post.id}'


class FunctionalRequirementDocument(models.Model):
    """Documento de Requerimientos Funcionales (DRF)"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='functional_requirement_documents',
        verbose_name=gettext_lazy('Empresa'),
        null=True,
        blank=True
    )
    company_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre de Empresa'),
        help_text=gettext_lazy('Nombre libre de la empresa si no está en el listado')
    )
    title = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Título')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción General'),
        help_text=gettext_lazy('Descripción general del proyecto o alcance')
    )
    sequence = models.CharField(
        max_length=50,
        verbose_name=gettext_lazy('Secuencia'),
        help_text=gettext_lazy('Se genera automáticamente'),
        unique=True,
        editable=False
    )
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token público')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_frd_documents',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    # Campos de aceptación/rechazo del documento completo
    document_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', gettext_lazy('Pendiente')),
            ('accepted', gettext_lazy('Aceptado')),
            ('rejected', gettext_lazy('Rechazado'))
        ],
        default='pending',
        verbose_name=gettext_lazy('Estado del Documento')
    )
    document_reviewed_by_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Revisado por')
    )
    document_reviewed_by_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email del revisor')
    )
    document_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de revisión')
    )
    document_review_comments = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentarios de revisión')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Documento de Requerimientos Funcionales')
        verbose_name_plural = gettext_lazy('Documentos de Requerimientos Funcionales')
    
    def __str__(self):
        return f"{self.sequence} - {self.title}"
    
    def get_company_display(self):
        """Retorna el nombre de la empresa (FK o libre)"""
        if self.company:
            return self.company.name
        return self.company_name or 'Sin empresa'
    
    @staticmethod
    def generate_sequence():
        """Genera la secuencia automática en formato DRF-YYYY-NNN"""
        from datetime import datetime
        year = datetime.now().year
        prefix = f"DRF-{year}-"
        
        # Buscar el último documento del año
        last_doc = FunctionalRequirementDocument.objects.filter(
            sequence__startswith=prefix
        ).order_by('-sequence').first()
        
        if last_doc:
            # Extraer el número y incrementar
            last_number = int(last_doc.sequence.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:03d}"
    
    def get_public_url(self):
        """Retorna la URL pública del documento"""
        from django.urls import reverse
        return reverse('public_frd', kwargs={'token': self.public_share_token})
    
    def get_approved_count(self):
        """Retorna el número de requerimientos aprobados"""
        return self.requirements.filter(is_approved=True).count()
    
    def get_total_count(self):
        """Retorna el número total de requerimientos"""
        return self.requirements.count()
    
    def get_approval_percentage(self):
        """Retorna el porcentaje de aprobación"""
        total = self.get_total_count()
        if total == 0:
            return 0
        return round((self.get_approved_count() / total) * 100, 1)
    
    def get_pending_count(self):
        """Retorna el número de requerimientos pendientes"""
        return self.get_total_count() - self.get_approved_count()
    
    def get_total_views(self):
        """Retorna el número total de visitas a la página pública"""
        return self.views.count()
    
    def get_unique_visitors(self):
        """Retorna el número de visitantes únicos por IP"""
        return self.views.values('ip_address').distinct().count()
    
    def get_recent_views(self, limit=10):
        """Retorna las últimas visitas"""
        return self.views.order_by('-viewed_at')[:limit]
    
    def get_views_by_date(self):
        """Retorna las visitas agrupadas por fecha"""
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        return self.views.annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')
    
    def accept_document(self, name, email, comments=''):
        """Acepta el documento completo"""
        self.document_status = 'accepted'
        self.document_reviewed_by_name = name
        self.document_reviewed_by_email = email
        self.document_review_comments = comments
        self.document_reviewed_at = timezone.now()
        self.save()
    
    def reject_document(self, name, email, comments=''):
        """Rechaza el documento completo"""
        self.document_status = 'rejected'
        self.document_reviewed_by_name = name
        self.document_reviewed_by_email = email
        self.document_review_comments = comments
        self.document_reviewed_at = timezone.now()
        self.save()
    
    def is_document_accepted(self):
        """Retorna True si el documento está aceptado"""
        return self.document_status == 'accepted'
    
    def is_document_rejected(self):
        """Retorna True si el documento está rechazado"""
        return self.document_status == 'rejected'
    
    def is_document_pending(self):
        """Retorna True si el documento está pendiente"""
        return self.document_status == 'pending'


class FunctionalRequirement(models.Model):
    """Requerimiento individual dentro de un DRF"""
    
    document = models.ForeignKey(
        FunctionalRequirementDocument,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name=gettext_lazy('Documento')
    )
    number = models.PositiveIntegerField(
        verbose_name=gettext_lazy('Número'),
        help_text=gettext_lazy('Número secuencial del requerimiento')
    )
    title = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título breve del requerimiento')
    )
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción del alcance o requerimiento')
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Aprobado')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de aprobación')
    )
    approved_by_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Aprobado por (nombre)')
    )
    approved_by_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Aprobado por (email)')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['document', 'number']
        verbose_name = gettext_lazy('Requerimiento Funcional')
        verbose_name_plural = gettext_lazy('Requerimientos Funcionales')
        unique_together = ['document', 'number']
    
    def __str__(self):
        return f"{self.document.sequence} - Req #{self.number}"
    
    def approve(self, name, email):
        """Aprueba el requerimiento"""
        self.is_approved = True
        self.approved_at = timezone.now()
        self.approved_by_name = name
        self.approved_by_email = email
        self.save()


class FunctionalRequirementDocumentView(models.Model):
    """Registra las visitas a la página pública de un DRF"""
    
    document = models.ForeignKey(
        FunctionalRequirementDocument,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=gettext_lazy('Documento')
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=gettext_lazy('Dirección IP'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        verbose_name=gettext_lazy('User Agent'),
        blank=True
    )
    referrer = models.URLField(
        verbose_name=gettext_lazy('Referrer'),
        blank=True,
        max_length=500
    )
    viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de visita')
    )
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = gettext_lazy('Vista de DRF')
        verbose_name_plural = gettext_lazy('Vistas de DRF')
    
    def __str__(self):
        return f"{self.document.sequence} - {self.viewed_at.strftime('%d/%m/%Y %H:%M')}"


class FunctionalRequirementComment(models.Model):
    """Comentarios en los requerimientos funcionales"""
    
    requirement = models.ForeignKey(
        FunctionalRequirement,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Requerimiento')
    )
    author_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del autor')
    )
    author_email = models.EmailField(
        verbose_name=gettext_lazy('Email del autor')
    )
    comment = models.TextField(
        verbose_name=gettext_lazy('Comentario')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Comentario de Requerimiento')
        verbose_name_plural = gettext_lazy('Comentarios de Requerimientos')
    
    def __str__(self):
        return f"Comentario de {self.author_name} en Req #{self.requirement.number}"


class AccessGroup(models.Model):
    """Modelo para grupos de accesos rápidos"""
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del Grupo'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    is_public = models.BooleanField(default=False, verbose_name=gettext_lazy('Público'))
    share_token = models.CharField(max_length=50, unique=True, blank=True, verbose_name=gettext_lazy('Token de Compartir'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_groups', verbose_name=gettext_lazy('Creado por'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última Actualización'))
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = gettext_lazy('Grupo de Accesos')
        verbose_name_plural = gettext_lazy('Grupos de Accesos')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = str(uuid.uuid4())[:12]
        super().save(*args, **kwargs)
    
    def get_public_url(self):
        """Retorna la URL pública del grupo"""
        if self.is_public and self.share_token:
            from django.urls import reverse
            return reverse('access_group_public', kwargs={'token': self.share_token})
        return None


class AccessLink(models.Model):
    """Modelo para enlaces dentro de un grupo de accesos"""
    group = models.ForeignKey(AccessGroup, on_delete=models.CASCADE, related_name='links', verbose_name=gettext_lazy('Grupo'))
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del Enlace'))
    url = models.URLField(max_length=500, verbose_name=gettext_lazy('URL'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name=gettext_lazy('Icono'),
        help_text=gettext_lazy('Clase de icono Bootstrap (ej: bi-link-45deg)')
    )
    color = models.CharField(
        max_length=20,
        default='primary',
        verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color del botón (primary, success, info, warning, danger, etc.)')
    )
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activo'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Enlace de Acceso')
        verbose_name_plural = gettext_lazy('Enlaces de Acceso')
    
    def __str__(self):
        return f"{self.title} ({self.group.title})"


# ============= MODELOS DE PLANIFICACIÓN DE TAREAS =============

class TaskPlan(models.Model):
    """Modelo para plan de tareas con días"""
    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título del Plan'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_plans', verbose_name=gettext_lazy('Creado por'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última Actualización'))
    is_public = models.BooleanField(default=False, verbose_name=gettext_lazy('Vista Pública Activada'))
    share_token = models.CharField(max_length=50, unique=True, blank=True, verbose_name=gettext_lazy('Token de Compartir'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Plan de Tareas')
        verbose_name_plural = gettext_lazy('Planes de Tareas')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = str(uuid.uuid4())[:12]
        super().save(*args, **kwargs)
    
    def get_public_url(self):
        """Retorna la URL pública del plan"""
        if self.is_public and self.share_token:
            from django.urls import reverse
            return reverse('task_plan_public', kwargs={'token': self.share_token})
        return None


class TaskPlanDay(models.Model):
    """Modelo para días dentro de un plan de tareas"""
    plan = models.ForeignKey(TaskPlan, on_delete=models.CASCADE, related_name='days', verbose_name=gettext_lazy('Plan'))
    title = models.CharField(max_length=100, verbose_name=gettext_lazy('Título del Día'), help_text=gettext_lazy('Ej: Día 1, Lunes, Semana 1'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción del Día'))
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Día del Plan')
        verbose_name_plural = gettext_lazy('Días del Plan')
        unique_together = ['plan', 'order']
    
    def __str__(self):
        return f"{self.title} - {self.plan.title}"


class TaskPlanItem(models.Model):
    """Modelo para tareas individuales dentro de un día"""
    day = models.ForeignKey(TaskPlanDay, on_delete=models.CASCADE, related_name='tasks', verbose_name=gettext_lazy('Día'))
    title = models.CharField(max_length=300, verbose_name=gettext_lazy('Título de la Tarea'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    is_completed = models.BooleanField(default=False, verbose_name=gettext_lazy('Completada'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Completada el'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    
    # Campos opcionales para mayor detalle
    estimated_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=gettext_lazy('Horas Estimadas')
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', gettext_lazy('Baja')),
            ('medium', gettext_lazy('Media')),
            ('high', gettext_lazy('Alta')),
            ('critical', gettext_lazy('Crítica'))
        ],
        default='medium',
        verbose_name=gettext_lazy('Prioridad')
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Tarea del Plan')
        verbose_name_plural = gettext_lazy('Tareas del Plan')
    
    def __str__(self):
        return f"{self.title} ({self.day.title})"


# ===================================
# MODELOS DE CHECKLIST
# ===================================

class Checklist(models.Model):
    """Modelo para checklist con tareas"""
    title = models.CharField(max_length=300, verbose_name=gettext_lazy('Título del Checklist'))
    company = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Empresa'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklists_assigned',
        verbose_name=gettext_lazy('Usuario Asignado')
    )
    is_public = models.BooleanField(default=False, verbose_name=gettext_lazy('Público'))
    public_can_toggle = models.BooleanField(default=True, verbose_name=gettext_lazy('Permitir marcar tareas públicamente'))
    share_token = models.CharField(max_length=100, unique=True, blank=True, verbose_name=gettext_lazy('Token de Compartir'))
    views_count = models.IntegerField(default=0, verbose_name=gettext_lazy('Visualizaciones'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=gettext_lazy('Creado por'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última Actualización'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Checklist')
        verbose_name_plural = gettext_lazy('Checklists')
    
    def __str__(self):
        return f"{self.title} - {self.company}" if self.company else self.title
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = str(uuid.uuid4())[:12]
        super().save(*args, **kwargs)
    
    def get_public_url(self):
        return f"/checklist/{self.share_token}/"
    
    def get_completion_percentage(self):
        """Calcular porcentaje de completado"""
        total = self.items.count()
        if total == 0:
            return 0
        completed = self.items.filter(is_completed=True).count()
        return int((completed / total) * 100)


class ChecklistItem(models.Model):
    """Modelo para items individuales del checklist"""
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items', verbose_name=gettext_lazy('Checklist'))
    title = models.CharField(max_length=500, verbose_name=gettext_lazy('Título de la Tarea'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    notes = models.TextField(blank=True, verbose_name=gettext_lazy('Notas adicionales'))
    url = models.URLField(blank=True, verbose_name=gettext_lazy('Enlace URL'))
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=gettext_lazy('Costo'))
    order = models.IntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    is_completed = models.BooleanField(default=False, verbose_name=gettext_lazy('Completada'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Completada el'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Item del Checklist')
        verbose_name_plural = gettext_lazy('Items del Checklist')
    
    def __str__(self):
        return f"{self.title} ({self.checklist.title})"


class Transaction(models.Model):
    """Modelo para transacciones rápidas - accesos directos a URLs del sistema"""
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=gettext_lazy('Código'),
        help_text=gettext_lazy('Código único de la transacción (ej: T001, TICKET, REPORTE)')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre'),
        help_text=gettext_lazy('Nombre descriptivo de la transacción')
    )
    
    url = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('URL'),
        help_text=gettext_lazy('URL de acceso (puede ser relativa o absoluta)')
    )
    
    visible_for_all = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Visible para Todos'),
        help_text=gettext_lazy('Si está marcado, todos pueden ver esta transacción. Si no, solo agentes.')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción opcional de la transacción')
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='bi-link-45deg',
        verbose_name=gettext_lazy('Ícono Bootstrap'),
        help_text=gettext_lazy('Clase del ícono Bootstrap (ej: bi-link-45deg, bi-file-text)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Solo las transacciones activas aparecen en la búsqueda')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transactions',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última Actualización'))
    
    class Meta:
        ordering = ['code']
        verbose_name = gettext_lazy('Transacción')
        verbose_name_plural = gettext_lazy('Transacciones')
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class KnowledgeBase(models.Model):
    """Modelo para Base de Conocimientos - conceptos técnicos y código fuente"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título del concepto o tema')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción detallada del concepto')
    )
    
    source_code = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Código Fuente'),
        help_text=gettext_lazy('Código fuente de ejemplo o snippet')
    )
    
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por comas (ej: python, django, api)')
    )
    
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Categoría'),
        help_text=gettext_lazy('Categoría del conocimiento (ej: Backend, Frontend, Base de Datos)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='knowledge_bases_created',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de Creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última Actualización'))
    
    # Campos para compartir públicamente
    public_share_enabled = models.BooleanField(default=False, verbose_name=gettext_lazy('Compartir Públicamente'))
    public_share_token = models.CharField(max_length=64, unique=True, null=True, blank=True, verbose_name=gettext_lazy('Token de Compartir'))
    public_share_password = models.CharField(max_length=128, blank=True, verbose_name=gettext_lazy('Contraseña de Acceso'))
    public_share_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=gettext_lazy('Fecha de Expiración'))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Base de Conocimiento')
        verbose_name_plural = gettext_lazy('Base de Conocimientos')
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.title
    
    def generate_share_token(self):
        """Genera un token único para compartir"""
        import secrets
        self.public_share_token = secrets.token_urlsafe(32)
        self.save()
        return self.public_share_token
    
    def get_share_url(self, request=None):
        """Obtiene la URL pública de compartir"""
        if not self.public_share_token:
            return None
        
        from django.urls import reverse
        try:
            path = reverse('knowledge_base_public', kwargs={'token': self.public_share_token})
            if request:
                return request.build_absolute_uri(path)
            return path
        except:
            return None
    
    def is_share_valid(self):
        """Verifica si el compartir está activo y no ha expirado"""
        if not self.public_share_enabled:
            return False
        
        if self.public_share_expires_at:
            from django.utils import timezone
            if timezone.now() > self.public_share_expires_at:
                return False
        
        return True


class Translation(models.Model):
    """Modelo para almacenar traducciones realizadas con IA"""
    
    LANGUAGES = [
        ('es', 'Español'),
        ('en', 'Inglés'),
        ('fr', 'Francés'),
        ('de', 'Alemán'),
        ('it', 'Italiano'),
        ('pt', 'Portugués'),
        ('ru', 'Ruso'),
        ('zh', 'Chino'),
        ('ja', 'Japonés'),
        ('ko', 'Coreano'),
        ('ar', 'Árabe'),
        ('hi', 'Hindi'),
        ('tr', 'Turco'),
        ('nl', 'Neerlandés'),
        ('pl', 'Polaco'),
        ('sv', 'Sueco'),
        ('no', 'Noruego'),
        ('da', 'Danés'),
        ('fi', 'Finlandés'),
        ('cs', 'Checo'),
        ('ca', 'Catalán'),
        ('val', 'Valenciano'),
    ]
    
    source_language = models.CharField(
        max_length=10,
        choices=LANGUAGES,
        default='en',
        verbose_name=gettext_lazy('Idioma Origen')
    )
    
    target_language = models.CharField(
        max_length=10,
        choices=LANGUAGES,
        default='es',
        verbose_name=gettext_lazy('Idioma Destino')
    )
    
    source_text = models.TextField(
        verbose_name=gettext_lazy('Texto Original'),
        help_text=gettext_lazy('Texto a traducir')
    )
    
    translated_text = models.TextField(
        verbose_name=gettext_lazy('Texto Traducido'),
        help_text=gettext_lazy('Resultado de la traducción')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_language']),
            models.Index(fields=['target_language']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = gettext_lazy('Traducción')
        verbose_name_plural = gettext_lazy('Traducciones')
    
    def __str__(self):
        return f"{self.get_source_language_display()} → {self.get_target_language_display()} ({self.created_at.strftime('%Y-%m-%d')})"


class SQLQuery(models.Model):
    """Modelo para almacenar consultas SQL y sus resultados"""
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Consulta'),
        help_text=gettext_lazy('Nombre descriptivo para identificar la consulta')
    )
    
    query = models.TextField(
        verbose_name=gettext_lazy('Consulta SQL'),
        help_text=gettext_lazy('Solo se permiten consultas SELECT')
    )
    
    result = models.TextField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Resultado'),
        help_text=gettext_lazy('Resultado de la última ejecución')
    )
    
    row_count = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Cantidad de Filas'),
        help_text=gettext_lazy('Número de filas retornadas')
    )
    
    execution_time = models.FloatField(
        default=0.0,
        verbose_name=gettext_lazy('Tiempo de Ejecución'),
        help_text=gettext_lazy('Tiempo de ejecución en segundos')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sql_queries',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    last_executed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última ejecución')
    )
    
    is_favorite = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Favorito')
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_favorite']),
        ]
        verbose_name = gettext_lazy('Consulta SQL')
        verbose_name_plural = gettext_lazy('Consultas SQL')
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"


class OdooConnection(models.Model):
    """Modelo para almacenar configuraciones de conexión a Odoo"""
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre de la Conexión'),
        help_text=gettext_lazy('Nombre descriptivo para identificar esta conexión')
    )
    
    url = models.URLField(
        verbose_name=gettext_lazy('URL de Odoo'),
        help_text=gettext_lazy('URL completa del servidor Odoo (ej: https://miodoo.com)')
    )
    
    port = models.IntegerField(
        default=8069,
        verbose_name=gettext_lazy('Puerto'),
        help_text=gettext_lazy('Puerto del servidor Odoo')
    )
    
    database = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Base de Datos'),
        help_text=gettext_lazy('Nombre de la base de datos en Odoo')
    )
    
    username = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Usuario'),
        help_text=gettext_lazy('Usuario de Odoo')
    )
    
    password = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Contraseña'),
        help_text=gettext_lazy('Contraseña del usuario')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    is_private = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Privada'),
        help_text=gettext_lazy('Si está marcada como privada, solo el usuario creador puede verla y usarla')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='odoo_connections',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    last_tested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Última prueba de conexión')
    )
    
    connection_status = models.CharField(
        max_length=50,
        default='not_tested',
        choices=[
            ('not_tested', gettext_lazy('No probada')),
            ('success', gettext_lazy('Exitosa')),
            ('failed', gettext_lazy('Fallida')),
        ],
        verbose_name=gettext_lazy('Estado de Conexión')
    )
    
    # Portal público para todas las tablas
    public_portal_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Portal Público Habilitado'),
        help_text=gettext_lazy('Permite acceso público a todas las tablas de esta conexión')
    )
    
    public_portal_token = models.CharField(
        max_length=64,
        blank=True,
        unique=True,
        null=True,
        verbose_name=gettext_lazy('Token del Portal Público'),
        help_text=gettext_lazy('Token único para acceso al portal público')
    )
    
    public_portal_password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=gettext_lazy('Contraseña del Portal'),
        help_text=gettext_lazy('Dejar en blanco para permitir acceso sin contraseña')
    )
    
    public_portal_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Expiración del Portal'),
        help_text=gettext_lazy('Fecha en que expira el acceso al portal (opcional)')
    )
    
    public_portal_allow_import = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Permitir Importación'),
        help_text=gettext_lazy('Si está activo, los usuarios pueden importar datos. Si no, solo pueden descargar plantillas')
    )
    
    # Portal público de operaciones RPC
    public_operations_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Portal de Operaciones Público Habilitado'),
        help_text=gettext_lazy('Permite acceso público al portal de operaciones RPC')
    )
    
    public_operations_token = models.CharField(
        max_length=64,
        blank=True,
        unique=True,
        null=True,
        verbose_name=gettext_lazy('Token del Portal de Operaciones'),
        help_text=gettext_lazy('Token único para acceso al portal de operaciones RPC')
    )
    
    public_operations_password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=gettext_lazy('Contraseña del Portal de Operaciones'),
        help_text=gettext_lazy('Dejar en blanco para permitir acceso sin contraseña')
    )
    
    public_operations_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Expiración del Portal de Operaciones'),
        help_text=gettext_lazy('Fecha en que expira el acceso al portal de operaciones (opcional)')
    )
    
    public_operations_read_only = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Portal de Operaciones Solo Lectura'),
        help_text=gettext_lazy('Si está activo, solo permite operaciones de búsqueda (no crear, actualizar o eliminar)')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Conexión Odoo')
        verbose_name_plural = gettext_lazy('Conexiones Odoo')
    
    def __str__(self):
        return f"{self.name} ({self.database})"
    
    def generate_portal_token(self):
        """Generar token único para portal público"""
        import secrets
        self.public_portal_token = secrets.token_urlsafe(32)
        self.save()
        return self.public_portal_token
    
    def get_portal_url(self, request=None):
        """Obtener URL del portal público"""
        if not self.public_portal_enabled or not self.public_portal_token:
            return None
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(
                reverse('odoo_rpc_public_portal', kwargs={'token': self.public_portal_token})
            )
        return f"/public/odoo-portal/{self.public_portal_token}/"
    
    def is_portal_valid(self):
        """Verificar si el portal público sigue siendo válido"""
        if not self.public_portal_enabled:
            return False
        if self.public_portal_expires_at:
            from django.utils import timezone
            return timezone.now() < self.public_portal_expires_at
        return True
    
    def generate_operations_token(self):
        """Generar token único para portal de operaciones RPC"""
        import secrets
        self.public_operations_token = secrets.token_urlsafe(32)
        self.save()
        return self.public_operations_token
    
    def get_operations_url(self, request=None):
        """Obtener URL del portal de operaciones público"""
        if not self.public_operations_enabled or not self.public_operations_token:
            return None
        if request:
            from django.urls import reverse
            try:
                return request.build_absolute_uri(
                    reverse('odoo_rpc_public_operations', kwargs={'token': self.public_operations_token})
                )
            except:
                # Fallback si la ruta no existe aún
                return request.build_absolute_uri(f"/public/odoo-operations/{self.public_operations_token}/")
        return f"/public/odoo-operations/{self.public_operations_token}/"
    
    def is_operations_valid(self):
        """Verificar si el portal de operaciones público sigue siendo válido"""
        if not self.public_operations_enabled:
            return False
        if self.public_operations_expires_at:
            from django.utils import timezone
            return timezone.now() < self.public_operations_expires_at
        return True


class OdooRPCTable(models.Model):
    """Modelo para definir tablas de Odoo a sincronizar"""
    
    connection = models.ForeignKey(
        OdooConnection,
        on_delete=models.CASCADE,
        related_name='rpc_tables',
        verbose_name=gettext_lazy('Conexión')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre Descriptivo'),
        help_text=gettext_lazy('Nombre descriptivo de la tabla')
    )
    
    odoo_model = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Modelo Odoo'),
        help_text=gettext_lazy('Nombre del modelo en Odoo (ej: product.product, res.partner)')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción de la tabla y su propósito')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='odoo_rpc_tables',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    # Campos para URL pública
    public_url_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('URL Pública Habilitada'),
        help_text=gettext_lazy('Permite acceso público para importar datos')
    )
    
    public_url_token = models.CharField(
        max_length=64,
        blank=True,
        unique=True,
        null=True,
        verbose_name=gettext_lazy('Token de URL Pública'),
        help_text=gettext_lazy('Token único para acceso público')
    )
    
    public_url_password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=gettext_lazy('Contraseña de URL Pública'),
        help_text=gettext_lazy('Dejar en blanco para permitir acceso sin contraseña')
    )
    
    public_url_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Expiración'),
        help_text=gettext_lazy('Fecha en que expira el acceso público (opcional)')
    )
    
    # Campos para formulario público de creación
    public_form_enabled = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Formulario Público Habilitado'),
        help_text=gettext_lazy('Permite crear registros vía formulario público')
    )
    
    public_form_token = models.CharField(
        max_length=64,
        blank=True,
        unique=True,
        null=True,
        verbose_name=gettext_lazy('Token de Formulario Público'),
        help_text=gettext_lazy('Token único para formulario público')
    )
    
    public_form_password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=gettext_lazy('Contraseña de Formulario Público'),
        help_text=gettext_lazy('Dejar en blanco para permitir acceso sin contraseña')
    )
    
    public_form_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de Expiración del Formulario'),
        help_text=gettext_lazy('Fecha en que expira el formulario público (opcional)')
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ['connection', 'odoo_model']
        verbose_name = gettext_lazy('Tabla RPC Odoo')
        verbose_name_plural = gettext_lazy('Tablas RPC Odoo')
    
    def __str__(self):
        return f"{self.name} ({self.odoo_model})"
    
    def generate_public_token(self):
        """Generar token único para URL pública"""
        import secrets
        self.public_url_token = secrets.token_urlsafe(32)
        self.save()
        return self.public_url_token
    
    def get_public_url(self, request=None):
        """Obtener URL pública para importación"""
        if not self.public_url_enabled or not self.public_url_token:
            return None
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(
                reverse('odoo_rpc_public_import', kwargs={'token': self.public_url_token})
            )
        return f"/public/odoo-import/{self.public_url_token}/"
    
    def is_public_url_valid(self):
        """Verificar si la URL pública sigue siendo válida"""
        if not self.public_url_enabled:
            return False
        if self.public_url_expires_at:
            from django.utils import timezone
            return timezone.now() < self.public_url_expires_at
        return True
    
    def generate_form_token(self):
        """Generar token único para formulario público"""
        import secrets
        self.public_form_token = secrets.token_urlsafe(32)
        self.save()
        return self.public_form_token
    
    def get_form_url(self, request=None):
        """Obtener URL pública para formulario de creación"""
        if not self.public_form_enabled or not self.public_form_token:
            return None
        if request:
            from django.urls import reverse
            try:
                return request.build_absolute_uri(
                    reverse('odoo_rpc_public_form', kwargs={'token': self.public_form_token})
                )
            except:
                return request.build_absolute_uri(f"/public/odoo-form/{self.public_form_token}/")
        return f"/public/odoo-form/{self.public_form_token}/"
    
    def is_form_valid(self):
        """Verificar si el formulario público sigue siendo válido"""
        if not self.public_form_enabled:
            return False
        if self.public_form_expires_at:
            from django.utils import timezone
            return timezone.now() < self.public_form_expires_at
        return True


class OdooRPCField(models.Model):
    """Modelo para definir campos de las tablas Odoo"""
    
    FIELD_TYPES = [
        ('char', 'Texto'),
        ('text', 'Texto Largo'),
        ('integer', 'Entero'),
        ('float', 'Decimal'),
        ('boolean', 'Booleano'),
        ('date', 'Fecha'),
        ('datetime', 'Fecha y Hora'),
        ('selection', 'Selección'),
        ('many2one', 'Relación Many2One'),
        ('one2many', 'Relación One2Many'),
        ('many2many', 'Relación Many2Many'),
    ]
    
    table = models.ForeignKey(
        OdooRPCTable,
        on_delete=models.CASCADE,
        related_name='rpc_fields',
        verbose_name=gettext_lazy('Tabla')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre Descriptivo'),
        help_text=gettext_lazy('Nombre descriptivo del campo')
    )
    
    odoo_field_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre del Campo en Odoo'),
        help_text=gettext_lazy('Nombre técnico del campo en Odoo (ej: name, default_code)')
    )
    
    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default='char',
        verbose_name=gettext_lazy('Tipo de Campo')
    )
    
    is_required = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Requerido'),
        help_text=gettext_lazy('Si el campo es obligatorio')
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en Excel')
    )
    
    help_text = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Texto de Ayuda'),
        help_text=gettext_lazy('Instrucciones para llenar este campo')
    )
    
    class Meta:
        ordering = ['table', 'order', 'name']
        unique_together = ['table', 'odoo_field_name']
        verbose_name = gettext_lazy('Campo RPC Odoo')
        verbose_name_plural = gettext_lazy('Campos RPC Odoo')
    
    def __str__(self):
        return f"{self.name} ({self.odoo_field_name})"


class OdooRPCData(models.Model):
    """Modelo para almacenar datos temporales antes de enviar a Odoo"""
    
    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('processing', gettext_lazy('Procesando')),
        ('success', gettext_lazy('Exitoso')),
        ('failed', gettext_lazy('Fallido')),
        ('fetched', gettext_lazy('Obtenido')),
    ]
    
    table = models.ForeignKey(
        OdooRPCTable,
        on_delete=models.CASCADE,
        related_name='rpc_data',
        verbose_name=gettext_lazy('Tabla')
    )
    
    data = models.JSONField(
        verbose_name=gettext_lazy('Datos'),
        help_text=gettext_lazy('Datos en formato JSON para enviar a Odoo')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=gettext_lazy('Estado')
    )
    
    odoo_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('ID en Odoo'),
        help_text=gettext_lazy('ID del registro creado en Odoo')
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Mensaje de Error'),
        help_text=gettext_lazy('Mensaje de error si la sincronización falló')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='odoo_rpc_data',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de procesamiento')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Dato RPC Odoo')
        verbose_name_plural = gettext_lazy('Datos RPC Odoo')
    
    def __str__(self):
        return f"{self.table.name} - {self.status} ({self.created_at.strftime('%Y-%m-%d')})"


class OdooRPCImportFile(models.Model):
    """Modelo para almacenar archivos de importación"""
    
    table = models.ForeignKey(
        OdooRPCTable,
        on_delete=models.CASCADE,
        related_name='import_files',
        verbose_name=gettext_lazy('Tabla')
    )
    
    file = models.FileField(
        upload_to='odoo_rpc_imports/%Y/%m/',
        verbose_name=gettext_lazy('Archivo')
    )
    
    original_filename = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy('Nombre Original')
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='odoo_rpc_imports',
        verbose_name=gettext_lazy('Subido por')
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de subida')
    )
    
    records_imported = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Registros importados')
    )
    
    records_success = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Registros exitosos')
    )
    
    records_failed = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Registros fallidos')
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = gettext_lazy('Archivo de Importación RPC')
        verbose_name_plural = gettext_lazy('Archivos de Importación RPC')
    
    def __str__(self):
        return f"{self.original_filename} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


# ==================== CHATBOT ====================

class Chatbot(models.Model):
    """Modelo para chatbots configurables"""
    
    TYPE_CHOICES = [
        ('internal', gettext_lazy('Interno (Solo esta web)')),
        ('external', gettext_lazy('Externo (Script integrable)')),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título del Chatbot')
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='internal',
        verbose_name=gettext_lazy('Tipo de Chatbot')
    )
    
    description = models.TextField(
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Describe el propósito del chatbot (ej: Agente de ventas que se dedica a captar leads)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    
    use_ai = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Usar IA'),
        help_text=gettext_lazy('Habilitar asistencia de IA para respuestas no configuradas')
    )
    
    ai_context = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Contexto para IA'),
        help_text=gettext_lazy('Información adicional para que la IA entienda el contexto del negocio')
    )
    
    welcome_message = models.TextField(
        default='¡Hola! ¿En qué puedo ayudarte?',
        verbose_name=gettext_lazy('Mensaje de bienvenida')
    )
    
    # Personalización visual
    primary_color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=gettext_lazy('Color primario'),
        help_text=gettext_lazy('Color del botón y encabezado (formato: #RRGGBB)')
    )
    
    secondary_color = models.CharField(
        max_length=7,
        default='#0056b3',
        verbose_name=gettext_lazy('Color secundario'),
        help_text=gettext_lazy('Color secundario para efectos hover (formato: #RRGGBB)')
    )
    
    bot_message_color = models.CharField(
        max_length=7,
        default='#f0f0f0',
        verbose_name=gettext_lazy('Color mensajes del bot'),
        help_text=gettext_lazy('Color de fondo para los mensajes del bot (formato: #RRGGBB)')
    )
    
    user_message_color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=gettext_lazy('Color mensajes del usuario'),
        help_text=gettext_lazy('Color de fondo para los mensajes del usuario (formato: #RRGGBB)')
    )
    
    icon_choice = models.CharField(
        max_length=20,
        choices=[
            ('chat', gettext_lazy('Chat (por defecto)')),
            ('robot', gettext_lazy('Robot')),
            ('headset', gettext_lazy('Auriculares')),
            ('person', gettext_lazy('Persona')),
        ],
        default='chat',
        verbose_name=gettext_lazy('Icono del botón'),
        help_text=gettext_lazy('Icono que se muestra en el botón flotante')
    )
    
    position = models.CharField(
        max_length=20,
        choices=[
            ('bottom-right', gettext_lazy('Inferior Derecha')),
            ('bottom-left', gettext_lazy('Inferior Izquierda')),
        ],
        default='bottom-right',
        verbose_name=gettext_lazy('Posición en pantalla')
    )
    
    # Integración externa
    script_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Token de script'),
        help_text=gettext_lazy('Token único para integración externa')
    )
    
    allowed_domains = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Dominios permitidos'),
        help_text=gettext_lazy('Dominios donde se puede integrar (uno por línea). Dejar vacío para permitir todos.')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chatbots_created',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Comportamiento
    response_delay = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Tiempo de espera (segundos)'),
        help_text=gettext_lazy('Segundos que espera el bot antes de responder (0 = inmediato)')
    )
    
    # Estadísticas
    total_conversations = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de conversaciones')
    )
    
    total_messages = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de mensajes')
    )
    
    total_clicks = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Total de clicks en el botón'),
        help_text=gettext_lazy('Número de veces que han dado click para abrir el chat')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Chatbot')
        verbose_name_plural = gettext_lazy('Chatbots')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generar token si no tiene (para todos los chatbots)
        if not self.script_token:
            import secrets
            self.script_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def get_script_url(self):
        """Retorna la URL del script para integración"""
        if self.type == 'external' and self.script_token:
            from django.urls import reverse
            return reverse('chatbot_script', kwargs={'token': self.script_token})
        return None


class ChatbotQuestion(models.Model):
    """Preguntas y respuestas configuradas para el chatbot"""
    
    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=gettext_lazy('Chatbot')
    )
    
    question = models.CharField(
        max_length=500,
        verbose_name=gettext_lazy('Pregunta'),
        help_text=gettext_lazy('Pregunta que el usuario puede hacer')
    )
    
    keywords = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=gettext_lazy('Palabras clave'),
        help_text=gettext_lazy('Palabras clave separadas por comas para detectar esta pregunta')
    )
    
    answer = models.TextField(
        verbose_name=gettext_lazy('Respuesta'),
        help_text=gettext_lazy('Respuesta que el chatbot dará')
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
        help_text=gettext_lazy('Orden de aparición en sugerencias')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa')
    )
    
    use_ai = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Mejorar con IA'),
        help_text=gettext_lazy('La IA puede expandir o mejorar esta respuesta')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    # Estadísticas
    times_used = models.IntegerField(
        default=0,
        verbose_name=gettext_lazy('Veces utilizada')
    )
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = gettext_lazy('Pregunta del Chatbot')
        verbose_name_plural = gettext_lazy('Preguntas del Chatbot')
    
    def __str__(self):
        return f"{self.question[:50]}..."
    
    def get_keywords_list(self):
        """Retorna lista de keywords"""
        if self.keywords:
            return [k.strip().lower() for k in self.keywords.split(',')]
        return []


class ChatbotConversation(models.Model):
    """Conversación de un usuario con el chatbot"""
    
    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name=gettext_lazy('Chatbot')
    )
    
    session_id = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('ID de sesión')
    )
    
    user_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email del usuario'),
        help_text=gettext_lazy('Email capturado durante la conversación')
    )
    
    user_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre del usuario')
    )
    
    user_phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=gettext_lazy('Teléfono del usuario')
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Dirección IP'),
        help_text=gettext_lazy('IP del usuario en la sesión')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('País'),
        help_text=gettext_lazy('País detectado del usuario')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=gettext_lazy('Ciudad'),
        help_text=gettext_lazy('Ciudad detectada del usuario')
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Inicio de conversación')
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actividad')
    )
    
    is_lead = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Es lead'),
        help_text=gettext_lazy('Marcado si se capturó información de contacto')
    )
    
    lead_quality = models.CharField(
        max_length=20,
        choices=[
            ('hot', gettext_lazy('Caliente')),
            ('warm', gettext_lazy('Tibio')),
            ('cold', gettext_lazy('Frío')),
        ],
        blank=True,
        verbose_name=gettext_lazy('Calidad del lead')
    )
    
    hide_chat = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Ocultar chat'),
        help_text=gettext_lazy('Si está marcado, el chat no se mostrará a este usuario')
    )
    
    reviewed = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Revisada'),
        help_text=gettext_lazy('Marca si la conversación ya fue revisada por un administrador')
    )
    
    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de revisión')
    )
    
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Revisada por')
    )
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = gettext_lazy('Conversación del Chatbot')
        verbose_name_plural = gettext_lazy('Conversaciones del Chatbot')
    
    def __str__(self):
        return f"Conversación {self.session_id[:8]} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class ChatbotMessage(models.Model):
    """Mensajes individuales en una conversación"""
    
    conversation = models.ForeignKey(
        ChatbotConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=gettext_lazy('Conversación')
    )
    
    is_bot = models.BooleanField(
        verbose_name=gettext_lazy('Es del bot'),
        help_text=gettext_lazy('True si es mensaje del bot, False si es del usuario')
    )
    
    message = models.TextField(
        verbose_name=gettext_lazy('Mensaje')
    )
    
    matched_question = models.ForeignKey(
        ChatbotQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_messages',
        verbose_name=gettext_lazy('Pregunta coincidente')
    )
    
    used_ai = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Usó IA'),
        help_text=gettext_lazy('True si la respuesta fue generada por IA')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Hora del mensaje')
    )
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = gettext_lazy('Mensaje del Chatbot')
        verbose_name_plural = gettext_lazy('Mensajes del Chatbot')
    
    def __str__(self):
        sender = "Bot" if self.is_bot else "Usuario"
        return f"{sender}: {self.message[:50]}..."


class ChatbotClick(models.Model):
    """Registro de clicks en el botón del chatbot"""
    
    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name='clicks',
        verbose_name=gettext_lazy('Chatbot')
    )
    
    clicked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha del click')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    
    class Meta:
        ordering = ['-clicked_at']
        verbose_name = gettext_lazy('Click del Chatbot')
        verbose_name_plural = gettext_lazy('Clicks del Chatbot')
        indexes = [
            models.Index(fields=['chatbot', '-clicked_at']),
        ]
    
    def __str__(self):
        return f"Click en {self.chatbot.title} - {self.clicked_at.strftime('%Y-%m-%d %H:%M')}"


class PrivacyPolicy(models.Model):
    """Modelo para políticas de privacidad"""
    title = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=gettext_lazy('Título'),
        help_text=gettext_lazy('Título de la política de privacidad')
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=gettext_lazy('Slug'),
        help_text=gettext_lazy('URL amigable (se genera automáticamente del título)')
    )
    content = models.TextField(
        verbose_name=gettext_lazy('Contenido'),
        help_text=gettext_lazy('Contenido completo de la política de privacidad')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activa'),
        help_text=gettext_lazy('Indica si la política está activa y visible públicamente')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_privacy_policies',
        verbose_name=gettext_lazy('Creado por')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Política de Privacidad')
        verbose_name_plural = gettext_lazy('Políticas de Privacidad')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generar slug si no existe
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# ==================== ERP3 - FACTURAS DE 3ROS ====================

class Invoice(models.Model):
    """
    Modelo para gestionar facturas de terceros
    """
    sequence = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=gettext_lazy('Secuencia/Número'),
        help_text=gettext_lazy('Número de factura (ej: FAC-2025-001)')
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name=gettext_lazy('Cliente/Empresa'),
        help_text=gettext_lazy('Empresa a la que se factura')
    )
    
    invoice_date = models.DateField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Factura')
    )
    
    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Fecha de Vencimiento'),
        help_text=gettext_lazy('Fecha límite de pago (opcional)')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Notas'),
        help_text=gettext_lazy('Notas o comentarios adicionales')
    )
    
    footer_message = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Mensaje al pie'),
        help_text=gettext_lazy('Mensaje que aparecerá al final de la factura (condiciones de pago, términos, etc.)')
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Subtotal')
    )
    
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Impuestos')
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Total')
    )
    
    currency = models.CharField(
        max_length=10,
        choices=[
            ('EUR', gettext_lazy('Euro (€)')),
            ('USD', gettext_lazy('Dólar Americano ($)')),
            ('GBP', gettext_lazy('Libra Esterlina (£)')),
            ('JPY', gettext_lazy('Yen Japonés (¥)')),
            ('CAD', gettext_lazy('Dólar Canadiense (C$)')),
            ('AUD', gettext_lazy('Dólar Australiano (A$)')),
            ('CHF', gettext_lazy('Franco Suizo (CHF)')),
            ('CNY', gettext_lazy('Yuan Chino (¥)')),
            ('MXN', gettext_lazy('Peso Mexicano ($)')),
            ('COP', gettext_lazy('Peso Colombiano ($)')),
        ],
        default='USD',
        verbose_name=gettext_lazy('Moneda'),
        help_text=gettext_lazy('Moneda en la que se factura')
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', gettext_lazy('Borrador')),
            ('sent', gettext_lazy('Enviada')),
            ('paid', gettext_lazy('Pagada')),
            ('cancelled', gettext_lazy('Cancelada')),
        ],
        default='draft',
        verbose_name=gettext_lazy('Estado')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_invoices',
        verbose_name=gettext_lazy('Creado por')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=gettext_lazy('Última Actualización')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Factura de 3ros')
        verbose_name_plural = gettext_lazy('Facturas de 3ros')
    
    def __str__(self):
        return f"{self.sequence} - {self.company.name}"
    
    def get_currency_symbol(self):
        """Obtiene el símbolo de la moneda"""
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
        return currency_symbols.get(self.currency, '$')
    
    def format_amount(self, amount):
        """Formatea un monto con la moneda"""
        symbol = self.get_currency_symbol()
        if self.currency in ['EUR', 'GBP']:
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{symbol}{amount:,.2f}"
    
    def calculate_totals(self):
        """Calcula los totales de la factura basándose en las líneas"""
        lines = self.lines.all()
        self.subtotal = sum(line.subtotal for line in lines)
        self.tax_amount = sum(line.tax_amount for line in lines)
        self.total = self.subtotal + self.tax_amount
    
    def save(self, *args, **kwargs):
        # Si es una nueva factura y no tiene secuencia, generarla
        if not self.pk and not self.sequence:
            # Obtener el perfil del usuario
            user_profile = self.created_by.profile
            
            # Si el usuario tiene un prefijo personalizado, usarlo
            if user_profile.invoice_sequence_prefix:
                # Usar el prefijo y el número siguiente del usuario
                self.sequence = f"{user_profile.invoice_sequence_prefix}{user_profile.invoice_next_number:05d}"
                
                # Incrementar el próximo número en el perfil del usuario
                user_profile.invoice_next_number += 1
                user_profile.save(update_fields=['invoice_next_number'])
            else:
                # Usar el sistema de secuencia por defecto (fallback)
                from datetime import datetime
                year = datetime.now().year
                # Obtener el último número de secuencia del año para este usuario
                last_invoice = Invoice.objects.filter(
                    created_by=self.created_by,
                    sequence__startswith=f'FAC-{year}-'
                ).order_by('-sequence').first()
                
                if last_invoice:
                    last_num = int(last_invoice.sequence.split('-')[-1])
                    new_num = last_num + 1
                else:
                    new_num = 1
                
                self.sequence = f'FAC-{year}-{new_num:04d}'
        
        super().save(*args, **kwargs)


class InvoiceLine(models.Model):
    """
    Modelo para las líneas/detalles de factura
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=gettext_lazy('Factura')
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='invoice_lines',
        verbose_name=gettext_lazy('Producto'),
        help_text=gettext_lazy('Producto o servicio facturado')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción adicional del producto/servicio')
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name=gettext_lazy('Cantidad')
    )
    
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=gettext_lazy('Precio Unitario')
    )
    
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Tasa de Impuesto (%)'),
        help_text=gettext_lazy('Porcentaje de impuesto (ej: 21 para IVA 21%)')
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Subtotal')
    )
    
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Impuestos')
    )
    
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=gettext_lazy('Total Línea')
    )
    
    line_number = models.IntegerField(
        default=1,
        verbose_name=gettext_lazy('Número de Línea')
    )
    
    class Meta:
        ordering = ['line_number']
        verbose_name = gettext_lazy('Línea de Factura')
        verbose_name_plural = gettext_lazy('Líneas de Factura')
    
    def __str__(self):
        return f"{self.invoice.sequence} - Línea {self.line_number}: {self.product.name}"
    
    def calculate_amounts(self):
        """Calcula los montos de la línea"""
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.line_total = self.subtotal + self.tax_amount
    
    def save(self, *args, **kwargs):
        # Calcular montos antes de guardar
        self.calculate_amounts()
        super().save(*args, **kwargs)
        
        # Actualizar totales de la factura
        if self.invoice:
            self.invoice.calculate_totals()
            self.invoice.save()


class InvoiceMessage(models.Model):
    """
    Modelo para mensajes/comentarios en facturas
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=gettext_lazy('Factura')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoice_messages',
        verbose_name=gettext_lazy('Usuario')
    )
    
    message = models.TextField(
        verbose_name=gettext_lazy('Mensaje'),
        help_text=gettext_lazy('Mensaje o comentario sobre la factura')
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de Creación')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Mensaje de Factura')
        verbose_name_plural = gettext_lazy('Mensajes de Facturas')
    
    def __str__(self):
        return f"Mensaje de {self.user.username} en {self.invoice.sequence}"


class Manual(models.Model):
    """Modelo para manuales con título y URL"""

    title = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Título')
    )
    url = models.URLField(
        verbose_name=gettext_lazy('URL del Manual'),
        help_text=gettext_lazy('Enlace directo al manual (PDF, sitio web, etc.)')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Creado por')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = gettext_lazy('Manual')
        verbose_name_plural = gettext_lazy('Manuales')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_access_count(self):
        return self.accesses.count()


class ManualAccess(models.Model):
    """Registro de accesos/descargas de manuales por usuario"""

    manual = models.ForeignKey(
        Manual,
        on_delete=models.CASCADE,
        related_name='accesses',
        verbose_name=gettext_lazy('Manual')
    )
    accessed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manual_accesses',
        verbose_name=gettext_lazy('Accedido por')
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('User Agent')
    )
    accessed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=gettext_lazy('Fecha de acceso')
    )

    class Meta:
        ordering = ['-accessed_at']
        verbose_name = gettext_lazy('Acceso a Manual')
        verbose_name_plural = gettext_lazy('Accesos a Manuales')

    def __str__(self):
        user = self.accessed_by.username if self.accessed_by else 'Anónimo'
        return f"{self.manual.title} - {user} - {self.accessed_at}"


class ProjectBook(models.Model):
    """Libro de Proyecto: documento colaborativo con trazabilidad por empresa"""

    STATUS_CHOICES = [
        ('active', gettext_lazy('Activo')),
        ('on_hold', gettext_lazy('En Pausa')),
        ('completed', gettext_lazy('Completado')),
        ('cancelled', gettext_lazy('Cancelado')),
    ]

    title = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Título')
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
        help_text=gettext_lazy('Descripción general del proyecto')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_books',
        verbose_name=gettext_lazy('Empresa')
    )
    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_project_books',
        verbose_name=gettext_lazy('Usuario asignado')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_project_books',
        verbose_name=gettext_lazy('Creado por')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=gettext_lazy('Estado')
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de inicio')
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de cierre estimada')
    )
    share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token de compartir')
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Etiquetas'),
        help_text=gettext_lazy('Etiquetas separadas por coma')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Activo')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Creado el'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Actualizado el'))

    class Meta:
        verbose_name = gettext_lazy('Libro de Proyecto')
        verbose_name_plural = gettext_lazy('Libros de Proyecto')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_status_color(self):
        colors = {
            'active': 'success',
            'on_hold': 'warning',
            'completed': 'primary',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def get_tag_list(self):
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []


class ProjectBookEntry(models.Model):
    """Entrada de trazabilidad en un Libro de Proyecto"""

    book = models.ForeignKey(
        ProjectBook,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name=gettext_lazy('Libro de Proyecto')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_book_entries',
        verbose_name=gettext_lazy('Autor')
    )
    content = models.TextField(verbose_name=gettext_lazy('Contenido'))
    is_agent_entry = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Entrada de agente'),
        help_text=gettext_lazy('Indica si fue escrita por un agente')
    )
    attachment = models.FileField(
        upload_to='project_book_attachments/%Y/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Archivo adjunto')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha'))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = gettext_lazy('Entrada de Libro de Proyecto')
        verbose_name_plural = gettext_lazy('Entradas de Libros de Proyecto')
        ordering = ['created_at']

    def __str__(self):
        author = self.author.get_full_name() or self.author.username if self.author else 'Desconocido'
        return f"{self.book.title} – {author} – {self.created_at:%d/%m/%Y %H:%M}"


class RFI(models.Model):
    """Request for Information - Solicitud de información"""

    code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Código')
    )
    title = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Título')
    )
    text = models.TextField(
        verbose_name=gettext_lazy('Texto')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfis',
        verbose_name=gettext_lazy('Creado por')
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfis',
        verbose_name=gettext_lazy('Empresa')
    )
    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfis_assigned',
        verbose_name=gettext_lazy('Usuario asignado')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gettext_lazy('Fecha de creación')
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de cierre')
    )
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token público')
    )

    class Meta:
        verbose_name = gettext_lazy('RFI')
        verbose_name_plural = gettext_lazy('RFIs')
        ordering = ['-created_at']

    @property
    def is_closed(self):
        return self.closed_at is not None

    def __str__(self):
        return self.title

    @property
    def days_since_request(self):
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.days

    def save(self, *args, **kwargs):
        if not self.code:
            with transaction.atomic():
                last = RFI.objects.select_for_update().order_by('-id').first()
                if last and last.code and last.code.startswith('RF'):
                    try:
                        seq = int(last.code[2:]) + 1
                    except ValueError:
                        seq = 1
                else:
                    seq = 1
                self.code = f"RF{seq:05d}"
        super().save(*args, **kwargs)


class RFIComment(models.Model):
    """Comentario en un RFI"""

    rfi = models.ForeignKey(
        RFI,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('RFI')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfi_comments',
        verbose_name=gettext_lazy('Autor')
    )
    guest_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Nombre (invitado)')
    )
    guest_email = models.EmailField(
        blank=True,
        default='',
        verbose_name=gettext_lazy('Correo (invitado)')
    )
    text = models.TextField(verbose_name=gettext_lazy('Comentario'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha'))

    class Meta:
        verbose_name = gettext_lazy('Comentario RFI')
        verbose_name_plural = gettext_lazy('Comentarios RFI')
        ordering = ['created_at']

    def __str__(self):
        return f"Comentario de {self.author} en {self.rfi}"


# ─────────────────────────────────────────────────────────────
# CAPACITACIONES
# ─────────────────────────────────────────────────────────────

class Capacitacion(models.Model):
    """Capacitación asignable a usuarios y/o empresas"""

    titulo = models.CharField(max_length=300, verbose_name=gettext_lazy('Título'))
    temas = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Temas'),
        help_text=gettext_lazy('Descripción general de los temas que cubre la capacitación'),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='capacitaciones_creadas',
        verbose_name=gettext_lazy('Creado por'),
    )
    assigned_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='capacitaciones_asignadas',
        verbose_name=gettext_lazy('Usuarios asignados'),
    )
    assigned_companies = models.ManyToManyField(
        'Company',
        blank=True,
        related_name='capacitaciones_asignadas',
        verbose_name=gettext_lazy('Empresas asignadas'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))
    is_active = models.BooleanField(default=True, verbose_name=gettext_lazy('Activa'))
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token público'),
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Capacitación')
        verbose_name_plural = gettext_lazy('Capacitaciones')

    def __str__(self):
        return self.titulo

    def user_can_view(self, user):
        """Retorna True si el usuario tiene acceso a esta capacitación"""
        from tickets.utils import is_agent
        if is_agent(user) or user.is_staff or user.is_superuser:
            return True
        if self.assigned_users.filter(pk=user.pk).exists():
            return True
        user_company = getattr(getattr(user, 'profile', None), 'company', None)
        if user_company and self.assigned_companies.filter(pk=user_company.pk).exists():
            return True
        return False


class CapacitacionEnlace(models.Model):
    """Enlace de acceso (URL + credenciales) asociado a una capacitación"""

    capacitacion = models.ForeignKey(
        Capacitacion,
        on_delete=models.CASCADE,
        related_name='enlaces',
        verbose_name=gettext_lazy('Capacitación'),
    )
    orden = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    titulo = models.CharField(max_length=200, verbose_name=gettext_lazy('Título'))
    url = models.URLField(verbose_name=gettext_lazy('URL'))
    usuario = models.CharField(max_length=150, blank=True, verbose_name=gettext_lazy('Usuario'))
    contrasena = models.CharField(max_length=150, blank=True, verbose_name=gettext_lazy('Contraseña'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        ordering = ['orden', 'created_at']
        verbose_name = gettext_lazy('Enlace de Capacitación')
        verbose_name_plural = gettext_lazy('Enlaces de Capacitación')

    def __str__(self):
        return f"{self.capacitacion} – {self.titulo}"


class CapacitacionLinea(models.Model):
    """Línea/tarea de una capacitación (la llena el agente)"""

    capacitacion = models.ForeignKey(
        Capacitacion,
        on_delete=models.CASCADE,
        related_name='lineas',
        verbose_name=gettext_lazy('Capacitación'),
    )
    orden = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    tarea = models.CharField(max_length=500, verbose_name=gettext_lazy('Tarea'))
    descripcion = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    fecha = models.DateField(null=True, blank=True, verbose_name=gettext_lazy('Fecha'))
    clase = models.ForeignKey(
        'CapacitacionClase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tareas',
        verbose_name=gettext_lazy('Clase'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        ordering = ['orden', 'created_at']
        verbose_name = gettext_lazy('Línea de Capacitación')
        verbose_name_plural = gettext_lazy('Líneas de Capacitación')

    def __str__(self):
        return f"{self.capacitacion} – {self.tarea}"


class CapacitacionClase(models.Model):
    """Clase/sesión programada dentro de una capacitación"""

    capacitacion = models.ForeignKey(
        Capacitacion,
        on_delete=models.CASCADE,
        related_name='clases',
        verbose_name=gettext_lazy('Capacitación'),
    )
    orden = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    titulo = models.CharField(max_length=300, verbose_name=gettext_lazy('Título'))
    fecha = models.DateField(null=True, blank=True, verbose_name=gettext_lazy('Fecha'))
    enlace = models.URLField(blank=True, verbose_name=gettext_lazy('Enlace / URL'))
    descripcion = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    resumen = models.TextField(blank=True, verbose_name=gettext_lazy('Resumen de la clase'))
    public_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=gettext_lazy('Token público'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        ordering = ['orden', 'fecha', 'created_at']
        verbose_name = gettext_lazy('Clase de Capacitación')
        verbose_name_plural = gettext_lazy('Clases de Capacitación')

    def __str__(self):
        return f"{self.capacitacion} – {self.titulo}"


class CapacitacionAsistencia(models.Model):
    """Registro de asistencia de una persona a una clase de capacitación"""

    clase = models.ForeignKey(
        CapacitacionClase,
        on_delete=models.CASCADE,
        related_name='asistencias',
        verbose_name=gettext_lazy('Clase'),
    )
    nombre = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email'))
    telefono = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Teléfono'))
    cargo = models.CharField(max_length=150, blank=True, verbose_name=gettext_lazy('Cargo'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de registro'))

    class Meta:
        ordering = ['nombre']
        verbose_name = gettext_lazy('Asistencia a Clase')
        verbose_name_plural = gettext_lazy('Asistencias a Clases')

    def __str__(self):
        return f"{self.nombre} – {self.clase}"


class CapacitacionSolicitudCambio(models.Model):
    """Solicitud de cambio enviada por un usuario público sobre una clase"""

    clase = models.ForeignKey(
        CapacitacionClase,
        on_delete=models.CASCADE,
        related_name='solicitudes',
        verbose_name=gettext_lazy('Clase'),
    )
    nombre = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email'))
    mensaje = models.TextField(verbose_name=gettext_lazy('Cambio solicitado'))
    atendida = models.BooleanField(default=False, verbose_name=gettext_lazy('Atendida'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de solicitud'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Solicitud de Cambio de Clase')
        verbose_name_plural = gettext_lazy('Solicitudes de Cambio de Clase')

    def __str__(self):
        return f"{self.nombre} – {self.clase}"


class CapacitacionClaseReaccion(models.Model):
    """Reacción (me gusta / no me gusta) de un usuario público a una clase"""

    TIPO_CHOICES = [
        ('like', gettext_lazy('Me gusta')),
        ('dislike', gettext_lazy('No me gusta')),
    ]

    clase = models.ForeignKey(
        CapacitacionClase,
        on_delete=models.CASCADE,
        related_name='reacciones',
        verbose_name=gettext_lazy('Clase'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name=gettext_lazy('Tipo'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Reacción a Clase')
        verbose_name_plural = gettext_lazy('Reacciones a Clases')

    def __str__(self):
        return f"{self.clase} – {self.get_tipo_display()}"


class CapacitacionClaseComentario(models.Model):
    """Comentario de un usuario público sobre una clase"""

    clase = models.ForeignKey(
        CapacitacionClase,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name=gettext_lazy('Clase'),
    )
    nombre = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(verbose_name=gettext_lazy('Email'))
    comentario = models.TextField(verbose_name=gettext_lazy('Comentario'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Comentario de Clase')
        verbose_name_plural = gettext_lazy('Comentarios de Clase')

    def __str__(self):
        return f"{self.nombre} – {self.clase}"


class CapacitacionRespuesta(models.Model):
    """Respuesta de un usuario a una línea/tarea de capacitación"""

    linea = models.ForeignKey(
        CapacitacionLinea,
        on_delete=models.CASCADE,
        related_name='respuestas',
        verbose_name=gettext_lazy('Línea'),
    )
    nombre = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    enlace = models.URLField(verbose_name=gettext_lazy('Enlace / URL'))
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='capacitacion_respuestas',
        verbose_name=gettext_lazy('Enviado por'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Fecha de envío'))

    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Respuesta de Capacitación')
        verbose_name_plural = gettext_lazy('Respuestas de Capacitación')

    def __str__(self):
        return f"{self.nombre} → {self.enlace}"


# ========================
# CARRITO DE COMPRAS PÚBLICO
# ========================

class CartQuotation(models.Model):
    """Cotización generada desde el carrito de compras público"""

    reference = models.CharField(
        max_length=20, unique=True, verbose_name=gettext_lazy('Referencia'),
        help_text=gettext_lazy('Número de cotización, ej: COT-2026-001')
    )
    customer_name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    customer_email = models.EmailField(verbose_name=gettext_lazy('Correo electrónico'))
    customer_phone = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Teléfono'))
    customer_company = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Empresa'))
    notes = models.TextField(blank=True, verbose_name=gettext_lazy('Notas adicionales'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=gettext_lazy('Total'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Cotización de Carrito')
        verbose_name_plural = gettext_lazy('Cotizaciones de Carrito')

    def __str__(self):
        return f'{self.reference} – {self.customer_name}'

    def save(self, *args, **kwargs):
        if not self.reference:
            from django.utils import timezone as tz
            year = tz.now().year
            last = CartQuotation.objects.filter(reference__startswith=f'COT-{year}-').count()
            self.reference = f'COT-{year}-{last + 1:04d}'
        super().save(*args, **kwargs)


class CartQuotationItem(models.Model):
    """Línea de producto dentro de una cotización de carrito"""

    quotation = models.ForeignKey(
        CartQuotation, on_delete=models.CASCADE, related_name='items', verbose_name=gettext_lazy('Cotización')
    )
    product = models.ForeignKey(
        'Product', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=gettext_lazy('Producto')
    )
    product_name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre del producto'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=gettext_lazy('Precio unitario'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=gettext_lazy('Cantidad'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=gettext_lazy('Subtotal'))

    class Meta:
        verbose_name = gettext_lazy('Línea de Cotización')
        verbose_name_plural = gettext_lazy('Líneas de Cotización')

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


# ============= LEVANTAMIENTO DE PROCESOS =============

class ProcessSurvey(models.Model):
    """Levantamiento de procesos de negocio"""

    name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre'),
    )
    folio = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Folio'),
        help_text=gettext_lazy('Generado automáticamente. Formato: LP-0001'),
    )
    date = models.DateField(
        verbose_name=gettext_lazy('Fecha'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción del proyecto'),
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_surveys',
        verbose_name=gettext_lazy('Empresa'),
    )
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token público'),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='process_surveys_created',
        verbose_name=gettext_lazy('Creado por'),
    )
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_surveys_responsible',
        verbose_name=gettext_lazy('Responsable'),
    )
    # Datos del solicitante (intake público)
    requester_name = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Nombre del solicitante'))
    requester_email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email del solicitante'))
    requester_phone = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Teléfono del solicitante'))
    requester_country = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('País del solicitante'))
    requester_company_name = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Empresa del solicitante'))

    STATUS_PROCESO = 'proceso'
    STATUS_ACEPTADO = 'aceptado'
    STATUS_RECHAZADO = 'rechazado'
    STATUS_CHOICES = [
        (STATUS_PROCESO, gettext_lazy('En proceso')),
        (STATUS_ACEPTADO, gettext_lazy('Aceptado')),
        (STATUS_RECHAZADO, gettext_lazy('Rechazado')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PROCESO,
        verbose_name=gettext_lazy('Estado'),
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Motivo de rechazo'),
    )
    importe = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Importe'),
    )
    importe_currency = models.CharField(
        max_length=10,
        default='USD',
        blank=True,
        verbose_name=gettext_lazy('Moneda'),
    )

    contract_title = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Título del contrato'),
    )
    contract_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha del contrato'),
    )
    contract_expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de vencimiento del contrato'),
    )
    client_signature_image = models.ImageField(
        upload_to='contract_client_signatures/',
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Firma del cliente'),
    )
    client_signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Fecha de firma del cliente'),
    )
    client_signed_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Nombre del firmante (cliente)'),
    )
    client_signed_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email del firmante (cliente)'),
    )

    # ── Identificación de partes (contrato) ──
    provider_nif = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('NIF/DNI/Pasaporte del proveedor'))
    provider_nationality = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Nacionalidad del proveedor'))
    provider_civil_status = models.CharField(max_length=80, blank=True, verbose_name=gettext_lazy('Estado civil del proveedor'))
    provider_occupation = models.CharField(max_length=100, blank=True, default='Autónomo', verbose_name=gettext_lazy('Ocupación del proveedor'))
    provider_address = models.CharField(max_length=300, blank=True, verbose_name=gettext_lazy('Domicilio del proveedor'))
    client_rep_name = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Nombre del representante cliente'))
    client_rep_id = models.CharField(max_length=80, blank=True, verbose_name=gettext_lazy('ID/NUE del representante cliente'))
    client_rep_role = models.CharField(max_length=150, blank=True, verbose_name=gettext_lazy('Cargo del representante cliente'))

    is_public_contract = models.BooleanField(
        default=True,
        verbose_name=gettext_lazy('Contrato público'),
        help_text=gettext_lazy('Si está desactivado, el enlace público no permite ver ni firmar el contrato.'),
    )

    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = gettext_lazy('Levantamiento de Procesos')
        verbose_name_plural = gettext_lazy('Levantamientos de Procesos')

    def __str__(self):
        return f'{self.name} ({self.date})'

    def save(self, *args, **kwargs):
        if not self.folio:
            last = ProcessSurvey.objects.filter(
                folio__startswith='LP-'
            ).order_by('-folio').first()
            if last and last.folio:
                try:
                    seq = int(last.folio.split('-')[1]) + 1
                except (IndexError, ValueError):
                    seq = 1
            else:
                seq = 1
            self.folio = f'LP-{seq:04d}'
        super().save(*args, **kwargs)

    def contract_is_expired(self):
        if not self.contract_expiration_date:
            return False
        return timezone.now().date() > self.contract_expiration_date

    def contract_days_remaining(self):
        if not self.contract_expiration_date:
            return None
        delta = self.contract_expiration_date - timezone.now().date()
        return delta.days


class ProcessSurveyLineCategory(models.Model):
    """Categoría reutilizable para las líneas de un levantamiento de procesos"""

    name = models.CharField(
        max_length=100,
        verbose_name=gettext_lazy('Nombre'),
    )
    color = models.CharField(
        max_length=20,
        default='#6c757d',
        verbose_name=gettext_lazy('Color'),
        help_text=gettext_lazy('Color en formato hexadecimal, ej: #0d6efd'),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_line_categories',
        verbose_name=gettext_lazy('Creado por'),
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))

    class Meta:
        ordering = ['name']
        verbose_name = gettext_lazy('Categoría de Línea')
        verbose_name_plural = gettext_lazy('Categorías de Línea')

    def __str__(self):
        return self.name


class ProcessSurveyLine(models.Model):
    """Línea de detalle de un levantamiento de procesos"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
    )
    title = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Título'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Descripción'),
    )

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, gettext_lazy('Pendiente')),
        (STATUS_ACCEPTED, gettext_lazy('Aceptado')),
        (STATUS_REJECTED, gettext_lazy('Rechazado')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=gettext_lazy('Estado'),
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('Oculto en vista pública'),
    )
    complexity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy('Complejidad'),
        help_text=gettext_lazy('Nivel de complejidad del proceso: 1 (muy simple) a 10 (muy complejo)'),
    )
    version = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=gettext_lazy('Versión'),
        help_text=gettext_lazy('Número de versión del levantamiento (máx. 10)'),
    )
    category = models.ForeignKey(
        'ProcessSurveyLineCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lines',
        verbose_name=gettext_lazy('Categoría'),
    )

    class Meta:
        ordering = ['version', 'order', 'pk']
        verbose_name = gettext_lazy('Línea de Levantamiento')
        verbose_name_plural = gettext_lazy('Líneas de Levantamiento')

    def __str__(self):
        return f'{self.survey} – {self.title}'


class ProcessSurveyLineComment(models.Model):
    """Comentario o adjunto público sobre una línea de levantamiento de procesos"""

    line = models.ForeignKey(
        ProcessSurveyLine,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gettext_lazy('Línea'),
    )
    author_name = models.CharField(
        max_length=200,
        verbose_name=gettext_lazy('Nombre'),
    )
    author_email = models.EmailField(
        blank=True,
        verbose_name=gettext_lazy('Email'),
    )
    body = models.TextField(
        blank=True,
        verbose_name=gettext_lazy('Comentario'),
    )
    attachment = models.FileField(
        upload_to='process_survey_attachments/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=gettext_lazy('Adjunto'),
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha'))

    class Meta:
        ordering = ['created_at']
        verbose_name = gettext_lazy('Comentario de Línea')
        verbose_name_plural = gettext_lazy('Comentarios de Línea')

    def __str__(self):
        return f'{self.author_name} – {self.line.title}'


class ProcessSurveyURL(models.Model):
    """URL de referencia asociada a un levantamiento de procesos"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='urls',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    label = models.CharField(
        max_length=300,
        verbose_name=gettext_lazy('Etiqueta'),
        help_text=gettext_lazy('Nombre descriptivo del enlace'),
    )
    url = models.URLField(
        max_length=2000,
        verbose_name=gettext_lazy('URL'),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
    )

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = gettext_lazy('URL de Levantamiento')
        verbose_name_plural = gettext_lazy('URLs de Levantamiento')

    def __str__(self):
        return f'{self.label} ({self.survey})'


class ProcessSurveyAIAnalysis(models.Model):
    """Registro histórico de análisis IA realizados sobre un levantamiento"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='ai_analyses',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    version = models.PositiveSmallIntegerField(verbose_name=gettext_lazy('Versión analizada'))
    total_lines = models.PositiveSmallIntegerField(default=0, verbose_name=gettext_lazy('Total de procesos'))
    analysis_text = models.TextField(verbose_name=gettext_lazy('Análisis'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Análisis IA de Levantamiento')
        verbose_name_plural = gettext_lazy('Análisis IA de Levantamientos')

    def __str__(self):
        return f'Análisis v{self.version} — {self.survey} ({self.created_at:%d/%m/%Y %H:%M})'


class ProcessSurveySignature(models.Model):
    """Firma digital de un acuerdo sobre el levantamiento de procesos"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='signatures',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    signer_name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    signer_email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email'))
    signer_phone = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Teléfono'))
    # Firma dibujada almacenada como data URL (PNG base64)
    signature_data = models.TextField(verbose_name=gettext_lazy('Firma (base64)'))
    signed_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Firmado el'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))

    class Meta:
        ordering = ['signed_at']
        verbose_name = gettext_lazy('Firma')
        verbose_name_plural = gettext_lazy('Firmas')

    def __str__(self):
        return f'{self.signer_name} – {self.survey.name}'


class ProcessSurveyPageView(models.Model):
    """Registro de apertura de la página pública de un levantamiento"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='page_views',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    status_at_view = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name=gettext_lazy('Estado al momento de la visita'),
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))
    country = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('País'))
    city = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Ciudad'))
    user_agent = models.CharField(max_length=500, blank=True, verbose_name=gettext_lazy('Navegador'))
    viewed_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha y hora'))

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = gettext_lazy('Apertura')
        verbose_name_plural = gettext_lazy('Aperturas')

    def __str__(self):
        return f'{self.survey.folio} – {self.ip_address} – {self.viewed_at:%d/%m/%Y %H:%M}'


class ProcessSurveyContractView(models.Model):
    """Registro de cada apertura del contrato público de un levantamiento"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='contract_views',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))
    country = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('País'))
    city = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Ciudad'))
    user_agent = models.CharField(max_length=500, blank=True, verbose_name=gettext_lazy('User-Agent'))
    device_type = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Dispositivo'))
    viewed_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha y hora'))

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = gettext_lazy('Apertura de contrato')
        verbose_name_plural = gettext_lazy('Aperturas de contrato')

    def __str__(self):
        return f'{self.survey.folio} – {self.ip_address} – {self.viewed_at:%d/%m/%Y %H:%M}'


class ProcessSurveyContractVisitor(models.Model):
    """Visitante que completó el formulario de acceso a un contrato privado"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='contract_visitors',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(verbose_name=gettext_lazy('Email'))
    phone = models.CharField(max_length=50, blank=True, verbose_name=gettext_lazy('Teléfono'))
    company_name = models.CharField(max_length=200, blank=True, verbose_name=gettext_lazy('Empresa'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=gettext_lazy('IP'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de acceso'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Visitante de contrato')
        verbose_name_plural = gettext_lazy('Visitantes de contrato')

    def __str__(self):
        return f'{self.name} – {self.survey.folio} – {self.created_at:%d/%m/%Y %H:%M}'


class ProcessSurveyClause(models.Model):
    """Cláusula de contrato de un levantamiento de procesos"""

    survey = models.ForeignKey(
        ProcessSurvey,
        on_delete=models.CASCADE,
        related_name='clauses',
        verbose_name=gettext_lazy('Levantamiento'),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=gettext_lazy('Orden'),
    )
    title = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=gettext_lazy('Título de la cláusula'),
        help_text=gettext_lazy('Ej: Objeto del contrato, Vigencia, Confidencialidad…'),
    )
    body = models.TextField(
        verbose_name=gettext_lazy('Texto de la cláusula'),
    )
    is_hidden_public = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy('No visible en público'),
        help_text=gettext_lazy('Si está activado, esta cláusula aparece borrosa en el contrato público.'),
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = gettext_lazy('Cláusula')
        verbose_name_plural = gettext_lazy('Cláusulas')

    def __str__(self):
        label = self.title or f'Cláusula {self.order}'
        return f'{label} — {self.survey.folio}'


class ProcessSurveyClauseHistory(models.Model):
    """Registro de cambios realizados por el usuario público en una cláusula de contrato"""

    clause = models.ForeignKey(
        ProcessSurveyClause,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=gettext_lazy('Cláusula'),
    )
    body_before = models.TextField(verbose_name=gettext_lazy('Texto anterior'))
    body_after = models.TextField(verbose_name=gettext_lazy('Texto nuevo'))
    edited_by_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=gettext_lazy('Editado por'),
    )
    edited_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de edición'))

    class Meta:
        ordering = ['-edited_at']
        verbose_name = gettext_lazy('Historial de cláusula')
        verbose_name_plural = gettext_lazy('Historial de cláusulas')

    def __str__(self):
        return f'Cambio en {self.clause} — {self.edited_at:%d/%m/%Y %H:%M}'


# ── Información de Proyecto ─────────────────────────────────────────────────

class ProjectInfo(models.Model):
    """Información general de un proyecto: nombre, empresa, folio y líneas de contenido."""

    name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre del proyecto'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción del proyecto'))
    pin = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=gettext_lazy('PIN de acceso'),
        help_text=gettext_lazy('Si se establece, la vista pública solicitará este PIN.'),
    )
    folio = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name=gettext_lazy('Folio'),
        help_text=gettext_lazy('Generado automáticamente. Formato: PI-0001'),
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_infos',
        verbose_name=gettext_lazy('Empresa'),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_infos_created',
        verbose_name=gettext_lazy('Creado por'),
    )
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token público'),
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Última actualización'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Información de Proyecto')
        verbose_name_plural = gettext_lazy('Información de Proyectos')

    def __str__(self):
        return f'{self.folio} – {self.name}'

    def save(self, *args, **kwargs):
        if not self.folio:
            last = ProjectInfo.objects.filter(folio__startswith='PI-').order_by('-folio').first()
            if last and last.folio:
                try:
                    seq = int(last.folio.split('-')[1]) + 1
                except (IndexError, ValueError):
                    seq = 1
            else:
                seq = 1
            self.folio = f'PI-{seq:04d}'
        super().save(*args, **kwargs)


class ProjectInfoLine(models.Model):
    """Línea de contenido de un proyecto (título, texto y categoría opcional)."""

    project = models.ForeignKey(
        ProjectInfo,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=gettext_lazy('Proyecto'),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Orden'))
    title = models.CharField(max_length=300, verbose_name=gettext_lazy('Título'))
    body = models.TextField(blank=True, verbose_name=gettext_lazy('Texto'))
    category = models.ForeignKey(
        'ProcessSurveyLineCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_info_lines',
        verbose_name=gettext_lazy('Categoría'),
    )
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token público de línea'),
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Creado'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Actualizado'))

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = gettext_lazy('Línea de Proyecto')
        verbose_name_plural = gettext_lazy('Líneas de Proyecto')

    def __str__(self):
        return f'{self.project.folio} – {self.title}'


class ProjectInfoResponsible(models.Model):
    """Usuario responsable asociado a un proyecto de información."""

    project = models.ForeignKey(
        ProjectInfo,
        on_delete=models.CASCADE,
        related_name='responsibles',
        verbose_name=gettext_lazy('Proyecto'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_info_responsibilities',
        verbose_name=gettext_lazy('Usuario'),
    )
    role_override = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=gettext_lazy('Cargo (sobreescribe perfil)'),
    )
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [('project', 'user')]
        ordering = ['added_at']
        verbose_name = gettext_lazy('Responsable de Proyecto')
        verbose_name_plural = gettext_lazy('Responsables de Proyecto')

    def __str__(self):
        return f'{self.project.folio} – {self.user.get_full_name() or self.user.username}'

    @property
    def display_role(self):
        if self.role_override:
            return self.role_override
        try:
            return self.user.profile.cargo or ''
        except Exception:
            return ''

    @property
    def display_phone(self):
        try:
            return self.user.profile.phone or ''
        except Exception:
            return ''


class ProjectInfoLink(models.Model):
    """Enlace (URL) asociado a un proyecto de información."""

    project = models.ForeignKey(
        ProjectInfo,
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name=gettext_lazy('Proyecto'),
    )
    name = models.CharField(max_length=200, verbose_name=gettext_lazy('Nombre'))
    url = models.URLField(max_length=500, verbose_name=gettext_lazy('URL'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción'))
    public_share_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=gettext_lazy('Token público de enlace'),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_info_links_created',
        verbose_name=gettext_lazy('Creado por'),
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Creado'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Enlace de Proyecto')
        verbose_name_plural = gettext_lazy('Enlaces de Proyecto')

    def __str__(self):
        return f'{self.project.folio} – {self.name}'


class ProjectInfoLinkVisit(models.Model):
    """Registro de apertura de la página pública de un enlace de proyecto."""

    link = models.ForeignKey(
        ProjectInfoLink,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name=gettext_lazy('Enlace'),
    )
    ip_address = models.GenericIPAddressField(verbose_name=gettext_lazy('IP'))
    user_agent = models.CharField(max_length=500, blank=True, verbose_name=gettext_lazy('User-Agent'))
    visited_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Apertura'))

    class Meta:
        ordering = ['-visited_at']
        verbose_name = gettext_lazy('Visita de Enlace')
        verbose_name_plural = gettext_lazy('Visitas de Enlace')

    def __str__(self):
        return f'{self.link.name} – {self.ip_address} – {self.visited_at:%d/%m/%Y %H:%M}'


class ProjectInfoVisit(models.Model):
    """Registro de apertura del enlace público de un proyecto."""

    project = models.ForeignKey(
        ProjectInfo,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name=gettext_lazy('Proyecto'),
    )
    ip_address = models.GenericIPAddressField(verbose_name=gettext_lazy('IP'))
    user_agent = models.CharField(max_length=500, blank=True, verbose_name=gettext_lazy('User-Agent'))
    visited_at = models.DateTimeField(default=timezone.now, verbose_name=gettext_lazy('Apertura'))

    class Meta:
        ordering = ['-visited_at']
        verbose_name = gettext_lazy('Visita Pública')
        verbose_name_plural = gettext_lazy('Visitas Públicas')

    def __str__(self):
        return f'{self.project.folio} – {self.ip_address} – {self.visited_at:%d/%m/%Y %H:%M}'


# ── Comentarios y adjuntos en líneas de proyecto ──────────────────────────────

class ProjectInfoLineComment(models.Model):
    """Comentario sobre una línea de proyecto (interno o público)."""

    line = models.ForeignKey(
        ProjectInfoLine, on_delete=models.CASCADE, related_name='comments',
    )
    author_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pi_line_comments',
    )
    author_name  = models.CharField(max_length=100, blank=True, verbose_name=gettext_lazy('Nombre público'))
    author_email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email público'))
    body = models.TextField(verbose_name=gettext_lazy('Comentario'))
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    @property
    def display_name(self):
        if self.author_user:
            return self.author_user.get_full_name() or self.author_user.username
        return self.author_name or 'Anónimo'

    def __str__(self):
        return f'{self.line} – {self.display_name}'


class ProjectInfoLineAttachment(models.Model):
    """Archivo adjunto a una línea de proyecto."""

    line = models.ForeignKey(
        ProjectInfoLine, on_delete=models.CASCADE, related_name='attachments',
    )
    uploaded_by_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pi_line_attachments',
    )
    uploaded_by_name = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='project_info_line_attachments/%Y/')
    original_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    @property
    def file_extension(self):
        return self.original_name.rsplit('.', 1)[-1].lower() if '.' in self.original_name else ''

    @property
    def is_image(self):
        return self.file_extension in ('jpg', 'jpeg', 'png', 'gif', 'webp')

    def __str__(self):
        return f'{self.line} – {self.original_name}'


# ==================== ERP3 - FIRMAS DIGITALES ====================

def _signature_upload_path(folder, ext):
    """Rutas con nombre aleatorio para que los archivos de firma no sean adivinables."""
    def _path(instance, filename):
        return f'signature_documents/{folder}/{timezone.now():%Y/%m}/{uuid.uuid4().hex}.{ext}'
    return _path


def signature_original_upload_to(instance, filename):
    return _signature_upload_path('original', 'pdf')(instance, filename)


def signature_signed_upload_to(instance, filename):
    return _signature_upload_path('signed', 'pdf')(instance, filename)


def signature_image_upload_to(instance, filename):
    return _signature_upload_path('signatures', 'png')(instance, filename)


class SignatureDocument(models.Model):
    """Documento PDF que se envía a una o varias personas para firmar."""

    STATUS_CHOICES = [
        ('draft', gettext_lazy('Borrador')),
        ('pending', gettext_lazy('Pendiente de firma')),
        ('completed', gettext_lazy('Completado')),
    ]

    title = models.CharField(max_length=200, verbose_name=gettext_lazy('Título'))
    description = models.TextField(blank=True, verbose_name=gettext_lazy('Descripción / mensaje para el firmante'))
    original_pdf = models.FileField(upload_to=signature_original_upload_to, verbose_name=gettext_lazy('PDF original'))
    signed_pdf = models.FileField(upload_to=signature_signed_upload_to, blank=True, null=True, verbose_name=gettext_lazy('PDF firmado'))
    page_count = models.PositiveIntegerField(default=0, verbose_name=gettext_lazy('Páginas'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name=gettext_lazy('Estado'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signature_documents', verbose_name=gettext_lazy('Creado por'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = gettext_lazy('Documento para firma')
        verbose_name_plural = gettext_lazy('Documentos para firma')

    def __str__(self):
        return self.title

    def refresh_status(self):
        """Recalcula el estado según los firmantes y campos colocados."""
        signers = list(self.signers.all())
        if signers and all(s.status == 'signed' for s in signers):
            new_status = 'completed'
        elif self.fields.exists():
            new_status = 'pending'
        else:
            new_status = 'draft'
        if new_status != self.status:
            self.status = new_status
            self.completed_at = timezone.now() if new_status == 'completed' else None
            self.save(update_fields=['status', 'completed_at', 'updated_at'])
        return self.status

    @property
    def signed_count(self):
        return self.signers.filter(status='signed').count()


class SignatureSigner(models.Model):
    """Persona que debe firmar un documento. Cada firmante tiene su propia URL de firma."""

    STATUS_CHOICES = [
        ('pending', gettext_lazy('Pendiente')),
        ('viewed', gettext_lazy('Visto')),
        ('signed', gettext_lazy('Firmado')),
    ]

    COLORS = ['#0d6efd', '#d63384', '#198754', '#fd7e14', '#6f42c1', '#20c997', '#dc3545', '#0dcaf0']

    document = models.ForeignKey(SignatureDocument, on_delete=models.CASCADE, related_name='signers')
    name = models.CharField(max_length=150, verbose_name=gettext_lazy('Nombre'))
    email = models.EmailField(blank=True, verbose_name=gettext_lazy('Email'))
    order = models.PositiveIntegerField(default=0)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    signature_image = models.FileField(upload_to=signature_image_upload_to, blank=True, null=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_ip = models.GenericIPAddressField(null=True, blank=True)
    signed_user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = gettext_lazy('Firmante')
        verbose_name_plural = gettext_lazy('Firmantes')

    def __str__(self):
        return f'{self.name} – {self.document}'

    @property
    def color(self):
        return self.COLORS[(self.order or 0) % len(self.COLORS)]

    def get_sign_url(self):
        from django.urls import reverse
        return reverse('signature_sign_public', kwargs={'token': self.token})


class SignatureField(models.Model):
    """
    Recuadro de firma colocado en una página del PDF.
    Las coordenadas son fracciones (0-1) de la página tal y como se muestra
    (origen arriba a la izquierda, rotación de la página aplicada).
    """

    document = models.ForeignKey(SignatureDocument, on_delete=models.CASCADE, related_name='fields')
    signer = models.ForeignKey(SignatureSigner, on_delete=models.CASCADE, related_name='fields')
    page = models.PositiveIntegerField(verbose_name=gettext_lazy('Página'))  # 1-based
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page', 'y', 'x']
        verbose_name = gettext_lazy('Campo de firma')
        verbose_name_plural = gettext_lazy('Campos de firma')

    def __str__(self):
        return f'{self.signer.name} – p.{self.page}'
