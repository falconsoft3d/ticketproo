from django.core.management.base import BaseCommand
from tickets.models import Task


class Command(BaseCommand):
    help = 'Genera números de tarea para todas las tareas que no tengan'

    def handle(self, *args, **options):
        tasks = Task.objects.filter(task_number__isnull=True).order_by('id')
        count = 0
        
        for task in tasks:
            task.save()  # El método save() generará automáticamente el task_number
            count += 1
            self.stdout.write(f'Tarea {task.id}: {task.task_number}')
        
        self.stdout.write(self.style.SUCCESS(f'Se generaron números para {count} tareas'))
