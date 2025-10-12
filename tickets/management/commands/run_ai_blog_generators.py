"""
Comando de gestión para ejecutar configuradores de IA de blog automáticamente
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tickets.models import AIBlogConfigurator
from tickets.ai_blog_generator import run_ai_blog_generation


class Command(BaseCommand):
    help = 'Ejecuta los configuradores de IA de blog que estén programados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la ejecución de todos los configuradores activos independientemente de su programación',
        )
        parser.add_argument(
            '--configurator-id',
            type=int,
            help='Ejecuta solo el configurador con el ID especificado',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué configuradores se ejecutarían sin ejecutarlos realmente',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                f'🤖 Iniciando ejecución de configuradores de IA - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )

        # Filtrar configuradores
        configurators = AIBlogConfigurator.objects.filter(is_active=True)
        
        if options['configurator_id']:
            configurators = configurators.filter(id=options['configurator_id'])
            if not configurators.exists():
                self.stdout.write(
                    self.style.ERROR(f'No se encontró configurador con ID {options["configurator_id"]}')
                )
                return

        if not options['force']:
            # Solo configuradores que necesitan ejecutarse
            now = timezone.now()
            # Filtrar configuradores que deben ejecutarse ahora
            ready_configurators = []
            for config in configurators:
                if config.should_run():  # Usar should_run() en lugar de should_run_now()
                    ready_configurators.append(config.id)
            
            configurators = configurators.filter(id__in=ready_configurators)

        if not configurators.exists():
            self.stdout.write(
                self.style.WARNING('No hay configuradores que ejecutar en este momento')
            )
            return

        self.stdout.write(
            f'📋 Encontrados {configurators.count()} configurador(es) para ejecutar'
        )

        total_posts = 0
        successful_runs = 0
        failed_runs = 0

        for configurator in configurators:
            self.stdout.write(f'\n🔄 Procesando: {configurator.name}')
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING(f'  [DRY RUN] Se ejecutaría configurador: {configurator.name}')
                )
                continue

            try:
                # Ejecutar generación (forzar si se especifica)
                result = run_ai_blog_generation(configurator, force=options['force'])
                
                if result['success']:
                    successful_runs += 1
                    total_posts += result['posts_created']
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Éxito: {result["posts_created"]} post(s) generado(s) '
                            f'en {result["execution_time"]}s'
                        )
                    )
                    if result['keywords_used']:
                        self.stdout.write(f'  📝 Keywords usadas: {", ".join(result["keywords_used"])}')
                else:
                    failed_runs += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ Error: {result["error"]} '
                            f'(tiempo: {result["execution_time"]}s)'
                        )
                    )

            except Exception as e:
                failed_runs += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error ejecutando configurador: {str(e)}')
                )

        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'📊 RESUMEN DE EJECUCIÓN:')
        )
        self.stdout.write(f'  • Configuradores procesados: {configurators.count()}')
        self.stdout.write(f'  • Ejecuciones exitosas: {successful_runs}')
        self.stdout.write(f'  • Ejecuciones fallidas: {failed_runs}')
        self.stdout.write(f'  • Total de posts generados: {total_posts}')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('  ⚠️  EJECUCIÓN EN MODO DRY RUN - No se generó contenido real')
            )

        self.stdout.write('='*50)
        self.stdout.write(
            self.style.SUCCESS(f'🏁 Ejecución completada - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        )