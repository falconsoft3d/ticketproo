# Generated manually on 2025-09-23 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0026_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateTimeField(
                blank=True,
                help_text='Fecha y hora límite para completar la tarea (opcional)',
                null=True,
                verbose_name='Fecha de vencimiento'
            ),
        ),
    ]