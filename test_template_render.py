#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import MultipleDocumentation
from tickets.forms import MultipleDocumentationForm
from django.template.loader import render_to_string

# Obtener la documentación
doc = MultipleDocumentation.objects.get(id=2)
form = MultipleDocumentationForm(instance=doc)

# Renderizar solo la parte del campo
context = {
    'form': form,
    'documentation': doc,
    'is_create': False,
    'page_title': 'Test',
    'request': type('Request', (), {'get_host': lambda: 'localhost:8001'})()
}

try:
    # Intentar renderizar el template completo
    html = render_to_string('tickets/multiple_documentation_form.html', context)
    
    # Buscar el campo de contraseña
    if 'value="mi_contraseña_123"' in html:
        print("✅ EL TEMPLATE SE RENDERIZA CORRECTAMENTE CON LA CONTRASEÑA")
    else:
        print("❌ EL TEMPLATE NO CONTIENE LA CONTRASEÑA")
        
    # Mostrar solo la parte relevante del HTML
    import re
    pattern = r'<div[^>]*id="password_field"[^>]*>.*?</div>\s*</div>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        print("\nCampo de contraseña encontrado en HTML:")
        print(match.group(0)[:500] + "..." if len(match.group(0)) > 500 else match.group(0))
    else:
        print("\n❌ No se encontró el div del campo de contraseña")
        
except Exception as e:
    print(f"Error al renderizar template: {e}")
    import traceback
    traceback.print_exc()