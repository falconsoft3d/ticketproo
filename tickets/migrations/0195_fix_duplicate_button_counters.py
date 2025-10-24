# Generated manually to fix duplicate button counter migrations

from django.db import migrations, models
from django.db import connection


def check_and_add_button_counters(apps, schema_editor):
    """
    Check if button counter columns exist and add them only if they don't exist
    """
    with connection.cursor() as cursor:
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='tickets_landingpage' 
            AND column_name IN ('meeting_button_clicks', 'contact_button_clicks')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        if 'meeting_button_clicks' not in existing_columns:
            cursor.execute("""
                ALTER TABLE tickets_landingpage 
                ADD COLUMN meeting_button_clicks INTEGER DEFAULT 0 NOT NULL
            """)
            
        if 'contact_button_clicks' not in existing_columns:
            cursor.execute("""
                ALTER TABLE tickets_landingpage 
                ADD COLUMN contact_button_clicks INTEGER DEFAULT 0 NOT NULL
            """)


def reverse_button_counters(apps, schema_editor):
    """
    Remove button counter columns if they exist
    """
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE tickets_landingpage DROP COLUMN IF EXISTS meeting_button_clicks")
        cursor.execute("ALTER TABLE tickets_landingpage DROP COLUMN IF EXISTS contact_button_clicks")


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