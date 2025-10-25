from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import AIRecommendation


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de recomendaciones IA'

    def handle(self, *args, **options):
        # Obtener un usuario para asignar como creador
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()
            
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios en el sistema. Crea un usuario primero.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al obtener usuario: {e}')
            )
            return

        # Crear recomendaciones de ejemplo
        recommendations = [
            {
                'title': 'Manejo de Quejas de Clientes',
                'context_text': '''Nuestra empresa prioriza la satisfacción del cliente por encima de todo. 
Las respuestas deben ser:
- Empáticas y comprensivas
- Profesionales pero cercanas
- Orientadas a soluciones concretas
- Incluir disculpas cuando sea apropiado

Políticas importantes:
- Siempre ofrecer al menos 2 alternativas de solución
- No culpar al cliente bajo ninguna circunstancia
- Mantener un tono respetuoso y constructivo
- Ofrecer compensaciones cuando sea justificado
- Finalizar con seguimiento o próximos pasos

Evitar:
- Lenguaje técnico complicado
- Respuestas defensivas
- Promesas que no podemos cumplir'''
            },
            {
                'title': 'Respuestas para Solicitudes de Reembolso',
                'context_text': '''Para solicitudes de reembolso, seguir estos principios:

Tono: Profesional, empático y orientado a soluciones
Política de reembolsos: 30 días para productos físicos, 14 días para servicios digitales

Estructura de respuesta:
1. Agradecer al cliente por contactarnos
2. Reconocer su preocupación
3. Explicar claramente las opciones disponibles
4. Proporcionar pasos específicos a seguir
5. Ofrecer asistencia adicional

Alternativas a ofrecer:
- Cambio por otro producto
- Crédito en tienda
- Reembolso parcial o completo según política
- Descuento en próxima compra

Mantener un enfoque colaborativo y mostrar que valoramos su negocio.'''
            },
            {
                'title': 'Comunicación con Clientes VIP',
                'context_text': '''Para clientes VIP y de alto valor:

Tono: Altamente personalizado, premium y deferente
Tratamiento: Usar nombres propios, reconocer su estatus especial

Elementos clave:
- Reconocer explícitamente su importancia para la empresa
- Ofrecer soluciones premium o escaladas
- Proporcionar contacto directo con gerencia si es necesario
- Tiempos de respuesta prioritarios
- Comunicación proactiva sobre estado de resolución

Privilegios especiales:
- Acceso a soporte premium 24/7
- Descuentos exclusivos
- Invitaciones a eventos especiales
- Contacto directo con account manager

Siempre exceder expectativas y demostrar que valoramos su lealtad.'''
            },
            {
                'title': 'Respuestas para Problemas Técnicos',
                'context_text': '''Para consultas técnicas y problemas de funcionamiento:

Enfoque: Educativo, paciente y paso a paso
Comunicación: Clara, sin jerga técnica, con ejemplos prácticos

Estructura recomendada:
1. Reconocer el problema específico
2. Tranquilizar que tiene solución
3. Proporcionar pasos claros y numerados
4. Ofrecer múltiples canales de soporte
5. Dar seguimiento para confirmar resolución

Herramientas a mencionar:
- Tutoriales en video disponibles
- Documentación paso a paso
- Soporte por chat en vivo
- Sesiones de pantalla compartida si es necesario

Siempre validar el nivel técnico del cliente y ajustar la explicación accordingly.
Ofrecer alternativas si el problema es complejo.'''
            }
        ]

        created_count = 0
        for rec_data in recommendations:
            recommendation, created = AIRecommendation.objects.get_or_create(
                title=rec_data['title'],
                defaults={
                    'context_text': rec_data['context_text'],
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creada recomendación: {recommendation.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Ya existe: {recommendation.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Proceso completado! Se crearon {created_count} nuevas recomendaciones.')
        )
        self.stdout.write(
            self.style.SUCCESS('Puedes acceder a ellas desde el menú: Empleado > Recomendaciones IA')
        )