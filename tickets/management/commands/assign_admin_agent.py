from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Asigna un usuario al grupo de Agentes'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='?',
            default='admin',
            help='Nombre de usuario a asignar al grupo Agentes (default: admin)'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            # Buscar el usuario
            user = User.objects.get(username=username)
            
            # Buscar el grupo de Agentes
            agentes_group = Group.objects.get(name='Agentes')
            
            # Asignar el usuario al grupo
            user.groups.add(agentes_group)
            
            self.stdout.write(
                self.style.SUCCESS(f'Usuario "{user.username}" asignado al grupo "Agentes" exitosamente')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario "{username}" no encontrado')
            )
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Grupo "Agentes" no encontrado. Ejecuta primero: python manage.py setup_groups')
            )
