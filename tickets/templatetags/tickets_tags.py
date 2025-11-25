from django import template
from tickets.utils import is_agent

register = template.Library()

@register.filter(name='is_agent')
def is_agent_filter(user):
    """
    Filtro de template para verificar si un usuario es agente.
    Uso: {% if user|is_agent %}
    """
    return is_agent(user)
