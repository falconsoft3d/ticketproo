#!/usr/bin/env python
"""
Script para resolver el problema de la migración duplicada 0251
en el servidor de producción con PostgreSQL.

Este script marca la migración 0251 como aplicada sin ejecutar las operaciones,
ya que la migración 0249 ya creó las tablas necesarias.

Uso:
python fix_migration_0251.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def fix_migration_0251():
    """
    Marca la migración 0251 como aplicada sin ejecutar las operaciones
    """
    print("🔧 Iniciando corrección de migración 0251...")
    
    # Verificar si las tablas ya existen
    with connection.cursor() as cursor:
        # Verificar PostgreSQL
        if 'postgresql' in connection.settings_dict['ENGINE']:
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE tablename IN ('tickets_contactcomment', 'tickets_contactattachment');
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tablas existentes: {existing_tables}")
            
            if 'tickets_contactcomment' in existing_tables and 'tickets_contactattachment' in existing_tables:
                print("✅ Las tablas ContactComment y ContactAttachment ya existen")
                
                # Verificar si la migración 0251 está marcada como aplicada
                recorder = MigrationRecorder(connection)
                applied_migrations = recorder.applied_migrations()
                
                migration_0251 = ('tickets', '0251_contact_comments_attachments')
                
                if migration_0251 not in applied_migrations:
                    print("🚀 Marcando migración 0251 como aplicada...")
                    recorder.record_applied('tickets', '0251_contact_comments_attachments')
                    print("✅ Migración 0251 marcada como aplicada exitosamente")
                else:
                    print("ℹ️  La migración 0251 ya está marcada como aplicada")
                    
            else:
                print("❌ Las tablas no existen. La migración 0249 no se aplicó correctamente.")
                return False
                
        else:
            print("ℹ️  Base de datos no es PostgreSQL, no es necesario aplicar corrección")
            
    print("🎉 Corrección completada exitosamente")
    return True

def check_migration_status():
    """
    Verifica el estado actual de las migraciones relacionadas
    """
    print("\n📊 Estado de migraciones relacionadas:")
    recorder = MigrationRecorder(connection)
    applied_migrations = recorder.applied_migrations()
    
    relevant_migrations = [
        ('tickets', '0249_contactcomment_contactattachment'),
        ('tickets', '0250_auto_20251030_2004'),
        ('tickets', '0251_contact_comments_attachments'),
        ('tickets', '0252_alter_contactattachment_file_and_more'),
        ('tickets', '0253_auto_20251030_2028'),
        ('tickets', '0254_opportunityactivity_contact'),
        ('tickets', '0255_contact_country'),
    ]
    
    for migration in relevant_migrations:
        status = "✅ Aplicada" if migration in applied_migrations else "❌ Pendiente"
        print(f"  {migration[1]}: {status}")

if __name__ == '__main__':
    print("🛠️  Script de Corrección de Migración 0251")
    print("=" * 50)
    
    try:
        check_migration_status()
        
        # Solo aplicar corrección si es necesario
        recorder = MigrationRecorder(connection)
        applied_migrations = recorder.applied_migrations()
        migration_0251 = ('tickets', '0251_contact_comments_attachments')
        
        if migration_0251 not in applied_migrations:
            print("\n🔧 Aplicando corrección...")
            if fix_migration_0251():
                print("\n✅ ¡Corrección aplicada exitosamente!")
                print("\nAhora puedes ejecutar: python manage.py migrate")
            else:
                print("\n❌ Error en la corrección")
                sys.exit(1)
        else:
            print("\nℹ️  No es necesario aplicar corrección")
            
        print("\n📊 Estado final:")
        check_migration_status()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nSi el error persiste, considera:")
        print("1. Verificar que la migración 0249 se aplicó correctamente")
        print("2. Revisar las dependencias de las migraciones")
        print("3. Consultar los logs de la base de datos")
        sys.exit(1)