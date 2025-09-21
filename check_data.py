#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import UserProfile, Project, TimeEntry

def main():
    print('=== USUARIOS Y SUS PRECIOS ===')
    for user in User.objects.all():
        try:
            profile = user.profile  # Cambiar de userprofile a profile
            print(f'Usuario: {user.username}')
            print(f'  - Precio por hora: €{profile.precio_hora}')
            print(f'  - Coste por hora: €{profile.coste_hora}')
            print()
        except UserProfile.DoesNotExist:
            print(f'Usuario: {user.username} - SIN PERFIL')
            print()

    print('=== PROYECTOS Y SUS REGISTROS DE TIEMPO ===')
    for project in Project.objects.all():
        print(f'Proyecto: {project.name}')
        time_entries = project.time_entries.all()
        print(f'  - Total registros de tiempo: {time_entries.count()}')
        
        total_hours = 0
        for entry in time_entries:
            hours = entry.horas_trabajadas
            total_hours += hours
            user_name = entry.user.username if entry.user else 'Sin usuario'
            print(f'    * {user_name}: {hours} horas')
        
        print(f'  - Total horas: {total_hours}')
        print(f'  - Coste total calculado: €{project.get_total_cost()}')
        print(f'  - Venta total calculada: €{project.get_total_revenue()}')
        print()

if __name__ == '__main__':
    main()