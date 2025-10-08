from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.db import models
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.conf import settings
from datetime import datetime, date
import os
from datetime import timedelta

# Imports para OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI library not available")

from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserProfile, 
    UserNote, TimeEntry, Project, Company, SystemConfiguration, Document, UrlManager, WorkOrder, Task,
    DailyTaskSession, DailyTaskItem, ChatRoom, ChatMessage, ContactFormSubmission,
    Opportunity, OpportunityStatus, OpportunityNote, OpportunityStatusHistory,
    Meeting, MeetingAttendee, MeetingQuestion, Contact,
    BlogCategory, BlogPost, BlogComment, AIChatSession, AIChatMessage, Concept
)
from .forms import (
    TicketForm, AgentTicketForm, UserManagementForm, UserEditForm, 
    TicketAttachmentForm, CategoryForm, UserTicketForm, UserTicketEditForm, 
    TicketCommentForm, UserNoteForm, TimeEntryStartForm, TimeEntryEndForm, 
    TimeEntryEditForm, ProjectForm, CompanyForm, SystemConfigurationForm, DocumentForm,
    UrlManagerForm, UrlManagerFilterForm, WorkOrderForm, WorkOrderFilterForm, TaskForm,
    ChatMessageForm, ChatRoomForm, AIChatSessionForm, AIChatMessageForm, ConceptForm
)
from .utils import is_agent, is_regular_user, get_user_role, assign_user_to_group

def home_view(request):
    """Vista para la página de inicio de TicketProo - accesible para todos"""
    # Estadísticas generales del sistema
    total_tickets = Ticket.objects.count()
    total_users = Ticket.objects.values('created_by').distinct().count()
    
    # Estadísticas por estado si el usuario está autenticado
    user_tickets_count = 0
    user_role = None
    tickets_by_status = {}
    
    if request.user.is_authenticated:
        user_role = get_user_role(request.user)
        
        if is_agent(request.user):
            # Para agentes: estadísticas de todos los tickets
            tickets_by_status = {
                'open': Ticket.objects.filter(status='open').count(),
                'in_progress': Ticket.objects.filter(status='in_progress').count(),
                'resolved': Ticket.objects.filter(status='resolved').count(),
                'closed': Ticket.objects.filter(status='closed').count(),
            }
            user_tickets_count = Ticket.objects.count()
        else:
            # Para usuarios regulares: solo sus tickets
            user_tickets = Ticket.objects.filter(created_by=request.user)
            tickets_by_status = {
                'open': user_tickets.filter(status='open').count(),
                'in_progress': user_tickets.filter(status='in_progress').count(),
                'resolved': user_tickets.filter(status='resolved').count(),
                'closed': user_tickets.filter(status='closed').count(),
            }
            user_tickets_count = user_tickets.count()
    
    # Obtener conceptos activos para mostrar en el home
    concepts = Concept.objects.filter(is_active=True)[:10]  # Máximo 10 conceptos
    
    context = {
        'total_tickets': total_tickets,
        'total_users': total_users,
        'user_tickets_count': user_tickets_count,
        'user_role': user_role,
        'tickets_by_status': tickets_by_status,
        'is_authenticated': request.user.is_authenticated,
        'concepts': concepts,
    }
    return render(request, 'tickets/home.html', context)

def register_view(request):
    """Vista para registro de nuevos usuarios"""
    # Verificar si el registro está habilitado en la configuración
    config = SystemConfiguration.get_config()
    
    if not config.allow_user_registration:
        messages.error(request, 'El registro de nuevos usuarios está deshabilitado. Contacta a un administrador.')
        return redirect('login')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Asignar automáticamente al grupo de Usuarios
            assign_user_to_group(user, 'Usuarios')
            
            messages.success(request, f'Cuenta creada para {username}. Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard_view(request):
    """Vista principal del dashboard de TicketProo"""
    user_role = get_user_role(request.user)
    
    if is_agent(request.user):
        # Estadísticas para agentes (todos los tickets)
        all_tickets = Ticket.objects.all()
        total_tickets = all_tickets.count()
        open_tickets = all_tickets.filter(status='open').count()
        in_progress_tickets = all_tickets.filter(status='in_progress').count()
        resolved_tickets = all_tickets.filter(status='resolved').count()
        recent_tickets = all_tickets[:5]
        
        # Estadísticas adicionales para agentes
        unassigned_tickets = all_tickets.filter(assigned_to__isnull=True).count()
        my_assigned_tickets = all_tickets.filter(assigned_to=request.user).count()
        
        # Obtener horas diarias
        daily_hours = 0
        try:
            daily_hours = request.user.userprofile.get_daily_hours()
        except AttributeError:
            # Crear UserProfile si no existe
            from tickets.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            daily_hours = profile.get_daily_hours()
        
        # Órdenes de trabajo pendientes de aprobación (solo primeras 5)
        pending_work_orders = WorkOrder.objects.filter(status='draft').order_by('-created_at')[:5]
        
        context = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'recent_tickets': recent_tickets,
            'unassigned_tickets': unassigned_tickets,
            'my_assigned_tickets': my_assigned_tickets,
            'pending_work_orders': pending_work_orders,
            'user_role': user_role,
            'is_agent': True,
            'daily_hours': daily_hours,
        }
        
        # Agregar conceptos activos
        concepts = Concept.objects.filter(is_active=True)[:10]
        context['concepts'] = concepts
    else:
        # Estadísticas para usuarios regulares (sus tickets + tickets de empresa + proyectos)
        user_projects = request.user.assigned_projects.all()
        user_company = None
        
        # Obtener empresa del usuario si tiene perfil
        try:
            user_company = request.user.profile.company
        except:
            pass
        
        # Construir query base
        query_conditions = Q(created_by=request.user)  # Sus propios tickets
        
        # Agregar tickets de proyectos asignados
        if user_projects.exists():
            query_conditions |= Q(project__in=user_projects)
        
        # Agregar tickets de la empresa del usuario
        if user_company:
            query_conditions |= Q(company=user_company)
        
        user_tickets = Ticket.objects.filter(query_conditions).distinct()
        total_tickets = user_tickets.count()
        open_tickets = user_tickets.filter(status='open').count()
        in_progress_tickets = user_tickets.filter(status='in_progress').count()
        resolved_tickets = user_tickets.filter(status='resolved').count()
        recent_tickets = user_tickets.order_by('-created_at')[:5]
        
        # Estadísticas adicionales para mostrar el contexto
        own_tickets = Ticket.objects.filter(created_by=request.user).count()
        company_tickets = 0
        if user_company:
            company_tickets = Ticket.objects.filter(company=user_company).exclude(created_by=request.user).count()
        
        # Obtener horas diarias
        daily_hours = 0
        try:
            daily_hours = request.user.userprofile.get_daily_hours()
        except AttributeError:
            # Crear UserProfile si no existe
            from tickets.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            daily_hours = profile.get_daily_hours()
        
        context = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'recent_tickets': recent_tickets,
            'own_tickets': own_tickets,
            'company_tickets': company_tickets,
            'user_company': user_company,
            'user_role': user_role,
            'is_agent': False,
            'daily_hours': daily_hours,
        }
    
    return render(request, 'tickets/dashboard.html', context)

@login_required
def ticket_list_view(request):
    """Vista para listar tickets según el rol del usuario"""
    if is_agent(request.user):
        # Los agentes ven todos los tickets
        tickets = Ticket.objects.all()
    else:
        # Los usuarios regulares ven sus propios tickets Y tickets de proyectos asignados Y tickets de su empresa
        user_projects = request.user.assigned_projects.all()
        user_company = None
        
        # Obtener empresa del usuario si tiene perfil
        try:
            user_company = request.user.profile.company
        except:
            pass
        
        # Construir query base
        query_conditions = Q(created_by=request.user)  # Sus propios tickets
        
        # Agregar tickets de proyectos asignados
        if user_projects.exists():
            query_conditions |= Q(project__in=user_projects)
        
        # Agregar tickets de la empresa del usuario
        if user_company:
            query_conditions |= Q(company=user_company)
        
        tickets = Ticket.objects.filter(query_conditions).distinct()
    
    # Filtros
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('search')
    assigned_filter = request.GET.get('assigned_to')  # Nuevo filtro para agentes
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    if search:
        tickets = tickets.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Filtro adicional para agentes
    if is_agent(request.user) and assigned_filter:
        if assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        elif assigned_filter == 'me':
            tickets = tickets.filter(assigned_to=request.user)
    
    # Paginación
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search': search,
        'assigned_filter': assigned_filter,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'is_agent': is_agent(request.user),
        'user_role': get_user_role(request.user),
    }
    return render(request, 'tickets/ticket_list.html', context)

@login_required
def ticket_create_view(request):
    """Vista para crear un nuevo ticket"""
    # Usar formulario apropiado según el rol
    FormClass = AgentTicketForm if is_agent(request.user) else UserTicketForm
    
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            # Los usuarios regulares siempre crean tickets con estado "open"
            if not is_agent(request.user):
                ticket.status = 'open'
            ticket.save()
            messages.success(request, 'Ticket creado exitosamente.')
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = FormClass()
    
    context = {
        'form': form,
        'is_agent': is_agent(request.user),
        'user_role': get_user_role(request.user),
    }
    
    return render(request, 'tickets/ticket_create.html', context)

@login_required
def ticket_detail_view(request, pk):
    """Vista para ver los detalles de un ticket"""
    if is_agent(request.user):
        # Los agentes pueden ver cualquier ticket
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        # Los usuarios pueden ver sus propios tickets O tickets de su empresa O tickets de proyectos asignados
        user_projects = request.user.assigned_projects.all()
        user_company = None
        
        # Obtener empresa del usuario si tiene perfil
        try:
            user_company = request.user.profile.company
        except:
            pass
        
        # Construir query de acceso
        query_conditions = Q(created_by=request.user)  # Sus propios tickets
        
        # Agregar tickets de proyectos asignados
        if user_projects.exists():
            query_conditions |= Q(project__in=user_projects)
        
        # Agregar tickets de la empresa del usuario
        if user_company:
            query_conditions |= Q(company=user_company)
        
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Verificar que el usuario tenga acceso al ticket
        if not Ticket.objects.filter(pk=pk).filter(query_conditions).exists():
            messages.error(request, 'No tienes permisos para ver este ticket.')
            return redirect('ticket_list')
    
    # Manejar autoasignación para agentes
    if request.method == 'POST' and 'assign_to_me' in request.POST and is_agent(request.user):
        ticket.assigned_to = request.user
        ticket.save()
        messages.success(request, f'Te has asignado el ticket #{ticket.pk}.')
        return redirect('ticket_detail', pk=pk)
    
    # Manejar activar compartir público (solo agentes)
    if request.method == 'POST' and 'enable_public_share' in request.POST and is_agent(request.user):
        ticket.is_public_shareable = True
        ticket.save()
        messages.success(request, 'Compartir público activado. Ahora puedes compartir este ticket mediante un enlace.')
        return redirect('ticket_detail', pk=pk)
    
    # Manejar desactivar compartir público (solo agentes)
    if request.method == 'POST' and 'disable_public_share' in request.POST and is_agent(request.user):
        ticket.is_public_shareable = False
        ticket.save()
        messages.warning(request, 'Compartir público desactivado. El enlace ya no será accesible.')
        return redirect('ticket_detail', pk=pk)
    
    # Manejar regenerar token (solo agentes)
    if request.method == 'POST' and 'regenerate_token' in request.POST and is_agent(request.user):
        ticket.regenerate_public_token()
        messages.info(request, 'Enlace público regenerado. El enlace anterior ya no es válido.')
        return redirect('ticket_detail', pk=pk)
    
    # Formulario para agregar comentarios
    comment_form = TicketCommentForm()
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_form = TicketCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comentario agregado exitosamente.')
            return redirect('ticket_detail', pk=pk)
    
    # Formulario para subir adjuntos
    attachment_form = TicketAttachmentForm()
    if request.method == 'POST' and 'upload_attachment' in request.POST:
        attachment_form = TicketAttachmentForm(request.POST, request.FILES)
        if attachment_form.is_valid():
            attachment = attachment_form.save(commit=False)
            attachment.ticket = ticket
            attachment.uploaded_by = request.user
            attachment.original_filename = attachment.file.name
            attachment.file_size = attachment.file.size
            attachment.save()
            messages.success(request, 'Adjunto subido exitosamente.')
            return redirect('ticket_detail', pk=pk)
    
    # Obtener comentarios del ticket
    comments = ticket.comments.all().order_by('created_at')
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
        'is_agent': is_agent(request.user),
        'user_role': get_user_role(request.user),
    }
    return render(request, 'tickets/ticket_detail.html', context)

@login_required
def ticket_edit_view(request, pk):
    """Vista para editar un ticket"""
    if is_agent(request.user):
        # Los agentes pueden editar cualquier ticket
        ticket = get_object_or_404(Ticket, pk=pk)
        FormClass = AgentTicketForm
    else:
        # Los usuarios pueden editar sus propios tickets O tickets de su empresa O tickets de proyectos asignados
        user_projects = request.user.assigned_projects.all()
        user_company = None
        
        # Obtener empresa del usuario si tiene perfil
        try:
            user_company = request.user.profile.company
        except:
            pass
        
        # Construir query de acceso
        query_conditions = Q(created_by=request.user)  # Sus propios tickets
        
        # Agregar tickets de proyectos asignados
        if user_projects.exists():
            query_conditions |= Q(project__in=user_projects)
        
        # Agregar tickets de la empresa del usuario
        if user_company:
            query_conditions |= Q(company=user_company)
        
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Verificar que el usuario tenga acceso al ticket
        if not Ticket.objects.filter(pk=pk).filter(query_conditions).exists():
            messages.error(request, 'No tienes permisos para editar este ticket.')
            return redirect('ticket_list')
        
        FormClass = UserTicketEditForm
    
    if request.method == 'POST':
        form = FormClass(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket actualizado exitosamente.')
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = FormClass(instance=ticket)
    
    context = {
        'form': form, 
        'ticket': ticket,
        'is_agent': is_agent(request.user),
        'user_role': get_user_role(request.user),
    }
    return render(request, 'tickets/ticket_edit.html', context)

@login_required
def ticket_delete_view(request, pk):
    """Vista para eliminar un ticket"""
    if is_agent(request.user):
        # Los agentes pueden eliminar cualquier ticket
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        # Los usuarios solo pueden eliminar sus propios tickets
        ticket = get_object_or_404(Ticket, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Ticket eliminado exitosamente.')
        return redirect('ticket_list')
    
    context = {
        'ticket': ticket,
        'is_agent': is_agent(request.user),
        'user_role': get_user_role(request.user),
    }
    return render(request, 'tickets/ticket_delete.html', context)


@login_required
def ticket_approve_view(request, pk):
    """Vista para aprobar/desaprobar un ticket"""
    # Verificar acceso al ticket
    if is_agent(request.user):
        # Los agentes pueden aprobar cualquier ticket
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        # Los usuarios pueden aprobar tickets donde están involucrados
        user_company = getattr(request.user.profile, 'company', None) if hasattr(request.user, 'profile') else None
        user_projects = Project.objects.filter(assigned_users=request.user)
        
        query_conditions = Q(created_by=request.user)
        
        if user_projects.exists():
            query_conditions |= Q(project__in=user_projects)
        
        if user_company:
            query_conditions |= Q(company=user_company)
        
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Verificar que el usuario tenga acceso al ticket
        if not Ticket.objects.filter(pk=pk).filter(query_conditions).exists():
            messages.error(request, 'No tienes permisos para aprobar este ticket.')
            return redirect('ticket_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            if not ticket.is_approved:
                ticket.approve_ticket(request.user)
                messages.success(request, f'Ticket #{ticket.ticket_number} aprobado exitosamente.')
            else:
                messages.info(request, 'Este ticket ya estaba aprobado.')
        
        elif action == 'unapprove':
            if ticket.is_approved:
                ticket.unapprove_ticket()
                messages.success(request, f'Aprobación del ticket #{ticket.ticket_number} removida.')
            else:
                messages.info(request, 'Este ticket no estaba aprobado.')
        
        return redirect('ticket_detail', pk=ticket.pk)
    
    # Si no es POST, redirigir al detalle del ticket
    return redirect('ticket_detail', pk=ticket.pk)

@login_required
def logout_view(request):
    """Vista personalizada para logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')

# ========== VISTAS DE GESTIÓN DE USUARIOS ==========

def agent_required(user):
    """Decorador para verificar si el usuario es agente"""
    return is_agent(user)

@login_required
@user_passes_test(agent_required, login_url='dashboard')
def user_management_view(request):
    """Vista para listar todos los usuarios (solo para agentes)"""
    users = User.objects.select_related('profile').prefetch_related('groups').all().order_by('username')
    
    # Filtros
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    
    if role_filter:
        if role_filter == 'agents':
            users = users.filter(groups__name='Agentes')
        elif role_filter == 'users':
            users = users.filter(groups__name='Usuarios')
    
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Agregar información de actividad actual para cada usuario
    for user in users:
        # Buscar si tiene una jornada activa (sin fecha de salida)
        current_entry = TimeEntry.objects.filter(
            user=user,
            fecha_salida__isnull=True
        ).select_related('project', 'ticket', 'work_order').first()
        
        user.current_entry = current_entry
        user.is_working = current_entry is not None
        
        # Calcular estadísticas de tiempo del usuario de manera simple
        from django.utils import timezone
        from datetime import timedelta
        
        # Tiempo total trabajado
        completed_entries = TimeEntry.objects.filter(
            user=user,
            fecha_salida__isnull=False
        )
        
        total_seconds = 0
        for entry in completed_entries:
            duration = entry.fecha_salida - entry.fecha_entrada
            total_seconds += duration.total_seconds()
        
        user.total_hours = round(total_seconds / 3600, 1)
        
        # Tiempo trabajado este mes
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_entries = TimeEntry.objects.filter(
            user=user,
            fecha_entrada__gte=start_of_month,
            fecha_salida__isnull=False
        )
        
        month_seconds = 0
        for entry in month_entries:
            duration = entry.fecha_salida - entry.fecha_entrada
            month_seconds += duration.total_seconds()
        
        user.month_hours = round(month_seconds / 3600, 1)
        
        # Tiempo trabajado esta semana
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        week_entries = TimeEntry.objects.filter(
            user=user,
            fecha_entrada__gte=start_of_week,
            fecha_salida__isnull=False
        )
        
        week_seconds = 0
        for entry in week_entries:
            duration = entry.fecha_salida - entry.fecha_entrada
            week_seconds += duration.total_seconds()
        
        user.week_hours = round(week_seconds / 3600, 1)
        
        # Tiempo trabajado hoy
        today = now.date()
        today_entries = TimeEntry.objects.filter(
            user=user,
            fecha_entrada__date=today,
            fecha_salida__isnull=False
        )
        
        today_seconds = 0
        for entry in today_entries:
            duration = entry.fecha_salida - entry.fecha_entrada
            today_seconds += duration.total_seconds()
        
        user.today_hours = round(today_seconds / 3600, 1)
    
    # Paginación
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'tickets/user_management.html', context)

@login_required
@user_passes_test(agent_required, login_url='dashboard')
def user_create_view(request):
    """Vista para crear nuevos usuarios (solo para agentes)"""
    if request.method == 'POST':
        form = UserManagementForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            messages.success(request, f'Usuario "{user.username}" creado exitosamente como {role[:-1]}.')
            return redirect('user_management')
    else:
        form = UserManagementForm()
    
    return render(request, 'tickets/user_create.html', {'form': form})

@login_required
@user_passes_test(agent_required, login_url='dashboard')
def user_edit_view(request, user_id):
    """Vista para editar usuarios existentes (solo para agentes)"""
    user_to_edit = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            user = form.save()
            
            # Actualizar rol del usuario
            new_role = form.cleaned_data['role']
            user.groups.clear()  # Remover todos los grupos
            try:
                group = Group.objects.get(name=new_role)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
            
            messages.success(request, f'Usuario "{user.username}" actualizado exitosamente.')
            return redirect('user_management')
    else:
        form = UserEditForm(instance=user_to_edit)
    
    context = {
        'form': form,
        'user_to_edit': user_to_edit,
    }
    return render(request, 'tickets/user_edit.html', context)

@login_required
@user_passes_test(agent_required, login_url='dashboard')
def user_toggle_status_view(request, user_id):
    """Vista para activar/desactivar usuarios (solo para agentes)"""
    user_to_toggle = get_object_or_404(User, pk=user_id)
    
    if user_to_toggle == request.user:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
    else:
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        
        status = "activado" if user_to_toggle.is_active else "desactivado"
        messages.success(request, f'Usuario "{user_to_toggle.username}" {status} exitosamente.')
    
    return redirect('user_management')


@login_required
def download_attachment_view(request, attachment_id):
    """Vista para descargar adjuntos"""
    attachment = get_object_or_404(TicketAttachment, pk=attachment_id)
    
    # Verificar permisos
    if is_agent(request.user) or attachment.ticket.created_by == request.user:
        if attachment.file:
            try:
                with open(attachment.file.path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachment; filename="{attachment.original_filename}"'
                    return response
            except FileNotFoundError:
                messages.error(request, 'El archivo no se encontró en el servidor.')
        else:
            messages.error(request, 'No hay archivo asociado.')
    else:
        messages.error(request, 'No tienes permisos para descargar este archivo.')
    
    return redirect('ticket_detail', pk=attachment.ticket.pk)


@login_required
def delete_attachment_view(request, attachment_id):
    """Vista para eliminar adjuntos"""
    attachment = get_object_or_404(TicketAttachment, pk=attachment_id)
    ticket_pk = attachment.ticket.pk
    
    # Verificar permisos (solo el que subió el archivo o agentes pueden eliminarlo)
    if is_agent(request.user) or attachment.uploaded_by == request.user:
        attachment.delete()
        messages.success(request, 'Adjunto eliminado exitosamente.')
    else:
        messages.error(request, 'No tienes permisos para eliminar este archivo.')
    
    return redirect('ticket_detail', pk=ticket_pk)


@login_required
@user_passes_test(agent_required, login_url='dashboard')
def unassign_ticket_view(request, pk):
    """Vista para que los agentes desasignen tickets"""
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.assigned_to = None
    ticket.save()
    messages.success(request, f'Ticket #{ticket.pk} desasignado exitosamente.')
    return redirect('ticket_detail', pk=pk)


# ================================
# VISTAS PARA GESTIÓN DE CATEGORÍAS
# ================================

@login_required
@user_passes_test(is_agent)
def category_list_view(request):
    """Vista para listar todas las categorías (solo agentes)"""
    categories = Category.objects.all().order_by('name')
    
    # Agregar contador de tickets por categoría
    for category in categories:
        category.ticket_count = category.tickets.count()
    
    context = {
        'categories': categories,
        'page_title': 'Gestión de Categorías'
    }
    return render(request, 'tickets/category_list.html', context)


@login_required
@user_passes_test(is_agent)
def category_create_view(request):
    """Vista para crear una nueva categoría (solo agentes)"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Categoría',
        'form_title': 'Nueva Categoría'
    }
    return render(request, 'tickets/category_form.html', context)


@login_required
@user_passes_test(is_agent)
def category_edit_view(request, pk):
    """Vista para editar una categoría existente (solo agentes)"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" actualizada exitosamente.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'page_title': 'Editar Categoría',
        'form_title': f'Editar: {category.name}'
    }
    return render(request, 'tickets/category_form.html', context)


@login_required
@user_passes_test(is_agent)
def category_delete_view(request, pk):
    """Vista para eliminar una categoría (solo agentes)"""
    category = get_object_or_404(Category, pk=pk)
    ticket_count = category.tickets.count()
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Categoría "{category_name}" eliminada exitosamente.')
        return redirect('category_list')
    
    context = {
        'category': category,
        'ticket_count': ticket_count,
        'page_title': 'Eliminar Categoría'
    }
    return render(request, 'tickets/category_delete.html', context)


@login_required
@user_passes_test(is_agent)
def category_detail_view(request, pk):
    """Vista para ver detalles de una categoría y sus tickets (solo agentes)"""
    category = get_object_or_404(Category, pk=pk)
    tickets = category.tickets.all().order_by('-created_at')
    
    # Paginación de tickets
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'tickets': page_obj,
        'ticket_count': tickets.count(),
        'page_title': f'Categoría: {category.name}'
    }
    return render(request, 'tickets/category_detail.html', context)


def public_ticket_view(request, token):
    """Vista pública para mostrar un ticket mediante su token único"""
    try:
        ticket = get_object_or_404(Ticket, public_share_token=token, is_public_shareable=True)
    except:
        # Si el ticket no existe o no está habilitado para compartir
        context = {
            'error_message': 'El enlace del ticket no es válido o ha expirado.',
            'error_type': 'not_found'
        }
        return render(request, 'tickets/public_ticket.html', context, status=404)
    
    # Obtener comentarios del ticket
    comments = ticket.comments.all().order_by('created_at')
    
    # Obtener adjuntos del ticket
    attachments = ticket.attachments.all().order_by('-uploaded_at')
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'attachments': attachments,
        'page_title': f'Ticket Público: {ticket.ticket_number}',
    }
    return render(request, 'tickets/public_ticket.html', context)


@login_required
def user_profile_view(request):
    """Vista para mostrar y actualizar el perfil del usuario"""
    from . import utils
    
    # Obtener o crear el perfil del usuario
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Asegurar que el perfil tenga un token público
    if not profile.public_token:
        import uuid
        profile.public_token = uuid.uuid4()
        profile.save()
    
    # Importar formularios aquí para evitar importación circular
    from .forms import UserProfileForm, CustomPasswordChangeForm
    
    profile_form = UserProfileForm(instance=profile, user=request.user)
    password_form = CustomPasswordChangeForm(request.user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            # Actualizar perfil
            profile_form = UserProfileForm(
                request.POST, 
                instance=profile, 
                user=request.user
            )
            if profile_form.is_valid():
                profile_form.save(user=request.user)
                messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
                return redirect('user_profile')
        
        elif 'update_contact_form_toggle' in request.POST:
            # Actualizar solo el toggle del formulario de contacto
            enable_form = request.POST.get('enable_public_contact_form') == 'true'
            profile.enable_public_contact_form = enable_form
            profile.save()
            return JsonResponse({'success': True})
        
        elif 'change_password' in request.POST:
            # Cambiar contraseña
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)  # Mantener la sesión activa
                messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
                return redirect('user_profile')
        
        elif 'regenerate_token' in request.POST:
            # Regenerar token público
            new_token = profile.regenerate_token()
            messages.success(request, 'Tu token de acceso público ha sido regenerado.')
            return redirect('user_profile')
    
    # Construir URL pública para tareas
    if request.is_secure():
        protocol = 'https'
    else:
        protocol = 'http'
    
    public_task_url = f"{protocol}://{request.get_host()}/public/tasks/{profile.public_token}/"
    
    # Construir URL pública para formulario de contacto
    public_contact_form_url = None
    contact_form_stats = None
    if profile.enable_public_contact_form:
        public_contact_form_url = f"{protocol}://{request.get_host()}/contact/{profile.public_token}/"
        
        # Calcular estadísticas de formularios de contacto
        from .models import ContactFormSubmission
        submissions = ContactFormSubmission.objects.filter(submitted_by_user=request.user)
        contact_form_stats = {
            'pending': submissions.filter(status='pending').count(),
            'approved': submissions.filter(status='approved').count(),
            'rejected': submissions.filter(status='rejected').count(),
            'company_created': submissions.filter(status='company_created').count(),
            'total': submissions.count(),
        }
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_profile': profile,
        'public_task_url': public_task_url,
        'public_contact_form_url': public_contact_form_url,
        'contact_form_stats': contact_form_stats,
        'is_agent': utils.is_agent(request.user),
        'page_title': 'Mi Perfil'
    }
    return render(request, 'tickets/user_profile.html', context)


# =====================================
# VIEWS PARA GESTIÓN DE NOTAS INTERNAS
# =====================================

@login_required
@user_passes_test(is_agent, login_url='dashboard')
def notes_list_view(request):
    """Lista todas las notas internas (solo para agentes)"""
    
    # Obtener parámetros de filtro
    search_query = request.GET.get('search', '')
    user_filter = request.GET.get('user', '')
    privacy_filter = request.GET.get('privacy', '')
    
    # Base queryset
    notes = UserNote.objects.select_related('user', 'created_by').prefetch_related('tickets')
    
    # Aplicar filtros
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if user_filter:
        notes = notes.filter(user_id=user_filter)
    
    if privacy_filter == 'private':
        notes = notes.filter(is_private=True)
    elif privacy_filter == 'public':
        notes = notes.filter(is_private=False)
    
    # Paginación
    paginator = Paginator(notes, 15)  # 15 notas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener lista de usuarios para el filtro
    users_with_notes = User.objects.filter(notes__isnull=False).distinct().order_by('username')
    
    context = {
        'page_obj': page_obj,
        'users_with_notes': users_with_notes,
        'search_query': search_query,
        'user_filter': user_filter,
        'privacy_filter': privacy_filter,
        'page_title': 'Notas Internas'
    }
    return render(request, 'tickets/notes_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def note_detail_view(request, note_id):
    """Vista detallada de una nota (solo para agentes)"""
    
    note = get_object_or_404(UserNote, id=note_id)
    
    # Verificar permisos
    if not note.can_view(request.user):
        messages.error(request, 'No tienes permisos para ver esta nota.')
        return redirect('notes_list')
    
    context = {
        'note': note,
        'page_title': f'Nota: {note.title}'
    }
    return render(request, 'tickets/note_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def note_create_view(request):
    """Crear nueva nota interna (solo para agentes)"""
    
    if request.method == 'POST':
        form = UserNoteForm(request.POST, current_user=request.user)
        if form.is_valid():
            note = form.save(created_by=request.user)
            messages.success(request, f'Nota "{note.title}" creada exitosamente.')
            return redirect('note_detail', note_id=note.id)
    else:
        form = UserNoteForm(current_user=request.user)
        
        # Si se pasa un usuario por parámetro, preseleccionarlo
        user_id = request.GET.get('user')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                form.fields['user'].initial = user
                # Cargar tickets del usuario seleccionado
                form.fields['tickets'].queryset = Ticket.objects.filter(
                    created_by=user
                ).order_by('-created_at')
            except User.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'page_title': 'Crear Nota Interna'
    }
    return render(request, 'tickets/note_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def note_edit_view(request, note_id):
    """Editar nota interna existente (solo para agentes)"""
    
    note = get_object_or_404(UserNote, id=note_id)
    
    # Verificar permisos
    if not note.can_edit(request.user):
        messages.error(request, 'No tienes permisos para editar esta nota.')
        return redirect('note_detail', note_id=note.id)
    
    if request.method == 'POST':
        form = UserNoteForm(request.POST, instance=note, current_user=request.user)
        if form.is_valid():
            note = form.save()
            messages.success(request, f'Nota "{note.title}" actualizada exitosamente.')
            return redirect('note_detail', note_id=note.id)
    else:
        form = UserNoteForm(instance=note, current_user=request.user)
    
    context = {
        'form': form,
        'note': note,
        'page_title': f'Editar Nota: {note.title}'
    }
    return render(request, 'tickets/note_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def note_delete_view(request, note_id):
    """Eliminar nota interna (solo para agentes)"""
    
    note = get_object_or_404(UserNote, id=note_id)
    
    # Verificar permisos
    if not note.can_delete(request.user):
        messages.error(request, 'No tienes permisos para eliminar esta nota.')
        return redirect('note_detail', note_id=note.id)
    
    if request.method == 'POST':
        note_title = note.title
        note.delete()
        messages.success(request, f'Nota "{note_title}" eliminada exitosamente.')
        return redirect('notes_list')
    
    context = {
        'note': note,
        'page_title': f'Eliminar Nota: {note.title}'
    }
    return render(request, 'tickets/note_delete.html', context)


@login_required
def user_notes_view(request, user_id=None):
    """Vista de notas asociadas a un usuario específico"""
    
    # Si no se proporciona user_id, usar el usuario actual
    if user_id is None:
        target_user = request.user
    else:
        target_user = get_object_or_404(User, id=user_id)
    
    # Verificar permisos
    can_view_notes = False
    if is_agent(request.user):
        # Los agentes pueden ver notas de cualquier usuario
        can_view_notes = True
        notes = UserNote.objects.filter(user=target_user)
    elif request.user == target_user:
        # Los usuarios pueden ver sus propias notas (solo las no privadas)
        can_view_notes = True
        notes = UserNote.objects.filter(user=target_user, is_private=False)
    else:
        # Otros usuarios no pueden ver las notas
        messages.error(request, 'No tienes permisos para ver estas notas.')
        return redirect('dashboard')
    
    if not can_view_notes:
        messages.error(request, 'No tienes permisos para ver estas notas.')
        return redirect('dashboard')
    
    # Ordenar por fecha de creación descendente
    notes = notes.select_related('created_by').prefetch_related('tickets').order_by('-created_at')
    
    # Paginación
    paginator = Paginator(notes, 10)  # 10 notas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'target_user': target_user,
        'page_obj': page_obj,
        'is_own_notes': request.user == target_user,
        'can_create_notes': is_agent(request.user),
        'page_title': f'Notas de {target_user.get_full_name() or target_user.username}'
    }
    return render(request, 'tickets/user_notes.html', context)


# =====================================
# API PARA OBTENER TICKETS DE USUARIO
# =====================================

@login_required
@user_passes_test(is_agent, login_url='dashboard')
def api_user_tickets(request, user_id):
    """API para obtener tickets de un usuario específico (solo para agentes)"""
    
    try:
        user = User.objects.get(id=user_id)
        tickets = Ticket.objects.filter(created_by=user).order_by('-created_at')
        
        tickets_data = [
            {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'title': ticket.title,
                'status': ticket.get_status_display(),
                'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for ticket in tickets
        ]
        
        return JsonResponse({
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name()
            },
            'tickets': tickets_data
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =======================================
# VISTAS PARA CONTROL DE HORARIO
# =======================================

@login_required
@user_passes_test(is_agent, login_url='dashboard')
def time_clock_view(request):
    """Vista principal del control de horario para agentes"""
    
    # Obtener registro activo del usuario
    active_entry = TimeEntry.get_active_entry(request.user)
    
    # Obtener registros recientes (última semana)
    from datetime import timedelta
    # Calcular el inicio de la semana actual (lunes)
    now = timezone.now()
    start_week = now - timedelta(days=now.weekday())
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    recent_entries = TimeEntry.objects.filter(
        user=request.user,
        fecha_entrada__gte=start_week
    ).order_by('-fecha_entrada')[:10]
    
    # Calcular estadísticas de la semana actual
    week_entries = TimeEntry.objects.filter(
        user=request.user,
        fecha_entrada__gte=start_week,
        fecha_salida__isnull=False  # Solo entradas completadas
    )
    total_minutos = sum(entry.duracion_trabajada for entry in week_entries)
    total_horas = round(total_minutos / 60, 2)
    
    context = {
        'active_entry': active_entry,
        'recent_entries': recent_entries,
        'total_horas_semana': total_horas,
        'can_start': not active_entry,
        'can_end': bool(active_entry),
        'page_title': 'Control de Horario'
    }
    
    return render(request, 'tickets/time_clock.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def time_start_work(request):
    """Iniciar jornada laboral"""
    
    # Verificar que no hay una jornada activa
    active_entry = TimeEntry.get_active_entry(request.user)
    if active_entry:
        messages.warning(request, 'Ya tienes una jornada activa desde las ' + 
                        active_entry.fecha_entrada.strftime('%H:%M'))
        return redirect('time_clock')
    
    if request.method == 'POST':
        form = TimeEntryStartForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                project = form.cleaned_data.get('project')
                ticket = form.cleaned_data.get('ticket')
                work_order = form.cleaned_data.get('work_order')
                task = form.cleaned_data.get('task')
                notas = form.cleaned_data.get('notas_entrada', '')
                
                entry = TimeEntry.create_entry(
                    user=request.user,
                    project=project,
                    ticket=ticket,
                    work_order=work_order,
                    task=task,
                    notas_entrada=notas
                )
                
                # Mensaje personalizado según los elementos seleccionados
                message_parts = [f'¡Jornada iniciada a las {entry.fecha_entrada.strftime("%H:%M")}']
                if project:
                    message_parts.append(f'en el proyecto "{project.name}"')
                if ticket:
                    message_parts.append(f'trabajando en el ticket "{ticket.ticket_number}"')
                if work_order:
                    message_parts.append(f'en la orden "{work_order.order_number}"')
                if task:
                    message_parts.append(f'en la tarea "{task.title}"')
                
                message = ' '.join(message_parts) + '!'
                messages.success(request, message)
                    
                return redirect('time_clock')
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('time_clock')
    else:
        form = TimeEntryStartForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Iniciar Jornada'
    }
    return render(request, 'tickets/time_start.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def time_end_work(request):
    """Finalizar jornada laboral"""
    
    # Verificar que hay una jornada activa
    active_entry = TimeEntry.get_active_entry(request.user)
    if not active_entry:
        messages.error(request, 'No tienes una jornada activa para finalizar.')
        return redirect('time_clock')
    
    if request.method == 'POST':
        form = TimeEntryEndForm(request.POST)
        if form.is_valid():
            try:
                notas_salida = form.cleaned_data.get('notas_salida', '')
                active_entry.finalizar_jornada(notas_salida)
                
                duracion = active_entry.duracion_formateada
                messages.success(request, 
                    f'¡Jornada finalizada! Duración total: {duracion} horas')
                return redirect('time_clock')
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('time_clock')
    else:
        form = TimeEntryEndForm()
    
    context = {
        'form': form,
        'active_entry': active_entry,
        'page_title': 'Finalizar Jornada'
    }
    return render(request, 'tickets/time_end.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def time_entries_list(request):
    """Lista de registros de horario del empleado"""
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Base queryset - solo registros del usuario actual
    entries = TimeEntry.objects.filter(user=request.user)
    
    # Aplicar filtros de fecha
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            entries = entries.filter(fecha_entrada__date__gte=fecha_desde_dt)
        except ValueError:
            messages.warning(request, 'Formato de fecha inválido')
    
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            entries = entries.filter(fecha_entrada__date__lte=fecha_hasta_dt)
        except ValueError:
            messages.warning(request, 'Formato de fecha inválido')
    
    # Ordenar por fecha descendente
    entries = entries.order_by('-fecha_entrada')
    
    # Paginación
    paginator = Paginator(entries, 20)  # 20 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular totales
    if page_obj.object_list:
        total_minutos = sum(entry.duracion_trabajada for entry in entries if entry.fecha_salida)
        total_horas = round(total_minutos / 60, 2)
        total_dias = entries.filter(fecha_salida__isnull=False).count()
    else:
        total_horas = 0
        total_dias = 0
    
    context = {
        'page_obj': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_horas': total_horas,
        'total_dias': total_dias,
        'page_title': 'Mis Registros de Horario'
    }
    
    return render(request, 'tickets/time_entries_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def time_entry_detail(request, entry_id):
    """Vista detallada de un registro de horario"""
    
    entry = get_object_or_404(TimeEntry, id=entry_id)
    
    # Verificar permisos - solo el propietario puede ver sus registros
    if not entry.can_view(request.user):
        messages.error(request, 'No tienes permisos para ver este registro.')
        return redirect('time_entries_list')
    
    context = {
        'entry': entry,
        'page_title': f'Registro del {entry.fecha_entrada.strftime("%d/%m/%Y")}'
    }
    
    return render(request, 'tickets/time_entry_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def time_entry_edit(request, entry_id):
    """Editar notas de un registro de horario"""
    
    entry = get_object_or_404(TimeEntry, id=entry_id)
    
    # Verificar permisos
    if not entry.can_edit(request.user):
        messages.error(request, 'No tienes permisos para editar este registro.')
        return redirect('time_entry_detail', entry_id=entry.id)
    
    if request.method == 'POST':
        form = TimeEntryEditForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro actualizado exitosamente.')
            return redirect('time_entry_detail', entry_id=entry.id)
    else:
        form = TimeEntryEditForm(instance=entry, user=request.user)
    
    context = {
        'form': form,
        'entry': entry,
        'page_title': f'Editar Registro del {entry.fecha_entrada.strftime("%d/%m/%Y")}'
    }
    
    return render(request, 'tickets/time_entry_edit.html', context)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def ajax_current_time_status(request):
    """API AJAX para obtener el estado actual del tiempo trabajado"""
    
    active_entry = TimeEntry.get_active_entry(request.user)
    
    if active_entry:
        return JsonResponse({
            'is_working': True,
            'start_time': active_entry.fecha_entrada.strftime('%H:%M'),
            'duration': active_entry.duracion_formateada,
            'minutes_worked': active_entry.duracion_trabajada
        })
    else:
        return JsonResponse({
            'is_working': False,
            'start_time': None,
            'duration': '00:00',
            'minutes_worked': 0
        })


# ===========================================
# VISTAS DE GESTIÓN DE PROYECTOS
# ===========================================

@login_required
@user_passes_test(is_agent, login_url='ticket_list')
def project_list(request):
    """Vista para listar todos los proyectos (solo agentes)"""
    projects = Project.objects.all()
    
    # Búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filtro por estado
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Paginación
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener configuración del sistema
    from tickets.models import SystemConfiguration
    system_config = SystemConfiguration.get_config()
    
    context = {
        'page_title': 'Gestión de Proyectos',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'project_status_choices': Project.STATUS_CHOICES,
        'system_config': system_config,
    }
    
    return render(request, 'tickets/project_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='ticket_list')
def project_create(request):
    """Vista para crear un nuevo proyecto (solo agentes)"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(created_by=request.user)
            messages.success(request, f'Proyecto "{project.name}" creado exitosamente.')
            return redirect('project_list')
    else:
        form = ProjectForm()
    
    context = {
        'page_title': 'Crear Nuevo Proyecto',
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'tickets/project_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='ticket_list')
def project_edit(request, project_id):
    """Vista para editar un proyecto existente (solo agentes)"""
    project = get_object_or_404(Project, id=project_id)
    
    # Verificar permisos
    if not project.can_edit(request.user):
        messages.error(request, 'No tienes permisos para editar este proyecto.')
        return redirect('project_list')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Proyecto "{project.name}" actualizado exitosamente.')
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'page_title': f'Editar Proyecto: {project.name}',
        'form': form,
        'project': project,
        'action': 'edit'
    }
    
    return render(request, 'tickets/project_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='ticket_list')
def project_detail(request, project_id):
    """Vista para ver detalles de un proyecto"""
    project = get_object_or_404(Project, id=project_id)
    
    # Obtener registros de tiempo de este proyecto
    time_entries = project.time_entries.filter(
        fecha_salida__isnull=False
    ).order_by('-fecha_entrada')[:10]
    
    # Obtener trabajadores activos en este proyecto
    active_workers = project.time_entries.filter(
        fecha_salida__isnull=True
    ).select_related('user')
    
    context = {
        'page_title': f'Proyecto: {project.name}',
        'project': project,
        'time_entries': time_entries,
        'active_workers': active_workers,
        'total_hours': project.get_total_hours(),
        'active_workers_count': project.get_active_workers_count(),
    }
    
    return render(request, 'tickets/project_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='ticket_list')
def project_delete(request, project_id):
    """Vista para eliminar un proyecto (solo agentes)"""
    project = get_object_or_404(Project, id=project_id)
    
    # Verificar permisos
    if not project.can_delete(request.user):
        messages.error(request, 'No tienes permisos para eliminar este proyecto.')
        return redirect('project_list')
    
    # Verificar si hay registros de tiempo asociados
    if project.time_entries.exists():
        messages.error(request, 
            'No se puede eliminar el proyecto porque tiene registros de tiempo asociados. '
            'Considera marcarlo como inactivo en su lugar.')
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Proyecto "{project_name}" eliminado exitosamente.')
        return redirect('project_list')
    
    context = {
        'page_title': f'Eliminar Proyecto: {project.name}',
        'project': project,
    }
    
    return render(request, 'tickets/project_delete.html', context)


@login_required
@user_passes_test(is_agent, login_url='ticket_list')
def project_generate_public_token(request, project_id):
    """Vista para generar o regenerar el token público de un proyecto"""
    project = get_object_or_404(Project, id=project_id)
    
    # Verificar permisos
    if not project.can_edit(request.user):
        messages.error(request, 'No tienes permisos para gestionar este proyecto.')
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        # Generar nuevo token (esto también actualizará uno existente)
        import secrets
        project.public_share_token = secrets.token_urlsafe(32)
        project.save()
        
        messages.success(request, 
            'Enlace público generado exitosamente. '
            'Ahora puedes compartir este proyecto con información básica sin necesidad de iniciar sesión.')
    
    return redirect('project_detail', project_id=project.id)


@login_required
@user_passes_test(is_agent, login_url='dashboard')
def attendance_overview(request):
    """Vista para que los agentes vean la asistencia de todos los empleados"""
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    # Filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    proyecto_id = request.GET.get('proyecto')
    usuario_id = request.GET.get('usuario')
    
    # Si no hay fechas, mostrar los últimos 7 días
    if not fecha_desde:
        fecha_desde = (timezone.now() - timedelta(days=7)).date()
    else:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    
    if not fecha_hasta:
        fecha_hasta = timezone.now().date()
    else:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    
    # Base queryset
    queryset = TimeEntry.objects.select_related('user', 'project').filter(
        fecha_entrada__date__gte=fecha_desde,
        fecha_entrada__date__lte=fecha_hasta
    ).order_by('-fecha_entrada')
    
    # Filtro por proyecto
    if proyecto_id:
        queryset = queryset.filter(project_id=proyecto_id)
    
    # Filtro por usuario
    if usuario_id:
        queryset = queryset.filter(user_id=usuario_id)
    
    # Obtener estadísticas
    total_entries = queryset.count()
    active_entries = queryset.filter(fecha_salida__isnull=True).count()
    
    # Calcular total de horas y promedio
    total_hours = 0
    completed_entries = 0
    completed_hours = 0
    
    for entry in queryset:
        if entry.fecha_salida:
            # Jornada completada
            duration = (entry.fecha_salida - entry.fecha_entrada).total_seconds()
            completed_hours += duration
            completed_entries += 1
        else:
            # Jornada activa - solo para el total
            duration = (timezone.now() - entry.fecha_entrada).total_seconds()
        
        total_hours += duration
    
    total_hours = round(total_hours / 3600, 2)
    
    # Calcular promedio por jornada (solo jornadas completadas)
    if completed_entries > 0:
        avg_hours_per_session = round(completed_hours / 3600 / completed_entries, 2)
    else:
        avg_hours_per_session = 0
    
    # Paginación
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    proyectos = Project.objects.filter(is_active=True).order_by('name')
    usuarios = User.objects.filter(
        groups__name='Agentes'
    ).order_by('first_name', 'username')
    
    context = {
        'page_title': 'Control de Asistencia General',
        'page_obj': page_obj,
        'total_entries': total_entries,
        'active_entries': active_entries,
        'total_hours': total_hours,
        'avg_hours_per_session': avg_hours_per_session,
        'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
        'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
        'proyectos': proyectos,
        'usuarios': usuarios,
        'proyecto_seleccionado': proyecto_id,
        'usuario_seleccionado': usuario_id,
    }
    
    return render(request, 'tickets/attendance_overview.html', context)



# =============================================================================
# VISTAS PARA GESTIÓN DE EMPRESAS (SOLO AGENTES)
# =============================================================================

@login_required
@user_passes_test(is_agent, login_url='/')
def company_list_view(request):
    """Vista para listar todas las empresas"""
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    
    # Filtro base
    queryset = Company.objects.all().order_by('name')
    
    # Aplicar filtros
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_companies = Company.objects.count()
    active_companies = Company.objects.filter(is_active=True).count()
    
    context = {
        'page_title': 'Gestión de Empresas',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_companies': total_companies,
        'active_companies': active_companies,
    }
    
    return render(request, 'tickets/company_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def company_create_view(request):
    """Vista para crear una nueva empresa"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'La empresa "{company.name}" ha sido creada exitosamente.')
            return redirect('company_list')
    else:
        form = CompanyForm()
    
    context = {
        'page_title': 'Crear Nueva Empresa',
        'form': form,
        'is_create': True,
    }
    
    return render(request, 'tickets/company_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def company_detail_view(request, company_id):
    """Vista para ver detalles de una empresa"""
    company = get_object_or_404(Company, id=company_id)
    
    # Estadísticas de la empresa
    total_tickets = company.tickets.count()
    open_tickets = company.tickets.filter(status='open').count()
    total_users = company.users.count()
    active_users = company.users.filter(user__is_active=True).count()
    
    # Tickets recientes
    recent_tickets = company.tickets.select_related(
        'created_by', 'assigned_to', 'category'
    ).order_by('-created_at')[:10]
    
    # Usuarios de la empresa
    company_users = company.users.select_related('user').order_by('user__first_name', 'user__username')
    
    context = {
        'page_title': f'Empresa: {company.name}',
        'company': company,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'total_users': total_users,
        'active_users': active_users,
        'recent_tickets': recent_tickets,
        'company_users': company_users,
    }
    
    return render(request, 'tickets/company_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def company_edit_view(request, company_id):
    """Vista para editar una empresa"""
    company = get_object_or_404(Company, id=company_id)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f'La empresa "{company.name}" ha sido actualizada exitosamente.')
            return redirect('company_detail', company_id=company.id)
    else:
        form = CompanyForm(instance=company)
    
    context = {
        'page_title': f'Editar Empresa: {company.name}',
        'form': form,
        'company': company,
        'is_create': False,
    }
    
    return render(request, 'tickets/company_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def company_delete_view(request, company_id):
    """Vista para eliminar una empresa"""
    company = get_object_or_404(Company, id=company_id)
    
    # Verificar si la empresa tiene tickets o usuarios asociados
    has_tickets = company.tickets.exists()
    has_users = company.users.exists()
    
    if request.method == 'POST':
        if has_tickets or has_users:
            messages.error(
                request, 
                f'No se puede eliminar la empresa "{company.name}" porque tiene tickets o usuarios asociados. '
                'Desactívala en su lugar.'
            )
        else:
            company_name = company.name
            company.delete()
            messages.success(request, f'La empresa "{company_name}" ha sido eliminada exitosamente.')
            return redirect('company_list')
    
    context = {
        'page_title': f'Eliminar Empresa: {company.name}',
        'company': company,
        'has_tickets': has_tickets,
        'has_users': has_users,
    }
    
    return render(request, 'tickets/company_delete.html', context)


# =============================================================================
# VISTAS PARA CONFIGURACIÓN DEL SISTEMA (SOLO AGENTES)
# =============================================================================

@login_required
@user_passes_test(is_agent, login_url='/')
def system_configuration_view(request):
    """Vista para configurar el sistema"""
    config = SystemConfiguration.get_config()
    
    if request.method == 'POST':
        form = SystemConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'La configuración del sistema ha sido actualizada exitosamente.')
            return redirect('system_configuration')
    else:
        form = SystemConfigurationForm(instance=config)
    
    context = {
        'page_title': 'Configuración del Sistema',
        'form': form,
        'config': config,
    }
    
    return render(request, 'tickets/system_configuration.html', context)


# =============================================================================
# VISTAS PARA GESTIÓN DE DOCUMENTOS
# =============================================================================

@login_required
@user_passes_test(is_agent, login_url='/')
def document_list_view(request):
    """Vista para listar todos los documentos"""
    search_query = request.GET.get('search', '').strip()
    company_filter = request.GET.get('company', '')
    tag_filter = request.GET.get('tag', '').strip()
    
    # Filtro base
    queryset = Document.objects.select_related('created_by', 'company').order_by('-created_at')
    
    # Aplicar filtros
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    if company_filter:
        if company_filter == 'none':
            queryset = queryset.filter(company__isnull=True)
        else:
            queryset = queryset.filter(company_id=company_filter)
    
    if tag_filter:
        queryset = queryset.filter(tags__icontains=tag_filter)
    
    # Paginación
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    companies = Company.objects.filter(is_active=True).order_by('name')
    
    # Obtener todas las etiquetas únicas
    all_tags = set()
    for doc in Document.objects.exclude(tags=''):
        for tag in doc.get_tags_list():
            all_tags.add(tag)
    all_tags = sorted(list(all_tags))
    
    context = {
        'page_title': 'Gestión de Documentos',
        'page_obj': page_obj,
        'search_query': search_query,
        'company_filter': company_filter,
        'tag_filter': tag_filter,
        'companies': companies,
        'all_tags': all_tags,
        'total_documents': Document.objects.count(),
    }
    
    return render(request, 'tickets/document_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def document_create_view(request):
    """Vista para crear un nuevo documento"""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.created_by = request.user
            document.save()
            messages.success(request, f'El documento "{document.title}" ha sido creado exitosamente.')
            return redirect('document_list')
    else:
        form = DocumentForm()
    
    context = {
        'page_title': 'Subir Nuevo Documento',
        'form': form,
        'is_create': True,
    }
    
    return render(request, 'tickets/document_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def document_detail_view(request, document_id):
    """Vista para ver detalles de un documento"""
    document = get_object_or_404(Document, id=document_id)
    
    context = {
        'page_title': f'Documento: {document.title}',
        'document': document,
    }
    
    return render(request, 'tickets/document_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def document_edit_view(request, document_id):
    """Vista para editar un documento"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, f'El documento "{document.title}" ha sido actualizado exitosamente.')
            return redirect('document_detail', document_id=document.id)
    else:
        form = DocumentForm(instance=document)
    
    context = {
        'page_title': f'Editar Documento: {document.title}',
        'form': form,
        'document': document,
        'is_create': False,
    }
    
    return render(request, 'tickets/document_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def document_delete_view(request, document_id):
    """Vista para eliminar un documento"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        document_title = document.title
        # Eliminar archivo físico
        if document.file:
            document.file.delete(save=False)
        document.delete()
        messages.success(request, f'El documento "{document_title}" ha sido eliminado exitosamente.')
        return redirect('document_list')
    
    context = {
        'page_title': f'Eliminar Documento: {document.title}',
        'document': document,
    }
    
    return render(request, 'tickets/document_delete.html', context)


def document_public_view(request, token):
    """Vista pública para compartir documentos sin autenticación"""
    document = get_object_or_404(Document, public_share_token=token, is_public=True)
    
    context = {
        'document': document,
        'page_title': f'Documento Compartido: {document.title}',
    }
    
    return render(request, 'tickets/document_public.html', context)


def document_download_view(request, token):
    """Vista para descargar documentos públicos"""
    document = get_object_or_404(Document, public_share_token=token, is_public=True)
    
    # Incrementar contador de descargas
    document.increment_download_count()
    
    # Servir el archivo
    from django.http import HttpResponse, Http404
    import os
    
    if not document.file or not os.path.exists(document.file.path):
        raise Http404("Archivo no encontrado")
    
    response = HttpResponse(
        document.file.read(),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
    
    return response


@login_required
@user_passes_test(is_agent, login_url='/')
def document_download_private_view(request, document_id):
    """Vista para descargar documentos con autenticación"""
    document = get_object_or_404(Document, id=document_id)
    
    # Incrementar contador de descargas
    document.increment_download_count()
    
    # Servir el archivo
    from django.http import HttpResponse, Http404
    import os
    
    if not document.file or not os.path.exists(document.file.path):
        raise Http404("Archivo no encontrado")
    
    response = HttpResponse(
        document.file.read(),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
    
    return response


# VIEWS PARA GESTIÓN DE URLs CON CREDENCIALES

@login_required
@user_passes_test(is_agent, login_url='/')
def url_manager_list_view(request):
    """Lista todas las URLs gestionadas (solo para agentes)"""
    from .models import UrlManager
    from .forms import UrlManagerFilterForm
    from django.db.models import Q
    
    # Obtener filtros
    form = UrlManagerFilterForm(request.GET)
    urls = UrlManager.objects.all()
    
    # Aplicar filtros
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        is_active = form.cleaned_data.get('is_active')
        
        if search:
                       urls = urls.filter(
                Q(title__icontains=search) |
                Q(url__icontains=search) |
                Q(description__icontains=search) |
                Q(username__icontains=search)
            )
        
        if category:
            urls = urls.filter(category__icontains=category)
        
        if is_active:
            urls = urls.filter(is_active=is_active == 'True')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(urls, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener categorías únicas para el filtro
    categories = UrlManager.objects.values_list('category', flat=True).distinct().exclude(category__isnull=True).exclude(category='')
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'categories': categories,
        'search_query': form.cleaned_data.get('search', '') if form.is_valid() else '',
        'category_filter': form.cleaned_data.get('category', '') if form.is_valid() else '',
        'status_filter': form.cleaned_data.get('is_active', '') if form.is_valid() else '',
        'page_title': 'Gestión de URLs'
    }
    
    return render(request, 'tickets/url_manager_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def url_manager_create_view(request):
    """Crear nueva URL gestionada (solo para agentes)"""
    from .models import UrlManager
    from .forms import UrlManagerForm
    
    if request.method == 'POST':
        form = UrlManagerForm(request.POST)
        if form.is_valid():
            url_manager = form.save(commit=False)
            url_manager.created_by = request.user
            url_manager.save()
            
            messages.success(request, f'URL "{url_manager.title}" creada exitosamente.')
            return redirect('url_manager_list')
    else:
        form = UrlManagerForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Nueva URL',
        'action': 'Crear'
    }
    
    return render(request, 'tickets/url_manager_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def url_manager_edit_view(request, url_id):
    """Editar URL gestionada (solo para agentes)"""
    from .models import UrlManager
    from .forms import UrlManagerForm
    
    url_manager = get_object_or_404(UrlManager, id=url_id)
    
    if request.method == 'POST':
        form = UrlManagerForm(request.POST, instance=url_manager)
        if form.is_valid():
            form.save()
            messages.success(request, f'URL "{url_manager.title}" actualizada exitosamente.')
            return redirect('url_manager_list')
    else:
        form = UrlManagerForm(instance=url_manager)
    
    context = {
        'form': form,
        'url_manager': url_manager,
        'page_title': f'Editar URL: {url_manager.title}',
        'action': 'Actualizar'
    }
    
    return render(request, 'tickets/url_manager_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def url_manager_detail_view(request, url_id):
    """Ver detalles de una URL gestionada (solo para agentes)"""
    from .models import UrlManager
    
    url_manager = get_object_or_404(UrlManager, id=url_id)
    
    # Marcar como accedida
    url_manager.mark_accessed()
    
    context = {
        'url_manager': url_manager,
        'page_title': f'Detalles: {url_manager.title}'
    }
    
    return render(request, 'tickets/url_manager_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def url_manager_delete_view(request, url_id):
    """Eliminar URL gestionada (solo para agentes)"""
    from .models import UrlManager
    
    url_manager = get_object_or_404(UrlManager, id=url_id)
    
    if request.method == 'POST':
        title = url_manager.title
        url_manager.delete()
        messages.success(request, f'URL "{title}" eliminada exitosamente.')
        return redirect('url_manager_list')
    
    context = {
        'url_manager': url_manager,
        'page_title': f'Eliminar URL: {url_manager.title}'
    }
    
    return render(request, 'tickets/url_manager_delete.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def url_manager_password_view(request, url_id):
    """AJAX endpoint para obtener la contraseña desencriptada"""
    from .models import UrlManager
    from django.http import JsonResponse
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Solicitando contraseña para URL ID: {url_id}")
    
    try:
        url_manager = get_object_or_404(UrlManager, id=url_id)
        logger.info(f"URL encontrada: {url_manager.title}")
        
        password = url_manager.get_password()
        logger.info(f"Contraseña obtenida exitosamente")
        
        return JsonResponse({
            'success': True,
            'password': password
        })
    except Exception as e:
        logger.error(f"Error al obtener contraseña: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ===========================================
# VISTAS PARA ÓRDENAS DE TRABAJO
# ===========================================

@login_required
@user_passes_test(is_agent, login_url='/')
def work_order_list_view(request):
    """Vista para listar órdenes de trabajo"""
    # Obtener todas las órdenes de trabajo
    work_orders = WorkOrder.objects.all()
    
    # Aplicar filtros si existen
    form = WorkOrderFilterForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        company = form.cleaned_data.get('company')
        status = form.cleaned_data.get('status')
        priority = form.cleaned_data.get('priority')
        assigned_to = form.cleaned_data.get('assigned_to')
        
        if search:
            work_orders = work_orders.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        if company:
            work_orders = work_orders.filter(company=company)
        
        if status:
            work_orders = work_orders.filter(status=status)
        
        if priority:
            work_orders = work_orders.filter(priority=priority)
        
        if assigned_to:
            work_orders = work_orders.filter(assigned_to=assigned_to)
    
    # Agregar información de permisos a cada orden
    for work_order in work_orders:
        work_order.user_can_edit = work_order.can_edit(request.user)
        work_order.user_can_delete = work_order.can_delete(request.user)
    
    # Paginación
    paginator = Paginator(work_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': form,
        'page_title': 'Órdenes de Trabajo'
    }
    
    return render(request, 'tickets/work_order_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def work_order_create_view(request):
    """Vista para crear nuevas órdenes de trabajo"""
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, request.FILES)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.created_by = request.user
            work_order.save()
            messages.success(request, f'Orden de trabajo "{work_order.title}" creada exitosamente.')
            return redirect('work_order_detail', pk=work_order.pk)
    else:
        form = WorkOrderForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Orden de Trabajo'
    }
    
    return render(request, 'tickets/work_order_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def work_order_detail_view(request, pk):
    """Vista para ver detalles de una orden de trabajo"""
    work_order = get_object_or_404(WorkOrder, pk=pk)
    
    context = {
        'work_order': work_order,
        'attachments': work_order.attachments.all(),
        'page_title': f'Orden: {work_order.order_number}'
    }
    
    return render(request, 'tickets/work_order_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def work_order_edit_view(request, pk):
    """Vista para editar órdenes de trabajo"""
    work_order = get_object_or_404(WorkOrder, pk=pk)
    
    # Verificar permisos
    if not work_order.can_edit(request.user):
        messages.error(request, 'No tienes permisos para editar esta orden de trabajo.')
        return redirect('work_order_detail', pk=work_order.pk)
    
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, request.FILES, instance=work_order)
        if form.is_valid():
            form.save(commit=False)
            messages.success(request, f'Orden de trabajo "{work_order.title}" actualizada exitosamente.')
            return redirect('work_order_detail', pk=work_order.pk)
    else:
        form = WorkOrderForm(instance=work_order)
    
    context = {
        'form': form,
        'work_order': work_order,
        'page_title': f'Editar: {work_order.order_number}'
    }
    
    return render(request, 'tickets/work_order_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def work_order_delete_view(request, pk):
    """Vista para eliminar órdenes de trabajo"""
    work_order = get_object_or_404(WorkOrder, pk=pk)
    
    # Verificar permisos
    if not work_order.can_delete(request.user):
        messages.error(request, 'No puedes eliminar esta orden de trabajo. Solo se pueden eliminar órdenes en estado borrador.')
        return redirect('work_order_detail', pk=work_order.pk)
    
    if request.method == 'POST':
        title = work_order.title
        work_order.delete()
        messages.success(request, f'Orden de trabajo "{title}" eliminada exitosamente.')
        return redirect('work_order_list')
    
    context = {
        'work_order': work_order,
        'page_title': f'Eliminar: {work_order.order_number}'
    }
    
    return render(request, 'tickets/work_order_delete.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def work_order_change_status_view(request, pk):
    """Vista AJAX para cambiar el estado de una orden de trabajo"""
    if request.method == 'POST':
        work_order = get_object_or_404(WorkOrder, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in ['draft', 'accepted', 'finished']:
            old_status = work_order.get_status_display()
            work_order.status = new_status
            
            # Si se marca como terminada, establecer fecha de finalización
            if new_status == 'finished':
                work_order.completed_at = timezone.now()
            else:
                work_order.completed_at = None
            
            work_order.save()
            
            new_status_display = work_order.get_status_display()
            messages.success(request, f'Estado de la orden cambiado de "{old_status}" a "{new_status_display}".')
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado a "{new_status_display}"',
                'new_status': new_status,
                'new_status_display': new_status_display
            })
        
        return JsonResponse({
            'success': False,
            'error': 'Estado inválido'
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def work_order_public_view(request, token):
    """Vista pública para órdenes de trabajo compartidas"""
    work_order = get_object_or_404(WorkOrder, public_share_token=token, is_public=True)
    
    # Manejar aprobación por POST
    if request.method == 'POST' and 'approve_work_order' in request.POST:
        if work_order.status == 'draft':
            work_order.status = 'accepted'
            work_order.save()
            messages.success(request, '¡Orden de trabajo aprobada exitosamente!')
        else:
            messages.info(request, 'Esta orden ya ha sido procesada.')
        
        return redirect('tickets:public_work_order', token=token)
    
    context = {
        'work_order': work_order,
        'attachments': work_order.attachments.all(),
        'page_title': f'Orden: {work_order.order_number}',
        'is_public_view': True
    }
    
    return render(request, 'tickets/work_order_public.html', context)


# ===========================================
# VISTAS PARA REPORTES
# ===========================================

@login_required
@user_passes_test(is_agent, login_url='/')
def daily_report_view(request):
    """Vista para generar reporte de parte diario"""
    
    # Obtener parámetros de fecha
    fecha_desde = request.GET.get('fecha_desde', date.today().strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('fecha_hasta', date.today().strftime('%Y-%m-%d'))
    usuario_id = request.GET.get('usuario')
    
    # Convertir fechas
    try:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        fecha_desde_obj = date.today()
        fecha_hasta_obj = date.today()
        fecha_desde = fecha_desde_obj.strftime('%Y-%m-%d')
        fecha_hasta = fecha_hasta_obj.strftime('%Y-%m-%d')
    
    # Obtener registros de tiempo
    time_entries = TimeEntry.objects.filter(
        fecha_entrada__date__gte=fecha_desde_obj,
        fecha_entrada__date__lte=fecha_hasta_obj
    )
    
    # Filtrar por usuario si se especifica
    usuario_nombre = None
    if usuario_id:
        time_entries = time_entries.filter(user_id=usuario_id)
        try:
            usuario = User.objects.get(id=usuario_id)
            usuario_nombre = usuario.get_full_name() or usuario.username
        except User.DoesNotExist:
            pass
    
    time_entries = time_entries.select_related('user', 'project', 'ticket', 'work_order', 'task').order_by('-fecha_entrada')
    
    # Agregar paginación
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(time_entries, 25)  # 25 registros por página
    page = request.GET.get('page')
    
    try:
        time_entries_page = paginator.page(page)
    except PageNotAnInteger:
        # Si page no es un entero, mostrar la primera página
        time_entries_page = paginator.page(1)
    except EmptyPage:
        # Si page está fuera de rango, mostrar la última página
        time_entries_page = paginator.page(paginator.num_pages)
    
    # Calcular estadísticas (usando el queryset original, no paginado)
    total_entries = time_entries.count()
    entries_in_progress = time_entries.filter(fecha_salida__isnull=True).count()
    
    # Calcular total de horas completadas
    total_hours = 0
    for entry in time_entries:
        if entry.fecha_salida:
            # Calcular duración en horas
            duration = entry.fecha_salida - entry.fecha_entrada
            total_hours += duration.total_seconds() / 3600
    
    # Obtener usuarios únicos
    unique_users = time_entries.values('user').distinct().count()
    
    # Obtener usuarios para el filtro
    usuarios = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
    
    context = {
        'time_entries': time_entries,
        'usuarios': usuarios,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'usuario_seleccionado': usuario_id,
        'usuario_nombre': usuario_nombre,
        'page_title': 'Reporte de Parte Diario',
        'total_entries': total_entries,
        'entries_in_progress': entries_in_progress,
        'total_hours': round(total_hours, 1),
        'unique_users': unique_users,
    }
    
    return render(request, 'tickets/daily_report.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def daily_report_pdf(request):
    """Vista para generar PDF del reporte diario"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import io
    
    # Obtener parámetros
    fecha_desde = request.GET.get('fecha_desde', date.today().strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('fecha_hasta', date.today().strftime('%Y-%m-%d'))
    usuario_id = request.GET.get('usuario')
    
    # Convertir fechas
    try:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        fecha_desde_obj = date.today()
        fecha_hasta_obj = date.today()
    
    # Obtener datos
    time_entries = TimeEntry.objects.filter(
        fecha_entrada__date__gte=fecha_desde_obj,
        fecha_entrada__date__lte=fecha_hasta_obj
    )
    
    if usuario_id:
        time_entries = time_entries.filter(user_id=usuario_id)
        usuario = User.objects.get(id=usuario_id)
        usuario_nombre = f" - {usuario.get_full_name() or usuario.username}"
    else:
        usuario_nombre = " - Todos los usuarios"
    
    time_entries = time_entries.select_related('user', 'project', 'ticket', 'work_order', 'task').order_by('user__username', 'fecha_entrada')
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Contenido del PDF
    story = []
    
    # Título
    title = f"Reporte de Parte Diario{usuario_nombre}"
    story.append(Paragraph(title, title_style))
    
    # Rango de fechas
    if fecha_desde_obj == fecha_hasta_obj:
        periodo = f"Fecha: {fecha_desde_obj.strftime('%d/%m/%Y')}"
    else:
        periodo = f"Período: {fecha_desde_obj.strftime('%d/%m/%Y')} al {fecha_hasta_obj.strftime('%d/%m/%Y')}"
    
    story.append(Paragraph(periodo, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tabla de datos
    data = [['Usuario', 'Fecha', 'Asignación', 'Entrada', 'Salida', 'Duración']]
    
    for entry in time_entries:
        # Construir asignación
        asignacion_parts = []
        if entry.project:
            asignacion_parts.append(f"Proyecto: {entry.project.name}")
        if entry.ticket:
            asignacion_parts.append(f"Ticket: #{entry.ticket.id}")
        if entry.work_order:
            asignacion_parts.append(f"Orden: #{entry.work_order.id}")
        if entry.task:
            asignacion_parts.append(f"Tarea: {entry.task.title}")
        
        asignacion = "\n".join(asignacion_parts) if asignacion_parts else "Sin asignación específica"
        
        # Formatear salida
        salida = entry.fecha_salida.strftime('%H:%M') if entry.fecha_salida else "En progreso"
        
        data.append([
            entry.user.get_full_name() or entry.user.username,
            entry.fecha_entrada.strftime('%d/%m/%Y'),
            asignacion,
            entry.fecha_entrada.strftime('%H:%M'),
            salida,
            entry.duracion_formateada
        ])
    
    # Crear tabla
    table = Table(data, colWidths=[1.5*inch, 1*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(table)
    
    # Construir PDF
    doc.build(story)
    
    # Respuesta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"parte_diario_{fecha_desde}_{fecha_hasta}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# ==================== VISTAS DE TAREAS ====================

@login_required
def task_list_view(request):
    """Vista para listar tareas"""
    tasks = Task.objects.all()
    
    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assigned_to_me = request.GET.get('assigned_to_me', '')
    
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    if assigned_to_me:
        tasks = tasks.filter(assigned_users=request.user)
    
    # Paginación
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_to_me': assigned_to_me,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }
    return render(request, 'tickets/task_list.html', context)


@login_required
def task_create_view(request):
    """Vista para crear una nueva tarea"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Para guardar los ManyToMany
            
            messages.success(request, f'Tarea "{task.title}" creada exitosamente.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm()
    
    context = {
        'form': form,
        'title': 'Crear Nueva Tarea'
    }
    return render(request, 'tickets/task_form.html', context)


@login_required
def task_detail_view(request, pk):
    """Vista para ver detalles de una tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    context = {
        'task': task,
    }
    return render(request, 'tickets/task_detail.html', context)


@login_required
def task_edit_view(request, pk):
    """Vista para editar una tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    # Solo el creador o agentes pueden editar
    if not is_agent(request.user) and task.created_by != request.user:
        messages.error(request, 'No tienes permisos para editar esta tarea.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            form.save_m2m()  # Para guardar los ManyToMany
            messages.success(request, f'Tarea "{task.title}" actualizada exitosamente.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'title': f'Editar Tarea: {task.title}'
    }
    return render(request, 'tickets/task_form.html', context)


@login_required
def task_delete_view(request, pk):
    """Vista para eliminar una tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    # Solo el creador o agentes pueden eliminar
    if not is_agent(request.user) and task.created_by != request.user:
        messages.error(request, 'No tienes permisos para eliminar esta tarea.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Tarea "{task_title}" eliminada exitosamente.')
        return redirect('task_list')
    
    context = {
        'task': task,
    }
    return render(request, 'tickets/task_delete.html', context)


@login_required
def task_toggle_status_view(request, pk):
    """Vista para cambiar el estado de una tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            old_status = task.get_status_display()
            task.status = new_status
            
            if new_status == 'completed':
                task.completed_at = timezone.now()
            elif task.status != 'completed' and task.completed_at:
                task.completed_at = None
            
            task.save()
            
            messages.success(request, f'Estado de la tarea "{task.title}" cambiado de {old_status} a {task.get_status_display()}.')
    
    return redirect('task_detail', pk=task.pk)


# ===========================================
# VISTAS PARA GESTIÓN DIARIA DE TAREAS
# ===========================================

def auto_load_daily_tasks(session, user, date):
    """
    Carga automáticamente tareas relevantes para el día en una nueva sesión.
    Prioriza:
    1. Tareas con fecha límite de hoy
    2. Tareas con alta prioridad sin fecha límite
    3. Tareas en progreso del usuario
    """
    # Tareas con fecha límite de hoy (máxima prioridad)
    tasks_due_today = Task.objects.filter(
        assigned_users=user,
        due_date=date,
        status__in=['pending', 'in_progress']
    ).exclude(
        status__in=['completed', 'cancelled']
    )
    
    # Tareas de alta prioridad sin fecha límite
    high_priority_tasks = Task.objects.filter(
        assigned_users=user,
        priority='high',
        due_date__isnull=True,
        status__in=['pending', 'in_progress']
    ).exclude(
        status__in=['completed', 'cancelled']
    )[:3]  # Máximo 3 tareas de alta prioridad
    
    # Tareas actualmente en progreso del usuario
    in_progress_tasks = Task.objects.filter(
        assigned_users=user,
        status='in_progress'
    ).exclude(
        status__in=['completed', 'cancelled']
    )
    
    # Combinar y eliminar duplicados
    auto_tasks = list(tasks_due_today) + list(high_priority_tasks) + list(in_progress_tasks)
    unique_tasks = []
    seen_ids = set()
    
    for task in auto_tasks:
        if task.id not in seen_ids:
            unique_tasks.append(task)
            seen_ids.add(task.id)
    
    # Crear items de la sesión diaria para estas tareas
    for order, task in enumerate(unique_tasks[:8], 1):  # Máximo 8 tareas auto-cargadas
        DailyTaskItem.objects.create(
            session=session,
            task=task,
            order=order
        )


@login_required
def daily_task_management(request):
    """Vista principal - Lista de gestiones de tareas de todos los usuarios"""
    # Obtener todas las gestiones de tareas ordenadas por fecha
    # Si el usuario es superuser o staff, ve todas las gestiones
    # Si no, solo ve las suyas
    if request.user.is_superuser or request.user.is_staff:
        task_sessions = DailyTaskSession.objects.all()
    else:
        task_sessions = DailyTaskSession.objects.filter(user=request.user)
    
    task_sessions = task_sessions.prefetch_related(
        'daily_task_items__task', 'user'
    ).order_by('-created_at')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(task_sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'task_sessions': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'tickets/daily_task_management.html', context)


@login_required
def create_task_session(request):
    """Crear nueva gestión de tareas"""
    if request.method == 'POST':
        # Obtener la fecha del formulario
        session_date = request.POST.get('date')
        notes = request.POST.get('notes', '')
        
        if session_date:
            # Crear nueva sesión
            session = DailyTaskSession.objects.create(
                user=request.user,
                date=session_date,
                notes=notes
            )
            
            # Cargar TODAS las tareas donde el usuario esté involucrado (sin filtros de fecha)
            # Incluir: asignadas al usuario O creadas por el usuario
            assigned_tasks = Task.objects.filter(
                Q(assigned_users=request.user) | Q(created_by=request.user)
            ).exclude(
                status__in=['cancelled']  # Solo excluir canceladas, no completadas
            ).order_by('priority', '-created_at').distinct()
            
            print(f"DEBUG: Usuario {request.user.username}")
            print(f"DEBUG: Tareas totales encontradas: {assigned_tasks.count()}")
            
            # Debug detallado
            all_tasks = Task.objects.all()
            print(f"DEBUG: Total de tareas en el sistema: {all_tasks.count()}")
            
            user_assigned = Task.objects.filter(assigned_users=request.user)
            user_created = Task.objects.filter(created_by=request.user)
            print(f"DEBUG: Tareas asignadas al usuario: {user_assigned.count()}")
            print(f"DEBUG: Tareas creadas por el usuario: {user_created.count()}")
            
            for task in assigned_tasks[:5]:  # Mostrar primeras 5 para debug
                assigned_users = [u.username for u in task.assigned_users.all()]
                print(f"  - {task.title} | Estado: {task.status} | Asignada a: {assigned_users} | Creada por: {task.created_by.username if task.created_by else 'N/A'}")
            
            # Crear items para todas las tareas asignadas
            for order, task in enumerate(assigned_tasks, 1):
                DailyTaskItem.objects.create(
                    session=session,
                    task=task,
                    order=order
                )
            
            messages.success(
                request, 
                f'Nueva gestión de tareas creada con {assigned_tasks.count()} tareas cargadas.'
            )
            return redirect('view_task_session', session_id=session.id)
        else:
            messages.error(request, 'Debes seleccionar una fecha.')
    
    # Pasar la fecha de hoy al template
    today = timezone.now().date()
    return render(request, 'tickets/create_task_session.html', {'today': today})


@login_required
def view_task_session(request, session_id):
    """Ver y gestionar una sesión específica de tareas (checklist)"""
    try:
        session = DailyTaskSession.objects.get(
            id=session_id,
            user=request.user
        )
    except DailyTaskSession.DoesNotExist:
        messages.error(request, 'Gestión de tareas no encontrada.')
        return redirect('daily_task_management')
    
    # Obtener items de la sesión
    session_items = session.daily_task_items.select_related('task').order_by('order')
    
    context = {
        'session': session,
        'session_items': session_items,
    }
    
    return render(request, 'tickets/view_task_session.html', context)


@login_required
def delete_task_session(request, session_id):
    """Eliminar una gestión de tareas"""
    try:
        session = DailyTaskSession.objects.get(id=session_id)
        
        # Verificar permisos: solo el propietario o superusuario puede eliminar
        if session.user != request.user and not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para eliminar esta gestión.')
            return redirect('daily_task_management')
        
        if request.method == 'POST':
            session_date = session.date.strftime('%d/%m/%Y')
            session_user = session.user.get_full_name() or session.user.username
            session.delete()
            messages.success(request, f'Gestión de tareas del {session_date} de {session_user} eliminada correctamente.')
            return redirect('daily_task_management')
        
        context = {
            'session': session,
        }
        
        return render(request, 'tickets/delete_task_session.html', context)
        
    except DailyTaskSession.DoesNotExist:
        messages.error(request, 'Gestión de tareas no encontrada.')
        return redirect('daily_task_management')


@login_required
def add_task_to_daily_session(request):
    """Agregar una tarea a la sesión diaria actual"""
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        today = timezone.now().date()
        
        try:
            task = Task.objects.get(id=task_id, assigned_users=request.user)
            session, created = DailyTaskSession.objects.get_or_create(
                user=request.user,
                date=today
            )
            
            # Verificar que la tarea no esté ya en la sesión
            if not DailyTaskItem.objects.filter(session=session, task=task).exists():
                # Obtener el siguiente orden
                max_order = session.daily_task_items.aggregate(
                    max_order=models.Max('order')
                )['max_order'] or 0
                
                DailyTaskItem.objects.create(
                    session=session,
                    task=task,
                    order=max_order + 1
                )
                
                messages.success(request, f'Tarea "{task.title}" agregada a tu plan del día.')
            else:
                messages.warning(request, 'Esta tarea ya está en tu plan del día.')
                
        except Task.DoesNotExist:
            messages.error(request, 'Tarea no encontrada o no tienes permisos.')
    
    return redirect('daily_task_management')


@login_required
def toggle_daily_task_completion(request, item_id):
    """Marcar/desmarcar una tarea como completada en la sesión"""
    try:
        item = DailyTaskItem.objects.get(
            id=item_id,
            session__user=request.user
        )
        
        if item.completed:
            item.mark_pending()
            messages.info(request, f'Tarea "{item.task.title}" marcada como pendiente.')
        else:
            item.mark_completed()
            messages.success(request, f'¡Excelente! Tarea "{item.task.title}" completada.')
        
        # Redirigir a la vista de la sesión específica
        return redirect('view_task_session', session_id=item.session.id)
        
    except DailyTaskItem.DoesNotExist:
        messages.error(request, 'Item no encontrado.')
        return redirect('daily_task_management')


@login_required
def remove_task_from_daily_session(request, item_id):
    """Remover una tarea de la sesión diaria"""
    try:
        item = DailyTaskItem.objects.get(
            id=item_id,
            session__user=request.user
        )
        task_title = item.task.title
        item.delete()
        messages.info(request, f'Tarea "{task_title}" removida de tu plan del día.')
        
    except DailyTaskItem.DoesNotExist:
        messages.error(request, 'Item no encontrado.')
    
    return redirect('daily_task_management')


@login_required
def update_daily_session_notes(request):
    """Actualizar las notas de la sesión diaria"""
    if request.method == 'POST':
        today = timezone.now().date()
        notes = request.POST.get('notes', '')
        
        session, created = DailyTaskSession.objects.get_or_create(
            user=request.user,
            date=today
        )
        
        session.notes = notes
        session.save()
        
        messages.success(request, 'Notas del día actualizadas.')
    
    return redirect('daily_task_management')


@login_required
def daily_task_history(request):
    """Vista del historial de sesiones diarias"""
    sessions = DailyTaskSession.objects.filter(
        user=request.user
    ).prefetch_related('daily_task_items__task').order_by('-date')
    
    # Aplicar filtros
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    min_completion = request.GET.get('min_completion')
    
    if date_from:
        sessions = sessions.filter(date__gte=date_from)
    if date_to:
        sessions = sessions.filter(date__lte=date_to)
    
    # Calcular estadísticas de todas las sesiones (sin filtros)
    all_sessions = DailyTaskSession.objects.filter(user=request.user)
    total_sessions = all_sessions.count()
    total_tasks = sum(session.get_total_tasks() for session in all_sessions)
    total_completed_tasks = sum(session.get_completed_tasks() for session in all_sessions)
    
    if total_sessions > 0:
        average_completion = sum(session.get_completion_percentage() for session in all_sessions) / total_sessions
    else:
        average_completion = 0
    
    # Filtrar por porcentaje mínimo de finalización
    if min_completion:
        filtered_sessions = []
        for session in sessions:
            if session.get_completion_percentage() >= int(min_completion):
                filtered_sessions.append(session)
        sessions = filtered_sessions
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sessions': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_sessions': total_sessions,
        'total_tasks': total_tasks,
        'total_completed_tasks': total_completed_tasks,
        'average_completion': round(average_completion, 1),
    }
    
    return render(request, 'tickets/daily_task_history.html', context)


@login_required
def refresh_daily_tasks(request):
    """Recargar tareas relevantes del día en la sesión actual"""
    today = timezone.now().date()
    
    try:
        session = DailyTaskSession.objects.get(
            user=request.user,
            date=today
        )
        
        # Obtener tareas ya en la sesión para no duplicar
        existing_task_ids = session.daily_task_items.values_list('task_id', flat=True)
        
        # Tareas con fecha límite de hoy que no están en la sesión
        tasks_due_today = Task.objects.filter(
            assigned_users=request.user,
            due_date=today,
            status__in=['pending', 'in_progress']
        ).exclude(
            id__in=existing_task_ids
        ).exclude(
            status__in=['completed', 'cancelled']
        )
        
        # Tareas de alta prioridad sin fecha que no están en la sesión
        high_priority_tasks = Task.objects.filter(
            assigned_users=request.user,
            priority='high',
            due_date__isnull=True,
            status__in=['pending', 'in_progress']
        ).exclude(
            id__in=existing_task_ids
        ).exclude(
            status__in=['completed', 'cancelled']
        )[:2]  # Máximo 2 adicionales
        
        # Obtener el siguiente orden disponible
        max_order = session.daily_task_items.aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        
        # Agregar nuevas tareas
        new_tasks = list(tasks_due_today) + list(high_priority_tasks)
        tasks_added = 0
        
        for task in new_tasks:
            max_order += 1
            DailyTaskItem.objects.create(
                session=session,
                task=task,
                order=max_order
            )
            tasks_added += 1
        
        if tasks_added > 0:
            messages.success(
                request, 
                f'Se agregaron {tasks_added} tarea(s) relevante(s) a tu plan del día.'
            )
        else:
            messages.info(
                request, 
                'No hay nuevas tareas relevantes para agregar hoy.'
            )
            
    except DailyTaskSession.DoesNotExist:
        messages.error(request, 'No tienes una sesión activa para hoy.')
    
    return redirect('daily_task_management')


# ===========================================
# VISTAS PARA CONTROL DIARIO DE TAREAS (MANTENEMOS LAS ANTERIORES)
# ===========================================

@login_required
def task_control_dashboard(request):
    """Dashboard diario de control de tareas para agentes"""
    # Obtener solo las tareas asignadas al usuario actual
    user_tasks = Task.objects.filter(
        assigned_users=request.user
    ).exclude(
        status__in=['cancelled']
    ).prefetch_related('assigned_users', 'created_by').order_by(
        'status', 'priority', 'due_date'
    )
    
    # Separar tareas por estado
    pending_tasks = user_tasks.filter(status='pending')
    in_progress_tasks = user_tasks.filter(status='in_progress')
    completed_tasks = user_tasks.filter(status='completed')
    
    # Estadísticas del día
    today = timezone.now().date()
    today_completed = user_tasks.filter(
        status='completed',
        completed_at__date=today
    ).count()
    
    overdue_tasks = [task for task in user_tasks if task.is_overdue()]
    
    context = {
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'today_completed': today_completed,
        'total_tasks': user_tasks.count(),
        'total_pending': pending_tasks.count(),
        'total_in_progress': in_progress_tasks.count(),
        'total_completed': completed_tasks.count(),
    }
    
    return render(request, 'tickets/task_control_dashboard.html', context)


@login_required
def task_control_complete(request, pk):
    """Marcar una tarea como completada desde el dashboard de control"""
    task = get_object_or_404(Task, pk=pk)
    
    # Verificar que el usuario esté asignado a la tarea
    if request.user not in task.assigned_users.all():
        messages.error(request, 'No tienes permisos para completar esta tarea.')
        return redirect('task_control_dashboard')
    
    if request.method == 'POST':
        old_status = task.get_status_display()
        task.mark_as_completed()
        
        messages.success(
            request,
            f'¡Excelente! Has completado la tarea "{task.title}".'
        )
    
    return redirect('task_control_dashboard')


@login_required
def task_control_start(request, pk):
    """Marcar una tarea como en progreso desde el dashboard de control"""
    task = get_object_or_404(Task, pk=pk)
    
    # Verificar que el usuario esté asignado a la tarea
    if request.user not in task.assigned_users.all():
        messages.error(request, 'No tienes permisos para modificar esta tarea.')
        return redirect('task_control_dashboard')
    
    if request.method == 'POST':
        if task.status == 'pending':
            task.status = 'in_progress'
            task.save()
            
            messages.success(
                request,
                f'Has comenzado a trabajar en la tarea "{task.title}".'
            )
        else:
            messages.warning(request, 'Esta tarea ya está en progreso o completada.')
    
    return redirect('task_control_dashboard')


@login_required
def task_control_pause(request, pk):
    """Pausar una tarea (marcar como pendiente) desde el dashboard de control"""
    task = get_object_or_404(Task, pk=pk)
    
    # Verificar que el usuario esté asignado a la tarea
    if request.user not in task.assigned_users.all():
        messages.error(request, 'No tienes permisos para modificar esta tarea.')
        return redirect('task_control_dashboard')
    
    if request.method == 'POST':
        if task.status == 'in_progress':
            task.status = 'pending'
            task.save()
            
            messages.info(
                request,
                f'Has pausado la tarea "{task.title}". Puedes retomarla cuando quieras.'
            )
        else:
            messages.warning(request, 'Solo puedes pausar tareas que estén en progreso.')
    
    return redirect('task_control_dashboard')


def public_task_view(request, token):
    """Vista pública para gestionar tareas sin autenticación"""
    try:
        user_profile = UserProfile.objects.get(public_token=token)
        user = user_profile.user
    except UserProfile.DoesNotExist:
        return render(request, 'tickets/public_tasks_error.html', {
            'error': 'Token no válido'
        })
    
    if request.method == 'POST':
        # Obtener las tareas seleccionadas (completadas)
        selected_task_ids = request.POST.getlist('selected_tasks')
        selected_task_ids = [int(task_id) for task_id in selected_task_ids]
        
        # Obtener TODAS las tareas asignadas al usuario (para crear la gestión completa)
        all_user_tasks = Task.objects.filter(
            Q(assigned_users=user) | Q(created_by=user)
        ).exclude(status__in=['cancelled']).distinct()
        
        if all_user_tasks.exists():
            # Crear nueva sesión con fecha de hoy
            from django.utils import timezone
            session = DailyTaskSession.objects.create(
                user=user,
                date=timezone.now().date(),
                notes='Gestión creada desde acceso público'
            )
            
            # Crear un item para CADA tarea asignada
            completed_count = 0
            order_counter = 1  # Contador para el orden
            for task in all_user_tasks:
                is_completed = task.id in selected_task_ids
                
                DailyTaskItem.objects.create(
                    session=session,
                    task=task,
                    order=order_counter,
                    completed=is_completed,
                    completed_at=timezone.now() if is_completed else None
                )
                
                order_counter += 1
                
                # Si la tarea fue marcada como completada, actualizar su estado
                if is_completed and task.status != 'completed':
                    task.status = 'completed'
                    task.save()
                    completed_count += 1
            
            return render(request, 'tickets/public_task_success.html', {
                'session': session,
                'user': user,
                'token': token,
                'task_count': all_user_tasks.count(),
                'completed_count': completed_count
            })
        else:
            error_message = 'No tienes tareas asignadas para crear una gestión'
    else:
        error_message = None
    
    # Obtener todas las tareas asignadas al usuario (incluyendo completadas)
    tasks = Task.objects.filter(
        Q(assigned_users=user) | Q(created_by=user)
    ).exclude(status='cancelled').distinct().order_by('-created_at')
    
    context = {
        'user': user,
        'tasks': tasks,
        'token': token,
        'error_message': error_message,
    }
    
    return render(request, 'tickets/public_tasks_simple.html', context)


def public_create_task_session(request, token):
    """Redirigir a la vista principal simplificada"""
    return redirect('public_task_view', token=token)


def public_project_view(request, token):
    """Vista pública para mostrar información del proyecto sin autenticación"""
    try:
        project = get_object_or_404(Project, public_share_token=token)
    except Project.DoesNotExist:
        return render(request, 'tickets/public_project_error.html', {
            'error': 'El enlace proporcionado no es válido o ha expirado.'
        })
    
    # Calcular estadísticas del proyecto usando los métodos del modelo
    total_hours = project.get_total_hours()
    tickets_count = project.get_tickets_count()
    resolved_tickets_count = project.get_resolved_tickets_count()
    completed_work_orders_count = project.get_completed_work_orders_count()
    
    # Obtener trabajadores del proyecto con sus datos de contacto
    workers = project.get_project_workers()
    
    # Crear lista de trabajadores con información de contacto
    workers_info = []
    for worker in workers:
        worker_info = {
            'name': f"{worker.first_name} {worker.last_name}".strip() or worker.username,
            'email': worker.email,
            'phone': getattr(worker.profile, 'phone', '') if hasattr(worker, 'profile') else '',
        }
        workers_info.append(worker_info)
    
    # Obtener tickets directamente asignados al proyecto para mostrar
    project_tickets = project.tickets.all().order_by('-created_at')[:10]
    
    # Obtener órdenes de trabajo directamente asignadas al proyecto para mostrar
    project_work_orders = project.work_orders.all().order_by('-created_at')[:10]
    
    context = {
        'project': project,
        'total_hours': total_hours,
        'tickets_count': tickets_count,
        'resolved_tickets_count': resolved_tickets_count,
        'completed_work_orders_count': completed_work_orders_count,
        'workers_info': workers_info,
        'project_tickets': project_tickets,
        'project_work_orders': project_work_orders,
    }
    
    return render(request, 'tickets/public_project.html', context)


# ===== VISTAS DEL CHAT =====

@login_required
def chat_list_view(request):
    """Vista para listar las salas de chat del usuario"""
    user_rooms = request.user.chat_rooms.all().order_by('-last_activity')
    
    # Agregar conteo de mensajes no leídos a cada sala
    for room in user_rooms:
        room.unread_count = room.get_unread_count_for_user(request.user)
    
    context = {
        'rooms': user_rooms,
        'page_title': 'Chat - Mensajes',
    }
    
    return render(request, 'tickets/chat_list.html', context)


@login_required
def chat_room_view(request, room_id):
    """Vista para una sala de chat específica"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    # Marcar mensajes como leídos
    room.mark_as_read_for_user(request.user)
    
    # Obtener mensajes de la sala
    messages = room.messages.all().order_by('created_at')
    
    # Procesar envío de mensaje
    if request.method == 'POST':
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = room
            message.sender = request.user
            message.save()
            
            # Actualizar última actividad de la sala
            room.last_activity = timezone.now()
            room.save()
            
            # Redirigir para evitar reenvío
            return redirect('chat_room', room_id=room.id)
    else:
        form = ChatMessageForm()
    
    context = {
        'room': room,
        'messages': messages,
        'form': form,
        'page_title': f'Chat - {room}',
    }
    
    return render(request, 'tickets/chat_room.html', context)


@login_required
def chat_start_conversation(request, user_id):
    """Inicia una conversación 1:1 con otro usuario"""
    other_user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Verificar que no es el mismo usuario
    if other_user == request.user:
        messages.error(request, 'No puedes iniciar una conversación contigo mismo.')
        return redirect('chat_list')
    
    # Buscar si ya existe una sala 1:1 entre estos usuarios
    existing_room = ChatRoom.objects.filter(
        is_group=False,
        participants=request.user
    ).filter(participants=other_user).first()
    
    if existing_room:
        return redirect('chat_room', room_id=existing_room.id)
    
    # Crear nueva sala 1:1
    room = ChatRoom.objects.create(is_group=False)
    room.participants.add(request.user, other_user)
    
    return redirect('chat_room', room_id=room.id)


@login_required
def chat_create_group(request):
    """Vista para crear un chat grupal"""
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, user=request.user)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Grupo "{room}" creado exitosamente.')
            return redirect('chat_room', room_id=room.id)
    else:
        form = ChatRoomForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Crear Grupo de Chat',
    }
    
    return render(request, 'tickets/chat_create_group.html', context)


@login_required
def chat_users_list(request):
    """Vista para listar usuarios disponibles para chat"""
    users = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by(
        'first_name', 'last_name', 'username'
    )
    
    context = {
        'users': users,
        'page_title': 'Usuarios - Chat',
    }
    
    return render(request, 'tickets/chat_users.html', context)


@login_required
def chat_ajax_load_messages(request, room_id):
    """Vista AJAX para cargar mensajes de una sala"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    # Obtener mensajes después de cierto timestamp (para polling)
    last_message_id = request.GET.get('last_message_id', 0)
    messages = room.messages.filter(id__gt=last_message_id).order_by('created_at')
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'sender_name': message.sender.get_full_name() or message.sender.username,
            'sender_id': message.sender.id,
            'message': message.message,
            'attachment_name': message.get_attachment_name(),
            'attachment_url': message.attachment.url if message.attachment else None,
            'attachment_size': message.get_attachment_size(),
            'created_at': message.created_at.strftime('%H:%M'),
            'is_own': message.sender == request.user,
        })
    
    return JsonResponse({
        'messages': messages_data,
        'room_id': room.id,
    })


@login_required
def chat_ajax_send_message(request, room_id):
    """Vista AJAX para enviar mensajes"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    form = ChatMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.room = room
        message.sender = request.user
        message.save()
        
        # Actualizar última actividad
        room.last_activity = timezone.now()
        room.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'sender_id': message.sender.id,
                'message': message.message,
                'attachment_name': message.get_attachment_name(),
                'attachment_url': message.attachment.url if message.attachment else None,
                'attachment_size': message.get_attachment_size(),
                'created_at': message.created_at.strftime('%H:%M'),
                'is_own': True,
            }
        })
    else:
        return JsonResponse({
            'error': 'Formulario inválido',
            'errors': form.errors
        }, status=400)


@login_required
@user_passes_test(is_agent)
def pdf_get_pages_view(request):
    """Vista para extraer páginas específicas de un PDF"""
    if request.method == 'POST':
        if 'pdf_file' not in request.FILES:
            messages.error(request, 'No se ha seleccionado ningún archivo PDF.')
            return render(request, 'tickets/pdf_get_pages.html')
        
        pdf_file = request.FILES['pdf_file']
        pages_input = request.POST.get('pages', '').strip()
        
        # Validar que el archivo sea PDF
        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, 'El archivo debe ser un PDF.')
            return render(request, 'tickets/pdf_get_pages.html')
        
        # Validar entrada de páginas
        if not pages_input:
            messages.error(request, 'Debe especificar las páginas a extraer.')
            return render(request, 'tickets/pdf_get_pages.html')
        
        try:
            # Importar PyPDF2
            from PyPDF2 import PdfReader, PdfWriter
            import io
            
            # Leer el PDF
            pdf_reader = PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            # Procesar la entrada de páginas (ej: "1,3,5-7")
            pages_to_extract = []
            for part in pages_input.split(','):
                part = part.strip()
                if '-' in part:
                    # Rango de páginas
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    if start > end:
                        raise ValueError("Rango inválido")
                    pages_to_extract.extend(range(start, end + 1))
                else:
                    # Página individual
                    pages_to_extract.append(int(part))
            
            # Validar que las páginas estén en el rango válido
            for page_num in pages_to_extract:
                if page_num < 1 or page_num > total_pages:
                    messages.error(request, f'La página {page_num} no existe. El PDF tiene {total_pages} páginas.')
                    return render(request, 'tickets/pdf_get_pages.html')
            
            # Crear nuevo PDF con las páginas seleccionadas
            pdf_writer = PdfWriter()
            for page_num in pages_to_extract:
                page = pdf_reader.pages[page_num - 1]  # PyPDF2 usa índice base 0
                pdf_writer.add_page(page)
            
            # Crear respuesta HTTP con el PDF
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            # Preparar nombre del archivo de salida
            original_name = pdf_file.name.rsplit('.', 1)[0]
            pages_str = pages_input.replace(',', '_').replace('-', '_')
            output_filename = f"{original_name}_pages_{pages_str}.pdf"
            
            response = HttpResponse(output.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            
            messages.success(request, f'PDF generado exitosamente con las páginas: {pages_input}')
            return response
            
        except ValueError as e:
            messages.error(request, f'Error en el formato de páginas: {str(e)}. Use formato como "1,3,5-7".')
        except Exception as e:
            messages.error(request, f'Error al procesar el PDF: {str(e)}')
        
        return render(request, 'tickets/pdf_get_pages.html')
    
    return render(request, 'tickets/pdf_get_pages.html')


@login_required
@user_passes_test(is_agent)
def pdf_join_view(request):
    """Vista para unir múltiples archivos PDF en uno solo"""
    if request.method == 'POST':
        pdf_files = request.FILES.getlist('pdf_files')
        
        if not pdf_files:
            messages.error(request, 'No se han seleccionado archivos PDF.')
            return render(request, 'tickets/pdf_join.html')
        
        if len(pdf_files) < 2:
            messages.error(request, 'Debe seleccionar al menos 2 archivos PDF para unir.')
            return render(request, 'tickets/pdf_join.html')
        
        # Validar que todos los archivos sean PDF
        for pdf_file in pdf_files:
            if not pdf_file.name.lower().endswith('.pdf'):
                messages.error(request, f'El archivo "{pdf_file.name}" no es un PDF válido.')
                return render(request, 'tickets/pdf_join.html')
        
        try:
            # Importar PyPDF2
            from PyPDF2 import PdfReader, PdfWriter
            import io
            
            # Crear nuevo PDF writer
            pdf_writer = PdfWriter()
            
            # Leer y agregar páginas de cada PDF
            for pdf_file in pdf_files:
                try:
                    pdf_reader = PdfReader(pdf_file)
                    
                    # Agregar todas las páginas del PDF actual
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                        
                except Exception as e:
                    messages.error(request, f'Error al procesar el archivo "{pdf_file.name}": {str(e)}')
                    return render(request, 'tickets/pdf_join.html')
            
            # Crear respuesta HTTP con el PDF unido
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            # Preparar nombre del archivo ZIP
            current_time = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"PDF_unido_{current_time}.pdf"
            
            response = HttpResponse(output.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            
            messages.success(request, f'PDF unido exitosamente. Se combinaron {len(pdf_files)} archivos.')
            return response
            
        except Exception as e:
            messages.error(request, f'Error al unir los PDFs: {str(e)}')
        
        return render(request, 'tickets/pdf_join.html')
    
    return render(request, 'tickets/pdf_join.html')


@login_required
@user_passes_test(is_agent)
def pdf_split_view(request):
    """Vista para dividir un PDF en archivos individuales por página"""
    if request.method == 'POST':
        if 'pdf_file' not in request.FILES:
            messages.error(request, 'No se ha seleccionado ningún archivo PDF.')
            return render(request, 'tickets/pdf_split.html')
        
        pdf_file = request.FILES['pdf_file']
        
        # Validar que el archivo sea PDF
        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, 'El archivo debe ser un PDF.')
            return render(request, 'tickets/pdf_split.html')
        
        try:
            # Importar PyPDF2 y zipfile
            from PyPDF2 import PdfReader, PdfWriter
            import io
            import zipfile
            from django.utils import timezone
            
            # Leer el PDF
            pdf_reader = PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            if total_pages == 0:
                messages.error(request, 'El PDF no contiene páginas válidas.')
                return render(request, 'tickets/pdf_split.html')
            
            if total_pages == 1:
                messages.warning(request, 'El PDF solo tiene una página. No es necesario dividirlo.')
                return render(request, 'tickets/pdf_split.html')
            
            # Crear un archivo ZIP en memoria
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Crear un PDF para cada página
                for page_num in range(total_pages):
                    pdf_writer = PdfWriter()
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)
                    
                    # Crear PDF en memoria
                    page_buffer = io.BytesIO()
                    pdf_writer.write(page_buffer)
                    page_buffer.seek(0)
                    
                    # Preparar nombre del archivo de página
                    original_name = pdf_file.name.rsplit('.', 1)[0]
                    page_filename = f"{original_name}_pagina_{page_num + 1:03d}.pdf"
                    
                    # Agregar al ZIP
                    zip_file.writestr(page_filename, page_buffer.read())
            
            zip_buffer.seek(0)
            
            # Preparar nombre del archivo ZIP
            current_time = timezone.now().strftime('%Y%m%d_%H%M%S')
            original_name = pdf_file.name.rsplit('.', 1)[0]
            zip_filename = f"{original_name}_dividido_{current_time}.zip"
            
            # Crear respuesta HTTP con el ZIP
            response = HttpResponse(zip_buffer.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
            
            messages.success(request, f'PDF dividido exitosamente en {total_pages} archivos individuales.')
            return response
            
        except Exception as e:
            messages.error(request, f'Error al dividir el PDF: {str(e)}')
        
        return render(request, 'tickets/pdf_split.html')
    
    return render(request, 'tickets/pdf_split.html')


@login_required
@user_passes_test(is_agent)
def calculator_view(request):
    """Vista para la calculadora con historial"""
    return render(request, 'tickets/calculator.html')


@login_required
@user_passes_test(is_agent)
def command_library_view(request):
    """Vista principal de la biblioteca de comandos con búsqueda"""
    from .forms import CommandSearchForm
    from .models import Command
    from django.db.models import Q
    
    form = CommandSearchForm(request.GET)
    commands = Command.objects.all()
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        favorites_only = form.cleaned_data.get('favorites_only')
        dangerous_only = form.cleaned_data.get('dangerous_only')
        
        # Búsqueda por texto
        if query:
            commands = commands.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(command__icontains=query) |
                Q(tags__icontains=query) |
                Q(example_usage__icontains=query) |
                Q(notes__icontains=query)
            )
        
        # Filtrar por categoría
        if category:
            commands = commands.filter(category=category)
        
        # Filtrar solo favoritos
        if favorites_only:
            commands = commands.filter(is_favorite=True)
        
        # Filtrar solo comandos peligrosos
        if dangerous_only:
            commands = commands.filter(is_dangerous=True)
    
    # Estadísticas
    total_commands = Command.objects.count()
    favorites_count = Command.objects.filter(is_favorite=True).count()
    dangerous_count = Command.objects.filter(is_dangerous=True).count()
    
    # Paginación
    paginator = Paginator(commands, 12)  # 12 comandos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_commands': total_commands,
        'favorites_count': favorites_count,
        'dangerous_count': dangerous_count,
        'query': request.GET.get('query', ''),
    }
    
    return render(request, 'tickets/command_library.html', context)


@login_required
@user_passes_test(is_agent)
def command_create_view(request):
    """Vista para crear un nuevo comando"""
    from .forms import CommandForm
    from .models import Command
    
    if request.method == 'POST':
        form = CommandForm(request.POST)
        if form.is_valid():
            command = form.save(commit=False)
            command.created_by = request.user
            command.save()
            messages.success(request, 'Comando creado exitosamente.')
            return redirect('command_detail', pk=command.pk)
    else:
        form = CommandForm()
    
    return render(request, 'tickets/command_form.html', {
        'form': form,
        'title': 'Crear Comando',
        'action': 'Crear'
    })


@login_required
@user_passes_test(is_agent)
def command_detail_view(request, pk):
    """Vista de detalle de un comando"""
    from .models import Command
    
    command = get_object_or_404(Command, pk=pk)
    
    context = {
        'command': command,
    }
    
    return render(request, 'tickets/command_detail.html', context)


@login_required
@user_passes_test(is_agent)
def command_edit_view(request, pk):
    """Vista para editar un comando"""
    from .forms import CommandForm
    from .models import Command
    
    command = get_object_or_404(Command, pk=pk)
    
    if request.method == 'POST':
        form = CommandForm(request.POST, instance=command)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comando actualizado exitosamente.')
            return redirect('command_detail', pk=command.pk)
    else:
        form = CommandForm(instance=command)
    
    return render(request, 'tickets/command_form.html', {
        'form': form,
        'command': command,
        'title': 'Editar Comando',
        'action': 'Actualizar'
    })


@login_required
@user_passes_test(is_agent)
def command_delete_view(request, pk):
    """Vista para eliminar un comando"""
    from .models import Command
    
    command = get_object_or_404(Command, pk=pk)
    
    if request.method == 'POST':
        command.delete()
        messages.success(request, 'Comando eliminado exitosamente.')
        return redirect('command_library')
    
    return render(request, 'tickets/command_delete.html', {
        'command': command,
    })


@login_required
@user_passes_test(is_agent)
def command_copy_view(request, pk):
    """Vista AJAX para copiar un comando e incrementar contador de uso"""
    from .models import Command
    
    if request.method == 'POST':
        command = get_object_or_404(Command, pk=pk)
        command.increment_usage()
        
        return JsonResponse({
            'success': True,
            'command': command.command,
            'usage_count': command.usage_count,
            'message': 'Comando copiado al portapapeles'
        })
    
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_agent)
def command_toggle_favorite_view(request, pk):
    """Vista AJAX para alternar favorito de un comando"""
    from .models import Command
    
    if request.method == 'POST':
        command = get_object_or_404(Command, pk=pk)
        command.is_favorite = not command.is_favorite
        command.save()
        
        return JsonResponse({
            'success': True,
            'is_favorite': command.is_favorite,
            'message': 'Favorito actualizado'
        })
    
    return JsonResponse({'success': False})


# ===== VISTAS DE FORMULARIO DE CONTACTO PÚBLICO =====

def public_contact_form_view(request, token):
    """Vista pública para formulario de contacto"""
    from .models import UserProfile, ContactFormSubmission
    from .forms import PublicContactForm
    
    # Buscar el perfil del usuario con el token
    try:
        profile = UserProfile.objects.get(public_token=token, enable_public_contact_form=True)
    except UserProfile.DoesNotExist:
        return render(request, 'tickets/public_contact_error.html', {
            'error_message': 'Formulario de contacto no encontrado o no disponible'
        })
    
    if request.method == 'POST':
        form = PublicContactForm(request.POST)
        if form.is_valid():
            # Crear la submission del formulario
            submission = form.save(commit=False)
            submission.submitted_by_user = profile.user
            
            # Obtener información adicional de la petición
            submission.ip_address = get_client_ip(request)
            submission.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            submission.save()
            
            # Redireccionar a página de éxito
            return redirect('contact_form_success')
    else:
        form = PublicContactForm()
    
    context = {
        'form': form,
        'profile': profile,
        'user_owner': profile.user,
        'page_title': f'Formulario de Contacto - {profile.user.get_full_name() or profile.user.username}'
    }
    
    return render(request, 'tickets/public_contact_form.html', context)


def contact_form_success(request):
    """Vista de éxito después de enviar formulario de contacto"""
    return render(request, 'tickets/contact_form_success.html')


@login_required
def contact_submissions_list(request):
    """Vista para listar formularios de contacto recibidos"""
    from .models import ContactFormSubmission
    from django.core.paginator import Paginator
    
    # Solo mostrar formularios enviados a este usuario
    submissions = ContactFormSubmission.objects.filter(
        submitted_by_user=request.user
    ).order_by('-submitted_at')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Paginación
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    stats = {
        'total': submissions.count(),
        'pending': submissions.filter(status='pending').count(),
        'approved': submissions.filter(status='approved').count(),
        'rejected': submissions.filter(status='rejected').count(),
        'company_created': submissions.filter(status='company_created').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'submissions': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'status_choices': ContactFormSubmission.STATUS_CHOICES,
        'page_title': 'Formularios de Contacto Recibidos'
    }
    
    return render(request, 'tickets/contact_submissions_list.html', context)


@login_required
def contact_submission_detail(request, pk):
    """Vista detallada de un formulario de contacto"""
    from .models import ContactFormSubmission
    from .forms import ContactFormManagementForm
    
    submission = get_object_or_404(
        ContactFormSubmission, 
        pk=pk, 
        submitted_by_user=request.user
    )
    
    if request.method == 'POST':
        if 'update_notes' in request.POST:
            # Actualizar solo las notas administrativas
            admin_notes = request.POST.get('admin_notes', '')
            submission.admin_notes = admin_notes
            submission.save()
            messages.success(request, 'Notas administrativas actualizadas exitosamente.')
            return redirect('contact_submission_detail', pk=pk)
        else:
            # Actualizar el formulario completo
            form = ContactFormManagementForm(request.POST, instance=submission)
            if form.is_valid():
                updated_submission = form.save(commit=False)
                if updated_submission.status != submission.status:
                    updated_submission.processed_by = request.user
                    updated_submission.processed_at = timezone.now()
                updated_submission.save()
                
                messages.success(request, 'Formulario de contacto actualizado exitosamente.')
                return redirect('contact_submission_detail', pk=pk)
    else:
        form = ContactFormManagementForm(instance=submission)
    
    context = {
        'submission': submission,
        'form': form,
        'page_title': f'Formulario de Contacto - {submission.company_name}'
    }
    
    return render(request, 'tickets/contact_submission_detail.html', context)


@login_required
def contact_submission_approve(request, pk):
    """Aprobar un formulario de contacto y crear empresa"""
    from .models import ContactFormSubmission, Company
    from .forms import CompanyFromContactForm
    
    submission = get_object_or_404(
        ContactFormSubmission, 
        pk=pk, 
        submitted_by_user=request.user
    )
    
    if request.method == 'POST':
        form = CompanyFromContactForm(request.POST, contact_form=submission)
        
        if form.is_valid():
            # Crear la empresa
            company = form.save()
            
            # Marcar el formulario como procesado
            submission.mark_as_processed(
                user=request.user,
                status='company_created',
                company=company
            )
            
            messages.success(request, f'Empresa "{company.name}" creada exitosamente desde el formulario de contacto.')
            return redirect('company_detail', company_id=company.id)
        else:
            messages.error(request, f'Error al crear la empresa: {form.errors}')
    else:
        form = CompanyFromContactForm(contact_form=submission)
    
    context = {
        'submission': submission,
        'form': form,
        'page_title': f'Crear Empresa - {submission.company_name}'
    }
    
    return render(request, 'tickets/contact_submission_approve.html', context)


@login_required
def contact_submission_reject(request, pk):
    """Rechazar un formulario de contacto"""
    from .models import ContactFormSubmission
    
    submission = get_object_or_404(
        ContactFormSubmission, 
        pk=pk, 
        submitted_by_user=request.user
    )
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Actualizar el formulario
        submission.mark_as_processed(
            user=request.user,
            status='rejected'
        )
        
        if reason:
            submission.admin_notes = f"Rechazado: {reason}"
            submission.save()
        
        messages.success(request, 'Formulario de contacto rechazado.')
        return redirect('contact_submissions_list')
    
    context = {
        'submission': submission,
        'page_title': f'Rechazar Formulario - {submission.company_name}'
    }
    
    return render(request, 'tickets/contact_submission_reject.html', context)


def get_client_ip(request):
    """Obtener la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def tetris_view(request):
    """Vista para el juego Tetris - para todos los usuarios autenticados"""
    context = {
        'page_title': 'Tetris - Juegos',
        'user_role': get_user_role(request.user)
    }
    return render(request, 'tickets/tetris.html', context)


def public_company_stats(request, token):
    """Vista pública para mostrar estadísticas de una empresa usando su token o ID"""
    try:
        # Intentar primero como UUID token
        company = Company.objects.get(public_token=token, is_active=True)
    except (Company.DoesNotExist, ValueError):
        try:
            # Si falla, intentar como ID numérico
            company = Company.objects.get(id=int(token), is_active=True)
        except (Company.DoesNotExist, ValueError):
            raise Http404("Empresa no encontrada o token inválido")
    
    # Obtener estadísticas públicas
    stats = company.get_public_stats()
    
    # Obtener tickets abiertos de la empresa (limitados a los primeros 10)
    open_tickets = company.tickets.filter(status='open').order_by('-created_at')[:10]
    
    context = {
        'company': company,
        'stats': stats,
        'open_tickets': open_tickets,
        'page_title': f'Estadísticas - {company.name}'
    }
    
    return render(request, 'tickets/public_company_stats.html', context)


# ============= VISTAS CRM =============

@login_required
def crm_dashboard(request):
    """Dashboard principal del CRM"""
    # Obtener configuración del sistema
    system_config = SystemConfiguration.get_config()
    
    # Obtener oportunidades del usuario
    if is_agent(request.user):
        opportunities = Opportunity.objects.all()
    else:
        opportunities = Opportunity.objects.filter(
            Q(created_by=request.user) | Q(assigned_to=request.user)
        )
    
    # Estadísticas generales
    total_opportunities = opportunities.count()
    total_value = opportunities.aggregate(total=Sum('value'))['total'] or 0
    total_expected_value = sum(opp.expected_value for opp in opportunities)
    
    # Oportunidades por estado
    status_stats = {}
    for status in OpportunityStatus.objects.filter(is_active=True):
        count = opportunities.filter(status=status).count()
        value = opportunities.filter(status=status).aggregate(total=Sum('value'))['total'] or 0
        status_stats[status] = {'count': count, 'value': value}
    
    # Oportunidades próximas a vencer (próximos 7 días)
    next_week = timezone.now().date() + timedelta(days=7)
    upcoming_opportunities = opportunities.filter(
        expected_close_date__lte=next_week,
        expected_close_date__gte=timezone.now().date(),
        status__is_final=False
    ).order_by('expected_close_date')[:5]
    
    # Oportunidades vencidas
    overdue_opportunities = opportunities.filter(
        expected_close_date__lt=timezone.now().date(),
        status__is_final=False
    ).count()
    
    context = {
        'total_opportunities': total_opportunities,
        'total_value': total_value,
        'total_expected_value': total_expected_value,
        'status_stats': status_stats,
        'upcoming_opportunities': upcoming_opportunities,
        'overdue_opportunities': overdue_opportunities,
        'page_title': 'CRM Dashboard',
        'system_config': system_config,
    }
    
    return render(request, 'tickets/crm_dashboard.html', context)


@login_required
def opportunity_list(request):
    """Lista de oportunidades"""
    # Obtener oportunidades del usuario
    if is_agent(request.user):
        opportunities = Opportunity.objects.all()
    else:
        opportunities = Opportunity.objects.filter(
            Q(created_by=request.user) | Q(assigned_to=request.user)
        )
    
    # Filtros
    status_filter = request.GET.get('status')
    company_filter = request.GET.get('company')
    assigned_filter = request.GET.get('assigned')
    search = request.GET.get('search')
    overdue_filter = request.GET.get('overdue')
    
    if status_filter:
        opportunities = opportunities.filter(status_id=status_filter)
    
    if company_filter:
        opportunities = opportunities.filter(company_id=company_filter)
    
    if assigned_filter:
        opportunities = opportunities.filter(assigned_to_id=assigned_filter)
    
    if overdue_filter == 'true':
        from django.utils import timezone
        today = timezone.now().date()
        opportunities = opportunities.filter(
            expected_close_date__lt=today,
            status__is_final=False
        )
    
    if search:
        opportunities = opportunities.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(company__name__icontains=search) |
            Q(contact_name__icontains=search)
        )
    
    # Ordenamiento
    order_by = request.GET.get('order_by', '-created_at')
    opportunities = opportunities.order_by(order_by)
    
    # Paginación
    paginator = Paginator(opportunities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Agregar información de permisos a cada oportunidad
    for opportunity in page_obj:
        opportunity.user_can_edit = opportunity.can_be_edited_by(request.user)
    
    # Para los filtros
    statuses = OpportunityStatus.objects.filter(is_active=True).order_by('order')
    companies = Company.objects.all()
    users = User.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'statuses': statuses,
        'companies': companies,
        'users': users,
        'current_filters': {
            'status': status_filter,
            'company': company_filter,
            'assigned': assigned_filter,
            'search': search,
            'order_by': order_by,
        },
        'page_title': 'Oportunidades'
    }
    
    return render(request, 'tickets/opportunity_list.html', context)


@login_required
def opportunity_detail(request, pk):
    """Detalle de oportunidad"""
    opportunity = get_object_or_404(Opportunity, pk=pk)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if opportunity.created_by != request.user and opportunity.assigned_to != request.user:
            messages.error(request, 'No tienes permisos para ver esta oportunidad.')
            return redirect('opportunity_list')
    
    # Obtener notas y historial
    notes = opportunity.notes.all()
    history = opportunity.status_history.all()
    
    # Verificar si puede ser editada
    can_be_edited = opportunity.can_be_edited_by(request.user)
    
    context = {
        'opportunity': opportunity,
        'notes': notes,
        'history': history,
        'can_be_edited': can_be_edited,
        'page_title': f'Oportunidad: {opportunity.name}'
    }
    
    return render(request, 'tickets/opportunity_detail.html', context)


@login_required
def opportunity_create(request):
    """Crear nueva oportunidad"""
    if request.method == 'POST':
        # Procesar formulario
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        company_id = request.POST.get('company')
        contact_name = request.POST.get('contact_name')
        contact_position = request.POST.get('contact_position', '')
        contact_email = request.POST.get('contact_email', '')
        contact_phone = request.POST.get('contact_phone', '')
        value = request.POST.get('value')
        probability = request.POST.get('probability', 20)
        status_id = request.POST.get('status')
        expected_close_date = request.POST.get('expected_close_date')
        assigned_to_id = request.POST.get('assigned_to')
        source = request.POST.get('source', '')
        
        try:
            company = Company.objects.get(pk=company_id)
            status = OpportunityStatus.objects.get(pk=status_id)
            assigned_to = User.objects.get(pk=assigned_to_id) if assigned_to_id else None
            
            opportunity = Opportunity.objects.create(
                name=name,
                description=description,
                company=company,
                contact_name=contact_name,
                contact_position=contact_position,
                contact_email=contact_email,
                contact_phone=contact_phone,
                value=value,
                probability=probability,
                status=status,
                expected_close_date=expected_close_date,
                assigned_to=assigned_to,
                created_by=request.user,
                source=source
            )
            
            # Crear historial inicial
            OpportunityStatusHistory.objects.create(
                opportunity=opportunity,
                new_status=status,
                changed_by=request.user,
                comment="Oportunidad creada"
            )
            
            messages.success(request, 'Oportunidad creada exitosamente.')
            return redirect('opportunity_detail', pk=opportunity.pk)
            
        except Exception as e:
            messages.error(request, f'Error al crear la oportunidad: {str(e)}')
    
    # Para GET request
    companies = Company.objects.all()
    statuses = OpportunityStatus.objects.filter(is_active=True).order_by('order')
    users = User.objects.filter(is_active=True)
    
    # Valores por defecto
    default_close_date = (timezone.now().date() + timedelta(days=90)).strftime('%Y-%m-%d')  # 3 meses
    default_status = statuses.first()  # Estado con menor secuencia (order)
    default_assigned_to = request.user  # Usuario que crea la oportunidad
    
    # Si viene un contact_id, precargar datos del contacto
    contact_data = {}
    contact_id = request.GET.get('contact_id')
    if contact_id:
        try:
            contact = Contact.objects.get(pk=contact_id)
            contact_data = {
                'contact_name': contact.name,
                'contact_email': contact.email or '',
                'contact_phone': contact.phone or '',
                'contact_position': contact.position or '',
                'source': f"Contacto: {contact.source}" if contact.source else "Contacto previo",
            }
            # Si el contacto tiene empresa, buscar si existe en Company
            if contact.company:
                try:
                    company = Company.objects.filter(name__iexact=contact.company).first()
                    if company:
                        contact_data['default_company'] = company
                except:
                    pass
        except Contact.DoesNotExist:
            pass
    
    # Opciones de probabilidad
    probability_choices = [
        (0, '0%'), (10, '10%'), (20, '20%'), (30, '30%'), (40, '40%'),
        (50, '50%'), (60, '60%'), (70, '70%'), (80, '80%'), (90, '90%'), (100, '100%')
    ]
    
    context = {
        'companies': companies,
        'statuses': statuses,
        'users': users,
        'probability_choices': probability_choices,
        'page_title': 'Nueva Oportunidad',
        'default_close_date': default_close_date,
        'default_status': default_status,
        'default_assigned_to': default_assigned_to,
        'contact_data': contact_data,
    }
    
    return render(request, 'tickets/opportunity_form.html', context)


@login_required
def opportunity_edit(request, pk):
    """Editar oportunidad"""
    opportunity = get_object_or_404(Opportunity, pk=pk)
    
    # Verificar permisos
    if not opportunity.can_be_edited_by(request.user):
        messages.error(request, 'No tienes permisos para editar esta oportunidad.')
        return redirect('opportunity_detail', pk=pk)
    
    if request.method == 'POST':
        # Procesar formulario
        previous_status = opportunity.status
        
        opportunity.name = request.POST.get('name')
        opportunity.description = request.POST.get('description', '')
        opportunity.company_id = request.POST.get('company')
        opportunity.contact_name = request.POST.get('contact_name')
        opportunity.contact_position = request.POST.get('contact_position', '')
        opportunity.contact_email = request.POST.get('contact_email', '')
        opportunity.contact_phone = request.POST.get('contact_phone', '')
        opportunity.value = request.POST.get('value')
        opportunity.probability = request.POST.get('probability', 20)
        opportunity.status_id = request.POST.get('status')
        opportunity.expected_close_date = request.POST.get('expected_close_date')
        opportunity.assigned_to_id = request.POST.get('assigned_to') or None
        opportunity.source = request.POST.get('source', '')
        
        # Si el estado cambió, crear historial
        if previous_status.pk != int(request.POST.get('status')):
            comment = request.POST.get('status_comment', '')
            OpportunityStatusHistory.objects.create(
                opportunity=opportunity,
                previous_status=previous_status,
                new_status=opportunity.status,
                changed_by=request.user,
                comment=comment
            )
        
        opportunity.save()
        messages.success(request, 'Oportunidad actualizada exitosamente.')
        return redirect('opportunity_detail', pk=pk)
    
    # Para GET request
    companies = Company.objects.all()
    statuses = OpportunityStatus.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
    # Opciones de probabilidad
    probability_choices = [
        (0, '0%'), (10, '10%'), (20, '20%'), (30, '30%'), (40, '40%'),
        (50, '50%'), (60, '60%'), (70, '70%'), (80, '80%'), (90, '90%'), (100, '100%')
    ]
    
    context = {
        'opportunity': opportunity,
        'companies': companies,
        'statuses': statuses,
        'users': users,
        'probability_choices': probability_choices,
        'page_title': f'Editar: {opportunity.name}'
    }
    
    return render(request, 'tickets/opportunity_form.html', context)


@login_required
def opportunity_delete(request, pk):
    """Eliminar oportunidad"""
    opportunity = get_object_or_404(Opportunity, pk=pk)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user) and opportunity.created_by != request.user:
        messages.error(request, 'No tienes permisos para eliminar esta oportunidad.')
        return redirect('opportunity_detail', pk=pk)
    
    if request.method == 'POST':
        opportunity.delete()
        messages.success(request, 'Oportunidad eliminada exitosamente.')
        return redirect('opportunity_list')
    
    context = {
        'opportunity': opportunity,
        'page_title': f'Eliminar: {opportunity.name}'
    }
    
    return render(request, 'tickets/opportunity_delete.html', context)


@login_required
def opportunity_status_list(request):
    """Lista de estados de oportunidades"""
    from . import utils
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    statuses = OpportunityStatus.objects.all().order_by('order', 'name')
    
    context = {
        'statuses': statuses,
        'page_title': 'Estados de Oportunidades'
    }
    
    return render(request, 'tickets/opportunity_status_list.html', context)


@login_required
def opportunity_status_create(request):
    """Crear estado de oportunidad"""
    from . import utils
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#007bff')
        is_final = request.POST.get('is_final') == 'on'
        is_won = request.POST.get('is_won') == 'on'
        order = request.POST.get('order', 0)
        
        try:
            status = OpportunityStatus.objects.create(
                name=name,
                description=description,
                color=color,
                is_final=is_final,
                is_won=is_won,
                order=order,
                created_by=request.user
            )
            messages.success(request, 'Estado creado exitosamente.')
            return redirect('opportunity_status_list')
        except Exception as e:
            messages.error(request, f'Error al crear el estado: {str(e)}')
    
    context = {
        'page_title': 'Nuevo Estado'
    }
    
    return render(request, 'tickets/opportunity_status_form.html', context)


@login_required
def opportunity_status_edit(request, pk):
    """Editar estado de oportunidad"""
    from .models import OpportunityStatus
    from . import utils
    
    status = get_object_or_404(OpportunityStatus, pk=pk)
    
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        status.name = request.POST.get('name')
        status.description = request.POST.get('description', '')
        status.color = request.POST.get('color', '#007bff')
        status.is_final = request.POST.get('is_final') == 'on'
        status.is_won = request.POST.get('is_won') == 'on'
        status.order = request.POST.get('order', 0)
        status.is_active = request.POST.get('is_active') == 'on'
        
        status.save()
        messages.success(request, 'Estado actualizado exitosamente.')
        return redirect('opportunity_status_list')
    
    context = {
        'status': status,
        'page_title': f'Editar: {status.name}'
    }
    
    return render(request, 'tickets/opportunity_status_form.html', context)


@login_required
def opportunity_status_delete(request, pk):
    """Eliminar estado de oportunidad"""
    from .models import OpportunityStatus
    
    status = get_object_or_404(OpportunityStatus, pk=pk)
    
    # Verificar si hay oportunidades usando este estado
    if status.opportunities.exists():
        messages.error(request, 'No se puede eliminar este estado porque hay oportunidades que lo utilizan.')
        return redirect('opportunity_status_list')
    
    if request.method == 'POST':
        status.delete()
        messages.success(request, 'Estado eliminado exitosamente.')
        return redirect('opportunity_status_list')
    
    context = {
        'status': status,
        'page_title': f'Eliminar: {status.name}'
    }
    
    return render(request, 'tickets/opportunity_status_delete.html', context)


@login_required
def opportunity_add_note(request, pk):
    """Agregar nota a oportunidad"""
    opportunity = get_object_or_404(Opportunity, pk=pk)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if opportunity.created_by != request.user and opportunity.assigned_to != request.user:
            messages.error(request, 'No tienes permisos para agregar notas a esta oportunidad.')
            return redirect('opportunity_detail', pk=pk)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        is_important = request.POST.get('is_important') == 'on'
        
        if content:
            OpportunityNote.objects.create(
                opportunity=opportunity,
                content=content,
                is_important=is_important,
                created_by=request.user
            )
            messages.success(request, 'Nota agregada exitosamente.')
        else:
            messages.error(request, 'El contenido de la nota es requerido.')
    
    return redirect('opportunity_detail', pk=pk)


# ============================
# VISTAS DE ACTIVIDADES DE OPORTUNIDADES
# ============================

@login_required
def opportunity_activity_create(request, opportunity_id):
    """Crear nueva actividad para oportunidad"""
    from .models import Opportunity, OpportunityActivity
    from .forms import OpportunityActivityForm
    
    opportunity = get_object_or_404(Opportunity, pk=opportunity_id)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if opportunity.created_by != request.user and opportunity.assigned_to != request.user:
            messages.error(request, 'No tienes permisos para crear actividades en esta oportunidad.')
            return redirect('opportunity_detail', pk=opportunity_id)
    
    if request.method == 'POST':
        form = OpportunityActivityForm(request.POST, opportunity=opportunity, current_user=request.user)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.opportunity = opportunity
            activity.created_by = request.user
            activity.save()
            
            messages.success(request, f'Actividad "{activity.title}" creada exitosamente.')
            return redirect('opportunity_detail', pk=opportunity_id)
    else:
        form = OpportunityActivityForm(opportunity=opportunity, current_user=request.user)
    
    context = {
        'form': form,
        'opportunity': opportunity,
        'page_title': f'Nueva Actividad - {opportunity.name}'
    }
    
    return render(request, 'tickets/opportunity_activity_form.html', context)


@login_required
def opportunity_activity_list(request, opportunity_id):
    """Listar actividades de una oportunidad"""
    from .models import Opportunity
    
    opportunity = get_object_or_404(Opportunity, pk=opportunity_id)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if opportunity.created_by != request.user and opportunity.assigned_to != request.user:
            messages.error(request, 'No tienes permisos para ver las actividades de esta oportunidad.')
            return redirect('opportunity_detail', pk=opportunity_id)
    
    activities = opportunity.activities.all()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        activities = activities.filter(status=status)
    
    activity_type = request.GET.get('type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    
    context = {
        'opportunity': opportunity,
        'activities': activities,
        'page_title': f'Actividades - {opportunity.name}'
    }
    
    return render(request, 'tickets/opportunity_activity_list.html', context)


@login_required
def opportunity_activity_detail(request, pk):
    """Detalle de actividad"""
    from .models import OpportunityActivity
    
    activity = get_object_or_404(OpportunityActivity, pk=pk)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if (activity.created_by != request.user and 
            activity.assigned_to != request.user):
            messages.error(request, 'No tienes permisos para ver esta actividad.')
            return redirect('opportunity_detail', pk=activity.opportunity.pk)
    
    context = {
        'activity': activity,
        'page_title': f'Actividad: {activity.title}'
    }
    
    return render(request, 'tickets/opportunity_activity_detail.html', context)


@login_required
def opportunity_activity_edit(request, pk):
    """Editar actividad"""
    from .models import OpportunityActivity
    from .forms import OpportunityActivityForm
    
    activity = get_object_or_404(OpportunityActivity, pk=pk)
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if (activity.created_by != request.user and 
            activity.assigned_to != request.user):
            messages.error(request, 'No tienes permisos para editar esta actividad.')
            return redirect('opportunity_activity_detail', pk=pk)
    
    if request.method == 'POST':
        form = OpportunityActivityForm(request.POST, instance=activity, opportunity=activity.opportunity)
        if form.is_valid():
            form.save()
            messages.success(request, 'Actividad actualizada exitosamente.')
            return redirect('opportunity_activity_detail', pk=pk)
    else:
        form = OpportunityActivityForm(instance=activity, opportunity=activity.opportunity)
    
    context = {
        'form': form,
        'activity': activity,
        'opportunity': activity.opportunity,
        'page_title': f'Editar: {activity.title}'
    }
    
    return render(request, 'tickets/opportunity_activity_form.html', context)


@login_required
def opportunity_activity_complete(request, pk):
    """Completar actividad"""
    from .models import OpportunityActivity
    from .forms import OpportunityActivityCompleteForm
    
    activity = get_object_or_404(OpportunityActivity, pk=pk)
    
    # Verificar permisos
    if activity.assigned_to != request.user:
        messages.error(request, 'Solo el asignado puede completar esta actividad.')
        return redirect('opportunity_activity_detail', pk=pk)
    
    if request.method == 'POST':
        form = OpportunityActivityCompleteForm(request.POST, instance=activity)
        if form.is_valid():
            activity = form.save(commit=False)
            if activity.status == 'completed':
                activity.completed_date = timezone.now()
            activity.save()
            
            messages.success(request, 'Actividad completada exitosamente.')
            return redirect('opportunity_activity_detail', pk=pk)
    else:
        form = OpportunityActivityCompleteForm(instance=activity)
    
    context = {
        'form': form,
        'activity': activity,
        'page_title': f'Completar: {activity.title}'
    }
    
    return render(request, 'tickets/opportunity_activity_complete.html', context)


@login_required
def opportunity_activity_delete(request, pk):
    """Eliminar actividad"""
    from .models import OpportunityActivity
    
    activity = get_object_or_404(OpportunityActivity, pk=pk)
    opportunity_id = activity.opportunity.pk
    
    # Verificar permisos
    from . import utils
    if not utils.is_agent(request.user):
        if activity.created_by != request.user:
            messages.error(request, 'No tienes permisos para eliminar esta actividad.')
            return redirect('opportunity_activity_detail', pk=pk)
    
    if request.method == 'POST':
        activity_title = activity.title
        activity.delete()
        messages.success(request, f'Actividad "{activity_title}" eliminada exitosamente.')
        return redirect('opportunity_detail', pk=opportunity_id)
    
    context = {
        'activity': activity,
        'page_title': f'Eliminar: {activity.title}'
    }
    
    return render(request, 'tickets/opportunity_activity_delete.html', context)


@login_required
def my_activities_dashboard(request):
    """Panel de actividades del usuario"""
    from .models import OpportunityActivity
    from django.db.models import Q
    
    # Actividades asignadas al usuario
    activities = OpportunityActivity.objects.filter(assigned_to=request.user)
    
    # Filtros
    status = request.GET.get('status')
    if status:
        activities = activities.filter(status=status)
    
    # Separar por estado y fecha
    today = timezone.now().date()
    
    overdue_activities = activities.filter(
        status__in=['pending', 'in_progress'],
        scheduled_date__date__lt=today
    )
    
    today_activities = activities.filter(
        scheduled_date__date=today
    )
    
    upcoming_activities = activities.filter(
        status__in=['pending', 'in_progress'],
        scheduled_date__date__gt=today
    ).order_by('scheduled_date')[:10]
    
    completed_recent = activities.filter(
        status='completed',
        completed_date__gte=today - timezone.timedelta(days=7)
    ).order_by('-completed_date')[:5]
    
    # Estadísticas
    stats = {
        'total_pending': activities.filter(status='pending').count(),
        'total_in_progress': activities.filter(status='in_progress').count(),
        'total_overdue': overdue_activities.count(),
        'total_today': today_activities.count(),
        'total_completed_week': completed_recent.count(),
    }
    
    context = {
        'overdue_activities': overdue_activities,
        'today_activities': today_activities,
        'upcoming_activities': upcoming_activities,
        'completed_recent': completed_recent,
        'stats': stats,
        'page_title': 'Mis Actividades'
    }
    
    return render(request, 'tickets/my_activities_dashboard.html', context)


# ============================
# VISTAS DE REUNIONES
# ============================

@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_list_view(request):
    """Vista para listar reuniones"""
    from .models import Meeting
    
    meetings = Meeting.objects.filter(organizer=request.user)
    
    # Filtros
    status = request.GET.get('status')
    if status:
        meetings = meetings.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        meetings = meetings.filter(
            models.Q(title__icontains=search) | 
            models.Q(description__icontains=search)
        )
    
    meetings = meetings.order_by('-date')
    
    # Estadísticas
    stats = {
        'total': Meeting.objects.filter(organizer=request.user).count(),
        'scheduled': Meeting.objects.filter(organizer=request.user, status='scheduled').count(),
        'in_progress': Meeting.objects.filter(organizer=request.user, status='in_progress').count(),
        'finished': Meeting.objects.filter(organizer=request.user, status='finished').count(),
    }
    
    context = {
        'page_title': 'Reuniones',
        'meetings': meetings,
        'stats': stats,
        'current_status': status,
        'search_query': search,
    }
    return render(request, 'tickets/meeting_list.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_create_view(request):
    """Vista para crear reuniones"""
    from .forms import MeetingForm
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, user=request.user)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.organizer = request.user
            meeting.save()
            messages.success(request, f'Reunión "{meeting.title}" creada exitosamente.')
            return redirect('meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm(user=request.user)
    
    context = {
        'page_title': 'Nueva Reunión',
        'form': form,
    }
    return render(request, 'tickets/meeting_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_detail_view(request, pk):
    """Vista detallada de una reunión"""
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    
    # Obtener asistentes y preguntas
    attendees = meeting.meetingattendee_set.all().order_by('registered_at')
    questions = meeting.meetingquestion_set.all().order_by('-asked_at')
    
    # Estadísticas
    stats = {
        'total_attendees': attendees.count(),
        'total_questions': questions.count(),
        'pending_questions': questions.filter(status='pending').count(),
        'answered_questions': questions.filter(status='answered').count(),
    }
    
    context = {
        'page_title': f'Reunión: {meeting.title}',
        'meeting': meeting,
        'attendees': attendees,
        'questions': questions,
        'stats': stats,
    }
    return render(request, 'tickets/meeting_detail.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_print_view(request, pk):
    """Vista para imprimir reunión"""
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    
    # Obtener asistentes y preguntas
    attendees = meeting.meetingattendee_set.all().order_by('registered_at')
    questions = meeting.meetingquestion_set.all().order_by('-asked_at')
    
    # Estadísticas
    stats = {
        'total_attendees': attendees.count(),
        'total_questions': questions.count(),
        'pending_questions': questions.filter(status='pending').count(),
        'answered_questions': questions.filter(status='answered').count(),
    }
    
    context = {
        'page_title': f'Informe: {meeting.title}',
        'meeting': meeting,
        'attendees': attendees,
        'questions': questions,
        'stats': stats,
    }
    return render(request, 'tickets/meeting_print.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_edit_view(request, pk):
    """Vista para editar reuniones"""
    from .forms import MeetingForm
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Reunión "{meeting.title}" actualizada exitosamente.')
            return redirect('meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm(instance=meeting, user=request.user)
    
    context = {
        'page_title': f'Editar: {meeting.title}',
        'form': form,
        'meeting': meeting,
    }
    return render(request, 'tickets/meeting_form.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_delete_view(request, pk):
    """Vista para eliminar reuniones"""
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    
    if request.method == 'POST':
        meeting_title = meeting.title
        meeting.delete()
        messages.success(request, f'Reunión "{meeting_title}" eliminada exitosamente.')
        return redirect('meeting_list')
    
    context = {
        'page_title': f'Eliminar: {meeting.title}',
        'meeting': meeting,
    }
    return render(request, 'tickets/meeting_delete.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_questions_view(request, pk):
    """Vista para gestionar preguntas de una reunión"""
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    questions = meeting.meetingquestion_set.all().order_by('-asked_at')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        questions = questions.filter(status=status)
    
    context = {
        'page_title': f'Preguntas: {meeting.title}',
        'meeting': meeting,
        'questions': questions,
        'current_status': status,
    }
    return render(request, 'tickets/meeting_questions.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_attendees_view(request, pk):
    """Vista para gestionar asistentes de una reunión"""
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    attendees = meeting.meetingattendee_set.all().order_by('registered_at')
    
    context = {
        'page_title': f'Asistentes: {meeting.title}',
        'meeting': meeting,
        'attendees': attendees,
    }
    return render(request, 'tickets/meeting_attendees.html', context)


# ============================
# VISTAS PÚBLICAS DE REUNIONES
# ============================

def meeting_public_view(request, token):
    """Vista pública de una reunión"""
    from .models import Meeting, MeetingAttendee, MeetingQuestion
    from .forms import MeetingAttendeeForm, MeetingQuestionForm
    
    meeting = get_object_or_404(Meeting, public_token=token, is_active=True)
    
    # Verificar si hay un usuario registrado en la sesión para esta reunión
    session_key = f'meeting_{meeting.id}_attendee_id'
    user_attendee = None
    user_registered = False
    user_questions = []
    
    if session_key in request.session:
        try:
            attendee_id = request.session[session_key]
            user_attendee = MeetingAttendee.objects.get(id=attendee_id, meeting=meeting)
            user_registered = True
            user_questions = MeetingQuestion.objects.filter(
                meeting=meeting, 
                attendee=user_attendee
            ).order_by('-asked_at')
        except MeetingAttendee.DoesNotExist:
            # Limpiar la sesión si el asistente no existe
            del request.session[session_key]
    
    # Solo mostrar el formulario de registro si no hay nadie registrado en la sesión
    register_form = None
    if not user_registered:
        register_form = MeetingAttendeeForm(meeting=meeting)
    
    question_form = MeetingQuestionForm() if meeting.allow_questions and user_registered else None
    
    context = {
        'page_title': f'Reunión: {meeting.title}',
        'meeting': meeting,
        'user_registered': user_registered,
        'user_attendee': user_attendee,
        'user_questions': user_questions,
        'register_form': register_form,
        'question_form': question_form,
    }
    return render(request, 'tickets/meeting_public.html', context)


def meeting_register_view(request, token):
    """Vista pública para registrarse en una reunión"""
    from .models import Meeting
    from .forms import MeetingAttendeeForm
    
    meeting = get_object_or_404(Meeting, public_token=token, is_active=True)
    
    # Verificar si ya hay un usuario registrado en esta sesión
    session_key = f'meeting_{meeting.id}_attendee_id'
    if session_key in request.session:
        messages.warning(request, 'Ya hay una persona registrada en esta sesión. Solo se permite un registro por sesión.')
        return redirect('meeting_public', token=token)
    
    if request.method == 'POST':
        form = MeetingAttendeeForm(request.POST, meeting=meeting)
        if form.is_valid():
            attendee = form.save(commit=False)
            attendee.meeting = meeting
            attendee.ip_address = request.META.get('REMOTE_ADDR')
            attendee.save()
            
            # Guardar el ID del asistente en la sesión
            request.session[session_key] = attendee.id
            
            messages.success(request, '¡Te has registrado exitosamente en la reunión!')
            return redirect('meeting_public', token=token)
    else:
        form = MeetingAttendeeForm(meeting=meeting)
    
    context = {
        'page_title': f'Registrarse: {meeting.title}',
        'meeting': meeting,
        'form': form,
    }
    return render(request, 'tickets/meeting_register.html', context)


def meeting_questions_public_view(request, token):
    """Vista pública para ver preguntas de una reunión"""
    from .models import Meeting
    
    meeting = get_object_or_404(Meeting, public_token=token, is_active=True)
    
    if not meeting.allow_questions:
        messages.error(request, 'Esta reunión no permite preguntas.')
        return redirect('meeting_public', token=token)
    
    questions = meeting.meetingquestion_set.filter(status__in=['pending', 'answered']).order_by('-asked_at')
    
    context = {
        'page_title': f'Preguntas: {meeting.title}',
        'meeting': meeting,
        'questions': questions,
    }
    return render(request, 'tickets/meeting_questions_public.html', context)


def meeting_ask_question_view(request, token):
    """Vista pública para hacer una pregunta"""
    from .models import Meeting, MeetingAttendee
    from .forms import MeetingQuestionForm
    
    meeting = get_object_or_404(Meeting, public_token=token, is_active=True)
    
    if not meeting.allow_questions:
        messages.error(request, 'Esta reunión no permite preguntas.')
        return redirect('meeting_public', token=token)
    
    # Verificar si hay un asistente registrado en la sesión
    session_key = f'meeting_{meeting.id}_attendee_id'
    user_attendee = None
    
    if session_key in request.session:
        try:
            attendee_id = request.session[session_key]
            user_attendee = MeetingAttendee.objects.get(id=attendee_id, meeting=meeting)
        except MeetingAttendee.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = MeetingQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.meeting = meeting
            question.attendee = user_attendee  # Asociar con el asistente de la sesión
            question.ip_address = request.META.get('REMOTE_ADDR')
            
            # Si no hay asistente en sesión, usar los datos del formulario
            if not user_attendee:
                question.asker_name = question.asker_name or 'Anónimo'
                question.asker_email = question.asker_email or ''
            else:
                question.asker_name = user_attendee.name
                question.asker_email = user_attendee.email
            
            question.save()
            messages.success(request, '¡Tu pregunta ha sido enviada!')
            return redirect('meeting_public', token=token)
    else:
        form = MeetingQuestionForm()
    
    context = {
        'page_title': f'Hacer Pregunta: {meeting.title}',
        'meeting': meeting,
        'form': form,
    }
    return render(request, 'tickets/meeting_ask_question.html', context)
    
    context = {
        'page_title': f'Hacer Pregunta: {meeting.title}',
        'meeting': meeting,
        'form': form,
    }
    return render(request, 'tickets/meeting_ask_question.html', context)


@login_required
@user_passes_test(is_agent, login_url='/')
def meeting_answer_question_view(request, pk, question_id):
    """Vista AJAX para responder preguntas"""
    from .models import Meeting, MeetingQuestion
    import json
    
    meeting = get_object_or_404(Meeting, pk=pk, organizer=request.user)
    question = get_object_or_404(MeetingQuestion, pk=question_id, meeting=meeting)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            answer = data.get('answer', '').strip()
            
            if not answer:
                return JsonResponse({
                    'success': False,
                    'error': 'La respuesta no puede estar vacía.'
                })
            
            question.answer = answer
            question.answered_by = request.user
            question.answered_at = timezone.now()
            question.status = 'answered'
            question.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Pregunta respondida exitosamente.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar la respuesta: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})


# ========================
# SISTEMA DE CAPACITACIÓN
# ========================

@login_required
def debug_user_access(request):
    """Vista de debug para verificar acceso de usuarios a cursos"""
    from .models import Course, Company
    from django.http import HttpResponse
    
    debug_info = []
    debug_info.append(f"Usuario actual: {request.user.username}")
    debug_info.append(f"Es agente: {request.user.groups.filter(name='Agentes').exists()}")
    
    try:
        profile = request.user.userprofile
        debug_info.append(f"UserProfile existe: Sí")
        debug_info.append(f"Empresa del usuario: {profile.company}")
        debug_info.append(f"ID de empresa del usuario: {profile.company.id if profile.company else 'None'}")
    except Exception as e:
        debug_info.append(f"Error con UserProfile: {e}")
    
    debug_info.append("\n--- CURSOS ---")
    courses = Course.objects.filter(is_active=True)
    for course in courses:
        debug_info.append(f"\nCurso: {course.title}")
        debug_info.append(f"Empresa del curso: {course.company}")
        debug_info.append(f"ID empresa del curso: {course.company.id if course.company else 'None'}")
        debug_info.append(f"Puede acceder: {course.can_user_access(request.user)}")
    
    debug_info.append("\n--- EMPRESAS ---")
    companies = Company.objects.all()
    for company in companies:
        debug_info.append(f"Empresa: {company.name} (ID: {company.id})")
    
    return HttpResponse("<pre>" + "\n".join(debug_info) + "</pre>")

@login_required
def course_generate_public_token(request, pk):
    """Generar token público para un curso"""
    from .models import Course
    from django.contrib import messages
    from django.http import JsonResponse
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    # Verificar permisos - solo el creador o superusuario
    if course.created_by != request.user and not request.user.is_superuser:
        # Verificar si es una petición AJAX usando headers
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'No tienes permisos para esta acción'})
        messages.error(request, 'No tienes permisos para generar enlaces públicos.')
        return redirect('course_detail', pk=pk)
    
    # Generar token
    token = course.generate_public_token()
    public_url = course.get_public_url(request)
    
    # Verificar si es una petición AJAX usando headers
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'token': str(token),
            'public_url': public_url,
            'message': 'Enlace público generado exitosamente'
        })
    
    messages.success(request, f'Enlace público generado: {public_url}')
    return redirect('course_detail', pk=pk)

@login_required
def course_disable_public_access(request, pk):
    """Deshabilitar acceso público a un curso"""
    from .models import Course
    from django.contrib import messages
    from django.http import JsonResponse
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    # Verificar permisos
    if course.created_by != request.user and not request.user.is_superuser:
        # Verificar si es una petición AJAX usando headers
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'No tienes permisos para esta acción'})
        messages.error(request, 'No tienes permisos para deshabilitar el acceso público.')
        return redirect('course_detail', pk=pk)
    
    course.disable_public_access()
    
    # Verificar si es una petición AJAX usando headers
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Acceso público deshabilitado'})
    
    messages.success(request, 'Acceso público deshabilitado correctamente.')
    return redirect('course_detail', pk=pk)

def course_public(request, token):
    """Vista pública del curso (sin autenticación requerida)"""
    from .models import Course, CourseClassView
    from django.shortcuts import get_object_or_404
    
    course = get_object_or_404(
        Course, 
        public_token=token, 
        is_public_enabled=True, 
        is_active=True
    )
    
    classes = course.classes.filter(is_active=True).order_by('order', 'title')
    
    # Agregar información de visualizaciones para cada clase
    classes_with_views = []
    for course_class in classes:
        view_count = course_class.get_view_count()
        user_has_viewed = False
        
        # Si hay usuario autenticado, verificar si ha visto la clase
        if request.user.is_authenticated:
            user_has_viewed = course_class.is_viewed_by_user(request.user)
        
        classes_with_views.append({
            'class': course_class,
            'view_count': view_count,
            'user_has_viewed': user_has_viewed,
            'status': 'vista' if user_has_viewed else 'sin ver'
        })
    
    context = {
        'course': course,
        'classes_with_views': classes_with_views,
        'page_title': f'Curso: {course.title}',
        'is_public_view': True
    }
    
    return render(request, 'tickets/course_public.html', context)

def course_class_public(request, token, class_id):
    """Vista pública de una clase específica"""
    from .models import Course, CourseClass, CourseClassView
    
    course = get_object_or_404(
        Course, 
        public_token=token, 
        is_public_enabled=True, 
        is_active=True
    )
    course_class = get_object_or_404(CourseClass, pk=class_id, course=course, is_active=True)
    
    # Verificar si el usuario autenticado ha visto la clase
    user_has_viewed = False
    if request.user.is_authenticated:
        user_has_viewed = course_class.is_viewed_by_user(request.user)
    
    # Registrar la visualización solo si hay usuario autenticado
    if request.user.is_authenticated:
        view_obj, created = CourseClassView.objects.get_or_create(
            course_class=course_class,
            user=request.user,
            defaults={
                'ip_address': get_client_ip(request)
            }
        )
        
        # Incrementar contador de vistas solo si es una nueva visualización
        if created:
            course_class.save()
    
    # Obtener clases siguientes y anteriores
    all_classes = course.classes.filter(is_active=True).order_by('order', 'title')
    current_index = None
    
    for i, class_item in enumerate(all_classes):
        if class_item.pk == course_class.pk:
            current_index = i
            break
    
    prev_class = None
    next_class = None
    
    if current_index is not None:
        if current_index > 0:
            prev_class = all_classes[current_index - 1]
        if current_index < len(all_classes) - 1:
            next_class = all_classes[current_index + 1]
    
    context = {
        'course': course,
        'course_class': course_class,
        'page_title': f'{course.title} - {course_class.title}',
        'user_has_viewed': user_has_viewed,
        'prev_class': prev_class,
        'next_class': next_class,
    }
    
    return render(request, 'tickets/course_class_public.html', context)

@login_required
def course_list(request):
    """Lista todos los cursos disponibles"""
    from .models import Course
    
    # Verificar si el usuario es agente
    is_agent = request.user.groups.filter(name='Agentes').exists()
    
    # Filtrar cursos según la empresa del usuario
    courses = Course.objects.filter(is_active=True)
    
    if is_agent:
        # Los agentes siempre ven todos los cursos (públicos y empresariales)
        user_accessible_courses = list(courses)
    else:
        # Filtrar según empresa del usuario para usuarios no agentes
        user_accessible_courses = []
        for course in courses:
            if course.can_user_access(request.user):
                user_accessible_courses.append(course)
    
    context = {
        'courses': user_accessible_courses,
        'page_title': 'Cursos de Capacitación'
    }
    
    return render(request, 'tickets/course_list.html', context)


@login_required
def course_detail(request, pk):
    """Detalle de un curso con sus clases"""
    from .models import Course
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    # Verificar si el usuario es agente
    is_agent = request.user.groups.filter(name='Agentes').exists()
    
    # Verificar si el usuario puede acceder a este curso
    if not is_agent and not course.can_user_access(request.user):
        messages.error(request, 'No tienes permisos para acceder a este curso.')
        return redirect('course_list')
    
    classes = course.classes.filter(is_active=True).order_by('order', 'title')
    
    # Agregar información de visualizaciones para cada clase
    classes_with_views = []
    for course_class in classes:
        view_count = course_class.get_view_count()
        user_has_viewed = course_class.is_viewed_by_user(request.user)
        
        classes_with_views.append({
            'class': course_class,
            'view_count': view_count,
            'user_has_viewed': user_has_viewed,
        })
    
    context = {
        'course': course,
        'classes': classes,
        'classes_with_views': classes_with_views,
        'page_title': f'Curso: {course.title}'
    }
    
    return render(request, 'tickets/course_detail.html', context)


@login_required
def course_create(request):
    """Crear nuevo curso (solo agentes)"""
    from .models import Course
    from .forms import CourseForm
    from . import utils
    
    if not utils.is_agent(request.user):
        messages.error(request, 'Solo los agentes pueden crear cursos.')
        return redirect('course_list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            messages.success(request, f'Curso "{course.title}" creado exitosamente.')
            return redirect('course_detail', pk=course.pk)
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Nuevo Curso'
    }
    
    return render(request, 'tickets/course_form.html', context)


@login_required
def course_edit(request, pk):
    """Editar curso (solo agentes)"""
    from .models import Course
    from .forms import CourseForm
    from . import utils
    
    course = get_object_or_404(Course, pk=pk)
    
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Curso "{course.title}" actualizado exitosamente.')
            return redirect('course_detail', pk=pk)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
        'page_title': f'Editar: {course.title}'
    }
    
    return render(request, 'tickets/course_form.html', context)


@login_required
def course_delete(request, pk):
    """Eliminar curso (solo agentes)"""
    from .models import Course
    from . import utils
    
    course = get_object_or_404(Course, pk=pk)
    
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Curso "{course_title}" eliminado exitosamente.')
        return redirect('course_list')
    
    context = {
        'course': course,
        'page_title': f'Eliminar: {course.title}'
    }
    
    return render(request, 'tickets/course_delete.html', context)


@login_required
def course_class_create(request, course_id):
    """Crear nueva clase para un curso (solo agentes)"""
    from .models import Course, CourseClass
    from .forms import CourseClassForm
    from . import utils
    
    course = get_object_or_404(Course, pk=course_id)
    
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        form = CourseClassForm(request.POST)
        if form.is_valid():
            course_class = form.save(commit=False)
            course_class.course = course
            course_class.created_by = request.user
            course_class.save()
            messages.success(request, f'Clase "{course_class.title}" agregada exitosamente.')
            return redirect('course_detail', pk=course_id)
    else:
        # Sugerir el siguiente número de orden
        next_order = course.classes.count() + 1
        form = CourseClassForm(initial={'order': next_order})
    
    context = {
        'form': form,
        'course': course,
        'page_title': f'Nueva Clase - {course.title}'
    }
    
    return render(request, 'tickets/course_class_form.html', context)


@login_required
def course_class_edit(request, course_id, pk):
    """Editar clase (solo agentes)"""
    from .models import Course, CourseClass
    from .forms import CourseClassForm
    from . import utils
    
    course = get_object_or_404(Course, pk=course_id)
    course_class = get_object_or_404(CourseClass, pk=pk, course=course)
    
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        form = CourseClassForm(request.POST, instance=course_class)
        if form.is_valid():
            form.save()
            messages.success(request, f'Clase "{course_class.title}" actualizada exitosamente.')
            return redirect('course_detail', pk=course_id)
    else:
        form = CourseClassForm(instance=course_class)
    
    context = {
        'form': form,
        'course': course,
        'course_class': course_class,
        'page_title': f'Editar: {course_class.title}'
    }
    
    return render(request, 'tickets/course_class_form.html', context)


@login_required
def course_class_delete(request, course_id, pk):
    """Eliminar clase (solo agentes)"""
    from .models import Course, CourseClass
    from . import utils
    
    course = get_object_or_404(Course, pk=course_id)
    course_class = get_object_or_404(CourseClass, pk=pk, course=course)
    
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    if request.method == 'POST':
        class_title = course_class.title
        course_class.delete()
        messages.success(request, f'Clase "{class_title}" eliminada exitosamente.')
        return redirect('course_detail', pk=course_id)
    
    context = {
        'course': course,
        'course_class': course_class,
        'page_title': f'Eliminar: {course_class.title}'
    }
    
    return render(request, 'tickets/course_class_delete.html', context)


@login_required
def course_class_detail(request, course_id, pk):
    """Ver detalle de una clase específica"""
    from .models import Course, CourseClass, CourseClassView
    
    course = get_object_or_404(Course, pk=course_id, is_active=True)
    course_class = get_object_or_404(CourseClass, pk=pk, course=course, is_active=True)
    
    # Verificar si el usuario es agente
    is_agent = request.user.groups.filter(name='Agentes').exists()
    
    # Verificar si el usuario puede acceder a este curso
    if not is_agent and not course.can_user_access(request.user):
        messages.error(request, 'No tienes permisos para acceder a este curso.')
        return redirect('course_list')
    
    # Registrar la visualización si no existe
    view_obj, created = CourseClassView.objects.get_or_create(
        course_class=course_class,
        user=request.user,
        defaults={
            'ip_address': get_client_ip(request)
        }
    )
    
    # Obtener clases anterior y siguiente para navegación
    all_classes = course.classes.filter(is_active=True).order_by('order', 'title')
    current_index = None
    
    for i, class_item in enumerate(all_classes):
        if class_item.pk == course_class.pk:
            current_index = i
            break
    
    prev_class = None
    next_class = None
    
    if current_index is not None:
        if current_index > 0:
            prev_class = all_classes[current_index - 1]
        if current_index < len(all_classes) - 1:
            next_class = all_classes[current_index + 1]
    
    context = {
        'course': course,
        'course_class': course_class,
        'page_title': f'{course.title} - {course_class.title}',
        'user_has_viewed': True,  # Siempre True ya que acabamos de registrar la vista
        'prev_class': prev_class,
        'next_class': next_class,
    }
    
    return render(request, 'tickets/course_class_detail.html', context)


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def mark_class_as_viewed(request, course_id, class_id):
    """Marcar una clase como vista via AJAX"""
    from .models import Course, CourseClass, CourseClassView
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        course = get_object_or_404(Course, pk=course_id, is_active=True)
        course_class = get_object_or_404(CourseClass, pk=class_id, course=course, is_active=True)
        
        # Verificar si el usuario es agente
        is_agent = request.user.groups.filter(name='Agentes').exists()
        
        # Verificar si el usuario puede acceder a este curso
        if not is_agent and not course.can_user_access(request.user):
            return JsonResponse({'success': False, 'error': 'No tienes permisos para acceder a este curso'})
        
        # Crear o actualizar la visualización
        view_obj, created = CourseClassView.objects.get_or_create(
            course_class=course_class,
            user=request.user,
            defaults={
                'ip_address': get_client_ip(request)
            }
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'view_count': course_class.get_view_count(),
            'message': 'Clase marcada como vista' if created else 'Ya habías visto esta clase'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ===== VISTAS DE CONTACTOS =====

@login_required
def contact_list(request):
    """Lista de contactos con filtros"""
    contacts = Contact.objects.all()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        contacts = contacts.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        contacts = contacts.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(company__icontains=search) |
            Q(phone__icontains=search)
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        contacts = contacts.filter(contact_date__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        contacts = contacts.filter(contact_date__date__lte=date_to)
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(contacts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_contacts = Contact.objects.count()
    positive_contacts = Contact.objects.filter(status='positive').count()
    negative_contacts = Contact.objects.filter(status='negative').count()
    today_contacts = Contact.objects.filter(contact_date__date=timezone.now().date()).count()
    
    context = {
        'page_obj': page_obj,
        'contacts': page_obj.object_list,
        'total_contacts': total_contacts,
        'positive_contacts': positive_contacts,
        'negative_contacts': negative_contacts,
        'today_contacts': today_contacts,
        'page_title': 'Contactos'
    }
    
    return render(request, 'tickets/contact_list.html', context)


@login_required
def contact_create(request):
    """Crear nuevo contacto"""
    from .forms import ContactForm
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.created_by = request.user
            contact.save()
            
            messages.success(request, f'Contacto "{contact.name}" creado exitosamente.')
            return redirect('contact_detail', pk=contact.pk)
    else:
        form = ContactForm()
    
    context = {
        'form': form,
        'page_title': 'Nuevo Contacto'
    }
    
    return render(request, 'tickets/contact_form.html', context)


@login_required
def contact_detail(request, pk):
    """Ver detalles de un contacto"""
    contact = get_object_or_404(Contact, pk=pk)
    
    context = {
        'contact': contact,
        'page_title': f'Contacto: {contact.name}'
    }
    
    return render(request, 'tickets/contact_detail.html', context)


@login_required
def contact_edit(request, pk):
    """Editar contacto"""
    from .forms import ContactForm
    
    contact = get_object_or_404(Contact, pk=pk)
    
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Contacto "{contact.name}" actualizado exitosamente.')
            return redirect('contact_detail', pk=contact.pk)
    else:
        form = ContactForm(instance=contact)
    
    context = {
        'form': form,
        'contact': contact,
        'page_title': f'Editar: {contact.name}'
    }
    
    return render(request, 'tickets/contact_form.html', context)


@login_required
def contact_delete(request, pk):
    """Eliminar contacto"""
    contact = get_object_or_404(Contact, pk=pk)
    
    if request.method == 'POST':
        contact_name = contact.name
        contact.delete()
        messages.success(request, f'Contacto "{contact_name}" eliminado exitosamente.')
        return redirect('contact_list')
    
    context = {
        'contact': contact,
        'page_title': f'Eliminar: {contact.name}'
    }
    
    return render(request, 'tickets/contact_delete.html', context)


# ===== VISTAS DEL BLOG =====

def blog_list(request):
    """Lista pública de artículos del blog"""
    posts = BlogPost.objects.filter(status='published').select_related('category', 'created_by')
    
    # Filtros
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    search = request.GET.get('search')
    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(excerpt__icontains=search) |
            Q(content__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorías para el menú
    categories = BlogCategory.objects.filter(is_active=True)
    
    # Artículos destacados
    featured_posts = BlogPost.objects.filter(
        status='published', 
        is_featured=True
    ).select_related('category')[:3]
    
    context = {
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'categories': categories,
        'featured_posts': featured_posts,
        'current_category': category_slug,
        'page_title': 'Blog',
        'is_authenticated': request.user.is_authenticated,
    }
    
    return render(request, 'tickets/blog_list.html', context)


def blog_post_detail(request, slug):
    """Vista detalle de un artículo del blog"""
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    # Incrementar contador de visualizaciones
    post.increment_views()
    
    # Procesar comentarios
    if request.method == 'POST':
        from .forms import BlogCommentForm
        comment_form = BlogCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            
            # Obtener IP del usuario
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                comment.ip_address = x_forwarded_for.split(',')[0]
            else:
                comment.ip_address = request.META.get('REMOTE_ADDR')
            
            comment.save()
            messages.success(request, 'Tu comentario ha sido enviado y está pendiente de aprobación.')
            return redirect('blog_post_detail', slug=slug)
    else:
        from .forms import BlogCommentForm
        comment_form = BlogCommentForm()
    
    # Comentarios aprobados
    comments = post.comments.filter(is_approved=True).order_by('created_at')
    
    # Artículos relacionados
    related_posts = BlogPost.objects.filter(
        status='published',
        category=post.category
    ).exclude(pk=post.pk)[:3]
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'related_posts': related_posts,
        'page_title': post.title,
        'is_authenticated': request.user.is_authenticated,
    }
    
    return render(request, 'tickets/blog_post_detail.html', context)


@login_required
def blog_category_list(request):
    """Lista de categorías del blog (admin)"""
    categories = BlogCategory.objects.all().order_by('name')
    
    context = {
        'categories': categories,
        'page_title': 'Categorías de Blog'
    }
    
    return render(request, 'tickets/blog_category_list.html', context)


@login_required
def blog_category_create(request):
    """Crear nueva categoría de blog"""
    from .forms import BlogCategoryForm
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")
        form = BlogCategoryForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        
        if form.is_valid():
            try:
                category = form.save(commit=False)
                category.created_by = request.user
                
                # Auto-generar slug único
                from django.utils.text import slugify
                base_slug = slugify(category.name)
                slug = base_slug
                counter = 1
                
                # Verificar si el slug ya existe y crear uno único
                while BlogCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                category.slug = slug
                category.save()
                print(f"Categoría creada: {category.name} - {category.slug}")
                
                messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
                return redirect('blog_category_list')
                
            except Exception as e:
                print(f"Exception al crear categoría: {str(e)}")
                messages.error(request, f'Error al crear la categoría: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = BlogCategoryForm()
    
    context = {
        'form': form,
        'page_title': 'Nueva Categoría'
    }
    
    return render(request, 'tickets/blog_category_form.html', context)


@login_required
def blog_post_list_admin(request):
    """Lista de artículos del blog (admin)"""
    posts = BlogPost.objects.all().select_related('category', 'created_by')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        posts = posts.filter(status=status)
    
    category_id = request.GET.get('category')
    if category_id:
        posts = posts.filter(category_id=category_id)
    
    search = request.GET.get('search')
    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(excerpt__icontains=search)
        )
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = BlogCategory.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'categories': categories,
        'page_title': 'Gestión de Blog'
    }
    
    return render(request, 'tickets/blog_post_list_admin.html', context)


@login_required
def blog_post_create(request):
    """Crear nuevo artículo de blog"""
    from .forms import BlogPostForm
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.created_by = request.user
            post.save()
            
            messages.success(request, f'Artículo "{post.title}" creado exitosamente.')
            return redirect('blog_post_detail_admin', pk=post.pk)
    else:
        form = BlogPostForm()
    
    context = {
        'form': form,
        'page_title': 'Nuevo Artículo'
    }
    
    return render(request, 'tickets/blog_post_form.html', context)


@login_required
def blog_post_detail_admin(request, pk):
    """Vista detalle de artículo (admin)"""
    post = get_object_or_404(BlogPost, pk=pk)
    
    # Comentarios pendientes
    pending_comments = post.comments.filter(is_approved=False).order_by('-created_at')
    approved_comments = post.comments.filter(is_approved=True).order_by('-created_at')
    
    context = {
        'post': post,
        'pending_comments': pending_comments,
        'approved_comments': approved_comments,
        'page_title': f'Artículo: {post.title}'
    }
    
    return render(request, 'tickets/blog_post_detail_admin.html', context)


@login_required
def blog_comment_approve(request, pk):
    """Aprobar comentario"""
    comment = get_object_or_404(BlogComment, pk=pk)
    comment.is_approved = True
    comment.save()
    
    messages.success(request, 'Comentario aprobado exitosamente.')
    return redirect('blog_post_detail_admin', pk=comment.post.pk)


@login_required
def blog_comment_delete(request, pk):
    """Eliminar comentario"""
    comment = get_object_or_404(BlogComment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    
    messages.success(request, 'Comentario eliminado exitosamente.')
    return redirect('blog_post_detail_admin', pk=post_pk)


@login_required
def blog_post_edit(request, pk):
    """Editar artículo de blog"""
    from .forms import BlogPostForm
    
    post = get_object_or_404(BlogPost, pk=pk)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            
            # Si se está publicando por primera vez, establecer fecha de publicación
            if post.status == 'published' and not post.published_at:
                from django.utils import timezone
                post.published_at = timezone.now()
            
            post.save()
            messages.success(request, f'Artículo "{post.title}" actualizado exitosamente.')
            return redirect('blog_post_detail_admin', pk=post.pk)
    else:
        form = BlogPostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'page_title': f'Editar: {post.title}',
        'action': 'Actualizar'
    }
    
    return render(request, 'tickets/blog_post_form.html', context)


@login_required
def blog_post_toggle_status(request, pk):
    """Cambiar estado de publicación del artículo"""
    post = get_object_or_404(BlogPost, pk=pk)
    
    if post.status == 'published':
        post.status = 'draft'
        post.published_at = None
        messages.success(request, f'Artículo "{post.title}" despublicado.')
    else:
        post.status = 'published'
        if not post.published_at:
            from django.utils import timezone
            post.published_at = timezone.now()
        messages.success(request, f'Artículo "{post.title}" publicado exitosamente.')
    
    post.save()
    return redirect('blog_post_detail_admin', pk=post.pk)


@login_required
def blog_post_delete(request, pk):
    """Eliminar artículo de blog"""
    post = get_object_or_404(BlogPost, pk=pk)
    
    if request.method == 'POST':
        title = post.title
        post.delete()
        messages.success(request, f'Artículo "{title}" eliminado exitosamente.')
        return redirect('blog_post_list_admin')
    
    context = {
        'post': post,
        'page_title': f'Eliminar: {post.title}'
    }
    
    return render(request, 'tickets/blog_post_delete.html', context)


# ===========================================
# VISTAS PARA CHAT CON IA
# ===========================================

@login_required
def ai_chat_list_view(request):
    """Vista principal del chat con IA - lista de sesiones"""
    config = SystemConfiguration.get_config()
    
    # Verificar si el chat IA está habilitado
    if not config.ai_chat_enabled:
        messages.warning(request, 'El chat con IA no está habilitado en el sistema.')
        return redirect('dashboard')
    
    # Verificar si hay API key configurada
    if not config.openai_api_key:
        messages.warning(request, 'El chat con IA no está configurado. Contacta al administrador.')
        return redirect('dashboard')
    
    # Obtener sesiones del usuario
    sessions = AIChatSession.objects.filter(user=request.user, is_active=True)
    
    # Formulario para nueva sesión
    if request.method == 'POST':
        form = AIChatSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            messages.success(request, f'Nueva conversación creada: {session.title}')
            return redirect('ai_chat_live', session_id=session.id)
    else:
        form = AIChatSessionForm(initial={'ai_model': config.openai_model})
    
    context = {
        'sessions': sessions,
        'form': form,
        'config': config,
    }
    
    return render(request, 'tickets/ai_chat_list.html', context)


@login_required
def ai_chat_session_view(request, session_id):
    """Vista para una sesión específica de chat con IA"""
    config = SystemConfiguration.get_config()
    
    # Verificar si el chat IA está habilitado
    if not config.ai_chat_enabled or not config.openai_api_key:
        messages.warning(request, 'El chat con IA no está disponible.')
        return redirect('dashboard')
    
    # Obtener la sesión
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user, is_active=True)
    
    # Obtener mensajes de la sesión
    messages_list = session.messages.all()
    
    # Formulario para nuevo mensaje
    if request.method == 'POST':
        print(f"DEBUG: POST recibido para sesión {session_id}")
        print(f"DEBUG: request.POST completo: {dict(request.POST)}")
        print(f"DEBUG: request.POST.get('message'): '{request.POST.get('message', 'NO_ENCONTRADO')}'")
        print(f"DEBUG: Content-Type: {request.content_type}")
        print(f"DEBUG: POST keys: {list(request.POST.keys())}")
        
        form = AIChatMessageForm(request.POST)
        print(f"DEBUG: Formulario creado con datos: {form.data}")
        print(f"DEBUG: Formulario es válido: {form.is_valid()}")
        
        if form.is_valid():
            user_message = form.cleaned_data['message']
            print(f"DEBUG: Mensaje del usuario: {user_message}")
            
            # Guardar mensaje del usuario
            user_msg = AIChatMessage.objects.create(
                session=session,
                role='user',
                content=user_message
            )
            print(f"DEBUG: Mensaje del usuario guardado con ID: {user_msg.id}")
            
            # Llamar a la API de OpenAI
            try:
                print("DEBUG: Llamando a OpenAI API...")
                ai_response = call_openai_api(session, user_message)
                print(f"DEBUG: Respuesta de OpenAI recibida: {ai_response['content'][:50]}...")
                
                # Guardar respuesta de la IA
                ai_msg = AIChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=ai_response['content'],
                    tokens_used=ai_response.get('tokens_used', 0)
                )
                print(f"DEBUG: Respuesta de IA guardada con ID: {ai_msg.id}")
                
                messages.success(request, 'Mensaje enviado correctamente.')
                
            except Exception as e:
                print(f"DEBUG: Error en OpenAI API: {str(e)}")
                messages.error(request, f'Error al comunicarse con la IA: {str(e)}')
            
            return redirect('ai_chat_session', session_id=session.id)
        else:
            print(f"DEBUG: Formulario no válido. Errores: {form.errors}")
            print(f"DEBUG: Errores por campo: {dict(form.errors)}")
            for field, errors in form.errors.items():
                print(f"DEBUG: Campo '{field}': {errors}")
    else:
        form = AIChatMessageForm()
    
    context = {
        'session': session,
        'messages_list': messages_list,
        'form': form,
        'config': config,
    }
    
    return render(request, 'tickets/ai_chat_session.html', context)


@login_required
def ai_chat_delete_session_view(request, session_id):
    """Vista para eliminar una sesión de chat"""
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        session.is_active = False
        session.save()
        messages.success(request, f'Conversación "{session.title}" eliminada.')
        return redirect('ai_chat_list')
    
    context = {
        'session': session,
    }
    
    return render(request, 'tickets/ai_chat_delete_session.html', context)


@login_required
def ai_chat_debug_view(request, session_id):
    """Vista de debug para chat IA"""
    config = SystemConfiguration.get_config()
    
    # Obtener la sesión
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user, is_active=True)
    
    # Obtener mensajes de la sesión
    messages_list = session.messages.all()
    
    # Formulario para nuevo mensaje
    if request.method == 'POST':
        print(f"DEBUG: POST recibido para sesión {session_id}")
        print(f"DEBUG: Datos POST: {request.POST}")
        
        form = AIChatMessageForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data['message']
            print(f"DEBUG: Mensaje del usuario: {user_message}")
            
            # Guardar mensaje del usuario
            user_msg = AIChatMessage.objects.create(
                session=session,
                role='user',
                content=user_message
            )
            print(f"DEBUG: Mensaje del usuario guardado con ID: {user_msg.id}")
            
            # Llamar a la API de OpenAI
            try:
                print("DEBUG: Llamando a OpenAI API...")
                ai_response = call_openai_api(session, user_message)
                print(f"DEBUG: Respuesta de OpenAI recibida: {ai_response['content'][:50]}...")
                
                # Guardar respuesta de la IA
                ai_msg = AIChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=ai_response['content'],
                    tokens_used=ai_response.get('tokens_used', 0)
                )
                print(f"DEBUG: Respuesta de IA guardada con ID: {ai_msg.id}")
                
                messages.success(request, 'Mensaje enviado correctamente.')
                
            except Exception as e:
                print(f"DEBUG: Error en OpenAI API: {str(e)}")
                messages.error(request, f'Error al comunicarse con la IA: {str(e)}')
            
            return redirect('ai_chat_debug', session_id=session.id)
        else:
            print(f"DEBUG: Formulario no válido: {form.errors}")
    else:
        form = AIChatMessageForm()
    
    context = {
        'session': session,
        'messages_list': messages_list,
        'form': form,
        'page_title': f'Debug Chat IA - {session.title}',
    }
    
    return render(request, 'tickets/ai_chat_debug.html', context)


@login_required
def ai_chat_simple_view(request, session_id):
    """Vista simple del chat IA para debugging"""
    config = SystemConfiguration.get_config()
    
    # Verificar configuración
    if not config.ai_chat_enabled or not config.openai_api_key:
        messages.warning(request, 'El chat con IA no está disponible.')
        return redirect('dashboard')
    
    # Obtener sesión
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user, is_active=True)
    messages_list = session.messages.all()
    
    # Procesar formulario
    if request.method == 'POST':
        print(f"=== POST SIMPLE RECIBIDO ===")
        print(f"request.POST: {dict(request.POST)}")
        print(f"message value: '{request.POST.get('message', 'NO_ENCONTRADO')}'")
        
        message_content = request.POST.get('message', '').strip()
        
        if len(message_content) >= 5:
            try:
                # Guardar mensaje del usuario
                user_msg = AIChatMessage.objects.create(
                    session=session,
                    role='user',
                    content=message_content
                )
                print(f"Usuario mensaje guardado: {user_msg.id}")
                
                # Llamar a OpenAI
                ai_response = call_openai_api(session, message_content)
                
                # Guardar respuesta IA
                ai_msg = AIChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=ai_response['content'],
                    tokens_used=ai_response.get('tokens_used', 0)
                )
                print(f"IA mensaje guardado: {ai_msg.id}")
                
                messages.success(request, 'Mensaje enviado correctamente.')
                return redirect('ai_chat_simple', session_id=session.id)
                
            except Exception as e:
                print(f"Error: {e}")
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'El mensaje debe tener al menos 5 caracteres.')
    
    # Crear formulario vacío para los errores
    form = AIChatMessageForm()
    
    context = {
        'session': session,
        'messages_list': messages_list,
        'form': form,
        'page_title': f'Chat Simple - {session.title}',
    }
    
    return render(request, 'tickets/ai_chat_simple.html', context)


@login_required
def ai_chat_ajax_send_message(request, session_id):
    """Vista AJAX para enviar mensajes al chat IA"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        config = SystemConfiguration.get_config()
        
        # Verificar configuración
        if not config.ai_chat_enabled or not config.openai_api_key:
            return JsonResponse({'error': 'Chat IA no disponible'}, status=400)
        
        # Obtener sesión
        try:
            session = AIChatSession.objects.get(id=session_id, user=request.user, is_active=True)
        except AIChatSession.DoesNotExist:
            return JsonResponse({'error': 'Sesión no encontrada'}, status=404)
        
        # Obtener mensaje
        message_content = request.POST.get('message', '').strip()
        
        if len(message_content) < 5:
            return JsonResponse({'error': 'El mensaje debe tener al menos 5 caracteres'}, status=400)
        
        # Guardar mensaje del usuario
        user_msg = AIChatMessage.objects.create(
            session=session,
            role='user',
            content=message_content
        )
        
        # Llamar a OpenAI
        ai_response = call_openai_api(session, message_content)
        
        # Guardar respuesta IA
        ai_msg = AIChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response['content'],
            tokens_used=ai_response.get('tokens_used', 0)
        )
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'created_at': user_msg.created_at.strftime('%H:%M')
            },
            'ai_message': {
                'id': ai_msg.id,
                'content': ai_msg.content,
                'created_at': ai_msg.created_at.strftime('%H:%M'),
                'tokens_used': ai_msg.tokens_used
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error completo: {traceback.format_exc()}")
        return JsonResponse({'error': f'Error al procesar mensaje: {str(e)}'}, status=500)


@login_required
def ai_chat_live_view(request, session_id):
    """Vista mejorada del chat IA con AJAX y UX mejorada"""
    config = SystemConfiguration.get_config()
    
    # Verificar configuración
    if not config.ai_chat_enabled:
        messages.warning(request, 'El chat con IA no está habilitado en el sistema.')
        return redirect('dashboard')
    
    if not config.openai_api_key:
        messages.warning(request, 'El chat con IA no está configurado. Contacta al administrador.')
        return redirect('dashboard')
    
    # Obtener sesión
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user, is_active=True)
    
    # Obtener mensajes
    messages_list = session.messages.all()
    
    context = {
        'session': session,
        'messages_list': messages_list,
        'page_title': f'{session.title} - Chat IA',
    }
    
    return render(request, 'tickets/ai_chat_live.html', context)


@login_required
def ai_chat_modern_view(request, session_id):
    """Vista del chat IA con diseño moderno (Telegram/Discord style)"""
    config = SystemConfiguration.get_config()
    
    # Verificar configuración
    if not config.ai_chat_enabled:
        messages.warning(request, 'El chat con IA no está habilitado en el sistema.')
        return redirect('dashboard')
    
    if not config.openai_api_key:
        messages.warning(request, 'El chat con IA no está configurado. Contacta al administrador.')
        return redirect('dashboard')
    
    # Obtener sesión
    session = get_object_or_404(AIChatSession, id=session_id, user=request.user, is_active=True)
    
    # Obtener mensajes
    messages_list = session.messages.all()
    
    context = {
        'session': session,
        'messages': messages_list,  # Cambio de nombre para el template moderno
        'page_title': f'{session.title} - Chat IA',
    }
    
    return render(request, 'tickets/ai_chat_modern.html', context)


# Helper function for AI analysis
def call_openai_api(session, message_content):
    """
    Función auxiliar para llamar a la API de OpenAI
    """
    config = SystemConfiguration.get_config()
    
    if not config.openai_api_key:
        raise Exception('API key de OpenAI no configurada')
    
    from openai import OpenAI
    client = OpenAI(api_key=config.openai_api_key)
    
    # Obtener historial de mensajes para contexto
    previous_messages = session.messages.order_by('created_at')[:10]  # Últimos 10 mensajes
    messages = [{"role": "system", "content": "Eres un asistente IA útil y conversacional."}]
    
    # Agregar mensajes previos para contexto
    for msg in previous_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Agregar mensaje actual
    messages.append({
        "role": "user",
        "content": message_content
    })
    
    response = client.chat.completions.create(
        model=config.openai_model or 'gpt-4o-mini',
        messages=messages,
        max_tokens=2000,
        temperature=0.7
    )
    
    return {
        'content': response.choices[0].message.content,
        'tokens_used': response.usage.total_tokens
    }


@login_required
def improve_ticket_with_ai(request, ticket_id):
    """Vista AJAX para mejorar el título y descripción de un ticket usando IA"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Verificar permisos del ticket
        if is_agent(request.user):
            ticket = get_object_or_404(Ticket, pk=ticket_id)
        else:
            # Los usuarios pueden solo editar sus propios tickets o tickets de su empresa/proyectos
            user_projects = request.user.assigned_projects.all()
            user_company = None
            
            try:
                user_company = request.user.profile.company
            except:
                pass
            
            query_conditions = Q(created_by=request.user)
            if user_projects.exists():
                query_conditions |= Q(project__in=user_projects)
            if user_company:
                query_conditions |= Q(company=user_company)
            
            ticket = get_object_or_404(Ticket, pk=ticket_id)
            if not Ticket.objects.filter(pk=ticket_id).filter(query_conditions).exists():
                return JsonResponse({'error': 'No tienes permisos para mejorar este ticket'}, status=403)
        
        # Verificar configuración de OpenAI
        config = SystemConfiguration.get_config()
        if not config.openai_api_key:
            return JsonResponse({'error': 'API key de OpenAI no configurada'}, status=500)
        
        # Obtener tipo de mejora solicitada
        improvement_type = request.POST.get('type', 'both')  # 'title', 'description', 'both'
        
        # Preparar el prompt según el tipo de mejora
        if improvement_type == 'title':
            prompt = f"""
            Mejora el siguiente título de ticket de soporte técnico para que sea más claro, específico y profesional:

            Título actual: "{ticket.title}"
            Descripción del problema: "{ticket.description}"
            
            Proporciona ÚNICAMENTE un título mejorado, sin explicaciones adicionales.
            El título debe ser:
            - Claro y específico
            - Profesional pero comprensible
            - Máximo 100 caracteres
            - Debe reflejar exactamente el problema descrito
            """
        elif improvement_type == 'description':
            prompt = f"""
            Mejora la siguiente descripción de ticket de soporte técnico para que sea más clara, detallada y estructurada:

            Título: "{ticket.title}"
            Descripción actual: "{ticket.description}"
            
            Proporciona ÚNICAMENTE una descripción mejorada, sin explicaciones adicionales.
            La descripción debe ser:
            - Clara y bien estructurada
            - Incluir pasos para reproducir si es relevante
            - Mencionar el impacto del problema
            - Ser específica y detallada
            - Mantener el contenido original pero mejor organizado
            """
        else:  # both
            prompt = f"""
            Mejora el siguiente ticket de soporte técnico para que el título y descripción sean más claros, específicos y profesionales:

            Título actual: "{ticket.title}"
            Descripción actual: "{ticket.description}"
            
            Responde ÚNICAMENTE con el siguiente formato JSON sin texto adicional:
            {{
                "title": "título mejorado aquí",
                "description": "descripción mejorada aquí"
            }}
            
            Criterios:
            - Título: Claro, específico, profesional, máximo 100 caracteres
            - Descripción: Clara, estructurada, detallada, bien organizada
            - Mantener el contenido original pero mejorado
            """
        
        # Llamar a OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=config.openai_api_key)
        
        response = client.chat.completions.create(
            model=config.openai_model or 'gpt-4o-mini',
            messages=[
                {"role": "system", "content": "Eres un experto en soporte técnico que mejora la comunicación de tickets para hacerlos más claros y profesionales."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Procesar respuesta según el tipo
        if improvement_type == 'both':
            try:
                import json
                # Limpiar respuesta si tiene marcadores de código
                if ai_response.startswith('```json'):
                    ai_response = ai_response.replace('```json', '').replace('```', '').strip()
                elif ai_response.startswith('```'):
                    ai_response = ai_response.replace('```', '').strip()
                
                result = json.loads(ai_response)
                return JsonResponse({
                    'success': True,
                    'title': result.get('title', ''),
                    'description': result.get('description', ''),
                    'tokens_used': response.usage.total_tokens
                })
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Error al procesar la respuesta de IA'}, status=500)
        else:
            return JsonResponse({
                'success': True,
                improvement_type: ai_response,
                'tokens_used': response.usage.total_tokens
            })
            
    except Exception as e:
        return JsonResponse({'error': f'Error al mejorar ticket: {str(e)}'}, status=500)


@login_required
@user_passes_test(is_agent, login_url='/')
def search_company_info_with_ai(request, company_id):
    """Vista AJAX para buscar información de una empresa en la web usando IA"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        company = get_object_or_404(Company, pk=company_id)
        
        # Verificar configuración de OpenAI
        config = SystemConfiguration.get_config()
        if not config.openai_api_key:
            return JsonResponse({'error': 'API key de OpenAI no configurada'}, status=500)
        
        # Obtener nombre de la empresa del request o usar el actual
        company_name = request.POST.get('company_name', company.name).strip()
        
        if not company_name:
            return JsonResponse({'error': 'Nombre de empresa requerido'}, status=400)
        
        # Prompt para buscar información de la empresa
        prompt = f"""
        Busca información detallada sobre la empresa "{company_name}". 
        
        Proporciona la información en el siguiente formato JSON exacto (sin texto adicional):
        {{
            "name": "nombre oficial completo de la empresa",
            "website": "sitio web principal (con https://)",
            "email": "email principal de contacto",
            "phone": "teléfono principal",
            "address": "dirección completa de la sede principal",
            "description": "descripción detallada de la empresa, sus servicios y actividades",
            "industry": "sector o industria principal",
            "founded": "año de fundación si está disponible",
            "employees": "número aproximado de empleados si está disponible",
            "social_media": {{
                "linkedin": "URL de LinkedIn",
                "twitter": "URL de Twitter",
                "facebook": "URL de Facebook"
            }},
            "additional_info": "información adicional relevante como premios, certificaciones, etc."
        }}
        
        IMPORTANTE:
        - Si no encuentras información específica, usa "No disponible" para ese campo
        - Asegúrate de que el website tenga formato completo (https://)
        - La descripción debe ser informativa y profesional
        - Incluye solo información verificable y actualizada
        """
        
        # Llamar a OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=config.openai_api_key)
        
        response = client.chat.completions.create(
            model=config.openai_model or 'gpt-4o-mini',
            messages=[
                {"role": "system", "content": "Eres un experto investigador de empresas que busca información precisa y actualizada sobre compañías usando fuentes públicas disponibles. Respondes únicamente con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Limpiar respuesta si tiene marcadores de código
        if ai_response.startswith('```json'):
            ai_response = ai_response.replace('```json', '').replace('```', '').strip()
        elif ai_response.startswith('```'):
            ai_response = ai_response.replace('```', '').strip()
        
        try:
            import json
            result = json.loads(ai_response)
            
            # Validar que los campos requeridos estén presentes
            required_fields = ['name', 'website', 'email', 'phone', 'address', 'description']
            for field in required_fields:
                if field not in result:
                    result[field] = 'No disponible'
            
            return JsonResponse({
                'success': True,
                'data': result,
                'tokens_used': response.usage.total_tokens
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Error al procesar la respuesta de IA'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': f'Error al buscar información: {str(e)}'}, status=500)


@login_required
@user_passes_test(is_agent, login_url='/')
def search_company_info_general(request):
    """Vista AJAX para buscar información de una empresa sin requerir ID específico"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Verificar configuración de OpenAI
        config = SystemConfiguration.get_config()
        if not config.openai_api_key:
            return JsonResponse({'error': 'API key de OpenAI no configurada'}, status=500)
        
        # Obtener nombre de la empresa del request
        company_name = request.POST.get('company_name', '').strip()
        
        if not company_name:
            return JsonResponse({'error': 'Nombre de empresa requerido'}, status=400)
        
        # Prompt para buscar información de la empresa
        prompt = f"""
        Busca información detallada sobre la empresa "{company_name}". 
        
        Proporciona la información en el siguiente formato JSON exacto (sin texto adicional):
        {{
            "name": "nombre oficial completo de la empresa",
            "website": "sitio web principal (con https://)",
            "email": "email principal de contacto",
            "phone": "teléfono principal",
            "address": "dirección completa de la sede principal",
            "description": "descripción detallada de la empresa, sus servicios y actividades",
            "industry": "sector o industria principal",
            "founded": "año de fundación si está disponible",
            "employees": "número aproximado de empleados si está disponible",
            "social_media": {{
                "linkedin": "URL de LinkedIn",
                "twitter": "URL de Twitter",
                "facebook": "URL de Facebook"
            }},
            "additional_info": "información adicional relevante como premios, certificaciones, etc."
        }}
        
        IMPORTANTE:
        - Si no encuentras información específica, usa "No disponible" para ese campo
        - Asegúrate de que el website tenga formato completo (https://)
        - La descripción debe ser informativa y profesional
        - Incluye solo información verificable y actualizada
        """
        
        # Llamar a OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=config.openai_api_key)
        
        response = client.chat.completions.create(
            model=config.openai_model or 'gpt-4o-mini',
            messages=[
                {"role": "system", "content": "Eres un experto investigador de empresas que busca información precisa y actualizada sobre compañías usando fuentes públicas disponibles. Respondes únicamente con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Limpiar respuesta si tiene marcadores de código
        if ai_response.startswith('```json'):
            ai_response = ai_response.replace('```json', '').replace('```', '').strip()
        elif ai_response.startswith('```'):
            ai_response = ai_response.replace('```', '').strip()
        
        try:
            import json
            result = json.loads(ai_response)
            
            # Validar que los campos requeridos estén presentes
            required_fields = ['name', 'website', 'email', 'phone', 'address', 'description']
            for field in required_fields:
                if field not in result:
                    result[field] = 'No disponible'
            
            return JsonResponse({
                'success': True,
                'data': result,
                'tokens_used': response.usage.total_tokens
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Error al procesar la respuesta de IA'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': f'Error al buscar información: {str(e)}'}, status=500)


@login_required
@user_passes_test(is_agent, login_url='/')
def enhance_contact_with_ai(request, contact_id):
    """Vista AJAX para mejorar información de un contacto usando IA"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        contact = get_object_or_404(Contact, pk=contact_id)
        
        # Verificar configuración de OpenAI
        config = SystemConfiguration.get_config()
        if not config.openai_api_key:
            return JsonResponse({'error': 'API key de OpenAI no configurada'}, status=500)
        
        # Obtener datos actuales del contacto del request
        import json
        contact_data = json.loads(request.body)
        
        # Construir información existente
        existing_info = []
        if contact_data.get('name'):
            existing_info.append(f"Nombre: {contact_data['name']}")
        if contact_data.get('email'):
            existing_info.append(f"Email: {contact_data['email']}")
        if contact_data.get('phone'):
            existing_info.append(f"Teléfono: {contact_data['phone']}")
        if contact_data.get('position'):
            existing_info.append(f"Posición: {contact_data['position']}")
        if contact_data.get('company'):
            existing_info.append(f"Empresa: {contact_data['company']}")
        if contact_data.get('notes'):
            existing_info.append(f"Notas actuales: {contact_data['notes']}")
        
        if not existing_info:
            return JsonResponse({'error': 'No hay información suficiente para mejorar'}, status=400)
        
        existing_info_text = "\n".join(existing_info)
        
        # Prompt para mejorar información del contacto
        prompt = f"""
        Tienes la siguiente información parcial de un contacto profesional:
        
        {existing_info_text}
        
        Basándote en esta información, busca y proporciona datos adicionales que podrían ser útiles para completar el perfil del contacto. 
        
        Proporciona la respuesta en el siguiente formato JSON exacto (sin texto adicional):
        {{
            "full_name": "nombre completo si es diferente o más completo que el actual",
            "position": "título o posición profesional más específica o completa",
            "professional_title": "título profesional o especialización",
            "email": "email profesional si no está disponible",
            "phone": "teléfono profesional si no está disponible",
            "linkedin": "URL del perfil de LinkedIn si está disponible",
            "company_info": {{
                "name": "nombre completo y correcto de la empresa",
                "industry": "industria o sector de la empresa", 
                "size": "tamaño aproximado de la empresa",
                "location": "ubicación principal de la empresa"
            }},
            "additional_info": "información adicional relevante sobre el contacto, su rol, experiencia, etc.",
            "suggested_notes": "sugerencias de notas profesionales para agregar al contacto basadas en la información encontrada"
        }}
        
        IMPORTANTE:
        - Si no encuentras información específica o no puedes mejorar un campo, usa "No disponible"
        - Proporciona solo información que sea profesionalmente relevante
        - Las sugerencias de notas deben ser útiles para seguimiento comercial o profesional
        - Usa fuentes públicas y profesionales para la información
        - Sé preciso y evita especulaciones
        """
        
        # Llamar a OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=config.openai_api_key)
        
        response = client.chat.completions.create(
            model=config.openai_model or 'gpt-4o-mini',
            messages=[
                {"role": "system", "content": "Eres un experto asistente de CRM que ayuda a completar información de contactos profesionales usando fuentes públicas y conocimiento general del mundo empresarial. Respondes únicamente con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Limpiar respuesta si tiene marcadores de código
        if ai_response.startswith('```json'):
            ai_response = ai_response.replace('```json', '').replace('```', '').strip()
        elif ai_response.startswith('```'):
            ai_response = ai_response.replace('```', '').strip()
        
        try:
            result = json.loads(ai_response)
            
            # Validar que los campos requeridos estén presentes
            required_fields = ['full_name', 'position', 'email', 'phone', 'additional_info', 'suggested_notes']
            for field in required_fields:
                if field not in result:
                    result[field] = 'No disponible'
            
            return JsonResponse({
                'success': True,
                'data': result,
                'tokens_used': response.usage.total_tokens
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Error al procesar la respuesta de IA'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': f'Error al mejorar contacto: {str(e)}'}, status=500)


# =============================================
# VISTAS DE CONCEPTOS
# =============================================

@login_required
@user_passes_test(is_agent)
def concept_list_view(request):
    """Vista para listar todos los conceptos"""
    concepts = Concept.objects.all().order_by('order', 'term')
    
    context = {
        'concepts': concepts,
        'title': 'Gestión de Conceptos'
    }
    return render(request, 'tickets/concept_list.html', context)


@login_required
@user_passes_test(is_agent)
def concept_create_view(request):
    """Vista para crear un nuevo concepto"""
    if request.method == 'POST':
        form = ConceptForm(request.POST)
        if form.is_valid():
            concept = form.save(commit=False)
            concept.created_by = request.user
            concept.save()
            messages.success(request, f'Concepto "{concept.term}" creado exitosamente.')
            return redirect('concept_list')
    else:
        form = ConceptForm()
    
    context = {
        'form': form,
        'title': 'Crear Concepto'
    }
    return render(request, 'tickets/concept_form.html', context)


@login_required
@user_passes_test(is_agent)
def concept_edit_view(request, pk):
    """Vista para editar un concepto existente"""
    concept = get_object_or_404(Concept, pk=pk)
    
    if request.method == 'POST':
        form = ConceptForm(request.POST, instance=concept)
        if form.is_valid():
            form.save()
            messages.success(request, f'Concepto "{concept.term}" actualizado exitosamente.')
            return redirect('concept_list')
    else:
        form = ConceptForm(instance=concept)
    
    context = {
        'form': form,
        'concept': concept,
        'title': 'Editar Concepto'
    }
    return render(request, 'tickets/concept_form.html', context)


@login_required
@user_passes_test(is_agent)
def concept_delete_view(request, pk):
    """Vista para eliminar un concepto"""
    concept = get_object_or_404(Concept, pk=pk)
    
    if request.method == 'POST':
        concept_term = concept.term
        concept.delete()
        messages.success(request, f'Concepto "{concept_term}" eliminado exitosamente.')
        return redirect('concept_list')
    
    context = {
        'concept': concept,
        'title': 'Eliminar Concepto'
    }
    return render(request, 'tickets/concept_delete.html', context)


@login_required
def concept_detail_view(request, pk):
    """Vista para ver los detalles de un concepto"""
    concept = get_object_or_404(Concept, pk=pk)
    
    context = {
        'concept': concept,
        'title': f'Concepto: {concept.term}'
    }
    return render(request, 'tickets/concept_detail.html', context)


def public_concepts_view(request):
    """Vista pública para mostrar el glosario de conceptos"""
    concepts = Concept.objects.filter(is_active=True).order_by('order', 'term')
    
    context = {
        'concepts': concepts,
        'title': 'Glosario de Conceptos'
    }
    return render(request, 'tickets/public_concepts.html', context)
