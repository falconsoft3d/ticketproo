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

@register.simple_tag(takes_context=True)
def absolute_url(context, relative_url):
    """Convierte una URL relativa en URL absoluta usando el request del contexto"""
    request = context.get('request')
    if request:
        return request.build_absolute_uri(relative_url)
    return relative_url

@register.filter
def sub(value, arg):
    """Resta arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplica value por arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide value entre arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def split(value, delimiter=','):
    """Divide un string usando un delimitador"""
    if not value:
        return []
    return str(value).split(delimiter)

@register.filter
def trim(value):
    """Elimina espacios en blanco al inicio y final"""
    if not value:
        return ''
    return str(value).strip()

@register.filter
def pluralize_es(value, singular_plural=''):
    """Pluralización en español"""
    try:
        count = int(value)
        if not singular_plural:
            return 's' if count != 1 else ''
        
        if ',' in singular_plural:
            singular, plural = singular_plural.split(',', 1)
            return plural if count != 1 else singular
        else:
            return singular_plural if count != 1 else ''
    except (ValueError, TypeError):
        return ''