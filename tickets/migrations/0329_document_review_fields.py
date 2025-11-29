# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0328_functionalrequirementdocument_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='functionalrequirementdocument',
            name='document_status',
            field=models.CharField(
                choices=[('pending', 'Pendiente'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado')],
                default='pending',
                max_length=20,
                verbose_name='Estado del Documento'
            ),
        ),
        migrations.AddField(
            model_name='functionalrequirementdocument',
            name='document_reviewed_by_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='Revisado por'),
        ),
        migrations.AddField(
            model_name='functionalrequirementdocument',
            name='document_reviewed_by_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email del revisor'),
        ),
        migrations.AddField(
            model_name='functionalrequirementdocument',
            name='document_reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de revisión'),
        ),
        migrations.AddField(
            model_name='functionalrequirementdocument',
            name='document_review_comments',
            field=models.TextField(blank=True, verbose_name='Comentarios de revisión'),
        ),
    ]
