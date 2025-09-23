#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import Task

# Obtener el primer usuario (o crear uno si no existe)
try:
    user = User.objects.first()
    if not user:
        print("No hay usuarios en la base de datos. Crear un usuario primero.")
        exit()
    
    print(f"Creando tarea de prueba para el usuario: {user.username}")
    
    # Crear una tarea de prueba
    task = Task.objects.create(
        title="Tarea de prueba para asistencia",
        description="Esta es una tarea de prueba para verificar el sistema de asistencia",
        status="pending",
        priority="medium",
        created_by=user
    )
    
    # Asignar la tarea al usuario
    task.assigned_users.add(user)
    task.save()
    
    print(f"Tarea creada exitosamente: {task.title}")
    print(f"ID: {task.id}")
    print(f"Estado: {task.status}")
    print(f"Prioridad: {task.priority}")
    print(f"Asignada a: {[u.username for u in task.assigned_users.all()]}")
    
except Exception as e:
    print(f"Error: {e}")