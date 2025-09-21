from django import template
from decimal import Decimal

register = template.Library()

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