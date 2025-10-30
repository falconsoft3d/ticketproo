# Generated manually for contact comments and attachments

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def contact_attachment_upload_path(instance, filename):
    """Ruta de subida para adjuntos de contactos"""
    return f'contact_attachments/contact_{instance.contact.id}/{filename}'


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0250_auto_20251030_2004'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Escribe tu comentario aquí', verbose_name='Comentario')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tickets.contact', verbose_name='Contacto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Comentario de Contacto',
                'verbose_name_plural': 'Comentarios de Contacto',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContactAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='contact_attachments/', verbose_name='Archivo')),
                ('original_filename', models.CharField(max_length=255, verbose_name='Nombre original')),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de subida')),
                ('file_size', models.PositiveIntegerField(default=0, verbose_name='Tamaño del archivo (bytes)')),
                ('description', models.TextField(blank=True, help_text='Descripción opcional del adjunto', verbose_name='Descripción')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='tickets.contact', verbose_name='Contacto')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Subido por')),
            ],
            options={
                'verbose_name': 'Adjunto de Contacto',
                'verbose_name_plural': 'Adjuntos de Contacto',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]