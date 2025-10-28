"""
Comando para resolver el problema de migración duplicada del campo public_token
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Resuelve el problema de migración duplicada del campo public_token en QRCode'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Resolviendo problema de migración duplicada...')
        
        # Verificar si la columna ya existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='tickets_qrcode' AND column_name='public_token';
            """)
            
            column_exists = cursor.fetchone() is not None
            
            if column_exists:
                self.stdout.write(
                    self.style.SUCCESS('✅ La columna public_token ya existe')
                )
                
                # Marcar la migración problemática como aplicada
                try:
                    from django.db.migrations.recorder import MigrationRecorder
                    recorder = MigrationRecorder(connection)
                    
                    # Verificar si la migración 0237 está marcada como aplicada
                    applied_migrations = recorder.applied_migrations()
                    migration_key = ('tickets', '0237_auto_20251028_1455')
                    
                    if migration_key not in applied_migrations:
                        # Marcar como aplicada sin ejecutar
                        recorder.record_applied('tickets', '0237_auto_20251028_1455')
                        self.stdout.write(
                            self.style.SUCCESS('✅ Migración 0237 marcada como aplicada')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING('⚠️ La migración 0237 ya está marcada como aplicada')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error al marcar migración: {e}')
                    )
                    
            else:
                self.stdout.write(
                    self.style.ERROR('❌ La columna public_token no existe. Ejecute las migraciones normalmente.')
                )
                
        self.stdout.write(
            self.style.SUCCESS('🎉 Proceso completado. Ahora puede ejecutar: python manage.py migrate')
        )