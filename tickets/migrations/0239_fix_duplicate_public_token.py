# Generated manually to fix duplicate public_token field migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0238_quicktodo'),
    ]

    operations = [
        # Esta migración no hace nada, solo marca que el problema fue resuelto
        # La columna public_token ya existe de la migración 0236
    ]