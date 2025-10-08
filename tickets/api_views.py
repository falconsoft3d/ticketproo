from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Ticket, Category, Company, Project
from .serializers import (
    TicketSerializer, TicketListSerializer, TicketCreateSerializer,
    CategorySerializer, CompanySerializer, ProjectSerializer
)
from .utils import is_agent


class TicketPermission(permissions.BasePermission):
    """
    Permisos personalizados para tickets via API
    """
    def has_permission(self, request, view):
        # El usuario debe estar autenticado y tener API habilitada
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.enable_api_access and profile.api_token
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Los agentes pueden ver/editar todos los tickets
        if is_agent(request.user):
            return True
        
        # Los usuarios regulares solo pueden ver/editar sus propios tickets
        # y tickets de su empresa
        user_company = None
        try:
            user_company = request.user.profile.company
        except:
            pass
        
        # Puede ver si es creador, asignado, o de su empresa
        if obj.created_by == request.user:
            return True
        if obj.assigned_to == request.user:
            return True
        if user_company and obj.company == user_company:
            return True
        
        return False


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operaciones CRUD de tickets via API
    """
    permission_classes = [TicketPermission]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        elif self.action == 'create':
            return TicketCreateSerializer
        return TicketSerializer
    
    def get_queryset(self):
        """
        Retorna tickets según los permisos del usuario
        """
        user = self.request.user
        
        if is_agent(user):
            # Los agentes ven todos los tickets
            queryset = Ticket.objects.all()
        else:
            # Los usuarios regulares ven sus propios tickets y los de su empresa
            user_company = None
            try:
                user_company = user.profile.company
            except:
                pass
            
            query_conditions = Q(created_by=user)  # Sus propios tickets
            
            # Agregar tickets de la empresa del usuario
            if user_company:
                query_conditions |= Q(company=user_company)
            
            # Agregar tickets asignados al usuario
            query_conditions |= Q(assigned_to=user)
            
            queryset = Ticket.objects.filter(query_conditions).distinct()
        
        # Aplicar filtros de query parameters
        status_filter = self.request.query_params.get('status')
        priority_filter = self.request.query_params.get('priority')
        search = self.request.query_params.get('search')
        assigned_filter = self.request.query_params.get('assigned_to')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        if is_agent(user) and assigned_filter:
            if assigned_filter == 'unassigned':
                queryset = queryset.filter(assigned_to__isnull=True)
            elif assigned_filter == 'me':
                queryset = queryset.filter(assigned_to=user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Asignar el usuario actual como creador del ticket
        """
        serializer.save(created_by=self.request.user)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para categorías
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [TicketPermission]


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para empresas
    """
    queryset = Company.objects.filter(is_active=True)
    serializer_class = CompanySerializer
    permission_classes = [TicketPermission]


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para proyectos
    """
    serializer_class = ProjectSerializer
    permission_classes = [TicketPermission]
    
    def get_queryset(self):
        user = self.request.user
        if is_agent(user):
            return Project.objects.filter(is_active=True)
        else:
            # Los usuarios regulares solo ven proyectos asignados o creados por ellos
            return Project.objects.filter(
                Q(assigned_users=user) | Q(created_by=user),
                is_active=True
            ).distinct()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_status(request):
    """
    Endpoint para verificar el estado de la API del usuario
    """
    try:
        profile = request.user.profile
        return Response({
            'api_enabled': profile.enable_api_access,
            'has_token': bool(profile.api_token),
            'user': request.user.username,
            'is_agent': is_agent(request.user)
        })
    except:
        return Response({
            'api_enabled': False,
            'has_token': False,
            'user': request.user.username,
            'is_agent': False
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_api_token(request):
    """
    Endpoint para generar un nuevo token de API
    """
    try:
        profile = request.user.profile
        token = profile.generate_api_token()
        profile.enable_api_access = True
        profile.save()
        
        return Response({
            'message': 'Token de API generado exitosamente',
            'token': token,
            'api_enabled': True
        })
    except Exception as e:
        return Response({
            'error': f'Error al generar token: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_api_access(request):
    """
    Endpoint para activar/desactivar el acceso a la API
    """
    try:
        profile = request.user.profile
        profile.enable_api_access = not profile.enable_api_access
        profile.save()
        
        return Response({
            'message': f'Acceso API {"activado" if profile.enable_api_access else "desactivado"}',
            'api_enabled': profile.enable_api_access
        })
    except Exception as e:
        return Response({
            'error': f'Error al cambiar estado de API: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)