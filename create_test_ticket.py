#!/usr/bin/env python
import os
import django
import uuid

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import Ticket, Category
from django.contrib.auth.models import User

# Crear un usuario si no existe
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
)

# Crear una categoría si no existe
category, created = Category.objects.get_or_create(
    name='General',
    defaults={'description': 'Categoría general para pruebas'}
)

# Crear un ticket de prueba con estado resuelto
ticket = Ticket.objects.create(
    title='Ticket de Prueba para Encuesta de Satisfacción',
    description='Este es un ticket de prueba para verificar la funcionalidad de encuestas de satisfacción.',
    status='resolved',
    priority='medium',
    category=category,
    created_by=user,
    assigned_to=user,
    is_public_shareable=True,
    public_share_token=uuid.uuid4(),
    is_approved=False
)

print(f'Ticket creado exitosamente!')
print(f'ID: {ticket.id}')
print(f'Número: {ticket.ticket_number}')
print(f'Token público: {ticket.public_share_token}')
print(f'URL pública: http://localhost:8001/public/{ticket.public_share_token}/')
print(f'URL encuesta: http://localhost:8001/public/{ticket.public_share_token}/survey/')