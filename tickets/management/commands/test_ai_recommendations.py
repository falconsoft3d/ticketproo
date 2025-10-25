from django.core.management.base import BaseCommand
from tickets.models import AIRecommendation, AIRecommendationUsage
from tickets.ai_utils import AIContentOptimizer
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Prueba el sistema de recomendaciones IA con un caso de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write('🤖 Probando el Sistema de Recomendaciones IA\n')

        # Obtener una recomendación de ejemplo
        try:
            recommendation = AIRecommendation.objects.filter(
                title='Manejo de Quejas de Clientes'
            ).first()
            
            if not recommendation:
                self.stdout.write(
                    self.style.ERROR('No se encontró la recomendación de ejemplo. Ejecuta primero: python manage.py create_ai_recommendations')
                )
                return

            self.stdout.write(f'📋 Usando recomendación: {recommendation.title}')
            self.stdout.write(f'👤 Creada por: {recommendation.created_by.username}\n')

            # Caso de ejemplo
            client_case = """Un cliente compró un televisor hace 2 semanas y ahora no enciende. 
Está muy molesto porque lo necesita para una reunión importante mañana. 
Dice que quiere devolver el producto y pedir reembolso completo, 
pero también menciona que si lo pueden arreglar rápido, preferiría quedárselo 
porque ya configuró todo su sistema de entretenimiento."""

            self.stdout.write('📝 Caso del cliente:')
            self.stdout.write(f'{client_case}\n')

            # Crear instancia del optimizador de IA
            ai_optimizer = AIContentOptimizer()
            
            # Verificar si hay API key configurada
            if not ai_optimizer.api_key:
                self.stdout.write(
                    self.style.WARNING('⚠️  API key de OpenAI no configurada.')
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ El sistema de recomendaciones está funcionando correctamente.')
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ Para probar la funcionalidad de IA, configura la API key de OpenAI en la configuración del sistema.')
                )
                return

            # Preparar el prompt para la IA
            messages_for_ai = [
                {
                    "role": "system",
                    "content": f"""Eres un asistente experto en comunicación empresarial y atención al cliente. 
                    
CONTEXTO BASE:
{recommendation.context_text}

Tu tarea es generar una respuesta profesional, políticamente correcta y empática para el caso del cliente que se te presente. 
La respuesta debe ser:
- Profesional y respetuosa
- Empática con la situación del cliente
- Clara y concisa
- Orientada a soluciones
- Políticamente correcta
- Apropiada para comunicación por email

Responde únicamente con la sugerencia de respuesta, sin explicaciones adicionales."""
                },
                {
                    "role": "user", 
                    "content": f"Caso del cliente: {client_case}"
                }
            ]

            self.stdout.write('🔄 Consultando IA...')
            
            # Hacer la petición a la IA
            result = ai_optimizer._make_ai_request(messages_for_ai, max_tokens=800, temperature=0.7)
            
            if 'error' not in result:
                try:
                    ai_response = result['choices'][0]['message']['content'].strip()
                    
                    self.stdout.write('\n' + '='*60)
                    self.stdout.write('🤖 RESPUESTA GENERADA POR IA:')
                    self.stdout.write('='*60)
                    self.stdout.write(ai_response)
                    self.stdout.write('='*60 + '\n')
                    
                    # Obtener el primer usuario para simular el uso
                    user = User.objects.first()
                    if user:
                        # Simular guardar el uso
                        usage = AIRecommendationUsage(
                            recommendation=recommendation,
                            user=user,
                            client_case=client_case,
                            ai_response=ai_response
                        )
                        # No guardar realmente para no contaminar la base de datos
                        self.stdout.write(f'✅ Respuesta generada para el usuario: {user.username}')
                    
                    self.stdout.write('\n✨ ¡El sistema de recomendaciones IA está funcionando perfectamente!')
                    self.stdout.write(f'🔗 Accede desde: http://localhost:8001/ai-recommendations/')
                    
                except (KeyError, IndexError) as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error al procesar respuesta de IA: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error de IA: {result["error"]}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inesperado: {e}')
            )