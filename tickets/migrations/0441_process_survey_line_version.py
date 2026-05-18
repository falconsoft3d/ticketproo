from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0440_process_survey_line_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='processsurveyline',
            name='version',
            field=models.PositiveSmallIntegerField(
                default=1,
                help_text='Número de versión del levantamiento (máx. 10)',
                verbose_name='Versión',
            ),
        ),
        migrations.AlterModelOptions(
            name='processsurveyline',
            options={
                'ordering': ['version', 'order', 'pk'],
                'verbose_name': 'Línea de Levantamiento',
                'verbose_name_plural': 'Líneas de Levantamiento',
            },
        ),
    ]
