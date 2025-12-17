# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0384_coursecomment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coursecomment',
            name='course',
        ),
        migrations.AddField(
            model_name='coursecomment',
            name='course_class',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                to='tickets.courseclass',
                verbose_name='Clase',
                default=1  # Valor temporal
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name='coursecomment',
            options={'ordering': ['-created_at'], 'verbose_name': 'Comentario de Clase', 'verbose_name_plural': 'Comentarios de Clases'},
        ),
    ]
