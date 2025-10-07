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

@register.filter
def format_currency(amount, currency_code=None):
    """Formatea un monto según la configuración de moneda del sistema"""
    if amount is None:
        amount = 0
    
    from tickets.models import SystemConfiguration
    
    if currency_code is None:
        config = SystemConfiguration.get_config()
        currency_code = config.default_currency
    
    currency_symbols = {
        'EUR': '€',
        'USD': '$',
        'GBP': '£',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'CHF': 'CHF',
        'CNY': '¥',
        'MXN': '$',
        'COP': '$',
    }
    
    symbol = currency_symbols.get(currency_code, '€')
    
    # Formatear según la moneda
    if currency_code in ['EUR', 'GBP']:
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{amount:,.0f} {symbol}"

@register.simple_tag
def get_currency_symbol():
    """Obtiene el símbolo de la moneda configurada en el sistema"""
    from tickets.models import SystemConfiguration
    config = SystemConfiguration.get_config()
    return config.get_currency_symbol()

@register.simple_tag
def get_currency_icon():
    """Obtiene el icono de Bootstrap apropiado para la moneda configurada"""
    from tickets.models import SystemConfiguration
    config = SystemConfiguration.get_config()
    
    currency_icons = {
        'EUR': 'bi-currency-euro',
        'USD': 'bi-currency-dollar',
        'GBP': 'bi-currency-pound',
        'JPY': 'bi-currency-yen',
        'CAD': 'bi-currency-dollar',
        'AUD': 'bi-currency-dollar',
        'CHF': 'bi-cash',
        'CNY': 'bi-currency-yen',
        'MXN': 'bi-currency-dollar',
        'COP': 'bi-currency-dollar',
    }
    
    return currency_icons.get(config.default_currency, 'bi-currency-euro')