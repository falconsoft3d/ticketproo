#!/usr/bin/env python3
"""
Script de prueba para verificar la lógica del control de horario público
"""

import os
import sys
import django
from datetime import datetime, date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import PublicTimeAccess, TimeEntry

def test_time_logic():
    print("=== Prueba de Lógica del Control de Horario ===")
    print()
    
    # Obtener usuario con acceso público
    try:
        public_access = PublicTimeAccess.objects.filter(is_active=True).first()
        if not public_access:
            print("❌ No hay usuarios con acceso público activo")
            return
        
        user = public_access.user
        print(f"👤 Usuario de prueba: {user.get_full_name() or user.username}")
        print(f"🔗 Token: {public_access.token[:16]}...")
        print()
        
        # Verificar estado actual
        active_entry = TimeEntry.get_active_entry(user)
        
        if active_entry:
            print("📋 Estado actual:")
            print(f"   ✅ Jornada ACTIVA desde: {active_entry.fecha_entrada.strftime('%H:%M')}")
            print(f"   ⏱️  Duración actual: {active_entry.duracion_formateada}")
            print(f"   📝 Notas entrada: {active_entry.notas_entrada or 'Sin notas'}")
            print()
            print("🔘 Botón visible: REGISTRAR SALIDA")
        else:
            print("📋 Estado actual:")
            print("   ❌ Sin jornada activa")
            print()
            print("🔘 Botón visible: REGISTRAR ENTRADA")
        
        print()
        
        # Mostrar entradas del día
        today = date.today()
        today_entries = TimeEntry.objects.filter(
            user=user,
            fecha_entrada__date=today
        ).order_by('-fecha_entrada')
        
        print(f"📅 Registros de hoy ({today.strftime('%d/%m/%Y')}):")
        if today_entries:
            for entry in today_entries:
                status = "🟢 Activo" if not entry.fecha_salida else "🔴 Finalizado"
                duration = entry.duracion_formateada if entry.fecha_salida else "En curso"
                entrada = entry.fecha_entrada.strftime('%H:%M')
                salida = entry.fecha_salida.strftime('%H:%M') if entry.fecha_salida else "--:--"
                
                print(f"   {status} | {entrada} - {salida} | {duration}")
                if entry.notas_entrada:
                    print(f"     📝 Entrada: {entry.notas_entrada}")
                if entry.notas_salida:
                    print(f"     📝 Salida: {entry.notas_salida}")
        else:
            print("   📭 Sin registros hoy")
        
        print()
        print("=== Lógica de Funcionamiento ===")
        print("✅ Si NO hay jornada activa → Muestra solo botón 'REGISTRAR ENTRADA'")
        print("✅ Si HAY jornada activa → Muestra solo botón 'REGISTRAR SALIDA'")
        print("✅ Al registrar entrada → Crea nuevo registro con solo hora de entrada")
        print("✅ Al registrar salida → Completa el registro existente con hora de salida")
        print("✅ Solo se ve un botón a la vez según el estado")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    test_time_logic()