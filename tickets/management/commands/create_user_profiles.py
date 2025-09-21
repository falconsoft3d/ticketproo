from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import UserProfile


class Command(BaseCommand):
    help = 'Crear perfiles para usuarios que no tienen UserProfile'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            if not hasattr(user, 'profile') or not UserProfile.objects.filter(user=user).exists():
                users_without_profile.append(user)
        
        if users_without_profile:
            for user in users_without_profile:
                UserProfile.objects.get_or_create(user=user)
                self.stdout.write(f'Perfil creado para: {user.username}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se crearon {len(users_without_profile)} perfiles de usuario.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todos los usuarios ya tienen perfiles.')
            )