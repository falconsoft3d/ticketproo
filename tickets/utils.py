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


def get_weather_info(city='Valencia', country_code='ES'):
    """
    Obtiene información del clima usando OpenWeatherMap API
    """
    try:
        import requests
        from django.conf import settings
        
        # API Key de OpenWeatherMap (usa una API gratuita)
        # Para desarrollo, usaremos una API que no requiere clave
        # En producción se debería usar OpenWeatherMap con API key
        
        # API alternativa gratuita que no requiere key
        url = f"https://api.open-meteo.com/v1/forecast"
        
        # Primero obtenemos las coordenadas de la ciudad
        geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            'name': city,
            'count': 1,
            'language': 'es',
            'format': 'json'
        }
        
        geo_response = requests.get(geocoding_url, params=geo_params, timeout=10)
        
        if geo_response.status_code != 200:
            return None
            
        geo_data = geo_response.json()
        
        if not geo_data.get('results'):
            return None
            
        location = geo_data['results'][0]
        lat = location['latitude']
        lon = location['longitude']
        
        # Obtener datos del clima actual
        weather_params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
            'timezone': 'Europe/Madrid',
            'language': 'es'
        }
        
        weather_response = requests.get(url, params=weather_params, timeout=10)
        
        if weather_response.status_code != 200:
            return None
            
        weather_data = weather_response.json()
        current = weather_data.get('current', {})
        
        # Mapear códigos de clima a descripciones e iconos
        weather_codes = {
            0: {'description': 'Despejado', 'icon': 'bi-sun'},
            1: {'description': 'Principalmente despejado', 'icon': 'bi-sun'},
            2: {'description': 'Parcialmente nublado', 'icon': 'bi-cloud-sun'},
            3: {'description': 'Nublado', 'icon': 'bi-clouds'},
            45: {'description': 'Niebla', 'icon': 'bi-cloud-fog'},
            48: {'description': 'Niebla helada', 'icon': 'bi-cloud-fog'},
            51: {'description': 'Llovizna ligera', 'icon': 'bi-cloud-drizzle'},
            53: {'description': 'Llovizna moderada', 'icon': 'bi-cloud-drizzle'},
            55: {'description': 'Llovizna intensa', 'icon': 'bi-cloud-drizzle'},
            61: {'description': 'Lluvia ligera', 'icon': 'bi-cloud-rain'},
            63: {'description': 'Lluvia moderada', 'icon': 'bi-cloud-rain'},
            65: {'description': 'Lluvia intensa', 'icon': 'bi-cloud-rain-heavy'},
            71: {'description': 'Nieve ligera', 'icon': 'bi-cloud-snow'},
            73: {'description': 'Nieve moderada', 'icon': 'bi-cloud-snow'},
            75: {'description': 'Nieve intensa', 'icon': 'bi-cloud-snow'},
            80: {'description': 'Chubascos ligeros', 'icon': 'bi-cloud-rain'},
            81: {'description': 'Chubascos moderados', 'icon': 'bi-cloud-rain'},
            82: {'description': 'Chubascos intensos', 'icon': 'bi-cloud-rain-heavy'},
            95: {'description': 'Tormenta', 'icon': 'bi-cloud-lightning'},
            96: {'description': 'Tormenta con granizo', 'icon': 'bi-cloud-lightning-rain'},
            99: {'description': 'Tormenta intensa', 'icon': 'bi-cloud-lightning-rain'},
        }
        
        weather_code = current.get('weather_code', 0)
        weather_info = weather_codes.get(weather_code, {'description': 'Desconocido', 'icon': 'bi-question'})
        
        return {
            'city': city,
            'country': location.get('country', country_code),
            'temperature': round(current.get('temperature_2m', 0)),
            'humidity': current.get('relative_humidity_2m', 0),
            'wind_speed': current.get('wind_speed_10m', 0),
            'description': weather_info['description'],
            'icon': weather_info['icon'],
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo información del clima: {str(e)}")
        return {
            'city': city,
            'temperature': '--',
            'description': 'No disponible',
            'icon': 'bi-exclamation-triangle',
            'success': False,
            'error': str(e)
        }


def get_country_from_ip(ip_address):
    """
    Obtiene el país desde una dirección IP usando la API gratuita de ip-api.com
    Retorna un diccionario con country, country_code, city, etc.
    """
    import requests
    
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        return {
            'country': 'Local',
            'country_code': 'LO',
            'city': 'Local',
            'success': False
        }
    
    try:
        # API gratuita sin necesidad de API key
        # Límite: 45 peticiones por minuto
        url = f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,city,lat,lon,timezone"
        response = requests.get(url, timeout=3)
        
        if response.status_code != 200:
            return {
                'country': 'Desconocido',
                'country_code': 'XX',
                'city': '',
                'success': False
            }
        
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'country': data.get('country', 'Desconocido'),
                'country_code': data.get('countryCode', 'XX'),
                'city': data.get('city', ''),
                'latitude': data.get('lat', 0),
                'longitude': data.get('lon', 0),
                'timezone': data.get('timezone', ''),
                'success': True
            }
        else:
            return {
                'country': 'Desconocido',
                'country_code': 'XX',
                'city': '',
                'success': False
            }
    
    except Exception as e:
        logger.error(f"Error obteniendo país desde IP {ip_address}: {str(e)}")
        return {
            'country': 'Error',
            'country_code': 'XX',
            'city': '',
            'success': False,
            'error': str(e)
        }


def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente considerando proxies y load balancers
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # La primera IP es la del cliente original
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
