from django import template
from tickets.utils import is_agent
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='is_agent')
def is_agent_filter(user):
    """
    Filtro de template para verificar si un usuario es agente.
    Uso: {% if user|is_agent %}
    """
    return is_agent(user)

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Filtro de template para obtener un valor de un diccionario.
    Uso: {{ record.data|get_item:field.name }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter(name='highlight_hashtags')
def highlight_hashtags(text):
    """
    Filtro de template para resaltar hashtags y menciones.
    Uso: {{ post.content|highlight_hashtags }}
    """
    if not text:
        return text
    
    # Reemplazar hashtags con versión en negrita
    pattern_hashtag = r'(#\w+)'
    highlighted = re.sub(pattern_hashtag, r'<strong>\1</strong>', text)
    
    # Reemplazar menciones @ con versión en negrita verde oscuro
    pattern_mention = r'(@\w+)'
    highlighted = re.sub(pattern_mention, r'<strong style="color: #198754;">\1</strong>', highlighted)
    
    return mark_safe(highlighted)


@register.filter(name='multiply')
def multiply(value, arg):
    """
    Filtro de template para multiplicar dos valores.
    Uso: {{ value|multiply:100 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='divide')
def divide(value, arg):
    """
    Filtro de template para dividir dos valores.
    Uso: {{ value|divide:total }}
    """
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0
