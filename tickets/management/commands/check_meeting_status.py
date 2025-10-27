"""
Comando para verificar el estado de procesamiento de una reunión
"""
from django.core.management.base import BaseCommand
from tickets.models import VideoMeeting


class Command(BaseCommand):
    help = 'Verifica el estado de procesamiento de una reunión'

    def add_arguments(self, parser):
        parser.add_argument('meeting_id', type=int, help='ID de la reunión')

    def handle(self, *args, **options):
        meeting_id = options['meeting_id']
        
        try:
            meeting = VideoMeeting.objects.get(id=meeting_id)
            
            self.stdout.write(self.style.SUCCESS(f'\n=== Reunión: {meeting.title} ==='))
            self.stdout.write(f'ID: {meeting.id}')
            self.stdout.write(f'Organizador: {meeting.organizer.get_full_name()}')
            self.stdout.write(f'Fecha: {meeting.scheduled_date}')
            self.stdout.write(f'Adjuntos: {meeting.attachments.count()}')
            
            # Estado de transcripción
            status_colors = {
                'pending': self.style.WARNING,
                'processing': self.style.HTTP_INFO,
                'completed': self.style.SUCCESS,
                'failed': self.style.ERROR
            }
            status_color = status_colors.get(meeting.transcription_status, self.style.WARNING)
            self.stdout.write(f'\nEstado de transcripción: {status_color(meeting.transcription_status.upper())}')
            
            if meeting.transcription_text:
                self.stdout.write(f'Longitud transcripción: {len(meeting.transcription_text)} caracteres')
                self.stdout.write(f'Fecha transcripción: {meeting.transcription_date}')
            
            if meeting.ai_summary:
                self.stdout.write(f'\n✅ Tiene resumen de IA')
                summary_preview = meeting.ai_summary[:100] + '...' if len(meeting.ai_summary) > 100 else meeting.ai_summary
                self.stdout.write(f'   Preview: {summary_preview}')
            
            if meeting.key_points:
                self.stdout.write(f'✅ Tiene puntos clave')
            
            if meeting.action_items:
                self.stdout.write(f'✅ Tiene items de acción')
            
            # Listar archivos
            self.stdout.write(f'\n=== Archivos adjuntos ({meeting.attachments.count()}) ===')
            for att in meeting.attachments.all():
                self.stdout.write(f'  • {att.filename} ({att.file_size / 1024 / 1024:.2f} MB)')
                self.stdout.write(f'    Subido: {att.uploaded_at}')
            
        except VideoMeeting.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Reunión con ID {meeting_id} no encontrada'))
