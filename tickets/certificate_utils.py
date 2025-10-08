"""
Utilidades para generar certificados de exámenes
"""
import io
import qrcode
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, blue, darkblue
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image


def generate_certificate_pdf(attempt):
    """
    Genera un certificado en PDF para un intento de examen aprobado
    """
    if not attempt.passed:
        return None
    
    # Asegurar que el token existe
    if not attempt.certificate_token:
        attempt.generate_certificate_token()
    
    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear el PDF
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Colores personalizados
    primary_color = Color(0.2, 0.3, 0.7)  # Azul
    secondary_color = Color(0.8, 0.8, 0.8)  # Gris claro
    accent_color = Color(0.1, 0.6, 0.3)  # Verde
    
    # Dibujar borde decorativo
    p.setStrokeColor(primary_color)
    p.setLineWidth(3)
    p.rect(40, 40, width-80, height-80)
    
    p.setStrokeColor(secondary_color)
    p.setLineWidth(1)
    p.rect(50, 50, width-100, height-100)
    
    # Título principal
    p.setFont("Helvetica-Bold", 32)
    p.setFillColor(primary_color)
    title_text = "CERTIFICADO DE LOGRO"
    title_width = p.stringWidth(title_text, "Helvetica-Bold", 32)
    p.drawString((width - title_width) / 2, height-120, title_text)
    
    # Línea decorativa
    p.setStrokeColor(accent_color)
    p.setLineWidth(2)
    p.line(width/2-150, height-140, width/2+150, height-140)
    
    # Texto "Se certifica que"
    p.setFont("Helvetica", 16)
    p.setFillColor(black)
    text1 = "Se certifica que"
    text1_width = p.stringWidth(text1, "Helvetica", 16)
    p.drawString((width - text1_width) / 2, height-180, text1)
    
    # Nombre del participante
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(primary_color)
    name_text = attempt.participant_name.upper()
    name_width = p.stringWidth(name_text, "Helvetica-Bold", 24)
    p.drawString((width - name_width) / 2, height-220, name_text)
    
    # Línea bajo el nombre
    p.setStrokeColor(secondary_color)
    p.setLineWidth(1)
    p.line(width/2-200, height-235, width/2+200, height-235)
    
    # Texto de logro
    p.setFont("Helvetica", 14)
    p.setFillColor(black)
    text_y = height-270
    achievement_text = "ha completado satisfactoriamente el examen"
    achievement_width = p.stringWidth(achievement_text, "Helvetica", 14)
    p.drawString((width - achievement_width) / 2, text_y, achievement_text)
    
    # Nombre del examen
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(primary_color)
    text_y -= 40
    # Dividir el título si es muy largo
    exam_title = attempt.exam.title
    if len(exam_title) > 50:
        words = exam_title.split()
        line1 = f'"{" ".join(words[:len(words)//2])}"'
        line2 = f'"{" ".join(words[len(words)//2:])}"'
        line1_width = p.stringWidth(line1, "Helvetica-Bold", 18)
        line2_width = p.stringWidth(line2, "Helvetica-Bold", 18)
        p.drawString((width - line1_width) / 2, text_y, line1)
        text_y -= 25
        p.drawString((width - line2_width) / 2, text_y, line2)
    else:
        exam_text = f'"{exam_title}"'
        exam_width = p.stringWidth(exam_text, "Helvetica-Bold", 18)
        p.drawString((width - exam_width) / 2, text_y, exam_text)
    
    # Información del rendimiento
    text_y -= 60
    p.setFont("Helvetica", 12)
    p.setFillColor(black)
    score_text = f"con una puntuación de {attempt.score:.1f}%"
    score_width = p.stringWidth(score_text, "Helvetica", 12)
    p.drawString((width - score_width) / 2, text_y, score_text)
    
    text_y -= 20
    details_text = f"({attempt.correct_answers} de {attempt.total_questions} preguntas correctas)"
    details_width = p.stringWidth(details_text, "Helvetica", 12)
    p.drawString((width - details_width) / 2, text_y, details_text)
    
    # Fecha
    text_y -= 40
    p.setFont("Helvetica-Bold", 12)
    fecha_texto = f"Otorgado el {attempt.completed_at.strftime('%d de %B de %Y')}"
    fecha_width = p.stringWidth(fecha_texto, "Helvetica-Bold", 12)
    p.drawString((width - fecha_width) / 2, text_y, fecha_texto)
    
    # Generar QR con URL de verificación
    qr_data = f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/certificate/verify/{attempt.certificate_token}/"
    
    # Crear QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Convertir QR a imagen
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar QR temporalmente
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Insertar QR en el PDF
    qr_size = 80
    qr_x = width - 150
    qr_y = 60
    
    # Crear imagen temporal para reportlab
    from reportlab.lib.utils import ImageReader
    qr_image = ImageReader(qr_buffer)
    p.drawImage(qr_image, qr_x, qr_y, qr_size, qr_size)
    
    # Texto junto al QR
    p.setFont("Helvetica", 8)
    p.setFillColor(black)
    p.drawString(qr_x, qr_y-15, "Escanea para verificar")
    p.drawString(qr_x, qr_y-25, "la autenticidad")
    
    # Información del certificado
    p.setFont("Helvetica", 8)
    p.drawString(60, 80, f"Certificado ID: {attempt.certificate_token}")
    p.drawString(60, 70, f"Generado: {attempt.certificate_generated_at.strftime('%d/%m/%Y %H:%M')}")
    
    # Información de la organización (lado izquierdo inferior)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, 120, "TicketPro Sistema de Capacitación")
    p.setFont("Helvetica", 8)
    p.drawString(60, 110, "Sistema de Gestión de Exámenes")
    p.drawString(60, 100, "Certificado válido y verificable")
    
    # Firma digital (simulada)
    p.setStrokeColor(primary_color)
    p.setLineWidth(1)
    signature_y = 180
    p.line(width/2+50, signature_y, width/2+200, signature_y)
    p.setFont("Helvetica", 10)
    p.drawString(width/2+50, signature_y-15, "Firma Digital Autorizada")
    p.setFont("Helvetica", 8)
    p.drawString(width/2+50, signature_y-25, "Sistema TicketPro")
    
    # Finalizar PDF
    p.showPage()
    p.save()
    
    # Obtener el contenido del buffer
    buffer.seek(0)
    return buffer


def create_certificate_response(attempt):
    """
    Crea una respuesta HTTP con el certificado PDF
    """
    pdf_buffer = generate_certificate_pdf(attempt)
    if not pdf_buffer:
        return None
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    filename = f"certificado_{attempt.participant_name.replace(' ', '_')}_{attempt.exam.title.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def verify_certificate_data(token):
    """
    Verifica un certificado usando su token
    """
    from .models import ExamAttempt
    
    try:
        attempt = ExamAttempt.objects.get(certificate_token=token, passed=True)
        return {
            'valid': True,
            'participant_name': attempt.participant_name,
            'participant_email': attempt.participant_email,
            'exam_title': attempt.exam.title,
            'score': attempt.score,
            'completed_at': attempt.completed_at,
            'certificate_generated_at': attempt.certificate_generated_at,
            'correct_answers': attempt.correct_answers,
            'total_questions': attempt.total_questions,
        }
    except ExamAttempt.DoesNotExist:
        return {
            'valid': False,
            'error': 'Certificado no encontrado o no válido'
        }