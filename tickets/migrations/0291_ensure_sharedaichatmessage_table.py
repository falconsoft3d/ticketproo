# Generated manually on 2025-11-25
# This migration ensures the SharedAIChatMessage table exists in all environments
# It's safe to run multiple times and works for both PostgreSQL and SQLite

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def create_shared_ai_chat_message_table(apps, schema_editor):
    """
    Crea la tabla tickets_sharedaichatmessage de forma segura.
    Compatible con PostgreSQL y SQLite.
    """
    db_alias = schema_editor.connection.alias
    connection = schema_editor.connection
    
    # Detectar el motor de base de datos
    engine = connection.settings_dict['ENGINE']
    is_postgres = 'postgresql' in engine
    is_sqlite = 'sqlite' in engine
    
    if is_postgres:
        # Para PostgreSQL
        schema_editor.execute("""
            CREATE TABLE IF NOT EXISTS tickets_sharedaichatmessage (
                id BIGSERIAL PRIMARY KEY,
                share_token VARCHAR(64) UNIQUE NOT NULL,
                title VARCHAR(200) DEFAULT '',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                views_count INTEGER DEFAULT 0 CHECK (views_count >= 0),
                expires_at TIMESTAMP WITH TIME ZONE NULL,
                message_id BIGINT NOT NULL,
                user_id INTEGER NOT NULL,
                CONSTRAINT tickets_sharedaichatmessage_message_id_fkey 
                    FOREIGN KEY (message_id) 
                    REFERENCES tickets_aichatmessage(id) 
                    ON DELETE CASCADE,
                CONSTRAINT tickets_sharedaichatmessage_user_id_fkey 
                    FOREIGN KEY (user_id) 
                    REFERENCES auth_user(id) 
                    ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_share_token 
                ON tickets_sharedaichatmessage(share_token);
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_message_id 
                ON tickets_sharedaichatmessage(message_id);
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_user_id 
                ON tickets_sharedaichatmessage(user_id);
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_created_at 
                ON tickets_sharedaichatmessage(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_is_active 
                ON tickets_sharedaichatmessage(is_active) 
                WHERE is_active = TRUE;
        """)
        
    elif is_sqlite:
        # Para SQLite
        schema_editor.execute("""
            CREATE TABLE IF NOT EXISTS tickets_sharedaichatmessage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_token VARCHAR(64) UNIQUE NOT NULL,
                title VARCHAR(200) DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                views_count INTEGER DEFAULT 0 CHECK (views_count >= 0),
                expires_at DATETIME NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (message_id) 
                    REFERENCES tickets_aichatmessage(id) 
                    ON DELETE CASCADE,
                FOREIGN KEY (user_id) 
                    REFERENCES auth_user(id) 
                    ON DELETE CASCADE
            );
        """)
        
        # Crear índices para SQLite
        schema_editor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_share_token 
                ON tickets_sharedaichatmessage(share_token);
        """)
        schema_editor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_message_id 
                ON tickets_sharedaichatmessage(message_id);
        """)
        schema_editor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_user_id 
                ON tickets_sharedaichatmessage(user_id);
        """)
        schema_editor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sharedaichatmessage_created_at 
                ON tickets_sharedaichatmessage(created_at DESC);
        """)


def reverse_migration(apps, schema_editor):
    """
    Revertir la migración eliminando la tabla de forma segura.
    """
    schema_editor.execute("""
        DROP TABLE IF EXISTS tickets_sharedaichatmessage CASCADE;
    """)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0290_webcounter_webcountervisit_and_more'),
    ]

    operations = [
        migrations.RunPython(
            create_shared_ai_chat_message_table,
            reverse_migration
        ),
    ]
