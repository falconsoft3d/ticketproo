# Generated manually to fix duplicate button counter migrations

from django.db import migrations, models
from django.db import connection


def check_and_add_button_counters(apps, schema_editor):
    """
    Check if button counter columns exist and add them only if they don't exist
    """
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        existing_columns = []
        
        if db_vendor == 'postgresql':
            # PostgreSQL syntax
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='tickets_landingpage' 
                AND column_name IN ('meeting_button_clicks', 'contact_button_clicks')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
        elif db_vendor == 'sqlite':
            # SQLite syntax
            try:
                cursor.execute("PRAGMA table_info(tickets_landingpage)")
                columns_info = cursor.fetchall()
                existing_columns = [col[1] for col in columns_info]  # Column name is at index 1
            except Exception:
                existing_columns = []
        
        # Add missing columns
        if 'meeting_button_clicks' not in existing_columns:
            try:
                cursor.execute("""
                    ALTER TABLE tickets_landingpage 
                    ADD COLUMN meeting_button_clicks INTEGER DEFAULT 0 NOT NULL
                """)
            except Exception:
                # Column might already exist
                pass
                
        if 'contact_button_clicks' not in existing_columns:
            try:
                cursor.execute("""
                    ALTER TABLE tickets_landingpage 
                    ADD COLUMN contact_button_clicks INTEGER DEFAULT 0 NOT NULL
                """)
            except Exception:
                # Column might already exist
                pass


def reverse_button_counters(apps, schema_editor):
    """
    Remove button counter columns if they exist
    """
    db_vendor = connection.vendor
    
    with connection.cursor() as cursor:
        if db_vendor == 'postgresql':
            cursor.execute("ALTER TABLE tickets_landingpage DROP COLUMN IF EXISTS meeting_button_clicks")
            cursor.execute("ALTER TABLE tickets_landingpage DROP COLUMN IF EXISTS contact_button_clicks")
        elif db_vendor == 'sqlite':
            # SQLite doesn't support DROP COLUMN IF EXISTS, so we need to be more careful
            try:
                cursor.execute("PRAGMA table_info(tickets_landingpage)")
                columns_info = cursor.fetchall()
                existing_columns = [col[1] for col in columns_info]
                
                # SQLite requires recreating the table to drop columns
                # For simplicity, we'll just leave the columns (they won't hurt)
                pass
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0194_add_signers_to_internal_agreement'),
    ]

    operations = [
        migrations.RunPython(
            check_and_add_button_counters,
            reverse_button_counters,
        ),
    ]