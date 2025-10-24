#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from tickets.models import MultipleDocumentation
from tickets.forms import MultipleDocumentationForm
from django.template import Template, Context

# Obtener la documentación
doc = MultipleDocumentation.objects.get(id=2)
form = MultipleDocumentationForm(instance=doc)

# Simular el contexto del template
context = Context({
    'form': form,
    'documentation': doc,
    'is_create': False
})

# Probar las condiciones del template
print("=== VALORES DE LAS CONDICIONES ===")
print(f"form['password_protected'].value(): {form['password_protected'].value()}")
print(f"form['access_password'].value(): {form['access_password'].value()}")
print(f"documentation.password_protected: {doc.password_protected}")
print(f"documentation.access_password: '{doc.access_password}'")

# Probar la condición original
condition1 = not form['password_protected'].value() and not form['access_password'].value()
print(f"\nCondición original (ocultar si ambos son falsy): {condition1}")

# Probar la condición nueva
condition2 = not form['password_protected'].value() and not doc.password_protected
print(f"Condición nueva (ocultar si checkbox no marcado y doc no protegida): {condition2}")

# El campo debería estar visible si:
# - El checkbox está marcado, o
# - La documentación ya está protegida
should_be_visible = form['password_protected'].value() or doc.password_protected
print(f"\n¿Debería estar visible? {should_be_visible}")

# Probar renderizado del campo
print(f"\n=== RENDERIZADO DEL CAMPO ===")
print(f"HTML: {form['access_password']}")

# Verificar initial vs value
print(f"\n=== DEBUG FORM FIELDS ===")
print(f"Initial: {form.fields['access_password'].initial}")
print(f"Data: {form.data}")
print(f"Bound: {form.is_bound}")

# Obtener valor a través de diferentes métodos
try:
    bound_value = form['access_password'].value()
    print(f"Bound value: {bound_value}")
except:
    print("Bound value: N/A")