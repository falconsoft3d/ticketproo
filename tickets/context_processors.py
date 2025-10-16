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