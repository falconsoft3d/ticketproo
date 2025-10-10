from django.core.management.base import BaseCommand
from tickets.models import ContactoWeb, SystemConfiguration
from tickets.utils import send_contact_notification
from django.utils import timezone


class Command(BaseCommand):
    help = 'Prueba el envío de notificaciones por email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            action='store_true',
            help='Configura automáticamente las notificaciones con valores de prueba',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Prueba de Notificaciones por Email ==='))
        
        # Obtener o crear configuración
        config = SystemConfiguration.get_config()
        
        if options['config']:
            # Configurar automáticamente para pruebas (modo consola)
            config.enable_email_notifications = True
            config.notification_emails = 'admin@localhost\ntest@localhost'
            config.email_host = 'localhost'
            config.email_port = 1025  # Puerto para servidor de prueba
            config.email_host_user = ''
            config.email_host_password = ''
            config.email_use_tls = False
            config.email_use_ssl = False
            config.email_from = 'noreply@ticketproo.local'
            config.save()
            self.stdout.write(
                self.style.SUCCESS('✅ Configuración de prueba establecida')
            )
        
        # Verificar configuración
        if not config.enable_email_notifications:
            self.stdout.write(
                self.style.ERROR('❌ Las notificaciones por email están deshabilitadas')
            )
            self.stdout.write('Usa --config para habilitar automáticamente')
            return
        
        if not config.notification_emails.strip():
            self.stdout.write(
                self.style.ERROR('❌ No hay emails de notificación configurados')
            )
            return
        
        # Crear un contacto de prueba
        contacto_prueba = ContactoWeb.objects.create(
            nombre='Usuario de Prueba',
            email='prueba@ejemplo.com',
            telefono='+34 600 123 456',
            empresa='Empresa de Prueba S.L.',
            asunto='Prueba de notificación por email',
            mensaje='Este es un mensaje de prueba para verificar que las notificaciones por email funcionan correctamente.\n\nSaludos cordiales.',
            ip_address='127.0.0.1',
            user_agent='Django Management Command Test'
        )
        
        self.stdout.write(f'📧 Contacto de prueba creado con ID: {contacto_prueba.id}')
        
        # Enviar notificación
        self.stdout.write('📤 Enviando notificación...')
        
        try:
            result = send_contact_notification(contacto_prueba)
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS('✅ Notificación enviada exitosamente')
                )
                
                # Mostrar detalles de configuración
                self.stdout.write('\n📋 Configuración utilizada:')
                self.stdout.write(f'   - Servidor SMTP: {config.email_host}:{config.email_port}')
                self.stdout.write(f'   - TLS: {config.email_use_tls}')
                self.stdout.write(f'   - SSL: {config.email_use_ssl}')
                self.stdout.write(f'   - Email remitente: {config.email_from}')
                
                recipient_emails = [
                    email.strip() for email in config.notification_emails.split('\n') 
                    if email.strip() and '@' in email.strip()
                ]
                self.stdout.write(f'   - Destinatarios: {", ".join(recipient_emails)}')
                
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Error enviando la notificación')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
        
        # Opcional: eliminar el contacto de prueba
        self.stdout.write('\n🗑️  ¿Deseas eliminar el contacto de prueba? (y/N): ', ending='')
        response = input()
        if response.lower() == 'y':
            contacto_prueba.delete()
            self.stdout.write(self.style.WARNING('🗑️  Contacto de prueba eliminado'))
        else:
            self.stdout.write('📝 Contacto de prueba conservado para revisión')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS('✅ Prueba completada')
        )