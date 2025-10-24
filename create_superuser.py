#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User

# Crear superusuario
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@test.com',
        'is_staff': True,
        'is_superuser': True
    }
)

if created:
    user.set_password('admin123')
    user.save()
    print(f"Superusuario creado: admin / admin123")
else:
    print(f"Superusuario ya existe: admin")