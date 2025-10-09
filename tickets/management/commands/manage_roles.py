from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from tickets.utils import is_agent, is_teacher, is_regular_user, get_user_role


class Command(BaseCommand):
    help = 'Gestiona roles de usuarios del sistema'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Acciones disponibles')
        
        # Comando para listar usuarios por rol
        list_parser = subparsers.add_parser('list', help='Lista usuarios por rol')
        list_parser.add_argument(
            '--role',
            choices=['agentes', 'profesores', 'usuarios', 'todos'],
            default='todos',
            help='Rol a filtrar'
        )
        
        # Comando para asignar rol
        assign_parser = subparsers.add_parser('assign', help='Asigna rol a usuario')
        assign_parser.add_argument('username', help='Nombre de usuario')
        assign_parser.add_argument(
            'role',
            choices=['agente', 'profesor', 'usuario'],
            help='Rol a asignar'
        )
        
        # Comando para mostrar información de usuario
        info_parser = subparsers.add_parser('info', help='Muestra información de usuario')
        info_parser.add_argument('username', help='Nombre de usuario')
        
        # Comando para crear grupos si no existen
        setup_parser = subparsers.add_parser('setup', help='Crea grupos necesarios')

    def handle(self, *args, **options):
        action = options.get('action')
        
        if action == 'list':
            self.list_users(options.get('role'))
        elif action == 'assign':
            self.assign_role(options.get('username'), options.get('role'))
        elif action == 'info':
            self.show_user_info(options.get('username'))
        elif action == 'setup':
            self.setup_groups()
        else:
            self.stdout.write(self.style.ERROR('Acción no especificada. Usa --help para ver opciones.'))

    def list_users(self, role_filter):
        """Lista usuarios por rol"""
        self.stdout.write(self.style.SUCCESS(f'\n=== USUARIOS POR ROL ===\n'))
        
        if role_filter in ['agentes', 'todos']:
            agents = User.objects.filter(groups__name='Agentes')
            self.stdout.write(self.style.HTTP_INFO(f'AGENTES ({agents.count()}):'))
            for user in agents:
                self.stdout.write(f'  • {user.username} - {user.get_full_name()} ({user.email})')
            self.stdout.write('')
        
        if role_filter in ['profesores', 'todos']:
            teachers = User.objects.filter(groups__name='Profesores')
            self.stdout.write(self.style.HTTP_INFO(f'PROFESORES ({teachers.count()}):'))
            for user in teachers:
                self.stdout.write(f'  • {user.username} - {user.get_full_name()} ({user.email})')
            self.stdout.write('')
        
        if role_filter in ['usuarios', 'todos']:
            regular_users = User.objects.filter(groups__name='Usuarios')
            self.stdout.write(self.style.HTTP_INFO(f'USUARIOS REGULARES ({regular_users.count()}):'))
            for user in regular_users:
                self.stdout.write(f'  • {user.username} - {user.get_full_name()} ({user.email})')
            self.stdout.write('')
        
        # Usuarios sin grupo
        users_without_group = User.objects.filter(groups__isnull=True)
        if users_without_group.exists():
            self.stdout.write(self.style.WARNING(f'USUARIOS SIN GRUPO ({users_without_group.count()}):'))
            for user in users_without_group:
                self.stdout.write(f'  • {user.username} - {user.get_full_name()} ({user.email})')

    def assign_role(self, username, role):
        """Asigna rol a usuario"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuario "{username}" no encontrado'))
            return

        # Mapear rol a nombre de grupo
        role_mapping = {
            'agente': 'Agentes',
            'profesor': 'Profesores',
            'usuario': 'Usuarios'
        }
        
        group_name = role_mapping[role]
        
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Grupo "{group_name}" no existe'))
            return

        # Remover de todos los grupos de roles
        user.groups.filter(name__in=['Agentes', 'Profesores', 'Usuarios']).delete()
        
        # Asignar nuevo rol
        user.groups.add(group)
        
        self.stdout.write(
            self.style.SUCCESS(f'Rol "{role}" asignado exitosamente al usuario "{username}"')
        )
        
        # Mostrar información actualizada
        self.show_user_info(username)

    def show_user_info(self, username):
        """Muestra información detallada de un usuario"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuario "{username}" no encontrado'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n=== INFORMACIÓN DE USUARIO ==='))
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Nombre: {user.get_full_name() or "No especificado"}')
        self.stdout.write(f'Email: {user.email or "No especificado"}')
        self.stdout.write(f'Activo: {"Sí" if user.is_active else "No"}')
        self.stdout.write(f'Staff: {"Sí" if user.is_staff else "No"}')
        self.stdout.write(f'Superuser: {"Sí" if user.is_superuser else "No"}')
        
        groups = user.groups.all()
        if groups:
            self.stdout.write(f'Grupos: {", ".join([g.name for g in groups])}')
        else:
            self.stdout.write(self.style.WARNING('Grupos: Ninguno'))
        
        # Información de rol usando utilidades
        role = get_user_role(user)
        self.stdout.write(f'Rol actual: {role}')
        
        # Permisos específicos
        permisos = []
        if is_agent(user):
            permisos.append('Gestión completa del sistema')
        if is_teacher(user):
            permisos.append('Gestión de cursos y exámenes')
        if is_regular_user(user):
            permisos.append('Acceso básico al sistema')
        
        if permisos:
            self.stdout.write(f'Permisos: {", ".join(permisos)}')
        
        # Información del perfil
        try:
            profile = user.profile
            if profile.company:
                self.stdout.write(f'Empresa: {profile.company.name}')
            if profile.cargo:
                self.stdout.write(f'Cargo: {profile.cargo}')
        except:
            pass

    def setup_groups(self):
        """Crea los grupos necesarios si no existen"""
        groups_to_create = ['Agentes', 'Profesores', 'Usuarios']
        
        self.stdout.write(self.style.SUCCESS('=== CONFIGURACIÓN DE GRUPOS ==='))
        
        for group_name in groups_to_create:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Grupo "{group_name}" creado'))
            else:
                self.stdout.write(f'• Grupo "{group_name}" ya existe')
        
        self.stdout.write(self.style.SUCCESS('\n¡Configuración de grupos completada!'))