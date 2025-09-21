from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from tickets.models import Ticket

class Command(BaseCommand):
    help = 'Crea los grupos de usuarios: Agentes y Usuarios'

    def handle(self, *args, **options):
        # Crear grupo de Agentes
        agentes_group, created = Group.objects.get_or_create(name='Agentes')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Grupo "Agentes" creado exitosamente')
            )
        else:
            self.stdout.write('Grupo "Agentes" ya existe')

        # Crear grupo de Usuarios
        usuarios_group, created = Group.objects.get_or_create(name='Usuarios')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Grupo "Usuarios" creado exitosamente')
            )
        else:
            self.stdout.write('Grupo "Usuarios" ya existe')

        # Obtener el ContentType para el modelo Ticket
        ticket_content_type = ContentType.objects.get_for_model(Ticket)

        # Permisos para Agentes (todos los permisos sobre tickets)
        agentes_permissions = Permission.objects.filter(
            content_type=ticket_content_type
        )
        agentes_group.permissions.set(agentes_permissions)

        # Permisos básicos para Usuarios (solo pueden crear y ver sus propios tickets)
        usuarios_permissions = Permission.objects.filter(
            content_type=ticket_content_type,
            codename__in=['add_ticket', 'change_ticket', 'view_ticket']
        )
        usuarios_group.permissions.set(usuarios_permissions)

        self.stdout.write(
            self.style.SUCCESS('Permisos configurados exitosamente')
        )
        self.stdout.write(
            self.style.SUCCESS('Configuración de grupos completada')
        )
