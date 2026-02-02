#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para la validación anti-spam de teléfonos en landing pages
ESTRATEGIA: Mostrar siempre mensaje de éxito, pero no crear contacto si es spam
"""

def test_phone_validation(phone):
    """Probar la lógica de validación de teléfono"""
    if phone:
        # Extraer solo dígitos del teléfono
        phone_digits = ''.join(filter(str.isdigit, phone))
        if len(phone_digits) < 5:
            return False, f"🔴 SPAM: '{phone}' ({len(phone_digits)} dígitos) → ✅ Mensaje OK, ❌ No crear contacto"
        else:
            return True, f"✅ VÁLIDO: '{phone}' ({len(phone_digits)} dígitos) → ✅ Mensaje OK, ✅ Crear contacto"
    return True, "✅ VACÍO: Teléfono opcional → ✅ Mensaje OK, ✅ Crear contacto"


# Casos de prueba
test_cases = [
    # Casos de spam (menos de 5 dígitos)
    "1",
    "12",
    "123",
    "1234",
    "abc",
    "123a",
    
    # Casos válidos (5 o más dígitos)
    "12345",
    "123456",
    "1234567890",
    "+34 123 456 789",
    "(555) 123-4567",
    "+1-555-123-4567",
    "555.123.4567",
    
    # Caso vacío
    "",
    None
]

print("=" * 80)
print("VALIDACIÓN ANTI-SPAM SILENCIOSA PARA TELÉFONOS")
print("=" * 80)
print("\n🎭 ESTRATEGIA: Engañar al atacante")
print("   - SIEMPRE mostrar mensaje de éxito")
print("   - SPAM: Guardar submission, pero NO crear contacto ni enviar notificaciones")
print("   - VÁLIDO: Guardar submission, crear contacto y enviar notificaciones")
print("\n📊 REGLA: Teléfono debe tener al menos 5 dígitos")
print("=" * 80)
print()

for phone in test_cases:
    is_valid, message = test_phone_validation(phone)
    print(message)

print("\n" + "=" * 80)
print("🔒 VENTAJAS DE SEGURIDAD:")
print("   ✓ El spammer ve 'éxito' siempre → No sabe que fue detectado")
print("   ✓ No desperdiciamos recursos en contactos spam")
print("   ✓ Los logs internos registran los intentos de spam")
print("   ✓ El submission queda guardado para análisis forense")
print("=" * 80)
