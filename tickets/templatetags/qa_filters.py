from django import template
import os

register = template.Library()

@register.filter
def filename(value):
    """
    Extrae el nombre del archivo de una ruta completa
    """
    if value:
        return os.path.basename(str(value))
    return value

@register.filter
def mul(value, arg):
    """
    Multiplica value por arg
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """
    Divide value por arg
    """
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0