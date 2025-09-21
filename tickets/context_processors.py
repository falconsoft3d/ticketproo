"""
Context processors para TicketProo
"""
from tickets.models import TimeEntry
from tickets.utils import is_agent


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