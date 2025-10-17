from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Agrega una clase CSS a un campo de formulario"""
    return field.as_widget(attrs={**field.field.widget.attrs, 'class': css_class})

@register.filter
def field_type(bound_field):
    return bound_field.field.widget.__class__.__name__

@register.filter
def get_item(dictionary, key):
    """Obtiene el BoundField de un formulario usando una clave"""
    try:
        return dictionary[key]
    except Exception:
        return None