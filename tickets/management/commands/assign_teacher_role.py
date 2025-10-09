from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Asigna el rol de Profesor a un usuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario al que asignar el rol de Profesor')
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Quitar el rol de Profesor del usuario',
        )

    def handle(self, *args, **options):
        username = options['username']
        remove = options['remove']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario "{username}" no encontrado')
            )
            return

        try:
            teacher_group = Group.objects.get(name='Profesores')
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Grupo "Profesores" no existe. Ejecuta las migraciones primero.')
            )
            return

        if remove:
            if user.groups.filter(name='Profesores').exists():
                user.groups.remove(teacher_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Rol de Profesor removido del usuario "{username}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'El usuario "{username}" no tiene el rol de Profesor')
                )
        else:
            if user.groups.filter(name='Profesores').exists():
                self.stdout.write(
                    self.style.WARNING(f'El usuario "{username}" ya tiene el rol de Profesor')
                )
            else:
                user.groups.add(teacher_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Rol de Profesor asignado al usuario "{username}"')
                )

        # Mostrar información del usuario
        self.stdout.write(f'\nInformación del usuario:')
        self.stdout.write(f'Nombre: {user.first_name} {user.last_name}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Grupos: {", ".join([g.name for g in user.groups.all()])}')