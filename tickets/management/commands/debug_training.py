from django.core.management.base import BaseCommand
from tickets.models import TrainingPlan, EmployeeLinkProgress
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Debug training progress'

    def handle(self, *args, **options):
        # Obtener todos los planes
        plans = TrainingPlan.objects.all()
        user = User.objects.first()

        if user:
            self.stdout.write(f'Usuario: {user.username}\n')
            
            for plan in plans:
                self.stdout.write(f'=== Plan: {plan.title} ===')
                self.stdout.write(f'Total links: {plan.get_total_links()}')
                
                # Progreso calculado por el método
                progress = plan.get_progress_for_user(user)
                self.stdout.write(f'Progreso calculado: {progress}%')
                
                # Verificar links completados directamente
                completed = EmployeeLinkProgress.objects.filter(employee=user, link__plan=plan).count()
                self.stdout.write(f'Links completados en BD: {completed}')
                
                # Calcular progreso manualmente
                if plan.get_total_links() > 0:
                    manual_progress = (completed / plan.get_total_links()) * 100
                    self.stdout.write(f'Progreso manual: {manual_progress}%')
                
                # Listar todos los links del plan
                self.stdout.write('Links del plan:')
                for link in plan.links.all():
                    is_completed = EmployeeLinkProgress.objects.filter(employee=user, link=link).exists()
                    status = "Completado" if is_completed else "Pendiente"
                    self.stdout.write(f'  - {link.title}: {status}')
                
                self.stdout.write('')  # Línea en blanco
        else:
            self.stdout.write('No hay usuarios en la BD')