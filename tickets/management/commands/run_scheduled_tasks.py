from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import ScheduledTask, ScheduledTaskExecution
import time
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ejecuta las tareas programadas que están listas para ejecutarse'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué tareas se ejecutarían sin ejecutarlas realmente',
        )
        parser.add_argument(
            '--task-id',
            type=int,
            help='Ejecuta solo la tarea con el ID especificado',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada de la ejecución',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        task_id = options['task_id']
        verbose = options['verbose']
        
        now = timezone.now()
        
        if task_id:
            # Ejecutar una tarea específica
            try:
                task = ScheduledTask.objects.get(id=task_id, is_active=True)
                tasks_to_execute = [task]
            except ScheduledTask.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tarea con ID {task_id} no encontrada o inactiva')
                )
                return
        else:
            # Buscar todas las tareas que deben ejecutarse
            tasks_to_execute = []
            for task in ScheduledTask.objects.filter(is_active=True):
                if task.should_execute():
                    tasks_to_execute.append(task)

        if not tasks_to_execute:
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS('No hay tareas programadas para ejecutar en este momento.')
                )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Encontradas {len(tasks_to_execute)} tareas para ejecutar:')
        )
        
        for task in tasks_to_execute:
            if verbose:
                next_exec = task.get_next_execution()
                self.stdout.write(f'  - {task.name} (próxima: {next_exec})')
            
            if dry_run:
                self.stdout.write(f'[DRY RUN] Se ejecutaría: {task.name}')
                continue
                
            self.execute_task(task, verbose)

    def execute_task(self, task, verbose=False):
        """Ejecuta una tarea específica"""
        if verbose:
            self.stdout.write(f'Ejecutando tarea: {task.name}')
        
        start_time = time.time()
        
        try:
            # Preparar el entorno de ejecución
            exec_globals = {
                '__builtins__': __builtins__,
                'timezone': timezone,
                'datetime': timezone.datetime,
                'timedelta': timezone.timedelta,
                'logger': logger,
                'print': self.safe_print,
            }
            
            # Importar modelos comunes que podrían necesitarse
            try:
                from django.contrib.auth.models import User
                from tickets.models import Ticket, Contact, Company
                exec_globals.update({
                    'User': User,
                    'Ticket': Ticket,
                    'Contact': Contact,
                    'Company': Company,
                })
            except ImportError:
                pass
            
            exec_locals = {}
            
            # Ejecutar el código de la tarea
            exec(task.code, exec_globals, exec_locals)
            
            execution_time = time.time() - start_time
            result = f"Ejecución exitosa (tiempo: {execution_time:.2f}s)"
            
            # Registrar la ejecución exitosa
            execution = ScheduledTaskExecution.objects.create(
                task=task,
                status='success',
                result=result,
                execution_time=execution_time
            )
            
            # Actualizar la tarea
            task.last_execution = timezone.now()
            task.last_result = result
            task.success_count += 1
            task.save()
            
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {task.name} ejecutada exitosamente en {execution_time:.2f}s')
                )
            
            logger.info(f'Tarea programada ejecutada exitosamente: {task.name} (ID: {task.id})')
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            # Registrar la ejecución con error
            execution = ScheduledTaskExecution.objects.create(
                task=task,
                status='error',
                result=error_message,
                execution_time=execution_time
            )
            
            # Actualizar la tarea
            task.last_execution = timezone.now()
            task.last_result = error_message
            task.error_count += 1
            task.save()
            
            self.stdout.write(
                self.style.ERROR(f'✗ Error ejecutando {task.name}: {error_message}')
            )
            
            logger.error(f'Error ejecutando tarea programada {task.name} (ID: {task.id}): {error_message}')

    def safe_print(self, *args, **kwargs):
        """Función print segura que captura la salida"""
        output = ' '.join(str(arg) for arg in args)
        self.stdout.write(output)
        return output