#!/usr/bin/env python3
"""
Script de prueba para demostrar la funcionalidad de acceso público al control de horario
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import PublicTimeAccess
from django.urls import reverse

def main():
    print("=== Sistema de Acceso Público al Control de Horario ===")
    print()
    
    # Mostrar usuarios existentes
    users = User.objects.filter(is_active=True)
    print(f"Usuarios disponibles en el sistema ({users.count()}):")
    for i, user in enumerate(users, 1):
        public_access = getattr(user, 'public_time_access', None)
        if public_access and public_access.is_active:
            status = f"✅ Acceso público activo - Token: {public_access.token[:16]}..."
            url = f"http://localhost:8000{public_access.public_url}"
        else:
            status = "❌ Acceso público desactivado"
        
        print(f"  {i}. {user.get_full_name() or user.username} ({user.email})")
        print(f"     {status}")
        if public_access and public_access.is_active:
            print(f"     🔗 URL: {url}")
        print()
    
    print("\n=== Cómo usar el sistema ===")
    print("1. Ve a http://localhost:8000/users/ para gestionar usuarios")
    print("2. Edita un usuario y activa 'Habilitar acceso público al control de horario'")
    print("3. Configura las opciones de seguridad según tus necesidades:")
    print("   - Requerir ubicación: Registra GPS al marcar entrada/salida")
    print("   - IPs permitidas: Restringe acceso a IPs específicas")
    print("4. Copia la URL pública generada y úsala desde cualquier dispositivo")
    print("5. La URL permite registrar entrada/salida sin iniciar sesión")
    print()
    
    print("=== Características del sistema ===")
    print("✅ Interfaz móvil responsiva")
    print("✅ Registro de entrada/salida con un click")
    print("✅ Geolocalización opcional")
    print("✅ Control de IPs permitidas")
    print("✅ Tokens únicos y seguros")
    print("✅ Integración con sistema de control de horario existente")
    print("✅ Historial de uso y auditoría")
    print()

if __name__ == "__main__":
    main()