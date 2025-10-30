#!/usr/bin/env python
"""
Script de verificación para diagnosticar el problema de migración 0251
en el servidor de producción.

Este script verifica:
1. Estado de las tablas en la base de datos
2. Estado de las migraciones aplicadas
3. Archivos de migración existentes
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_system.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
import glob

def check_database_tables():
    """Verifica qué tablas existen en la base de datos"""
    print("🗄️  Verificando tablas en la base de datos...")
    
    with connection.cursor() as cursor:
        if 'postgresql' in connection.settings_dict['ENGINE']:
            # PostgreSQL
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE tablename LIKE 'tickets_contact%'
                ORDER BY tablename;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"   Base de datos: PostgreSQL")
            print(f"   Tablas encontradas: {len(tables)}")
            for table in tables:
                print(f"     ✅ {table}")
                
            # Verificar tablas específicas
            required_tables = ['tickets_contact', 'tickets_contactcomment', 'tickets_contactattachment']
            missing = [table for table in required_tables if table not in tables]
            
            if missing:
                print(f"   ❌ Tablas faltantes: {missing}")
            else:
                print(f"   ✅ Todas las tablas necesarias están presentes")
                
        elif 'sqlite' in connection.settings_dict['ENGINE']:
            # SQLite
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'tickets_contact%'
                ORDER BY name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"   Base de datos: SQLite")
            print(f"   Tablas encontradas: {len(tables)}")
            for table in tables:
                print(f"     ✅ {table}")
        else:
            print(f"   Base de datos: {connection.settings_dict['ENGINE']}")
            print(f"   ⚠️  No se puede verificar automáticamente")
    
    return tables

def check_migration_files():
    """Verifica qué archivos de migración existen"""
    print("\n📁 Verificando archivos de migración...")
    
    migration_path = "tickets/migrations/"
    pattern = os.path.join(migration_path, "024[9-9]_*.py") + " " + os.path.join(migration_path, "025[0-5]_*.py")
    
    files = []
    for pattern_part in pattern.split():
        files.extend(glob.glob(pattern_part))
    
    files.sort()
    
    print(f"   Archivos de migración encontrados: {len(files)}")
    
    relevant_migrations = [
        "0249_contactcomment_contactattachment.py",
        "0250_auto_20251030_2004.py", 
        "0251_contact_comments_attachments.py",
        "0252_alter_contactattachment_file_and_more.py",
        "0253_auto_20251030_2028.py",
        "0254_opportunityactivity_contact.py",
        "0255_contact_country.py"
    ]
    
    for migration in relevant_migrations:
        file_path = os.path.join(migration_path, migration)
        if os.path.exists(file_path):
            print(f"     ✅ {migration}")
        else:
            print(f"     ❌ {migration} (FALTANTE)")
    
    return files

def check_applied_migrations():
    """Verifica qué migraciones están marcadas como aplicadas"""
    print("\n📋 Verificando migraciones aplicadas...")
    
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
    
    print(f"   Migraciones verificadas:")
    for migration in relevant_migrations:
        status = "✅ Aplicada" if migration in applied_migrations else "❌ Pendiente"
        print(f"     {migration[1]}: {status}")
    
    return applied_migrations

def diagnose_problem():
    """Diagnostica el problema específico"""
    print("\n🔍 Diagnóstico del problema...")
    
    # Obtener información
    tables = check_database_tables()
    files = check_migration_files() 
    applied = check_applied_migrations()
    
    # Analizar situación
    has_contact_tables = any('contactcomment' in table for table in tables) and any('contactattachment' in table for table in tables)
    has_0249_applied = ('tickets', '0249_contactcomment_contactattachment') in applied
    has_0251_file = os.path.exists('tickets/migrations/0251_contact_comments_attachments.py')
    has_0251_applied = ('tickets', '0251_contact_comments_attachments') in applied
    
    print(f"\n📊 Análisis:")
    print(f"   Las tablas ContactComment/ContactAttachment existen: {'✅ Sí' if has_contact_tables else '❌ No'}")
    print(f"   Migración 0249 aplicada: {'✅ Sí' if has_0249_applied else '❌ No'}")
    print(f"   Archivo 0251 existe: {'✅ Sí' if has_0251_file else '❌ No'}")
    print(f"   Migración 0251 aplicada: {'✅ Sí' if has_0251_applied else '❌ No'}")
    
    print(f"\n💡 Recomendación:")
    if has_contact_tables and has_0249_applied and not has_0251_file:
        print("   ✅ Situación CORRECTA - Las tablas existen y 0251 fue eliminada correctamente")
        print("   ➡️  Ejecutar: python manage.py migrate")
    elif has_contact_tables and has_0249_applied and has_0251_file:
        print("   ⚠️  PROBLEMA - Archivo 0251 duplicado existe")
        print("   ➡️  Eliminar: tickets/migrations/0251_contact_comments_attachments.py")
        print("   ➡️  Luego ejecutar: python manage.py migrate")
    elif has_contact_tables and not has_0251_applied:
        print("   🔧 SOLUCIÓN - Marcar 0251 como aplicada")
        print("   ➡️  Ejecutar: python fix_migration_0251.py")
    else:
        print("   ❌ PROBLEMA COMPLEJO - Revisar manualmente")
        print("   ➡️  Consultar documentación o soporte")

if __name__ == '__main__':
    print("🔍 DIAGNÓSTICO DE MIGRACIÓN 0251")
    print("=" * 50)
    
    try:
        check_database_tables()
        check_migration_files()
        check_applied_migrations()
        diagnose_problem()
        
        print(f"\n✅ Diagnóstico completado")
        
    except Exception as e:
        print(f"\n❌ Error durante diagnóstico: {e}")
        sys.exit(1)