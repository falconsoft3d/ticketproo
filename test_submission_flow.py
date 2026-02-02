#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar el flujo completo de submission con validación anti-spam
"""

def simulate_submission(telefono, nombre="Juan", apellido="Pérez", email="test@test.com"):
    """Simular el proceso de envío de formulario"""
    
    print(f"\n{'='*80}")
    print(f"📝 SIMULACIÓN DE ENVÍO")
    print(f"   Nombre: {nombre} {apellido}")
    print(f"   Email: {email}")
    print(f"   Teléfono: '{telefono}'")
    print(f"{'='*80}")
    
    # Paso 1: El formulario se valida (sin restricciones de teléfono)
    print("✅ Paso 1: Formulario válido (nombre, apellido, email presentes)")
    
    # Paso 2: Se guarda el submission
    print("✅ Paso 2: Submission guardado en base de datos")
    
    # Paso 3: Detectar spam
    is_spam = False
    if telefono:
        phone_digits = ''.join(filter(str.isdigit, telefono))
        if len(phone_digits) < 5:
            is_spam = True
            print(f"⚠️  Paso 3: SPAM DETECTADO - Teléfono '{telefono}' tiene {len(phone_digits)} dígitos")
        else:
            print(f"✅ Paso 3: Teléfono válido - '{telefono}' tiene {len(phone_digits)} dígitos")
    else:
        print("✅ Paso 3: Teléfono vacío (opcional)")
    
    # Paso 4: Crear contacto solo si NO es spam
    if not is_spam:
        print("✅ Paso 4: Contacto creado en el sistema")
        print("📧 Paso 5: Notificaciones enviadas (email + telegram)")
    else:
        print("❌ Paso 4: Contacto NO creado (es spam)")
        print("❌ Paso 5: Notificaciones NO enviadas (es spam)")
    
    # Paso 6: SIEMPRE mostrar página de éxito
    print("🎉 Paso 6: MENSAJE DE ÉXITO MOSTRADO AL USUARIO")
    print("           '¡Formulario enviado con éxito! Nos pondremos en contacto contigo pronto.'")
    
    if is_spam:
        print("\n🎭 RESULTADO: El spammer ve éxito, pero no se creó contacto ni se enviaron notificaciones")
    else:
        print("\n✅ RESULTADO: Lead legítimo procesado completamente")
    
    print(f"{'='*80}\n")


# Casos de prueba
print("\n" + "="*80)
print("PRUEBA DE FLUJO COMPLETO: VALIDACIÓN ANTI-SPAM SILENCIOSA")
print("="*80)

# Casos de spam
print("\n🔴 CASOS DE SPAM (< 5 dígitos):")
simulate_submission("1")
simulate_submission("123")
simulate_submission("1234")

# Casos válidos
print("\n✅ CASOS VÁLIDOS (≥ 5 dígitos):")
simulate_submission("12345")
simulate_submission("+34 123 456 789")
simulate_submission("(555) 123-4567")

print("\n" + "="*80)
print("CONCLUSIÓN:")
print("En TODOS los casos, el usuario ve el mensaje de éxito.")
print("Solo cambia internamente si se crea el contacto o no.")
print("="*80)
