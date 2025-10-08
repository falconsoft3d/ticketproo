"""
Utilidades para integración con Telegram
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_telegram_message(bot_token, chat_id, message, parse_mode='HTML'):
    """
    Envía un mensaje a un chat de Telegram
    
    Args:
        bot_token (str): Token del bot de Telegram
        chat_id (str): ID del chat o grupo
        message (str): Mensaje a enviar
        parse_mode (str): Modo de parsing ('HTML' o 'Markdown')
    
    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario
    """
    if not bot_token or not chat_id:
        logger.warning("Token del bot o chat_id no configurados para Telegram")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('ok'):
            logger.info(f"Mensaje enviado a Telegram correctamente: {chat_id}")
            return True
        else:
            logger.error(f"Error en respuesta de Telegram: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar mensaje a Telegram: {e}")
        return False

def format_ticket_notification(ticket):
    """
    Formatea un mensaje de notificación para un nuevo ticket
    
    Args:
        ticket: Instancia del modelo Ticket
    
    Returns:
        str: Mensaje formateado para Telegram
    """
    try:
        # Información básica del ticket
        ticket_number = ticket.ticket_number
        title = ticket.title
        creator = ticket.created_by.get_full_name() if ticket.created_by.get_full_name() else ticket.created_by.username
        
        # Información adicional
        priority = ticket.get_priority_display()
        company = ticket.company.name if ticket.company else "Sin empresa"
        category = ticket.category.name if ticket.category else "Sin categoría"
        
        # Emojis según prioridad
        priority_emoji = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🟠',
            'urgent': '🔴',
            'critical': '🚨'
        }.get(ticket.priority, '⚪')
        
        # Construir el mensaje
        message = f"""🎫 <b>Nuevo Ticket Creado</b>
        
📋 <b>Ticket:</b> #{ticket_number}
📝 <b>Título:</b> {title}
👤 <b>Creado por:</b> {creator}
{priority_emoji} <b>Prioridad:</b> {priority}
🏢 <b>Empresa:</b> {company}
📁 <b>Categoría:</b> {category}
📅 <b>Fecha:</b> {ticket.created_at.strftime('%d/%m/%Y %H:%M')}"""

        # Agregar descripción si existe (limitada)
        if ticket.description:
            description = ticket.description[:100]
            if len(ticket.description) > 100:
                description += "..."
            message += f"\n💬 <b>Descripción:</b> {description}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error al formatear notificación de ticket: {e}")
        return f"🎫 Nuevo ticket creado: #{ticket.ticket_number} - {ticket.title} por {ticket.created_by.username}"

def test_telegram_connection(bot_token, chat_id):
    """
    Prueba la conexión con Telegram enviando un mensaje de test
    
    Args:
        bot_token (str): Token del bot
        chat_id (str): ID del chat
    
    Returns:
        dict: Resultado de la prueba con 'success' y 'message'
    """
    test_message = "🤖 <b>Prueba de conexión exitosa</b>\n\nEl bot de TicketProo está configurado correctamente y puede enviar notificaciones a este chat."
    
    if send_telegram_message(bot_token, chat_id, test_message):
        return {
            'success': True,
            'message': 'Conexión exitosa. Se envió un mensaje de prueba al chat de Telegram.'
        }
    else:
        return {
            'success': False, 
            'message': 'Error al enviar mensaje. Verifica el token del bot y el ID del chat.'
        }

def notify_ticket_created(ticket):
    """
    Envía una notificación a Telegram cuando se crea un nuevo ticket
    
    Args:
        ticket: Instancia del modelo Ticket
    
    Returns:
        bool: True si se envió la notificación, False en caso contrario
    """
    try:
        logger.info(f"Iniciando notificación de Telegram para ticket {ticket.ticket_number}")
        
        # Obtener configuración global del sistema
        from .models import SystemConfiguration
        config = SystemConfiguration.get_config()
        
        logger.info(f"Configuración obtenida: telegram_enabled={config.enable_telegram_notifications}")
        
        if not config.enable_telegram_notifications:
            logger.info("Notificaciones de Telegram deshabilitadas")
            return False
        
        if not config.telegram_bot_token or not config.telegram_chat_id:
            logger.warning("Configuración de Telegram incompleta en la configuración del sistema")
            logger.warning(f"Bot token presente: {bool(config.telegram_bot_token)}")
            logger.warning(f"Chat ID presente: {bool(config.telegram_chat_id)}")
            return False
        
        logger.info("Formateando mensaje de notificación")
        message = format_ticket_notification(ticket)
        logger.info(f"Mensaje formateado: {message[:100]}...")
        
        logger.info("Enviando mensaje a Telegram")
        result = send_telegram_message(
            config.telegram_bot_token,
            config.telegram_chat_id,
            message
        )
        
        logger.info(f"Resultado del envío: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error al notificar creación de ticket a Telegram: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False