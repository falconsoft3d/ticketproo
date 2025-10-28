# Generated manually on 2025-10-28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_user_field_data(apps, schema_editor):
    """Migrar datos del campo user de texto a ForeignKey"""
    MonthlyCumplimiento = apps.get_model('tickets', 'MonthlyCumplimiento')
    User = apps.get_model('auth', 'User')
    
    # Obtener todos los registros existentes
    for cumplimiento in MonthlyCumplimiento.objects.all():
        user_text = cumplimiento.user
        
        # Intentar encontrar el usuario por diferentes criterios
        user = None
        
        # 1. Buscar por username exacto
        try:
            user = User.objects.get(username=user_text)
        except User.DoesNotExist:
            pass
        
        # 2. Si no se encuentra, buscar por first_name
        if not user:
            try:
                user = User.objects.get(first_name__iexact=user_text)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        
        # 3. Si no se encuentra, buscar por last_name
        if not user:
            try:
                user = User.objects.get(last_name__iexact=user_text)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        
        # 4. Si no se encuentra, crear un usuario por defecto o usar el primer superusuario
        if not user:
            # Usar el primer superusuario como fallback
            try:
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    # Si no hay superusuarios, usar el primer usuario disponible
                    user = User.objects.first()
            except:
                pass
        
        # Actualizar el campo user_temp con el ID del usuario encontrado
        if user:
            cumplimiento.user_temp = user.id
            cumplimiento.save()


def reverse_migrate_user_field_data(apps, schema_editor):
    """Revertir la migración (no implementada)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0231_monthlycumplimiento_dailycumplimiento_and_more'),
    ]

    operations = [
        # Paso 1: Agregar campo temporal para almacenar el ID del usuario
        migrations.AddField(
            model_name='monthlycumplimiento',
            name='user_temp',
            field=models.IntegerField(null=True, blank=True),
        ),
        
        # Paso 2: Migrar los datos del campo texto al campo temporal
        migrations.RunPython(migrate_user_field_data, reverse_migrate_user_field_data),
        
        # Paso 3: Eliminar el campo user original
        migrations.RemoveField(
            model_name='monthlycumplimiento',
            name='user',
        ),
        
        # Paso 4: Agregar el nuevo campo user como ForeignKey
        migrations.AddField(
            model_name='monthlycumplimiento',
            name='user',
            field=models.ForeignKey(
                help_text='Usuario que debe cumplir esta meta',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='monthly_cumplimientos',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuario',
                null=True  # Temporalmente nullable
            ),
        ),
        
        # Paso 5: Copiar datos del campo temporal al nuevo campo ForeignKey
        migrations.RunSQL(
            "UPDATE tickets_monthlycumplimiento SET user_id = user_temp WHERE user_temp IS NOT NULL;",
            reverse_sql="UPDATE tickets_monthlycumplimiento SET user_temp = user_id WHERE user_id IS NOT NULL;"
        ),
        
        # Paso 6: Hacer el campo user no-nullable
        migrations.AlterField(
            model_name='monthlycumplimiento',
            name='user',
            field=models.ForeignKey(
                help_text='Usuario que debe cumplir esta meta',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='monthly_cumplimientos',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuario'
            ),
        ),
        
        # Paso 7: Eliminar el campo temporal
        migrations.RemoveField(
            model_name='monthlycumplimiento',
            name='user_temp',
        ),
    ]