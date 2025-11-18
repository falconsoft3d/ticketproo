#!/usr/bin/env python
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import ShortUrl, ShortUrlClick
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate

# Obtener la URL con ID 2
short_url = ShortUrl.objects.get(pk=2)
clicks = short_url.click_records.all()

print(f"URL: {short_url.short_code}")
print(f"Total clicks (contador): {short_url.clicks}")
print(f"Clicks detallados: {clicks.count()}")
print(f"Clicks históricos: {short_url.clicks - clicks.count()}")
print()

# Ver los últimos 30 días
thirty_days_ago = timezone.now() - timedelta(days=30)
print(f"Fecha actual: {timezone.now()}")
print(f"30 días atrás: {thirty_days_ago}")
print(f"Fecha de creación URL: {short_url.created_at}")
print()

# Ver clicks en el rango de 30 días
clicks_in_range = clicks.filter(clicked_at__gte=thirty_days_ago)
print(f"Clicks en rango de 30 días: {clicks_in_range.count()}")
print()

# Ver la agregación por día
clicks_by_day_data = clicks.filter(clicked_at__gte=thirty_days_ago).annotate(
    date=TruncDate('clicked_at')
).values('date').annotate(
    count=Count('id')
).order_by('date')

print("Datos agregados por día:")
for item in clicks_by_day_data:
    print(f"  {item['date']}: {item['count']} clicks")
print()

# Ver el diccionario que se crea
clicks_by_day_dict = {item['date'].strftime('%d/%m'): item['count'] for item in clicks_by_day_data}
print("Diccionario clicks_by_day_dict:")
for key, value in clicks_by_day_dict.items():
    print(f"  {key}: {value}")
print()

# Ver las etiquetas que se generan
clicks_by_day_labels = []
clicks_by_day_values = []
for i in range(30):
    day = timezone.now().date() - timedelta(days=29-i)
    label = day.strftime('%d/%m')
    clicks_by_day_labels.append(label)
    clicks_by_day_values.append(clicks_by_day_dict.get(label, 0))

print("Primeros 10 días generados:")
for i in range(min(10, len(clicks_by_day_labels))):
    print(f"  {clicks_by_day_labels[i]}: {clicks_by_day_values[i]} clicks")
print()

# Ver los clicks históricos
clicks_detallados = clicks.count()
clicks_historicos = short_url.clicks - clicks_detallados
print(f"Clicks históricos a agregar: {clicks_historicos}")

if clicks_historicos > 0:
    if short_url.created_at >= thirty_days_ago:
        target_date = short_url.created_at.date()
    else:
        target_date = thirty_days_ago.date()
    
    target_label = target_date.strftime('%d/%m')
    print(f"Fecha objetivo para clicks históricos: {target_date} -> Etiqueta: {target_label}")
    print(f"¿Está en el diccionario? {target_label in clicks_by_day_dict}")
    
print()
print("Total de clicks que deberían mostrarse en el gráfico:", sum(clicks_by_day_values))
