#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import MultipleDocumentation
from django.contrib.auth.models import User

# Obtener o crear un usuario
user, created = User.objects.get_or_create(
    username='test_user',
    defaults={'email': 'test@example.com', 'is_staff': True}
)

# Crear una documentación de prueba con contraseña
doc = MultipleDocumentation.objects.create(
    title="Documentación de Prueba",
    description="Esta es una prueba para verificar la contraseña",
    password_protected=True,
    access_password="mi_contraseña_123",
    is_active=True,
    created_by=user
)

print(f"Documentación creada con ID: {doc.id}")
print(f"Contraseña guardada: {doc.access_password}")
print(f"URL para editar: http://127.0.0.1:8001/documentaciones/{doc.id}/editar/")