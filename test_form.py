#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import MultipleDocumentation
from tickets.forms import MultipleDocumentationForm

# Obtener la documentación de prueba
try:
    doc = MultipleDocumentation.objects.get(id=2)
    print(f"Documentación encontrada:")
    print(f"  ID: {doc.id}")
    print(f"  Título: {doc.title}")
    print(f"  Protegida: {doc.password_protected}")
    print(f"  Contraseña: '{doc.access_password}'")
    print(f"  Longitud contraseña: {len(doc.access_password) if doc.access_password else 0}")
    print()
    
    # Crear formulario como en la vista
    print("Creando formulario (simulando vista de edición)...")
    form = MultipleDocumentationForm(instance=doc)
    
    print("\nEstado del formulario:")
    print(f"  Campo access_password.initial: '{form.fields['access_password'].initial}'")
    print(f"  Campo access_password.widget.attrs: {form.fields['access_password'].widget.attrs}")
    
    # Renderizar el campo para ver qué valor tiene
    field_html = str(form['access_password'])
    print(f"\nHTML del campo: {field_html}")
    
    # Verificar si el valor está en el HTML
    if doc.access_password in field_html:
        print("✅ LA CONTRASEÑA ESTÁ EN EL HTML DEL CAMPO")
    else:
        print("❌ LA CONTRASEÑA NO ESTÁ EN EL HTML DEL CAMPO")
        
except MultipleDocumentation.DoesNotExist:
    print("Error: No se encontró la documentación con ID 2")
    print("Ejecuta primero: python test_documentation.py")