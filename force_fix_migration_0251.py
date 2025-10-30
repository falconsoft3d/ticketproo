#!/usr/bin/env python
"""
Script alternativo para el servidor de producción.
Este script fuerza la marcación de la migración 0251 como aplicada
independientemente del estado actual.

USAR SOLO EN PRODUCCIÓN DESPUÉS DE VERIFICAR QUE LAS TABLAS EXISTEN.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def force_mark_migration_applied():
    """
    Fuerza la marcación de la migración 0251 como aplicada
    """
    print("🔧 Forzando marcación de migración 0251 como aplicada...")
    
    try:
        # Verificar si las tablas existen
        with connection.cursor() as cursor:
            if 'postgresql' in connection.settings_dict['ENGINE']:
                # PostgreSQL
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('tickets_contactcomment', 'tickets_contactattachment')
                    AND table_schema = 'public';
                """)
                table_count = cursor.fetchone()[0]
                
                if table_count == 2:
                    print("✅ Las tablas ContactComment y ContactAttachment existen")
                    
                    # Marcar como aplicada
                    recorder = MigrationRecorder(connection)
                    
                    # Eliminar registro previo si existe
                    cursor.execute("""
                        DELETE FROM django_migrations 
                        WHERE app = 'tickets' AND name = '0251_contact_comments_attachments';
                    """)
                    
                    # Insertar nuevo registro
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('tickets', '0251_contact_comments_attachments', NOW());
                    """)
                    
                    print("✅ Migración 0251 marcada como aplicada exitosamente")
                    return True
                else:
                    print(f"❌ Solo se encontraron {table_count} de 2 tablas esperadas")
                    return False
            else:
                print("ℹ️  No es base de datos PostgreSQL")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("🚨 SCRIPT DE EMERGENCIA - Marcación Forzada de Migración 0251")
    print("=" * 60)
    print("⚠️  USAR SOLO EN PRODUCCIÓN DESPUÉS DE VERIFICAR TABLAS")
    print("=" * 60)
    
    try:
        if force_mark_migration_applied():
            print("\n✅ ¡Migración marcada exitosamente!")
            print("\nAhora ejecuta: python manage.py migrate")
        else:
            print("\n❌ Error al marcar la migración")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        sys.exit(1)