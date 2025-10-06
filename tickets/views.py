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
from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserProfile, 
    UserNote, TimeEntry, Project, Company, SystemConfiguration, Document, UrlManager, WorkOrder, Task,
    DailyTaskSession, DailyTaskItem, ChatRoom, ChatMessage, ContactFormSubmission,
    Opportunity, OpportunityStatus, OpportunityNote, OpportunityStatusHistory
)
from .forms import (
    TicketForm, AgentTicketForm, UserManagementForm, UserEditForm, 
    TicketAttachmentForm, CategoryForm, UserTicketForm, UserTicketEditForm, 
    TicketCommentForm, UserNoteForm, TimeEntryStartForm, TimeEntryEndForm, 
    TimeEntryEditForm, ProjectForm, CompanyForm, SystemConfigurationForm, DocumentForm,
    UrlManagerForm, UrlManagerFilterForm, WorkOrderForm, WorkOrderFilterForm, TaskForm,
    ChatMessageForm, ChatRoomForm
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
    
    context = {
        'total_tickets': total_tickets,
        'total_users': total_users,
        'user_tickets_count': user_tickets_count,
        'user_role': user_role,
        'tickets_by_status': tickets_by_status,
        'is_authenticated': request.user.is_authenticated,
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
    
    context = {
        'page_title': 'Gestión de Proyectos',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'project_status_choices': Project.STATUS_CHOICES,
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
# VISTAS PARA ÓRDENES DE TRABAJO
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
            work_order = form.save(created_by=request.user)
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
            form.save(created_by=request.user)
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
        titulo_usuario = f" - {usuario.get_full_name() or usuario.username}"
    else:
        titulo_usuario = " - Todos los usuarios"
    
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
    title = f"Reporte de Parte Diario{titulo_usuario}"
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
            
            messages.success(
                request, 
                f'Estado de la tarea "{task.title}" cambiado de {old_status} a {task.get_status_display()}.'
            )
    
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
                models.Q(assigned_users=request.user) | models.Q(created_by=request.user)
            ).exclude(
                status='cancelled'  # Solo excluir canceladas, no completadas
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
        
        # Verificar permisos: solo el propietario o superuser puede eliminar
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
    """Vista pública simplificada para gestionar tareas sin autenticación"""
    from django.db.models import Q
    
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
            for i, task in enumerate(all_user_tasks):
                is_completed = task.id in selected_task_ids
                
                DailyTaskItem.objects.create(
                    session=session,
                    task=task,
                    order=i + 1,
                    completed=is_completed,
                    completed_at=timezone.now() if is_completed else None
                )
                
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
            
            # Preparar nombre del archivo de salida
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
    from django.core.paginator import Paginator
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
            
            messages.success(
                request, 
                f'Empresa "{company.name}" creada exitosamente desde el formulario de contacto.'
            )
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
    """Vista pública para mostrar estadísticas de una empresa usando su token"""
    try:
        company = Company.objects.get(public_token=token, is_active=True)
    except Company.DoesNotExist:
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
    from . import utils
    
    # Obtener oportunidades del usuario
    if utils.is_agent(request.user):
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
        'page_title': 'CRM Dashboard'
    }
    
    return render(request, 'tickets/crm_dashboard.html', context)


@login_required
def opportunity_list(request):
    """Lista de oportunidades"""
    from . import utils
    
    # Obtener oportunidades del usuario
    if utils.is_agent(request.user):
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
    
    if status_filter:
        opportunities = opportunities.filter(status_id=status_filter)
    
    if company_filter:
        opportunities = opportunities.filter(company_id=company_filter)
    
    if assigned_filter:
        opportunities = opportunities.filter(assigned_to_id=assigned_filter)
    
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
    statuses = OpportunityStatus.objects.filter(is_active=True)
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
    statuses = OpportunityStatus.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
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
        'page_title': 'Nueva Oportunidad'
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
    from . import utils
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
    status = get_object_or_404(OpportunityStatus, pk=pk)
    
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
    from . import utils
    if not utils.is_agent(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('crm_dashboard')
    
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
