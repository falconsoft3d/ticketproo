from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.conf import settings
import os
from datetime import timedelta
from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserProfile, 
    UserNote, TimeEntry, Project, Company, SystemConfiguration, Document
)
from .forms import (
    TicketForm, AgentTicketForm, UserManagementForm, UserEditForm, 
    TicketAttachmentForm, CategoryForm, UserTicketForm, UserTicketEditForm, 
    TicketCommentForm, UserNoteForm, TimeEntryStartForm, TimeEntryEndForm, 
    TimeEntryEditForm, ProjectForm, CompanyForm, SystemConfigurationForm, DocumentForm
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
        
        context = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'recent_tickets': recent_tickets,
            'unassigned_tickets': unassigned_tickets,
            'my_assigned_tickets': my_assigned_tickets,
            'user_role': user_role,
            'is_agent': True,
            'daily_hours': daily_hours,
        }
    else:
        # Estadísticas para usuarios regulares (solo sus tickets)
        user_tickets = Ticket.objects.filter(created_by=request.user)
        total_tickets = user_tickets.count()
        open_tickets = user_tickets.filter(status='open').count()
        in_progress_tickets = user_tickets.filter(status='in_progress').count()
        resolved_tickets = user_tickets.filter(status='resolved').count()
        recent_tickets = user_tickets[:5]
        
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
        # Los usuarios regulares solo ven sus propios tickets
        tickets = Ticket.objects.filter(created_by=request.user)
    
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
        # Los usuarios solo pueden ver sus propios tickets
        ticket = get_object_or_404(Ticket, pk=pk, created_by=request.user)
    
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
        # Los usuarios solo pueden editar sus propios tickets
        ticket = get_object_or_404(Ticket, pk=pk, created_by=request.user)
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
    # Obtener o crear el perfil del usuario
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
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
        
        elif 'change_password' in request.POST:
            # Cambiar contraseña
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)  # Mantener la sesión activa
                messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
                return redirect('user_profile')
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_profile': profile,
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
        form = TimeEntryStartForm(request.POST)
        if form.is_valid():
            try:
                project = form.cleaned_data.get('project')
                notas = form.cleaned_data.get('notas_entrada', '')
                entry = TimeEntry.create_entry(request.user, project, notas)
                messages.success(request, f'¡Jornada iniciada a las {entry.fecha_entrada.strftime("%H:%M")} en el proyecto "{project.name}"!')
                return redirect('time_clock')
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('time_clock')
    else:
        form = TimeEntryStartForm()
    
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
        form = TimeEntryEditForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notas del registro actualizadas exitosamente.')
            return redirect('time_entry_detail', entry_id=entry.id)
    else:
        form = TimeEntryEditForm(instance=entry)
    
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
        form = CompanyForm(request.POST)
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
    total_users = company.userprofile_set.count()
    active_users = company.userprofile_set.filter(user__is_active=True).count()
    
    # Tickets recientes
    recent_tickets = company.tickets.select_related(
        'created_by', 'assigned_to', 'category'
    ).order_by('-created_at')[:10]
    
    # Usuarios de la empresa
    company_users = company.userprofile_set.select_related('user').order_by('user__first_name', 'user__username')
    
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
        form = CompanyForm(request.POST, instance=company)
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
    has_users = company.userprofile_set.exists()
    
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
