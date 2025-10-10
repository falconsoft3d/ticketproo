from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def is_agent(user):
    """
    Verifica si un usuario pertenece al grupo de Agentes
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Agentes').exists()

def is_regular_user(user):
    """
    Verifica si un usuario pertenece al grupo de Usuarios
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Usuarios').exists()

def is_teacher(user):
    """
    Verifica si un usuario pertenece al grupo de Profesores
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Profesores').exists()

def can_manage_courses(user):
    """
    Verifica si un usuario puede gestionar cursos (Agentes o Profesores)
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name__in=['Agentes', 'Profesores']).exists()

def get_user_role(user):
    """
    Obtiene el rol del usuario
    """
    if not user.is_authenticated:
        return None
    
    if is_agent(user):
        return 'agent'
    elif is_teacher(user):
        return 'teacher'
    elif is_regular_user(user):
        return 'user'
    else:
        return 'unassigned'

def assign_user_to_group(user, group_name):
    """
    Asigna un usuario a un grupo específico
    """
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return True
    except Group.DoesNotExist:
        return False


def send_contact_notification(contacto_web):
    """
    Envía notificación por email cuando se recibe un nuevo contacto web
    """
    try:
        from tickets.models import SystemConfiguration
        
        # Obtener configuración del sistema
        config = SystemConfiguration.get_config()
        
        # Verificar si las notificaciones por email están habilitadas
        if not config.enable_email_notifications:
            logger.info("Notificaciones por email deshabilitadas")
            return False
        
        # Verificar si hay emails de notificación configurados
        if not config.notification_emails.strip():
            logger.warning("No hay emails de notificación configurados")
            return False
        
        # Actualizar configuración de Django con los valores de la base de datos
        if config.email_host:
            settings.EMAIL_HOST = config.email_host
        if config.email_port:
            settings.EMAIL_PORT = config.email_port
        if config.email_host_user:
            settings.EMAIL_HOST_USER = config.email_host_user
        if config.email_host_password:
            settings.EMAIL_HOST_PASSWORD = config.email_host_password
        settings.EMAIL_USE_TLS = config.email_use_tls
        settings.EMAIL_USE_SSL = config.email_use_ssl
        if config.email_from:
            settings.DEFAULT_FROM_EMAIL = config.email_from
        
        # Preparar lista de destinatarios
        recipient_emails = [
            email.strip() for email in config.notification_emails.split('\n') 
            if email.strip() and '@' in email.strip()
        ]
        
        if not recipient_emails:
            logger.warning("No hay emails de notificación válidos configurados")
            return False
        
        # Preparar el asunto
        subject = f"🔔 Nuevo contacto web: {contacto_web.asunto}"
        
        # Renderizar template HTML
        html_message = render_to_string('emails/contact_notification.html', {
            'contacto': contacto_web
        })
        
        # Crear versión de texto plano
        plain_message = strip_tags(html_message)
        
        # Enviar el email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Notificación de contacto web enviada a {len(recipient_emails)} destinatarios")
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enviando notificación por email: {str(e)}")
        return False


def send_landing_page_notification(submission):
    """
    Envía notificación por email cuando se recibe un envío de landing page
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from .models import SystemConfiguration
        
        # Obtener configuración del sistema
        config = SystemConfiguration.get_instance()
        
        if not config or not config.email_notifications_enabled:
            return True
        
        # Preparar datos para el template
        context = {
            'submission': submission,
            'landing_page': submission.landing_page,
        }
        
        # Renderizar contenido del email
        html_message = render_to_string('tickets/email/landing_page_notification.html', context)
        plain_message = strip_tags(html_message)
        
        subject = f'Nueva solicitud de {submission.landing_page.nombre_producto} - {submission.nombre} {submission.apellido}'
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=config.smtp_from_email,
            recipient_list=[config.notification_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enviando notificación de landing page: {str(e)}")
        return False


def send_contact_creation_notification(contact, landing_page):
    """
    Envía notificación por email cuando se crea un contacto desde una landing page
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from .models import SystemConfiguration
        
        # Obtener configuración del sistema
        config = SystemConfiguration.get_instance()
        
        if not config or not config.email_notifications_enabled:
            return True
        
        # Preparar datos para el template
        context = {
            'contact': contact,
            'landing_page': landing_page,
        }
        
        # Renderizar contenido del email
        html_message = render_to_string('tickets/email/contact_creation_notification.html', context)
        plain_message = strip_tags(html_message)
        
        subject = f'Nuevo contacto generado: {contact.name} - {landing_page.nombre_producto}'
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=config.smtp_from_email,
            recipient_list=[config.notification_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enviando notificación de creación de contacto: {str(e)}")
        return False


def send_telegram_notification(landing_page, submission):
    """
    Envía notificación por Telegram cuando se recibe un nuevo envío de formulario
    """
    if not landing_page.telegram_bot_token or not landing_page.telegram_chat_id:
        return False
    
    try:
        import requests
        import json
        
        # Preparar mensaje
        mensaje = f"🎯 *Nuevo Lead desde Landing Page*\n\n"
        mensaje += f"📱 *Producto:* {landing_page.nombre_producto}\n"
        mensaje += f"👤 *Nombre:* {submission.nombre} {submission.apellido}\n"
        mensaje += f"📧 *Email:* {submission.email}\n"
        
        if submission.telefono:
            mensaje += f"📞 *Teléfono:* {submission.telefono}\n"
        
        if submission.empresa:
            mensaje += f"🏢 *Empresa:* {submission.empresa}\n"
            
        if hasattr(submission, 'mensaje') and submission.mensaje:
            mensaje += f"💬 *Mensaje:*\n{submission.mensaje}\n"
        
        mensaje += f"\n📊 *Información de seguimiento:*\n"
        if submission.utm_source:
            mensaje += f"• Source: {submission.utm_source}\n"
        if submission.utm_medium:
            mensaje += f"• Medium: {submission.utm_medium}\n"
        if submission.utm_campaign:
            mensaje += f"• Campaign: {submission.utm_campaign}\n"
        
        mensaje += f"⏰ *Fecha:* {submission.created_at.strftime('%d/%m/%Y %H:%M')}\n"
        mensaje += f"🌐 *IP:* {submission.ip_address or 'N/A'}"
        
        # Enviar mensaje
        url = f"https://api.telegram.org/bot{landing_page.telegram_bot_token}/sendMessage"
        data = {
            'chat_id': landing_page.telegram_chat_id,
            'text': mensaje,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error enviando mensaje de Telegram: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enviando notificación de Telegram: {str(e)}")
        return False
