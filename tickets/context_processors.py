"""
Context processors para TicketProo
"""
from django.db import models
from tickets.models import TimeEntry, BlogCategory, SystemConfiguration
from tickets.utils import is_agent


def system_config(request):
    """
    Context processor que proporciona la configuración del sistema
    en todas las plantillas.
    """
    try:
        config = SystemConfiguration.objects.get(pk=1)
    except SystemConfiguration.DoesNotExist:
        # Crear configuración por defecto si no existe
        config = SystemConfiguration.objects.create()
    
    return {
        'system_config': config,
    }


def time_status(request):
    """
    Context processor que proporciona el estado del tiempo de trabajo
    en todas las plantillas de la aplicación.
    """
    context = {
        'active_time_entry': None,
        'can_start_work': False,
        'can_end_work': False,
        'is_working': False,
    }
    
    if request.user.is_authenticated and is_agent(request.user):
        active_time_entry = TimeEntry.get_active_entry(request.user)
        
        context.update({
            'active_time_entry': active_time_entry,
            'can_start_work': not active_time_entry,
            'can_end_work': bool(active_time_entry),
            'is_working': bool(active_time_entry),
        })
    
    return context


def blog_categories(request):
    """
    Context processor que proporciona las categorías del blog
    en todas las plantillas públicas.
    """
    try:
        categories = BlogCategory.objects.annotate(
            posts_count=models.Count('posts', filter=models.Q(posts__status='published'))
        ).filter(posts_count__gt=0).order_by('name')
    except:
        categories = []
    
    return {
        'blog_categories': categories,
    }


def crm_counters(request):
    """
    Context processor que proporciona contadores para los menús del CRM
    """
    if not request.user.is_authenticated:
        return {}

    # Contador de RFIs abiertos para no-agentes (sus propias + empresa + asignadas)
    if not is_agent(request.user):
        try:
            from tickets.models import RFI
            from django.db.models import Q
            from django.utils import timezone
            user = request.user
            user_company = getattr(user, 'profile', None)
            user_company = user_company.company if user_company else None
            open_rfi_q = Q(created_by=user) | Q(assigned_user=user)
            if user_company:
                open_rfi_q |= Q(company=user_company)
            open_rfis = RFI.objects.filter(open_rfi_q, closed_at__isnull=True).distinct()
            rfi_open_count = open_rfis.count()
            oldest_rfi = open_rfis.order_by('created_at').first()
            rfi_oldest_days = (timezone.now() - oldest_rfi.created_at).days if oldest_rfi else 0

            from tickets.models import Ticket
            ticket_active_q = Q(created_by=user) | Q(assigned_to=user)
            if user_company:
                ticket_active_q |= Q(company=user_company)
            ticket_active_count = Ticket.objects.filter(
                ticket_active_q, status__in=['open', 'working']
            ).distinct().count()

            return {
                'rfi_open_count': rfi_open_count,
                'rfi_oldest_days': rfi_oldest_days,
                'ticket_active_count': ticket_active_count,
            }
        except Exception:
            return {}

    try:
        from tickets.models import Contact, Company, Opportunity, Meeting, Quotation, QuotationTemplate, OpportunityActivity, CrmQuestion
        
        # Contadores básicos
        contacts_count = Contact.objects.count()
        companies_count = Company.objects.filter(is_active=True).count()
        
        # Oportunidades activas (no ganadas ni perdidas)
        opportunities_count = Opportunity.objects.exclude(
            status__name__in=['Ganada', 'Perdida', 'Cancelada']
        ).count()
        
        # Reuniones futuras o de hoy
        from django.utils import timezone
        today = timezone.now().date()
        meetings_count = Meeting.objects.filter(date__gte=today).count()
        
        # Preguntas pendientes de respuesta
        questions_count = CrmQuestion.objects.filter(answer__isnull=True).count()
        
        # Cotizaciones activas (draft, sent, approved)
        quotations_count = Quotation.objects.filter(
            status__in=['draft', 'sent', 'approved']
        ).count()
        
        # Plantillas públicas activas
        templates_count = QuotationTemplate.objects.filter(is_active=True).count()
        
        # Actividades pendientes del usuario
        pending_activities_count = OpportunityActivity.objects.filter(
            assigned_to=request.user,
            status__in=['pending', 'in_progress']
        ).count()

        # RFIs registradas
        from tickets.models import RFI
        rfi_count = RFI.objects.count()
        
        return {
            'crm_counters': {
                'contacts': contacts_count,
                'companies': companies_count,
                'opportunities': opportunities_count,
                'meetings': meetings_count,
                'questions': questions_count,
                'quotations': quotations_count,
                'templates': templates_count,
                'pending_activities': pending_activities_count,
                'rfi': rfi_count,
            }
        }
    except Exception:
        return {}


def active_chatbot(request):
    """
    Context processor que proporciona el chatbot interno activo
    para mostrarlo en el home público
    """
    try:
        from tickets.models import Chatbot
        
        # Buscar chatbot interno activo
        chatbot = Chatbot.objects.filter(
            type='internal',
            is_active=True
        ).first()
        
        return {
            'active_internal_chatbot': chatbot
        }
    except Exception:
        return {
            'active_internal_chatbot': None
        }