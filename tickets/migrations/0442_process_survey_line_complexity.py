from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0441_process_survey_line_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='processsurveyline',
            name='complexity',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name='Complejidad',
                help_text='Nivel de complejidad del proceso: 1 (muy simple) a 10 (muy complejo)',
            ),
        ),
    ]
