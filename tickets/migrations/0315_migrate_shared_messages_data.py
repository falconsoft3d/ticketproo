# Generated manually to migrate data from SharedAIChatMessage to PublicAIMessageShare

from django.db import migrations


def migrate_shared_messages(apps, schema_editor):
    """Migrar datos del modelo antiguo al nuevo"""
    # Obtener modelos
    SharedAIChatMessage = apps.get_model('tickets', 'SharedAIChatMessage')
    PublicAIMessageShare = apps.get_model('tickets', 'PublicAIMessageShare')
    
    # Copiar todos los registros activos del modelo antiguo al nuevo
    old_shares = SharedAIChatMessage.objects.all()
    
    for old_share in old_shares:
        # Verificar si ya existe para evitar duplicados
        exists = PublicAIMessageShare.objects.filter(token=old_share.share_token).exists()
        
        if not exists:
            try:
                PublicAIMessageShare.objects.create(
                    chat_message_id=old_share.message_id,
                    shared_by_id=old_share.user_id,
                    token=old_share.share_token,
                    public_title=old_share.title,
                    is_active=old_share.is_active,
                    created_at=old_share.created_at,
                    views_count=old_share.views_count,
                    expiration_date=old_share.expires_at
                )
                print(f"✅ Migrado: {old_share.share_token[:8]}...")
            except Exception as e:
                print(f"❌ Error migrando {old_share.share_token[:8]}...: {e}")


def reverse_migration(apps, schema_editor):
    """Revertir la migración si es necesario"""
    PublicAIMessageShare = apps.get_model('tickets', 'PublicAIMessageShare')
    PublicAIMessageShare.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0314_create_publicaimessageshare'),
    ]

    operations = [
        migrations.RunPython(migrate_shared_messages, reverse_migration),
    ]
