# Generated manually to migrate data from SharedAIChatMessage to PublicAIMessageShare

from django.db import migrations


def migrate_shared_messages(apps, schema_editor):
    """Migrar datos del modelo antiguo al nuevo"""
    try:
        # Obtener modelos
        PublicAIMessageShare = apps.get_model('tickets', 'PublicAIMessageShare')
        
        # Intentar obtener el modelo antiguo
        try:
            SharedAIChatMessage = apps.get_model('tickets', 'SharedAIChatMessage')
        except LookupError:
            print("ℹ️  Modelo SharedAIChatMessage no encontrado, saltando migración de datos")
            return
        
        # Verificar si la tabla antigua existe
        db_alias = schema_editor.connection.alias
        table_name = SharedAIChatMessage._meta.db_table
        
        with schema_editor.connection.cursor() as cursor:
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, [table_name])
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print("ℹ️  Tabla antigua no existe, saltando migración de datos")
                return
            
            # Verificar qué columnas existen en la tabla antigua
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s;
            """, [table_name])
            
            existing_columns = [row[0] for row in cursor.fetchall()]
            print(f"ℹ️  Columnas disponibles: {existing_columns}")
        
        # Intentar migrar datos solo si hay registros
        try:
            old_shares_count = SharedAIChatMessage.objects.count()
            
            if old_shares_count == 0:
                print("ℹ️  No hay datos para migrar")
                return
            
            print(f"ℹ️  Intentando migrar {old_shares_count} registros...")
            
            # Usar raw SQL para obtener solo las columnas que existen
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [col[0] for col in cursor.description]
                
                for row in cursor.fetchall():
                    row_data = dict(zip(columns, row))
                    
                    # Extraer token de diferentes posibles nombres de columna
                    token = row_data.get('token') or row_data.get('share_token')
                    
                    if not token:
                        continue
                    
                    # Verificar si ya existe
                    if PublicAIMessageShare.objects.filter(token=token).exists():
                        continue
                    
                    # Crear nuevo registro
                    PublicAIMessageShare.objects.create(
                        chat_message_id=row_data.get('message_id') or row_data.get('chat_message_id'),
                        shared_by_id=row_data.get('user_id') or row_data.get('shared_by_id'),
                        token=token,
                        public_title=row_data.get('title', '') or row_data.get('public_title', ''),
                        is_active=row_data.get('is_active', True),
                        created_at=row_data.get('created_at'),
                        views_count=row_data.get('views_count', 0),
                        expiration_date=row_data.get('expires_at') or row_data.get('expiration_date')
                    )
                    print(f"✅ Migrado: {token[:8]}...")
        except Exception as e:
            print(f"⚠️  Error durante la migración de datos: {e}")
            
    except Exception as e:
        print(f"ℹ️  Migración de datos saltada (esto es normal en instalaciones nuevas): {e}")


def reverse_migration(apps, schema_editor):
    """Revertir la migración si es necesario"""
    try:
        PublicAIMessageShare = apps.get_model('tickets', 'PublicAIMessageShare')
        PublicAIMessageShare.objects.all().delete()
        print("ℹ️  Datos revertidos exitosamente")
    except Exception as e:
        print(f"ℹ️  No se pudo revertir la migración: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0314_create_publicaimessageshare'),
    ]

    operations = [
        migrations.RunPython(migrate_shared_messages, reverse_migration),
    ]
