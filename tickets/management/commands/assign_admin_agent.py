from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Asigna el usuario admin al grupo de Agentes'

    def handle(self, *args, **options):
        try:
            # Buscar el usuario admin
            admin_user = User.objects.get(username='admin')
            
            # Buscar el grupo de Agentes
            agentes_group = Group.objects.get(name='Agentes')
            
            # Asignar el usuario al grupo
            admin_user.groups.add(agentes_group)
            
            self.stdout.write(
                self.style.SUCCESS(f'Usuario "{admin_user.username}" asignado al grupo "Agentes" exitosamente')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuario "admin" no encontrado')
            )
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Grupo "Agentes" no encontrado. Ejecuta primero: python manage.py setup_groups')
            )
