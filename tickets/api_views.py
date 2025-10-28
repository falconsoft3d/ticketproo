from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
import psutil
import platform
import socket
import subprocess
import os
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


@api_view(['POST'])
def whatsapp_receive_message(request):
    """
    Endpoint para recibir mensajes de WhatsApp desde el servidor Node.js
    No requiere autenticación porque viene del servidor interno
    """
    from .models import WhatsAppConnection, WhatsAppMessage, WhatsAppKeyword
    from django.contrib.auth.models import User
    
    try:
        # Extraer datos del mensaje
        user_id = request.data.get('user_id')
        from_number = request.data.get('from')
        body = request.data.get('body', '')
        timestamp = request.data.get('timestamp')
        message_id = request.data.get('message_id')
        
        if not user_id or not from_number:
            return Response({
                'error': 'Faltan datos requeridos (user_id, from)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el usuario y la conexión
        try:
            user = User.objects.get(id=user_id)
            connection = WhatsAppConnection.objects.get(user=user)
        except (User.DoesNotExist, WhatsAppConnection.DoesNotExist):
            return Response({
                'error': 'Usuario o conexión no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Guardar el mensaje recibido
        incoming_message = WhatsAppMessage.objects.create(
            connection=connection,
            sender_number=from_number,
            message_text=body,
            message_type='received',
            whatsapp_message_id=message_id
        )
        
        # Buscar palabra clave que coincida
        keywords = WhatsAppKeyword.objects.filter(
            connection=connection,
            is_active=True
        ).order_by('-priority', 'keyword')
        
        auto_reply_text = None
        matched_keyword = None
        
        for keyword in keywords:
            message_to_check = body
            keyword_to_check = keyword.keyword
            
            # Aplicar sensibilidad a mayúsculas/minúsculas
            if not keyword.is_case_sensitive:
                message_to_check = message_to_check.lower()
                keyword_to_check = keyword_to_check.lower()
            
            # Verificar coincidencia
            if keyword.is_exact_match:
                if message_to_check == keyword_to_check:
                    auto_reply_text = keyword.response
                    matched_keyword = keyword
                    break
            else:
                if keyword_to_check in message_to_check:
                    auto_reply_text = keyword.response
                    matched_keyword = keyword
                    break
        
        # Si hay respuesta automática, enviarla
        if auto_reply_text:
            # Guardar la respuesta automática en la base de datos
            WhatsAppMessage.objects.create(
                connection=connection,
                sender_number=connection.phone_number or 'Bot',
                recipient_number=from_number,
                message_text=auto_reply_text,
                message_type='auto_reply',
                related_keyword=matched_keyword
            )
            
            return Response({
                'auto_reply': auto_reply_text,
                'matched_keyword': matched_keyword.keyword
            })
        else:
            return Response({
                'message': 'Mensaje recibido, sin respuesta automática'
            })
            
    except Exception as e:
        return Response({
            'error': f'Error al procesar mensaje: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # No requiere autenticación para permitir acceso público
def landing_page_meeting_click(request, slug):
    """
    Incrementa el contador de clics del botón "Planificar Reunión"
    """
    try:
        from .models import LandingPage
        from django.db import transaction
        
        # Buscar la landing page por slug
        landing_page = LandingPage.objects.get(slug=slug, is_active=True)
        
        # Incrementar el contador de clics de reunión de forma atómica
        with transaction.atomic():
            landing_page.meeting_button_clicks += 1
            landing_page.save(update_fields=['meeting_button_clicks'])
        
        return Response({
            'success': True,
            'meeting_clicks': landing_page.meeting_button_clicks
        })
        
    except LandingPage.DoesNotExist:
        return Response({
            'error': 'Landing page no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error al incrementar contador: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # No requiere autenticación para permitir acceso público
def landing_page_contact_click(request, slug):
    """
    Incrementa el contador de clics del botón "Contactar"
    """
    try:
        from .models import LandingPage
        from django.db import transaction
        
        # Buscar la landing page por slug
        landing_page = LandingPage.objects.get(slug=slug, is_active=True)
        
        # Incrementar el contador de clics de contacto de forma atómica
        with transaction.atomic():
            landing_page.contact_button_clicks += 1
            landing_page.save(update_fields=['contact_button_clicks'])
        
        return Response({
            'success': True,
            'contact_clicks': landing_page.contact_button_clicks
        })
        
    except LandingPage.DoesNotExist:
        return Response({
            'error': 'Landing page no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error al incrementar contador: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])  # No requiere autenticación para acceso público
def active_users_count(request):
    """
    Devuelve el número de usuarios activos en oficina
    Usuarios activos = tienen entrada hoy pero no han registrado salida
    """
    try:
        from django.contrib.auth.models import User
        from .models import TimeEntry
        from django.utils import timezone
        from datetime import datetime
        
        today = timezone.now().date()
        
        # Buscar usuarios que tengan entrada hoy pero no salida
        active_entries = TimeEntry.objects.filter(
            fecha_entrada__date=today,
            fecha_salida__isnull=True
        ).values('user').distinct()
        
        active_count = active_entries.count()
        
        return Response({
            'count': active_count,
            'date': today.isoformat()
        })
        
    except Exception as e:
        # En caso de error, devolver datos de ejemplo
        return Response({
            'count': 0,
            'date': timezone.now().date().isoformat(),
            'error': str(e)
        })


@api_view(['GET'])
@permission_classes([])  # No requiere autenticación para acceso público
def active_users_list(request):
    """
    Devuelve la lista de usuarios activos en oficina con detalles
    Usuarios activos = tienen entrada hoy pero no han registrado salida
    """
    try:
        from django.contrib.auth.models import User
        from .models import TimeEntry
        from django.utils import timezone
        from datetime import datetime
        import json
        
        today = timezone.now().date()
        
        # Buscar entradas de tiempo activas (con entrada pero sin salida hoy)
        active_entries = TimeEntry.objects.filter(
            fecha_entrada__date=today,
            fecha_salida__isnull=True
        ).select_related('user').order_by('fecha_entrada')
        
        users_data = []
        seen_users = set()  # Para evitar duplicados si un usuario tiene múltiples entradas
        
        for entry in active_entries:
            user = entry.user
            
            # Evitar duplicados
            if user.id in seen_users:
                continue
            seen_users.add(user.id)
            
            # Obtener información del perfil del usuario
            phone = ''
            email = user.email or ''
            
            if hasattr(user, 'userprofile') and user.userprofile:
                phone = user.userprofile.phone or ''
            
            # Formatear nombre completo
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            
            # Formatear hora de entrada
            entry_time = entry.fecha_entrada.strftime('%H:%M')
            
            users_data.append({
                'id': user.id,
                'name': full_name,
                'username': user.username,
                'email': email,
                'phone': phone,
                'entry_time': entry_time,
                'entry_datetime': entry.fecha_entrada.isoformat(),
                'avatar_url': f"https://ui-avatars.com/api/?name={user.first_name}+{user.last_name}&background=28a745&color=fff&size=40",
                'status': 'active',
                'hours_worked': None  # Se podría calcular las horas desde la entrada
            })
        
        # Calcular horas trabajadas para cada usuario
        for user_data in users_data:
            entry_datetime = datetime.fromisoformat(user_data['entry_datetime'].replace('Z', '+00:00'))
            if timezone.is_naive(entry_datetime):
                entry_datetime = timezone.make_aware(entry_datetime)
            
            time_diff = timezone.now() - entry_datetime
            hours_worked = round(time_diff.total_seconds() / 3600, 1)
            user_data['hours_worked'] = hours_worked
        
        return Response({
            'users': users_data,
            'count': len(users_data),
            'date': today.isoformat(),
            'last_update': timezone.now().isoformat()
        })
        
    except Exception as e:
        # En caso de error, devolver respuesta vacía con información del error
        return Response({
            'users': [],
            'count': 0,
            'date': timezone.now().date().isoformat(),
            'last_update': timezone.now().isoformat(),
            'error': str(e)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def open_tickets_count(request):
    """
    Obtener el conteo de tickets abiertos según el tipo de usuario
    - Agentes: pueden ver todos los tickets abiertos del sistema
    - Usuarios: solo pueden ver tickets abiertos de su empresa
    """
    try:
        # Estados considerados como "abiertos" (en inglés como están en la BD)
        open_statuses = ['open', 'in_progress', 'escalated']
        
        # Verificar si es agente
        if is_agent(request.user):
            # Los agentes ven todos los tickets abiertos
            count = Ticket.objects.filter(
                status__in=open_statuses
            ).count()
        else:
            # Los usuarios normales solo ven tickets de su empresa
            user_company = None
            try:
                user_company = request.user.profile.company
            except:
                pass
            
            if user_company:
                count = Ticket.objects.filter(
                    company=user_company,
                    status__in=open_statuses
                ).count()
            else:
                # Si no tiene empresa, solo sus propios tickets
                count = Ticket.objects.filter(
                    created_by=request.user,
                    status__in=open_statuses
                ).count()
        
        return Response({
            'count': count,
            'is_agent': is_agent(request.user),
            'user_company': request.user.profile.company.name if hasattr(request.user, 'profile') and request.user.profile.company else None
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'count': 0
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def direct_ai_chat(request):
    """
    Endpoint directo para chat con IA usando OpenAI
    """
    try:
        from .models import SystemConfiguration
        import openai
        
        # Obtener el mensaje del usuario
        message = request.data.get('message', '').strip()
        if not message:
            return Response({
                'error': 'Mensaje requerido'
            }, status=400)
        
        # Obtener configuración del sistema
        config = SystemConfiguration.get_config()
        
        # Verificar si el chat IA está habilitado
        if not config.ai_chat_enabled:
            return Response({
                'error': 'El chat con IA no está habilitado'
            }, status=400)
        
        # Verificar si hay API key configurada
        if not config.openai_api_key:
            return Response({
                'error': 'API key de OpenAI no configurada'
            }, status=400)
        
        # Crear cliente OpenAI
        client = openai.OpenAI(api_key=config.openai_api_key)
        
        # Preparar contexto del sistema
        system_prompt = f"""Eres un asistente inteligente para el sistema de tickets TicketProo. 
Usuario actual: {request.user.username} ({request.user.first_name} {request.user.last_name})
Tu función es ayudar con consultas sobre tickets, tareas, gestión del sistema y proporcionar información útil.
Responde de forma clara, concisa y profesional."""
        
        # Realizar llamada a la API de OpenAI
        response = client.chat.completions.create(
            model=config.openai_model or 'gpt-4o',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return Response({
            'status': 'success',
            'response': ai_response,
            'user': request.user.username,
            'model': config.openai_model or 'gpt-4o'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': f'Error al procesar mensaje: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_info_api(request):
    """
    API para obtener información del sistema en tiempo real
    """
    try:
        # Información de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Información de memoria
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)  # GB
        memory_used = round(memory.used / (1024**3), 2)    # GB
        memory_percent = memory.percent
        
        # Información de disco
        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024**3), 2)      # GB
        disk_used = round(disk.used / (1024**3), 2)        # GB
        disk_free = round(disk.free / (1024**3), 2)        # GB
        disk_percent = round((disk.used / disk.total) * 100, 1)
        
        # Información de red
        network_interfaces = psutil.net_if_addrs()
        local_ip = None
        
        # Buscar la IP local (no loopback)
        for interface_name, interface_addresses in network_interfaces.items():
            for address in interface_addresses:
                if str(address.family) == 'AddressFamily.AF_INET':
                    if not address.address.startswith('127.'):
                        local_ip = address.address
                        break
            if local_ip:
                break
        
        # Información del sistema
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': socket.gethostname(),
            'processor': platform.processor()
        }
        
        # Obtener MAC address de la interfaz principal
        mac_address = None
        try:
            import uuid
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                                   for ele in range(0,8*6,8)][::-1])
        except:
            mac_address = 'No disponible'
        
        # Procesos principales que consumen CPU
        processes = []
        total_processes = 0
        try:
            all_processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent']))
            total_processes = len(all_processes)
            
            for proc in all_processes:
                processes.append(proc.info)
            
            # Ordenar por CPU y tomar los top 5
            processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)[:5]
        except:
            processes = []
            total_processes = 0
        
        # Información de temperatura (macOS/Linux específico)
        cpu_temperature = None
        try:
            if platform.system() == "Darwin":  # macOS
                # En macOS podemos intentar obtener la temperatura usando SMC
                cpu_temperature = "45°C"  # Valor simulado por ahora
            elif platform.system() == "Linux":
                # En Linux intentar leer desde /sys/class/thermal/
                temp_files = ['/sys/class/thermal/thermal_zone0/temp']
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        with open(temp_file, 'r') as f:
                            temp = int(f.read().strip()) / 1000
                            cpu_temperature = f"{temp:.1f}°C"
                            break
        except:
            pass
        
        # Obtener usuarios activos
        user_sessions = 0
        try:
            users = psutil.users()
            user_sessions = len(set([user.name for user in users]))
        except:
            user_sessions = 1
        
        # Tiempo de funcionamiento del sistema
        try:
            uptime_seconds = psutil.boot_time()
            uptime = timezone.now().timestamp() - uptime_seconds
            uptime_hours = int(uptime // 3600)
            uptime_days = int(uptime_hours // 24)
        except:
            uptime_days = 0
            uptime_hours = 0
        
        return JsonResponse({
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'cpu': {
                'usage_percent': round(cpu_percent, 1),
                'cores': cpu_count,
                'frequency': round(cpu_freq.current, 2) if cpu_freq else None
            },
            'memory': {
                'total_gb': memory_total,
                'used_gb': memory_used,
                'free_gb': round(memory_total - memory_used, 2),
                'usage_percent': round(memory_percent, 1)
            },
            'disk': {
                'total_gb': disk_total,
                'used_gb': disk_used,
                'free_gb': disk_free,
                'usage_percent': disk_percent
            },
            'network': {
                'local_ip': local_ip or 'No disponible',
                'mac_address': mac_address,
                'hostname': system_info['hostname']
            },
            'system': system_info,
            'uptime': {
                'days': uptime_days,
                'hours': uptime_hours % 24
            },
            'top_processes': processes,
            'process_count': total_processes,
            'temperature': cpu_temperature,
            'user_sessions': user_sessions
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': f'Error al obtener información del sistema: {str(e)}'
        }, status=500)
