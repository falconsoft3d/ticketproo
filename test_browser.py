#!/usr/bin/env python
import os
import django
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Crear cliente de prueba
client = Client()

# Obtener usuario admin
try:
    user = User.objects.get(username='admin')
    
    # Hacer login
    client.force_login(user)
    
    # Acceder a la página de edición
    response = client.get('/documentaciones/2/editar/')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Buscar el campo de contraseña en el HTML
        if 'value="mi_contraseña_123"' in content:
            print("✅ LA CONTRASEÑA SE MUESTRA CORRECTAMENTE EN EL NAVEGADOR")
        else:
            print("❌ LA CONTRASEÑA NO SE MUESTRA EN EL NAVEGADOR")
            
        # Mostrar el campo de contraseña específico
        import re
        password_match = re.search(r'<input[^>]*name="access_password"[^>]*>', content)
        if password_match:
            print(f"\nCampo de contraseña encontrado:")
            print(password_match.group(0))
        else:
            print("\n❌ No se encontró el campo de contraseña")
            
    else:
        print(f"Error: {response.status_code}")
        print(response.content.decode('utf-8')[:500])
        
except User.DoesNotExist:
    print("Error: Usuario admin no existe")
    print("Ejecuta: python create_superuser.py")