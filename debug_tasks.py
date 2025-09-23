#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import Task
from django.db.models import Q

# Verificar tareas en la base de datos
print("=== VERIFICACIÓN DE TAREAS ===")
print(f"Total tareas en DB: {Task.objects.count()}")

# Mostrar todas las tareas
tasks = Task.objects.all()
for task in tasks:
    print(f"Tarea: {task.title} | Estado: {task.status} | Creada por: {task.created_by.username}")
    assigned_users = task.assigned_users.all()
    if assigned_users:
        print(f"  Asignada a: {[u.username for u in assigned_users]}")
    else:
        print(f"  No asignada a nadie")
    print("---")

# Verificar usuarios
print("\n=== USUARIOS ===")
users = User.objects.all()
for user in users:
    print(f"Usuario: {user.username}")
    
    # Tareas asignadas o creadas por este usuario
    user_tasks = Task.objects.filter(
        Q(assigned_users=user) | Q(created_by=user)
    ).distinct()
    print(f"  Total tareas: {user_tasks.count()}")
    
    # Tareas pendientes/en progreso
    available_tasks = Task.objects.filter(
        Q(assigned_users=user) | Q(created_by=user),
        status__in=['pending', 'in_progress']
    ).distinct()
    print(f"  Tareas disponibles para asistencia: {available_tasks.count()}")
    
    for task in available_tasks:
        print(f"    - {task.title} ({task.status})")
    print("---")

print("\n=== ESTADOS DE TAREAS ===")
for status in ['pending', 'in_progress', 'completed', 'cancelled']:
    count = Task.objects.filter(status=status).count()
    print(f"{status}: {count}")