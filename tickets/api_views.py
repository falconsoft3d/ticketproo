from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
import json
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
@login_required
def upcoming_events_list(request):
    """
    Devuelve la lista de próximos eventos
    """
    try:
        from .models import Event
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now()
        
        # Obtener eventos futuros ordenados por fecha
        upcoming_events = Event.objects.filter(
            event_date__gte=now
        ).order_by('event_date')[:20]  # Limitar a 20 eventos
        
        events_data = []
        for event in upcoming_events:
            # Calcular días hasta el evento
            days_until = (event.event_date.date() - now.date()).days
            
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description[:100] + '...' if len(event.description) > 100 else event.description,
                'event_date': event.event_date.strftime('%d/%m/%Y %H:%M'),
                'event_date_iso': event.event_date.isoformat(),
                'location': event.location or 'Sin ubicación',
                'color': event.color,
                'is_all_day': event.is_all_day,
                'days_until': days_until,
                'created_by': event.created_by.get_full_name() if event.created_by else 'Sistema',
            })
        
        return JsonResponse({
            'count': len(events_data),
            'events': events_data
        })
    
    except Exception as e:
        print(f"Error en upcoming_events_list: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'count': 0, 'events': [], 'error': str(e)})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
            birth_date = None
            days_to_birthday = None
            
            if hasattr(user, 'profile') and user.profile:
                phone = user.profile.phone or ''
                
                # Obtener fecha de cumpleaños y calcular días restantes
                if user.profile.birth_date:
                    birth_date = user.profile.birth_date.strftime('%d/%m/%Y')
                    
                    # Calcular próximo cumpleaños
                    today_date = today
                    next_birthday = user.profile.birth_date.replace(year=today_date.year)
                    
                    # Si el cumpleaños ya pasó este año, calcular para el próximo año
                    if next_birthday < today_date:
                        next_birthday = next_birthday.replace(year=today_date.year + 1)
                    
                    # Calcular días restantes
                    days_to_birthday = (next_birthday - today_date).days
            
            # Formatear nombre completo
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
            
            # Formatear hora de entrada
            entry_time = entry.fecha_entrada.strftime('%H:%M')
            
            # Contar tareas pendientes del usuario
            from .models import Task
            pending_tasks_count = Task.objects.filter(
                assigned_users=user,
                status__in=['pending', 'in_progress']
            ).count()
            
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
                'hours_worked': None,  # Se podría calcular las horas desde la entrada
                'birth_date': birth_date,
                'days_to_birthday': days_to_birthday,
                'pending_tasks': pending_tasks_count
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def short_url_stats_api(request):
    """
    API endpoint para obtener estadísticas de URLs cortas del usuario actual
    """
    from .models import ShortUrl
    from django.db.models import Sum
    
    try:
        # Obtener todas las URLs del usuario
        user_short_urls = ShortUrl.objects.filter(created_by=request.user, is_active=True)
        
        # Calcular estadísticas
        total_urls = user_short_urls.count()
        total_clicks = user_short_urls.aggregate(total=Sum('clicks'))['total'] or 0
        
        # Obtener las 5 URLs más populares
        top_urls = user_short_urls.order_by('-clicks')[:5].values(
            'id', 'short_code', 'title', 'clicks', 'original_url'
        )
        
        return JsonResponse({
            'status': 'success',
            'total_urls': total_urls,
            'total_clicks': total_clicks,
            'top_urls': list(top_urls)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


# ==================== Web Counter API ====================

@csrf_exempt
def web_counter_track(request):
    """API pública para rastrear visitas del contador web"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    from .models import WebCounter, WebCounterVisit
    import hashlib
    from user_agents import parse
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'error': 'Token requerido'}, status=400)
        
        # Buscar el contador
        try:
            counter = WebCounter.objects.get(token=token, is_active=True)
        except WebCounter.DoesNotExist:
            return JsonResponse({'error': 'Contador no encontrado'}, status=404)
        
        # Obtener IP del visitante
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Parse user agent
        user_agent_string = data.get('user_agent', request.META.get('HTTP_USER_AGENT', ''))
        user_agent = parse(user_agent_string)
        
        # Determinar tipo de dispositivo
        if user_agent.is_mobile:
            device_type = 'mobile'
        elif user_agent.is_tablet:
            device_type = 'tablet'
        else:
            device_type = 'desktop'
        
        # Generar session ID único basado en IP + User Agent
        session_string = f"{ip_address}_{user_agent_string}_{counter.token}"
        session_id = hashlib.md5(session_string.encode()).hexdigest()
        
        # Verificar si es una nueva visita (sesión nueva en las últimas 30 minutos)
        from datetime import timedelta
        recent_visit = WebCounterVisit.objects.filter(
            counter=counter,
            session_id=session_id,
            created_at__gte=timezone.now() - timedelta(minutes=30)
        ).first()
        
        is_new_visit = not recent_visit
        
        # Obtener geolocalización (simplificada - se puede mejorar con servicios externos)
        country = ''
        city = ''
        # Aquí podrías integrar un servicio de geolocalización como ipinfo.io o geoip2
        
        # Crear registro de visita
        visit = WebCounterVisit.objects.create(
            counter=counter,
            url=data.get('url', '')[:2048],
            referrer=data.get('referrer', '')[:2048],
            ip_address=ip_address,
            country=country,
            city=city,
            user_agent=user_agent_string[:1000],
            browser=f"{user_agent.browser.family} {user_agent.browser.version_string}",
            os=f"{user_agent.os.family} {user_agent.os.version_string}",
            device_type=device_type,
            screen_resolution=data.get('screen_resolution', ''),
            language=data.get('language', ''),
            session_id=session_id
        )
        
        # Actualizar contadores
        counter.total_page_views += 1
        if is_new_visit:
            counter.total_visits += 1
        counter.save()
        
        return JsonResponse({
            'success': True,
            'visit_id': visit.id,
            'is_new_visit': is_new_visit
        })
        
    except Exception as e:
        print(f"Error en web_counter_track: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([])  # Público
def web_counter_stats(request, token):
    """Obtener estadísticas actualizadas del contador"""
    from .models import WebCounter
    
    try:
        counter = WebCounter.objects.get(token=token, is_active=True)
        
        return Response({
            'success': True,
            'total_visits': counter.total_visits,
            'total_page_views': counter.total_page_views
        })
        
    except WebCounter.DoesNotExist:
        return Response({'error': 'Contador no encontrado'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_create_task(request):
    """Crear tarea rápida desde el botón flotante"""
    from .models import Task
    from datetime import datetime
    
    try:
        # Usar request.data en lugar de json.loads(request.body) para DRF
        data = request.data
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium')
        due_date_str = data.get('due_date')
        assigned_user_id = data.get('assigned_user_id')
        
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'El título es requerido'
            }, status=400)
        
        # Convertir fecha si existe
        due_date = None
        if due_date_str:
            try:
                # Convertir fecha string (YYYY-MM-DD) a datetime
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                # Establecer la hora al final del día
                due_date = due_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass  # Si hay error en la fecha, simplemente la ignoramos
        
        # Crear la tarea
        task = Task.objects.create(
            title=title,
            description=description if description else '',
            priority=priority,
            due_date=due_date,
            created_by=request.user,
            status='pending'
        )
        
        # Asignar usuario: si se seleccionó uno, asignarlo, sino asignar al creador
        if assigned_user_id:
            try:
                from django.contrib.auth.models import User
                assigned_user = User.objects.get(id=assigned_user_id)
                task.assigned_users.add(assigned_user)
            except User.DoesNotExist:
                # Si el usuario no existe, asignar al creador
                task.assigned_users.add(request.user)
        else:
            # Si no se seleccionó usuario, asignar al creador
            task.assigned_users.add(request.user)
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': 'Tarea creada exitosamente'
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_tasks_count(request):
    """Obtener cantidad de tareas pendientes del usuario"""
    from .models import Task
    
    try:
        # Contar tareas pendientes o en progreso asignadas al usuario
        count = Task.objects.filter(
            assigned_users=request.user,
            status__in=['pending', 'in_progress']
        ).count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'count': 0
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users_for_tasks(request):
    """Obtener todos los usuarios para asignar tareas"""
    from django.contrib.auth.models import User
    
    try:
        users = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
        
        users_data = []
        for user in users:
            full_name = user.get_full_name() or user.username
            users_data.append({
                'id': user.id,
                'username': user.username,
                'full_name': full_name,
                'email': user.email
            })
        
        return JsonResponse({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'users': []
        }, status=500)


# ============= API PARA TABLAS DINÁMICAS =============

def validate_dynamic_table_token(table_name, token):
    """Valida el token de una tabla dinámica"""
    from .models import DynamicTable
    try:
        table = DynamicTable.objects.get(name=table_name, api_token=token, is_active=True)
        return table
    except DynamicTable.DoesNotExist:
        return None


def validate_record_data(table, data):
    """Valida los datos de un registro según los campos definidos"""
    errors = []
    validated_data = {}
    
    for field in table.fields.all():
        value = data.get(field.name)
        
        # Verificar campos requeridos
        if field.is_required and not value:
            errors.append(f'El campo "{field.display_name}" es requerido')
            continue
        
        # Si el campo no es requerido y está vacío, usar valor por defecto
        if not value and field.default_value:
            value = field.default_value
        
        # Validación por tipo de campo
        if value:
            try:
                if field.field_type == 'number':
                    value = int(value)
                elif field.field_type == 'decimal':
                    value = float(value)
                elif field.field_type == 'boolean':
                    value = bool(value)
                elif field.field_type == 'json':
                    if isinstance(value, str):
                        import json
                        value = json.loads(value)
                elif field.field_type == 'text' and field.max_length:
                    if len(str(value)) > field.max_length:
                        errors.append(f'El campo "{field.display_name}" excede la longitud máxima de {field.max_length}')
            except (ValueError, json.JSONDecodeError) as e:
                errors.append(f'Valor inválido para el campo "{field.display_name}": {str(e)}')
                continue
        
        # Verificar unicidad
        if field.is_unique and value:
            from .models import DynamicTableRecord
            existing = DynamicTableRecord.objects.filter(
                table=table,
                data__contains={field.name: value}
            ).exists()
            if existing:
                errors.append(f'El valor para "{field.display_name}" ya existe')
        
        validated_data[field.name] = value
    
    return validated_data, errors


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def dynamic_table_api_list(request, table_name):
    """API para listar o crear registros en una tabla dinámica"""
    from .models import DynamicTable, DynamicTableRecord
    
    # Obtener token del header o query param
    token = request.headers.get('X-API-Token') or request.GET.get('token')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token de API requerido'
        }, status=401)
    
    # Validar token y obtener tabla
    table = validate_dynamic_table_token(table_name, token)
    if not table:
        return JsonResponse({
            'success': False,
            'error': 'Token inválido o tabla inactiva'
        }, status=403)
    
    # GET - Listar registros
    if request.method == 'GET':
        if not table.allow_public_read:
            return JsonResponse({
                'success': False,
                'error': 'Lectura no permitida para esta tabla'
            }, status=403)
        
        records = DynamicTableRecord.objects.filter(table=table)
        
        # Filtros opcionales
        search = request.GET.get('search')
        if search:
            # Buscar en todos los campos de texto
            q_objects = Q()
            for field in table.fields.filter(field_type__in=['text', 'textarea', 'email']):
                q_objects |= Q(data__contains={field.name: search})
            records = records.filter(q_objects)
        
        # Paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        start = (page - 1) * per_page
        end = start + per_page
        
        total = records.count()
        records = records[start:end]
        
        data = []
        for record in records:
            record_data = {
                'id': record.id,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat(),
                **record.data
            }
            data.append(record_data)
        
        return JsonResponse({
            'success': True,
            'table': table.name,
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': data
        })
    
    # POST - Crear registro
    elif request.method == 'POST':
        if not table.allow_public_create:
            return JsonResponse({
                'success': False,
                'error': 'Creación no permitida para esta tabla'
            }, status=403)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido'
            }, status=400)
        
        # Validar datos
        validated_data, errors = validate_record_data(table, data)
        
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
        
        # Crear registro
        record = DynamicTableRecord.objects.create(
            table=table,
            data=validated_data,
            created_by_ip=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Registro creado exitosamente',
            'id': record.id,
            'data': {
                'id': record.id,
                'created_at': record.created_at.isoformat(),
                **record.data
            }
        }, status=201)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def dynamic_table_api_detail(request, table_name, record_id):
    """API para obtener, actualizar o eliminar un registro específico"""
    from .models import DynamicTable, DynamicTableRecord
    
    # Obtener token
    token = request.headers.get('X-API-Token') or request.GET.get('token')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token de API requerido'
        }, status=401)
    
    # Validar token y obtener tabla
    table = validate_dynamic_table_token(table_name, token)
    if not table:
        return JsonResponse({
            'success': False,
            'error': 'Token inválido o tabla inactiva'
        }, status=403)
    
    # Obtener registro
    try:
        record = DynamicTableRecord.objects.get(id=record_id, table=table)
    except DynamicTableRecord.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Registro no encontrado'
        }, status=404)
    
    # GET - Obtener registro
    if request.method == 'GET':
        if not table.allow_public_read:
            return JsonResponse({
                'success': False,
                'error': 'Lectura no permitida para esta tabla'
            }, status=403)
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': record.id,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat(),
                **record.data
            }
        })
    
    # PUT - Actualizar registro
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido'
            }, status=400)
        
        # Validar datos
        validated_data, errors = validate_record_data(table, data)
        
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
        
        # Actualizar registro
        record.data = validated_data
        record.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Registro actualizado exitosamente',
            'data': {
                'id': record.id,
                'updated_at': record.updated_at.isoformat(),
                **record.data
            }
        })
    
    # DELETE - Eliminar registro
    elif request.method == 'DELETE':
        record.delete()
        return JsonResponse({
            'success': True,
            'message': 'Registro eliminado exitosamente'
        })

