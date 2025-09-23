#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import Task

print("=== VERIFICACIÓN DE TAREAS Y USUARIOS ASIGNADOS ===")
tasks = Task.objects.all().prefetch_related('assigned_users')

for task in tasks:
    print(f"\nTarea ID: {task.id}")
    print(f"Título: {task.title}")
    print(f"Usuarios asignados: {task.assigned_users.count()}")
    for user in task.assigned_users.all():
        print(f"  - {user.username} ({user.get_full_name()})")
    print(f"Creado por: {task.created_by}")
    print("-" * 50)