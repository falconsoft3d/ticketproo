# Generated manually on 2025-09-23 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0027_make_due_date_optional'),
    ]

    operations = [
        # Renombrar el campo 'name' a 'title'
        migrations.RenameField(
            model_name='task',
            old_name='name',
            new_name='title',
        ),
        
        # Cambiar due_date de DateTimeField a DateField
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateField(
                blank=True,
                help_text='Fecha límite para completar la tarea (opcional)',
                null=True,
                verbose_name='Fecha de vencimiento'
            ),
        ),
        
        # Agregar campo ticket
        migrations.AddField(
            model_name='task',
            name='ticket',
            field=models.ForeignKey(
                blank=True,
                help_text='Ticket asociado a esta tarea',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to='tickets.ticket',
                verbose_name='Ticket relacionado'
            ),
        ),
        
        # Remover el campo actual_hours si existe
        migrations.RemoveField(
            model_name='task',
            name='actual_hours',
        ),
    ]