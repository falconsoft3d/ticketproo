import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import ShortUrl, ShortUrlClick
from django.utils import timezone
from datetime import timedelta

short_url = ShortUrl.objects.get(pk=2)
print(f"URL: {short_url.short_code}")
print(f"Total clicks: {short_url.clicks}")
print(f"Fecha de creación: {short_url.created_at}")
print(f"Clicks detallados: {short_url.click_records.count()}")

print("\n--- Clicks registrados ---")
for click in short_url.click_records.all():
    print(f"  {click.clicked_at} - {click.country or 'Sin país'}")

print("\n--- Últimos 30 días ---")
thirty_days_ago = timezone.now() - timedelta(days=30)
print(f"Desde: {thirty_days_ago}")
print(f"Hasta: {timezone.now()}")
print(f"Fecha creación dentro del rango: {short_url.created_at >= thirty_days_ago}")

print("\n--- Datos para el gráfico ---")
clicks_detallados = short_url.click_records.count()
clicks_historicos = short_url.clicks - clicks_detallados
print(f"Clicks históricos: {clicks_historicos}")
print(f"Fecha creación formato: {short_url.created_at.strftime('%d/%m')}")
