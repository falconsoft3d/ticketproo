"""
Tareas asíncronas para el procesamiento de reuniones de video usando threading
(sin dependencias externas como Celery)
"""
import threading
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


def process_meeting_recordings_async(meeting_id, file_paths):
    """
    Inicia el procesamiento de archivos de reunión en un thread separado
    
    Args:
        meeting_id: ID de la reunión
        file_paths: Lista de rutas de archivos guardados
    """
    thread = threading.Thread(
        target=_process_meeting_recordings,
        args=(meeting_id, file_paths),
        daemon=True
    )
    thread.start()
    logger.info(f"Iniciado procesamiento asíncrono de reunión {meeting_id} con {len(file_paths)} archivos")


def _process_meeting_recordings(meeting_id, file_paths):
    """
    Procesa múltiples archivos de grabación de reunión en segundo plano:
    1. Transcribe cada archivo con IA
    2. Genera resumen consolidado
    3. Extrae puntos clave y acciones
    
    Args:
        meeting_id: ID de la reunión
        file_paths: Lista de rutas de archivos guardados
    """
    from tickets.models import VideoMeeting
    from tickets.ai_utils import transcribe_audio_file, generate_meeting_summary
    from django.utils import timezone
    import sys
    import traceback
    
    logger.info(f"=== INICIO DEL THREAD: Procesando reunión {meeting_id} ===")
    logger.info(f"Thread ID: {threading.current_thread().ident}")
    logger.info(f"Archivos a procesar: {file_paths}")
    
    try:
        logger.info(f"Buscando reunión {meeting_id} en la base de datos...")
        meeting = VideoMeeting.objects.get(id=meeting_id)
        logger.info(f"Reunión encontrada: {meeting.title}, estado actual: {meeting.transcription_status}")
        
        logger.info(f"Actualizando estado a 'processing'...")
        meeting.transcription_status = 'processing'
        meeting.save()
        logger.info(f"Estado actualizado correctamente")
        
        logger.info(f"Iniciando procesamiento de reunión {meeting_id} con {len(file_paths)} archivos")
        
        all_transcriptions = []
        processed_files = 0
        
        # Procesar cada archivo
        for file_path in file_paths:
            try:
                logger.info(f"Procesando archivo: {file_path}")
                
                # Obtener ruta completa del archivo
                full_path = default_storage.path(file_path)
                
                # Transcribir archivo
                transcription = transcribe_audio_file(full_path)
                
                if transcription:
                    all_transcriptions.append({
                        'file': file_path,
                        'text': transcription
                    })
                    processed_files += 1
                    
                    logger.info(f"Archivo procesado exitosamente: {file_path}")
                else:
                    logger.warning(f"No se pudo transcribir: {file_path}")
                    
            except Exception as e:
                logger.error(f"Error procesando archivo {file_path}: {str(e)}")
                continue
        
        if not all_transcriptions:
            meeting.transcription_status = 'failed'
            meeting.save()
            logger.error(f"No se pudo transcribir ningún archivo para la reunión {meeting_id}")
            return
        
        # Consolidar todas las transcripciones
        consolidated_text = "\n\n=== ARCHIVO: {} ===\n\n".join([
            f"{t['file']}\n{t['text']}" for t in all_transcriptions
        ])
        
        # Guardar transcripción consolidada
        meeting.transcription_text = consolidated_text
        meeting.transcription_date = timezone.now()
        
        # Generar resumen con IA
        try:
            summary_data = generate_meeting_summary(consolidated_text)
            
            if summary_data:
                meeting.ai_summary = summary_data.get('summary', '')
                meeting.key_points = summary_data.get('key_points', '')
                meeting.action_items = summary_data.get('action_items', '')
                
                logger.info(f"Resumen de IA generado para reunión {meeting_id}")
        except Exception as e:
            logger.error(f"Error generando resumen de IA: {str(e)}")
        
        meeting.transcription_status = 'completed'
        meeting.save()
        
        logger.info(
            f"Procesamiento completado para reunión {meeting_id}. "
            f"Archivos procesados: {processed_files}/{len(file_paths)}"
        )
        
        # Enviar notificación al organizador
        try:
            from tickets.utils import send_notification
            send_notification(
                user=meeting.organizer,
                title=f'Reunión procesada: {meeting.title}',
                message=f'Se procesaron {processed_files} archivos y se generó el análisis con IA.',
                notification_type='meeting_processed'
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar notificación: {str(e)}")
        
    except VideoMeeting.DoesNotExist:
        logger.error(f"=== ERROR: Reunión {meeting_id} no encontrada ===")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        logger.error(f"=== ERROR GENERAL procesando reunión {meeting_id} ===")
        logger.error(f"Tipo de error: {type(e).__name__}")
        logger.error(f"Mensaje: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            meeting = VideoMeeting.objects.get(id=meeting_id)
            meeting.transcription_status = 'failed'
            meeting.save()
            logger.error(f"Estado actualizado a 'failed'")
        except Exception as e2:
            logger.error(f"No se pudo actualizar estado a 'failed': {str(e2)}")
    
    logger.info(f"=== FIN DEL THREAD: Reunión {meeting_id} ===")


def transcribe_single_file_async(meeting_id, file_path):
    """
    Inicia la transcripción de un solo archivo en un thread separado
    
    Args:
        meeting_id: ID de la reunión
        file_path: Ruta del archivo a transcribir
    """
    thread = threading.Thread(
        target=_transcribe_single_file,
        args=(meeting_id, file_path),
        daemon=True
    )
    thread.start()
    logger.info(f"Iniciada transcripción asíncrona para reunión {meeting_id}")


def _transcribe_single_file(meeting_id, file_path):
    """
    Transcribe un solo archivo de reunión en segundo plano
    
    Args:
        meeting_id: ID de la reunión
        file_path: Ruta del archivo a transcribir
    """
    from tickets.models import VideoMeeting
    from tickets.ai_utils import transcribe_audio_file
    from django.utils import timezone
    
    try:
        meeting = VideoMeeting.objects.get(id=meeting_id)
        meeting.transcription_status = 'processing'
        meeting.save()
        
        # Obtener ruta completa
        full_path = default_storage.path(file_path)
        
        # Transcribir
        transcription = transcribe_audio_file(full_path)
        
        if transcription:
            meeting.transcription_text = transcription
            meeting.transcription_date = timezone.now()
            meeting.transcription_status = 'completed'
            meeting.save()
            
            logger.info(f"Transcripción completada para reunión {meeting_id}")
        else:
            meeting.transcription_status = 'failed'
            meeting.save()
            logger.error(f"Fallo en transcripción para reunión {meeting_id}")
            
    except Exception as e:
        logger.error(f"Error en transcripción: {str(e)}")
        try:
            meeting = VideoMeeting.objects.get(id=meeting_id)
            meeting.transcription_status = 'failed'
            meeting.save()
        except:
            pass
