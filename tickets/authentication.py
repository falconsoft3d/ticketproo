from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
from .models import UserProfile


class TokenAuthentication(BaseAuthentication):
    """
    Autenticación personalizada usando el token API del usuario
    """
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            keyword, token = auth_header.split()
        except ValueError:
            return None
        
        if keyword.lower() != self.keyword.lower():
            return None
        
        return self.authenticate_credentials(token)
    
    def authenticate_credentials(self, token):
        try:
            profile = UserProfile.objects.get(api_token=token, enable_api_access=True)
        except UserProfile.DoesNotExist:
            raise AuthenticationFailed('Token de API inválido o API deshabilitada')
        
        if not profile.user.is_active:
            raise AuthenticationFailed('Usuario inactivo')
        
        return (profile.user, token)
    
    def authenticate_header(self, request):
        return f'{self.keyword} realm="api"'