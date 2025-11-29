# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0329_document_review_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='functionalrequirement',
            name='title',
            field=models.CharField(blank=True, help_text='Título breve del requerimiento', max_length=300, verbose_name='Título'),
        ),
    ]
