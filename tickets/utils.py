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
        
        # Preparar el asunto y mensaje
        subject = f"🔔 Nuevo contacto web: {contacto_web.asunto}"
        
        # Crear mensaje HTML
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">📧 Nuevo Contacto Web</h1>
                <p style="margin: 5px 0 0 0;">TicketProo - Sistema de Gestión</p>
            </div>
            
            <div style="padding: 20px; border: 1px solid #e0e0e0;">
                <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    Detalles del Contacto
                </h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #666; width: 120px;">
                            <strong>👤 Nombre:</strong>
                        </td>
                        <td style="padding: 8px 0;">{contacto_web.nombre}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px 0; font-weight: bold; color: #666;">
                            <strong>📧 Email:</strong>
                        </td>
                        <td style="padding: 8px 0;">
                            <a href="mailto:{contacto_web.email}" style="color: #667eea;">
                                {contacto_web.email}
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #666;">
                            <strong>📱 Teléfono:</strong>
                        </td>
                        <td style="padding: 8px 0;">{contacto_web.telefono or 'No proporcionado'}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px 0; font-weight: bold; color: #666;">
                            <strong>🏢 Empresa:</strong>
                        </td>
                        <td style="padding: 8px 0;">{contacto_web.empresa or 'No proporcionada'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #666;">
                            <strong>📝 Asunto:</strong>
                        </td>
                        <td style="padding: 8px 0;"><strong>{contacto_web.asunto}</strong></td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px 0; font-weight: bold; color: #666; vertical-align: top;">
                            <strong>💬 Mensaje:</strong>
                        </td>
                        <td style="padding: 8px 0;">
                            <div style="background: white; padding: 10px; border-left: 3px solid #667eea; margin: 5px 0;">
                                {contacto_web.mensaje.replace(chr(10), '<br>')}
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #666;">
                            <strong>🕒 Fecha:</strong>
                        </td>
                        <td style="padding: 8px 0;">{contacto_web.fecha_creacion.strftime('%d/%m/%Y %H:%M')}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px 0; font-weight: bold; color: #666;">
                            <strong>🌐 IP:</strong>
                        </td>
                        <td style="padding: 8px 0;">{contacto_web.ip_address or 'No disponible'}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; text-align: center;">
                    <a href="http://localhost:8000/admin/tickets/contactoweb/{contacto_web.id}/change/" 
                       style="background: #667eea; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        🔗 Ver en Panel de Administración
                    </a>
                </div>
            </div>
            
            <div style="background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p style="margin: 0;">Este email fue enviado automáticamente por TicketProo</p>
                <p style="margin: 5px 0 0 0;">Para desactivar estas notificaciones, modifica la configuración del sistema</p>
            </div>
        </div>
        """
        
        # Crear versión de texto plano
        plain_message = f"""
Nuevo Contacto Web - TicketProo

Detalles del Contacto:
- Nombre: {contacto_web.nombre}
- Email: {contacto_web.email}
- Teléfono: {contacto_web.telefono or 'No proporcionado'}
- Empresa: {contacto_web.empresa or 'No proporcionada'}
- Asunto: {contacto_web.asunto}
- Fecha: {contacto_web.fecha_creacion.strftime('%d/%m/%Y %H:%M')}
- IP: {contacto_web.ip_address or 'No disponible'}

Mensaje:
{contacto_web.mensaje}

---
Ver en panel de administración: http://localhost:8000/admin/tickets/contactoweb/{contacto_web.id}/change/

Este email fue enviado automáticamente por TicketProo.
        """
        
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
        logger.error(f"Error enviando notificación de contacto web: {str(e)}")
        return False
