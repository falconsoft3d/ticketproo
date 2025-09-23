#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User

print("=== USUARIOS EN EL SISTEMA ===")
users = User.objects.filter(is_active=True)
print(f"Total de usuarios activos: {users.count()}")

for user in users:
    print(f"- {user.username} ({user.first_name} {user.last_name}) - Email: {user.email}")

print("\n=== FORMULARIO DE TAREAS ===")
from tickets.forms import TaskForm
form = TaskForm()
print(f"Usuarios disponibles para asignar: {form.fields['assigned_users'].queryset.count()}")
for user in form.fields['assigned_users'].queryset:
    print(f"- {user.username}")