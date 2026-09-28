import uuid

from django.db import migrations, models


def fix_duplicate_public_tokens(apps, schema_editor):
    """
    La migración 0048 añadió public_token con default=uuid.uuid4, lo que asignó
    el mismo UUID a todas las empresas existentes. Se conserva el token en la
    empresa con menor id (la que resolvía hasta ahora) y se regenera en el resto.
    """
    Company = apps.get_model('tickets', 'Company')
    seen = set()
    for company in Company.objects.order_by('id'):
        if company.public_token is None or company.public_token in seen:
            company.public_token = uuid.uuid4()
            company.save(update_fields=['public_token'])
        seen.add(company.public_token)


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0486_apiendpoint'),
    ]

    operations = [
        migrations.RunPython(fix_duplicate_public_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='company',
            name='public_token',
            field=models.UUIDField(blank=True, default=uuid.uuid4, help_text='Token único para acceso público a estadísticas', null=True, unique=True, verbose_name='Token público'),
        ),
    ]
