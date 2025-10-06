from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def can_edit_opportunity(opportunity, user):
    """Filtro para verificar si un usuario puede editar una oportunidad"""
    if not user or not user.is_authenticated:
        return False
    return opportunity.can_be_edited_by(user)

@register.filter
def is_agent(user):
    """Filtro para verificar si un usuario es agente"""
    if not user or not user.is_authenticated:
        return False
    from tickets.utils import is_agent
    return is_agent(user)

@register.simple_tag
def can_edit_opportunity_tag(opportunity, user):
    """Tag para verificar si un usuario puede editar una oportunidad"""
    if not user or not user.is_authenticated:
        return False
    return opportunity.can_be_edited_by(user)