from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.conf import settings
import os
from .models import Ticket, TicketAttachment, Category, TicketComment, UserProfile
from .forms import TicketForm, AgentTicketForm, UserManagementForm, UserEditForm, TicketAttachmentForm, CategoryForm, UserTicketForm, UserTicketEditForm, TicketCommentForm
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
        }
    else:
        # Estadísticas para usuarios regulares (solo sus tickets)
        user_tickets = Ticket.objects.filter(created_by=request.user)
        total_tickets = user_tickets.count()
        open_tickets = user_tickets.filter(status='open').count()
        in_progress_tickets = user_tickets.filter(status='in_progress').count()
        resolved_tickets = user_tickets.filter(status='resolved').count()
        recent_tickets = user_tickets[:5]
        
        context = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'recent_tickets': recent_tickets,
            'user_role': user_role,
            'is_agent': False,
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
    users = User.objects.all().order_by('username')
    
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
