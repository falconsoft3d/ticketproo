from django import template
from decimal import Decimal
import re

register = template.Library()

@register.filter
def can_manage_courses(user):
    """Verifica si el usuario puede gestionar cursos (agentes y profesores)"""
    from tickets import utils
    return utils.can_manage_courses(user)

@register.filter
def sum_cost(projects):
    """Suma el coste total de todos los proyectos"""
    total = Decimal('0.00')
    for project in projects:
        total += project.get_total_cost()
    return total

@register.filter
def sum_revenue(projects):
    """Suma la venta total de todos los proyectos"""
    total = Decimal('0.00')
    for project in projects:
        total += project.get_total_revenue()
    return total

@register.filter
def sum_profit(projects):
    """Suma el beneficio total de todos los proyectos"""
    total = Decimal('0.00')
    for project in projects:
        total += project.get_profit()
    return total

@register.filter
def clean_phone_for_whatsapp(phone):
    """Limpia el número de teléfono para WhatsApp eliminando espacios, guiones y paréntesis"""
    if not phone:
        return ""
    # Eliminar todos los caracteres que no sean números o el símbolo +
    cleaned = re.sub(r'[^\d+]', '', str(phone))
    return cleaned