"""
Comando para probar la evaluación de IA en landing pages
"""
from django.core.management.base import BaseCommand
from tickets.ai_landing_evaluator import batch_evaluate_submissions, get_evaluation_stats
from tickets.models import LandingPageSubmission


class Command(BaseCommand):
    help = 'Prueba el sistema de evaluación de IA para landing pages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--evaluate',
            action='store_true',
            help='Evaluar envíos pendientes'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estadísticas de evaluación'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Límite de envíos a evaluar (default: 5)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 Sistema de Evaluación IA - Landing Pages')
        )
        self.stdout.write('=' * 50)

        if options['stats']:
            self.show_stats()

        if options['evaluate']:
            self.evaluate_submissions(options['limit'])

        if not options['stats'] and not options['evaluate']:
            self.show_stats()

    def show_stats(self):
        """Muestra estadísticas del sistema"""
        self.stdout.write('\n📊 ESTADÍSTICAS ACTUALES')
        self.stdout.write('-' * 30)
        
        try:
            stats = get_evaluation_stats()
            
            self.stdout.write(f"Total de envíos: {stats.get('total_submissions', 0)}")
            self.stdout.write(f"Evaluados: {stats.get('evaluated_submissions', 0)}")
            self.stdout.write(f"Pendientes: {stats.get('pending_evaluation', 0)}")
            self.stdout.write(f"Porcentaje evaluado: {stats.get('evaluation_percentage', 0):.1f}%")
            
            if stats.get('avg_overall_score'):
                self.stdout.write(f"Puntuación promedio: {stats['avg_overall_score']:.1f}/10")
                self.stdout.write(f"- Empresa: {stats.get('avg_company_score', 0):.1f}/10")
                self.stdout.write(f"- Contacto: {stats.get('avg_contact_score', 0):.1f}/10")
                self.stdout.write(f"- Proyecto: {stats.get('avg_project_score', 0):.1f}/10")
                
                # Distribución por prioridad
                priority_dist = stats.get('priority_distribution', {})
                if priority_dist:
                    self.stdout.write("\nDistribución por prioridad:")
                    for priority, count in priority_dist.items():
                        self.stdout.write(f"- {priority}: {count}")
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error obteniendo estadísticas: {e}")
            )

    def evaluate_submissions(self, limit):
        """Evalúa envíos pendientes"""
        self.stdout.write(f'\n🔍 EVALUANDO {limit} ENVÍOS PENDIENTES')
        self.stdout.write('-' * 40)
        
        # Verificar si hay envíos pendientes
        pending_count = LandingPageSubmission.objects.filter(ai_evaluated=False).count()
        
        if pending_count == 0:
            self.stdout.write(
                self.style.WARNING("No hay envíos pendientes de evaluación")
            )
            return

        self.stdout.write(f"Envíos pendientes disponibles: {pending_count}")
        
        try:
            results = batch_evaluate_submissions(limit=limit)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Procesados: {results['processed']}")
            )
            
            if results['errors'] > 0:
                self.stdout.write(
                    self.style.ERROR(f"❌ Errores: {results['errors']}")
                )
            
            # Mostrar resultados detallados
            self.stdout.write("\nResultados detallados:")
            for result in results['results']:
                if result['status'] == 'success':
                    self.stdout.write(
                        f"✅ ID {result['id']}: {result['score']:.1f}/10 - {result['priority']}"
                    )
                else:
                    self.stdout.write(
                        f"❌ ID {result['id']}: {result['error']}"
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error en evaluación: {e}")
            )

        # Mostrar estadísticas actualizadas
        self.stdout.write('\n📊 ESTADÍSTICAS ACTUALIZADAS')
        self.show_stats()