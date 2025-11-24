# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0279_quotationview'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='had_meeting',
            field=models.BooleanField(default=False, help_text='Marcar si se tuvo una reunion con este contacto', verbose_name='Reunion realizada'),
        ),
        migrations.AddField(
            model_name='contact',
            name='meeting_date',
            field=models.DateField(blank=True, help_text='Fecha en la que se realizo la reunion', null=True, verbose_name='Fecha de reunion'),
        ),
    ]
