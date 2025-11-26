from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.db import models
from django.utils import timezone
import os


class DateTimeLocalWidget(forms.DateTimeInput):
    """Widget personalizado para datetime-local que maneja correctamente el formato"""
    input_type = 'datetime-local'
    
    def __init__(self, attrs=None, format=None):
        super().__init__(attrs, format='%Y-%m-%dT%H:%M')
    
    def format_value(self, value):
        if value:
            # Asegurar formato ISO para input type="datetime-local"
            if hasattr(value, 'strftime'):
                return value.strftime('%Y-%m-%dT%H:%M')
            return value
        return ''


class DateInput(forms.DateInput):
    """Widget personalizado para campos de fecha"""
    input_type = 'date'
    
    def format_value(self, value):
        if value:
            # Asegurar formato ISO para input type="date"
            if hasattr(value, 'strftime'):
                return value.strftime('%Y-%m-%d')
            return value
        return ''


from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserProfile, 
    UserNote, TimeEntry, PublicTimeAccess, Project, Company, SystemConfiguration, Document, UrlManager, WorkOrder, Task,
    ChatRoom, ChatMessage, Command, ContactFormSubmission, Meeting, MeetingAttendee, MeetingQuestion, OpportunityActivity,
    Course, CourseClass, Contact, ContactComment, ContactAttachment, BlogCategory, BlogPost, BlogComment, AIChatSession, AIChatMessage, Concept, ContactoWeb, Employee, EmployeePayroll,
    Agreement, AgreementSignature, LandingPage, LandingPageSubmission, WorkOrderTask, WorkOrderTaskTimeEntry, SharedFile, SharedFileDownload,
    Recording, RecordingPlayback, MultipleDocumentation, TaskSchedule, ScheduleTask, ScheduleComment, FinancialAction,
    ClientProjectAccess, ClientTimeEntry, ProductSet, ProductItem, Precotizador, PrecotizadorExample, PrecotizadorQuote,
    CompanyDocumentation, CompanyDocumentationURL, TermsOfUse, ContactGenerator,
    CompanyRequestGenerator, CompanyRequest, CompanyRequestComment,
    Form, FormQuestion, FormQuestionOption, FormResponse, FormAnswer,
    EmployeeRequest, InternalAgreement, Asset, AssetHistory, 
    AITutor, AITutorProgressReport, AITutorAttachment, ExpenseReport, ExpenseItem, ExpenseComment,
    VideoMeeting, MeetingNote, QuoteGenerator, CountdownTimer, AbsenceType,
    MonthlyCumplimiento, DailyCumplimiento, QRCode, CrmQuestion, SupportMeeting, SupportMeetingPoint, ScheduledTask,
    ClientRequest, ClientRequestResponse, ClientRequestTemplate, ClientRequestTemplateItem, Event, Trip, TripStop
)

class CategoryForm(forms.ModelForm):
    """Formulario para crear y editar categorías"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría (opcional)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre',
            'description': 'Descripción',
            'color': 'Color',
            'is_active': 'Activa',
        }


class ProjectForm(forms.ModelForm):
    """Formulario para crear y editar proyectos"""
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'color', 'status', 'start_date', 'end_date', 'assigned_users', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proyecto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del proyecto (opcional)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#28a745'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'assigned_users': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'multiple': True,
                'size': 5,
                'data-placeholder': 'Selecciona usuarios...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre del Proyecto',
            'description': 'Descripción',
            'color': 'Color',
            'status': 'Estado',
            'start_date': 'Fecha de Inicio',
            'end_date': 'Fecha de Fin',
            'assigned_users': 'Usuarios Asignados',
            'is_active': 'Activo',
        }
        help_texts = {
            'name': 'Nombre único para identificar el proyecto',
            'description': 'Descripción detallada del proyecto',
            'color': 'Color que representará el proyecto en reportes',
            'start_date': 'Fecha de inicio del proyecto (opcional)',
            'end_date': 'Fecha estimada de finalización (opcional)',
            'is_active': 'Si está marcado, el proyecto aparecerá en el registro de tiempo',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin.')
        
        return cleaned_data
    
    def save(self, created_by=None, commit=True):
        project = super().save(commit=False)
        
        if created_by:
            project.created_by = created_by
        
        if commit:
            project.save()
        
        return project


class TicketForm(forms.ModelForm):
    """Formulario básico para crear/editar tickets (usado por agentes)"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Seleccionar categoría"
        
        # Configurar campo empresa
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "Seleccionar empresa (opcional)"
        
        # Configurar campo proyecto
        self.fields['project'].queryset = Project.objects.filter(is_active=True).order_by('name')
        self.fields['project'].empty_label = "Seleccionar proyecto (opcional)"

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'status', 'ticket_type', 'company', 'project', 'hours']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el título del ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe detalladamente el problema o solicitud'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
                'ticket_type': forms.Select(attrs={
                    'class': 'form-select'
                }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2.5',
                'step': '0.5',
                'min': '0'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
            'status': 'Estado',
                'ticket_type': 'Tipo de ticket',
            'company': 'Empresa',
            'project': 'Proyecto',
            'hours': 'Horas estimadas/trabajadas',
        }


class UserTicketForm(forms.ModelForm):
    """Formulario simplificado para usuarios regulares al crear tickets"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Seleccionar categoría"
        
        # Configurar campo empresa
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "Seleccionar empresa (opcional)"

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'ticket_type', 'company']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el título del ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe detalladamente el problema o solicitud'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ticket_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
            'ticket_type': 'Tipo de ticket',
            'company': 'Empresa',
        }

class UserTicketEditForm(forms.ModelForm):
    """Formulario para editar tickets por usuarios regulares"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Seleccionar categoría"
        
        # Configurar campo empresa
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "Seleccionar empresa (opcional)"

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'ticket_type', 'company']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el título del ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe detalladamente el problema o solicitud'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ticket_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
            'ticket_type': 'Tipo de ticket',
            'company': 'Empresa',
        }


class AgentTicketForm(forms.ModelForm):
    """Formulario extendido para agentes con campo de asignación y horas"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener solo usuarios que son agentes para la asignación
        try:
            agentes_group = Group.objects.get(name='Agentes')
            agentes = User.objects.filter(groups=agentes_group)
            self.fields['assigned_to'].queryset = agentes
        except Group.DoesNotExist:
            self.fields['assigned_to'].queryset = User.objects.none()
        
        # Filtrar solo categorías activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Seleccionar categoría"
        
        # Filtrar solo empresas activas
        self.fields['company'].queryset = Company.objects.filter(is_active=True)
        self.fields['company'].empty_label = "Seleccionar empresa (opcional)"
        
        # Configurar campo proyecto
        self.fields['project'].queryset = Project.objects.filter(is_active=True).order_by('name')
        self.fields['project'].empty_label = "Seleccionar proyecto (opcional)"
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'company', 'project', 'priority', 'status', 'ticket_type', 'assigned_to', 'hours', 'is_public_shareable']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el título del ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe detalladamente el problema o solicitud'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ticket_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2.5',
                'step': '0.5',
                'min': '0'
            }),
            'is_public_shareable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'company': 'Empresa',
            'project': 'Proyecto',
            'priority': 'Prioridad',
            'status': 'Estado',
            'ticket_type': 'Tipo de ticket',
            'assigned_to': 'Asignar a',
            'hours': 'Horas estimadas/trabajadas',
            'is_public_shareable': 'Permitir compartir públicamente',
        }

class UserManagementForm(UserCreationForm):
    """Formulario para crear usuarios con selección de rol"""
    
    ROLE_CHOICES = [
        ('Usuarios', 'Usuario'),
        ('Agentes', 'Agente'),
        ('Profesores', 'Profesor'),
    ]
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        }),
        label='Apellido'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo electrónico'
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Rol del usuario',
        initial='Usuarios'
    )
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        required=False,
        empty_label="Sin empresa asignada",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Empresa'
    )
    
    precio_hora = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Precio por hora (€)',
        help_text='Precio de venta por hora de trabajo'
    )
    
    coste_hora = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Coste por hora (€)',
        help_text='Coste interno por hora de trabajo'
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role', 'company', 'precio_hora', 'coste_hora')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
        }
        labels = {
            'username': 'Nombre de usuario',
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Crear o actualizar el perfil del usuario
            profile, created = UserProfile.objects.get_or_create(user=user)
            company = self.cleaned_data.get('company')
            precio_hora = self.cleaned_data.get('precio_hora', 0.00)
            coste_hora = self.cleaned_data.get('coste_hora', 0.00)
            
            profile.company = company
            profile.precio_hora = precio_hora
            profile.coste_hora = coste_hora
            profile.save()
            
            # Asignar al grupo correspondiente
            role = self.cleaned_data['role']
            try:
                group = Group.objects.get(name=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
        
        return user

class UserEditForm(forms.ModelForm):
    """Formulario para editar usuarios existentes"""
    
    ROLE_CHOICES = [
        ('Usuarios', 'Usuario'),
        ('Agentes', 'Agente'),
        ('Profesores', 'Profesor'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Rol del usuario'
    )
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        required=False,
        empty_label="Sin empresa asignada",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Empresa'
    )
    
    precio_hora = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Precio por hora (€)',
        help_text='Precio de venta por hora de trabajo'
    )
    
    coste_hora = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Coste por hora (€)',
        help_text='Coste interno por hora de trabajo'
    )
    
    cargo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Diseñador, Desarrollador, Gerente...'
        }),
        label='Cargo',
        help_text='Cargo o posición del usuario en la empresa'
    )
    
    descripcion_cargo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe las responsabilidades del cargo...'
        }),
        label='Descripción del Cargo',
        help_text='Descripción detallada de las responsabilidades del cargo'
    )
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d'],
        label='Fecha de cumpleaños',
        help_text='Fecha de nacimiento del usuario'
    )
    
    quote_terms_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Términos y condiciones que aparecerán en las cotizaciones rápidas...'
        }),
        label='Términos y Condiciones de Cotizaciones',
        help_text='Estos términos se mostrarán automáticamente en todas las cotizaciones rápidas'
    )
    
    # Campos para acceso público al control de horario
    enable_public_time_access = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Habilitar acceso público al control de horario',
        help_text='Permite al usuario registrar entrada/salida sin iniciar sesión usando un enlace público'
    )
    
    require_location = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Requerir ubicación',
        help_text='Registra la ubicación GPS al marcar entrada/salida'
    )
    
    allowed_ip_addresses = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ej: 192.168.1.1, 10.0.0.1\nSeparar con comas'
        }),
        label='IPs permitidas (opcional)',
        help_text='Lista de IPs permitidas separadas por comas. Dejar vacío para permitir cualquier IP.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'role', 'company', 'precio_hora', 'coste_hora', 'cargo', 'descripcion_cargo')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'is_active': 'Usuario activo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Determinar el rol actual del usuario
            if self.instance.groups.filter(name='Agentes').exists():
                self.fields['role'].initial = 'Agentes'
            elif self.instance.groups.filter(name='Profesores').exists():
                self.fields['role'].initial = 'Profesores'
            else:
                self.fields['role'].initial = 'Usuarios'
            
            # Establecer la empresa actual del usuario
            try:
                profile = self.instance.profile
                if profile.company:
                    self.fields['company'].initial = profile.company
                # Cargar valores de precio y coste por hora
                self.fields['precio_hora'].initial = profile.precio_hora
                self.fields['coste_hora'].initial = profile.coste_hora
                # Cargar valores de cargo
                self.fields['cargo'].initial = profile.cargo
                self.fields['descripcion_cargo'].initial = profile.descripcion_cargo
                # Cargar fecha de cumpleaños
                self.fields['birth_date'].initial = profile.birth_date
                # Cargar términos y condiciones
                self.fields['quote_terms_conditions'].initial = profile.quote_terms_conditions
            except UserProfile.DoesNotExist:
                pass
                
            # Cargar configuración de acceso público
            try:
                public_access = self.instance.public_time_access
                self.fields['enable_public_time_access'].initial = public_access.is_active
                self.fields['require_location'].initial = public_access.require_location
                self.fields['allowed_ip_addresses'].initial = public_access.allowed_ip_addresses
            except PublicTimeAccess.DoesNotExist:
                pass
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        
        if commit:
            # Crear o actualizar el perfil del usuario
            profile, created = UserProfile.objects.get_or_create(user=user)
            company = self.cleaned_data.get('company')
            precio_hora = self.cleaned_data.get('precio_hora', 0.00)
            coste_hora = self.cleaned_data.get('coste_hora', 0.00)
            cargo = self.cleaned_data.get('cargo', '')
            descripcion_cargo = self.cleaned_data.get('descripcion_cargo', '')
            birth_date = self.cleaned_data.get('birth_date')
            
            profile.company = company
            profile.precio_hora = precio_hora
            profile.coste_hora = coste_hora
            profile.cargo = cargo
            profile.descripcion_cargo = descripcion_cargo
            profile.birth_date = birth_date
            profile.quote_terms_conditions = self.cleaned_data.get('quote_terms_conditions', '')
            profile.save()
            
            # Manejar configuración de acceso público
            enable_public_access = self.cleaned_data.get('enable_public_time_access', False)
            require_location = self.cleaned_data.get('require_location', False)
            allowed_ip_addresses = self.cleaned_data.get('allowed_ip_addresses', '')
            
            if enable_public_access:
                # Crear o actualizar acceso público
                public_access, created = PublicTimeAccess.objects.get_or_create(user=user)
                public_access.is_active = True
                public_access.require_location = require_location
                public_access.allowed_ip_addresses = allowed_ip_addresses
                public_access.save()
            else:
                # Desactivar acceso público si existe
                try:
                    public_access = user.public_time_access
                    public_access.is_active = False
                    public_access.save()
                except PublicTimeAccess.DoesNotExist:
                    pass
            
            # Actualizar grupos del usuario
            role = self.cleaned_data['role']
            user.groups.clear()
            try:
                group = Group.objects.get(name=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass
        
        return user


class TicketAttachmentForm(forms.ModelForm):
    """Formulario para subir adjuntos a tickets"""
    
    class Meta:
        model = TicketAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar'
            })
        }
        labels = {
            'file': 'Seleccionar archivo'
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Verificar tamaño del archivo (máximo 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10 MB.')
            
            # Verificar tipos de archivo permitidos
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError('Tipo de archivo no permitido.')
        
        return file


class TicketWithAttachmentsForm(forms.ModelForm):
    """Formulario combinado para crear tickets con adjuntos (usuarios regulares)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Seleccionar categoría"
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el título del ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe detalladamente el problema o solicitud'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
        }



class TicketCommentForm(forms.ModelForm):
    """Formulario para agregar comentarios a tickets"""
    
    class Meta:
        model = TicketComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario aquí...',
                'maxlength': '1000'
            }),
        }
        labels = {
            'content': 'Nuevo comentario',
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content:
            content = content.strip()
            if len(content) < 10:
                raise forms.ValidationError('El comentario debe tener al menos 10 caracteres.')
            if len(content) > 1000:
                raise forms.ValidationError('El comentario no puede exceder 1000 caracteres.')
        return content


class UserProfileForm(forms.ModelForm):
    """Formulario para actualizar información básica del usuario"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        }),
        label='Apellido'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico'
    )
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'bio', 'cargo', 'descripcion_cargo', 'company', 'birth_date', 'enable_public_contact_form']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 612 345 678'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Cuéntanos algo sobre ti...'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Diseñador, Desarrollador, Gerente...'
            }),
            'descripcion_cargo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe las responsabilidades de tu cargo...'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'enable_public_contact_form': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'phone': 'Teléfono',
            'bio': 'Biografía',
            'cargo': 'Cargo',
            'descripcion_cargo': 'Descripción del Cargo',
            'company': 'Empresa',
            'birth_date': 'Fecha de cumpleaños',
            'enable_public_contact_form': 'Activar formulario de contacto público',
        }
        help_texts = {
            'enable_public_contact_form': 'Permite que visitantes envíen formularios para crear empresas en tu cuenta',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo empresas activas
        self.fields['company'].queryset = Company.objects.filter(is_active=True)
        self.fields['company'].empty_label = "Sin empresa asignada"
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def save(self, user=None, commit=True):
        profile = super().save(commit=False)
        
        if user:
            # Actualizar campos del User
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            
            if commit:
                user.save()
                profile.save()
        
        return profile


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulario personalizado para cambio de contraseña"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        })
        
        # Personalizar labels
        self.fields['old_password'].label = 'Contraseña Actual'
        self.fields['new_password1'].label = 'Nueva Contraseña'
        self.fields['new_password2'].label = 'Confirmar Nueva Contraseña'


class UserNoteForm(forms.ModelForm):
    """Formulario para crear y editar notas internas de usuarios"""
    
    def __init__(self, *args, **kwargs):
        # Permitir pasar el usuario actual para filtrar tickets
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Solo mostrar tickets del usuario asociado a la nota
        if self.instance.pk and self.instance.user:
            # Si estamos editando, filtrar tickets del usuario de la nota
            self.fields['tickets'].queryset = Ticket.objects.filter(
                created_by=self.instance.user
            ).order_by('-created_at')
        elif current_user:
            # Si estamos creando, inicialmente no mostrar tickets
            # Se llenarán dinámicamente cuando se seleccione el usuario
            self.fields['tickets'].queryset = Ticket.objects.none()
        
        # Configurar widget para selección múltiple de tickets
        self.fields['tickets'].widget.attrs.update({
            'class': 'form-select',
            'size': '5'
        })
        
        # Personalizar queryset de usuarios (solo mostrar usuarios que tienen tickets)
        users_with_tickets = User.objects.filter(
            created_tickets__isnull=False
        ).distinct().order_by('username')
        self.fields['user'].queryset = users_with_tickets
        
        # Configurar queryset de empresas (mostrar todas las empresas activas)
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "Seleccionar empresa (opcional)"
    
    class Meta:
        model = UserNote
        fields = ['title', 'description', 'user', 'company', 'tickets', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo de la nota'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descripción detallada de la interacción con el cliente...'
            }),
            'user': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_user_select'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título de la Nota',
            'description': 'Descripción',
            'user': 'Usuario Asociado',
            'company': 'Empresa',
            'tickets': 'Tickets Relacionados',
            'is_private': 'Nota Privada',
        }
        help_texts = {
            'title': 'Breve descripción del motivo de la nota',
            'description': 'Detalle completo de la interacción, observaciones o comentarios internos',
            'user': 'Usuario al que se asocia esta nota',
            'company': 'Empresa asociada a esta nota (opcional)',
            'tickets': 'Selecciona los tickets relacionados con esta nota (opcional)',
            'is_private': 'Si está marcada, solo tú podrás ver, editar y eliminar esta nota',
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) < 5:
                raise forms.ValidationError('El título debe tener al menos 5 caracteres.')
            if len(title) > 200:
                raise forms.ValidationError('El título no puede exceder 200 caracteres.')
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            if len(description) < 10:
                raise forms.ValidationError('La descripción debe tener al menos 10 caracteres.')
            if len(description) > 2000:
                raise forms.ValidationError('La descripción no puede exceder 2000 caracteres.')
        return description
    
    def save(self, created_by=None, commit=True):
        note = super().save(commit=False)
        
        if created_by:
            note.created_by = created_by
        
        if commit:
            note.save()
            # Guardar relaciones many-to-many
            self.save_m2m()
        
        return note


# ===========================================
# FORMULARIOS PARA CONTROL DE HORARIO
# ===========================================

class TimeEntryStartForm(forms.Form):
    """Formulario para iniciar jornada laboral"""
    
    project = forms.ModelChoiceField(
        queryset=Project.objects.filter(is_active=True, status='active'),
        empty_label="Seleccionar proyecto (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        label='Proyecto',
        help_text='Selecciona el proyecto en el que vas a trabajar (opcional)',
        required=False
    )
    
    ticket = forms.ModelChoiceField(
        queryset=None,  # Se configurará en __init__
        empty_label="Seleccionar ticket (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        label='Ticket',
        help_text='Selecciona el ticket en el que vas a trabajar (opcional)',
        required=False
    )
    
    work_order = forms.ModelChoiceField(
        queryset=None,  # Se configurará en __init__
        empty_label="Seleccionar orden de trabajo (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        label='Orden de Trabajo',
        help_text='Selecciona la orden de trabajo en la que vas a trabajar (opcional)',
        required=False
    )
    
    task = forms.ModelChoiceField(
        queryset=None,  # Se configurará en __init__
        empty_label="Seleccionar tarea (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        label='Tarea',
        help_text='Selecciona la tarea en la que vas a trabajar (opcional)',
        required=False
    )
    
    notas_entrada = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comentarios opcionales sobre el inicio de jornada...',
        }),
        label='Notas de entrada (opcional)',
        help_text='Puedes agregar comentarios sobre tareas a realizar, estado del proyecto, etc.'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Asegurar que solo se muestren proyectos activos
        self.fields['project'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Configurar queryset para tickets
        if user:
            from .utils import is_agent
            if is_agent(user):
                # Agentes pueden ver todos los tickets
                self.fields['ticket'].queryset = Ticket.objects.all().order_by('-created_at')
            else:
                # Usuarios normales solo ven sus tickets
                self.fields['ticket'].queryset = Ticket.objects.filter(
                    created_by=user
                ).order_by('-created_at')
        else:
            self.fields['ticket'].queryset = Ticket.objects.none()
        
        # Configurar queryset para órdenes de trabajo
        self.fields['work_order'].queryset = WorkOrder.objects.all().order_by('-created_at')
        
        # Configurar queryset para tareas (todas las tareas disponibles)
        if user:
            from django.db.models import Q
            from .utils import is_agent
            
            if is_agent(user):
                # Agentes pueden ver todas las tareas
                self.fields['task'].queryset = Task.objects.all().order_by('-created_at')
            else:
                # Usuarios normales ven sus tareas asignadas o creadas por ellos
                self.fields['task'].queryset = Task.objects.filter(
                    Q(assigned_users=user) | Q(created_by=user)
                ).distinct().order_by('-created_at')
        else:
            self.fields['task'].queryset = Task.objects.none()
    
    def clean_project(self):
        """Validar proyecto (sin restricciones de estado)"""
        project = self.cleaned_data.get('project')
        # Permitir cualquier proyecto activo
        return project
    
    def clean_ticket(self):
        """Validar ticket (sin restricciones de estado)"""
        ticket = self.cleaned_data.get('ticket')
        # Permitir cualquier ticket
        return ticket
    
    def clean_work_order(self):
        """Validar orden de trabajo (sin restricciones de estado)"""
        work_order = self.cleaned_data.get('work_order')
        # Permitir cualquier orden de trabajo
        return work_order
    
    def clean_task(self):
        """Validar tarea (sin restricciones de estado)"""
        task = self.cleaned_data.get('task')
        # Permitir cualquier tarea sin importar su estado
        return task


class TimeEntryEndForm(forms.Form):
    """Formulario para finalizar jornada laboral"""
    
    end_reason = forms.ChoiceField(
        choices=[
            ('comer', 'Comer'),
            ('fin_jornada', 'Fin de Jornada'),
            ('otro', 'Otro'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Causa de finalización',
        help_text='Selecciona el motivo por el cual finalizas la jornada'
    )
    
    notas_salida = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Resumen de tareas realizadas, pendientes, etc...',
        }),
        label='Resumen de la jornada (opcional)',
        help_text='Describe brevemente las actividades realizadas durante la jornada'
    )
    
    def clean_notas_salida(self):
        notas = self.cleaned_data.get('notas_salida')
        if notas:
            notas = notas.strip()
            if len(notas) > 500:
                raise forms.ValidationError('Las notas no pueden exceder 500 caracteres.')
        return notas


class TimeEntryEditForm(forms.ModelForm):
    """Formulario para editar registros de horario"""
    
    fecha_entrada = forms.DateTimeField(
        widget=DateTimeLocalWidget(
            attrs={
                'class': 'form-control',
            }
        ),
        label='Fecha y hora de entrada'
    )
    
    fecha_salida = forms.DateTimeField(
        required=False,
        widget=DateTimeLocalWidget(
            attrs={
                'class': 'form-control',
            }
        ),
        label='Fecha y hora de salida'
    )
    
    change_reason = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Razón del cambio (opcional)'
        }),
        label='Razón del cambio',
        help_text='Opcional: Explica por qué modificas los horarios'
    )
    
    class Meta:
        model = TimeEntry
        fields = ['fecha_entrada', 'fecha_salida', 'project', 'ticket', 'work_order', 'task', 'notas']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'form-select',
            }),
            'ticket': forms.Select(attrs={
                'class': 'form-select',
            }),
            'work_order': forms.Select(attrs={
                'class': 'form-select',
            }),
            'task': forms.Select(attrs={
                'class': 'form-select',
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comentarios sobre la jornada laboral...',
            }),
        }
        labels = {
            'project': 'Proyecto',
            'ticket': 'Ticket',
            'work_order': 'Orden de Trabajo',
            'task': 'Tarea',
            'notas': 'Notas de la jornada',
        }
        help_texts = {
            'project': 'Proyecto en el que se trabajó',
            'ticket': 'Ticket en el que se trabajó',
            'work_order': 'Orden de trabajo en la que se trabajó',
            'task': 'Tarea en la que se trabajó',
            'notas': 'Describe las actividades realizadas, observaciones o comentarios relevantes',
            'fecha_entrada': 'Ajusta la fecha y hora de entrada si es necesario',
            'fecha_salida': 'Ajusta la fecha y hora de salida si es necesario',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar querysets igual que en TimeEntryStartForm
        self.fields['project'].queryset = Project.objects.filter(
            is_active=True
        ).order_by('name')
        
        if user:
            from .utils import is_agent
            from django.db.models import Q
            
            if is_agent(user):
                self.fields['ticket'].queryset = Ticket.objects.all().order_by('-created_at')
                
                self.fields['task'].queryset = Task.objects.all().order_by('-created_at')
            else:
                self.fields['ticket'].queryset = Ticket.objects.filter(
                    created_by=user
                ).order_by('-created_at')
                
                self.fields['task'].queryset = Task.objects.filter(
                    Q(assigned_users=user) | Q(created_by=user)
                ).distinct().order_by('-created_at')
        else:
            self.fields['ticket'].queryset = Ticket.objects.none()
            self.fields['task'].queryset = Task.objects.none()
        
        self.fields['work_order'].queryset = WorkOrder.objects.all().order_by('-created_at')
        
        # Hacer todos los campos opcionales
        for field in ['project', 'ticket', 'work_order', 'task']:
            self.fields[field].required = False
            self.fields[field].empty_label = f"Seleccionar {self.fields[field].label.lower()} (opcional)"
    
    def clean_fecha_entrada(self):
        fecha_entrada = self.cleaned_data.get('fecha_entrada')
        if not fecha_entrada:
            raise forms.ValidationError('La fecha de entrada es requerida.')
        
        # No puede ser en el futuro
        if fecha_entrada > timezone.now():
            raise forms.ValidationError('La fecha de entrada no puede ser en el futuro.')
        
        return fecha_entrada
    
    def clean_fecha_salida(self):
        fecha_salida = self.cleaned_data.get('fecha_salida')
        fecha_entrada = self.cleaned_data.get('fecha_entrada')
        
        if fecha_salida:
            # No puede ser en el futuro
            if fecha_salida > timezone.now():
                raise forms.ValidationError('La fecha de salida no puede ser en el futuro.')
            
            # No puede ser antes que la entrada
            if fecha_entrada and fecha_salida < fecha_entrada:
                raise forms.ValidationError('La fecha de salida no puede ser anterior a la fecha de entrada.')
        
        return fecha_salida
    
    def clean_notas(self):
        notas = self.cleaned_data.get('notas')
        if notas:
            notas = notas.strip()
            if len(notas) > 500:
                raise forms.ValidationError('Las notas no pueden exceder 500 caracteres.')
        return notas
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Guardar información de auditoría si hay cambios en fecha_entrada o fecha_salida
        if self.instance.pk:  # Solo si es una edición
            original = TimeEntry.objects.get(pk=self.instance.pk)
            changes = []
            
            if original.fecha_entrada != instance.fecha_entrada:
                changes.append({
                    'field': 'fecha_entrada',
                    'old_value': original.fecha_entrada.strftime('%Y-%m-%d %H:%M:%S'),
                    'new_value': instance.fecha_entrada.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if original.fecha_salida != instance.fecha_salida:
                old_value = original.fecha_salida.strftime('%Y-%m-%d %H:%M:%S') if original.fecha_salida else None
                new_value = instance.fecha_salida.strftime('%Y-%m-%d %H:%M:%S') if instance.fecha_salida else None
                changes.append({
                    'field': 'fecha_salida',
                    'old_value': old_value,
                    'new_value': new_value
                })
            
            if commit:
                instance.save()
                
                # Crear logs de auditoría para los cambios
                change_reason = self.cleaned_data.get('change_reason', '')
                for change in changes:
                    from .models import TimeEntryAuditLog
                    TimeEntryAuditLog.objects.create(
                        time_entry=instance,
                        user=getattr(self, '_user', None),  # Se establecerá en la vista
                        field_name=change['field'],
                        old_value=change['old_value'],
                        new_value=change['new_value'],
                        change_reason=change_reason
                    )
        elif commit:
            instance.save()
        
        return instance


class PublicTimeAccessForm(forms.ModelForm):
    """Formulario para configurar acceso público al control de horario"""
    
    class Meta:
        model = PublicTimeAccess
        fields = ['is_active', 'require_location', 'allowed_ip_addresses']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_location': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allowed_ip_addresses': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ejemplo: 192.168.1.100, 10.0.0.50 (opcional)'
            }),
        }
        help_texts = {
            'is_active': 'Permite que el usuario acceda al control de horario mediante URL pública',
            'require_location': 'Registrará la ubicación GPS cuando marque entrada/salida',
            'allowed_ip_addresses': 'Lista de direcciones IP permitidas, separadas por comas (opcional)',
        }


class PublicTimeEntryForm(forms.Form):
    """Formulario público para registrar entrada/salida"""
    
    action = forms.ChoiceField(
        choices=[
            ('entrada', 'Registrar Entrada'),
            ('salida', 'Registrar Salida')
        ],
        widget=forms.HiddenInput(),
        required=True
    )
    
    notes = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notas opcionales sobre tu jornada...'
        }),
        label='Notas (opcional)',
        help_text='Puedes agregar comentarios sobre tu trabajo del día'
    )
    
    # Campos ocultos para ubicación (si se requiere)
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.public_access = kwargs.pop('public_access', None)
        super().__init__(*args, **kwargs)
        
        # Si se requiere ubicación, hacer los campos obligatorios
        if self.public_access and self.public_access.require_location:
            self.fields['latitude'].required = True
            self.fields['longitude'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        
        # Validar ubicación si es requerida
        if self.public_access and self.public_access.require_location:
            if not latitude or not longitude:
                raise forms.ValidationError(
                    'Se requiere proporcionar la ubicación para registrar horario.'
                )
        
        return cleaned_data


class CompanyForm(forms.ModelForm):
    """Formulario para crear y editar empresas"""
    
    class Meta:
        model = Company
        fields = ['name', 'description', 'business_objectives', 'address', 'phone', 'email', 'website', 'color', 'logo', 'public_token', 'is_active', 
                  'tax_id', 'city', 'state', 'postal_code', 'country',
                  'bank_name', 'bank_url', 'bank_account_holder', 'bank_account', 'bank_swift',
                  'payment_terms']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la empresa (opcional)'
            }),
            'business_objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Define los objetivos, metas y KPIs estratégicos de la empresa...\n\nEjemplos:\n- Aumentar las ventas un 20% este año\n- Mejorar la satisfacción del cliente al 95%\n- Reducir costos operativos en un 15%\n- Lanzar 3 nuevos productos\n- Expandirse a 2 nuevos mercados'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 123 456 789'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contacto@empresa.com'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.empresa.com'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Selecciona un color identificativo'
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'public_token': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Token público para enlaces (se genera automáticamente)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NIF/CIF'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado/Provincia'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código Postal'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'País'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del banco'
            }),
            'bank_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.banco.com'
            }),
            'bank_account_holder': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titular de la cuenta'
            }),
            'bank_account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IBAN o número de cuenta'
            }),
            'bank_swift': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SWIFT/BIC'
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Condiciones de pago generales...'
            }),
        }
        labels = {
            'name': 'Nombre de la Empresa',
            'description': 'Descripción',
            'business_objectives': 'Objetivos Empresariales',
            'address': 'Dirección',
            'phone': 'Teléfono',
            'email': 'Email de Contacto',
            'website': 'Sitio Web',
            'color': 'Color Identificativo',
            'public_token': 'Token Público',
            'is_active': 'Empresa Activa',
            'tax_id': 'NIF/CIF/Tax ID',
            'city': 'Ciudad',
            'state': 'Estado/Provincia',
            'postal_code': 'Código Postal',
            'country': 'País',
            'bank_name': 'Nombre del Banco',
            'bank_url': 'URL del Banco',
            'bank_account_holder': 'Titular de la Cuenta',
            'bank_account': 'Número de Cuenta',
            'bank_swift': 'SWIFT/BIC',
            'payment_terms': 'Condiciones de Pago',
        }
        help_texts = {
            'business_objectives': 'Define los objetivos, metas y KPIs estratégicos. Estos serán considerados por los gerentes IA al generar resúmenes ejecutivos.',
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
            
            # Verificar unicidad
            query = Company.objects.filter(name__iexact=name)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise forms.ValidationError('Ya existe una empresa con este nombre.')
        
        return name
    
    def save(self, commit=True):
        """Generar token público si no existe"""
        instance = super().save(commit=False)
        
        if not instance.public_token:
            import uuid
            instance.public_token = uuid.uuid4()
        
        if commit:
            instance.save()
        
        return instance


class SystemConfigurationForm(forms.ModelForm):
    """Formulario para configurar el sistema"""
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'site_name',
            'allow_user_registration',
            'default_ticket_priority',
            'default_currency',
            'ai_chat_enabled',
            'openai_api_key',
            'openai_model',
            'ai_employee_analysis_prompt',
            'paypal_enabled',
            'paypal_mode',
            'paypal_client_id',
            'paypal_client_secret',
            'paypal_webhook_id',
            'enable_telegram_notifications',
            'telegram_bot_token',
            'telegram_chat_id',
            'enable_email_notifications',
            'notification_emails',
            'email_host',
            'email_port',
            'email_host_user',
            'email_host_password',
            'email_use_tls',
            'email_use_ssl',
            'email_from'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del sitio'
            }),
            'allow_user_registration': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'default_ticket_priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ai_chat_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'openai_api_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'sk-...',
                'type': 'password'
            }),
            'openai_model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'gpt-4o'
            }),
            'ai_employee_analysis_prompt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Prompt personalizado para el análisis de empleados...'
            }),
            'paypal_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'paypal_mode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'paypal_client_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Client ID de PayPal',
                'type': 'password'
            }),
            'paypal_client_secret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Client Secret de PayPal',
                'type': 'password'
            }),
            'paypal_webhook_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Webhook ID (opcional)'
            }),
            'enable_telegram_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'telegram_bot_token': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Token del bot de Telegram',
                'type': 'password'
            }),
            'telegram_chat_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '-100123456789'
            }),
            'enable_email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notification_emails': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'admin@ejemplo.com\nsupport@ejemplo.com'
            }),
            'email_host': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'smtp.gmail.com'
            }),
            'email_port': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '587'
            }),
            'email_host_user': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu-email@gmail.com'
            }),
            'email_host_password': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña o token de aplicación',
                'type': 'password'
            }),
            'email_use_tls': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_use_ssl': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_from': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'noreply@tu-dominio.com'
            }),
        }
        labels = {
            'site_name': 'Nombre del sitio',
            'allow_user_registration': 'Permitir registro de usuarios',
            'default_ticket_priority': 'Prioridad por defecto de tickets',
            'default_currency': 'Moneda por defecto',
            'ai_chat_enabled': 'Habilitar Chat IA',
            'openai_api_key': 'API Key de OpenAI',
            'openai_model': 'Modelo de IA',
            'ai_employee_analysis_prompt': 'Prompt para análisis de empleados',
            'paypal_enabled': 'Habilitar PayPal',
            'paypal_mode': 'Modo de PayPal',
            'paypal_client_id': 'Client ID de PayPal',
            'paypal_client_secret': 'Client Secret de PayPal',
            'paypal_webhook_id': 'Webhook ID de PayPal',
            'enable_telegram_notifications': 'Activar notificaciones de Telegram',
            'telegram_bot_token': 'Token del Bot de Telegram',
            'telegram_chat_id': 'ID del Chat/Grupo de Telegram',
            'enable_email_notifications': 'Activar notificaciones por email',
            'notification_emails': 'Emails de notificación',
            'email_host': 'Servidor SMTP',
            'email_port': 'Puerto SMTP',
            'email_host_user': 'Usuario SMTP',
            'email_host_password': 'Contraseña SMTP',
            'email_use_tls': 'Usar TLS',
            'email_use_ssl': 'Usar SSL',
            'email_from': 'Email remitente',
        }
        help_texts = {
            'site_name': 'Nombre que aparece en el encabezado del sistema',
            'allow_user_registration': 'Permite que nuevos usuarios se registren en el sistema',
            'default_ticket_priority': 'Prioridad asignada automáticamente a nuevos tickets',
            'default_currency': 'Moneda utilizada para mostrar valores en el sistema',
            'ai_chat_enabled': 'Habilita la funcionalidad de chat con IA',
            'openai_api_key': 'Clave de API de OpenAI para acceder a ChatGPT',
            'openai_model': 'Modelo de IA a utilizar (ej: gpt-4o, gpt-3.5-turbo)',
            'ai_employee_analysis_prompt': 'Plantilla del prompt que se enviará a la IA para analizar candidatos. Usa {datos} donde se insertarán los datos del candidato.',
            'paypal_enabled': 'Habilita el sistema de pagos con PayPal',
            'paypal_mode': 'Usa "sandbox" para pruebas o "live" para producción',
            'paypal_client_id': 'Client ID obtenido desde https://developer.paypal.com',
            'paypal_client_secret': 'Client Secret obtenido desde https://developer.paypal.com',
            'paypal_webhook_id': 'ID del webhook para notificaciones avanzadas (opcional)',
            'enable_telegram_notifications': 'Envía notificaciones cuando se crean nuevos tickets',
            'telegram_bot_token': 'Token proporcionado por @BotFather al crear el bot',
            'telegram_chat_id': 'ID del grupo donde enviar notificaciones (ej: -100123456789)',
            'enable_email_notifications': 'Envía notificaciones por email cuando se reciben contactos desde la web',
            'notification_emails': 'Direcciones de email donde enviar notificaciones (una por línea)',
            'email_host': 'Servidor de correo saliente (ej: smtp.gmail.com, mail.tu-dominio.com)',
            'email_port': 'Puerto del servidor SMTP (587 para TLS, 465 para SSL, 25 para sin cifrado)',
            'email_host_user': 'Dirección de email para autenticación SMTP',
            'email_host_password': 'Contraseña o token de aplicación para SMTP',
            'email_use_tls': 'Activar cifrado TLS (recomendado para puerto 587)',
            'email_use_ssl': 'Activar cifrado SSL (para puerto 465)',
            'email_from': 'Dirección de email que aparecerá como remitente',
        }
    
    def clean_site_name(self):
        """Validar el nombre del sitio"""
        site_name = self.cleaned_data.get('site_name', '').strip()
        
        if not site_name:
            raise forms.ValidationError('El nombre del sitio es requerido.')
        
        if len(site_name) < 3:
            raise forms.ValidationError('El nombre del sitio debe tener al menos 3 caracteres.')
        
        if len(site_name) > 100:
            raise forms.ValidationError('El nombre del sitio no puede exceder 100 caracteres.')
        
        return site_name
    
    def clean_ai_employee_analysis_prompt(self):
        """Validar el prompt de análisis de empleados"""
        prompt = self.cleaned_data.get('ai_employee_analysis_prompt', '').strip()
        
        if prompt and '{datos}' not in prompt:
            raise forms.ValidationError('El prompt debe contener la variable {datos} donde se insertarán los datos del candidato.')
        
        return prompt


class DocumentForm(forms.ModelForm):
    """Formulario para crear y editar documentos"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'company', 'tags', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del documento',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional del documento...',
                'maxlength': '500'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.rtf,.odt,.xls,.xlsx,.ods,.ppt,.pptx,.odp,.jpg,.jpeg,.png,.gif,.bmp,.svg,.zip,.rar,.7z,.tar,.gz'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiquetas separadas por comas (ej: manual, tutorial, guía)',
                'maxlength': '300'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'file': 'Archivo',
            'company': 'Empresa/Cliente',
            'tags': 'Etiquetas',
            'is_public': 'Disponible públicamente',
        }
        help_texts = {
            'file': 'Archivos permitidos: PDF, DOC, DOCX, TXT, imágenes, etc. Máximo 10MB',
            'tags': 'Etiquetas para categorizar y buscar el documento',
            'is_public': 'Si está marcado, el documento puede ser accedido sin autenticación',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo empresas activas
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "Sin empresa asociada"
    
    def clean_file(self):
        """Validar el archivo subido"""
        file = self.cleaned_data.get('file')
        
        if not file:
            return file
        
        # Validar tamaño
        from django.conf import settings
        max_size = getattr(settings, 'DOCUMENT_UPLOAD_MAX_SIZE', 10 * 1024 * 1024)
        if file.size > max_size:
            raise forms.ValidationError(f'El archivo es demasiado grande. Máximo permitido: {max_size // (1024*1024)}MB')
        
        # Validar extensión
        allowed_extensions = getattr(settings, 'DOCUMENT_ALLOWED_EXTENSIONS', [])
        if allowed_extensions:
            file_extension = file.name.split('.')[-1].lower() if '.' in file.name else ''
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f'Tipo de archivo no permitido. Extensiones permitidas: {", ".join(allowed_extensions)}')
        
        return file
    
    def clean_title(self):
        """Validar el título"""
        title = self.cleaned_data.get('title', '').strip()
        
        if not title:
            raise forms.ValidationError('El título es requerido.')
        
        if len(title) < 3:
            raise forms.ValidationError('El título debe tener al menos 3 caracteres.')
        
        return title
    
    def clean_tags(self):
        """Limpiar y validar etiquetas"""
        tags = self.cleaned_data.get('tags', '').strip()
        
        if tags:
            # Limpiar etiquetas: eliminar espacios extras y vacías
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Validar longitud de etiquetas individuales
            for tag in tag_list:
                if len(tag) > 50:
                    raise forms.ValidationError('Las etiquetas individuales no pueden exceder 50 caracteres.')
            
            # Reunir las etiquetas limpias
            tags = ', '.join(tag_list)
        
        return tags


class UrlManagerForm(forms.ModelForm):
    """Formulario para crear y editar URLs con credenciales"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la contraseña (opcional)'
        }),
        label='Contraseña (opcional)',
        help_text='La contraseña se almacenará de forma segura y encriptada',
        required=False
    )
    
    class Meta:
        model = UrlManager
        fields = ['title', 'url', 'username', 'password', 'description', 'category', 'is_active', 'is_principal']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Panel de administración del servidor'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/admin'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nombre_usuario (opcional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de esta URL y sus credenciales...'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Servidor, Base de datos, API, etc.'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_principal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'url': 'URL',
            'username': 'Usuario (opcional)',
            'description': 'Descripción',
            'category': 'Categoría',
            'is_active': 'Activo',
            'is_principal': 'URL Principal',
        }
        help_texts = {
            'title': 'Nombre descriptivo para identificar esta URL',
            'url': 'Dirección web completa (debe incluir http:// o https://)',
            'username': 'Nombre de usuario para acceder a esta URL (opcional)',
            'description': 'Información adicional sobre el propósito de esta URL',
            'category': 'Categoría para organizar las URLs',
            'is_active': 'Desmarcar si la URL ya no está en uso',
            'is_principal': 'Marcar para mostrar esta URL en el dashboard principal',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance_pk = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        # Hacer username y password opcionales
        self.fields['username'].required = False
        self.fields['password'].required = False
        
        # Si estamos editando, cambiar el help text de la contraseña
        if self.instance_pk and hasattr(self.instance_pk, 'pk'):
            self.fields['password'].help_text = 'Dejar en blanco para mantener la contraseña actual'
            self.fields['password'].required = False
    
    def clean_url(self):
        """Validar la URL"""
        url = self.cleaned_data.get('url', '').strip()
        
        if not url:
            raise forms.ValidationError('La URL es requerida.')
        
        # Validar que tenga protocolo
        if not url.startswith(('http://', 'https://')):
            raise forms.ValidationError('La URL debe comenzar con http:// o https://')
        
        # Validar que no sea demasiado larga
        if len(url) > 500:
            raise forms.ValidationError('La URL es demasiado larga (máximo 500 caracteres).')
        
        return url
    
    def clean_title(self):
        """Validar el título"""
        title = self.cleaned_data.get('title', '').strip()
        
        if not title:
            raise forms.ValidationError('El título es requerido.')
        
        if len(title) < 3:
            raise forms.ValidationError('El título debe tener al menos 3 caracteres.')
        
        return title
    
    def clean_username(self):
        """Validar el usuario"""
        username = self.cleaned_data.get('username')
        
        # Si es None o vacío, retornar vacío (es opcional)
        if not username:
            return ""
        
        # Si hay valor, validar que tenga al menos 2 caracteres
        username = username.strip()
        if len(username) < 2:
            raise forms.ValidationError('El nombre de usuario debe tener al menos 2 caracteres.')
        
        return username
    
    def clean_password(self):
        """Validar la contraseña"""
        password = self.cleaned_data.get('password')
        
        # La contraseña es opcional ahora
        if not password:
            return ""
        
        # Si hay contraseña, validar longitud mínima
        if len(password) < 3:
            raise forms.ValidationError('La contraseña debe tener al menos 3 caracteres.')
        
        return password
    
    def save(self, commit=True):
        """Guardar URL con contraseña encriptada"""
        instance = super().save(commit=False)
        
        # Solo encriptar la contraseña si se proporcionó una nueva
        password = self.cleaned_data.get('password')
        if password:
            instance.set_password(password)
        
        if commit:
            instance.save()
        
        return instance


class UrlManagerFilterForm(forms.Form):
    """Formulario para filtrar URLs"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título, URL o descripción...'
        }),
        label='Buscar'
    )
    
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por categoría...'
        }),
        label='Categoría'
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('True', 'Solo activas'),
            ('False', 'Solo inactivas'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )


class MultipleFileInput(forms.ClearableFileInput):
    """Widget personalizado para múltiples archivos"""
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    """Campo personalizado para múltiples archivos"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class WorkOrderForm(forms.ModelForm):
    """Formulario para crear y editar órdenes de trabajo"""
    
    attachments = MultipleFileField(
        required=False,
        label='Adjuntos',
        help_text='Puede seleccionar múltiples archivos (PDF, DOC, TXT, imágenes, Excel, ZIP)',
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.xls,.xlsx,.zip,.rar'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo empresas activas
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
        self.fields['company'].empty_label = "Seleccionar empresa"
        
        # Configurar campo proyecto
        self.fields['project'].queryset = Project.objects.filter(is_active=True).order_by('name')
        self.fields['project'].empty_label = "Seleccionar proyecto (opcional)"
        
        # Configurar queryset para usuarios asignables (agentes)
        try:
            agentes_group = Group.objects.get(name='Agentes')
            agentes = User.objects.filter(groups=agentes_group, is_active=True)
            self.fields['assigned_to'].queryset = agentes
        except Group.DoesNotExist:
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        
        self.fields['assigned_to'].empty_label = "Sin asignar"
    
    class Meta:
        model = WorkOrder
        fields = [
            'title', 'description', 'company', 'project', 'status', 'due_date', 
            'estimated_hours', 'amount', 'priority', 'assigned_to', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo de la orden de trabajo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descripción detallada del trabajo a realizar...'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'project': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 8.5',
                'step': '0.5',
                'min': '0'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1500.00',
                'step': '0.01',
                'min': '0'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción del trabajo',
            'company': 'Empresa',
            'project': 'Proyecto',
            'status': 'Estado',
            'due_date': 'Fecha de entrega',
            'estimated_hours': 'Horas estimadas',
            'amount': 'Importe',
            'priority': 'Prioridad',
            'assigned_to': 'Asignar a',
            'is_public': 'Publicar públicamente',
        }
        help_texts = {
            'title': 'Título descriptivo de la orden de trabajo',
            'description': 'Descripción detallada de todo lo que se necesita realizar',
            'company': 'Empresa a la que se dirige la orden de trabajo',
            'project': 'Proyecto asociado a la orden de trabajo (opcional)',
            'due_date': 'Fecha límite para completar la orden (opcional)',
            'estimated_hours': 'Tiempo estimado para completar el trabajo',
            'amount': 'Precio o costo de la orden de trabajo (opcional)',
            'priority': 'Nivel de urgencia de la orden',
            'assigned_to': 'Usuario responsable de ejecutar la orden',
            'is_public': 'Permite que esta orden sea visible públicamente',
        }
    
    def clean_title(self):
        """Validar el título"""
        title = self.cleaned_data.get('title', '').strip()
        
        if not title:
            raise forms.ValidationError('El título es requerido.')
        
        if len(title) < 5:
            raise forms.ValidationError('El título debe tener al menos 5 caracteres.')
        
        if len(title) > 200:
            raise forms.ValidationError('El título no puede exceder 200 caracteres.')
        
        return title
    
    def clean_description(self):
        """Validar la descripción"""
        description = self.cleaned_data.get('description', '').strip()
        
        if not description:
            raise forms.ValidationError('La descripción es requerida.')
        
        if len(description) < 20:
            raise forms.ValidationError('La descripción debe tener al menos 20 caracteres.')
        
        return description
    
    def clean_due_date(self):
        """Validar la fecha de entrega"""
        due_date = self.cleaned_data.get('due_date')
        
        if not due_date:
            raise forms.ValidationError('La fecha de entrega es requerida.')
        
        # Verificar que la fecha no sea en el pasado
        from django.utils import timezone
        if due_date < timezone.now().date():
            raise forms.ValidationError('La fecha de entrega no puede ser en el pasado.')
        
        return due_date
    
    def clean_estimated_hours(self):
        """Validar las horas estimadas"""
        hours = self.cleaned_data.get('estimated_hours')
        
        if hours is not None:
            if hours < 0:
                raise forms.ValidationError('Las horas estimadas no pueden ser negativas.')
            
            if hours > 1000:
                raise forms.ValidationError('Las horas estimadas no pueden exceder 1000.')
        
        return hours
    
    def save(self, created_by=None, commit=True):
        """Guardar orden de trabajo"""
        work_order = super().save(commit=False)
        
        if created_by:
            work_order.created_by = created_by
        
        if commit:
            work_order.save()
            
            # Manejar adjuntos múltiples
            files = self.files.getlist('attachments')
            if files:
                from .models import WorkOrderAttachment
                import os
                
                for file in files:
                    # Crear el adjunto
                    attachment = WorkOrderAttachment(
                        work_order=work_order,
                        file=file,
                        original_filename=file.name,
                        uploaded_by=created_by if created_by else work_order.created_by,
                        file_size=file.size
                    )
                    attachment.save()
        
        return work_order


class WorkOrderFilterForm(forms.Form):
    """Formulario para filtrar órdenes de trabajo"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título o descripción...'
        }),
        label='Buscar'
    )
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        required=False,
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Empresa'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + WorkOrder.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las prioridades')] + [
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Prioridad'
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Todos los asignados",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Asignado a'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo agentes para el campo assigned_to
        try:
            agentes_group = Group.objects.get(name='Agentes')
            agentes = User.objects.filter(groups=agentes_group, is_active=True)
            self.fields['assigned_to'].queryset = agentes
        except Group.DoesNotExist:
            pass


class TaskForm(forms.ModelForm):
    """Formulario para crear y editar tareas"""
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'assigned_users', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la tarea'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la tarea'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_users': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'status': 'Estado',
            'priority': 'Prioridad',
            'assigned_users': 'Usuarios Asignados',
            'due_date': 'Fecha de Vencimiento',
        }
        help_texts = {
            'assigned_users': 'Selecciona uno o más usuarios para asignar a esta tarea',
            'due_date': 'Fecha y hora límite para completar la tarea (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar usuarios activos
        self.fields['assigned_users'].queryset = User.objects.filter(is_active=True).order_by('username')
        
        # Configurar widget más amigable para múltiples usuarios
        self.fields['assigned_users'].widget = forms.CheckboxSelectMultiple()
        
        # Hacer algunos campos opcionales para nueva tarea
        if not self.instance.pk:  # Nueva tarea
            self.fields['status'].initial = 'pending'
            self.fields['priority'].initial = 'medium'


class ChatMessageForm(forms.ModelForm):
    """Formulario para enviar mensajes de chat"""
    
    class Meta:
        model = ChatMessage
        fields = ['message', 'attachment']
        widgets = {
            'message': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe un mensaje...',
                'autocomplete': 'off',
                'maxlength': '1000'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,application/pdf,.doc,.docx,.txt,.zip,.rar'
            }),
        }
        labels = {
            'message': 'Mensaje',
            'attachment': 'Archivo adjunto',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].required = False
        self.fields['attachment'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
        attachment = cleaned_data.get('attachment')
        
        if not message and not attachment:
            raise forms.ValidationError('Debes escribir un mensaje o adjuntar un archivo.')
        
        return cleaned_data


class ChatRoomForm(forms.ModelForm):
    """Formulario para crear salas de chat grupales"""
    
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label='Participantes'
    )
    
    class Meta:
        model = ChatRoom
        fields = ['name', 'participants']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del grupo (opcional)'
            }),
        }
        labels = {
            'name': 'Nombre del grupo',
            'participants': 'Participantes',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Excluir al usuario actual de la lista de participantes
        if self.user:
            self.fields['participants'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id=self.user.id).order_by('first_name', 'last_name', 'username')
    
    def save(self, commit=True):
        room = super().save(commit=False)
        room.is_group = True
        
        if commit:
            room.save()
            # Agregar participantes seleccionados
            room.participants.set(self.cleaned_data['participants'])
            # Agregar al usuario actual como participante
            if self.user:
                room.participants.add(self.user)
        
        return room


class CommandForm(forms.ModelForm):
    """Formulario para crear y editar comandos"""
    
    class Meta:
        model = Command
        fields = [
            'title', 'command', 'description', 'category', 'tags',
            'example_usage', 'notes', 'is_dangerous', 'is_favorite'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Buscar archivos por extensión'
            }),
            'command': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 3,
                'placeholder': 'find . -name "*.txt" -type f'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de lo que hace el comando'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'buscar, archivos, find, linux'
            }),
            'example_usage': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 3,
                'placeholder': 'Ejemplo práctico de uso (opcional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas adicionales, advertencias o tips (opcional)'
            }),
            'is_dangerous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_favorite': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'command': 'Comando',
            'description': 'Descripción',
            'category': 'Categoría',
            'tags': 'Etiquetas',
            'example_usage': 'Ejemplo de uso',
            'notes': 'Notas adicionales',
            'is_dangerous': 'Comando peligroso',
            'is_favorite': 'Marcar como favorito',
        }


class CommandSearchForm(forms.Form):
    """Formulario para buscar comandos"""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Buscar comandos... (título, descripción, etiquetas)',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ChoiceField(
        choices=[('', 'Todas las categorías')] + Command.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    favorites_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Solo favoritos'
    )
    
    dangerous_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Solo comandos peligrosos'
    )


class PublicContactForm(forms.ModelForm):
    """Formulario público para envío de datos de contacto"""
    
    class Meta:
        model = ContactFormSubmission
        fields = [
            'company_name', 'contact_name', 'email', 'phone', 
            'website', 'address', 'message'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre de su empresa',
                'required': True
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Su nombre completo',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'correo@empresa.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 600 000 000'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.empresa.com'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa de la empresa'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntenos sobre su empresa y los servicios que necesita...'
            })
        }
        labels = {
            'company_name': 'Nombre de la Empresa *',
            'contact_name': 'Nombre del Contacto *',
            'email': 'Correo Electrónico *',
            'phone': 'Teléfono',
            'website': 'Sitio Web',
            'address': 'Dirección',
            'message': 'Mensaje Adicional'
        }
        help_texts = {
            'email': 'Utilizaremos este correo para contactarle',
            'phone': 'Número de teléfono de contacto',
            'website': 'URL completa de su sitio web',
            'address': 'Dirección física de su empresa',
            'message': 'Información adicional sobre su empresa o servicios que necesita'
        }


class ContactFormManagementForm(forms.ModelForm):
    """Formulario para gestionar formularios de contacto desde el admin"""
    
    class Meta:
        model = ContactFormSubmission
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas internas sobre el procesamiento de esta solicitud...'
            })
        }


class CompanyFromContactForm(forms.ModelForm):
    """Formulario para crear empresa desde formulario de contacto"""
    
    class Meta:
        model = Company
        fields = ['name', 'description', 'address', 'phone', 'email', 'website', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la empresa...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#28a745'
            })
        }
    
    def __init__(self, *args, **kwargs):
        contact_form = kwargs.pop('contact_form', None)
        super().__init__(*args, **kwargs)
        
        # Siempre asegurar que el color tenga un valor por defecto
        self.fields['color'].initial = '#28a745'
        
        if contact_form:
            # Pre-llenar campos desde el formulario de contacto
            self.fields['name'].initial = contact_form.company_name
            if contact_form.address:
                self.fields['address'].initial = contact_form.address
            if contact_form.phone:
                self.fields['phone'].initial = contact_form.phone
            if contact_form.email:
                self.fields['email'].initial = contact_form.email
            if contact_form.website:
                self.fields['website'].initial = contact_form.website
            
            description_parts = ["Empresa creada desde formulario de contacto."]
            if contact_form.contact_name:
                description_parts.append(f"Contacto: {contact_form.contact_name}")
            if contact_form.message:
                description_parts.append(f"Mensaje original: {contact_form.message}")
            
            self.fields['description'].initial = "\n\n".join(description_parts)

    def save(self, commit=True):
        """Guardar la empresa con validaciones adicionales"""
        company = super().save(commit=False)
        
        # Asegurar que el nombre no esté vacío
        if not company.name or company.name.strip() == '':
            raise forms.ValidationError("El nombre de la empresa es requerido")
        
        # Asegurar que el color no esté vacío
        if not company.color:
            company.color = '#28a745'
        
        if commit:
            company.save()
        return company


class MeetingForm(forms.ModelForm):
    """Formulario para crear y editar reuniones"""
    
    meeting_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de la reunión'
    )
    
    meeting_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Hora de la reunión'
    )
    
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'spin_methodology', 'company', 'product', 'duration', 'location', 'status', 'allow_questions', 'require_email']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la reunión'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción de la reunión'
            }),
            'spin_methodology': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Preguntas SPIN se generarán automáticamente aquí...',
                'readonly': True
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'product': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'max': '480',
                'step': '15',
                'placeholder': '60'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación o enlace de la reunión'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'allow_questions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['duration'].help_text = 'Duración en minutos'
        self.fields['allow_questions'].help_text = 'Permitir que los asistentes hagan preguntas'
        self.fields['require_email'].help_text = 'Requerir email para registrarse'
        
        # Configurar producto disponible
        from .models import Company, Product
        companies = Company.objects.all().order_by('name')
        company_choices = [('', '---------')] + [(c.id, c.name) for c in companies]
        self.fields['company'].choices = company_choices
        self.fields['company'].required = False
        
        products = Product.objects.filter(is_active=True).order_by('name')
        product_choices = [('', '---------')] + [(p.id, f"{p.name} - {p.price_with_currency}") for p in products]
        self.fields['product'].choices = product_choices
        self.fields['product'].required = False
        self.fields['product'].help_text = 'Selecciona el producto principal que se discutirá en la reunión'
        
        # Si estamos editando, llenar los campos de fecha y hora
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['meeting_date'].initial = self.instance.date.date()
            self.fields['meeting_time'].initial = self.instance.date.time()
    
    def save(self, commit=True):
        meeting = super().save(commit=False)
        
        # Combinar fecha y hora
        meeting_date = self.cleaned_data['meeting_date']
        meeting_time = self.cleaned_data['meeting_time']
        
        from datetime import datetime
        meeting.date = datetime.combine(meeting_date, meeting_time)
        
        if commit:
            meeting.save()
            # Guardar relaciones ManyToMany después de guardar el objeto principal
            self.save_m2m()
        return meeting


class MeetingAttendeeForm(forms.ModelForm):
    """Formulario público para registro de asistentes"""
    
    class Meta:
        model = MeetingAttendee
        fields = ['name', 'email', 'company']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu empresa (opcional)'
            }),
        }
    
    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting = meeting
        
        # Si la reunión requiere email, hacerlo obligatorio
        if meeting and meeting.require_email:
            self.fields['email'].required = True
            self.fields['email'].widget.attrs['required'] = True
        
        self.fields['name'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Permitir múltiples registros con el mismo email
        return email


class MeetingQuestionForm(forms.ModelForm):
    """Formulario público para hacer preguntas"""
    
    class Meta:
        model = MeetingQuestion
        fields = ['question', 'asker_name', 'asker_email']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '¿Cuál es tu pregunta?',
                'required': True
            }),
            'asker_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre (opcional)'
            }),
            'asker_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question'].required = True


class MeetingAnswerForm(forms.ModelForm):
    """Formulario para responder preguntas (solo organizadores)"""
    
    class Meta:
        model = MeetingQuestion
        fields = ['answer', 'status']
        widgets = {
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Respuesta a la pregunta'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class OpportunityActivityForm(forms.ModelForm):
    """Formulario para crear y editar actividades de oportunidades"""
    
    class Meta:
        model = OpportunityActivity
        fields = [
            'title', 'description', 'activity_type', 'priority', 
            'scheduled_date', 'assigned_to', 'duration_minutes', 'location'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la actividad'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la actividad'
            }),
            'activity_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duración en minutos',
                'min': '1'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        opportunity = kwargs.pop('opportunity', None)
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios a solo agentes activos
        if hasattr(User, 'groups'):
            try:
                agent_group = Group.objects.get(name='Agentes')
                agent_users = User.objects.filter(
                    groups=agent_group,
                    is_active=True
                ).order_by('first_name', 'last_name')
            except Group.DoesNotExist:
                agent_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        else:
            agent_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        self.fields['assigned_to'].queryset = agent_users
        
        # Si hay un usuario actual, asignarlo por defecto
        if current_user:
            self.fields['assigned_to'].initial = current_user
        
        # Configurar fecha por defecto a la hora actual + 1 hora
        if not self.instance.pk:
            from django.utils import timezone
            default_date = timezone.now() + timezone.timedelta(hours=1)
            self.fields['scheduled_date'].initial = default_date.strftime('%Y-%m-%dT%H:%M')


class OpportunityActivityStandaloneForm(forms.ModelForm):
    """Formulario para crear actividades seleccionando la oportunidad"""
    
    opportunity = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Oportunidad',
        help_text='Selecciona la oportunidad para esta actividad (opcional)',
        required=False
    )
    
    contact = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Contacto',
        help_text='Selecciona el contacto relacionado con esta actividad (opcional)',
        required=False
    )
    
    class Meta:
        model = OpportunityActivity
        fields = [
            'opportunity', 'contact', 'title', 'description', 'activity_type', 'priority', 
            'scheduled_date', 'assigned_to', 'duration_minutes', 'location'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la actividad'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la actividad'
            }),
            'activity_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duración en minutos',
                'min': '1'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar oportunidades
        from .models import Opportunity
        from . import utils
        from django.db import models
        if current_user and utils.is_agent(current_user):
            # Agentes pueden ver todas las oportunidades
            self.fields['opportunity'].queryset = Opportunity.objects.all().order_by('-created_at')
        elif current_user:
            # Usuarios normales solo ven sus oportunidades
            self.fields['opportunity'].queryset = Opportunity.objects.filter(
                models.Q(created_by=current_user) | models.Q(assigned_to=current_user)
            ).order_by('-created_at')
        
        # Filtrar contactos (todos los usuarios pueden ver todos los contactos)
        self.fields['contact'].queryset = Contact.objects.all().order_by('name')
        self.fields['contact'].empty_label = "Seleccionar contacto (opcional)"
        
        # Filtrar usuarios a solo agentes activos
        if hasattr(User, 'groups'):
            try:
                agent_group = Group.objects.get(name='Agentes')
                agent_users = User.objects.filter(
                    groups=agent_group,
                    is_active=True
                ).order_by('first_name', 'last_name')
            except Group.DoesNotExist:
                agent_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        else:
            agent_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        self.fields['assigned_to'].queryset = agent_users
        
        # Si hay un usuario actual, asignarlo por defecto
        if current_user:
            self.fields['assigned_to'].initial = current_user
        
        # Configurar fecha por defecto a la hora actual + 1 hora
        if not self.instance.pk:
            from django.utils import timezone
            default_date = timezone.now() + timezone.timedelta(hours=1)
            self.fields['scheduled_date'].initial = default_date.strftime('%Y-%m-%dT%H:%M')
        
        self.fields['assigned_to'].queryset = agent_users
        self.fields['assigned_to'].empty_label = "Seleccionar agente"
        
        # Establecer valores por defecto al crear nueva actividad
        if not self.instance.pk:
            # Usuario actual como asignado por defecto
            if current_user:
                self.fields['assigned_to'].initial = current_user
            
            # Fecha programada: 7 días más desde hoy
            from django.utils import timezone
            from datetime import timedelta
            default_date = timezone.now() + timedelta(days=7)
            self.fields['scheduled_date'].initial = default_date.strftime('%Y-%m-%dT%H:%M')
            
            # Duración por defecto: 5 minutos
            self.fields['duration_minutes'].initial = 5
        
        # Personalizar labels
        self.fields['title'].label = 'Título de la Actividad'
        self.fields['description'].label = 'Descripción'
        self.fields['activity_type'].label = 'Tipo de Actividad'
        self.fields['priority'].label = 'Prioridad'
        self.fields['scheduled_date'].label = 'Fecha y Hora Programada'
        self.fields['assigned_to'].label = 'Asignado a'
        self.fields['duration_minutes'].label = 'Duración (minutos)'
        self.fields['location'].label = 'Ubicación'


class OpportunityActivityCompleteForm(forms.ModelForm):
    """Formulario para completar actividades"""
    
    class Meta:
        model = OpportunityActivity
        fields = ['result', 'status']
        widgets = {
            'result': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el resultado de la actividad...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo permitir estados de finalización
        self.fields['status'].choices = [
            ('completed', 'Completada'),
            ('cancelled', 'Cancelada'),
        ]
        
        self.fields['result'].label = 'Resultado de la Actividad'
        self.fields['status'].label = 'Estado Final'


class ClientRequestForm(forms.ModelForm):
    """Formulario para crear solicitudes al cliente"""
    
    class Meta:
        model = ClientRequest
        fields = ['title', 'description', 'requested_to', 'company', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la solicitud',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe lo que necesitas del cliente...'
            }),
            'requested_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la persona'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'requested_to': 'Solicitado a',
            'company': 'Empresa',
            'attachment': 'Archivo adjunto (opcional)',
        }


class ClientRequestResponseForm(forms.ModelForm):
    """Formulario para que el cliente responda una solicitud"""
    
    class Meta:
        model = ClientRequestResponse
        fields = ['response_text', 'attachment']
        widgets = {
            'response_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Escribe tu respuesta aquí...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'response_text': 'Respuesta',
            'attachment': 'Adjunto (Opcional)',
        }


class ClientRequestTemplateForm(forms.ModelForm):
    """Formulario para crear plantillas de solicitudes"""
    
    class Meta:
        model = ClientRequestTemplate
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Onboarding de Cliente, Cierre de Mes, etc.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe para qué sirve esta plantilla...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre de la Plantilla',
            'description': 'Descripción',
            'is_active': 'Activa',
        }


class ClientRequestTemplateItemForm(forms.ModelForm):
    """Formulario para items de plantilla"""
    
    class Meta:
        model = ClientRequestTemplateItem
        fields = ['title', 'description', 'requested_to', 'order', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la solicitud'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de lo que se solicita...'
            }),
            'requested_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la persona'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'requested_to': 'Solicitado a',
            'order': 'Orden',
            'attachment': 'Archivo adjunto (opcional)',
        }


class ExecuteTemplateForm(forms.Form):
    """Formulario para ejecutar una plantilla y crear solicitudes"""
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Empresa',
        help_text='Selecciona la empresa para la cual crear las solicitudes'
    )


class CourseForm(forms.ModelForm):
    """Formulario para crear y editar cursos"""
    
    class Meta:
        model = Course
        fields = ['title', 'description', 'company', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del curso',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del curso...'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título del Curso',
            'description': 'Descripción',
            'company': 'Empresa (Opcional)',
            'is_active': 'Activo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Company
        
        # Hacer el campo company opcional
        self.fields['company'].required = False
        self.fields['company'].empty_label = "Todos los usuarios (público)"
        
        # Solo mostrar empresas activas
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')


class CourseClassForm(forms.ModelForm):
    """Formulario para crear y editar clases de curso"""
    
    class Meta:
        model = CourseClass
        fields = ['title', 'description', 'video_url', 'order', 'duration_minutes', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la clase',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la clase...'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '60'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título de la Clase',
            'description': 'Descripción',
            'video_url': 'URL del Video',
            'order': 'Orden',
            'duration_minutes': 'Duración (minutos)',
            'is_active': 'Activa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['video_url'].required = False
        self.fields['duration_minutes'].required = False


class ContactForm(forms.ModelForm):
    """Formulario para crear y editar contactos"""
    
    class Meta:
        model = Contact
        fields = [
            'name', 'email', 'phone', 'position', 'company', 'country', 'erp',
            'status', 'source', 'notes', 'contact_date',
            'contacted_by_phone', 'contacted_by_web', 'had_meeting', 'meeting_date',
            'contact_tracking_notes', 'last_contact_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@empresa.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 600 000 000'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Director, Gerente, etc.'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'España, México, Argentina, etc.'
            }),
            'erp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SAP, Odoo, Navision, etc.'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'LinkedIn, referencia, evento, etc.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre la conversación...'
            }),
            'contact_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'contacted_by_phone': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'contacted_by_web': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'had_meeting': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'meeting_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'contact_tracking_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas sobre los contactos realizados...'
            }),
            'last_contact_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        from django.utils import timezone
        now = timezone.now()
        
        # Establecer valores por defecto para nuevos contactos
        if not self.instance.pk:
            # Contacto nuevo
            self.fields['contact_date'].initial = now.strftime('%Y-%m-%dT%H:%M')
            self.fields['last_contact_date'].initial = now.strftime('%Y-%m-%dT%H:%M')
        else:
            # Contacto existente - mantener valores actuales o sugerir fecha actual si está vacío
            if self.instance.contact_date:
                self.fields['contact_date'].initial = self.instance.contact_date.strftime('%Y-%m-%dT%H:%M')
            else:
                self.fields['contact_date'].initial = now.strftime('%Y-%m-%dT%H:%M')
                
            if self.instance.last_contact_date:
                self.fields['last_contact_date'].initial = self.instance.last_contact_date.strftime('%Y-%m-%dT%H:%M')
            elif not self.instance.last_contact_date:
                # Si no hay fecha de último contacto, sugerir la fecha actual
                self.fields['last_contact_date'].initial = now.strftime('%Y-%m-%dT%H:%M')
        
        # Personalizar labels
        self.fields['name'].label = 'Nombre Completo'
        self.fields['email'].label = 'Email'
        self.fields['phone'].label = 'Teléfono'
        self.fields['position'].label = 'Cargo'
        self.fields['company'].label = 'Empresa'
        self.fields['status'].label = 'Estado del Contacto'
        self.fields['source'].label = 'Fuente'
        self.fields['notes'].label = 'Notas'
        self.fields['contact_date'].label = 'Fecha y Hora de Contacto'
        self.fields['contacted_by_phone'].label = 'Contactado por teléfono'
        self.fields['contacted_by_web'].label = 'Contactado por web/email'
        self.fields['had_meeting'].label = 'Reunión realizada'
        self.fields['meeting_date'].label = 'Fecha de reunión'
        self.fields['contact_tracking_notes'].label = 'Notas de seguimiento'
        self.fields['last_contact_date'].label = 'Fecha del último contacto'


class BlogCategoryForm(forms.ModelForm):
    """Formulario para crear y editar categorías de blog"""
    
    class Meta:
        model = BlogCategory
        fields = ['name', 'description', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría...'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nombre'
        self.fields['description'].label = 'Descripción'
        self.fields['color'].label = 'Color'
        self.fields['is_active'].label = 'Activa'
        
        # Establecer valor por defecto para el color si no existe
        if not self.instance.pk and not self.fields['color'].initial:
            self.fields['color'].initial = '#007bff'
        
        # Establecer valor por defecto para color si no está establecido
        if not self.instance.pk and not self.data.get('color'):
            self.fields['color'].initial = '#007bff'


class BlogPostForm(forms.ModelForm):
    """Formulario para crear y editar artículos de blog"""
    
    class Meta:
        model = BlogPost
        fields = [
            'title', 'excerpt', 'content', 'featured_image', 'category', 
            'status', 'tags', 'meta_description', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del artículo'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Breve resumen del artículo...',
                'maxlength': '300'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Contenido del artículo...'
            }),
            'featured_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiquetas separadas por comas'
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción para SEO...',
                'maxlength': '160'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo categorías activas
        self.fields['category'].queryset = BlogCategory.objects.filter(is_active=True)
        
        # Personalizar labels
        self.fields['title'].label = 'Título'
        self.fields['excerpt'].label = 'Resumen'
        self.fields['content'].label = 'Contenido'
        self.fields['featured_image'].label = 'Imagen Principal'
        self.fields['category'].label = 'Categoría'
        self.fields['status'].label = 'Estado'
        self.fields['tags'].label = 'Etiquetas'
        self.fields['meta_description'].label = 'Meta Descripción (SEO)'
        self.fields['is_featured'].label = 'Artículo Destacado'


class BlogCommentForm(forms.ModelForm):
    """Formulario para comentarios públicos del blog"""
    
    class Meta:
        model = BlogComment
        fields = ['name', 'email', 'website', 'content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tu-sitio-web.com (opcional)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Nombre'
        self.fields['email'].label = 'Email'
        self.fields['website'].label = 'Sitio Web'
        self.fields['content'].label = 'Comentario'
        self.fields['website'].required = False


# ===========================================
# FORMULARIOS PARA CHAT CON IA
# ===========================================

class AIChatSessionForm(forms.ModelForm):
    """Formulario para crear una nueva sesión de chat con IA"""
    
    # Definir las opciones de modelos disponibles
    MODEL_CHOICES = [
        ('gpt-4o', 'GPT-4o (Recomendado)'),
        ('gpt-4o-mini', 'GPT-4o Mini (Rápido)'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo (Económico)'),
        ('gpt-4', 'GPT-4 (Avanzado)'),
    ]
    
    ai_model = forms.ChoiceField(
        choices=MODEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Modelo de IA',
        help_text='Selecciona el modelo de IA que deseas utilizar',
        initial='gpt-4o'
    )
    
    class Meta:
        model = AIChatSession
        fields = ['title', 'ai_model']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la conversación',
                'maxlength': '200'
            }),
        }
        labels = {
            'title': 'Título de la conversación',
        }
        help_texts = {
            'title': 'Dale un nombre descriptivo a tu conversación',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ya no necesitamos configurar choices aquí porque está definido arriba


class AIChatMessageForm(forms.Form):
    """Formulario para enviar mensajes en el chat con IA"""
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Escribe tu mensaje aquí...',
            'maxlength': '4000',
            'name': 'message',
            'id': 'id_message'
        }),
        label='Mensaje',
        max_length=4000,
        help_text='Máximo 4000 caracteres',
        required=True
    )
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        
        if not message:
            raise forms.ValidationError('El mensaje no puede estar vacío.')
        
        if len(message) < 5:
            raise forms.ValidationError('El mensaje debe tener al menos 5 caracteres.')
        
        return message


class ConceptForm(forms.ModelForm):
    """Formulario para crear y editar conceptos"""
    
    class Meta:
        model = Concept
        fields = ['term', 'definition', 'category', 'is_active', 'order']
        widgets = {
            'term': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Término o concepto'
            }),
            'definition': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Definición del concepto',
                'rows': 4
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Categoría (opcional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Orden de visualización'
            }),
        }
        labels = {
            'term': 'Término',
            'definition': 'Definición',
            'category': 'Categoría',
            'is_active': 'Activo',
            'order': 'Orden'
        }
        help_texts = {
            'term': 'Nombre del concepto o término',
            'definition': 'Explicación clara y concisa del concepto',
            'category': 'Categoría a la que pertenece (opcional)',
            'is_active': 'Marcar si el concepto debe mostrarse',
            'order': 'Número para ordenar los conceptos (menor = primero)'
        }


class ContactoWebForm(forms.ModelForm):
    """Formulario para contactos desde la web pública"""
    
    # Campo CAPTCHA matemático
    captcha_question = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'readonly': True,
            'class': 'form-control',
            'style': 'background-color: #f8f9fa; cursor: not-allowed;'
        }),
        label='Verificación de seguridad',
        required=False
    )
    
    captcha_answer = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce el resultado',
            'required': True
        }),
        label='Resultado'
    )
    
    class Meta:
        model = ContactoWeb
        fields = ['nombre', 'email', 'telefono', 'empresa', 'asunto', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu número de teléfono (opcional)'
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de tu empresa (opcional)'
            }),
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '¿En qué podemos ayudarte?',
                'required': True
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe tu consulta o requerimiento...',
                'rows': 4,
                'required': True
            }),
        }
        labels = {
            'nombre': 'Nombre completo',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'empresa': 'Empresa',
            'asunto': 'Asunto',
            'mensaje': 'Mensaje'
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return nombre
    
    def clean_mensaje(self):
        mensaje = self.cleaned_data.get('mensaje')
        if len(mensaje) < 10:
            raise forms.ValidationError('El mensaje debe tener al menos 10 caracteres.')
        return mensaje


class EmployeeHiringOpinionForm(forms.ModelForm):
    """Formulario para editar la opinión de reunión de contratación"""
    
    class Meta:
        model = Employee
        fields = ['hiring_meeting_opinion']
        widgets = {
            'hiring_meeting_opinion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Escriba aquí la opinión sobre la reunión/entrevista de contratación...\n\nPuede incluir:\n- Impresión general del candidato\n- Puntos fuertes identificados\n- Áreas de mejora o preocupaciones\n- Recomendaciones para la decisión final\n- Comentarios sobre fit cultural',
            })
        }
        labels = {
            'hiring_meeting_opinion': 'Opinión de Reunión de Contratación'
        }
        help_texts = {
            'hiring_meeting_opinion': 'Registre aquí sus comentarios y evaluación de la reunión/entrevista con el candidato.'
        }


class EmployeePayrollForm(forms.ModelForm):
    """Formulario para agregar nóminas de empleados"""
    
    class Meta:
        model = EmployeePayroll
        fields = ['period_month', 'period_year', 'payroll_pdf', 'payment_receipt', 'gross_salary', 'net_salary', 'notes']
        widgets = {
            'period_month': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
                (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
                (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
            ]),
            'period_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2020',
                'max': '2030',
                'placeholder': 'Ej: 2025'
            }),
            'payroll_pdf': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'payment_receipt': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'gross_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'net_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre esta nómina...'
            })
        }
        labels = {
            'period_month': 'Mes',
            'period_year': 'Año',
            'payroll_pdf': 'Archivo de Nómina (PDF)',
            'payment_receipt': 'Comprobante de Pago',
            'gross_salary': 'Salario Bruto (€)',
            'net_salary': 'Salario Neto (€)',
            'notes': 'Notas'
        }
        help_texts = {
            'period_month': 'Seleccione el mes de la nómina',
            'period_year': 'Ingrese el año de la nómina',
            'payroll_pdf': 'Archivo PDF de la nómina (requerido)',
            'payment_receipt': 'Comprobante de pago (opcional) - PDF, JPG o PNG',
            'gross_salary': 'Salario bruto antes de descuentos',
            'net_salary': 'Salario neto después de descuentos',
            'notes': 'Información adicional sobre esta nómina'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        period_month = cleaned_data.get('period_month')
        period_year = cleaned_data.get('period_year')
        
        if period_month and period_year:
            # Verificar que no sea una fecha futura
            from django.utils import timezone
            import datetime
            
            current_date = timezone.now().date()
            period_date = datetime.date(period_year, period_month, 1)
            
            if period_date > current_date:
                raise forms.ValidationError('No se puede agregar una nómina de un período futuro.')
        
        return cleaned_data
    
    def clean_payroll_pdf(self):
        payroll_pdf = self.cleaned_data.get('payroll_pdf')
        if payroll_pdf:
            if not payroll_pdf.name.lower().endswith('.pdf'):
                raise forms.ValidationError('El archivo de nómina debe ser un PDF.')
            if payroll_pdf.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('El archivo es demasiado grande. Máximo 10MB.')
        return payroll_pdf
    
    def clean_payment_receipt(self):
        payment_receipt = self.cleaned_data.get('payment_receipt')
        if payment_receipt:
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            if not any(payment_receipt.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('El comprobante debe ser PDF, JPG, JPEG o PNG.')
            if payment_receipt.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo es demasiado grande. Máximo 5MB.')
        return payment_receipt


class AgreementForm(forms.ModelForm):
    """Formulario para crear y editar acuerdos"""
    
    generate_ai_content = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Generar contenido con IA',
        help_text='Generar automáticamente el contenido del acuerdo basado en el título'
    )
    
    ai_prompt_addition = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Instrucciones adicionales para la IA (opcional)...'
        }),
        label='Instrucciones adicionales para IA',
        help_text='Detalles específicos que quieres incluir en el acuerdo'
    )
    
    class Meta:
        model = Agreement
        fields = ['title', 'body', 'status', 'expires_at', 'max_signers', 'requires_approval']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Acuerdo de Confidencialidad'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Contenido completo del acuerdo...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_signers': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Título del Acuerdo',
            'body': 'Contenido del Acuerdo',
            'status': 'Estado',
            'expires_at': 'Fecha de Expiración',
            'max_signers': 'Máximo de Firmantes',
            'requires_approval': 'Requiere Aprobación'
        }
        help_texts = {
            'title': 'Nombre descriptivo del acuerdo',
            'body': 'Contenido completo del acuerdo/contrato',
            'status': 'Estado actual del acuerdo',
            'expires_at': 'Fecha límite para firmar (opcional)',
            'max_signers': 'Número máximo de personas que pueden firmar',
            'requires_approval': 'Las firmas necesitan aprobación manual'
        }
    
    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        if expires_at:
            from django.utils import timezone
            if expires_at <= timezone.now():
                raise forms.ValidationError('La fecha de expiración debe ser en el futuro.')
        return expires_at
    
    def clean(self):
        cleaned_data = super().clean()
        generate_ai = cleaned_data.get('generate_ai_content')
        body = cleaned_data.get('body')
        title = cleaned_data.get('title')
        
        # Si se solicita generar contenido IA, no es necesario que haya body
        if generate_ai and title:
            # El contenido se generará en la vista
            pass
        elif not generate_ai and not body:
            raise forms.ValidationError('Debes proporcionar el contenido del acuerdo o usar la generación con IA.')
        
        return cleaned_data


class AgreementSignatureForm(forms.ModelForm):
    """Formulario para firmar un acuerdo"""
    
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Acepto los términos y condiciones de este acuerdo',
        help_text='Debes aceptar los términos para poder firmar'
    )
    
    class Meta:
        model = AgreementSignature
        fields = ['signer_name', 'signer_email', 'signature_data']
        widgets = {
            'signer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'signer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'signature_data': forms.HiddenInput()
        }
        labels = {
            'signer_name': 'Nombre Completo',
            'signer_email': 'Correo Electrónico',
            'signature_data': 'Firma'
        }
        help_texts = {
            'signer_name': 'Tu nombre como aparecerá en el acuerdo',
            'signer_email': 'Correo para notificaciones y descarga del PDF',
        }
    
    def clean_signer_email(self):
        email = self.cleaned_data.get('signer_email')
        agreement = getattr(self, 'agreement', None)
        
        if agreement and email:
            # Verificar si ya existe una firma para este email en este acuerdo
            existing = AgreementSignature.objects.filter(
                agreement=agreement,
                signer_email=email
            ).first()
            
            if existing and existing != self.instance:
                raise forms.ValidationError('Este correo ya ha firmado este acuerdo.')
        
        return email
    
    def clean_signature_data(self):
        signature_data = self.cleaned_data.get('signature_data')
        if not signature_data:
            raise forms.ValidationError('Debes proporcionar tu firma digital.')
        return signature_data


class AgreementPublicForm(forms.Form):
    """Formulario para publicar un acuerdo"""
    
    confirm_publish = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Confirmo que quiero publicar este acuerdo',
        help_text='Una vez publicado, el acuerdo estará disponible para firmar'
    )
    
    send_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Enviar notificaciones por email',
        help_text='Enviar el enlace del acuerdo por correo (si está configurado)'
    )
    
    email_list = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'email1@ejemplo.com, email2@ejemplo.com'
        }),
        label='Lista de correos (opcional)',
        help_text='Correos separados por comas para enviar el enlace del acuerdo'
    )
    
    def clean_email_list(self):
        email_list = self.cleaned_data.get('email_list', '').strip()
        if email_list:
            emails = [email.strip() for email in email_list.split(',')]
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            
            for email in emails:
                try:
                    validate_email(email)
                except ValidationError:
                    raise forms.ValidationError(f'Email inválido: {email}')
            
            return emails


class LandingPageForm(forms.ModelForm):
    """Formulario para crear/editar Landing Pages"""
    
    class Meta:
        model = LandingPage
        fields = [
            'nombre_producto',
            'descripcion',
            'imagen',
            'slug',
            'is_active',
            'color_principal',
            'color_secundario',
            'titulo_formulario',
            'subtitulo_formulario',
            'empresa_campana',
            'telegram_bot_token',
            'telegram_chat_id',
            'meeting_url'
        ]
        widgets = {
            'nombre_producto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto o servicio'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del producto que aparecerá en la landing page'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'mi-producto-2025'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'color_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'color_secundario': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'titulo_formulario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'VEA TODAS LAS DEMOSTRACIONES'
            }),
            'subtitulo_formulario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción que aparecerá debajo del título del formulario'
            }),
            'empresa_campana': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa de la campaña'
            }),
            'telegram_bot_token': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
            }),
            'telegram_chat_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '-1001234567890 o @mi_canal'
            }),
            'meeting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://calendly.com/tu-usuario'
            })
        }
        labels = {
            'nombre_producto': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'imagen': 'Imagen Principal',
            'slug': 'URL de la Landing Page',
            'is_active': 'Página Activa',
            'color_principal': 'Color Principal',
            'color_secundario': 'Color Secundario',
            'titulo_formulario': 'Título del Formulario',
            'subtitulo_formulario': 'Subtítulo del Formulario',
            'empresa_campana': 'Empresa de la Campaña',
            'telegram_bot_token': 'Bot Token de Telegram',
            'telegram_chat_id': 'Chat ID de Telegram',
            'meeting_url': 'URL de Reunión'
        }
        help_texts = {
            'slug': 'URL única para acceder a la landing page (solo letras, números y guiones)',
            'color_principal': 'Color principal usado en botones y elementos destacados',
            'color_secundario': 'Color de fondo y elementos secundarios',
            'is_active': 'Si está marcado, la landing page será visible públicamente',
            'telegram_bot_token': 'Token del bot de Telegram para enviar notificaciones. Obtén uno creando un bot con @BotFather',
            'telegram_chat_id': 'ID del chat o canal donde enviar notificaciones. Puedes usar @userinfobot para obtenerlo',
            'meeting_url': 'URL donde los visitantes pueden agendar reuniones contigo (Calendly, Google Meet, etc.)'
        }
    
    def clean_slug(self):
        """Validar que el slug sea único y válido"""
        slug = self.cleaned_data.get('slug')
        if slug:
            # Convertir a minúsculas y reemplazar espacios
            slug = slug.lower().replace(' ', '-')
            
            # Validar caracteres permitidos
            import re
            if not re.match(r'^[a-z0-9-]+$', slug):
                raise forms.ValidationError('Solo se permiten letras minúsculas, números y guiones')
            
            # Verificar unicidad
            if self.instance.pk:
                # Editando una landing page existente
                if LandingPage.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe una landing page con esta URL')
            else:
                # Creando nueva landing page
                if LandingPage.objects.filter(slug=slug).exists():
                    raise forms.ValidationError('Ya existe una landing page con esta URL')
        
        return slug


class LandingPageSubmissionForm(forms.ModelForm):
    """Formulario público para envíos de landing pages"""
    
    class Meta:
        model = LandingPageSubmission
        fields = ['nombre', 'apellido', 'email', 'telefono', 'empresa', 'cargo', 'mensaje', 'preferred_contact_time']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre',
                'required': True
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono',
                'required': True
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Empresa',
                'required': True
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo',
                'required': True
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Cuéntanos sobre tu proyecto o necesidades...',
                'rows': 4,
                'style': 'resize: vertical;',
                'required': True
            }),
            'preferred_contact_time': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellidos',
            'email': 'Email',
            'telefono': 'Teléfono',
            'empresa': 'Empresa',
            'cargo': 'Cargo',
            'mensaje': 'Mensaje o comentarios',
            'preferred_contact_time': 'Cuándo prefieres que te contactemos'
        }
    
    def clean_email(self):
        """Validar formato de email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
        return []


class PublicCompanyTicketForm(forms.ModelForm):
    """Formulario público para crear tickets desde una empresa"""
    
    customer_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo'
        }),
        label='Nombre'
    )
    
    customer_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        }),
        label='Email de contacto'
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 123 456 789'
        }),
        label='Teléfono (opcional)'
    )
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Describe brevemente tu solicitud'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Explica detalladamente tu problema o solicitud...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Asunto',
            'description': 'Descripción detallada',
            'priority': 'Prioridad',
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Configurar las opciones de prioridad (excluir "urgent" para usuarios públicos)
        self.fields['priority'].choices = [
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
        ]
        self.fields['priority'].initial = 'medium'
    
    def save(self, commit=True):
        """Crear el ticket con información adicional del cliente"""
        ticket = super().save(commit=False)
        
        if self.company:
            ticket.company = self.company
        
        # Agregar información del cliente a la descripción
        customer_info = f"\n\n--- Información del Cliente ---\n"
        customer_info += f"Nombre: {self.cleaned_data['customer_name']}\n"
        customer_info += f"Email: {self.cleaned_data['customer_email']}\n"
        if self.cleaned_data['customer_phone']:
            customer_info += f"Teléfono: {self.cleaned_data['customer_phone']}\n"
        
        ticket.description = f"{ticket.description}{customer_info}"
        
        if commit:
            ticket.save()
        
        return ticket


class WorkOrderTaskForm(forms.ModelForm):
    """Formulario para crear y editar tareas de órdenes de trabajo"""
    
    class Meta:
        model = WorkOrderTask
        fields = ['title', 'description', 'estimated_hours', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la tarea'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la tarea (opcional)'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0',
                'placeholder': '0.0'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }
        labels = {
            'title': 'Título de la Tarea',
            'description': 'Descripción',
            'estimated_hours': 'Horas Estimadas',
            'order': 'Orden de Ejecución',
        }
    
    def __init__(self, *args, **kwargs):
        self.work_order = kwargs.pop('work_order', None)
        super().__init__(*args, **kwargs)
        
        # Si no hay orden especificada, usar la siguiente disponible
        if not self.instance.pk and self.work_order:
            next_order = self.work_order.tasks.count() + 1
            self.fields['order'].initial = next_order


class WorkOrderTaskTimeEntryForm(forms.ModelForm):
    """Formulario para registrar tiempo en tareas de órdenes de trabajo"""
    
    class Meta:
        model = WorkOrderTaskTimeEntry
        fields = ['hours', 'description', 'date']
        widgets = {
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.25',
                'min': '0.25',
                'placeholder': '1.0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del trabajo realizado (opcional)'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'hours': 'Horas Trabajadas',
            'description': 'Descripción del Trabajo',
            'date': 'Fecha',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Usar la fecha actual por defecto
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date'].initial = timezone.now().date()


class WorkOrderTaskBulkForm(forms.Form):
    """Formulario para agregar múltiples tareas a una orden de trabajo"""
    
    tasks_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Escribe una tarea por línea:\n\nTarea 1\nTarea 2\nTarea 3\n...'
        }),
        label='Tareas',
        help_text='Escribe una tarea por línea. Cada línea se convertirá en una tarea separada.'
    )
    
    def clean_tasks_text(self):
        """Valida y limpia el texto de tareas"""
        tasks_text = self.cleaned_data['tasks_text']
        lines = [line.strip() for line in tasks_text.split('\n') if line.strip()]
        
        if not lines:
            raise forms.ValidationError('Debes escribir al menos una tarea.')
        
        if len(lines) > 50:
            raise forms.ValidationError('No puedes crear más de 50 tareas a la vez.')
        
        return lines


class SharedFileForm(forms.ModelForm):
    """Formulario para subir archivos compartidos"""
    
    class Meta:
        model = SharedFile
        fields = ['title', 'description', 'file', 'company', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del archivo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del archivo (opcional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar,.7z'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título del Archivo',
            'description': 'Descripción',
            'file': 'Archivo',
            'company': 'Empresa',
            'is_public': 'Público para toda la empresa',
        }
        help_texts = {
            'file': 'Archivos permitidos: PDF, Word, Excel, PowerPoint, imágenes, archivos comprimidos',
            'is_public': 'Si está marcado, todos los usuarios de la empresa pueden ver este archivo',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar empresas según el usuario
        if user:
            user_profile = getattr(user, 'userprofile', None)
            from .utils import is_agent
            
            if is_agent(user):
                # Los agentes pueden asignar archivos a cualquier empresa
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
            else:
                # Los usuarios regulares solo pueden usar su empresa
                if user_profile and user_profile.company:
                    self.fields['company'].queryset = Company.objects.filter(
                        id=user_profile.company.id
                    )
                    self.fields['company'].initial = user_profile.company
                    self.fields['company'].widget.attrs['readonly'] = True
                else:
                    # Si no tiene empresa, usar la primera empresa activa
                    first_company = Company.objects.filter(is_active=True).first()
                    if first_company:
                        self.fields['company'].queryset = Company.objects.filter(
                            id=first_company.id
                        )
                        self.fields['company'].initial = first_company
                        self.fields['company'].widget.attrs['readonly'] = True
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Verificar tamaño del archivo (máximo 50MB)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 50MB.')
            
            # Verificar extensión del archivo
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.7z'
            ]
            
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. '
                    'Extensiones permitidas: ' + ', '.join(allowed_extensions)
                )
        
        return file


class PublicSharedFileForm(forms.ModelForm):
    """Formulario público para subir archivos sin autenticación"""
    
    uploader_name = forms.CharField(
        max_length=100,
        label='Tu Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre'
        })
    )
    uploader_email = forms.EmailField(
        label='Tu Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        }),
        help_text='Si ya tienes cuenta en el sistema, se asignará automáticamente a tu empresa'
    )
    
    class Meta:
        model = SharedFile
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del archivo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del archivo (opcional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar,.7z'
            }),
        }
        labels = {
            'title': 'Título del Archivo',
            'description': 'Descripción',
            'file': 'Archivo',
        }
        help_texts = {
            'file': 'Archivos permitidos: PDF, Word, Excel, PowerPoint, imágenes, archivos comprimidos (máximo 50MB)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No necesitamos inicializar company_selection ya que lo removimos
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Verificar tamaño del archivo (máximo 50MB)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 50MB.')
            
            # Verificar extensión del archivo
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.7z'
            ]
            
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. '
                    'Extensiones permitidas: ' + ', '.join(allowed_extensions)
                )
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Buscar usuario por email para asignar empresa automáticamente
        uploader_email = self.cleaned_data['uploader_email']
        try:
            existing_user = User.objects.get(email=uploader_email)
            # Si el usuario tiene perfil con empresa, usar esa empresa
            if hasattr(existing_user, 'userprofile') and existing_user.userprofile.company:
                instance.company = existing_user.userprofile.company
            else:
                # Si no tiene empresa asignada, dejarlo sin empresa
                instance.company = None
        except User.DoesNotExist:
            # Si no existe el usuario, dejarlo sin empresa
            instance.company = None
        
        # Guardar información del uploader en la descripción si no hay descripción
        uploader_info = f"\nSubido por: {self.cleaned_data['uploader_name']} ({uploader_email})"
        if instance.description:
            instance.description += uploader_info
        else:
            instance.description = f"Archivo subido públicamente.{uploader_info}"
        
        # Marcar como público
        instance.is_public = True
        
        if commit:
            instance.save()
        
        return instance


class RecordingForm(forms.ModelForm):
    """Formulario para grabar audio desde el navegador"""
    
    # Campo oculto para almacenar los datos de audio en base64
    audio_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Recording
        fields = ['title', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la grabación',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la grabación (opcional)'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título de la Grabación',
            'description': 'Descripción',
            'is_public': 'Público',
        }
        help_texts = {
            'is_public': 'Si está marcado, todos los usuarios de tu empresa pueden escuchar esta grabación',
        }
    
    def clean_audio_data(self):
        audio_data = self.cleaned_data.get('audio_data')
        if not audio_data:
            raise forms.ValidationError('Debe grabar audio antes de enviar el formulario.')
        return audio_data


class PublicRecordingForm(forms.ModelForm):
    """Formulario público para grabar audio desde el navegador"""
    
    uploader_name = forms.CharField(
        max_length=100,
        label='Tu Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre',
            'required': True
        })
    )
    uploader_email = forms.EmailField(
        label='Tu Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'required': True
        }),
        help_text='Si ya tienes cuenta en el sistema, se asignará automáticamente a tu empresa'
    )
    
    # Campo oculto para almacenar los datos de audio en base64
    audio_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Recording
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la grabación',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la grabación (opcional)'
            }),
        }
        labels = {
            'title': 'Título de la Grabación',
            'description': 'Descripción',
        }
    
    def clean_audio_data(self):
        audio_data = self.cleaned_data.get('audio_data')
        if not audio_data:
            raise forms.ValidationError('Debe grabar audio antes de enviar el formulario.')
        return audio_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Buscar usuario por email para asignar empresa automáticamente
        uploader_email = self.cleaned_data['uploader_email']
        try:
            existing_user = User.objects.get(email=uploader_email)
            # Si el usuario tiene perfil con empresa, usar esa empresa
            if hasattr(existing_user, 'userprofile') and existing_user.userprofile.company:
                instance.company = existing_user.userprofile.company
            else:
                # Si no tiene empresa asignada, dejarlo sin empresa
                instance.company = None
        except User.DoesNotExist:
            # Si no existe el usuario, dejarlo sin empresa
            instance.company = None
        
        # Guardar información del uploader en la descripción si no hay descripción
        uploader_info = f"\nSubido por: {self.cleaned_data['uploader_name']} ({uploader_email})"
        if instance.description:
            instance.description += uploader_info
        else:
            instance.description = f"Grabación subida públicamente.{uploader_info}"
        
        # Marcar como público
        instance.is_public = True
        
        if commit:
            instance.save()
        
        return instance


class TranscriptionEditForm(forms.ModelForm):
    """Formulario para editar la transcripción de una grabación"""
    
    class Meta:
        model = Recording
        fields = ['transcription_text']
        widgets = {
            'transcription_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'La transcripción aparecerá aquí...',
                'style': 'font-family: monospace; font-size: 14px;'
            }),
        }
        labels = {
            'transcription_text': 'Transcripción',
        }
        help_texts = {
            'transcription_text': 'Puedes editar manualmente la transcripción o regenerarla con IA',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si no hay transcripción, mostrar mensaje informativo
        if self.instance and not self.instance.transcription_text:
            self.fields['transcription_text'].widget.attrs['placeholder'] = 'Aún no hay transcripción disponible. Puedes generar una automáticamente con IA.'


class TranscriptionActionForm(forms.Form):
    """Formulario para acciones de transcripción (generar, regenerar, etc.)"""
    
    ACTION_CHOICES = [
        ('generate', 'Generar transcripción con IA'),
        ('regenerate', 'Regenerar transcripción con IA'),
        ('improve', 'Mejorar transcripción existente'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Acción'
    )
    
    context_hint = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contexto adicional para mejorar la transcripción (opcional)'
        }),
        label='Contexto adicional',
        help_text='Información adicional que puede ayudar a mejorar la transcripción'
    )
    
    def __init__(self, *args, **kwargs):
        self.recording = kwargs.pop('recording', None)
        super().__init__(*args, **kwargs)
        
        # Ajustar opciones según el estado de la transcripción
        if self.recording:
            if not self.recording.transcription_text:
                # Solo permitir generar si no hay transcripción
                self.fields['action'].choices = [('generate', 'Generar transcripción con IA')]
                self.fields['action'].initial = 'generate'
            else:
                # Si ya hay transcripción, permitir regenerar o mejorar
                self.fields['action'].choices = [
                    ('regenerate', 'Regenerar transcripción con IA'),
                    ('improve', 'Mejorar transcripción existente'),
                ]
                self.fields['action'].initial = 'improve'


# ============================================
# FORMULARIOS DE DOCUMENTACIÓN MÚLTIPLE
# ============================================

class MultipleDocumentationForm(forms.ModelForm):
    """Formulario para crear y editar documentaciones múltiples"""
    
    # Campo personalizado para la contraseña que mantenga el valor en edición
    access_password = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña de acceso',
            'maxlength': '100',
            'id': 'access_password_field',
            'type': 'text'  # Usar texto normal para mostrar el valor
        }),
        label='Contraseña de acceso',
        help_text='Contraseña que los usuarios deberán ingresar para acceder'
    )
    
    class Meta:
        model = MultipleDocumentation
        fields = ['title', 'description', 'is_active', 'password_protected', 'access_password']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la documentación múltiple',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de qué contiene esta documentación...',
                'maxlength': '1000'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'password_protected': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'password_protected_checkbox'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción', 
            'is_active': 'Activo',
            'password_protected': 'Protegido con contraseña',
        }
        help_texts = {
            'title': 'Nombre descriptivo para identificar esta documentación',
            'description': 'Descripción opcional de qué contiene esta documentación',
            'is_active': 'Si está activo, se puede acceder públicamente',
            'password_protected': 'Si está marcado, se requerirá una contraseña para acceder',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando una instancia existente, establecer el valor de la contraseña
        if self.instance and self.instance.pk:
            # Solo usar initial, que es la forma correcta en Django
            if hasattr(self.instance, 'access_password') and self.instance.access_password:
                self.fields['access_password'].initial = self.instance.access_password
    
    def clean(self):
        cleaned_data = super().clean()
        password_protected = cleaned_data.get('password_protected')
        access_password = cleaned_data.get('access_password')
        
        # Si está protegido por contraseña pero no se proporciona una contraseña
        if password_protected and not access_password:
            # Si estamos editando y la instancia ya tiene contraseña, mantenerla
            if self.instance and self.instance.pk and self.instance.access_password:
                cleaned_data['access_password'] = self.instance.access_password
            else:
                # Si es nueva documentación, requerir contraseña
                raise forms.ValidationError('Debe proporcionar una contraseña cuando la documentación está protegida.')
        
        # Si no está protegido por contraseña, limpiar el campo
        if not password_protected:
            cleaned_data['access_password'] = ''
        
        return cleaned_data


class DocumentationPasswordForm(forms.Form):
    """Formulario para solicitar contraseña de acceso a documentación"""
    
    password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese la contraseña',
            'autofocus': True,
            'autocomplete': 'off'
        }),
        label='Contraseña de acceso'
    )
    
    def __init__(self, *args, **kwargs):
        self.documentation = kwargs.pop('documentation', None)
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if self.documentation and password != self.documentation.access_password:
            raise forms.ValidationError('Contraseña incorrecta.')
        
        return password


class TaskScheduleForm(forms.ModelForm):
    """Formulario para crear y editar cronogramas de tareas"""
    
    class Meta:
        model = TaskSchedule
        fields = ['title', 'description', 'company', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del cronograma'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del cronograma'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'company': 'Empresa',
            'is_public': 'Hacer público',
        }
    
    def save(self, commit=True):
        """Guarda el cronograma con fechas por defecto si no existen tareas"""
        instance = super().save(commit=False)
        
        # Si es un nuevo cronograma, establecer fechas por defecto
        if not instance.pk:
            from django.utils import timezone
            today = timezone.now().date()
            instance.start_date = today
            instance.end_date = today
        
        if commit:
            instance.save()
            # Actualizar fechas automáticamente si hay tareas
            instance.update_auto_dates()
        
        return instance


class ScheduleTaskForm(forms.ModelForm):
    """Formulario para crear y editar tareas del cronograma"""
    
    class Meta:
        model = ScheduleTask
        fields = [
            'title', 'description', 'start_date', 'end_date', 
            'priority', 'assigned_to', 'is_completed', 'dependencies'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la tarea'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la tarea'
            }),
            'start_date': DateInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'end_date': DateInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'dependencies': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'start_date': 'Fecha de Inicio',
            'end_date': 'Fecha de Fin',
            'priority': 'Prioridad',
            'assigned_to': 'Asignado a',
            'is_completed': 'Completada',
            'dependencies': 'Dependencias',
        }
    
    def __init__(self, *args, **kwargs):
        schedule = kwargs.pop('schedule', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar dependencias para mostrar solo tareas del mismo cronograma
        if schedule:
            self.fields['dependencies'].queryset = ScheduleTask.objects.filter(
                schedule=schedule
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
        else:
            self.fields['dependencies'].queryset = ScheduleTask.objects.none()
        
        # Filtrar usuarios activos
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_to'].required = False
        
        # Asegurar que las fechas se formateen correctamente para input type="date"
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                # Formatear fecha en formato ISO (YYYY-MM-DD) para input type="date"
                self.fields['start_date'].initial = self.instance.start_date.strftime('%Y-%m-%d')
                self.fields['start_date'].widget.attrs['value'] = self.instance.start_date.strftime('%Y-%m-%d')
            if self.instance.end_date:
                # Formatear fecha en formato ISO (YYYY-MM-DD) para input type="date"
                self.fields['end_date'].initial = self.instance.end_date.strftime('%Y-%m-%d')
                self.fields['end_date'].widget.attrs['value'] = self.instance.end_date.strftime('%Y-%m-%d')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError({
                'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Establecer progreso automáticamente según el estado
        if instance.is_completed:
            instance.progress_percentage = 100
        else:
            instance.progress_percentage = 0
        
        if commit:
            instance.save()
        
        return instance


class ScheduleCommentForm(forms.ModelForm):
    """Formulario para comentarios en tareas"""
    
    class Meta:
        model = ScheduleComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe tu comentario aquí...'
            }),
        }
        labels = {
            'comment': 'Comentario',
        }


class FinancialActionForm(forms.ModelForm):
    """Formulario para crear y editar acciones financieras"""
    
    class Meta:
        model = FinancialAction
        fields = ['symbol', 'name', 'current_price', 'previous_price', 'currency', 'is_active', 'order']
        widgets = {
            'symbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: EUR/USD, AAPL, BTC/USD'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa;'
            }),
            'previous_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa;'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                ('USD', 'USD - Dólar Estadounidense'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - Libra Esterlina'),
                ('JPY', 'JPY - Yen Japonés'),
                ('CAD', 'CAD - Dólar Canadiense'),
                ('CHF', 'CHF - Franco Suizo'),
                ('AUD', 'AUD - Dólar Australiano'),
            ]),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }
        labels = {
            'symbol': 'Símbolo',
            'name': 'Nombre',
            'current_price': 'Precio Actual',
            'previous_price': 'Precio Anterior',
            'currency': 'Moneda',
            'is_active': 'Activa',
            'order': 'Orden',
        }
        help_texts = {
            'symbol': 'Símbolo de la acción (se convertirá a mayúsculas automáticamente)',
            'current_price': 'Se actualiza automáticamente desde APIs externas',
            'previous_price': 'Se actualiza automáticamente desde APIs externas',
            'order': 'Orden de aparición en el ticker (menor número = primera posición)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si es una instancia existente, hacer los campos de precio de solo lectura
        if self.instance and self.instance.pk:
            self.fields['current_price'].widget.attrs.update({
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa; cursor: not-allowed;'
            })
            self.fields['previous_price'].widget.attrs.update({
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa; cursor: not-allowed;'
            })
        
        # Agregar clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if field_name not in ['is_active']:
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})
    
    def clean_symbol(self):
        """Convertir símbolo a mayúsculas"""
        symbol = self.cleaned_data.get('symbol', '')
        return symbol.upper()


class ProductForm(forms.ModelForm):
    """
    Formulario para crear y editar productos
    """
    class Meta:
        from .models import Product
        model = Product
        fields = ['name', 'price', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del producto'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre del Producto',
            'price': 'Precio',
            'description': 'Descripción',
            'is_active': 'Producto Activo',
        }
        help_texts = {
            'name': 'Nombre identificativo del producto',
            'price': 'Precio del producto en la moneda base',
            'description': 'Descripción completa del producto, características, beneficios, etc.',
            'is_active': 'Si está marcado, el producto estará disponible para su uso',
        }
    
    def __init__(self, *args, **kwargs):
        # Importar el modelo aquí para evitar importaciones circulares
        from .models import Product, SystemConfiguration
        self._meta.model = Product
        
        super().__init__(*args, **kwargs)
        
        # Obtener la moneda configurada en el sistema
        config = SystemConfiguration.objects.first()
        currency_symbol = '€'  # Por defecto
        currency_code = 'EUR'
        
        if config:
            currency_symbols = {
                'EUR': '€',
                'USD': '$',
                'GBP': '£',
                'JPY': '¥',
                'CAD': 'C$',
                'AUD': 'A$',
                'CHF': 'CHF',
                'CNY': '¥',
                'MXN': '$',
                'COP': '$',
            }
            currency_symbol = currency_symbols.get(config.default_currency, '€')
            currency_code = config.default_currency
        
        # Actualizar el placeholder del campo precio con la moneda
        self.fields['price'].widget.attrs['placeholder'] = f'0.00 ({currency_symbol})'
        self.fields['price'].help_text = f'Precio del producto en {currency_code}'
        
        # Agregar clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if field_name not in ['is_active']:
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})
    
    def clean_price(self):
        """Validar que el precio sea positivo"""
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('El precio no puede ser negativo')
        return price


# ===== FORMULARIOS PARA ASISTENCIA DE CLIENTE =====

class ClientProjectAccessForm(forms.ModelForm):
    """Formulario para configurar el acceso público a proyectos para clientes"""
    
    allowed_categories = forms.MultipleChoiceField(
        choices=[
            ('capacitacion', 'Capacitación'),
            ('pruebas', 'Pruebas'),
            ('uso', 'Uso'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Categorías Permitidas',
        help_text='Seleccione las categorías que los clientes podrán elegir'
    )
    
    class Meta:
        from .models import ClientProjectAccess
        model = ClientProjectAccess
        fields = [
            'project', 'is_active', 'max_entries_per_day', 
            'requires_phone', 'allowed_categories', 'instructions'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'instructions': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'max_entries_per_day': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar estilos de los campos
        for field_name, field in self.fields.items():
            if field_name not in ['is_active', 'requires_phone', 'allowed_categories']:
                if hasattr(field.widget, 'attrs'):
                    if 'class' not in field.widget.attrs:
                        field.widget.attrs['class'] = 'form-control'
        
        # Configurar checkboxes
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['requires_phone'].widget.attrs.update({'class': 'form-check-input'})
        
        # Configurar placeholder e instrucciones
        self.fields['instructions'].widget.attrs.update({
            'placeholder': 'Instrucciones especiales para los clientes...'
        })
        
        # Filtrar solo proyectos activos
        self.fields['project'].queryset = self.fields['project'].queryset.filter(is_active=True)
        
        # Si es edición, cargar las categorías seleccionadas
        if self.instance and self.instance.pk and self.instance.allowed_categories:
            self.fields['allowed_categories'].initial = self.instance.allowed_categories
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Guardar las categorías seleccionadas
        if self.cleaned_data['allowed_categories']:
            instance.allowed_categories = list(self.cleaned_data['allowed_categories'])
        else:
            instance.allowed_categories = ['capacitacion', 'pruebas', 'uso']  # default
        
        if commit:
            instance.save()
        return instance


class ClientTimeEntryForm(forms.ModelForm):
    """Formulario público para que los clientes registren horas"""
    
    entry_date = forms.DateField(
        widget=DateInput(attrs={'class': 'form-control'}),
        label='Fecha de las Horas',
        help_text='Fecha cuando realizó el trabajo'
    )
    
    class Meta:
        from .models import ClientTimeEntry
        model = ClientTimeEntry
        fields = ['client_name', 'client_email', 'client_phone', 'hours', 'category', 'description', 'entry_date']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Juan Pérez'
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'su.email@ejemplo.com'
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 234 567 8900'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.25',
                'max': '24',
                'step': '0.25',
                'placeholder': '2.5'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional del trabajo realizado...'
            }),
        }
    
    def __init__(self, *args, access=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.access = access
        
        # Si se requiere teléfono, hacerlo obligatorio
        if access and access.requires_phone:
            self.fields['client_phone'].required = True
        else:
            self.fields['client_phone'].required = False
        
        # Filtrar categorías según la configuración del acceso
        if access and access.allowed_categories:
            choices = [(cat, dict(self.fields['category'].choices).get(cat, cat.title())) 
                      for cat in access.allowed_categories]
            self.fields['category'].choices = choices
        
        # Configurar fecha por defecto (hoy)
        from django.utils import timezone
        self.fields['entry_date'].initial = timezone.now().date()
        
        # Agregar clases para responsive design
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' mb-2'})
    
    def clean_hours(self):
        """Validar que las horas sean válidas"""
        hours = self.cleaned_data.get('hours')
        if hours is not None:
            if hours <= 0:
                raise forms.ValidationError('Las horas deben ser mayor a 0')
            if hours > 24:
                raise forms.ValidationError('No puede registrar más de 24 horas por día')
        return hours
    
    def clean_entry_date(self):
        """Validar que la fecha no sea futura ni muy antigua"""
        from django.utils import timezone
        from datetime import timedelta
        
        entry_date = self.cleaned_data.get('entry_date')
        if entry_date:
            today = timezone.now().date()
            if entry_date > today:
                raise forms.ValidationError('No puede registrar horas para una fecha futura')
            
            # No permitir fechas más antiguas que 30 días
            thirty_days_ago = today - timedelta(days=30)
            if entry_date < thirty_days_ago:
                raise forms.ValidationError('No puede registrar horas para fechas anteriores a 30 días')
        
        return entry_date


class ProductSetForm(forms.ModelForm):
    """Formulario para conjuntos de productos"""
    
    class Meta:
        model = ProductSet
        fields = ['title', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Productos de Software 2024'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el conjunto de productos...'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Título del Conjunto',
            'description': 'Descripción',
            'is_public': 'Hacer público'
        }
        help_texts = {
            'title': 'Nombre descriptivo del conjunto de productos',
            'description': 'Descripción detallada del conjunto',
            'is_public': 'Si está marcado, los clientes podrán ver este conjunto'
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('El título debe tener al menos 5 caracteres')
        return title


class ProductItemForm(forms.ModelForm):
    """Formulario para productos individuales"""
    
    class Meta:
        model = ProductItem
        fields = ['name', 'description', 'price', 'video_link', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sistema de Gestión de Inventario'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe las características del producto...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'video_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            })
        }
        labels = {
            'name': 'Nombre del Producto',
            'description': 'Descripción',
            'price': 'Precio',
            'video_link': 'Link del Video',
            'order': 'Orden de Aparición'
        }
        help_texts = {
            'name': 'Nombre descriptivo del producto',
            'description': 'Descripción detallada del producto',
            'price': 'Precio del producto individual',
            'video_link': 'URL del video demostrativo (opcional)',
            'order': 'Número para ordenar la lista (menor número aparece primero)'
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres')
        return name
    
    def clean_video_link(self):
        video_link = self.cleaned_data.get('video_link')
        if video_link:
            # Validar que sea una URL válida para videos
            valid_domains = ['youtube.com', 'youtu.be', 'vimeo.com', 'drive.google.com']
            if not any(domain in video_link.lower() for domain in valid_domains):
                raise forms.ValidationError('Por favor, use una URL válida de YouTube, Vimeo o Google Drive')
        return video_link


# Formset para manejar múltiples productos
ProductItemFormSet = forms.inlineformset_factory(
    ProductSet,
    ProductItem,
    form=ProductItemForm,
    extra=0,  # No mostrar formularios extra por defecto
    can_delete=True,
    min_num=0,
    validate_min=False
)


class PrecotizadorForm(forms.ModelForm):
    """Formulario para crear/editar precotizadores"""
    
    class Meta:
        model = Precotizador
        fields = ['title', 'client_description', 'hourly_rate']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Desarrollos de Software para PyMEs'
            }),
            'client_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el tipo de cliente, sector, necesidades típicas...'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
        }
        labels = {
            'title': 'Título del Precotizador',
            'client_description': 'Descripción del Cliente',
            'hourly_rate': 'Precio por Hora'
        }
        help_texts = {
            'title': 'Nombre descriptivo del precotizador',
            'client_description': 'Descripción detallada del tipo de cliente y sus necesidades',
            'hourly_rate': 'Tu tarifa por hora para este tipo de trabajo'
        }


class PrecotizadorExampleForm(forms.ModelForm):
    """Formulario para ejemplos de casos del precotizador"""
    
    class Meta:
        model = PrecotizadorExample
        fields = ['description', 'estimated_hours', 'order']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Reporte en Excel de 10 columnas con gráficos'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.25',
                'min': '0'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }
        labels = {
            'description': 'Descripción del Caso',
            'estimated_hours': 'Horas Estimadas',
            'order': 'Orden'
        }
        help_texts = {
            'description': 'Descripción detallada del trabajo a realizar',
            'estimated_hours': 'Número de horas estimadas para completar el trabajo',
            'order': 'Orden de aparición en la lista'
        }


class PrecotizadorQuoteForm(forms.ModelForm):
    """Formulario para generar cotizaciones con IA"""
    
    class Meta:
        model = PrecotizadorQuote
        fields = ['client_request']
        widgets = {
            'client_request': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el trabajo que necesita el cliente...'
            })
        }
        labels = {
            'client_request': 'Solicitud del Cliente'
        }
        help_texts = {
            'client_request': 'Descripción detallada del trabajo solicitado por el cliente'
        }


# Formset para manejar múltiples ejemplos de casos
PrecotizadorExampleFormSet = forms.inlineformset_factory(
    Precotizador,
    PrecotizadorExample,
    form=PrecotizadorExampleForm,
    extra=10,  # Exactamente 10 casos como solicitado
    max_num=10,
    min_num=10,
    can_delete=False,
    validate_min=True,
    validate_max=True
)



# ============= FORMULARIOS PARA DOCUMENTACIONES DE EMPRESAS =============

class CompanyDocumentationForm(forms.ModelForm):
    """Formulario para crear/editar documentaciones de empresas"""
    
    class Meta:
        model = CompanyDocumentation
        fields = ['title', 'description', 'company', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la documentación'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción opcional de la documentación'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'company': 'Empresa',
            'is_public': 'Hacer público'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar empresas según el usuario
            if user.is_superuser or user.groups.filter(name='Administradores').exists():
                # Administradores ven todas las empresas
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
            else:
                # Otros usuarios solo ven su empresa
                try:
                    user_company = user.profile.company
                    if user_company:
                        self.fields['company'].queryset = Company.objects.filter(id=user_company.id)
                    else:
                        self.fields['company'].queryset = Company.objects.none()
                except:
                    self.fields['company'].queryset = Company.objects.none()


class CompanyDocumentationURLForm(forms.ModelForm):
    """Formulario para crear/editar URLs de documentaciones"""
    
    class Meta:
        model = CompanyDocumentationURL
        fields = ['title', 'url', 'description', 'username', 'password', 'notes', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del enlace'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del enlace'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuario (opcional)'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña (opcional)',
                'required': False
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas adicionales'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }
        labels = {
            'title': 'Título del enlace',
            'url': 'URL',
            'description': 'Descripción',
            'username': 'Usuario (opcional)',
            'password': 'Contraseña (opcional)',
            'notes': 'Notas adicionales',
            'is_active': 'Está activo',
            'order': 'Orden'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer los campos username y password opcionales
        self.fields['username'].required = False
        self.fields['password'].required = False
        self.fields['description'].required = False
        self.fields['notes'].required = False


# Formset para manejar múltiples URLs
CompanyDocumentationURLFormSet = forms.inlineformset_factory(
    CompanyDocumentation,
    CompanyDocumentationURL,
    form=CompanyDocumentationURLForm,
    extra=3,
    can_delete=True
)


class TermsOfUseForm(forms.ModelForm):
    """Formulario para crear y editar Condiciones de Uso"""
    
    class Meta:
        model = TermsOfUse
        fields = ['title', 'content', 'effective_date', 'version', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de las condiciones de uso'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Contenido completo de las condiciones de uso...'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: v1.0, v2.0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Título',
            'content': 'Contenido',
            'effective_date': 'Fecha de vigencia',
            'version': 'Versión',
            'is_active': 'Está activo'
        }
        help_texts = {
            'is_active': 'Solo puede haber una condición de uso activa a la vez'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['version'].required = False


class ContactGeneratorForm(forms.ModelForm):
    """Formulario para crear y editar generadores de contactos"""
    
    class Meta:
        model = ContactGenerator
        fields = [
            'title', 'description', 'company', 
            'collect_phone', 'collect_company', 'collect_position', 'collect_notes',
            'welcome_message', 'success_message', 'background_color'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Formulario de Contacto Principal'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del generador de contactos'
            }),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'collect_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collect_company': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collect_position': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collect_notes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'welcome_message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'success_message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'background_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar empresas según el usuario
        if user:
            if user.is_superuser:
                self.fields['company'].queryset = Company.objects.all()
            else:
                # Obtener las empresas del usuario
                user_companies = []
                if hasattr(user, 'company'):
                    user_companies.append(user.company.id)
                if hasattr(user, 'additional_companies'):
                    user_companies.extend(user.additional_companies.values_list('id', flat=True))
                
                self.fields['company'].queryset = Company.objects.filter(id__in=user_companies)


class PublicContactForm(forms.ModelForm):
    """Formulario público para capturar contactos"""
    
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'position', 'company', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Tu nombre completo',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'tu@email.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Tu número de teléfono'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Tu cargo o posición'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre de tu empresa (donde trabajas)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comentarios adicionales (opcional)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        generator = kwargs.pop('generator', None)
        super().__init__(*args, **kwargs)
        
        # Configurar campos según la configuración del generador
        if generator:
            # Si no debe recopilar teléfono, ocultar el campo
            if not generator.collect_phone:
                self.fields.pop('phone')
            
            # Si no debe recopilar empresa, ocultar el campo
            if not generator.collect_company:
                self.fields.pop('company')
            
            # Si no debe recopilar cargo, ocultar el campo
            if not generator.collect_position:
                self.fields.pop('position')
            
            # Si no debe recopilar notas, ocultar el campo
            if not generator.collect_notes:
                self.fields.pop('notes')


class CompanyRequestGeneratorForm(forms.ModelForm):
    """Formulario para crear y editar generadores de Solicitudes de Empresas"""

    class Meta:
        model = CompanyRequestGenerator
        fields = [
            'title', 'description', 'company',
            'sequence_prefix', 'next_sequence',
            'collect_date', 'collect_text', 'collect_url',
            'welcome_message', 'success_message'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'sequence_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'next_sequence': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'collect_date': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collect_text': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collect_url': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'success_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser:
                self.fields['company'].queryset = Company.objects.all()
            else:
                user_companies = []
                if hasattr(user, 'company'):
                    user_companies.append(user.company.id)
                if hasattr(user, 'additional_companies'):
                    user_companies.extend(user.additional_companies.values_list('id', flat=True))
                self.fields['company'].queryset = Company.objects.filter(id__in=user_companies)


class PublicCompanyRequestForm(forms.ModelForm):
    """Formulario público para enviar una CompanyRequest"""

    class Meta:
        model = CompanyRequest
        fields = ['text', 'url']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe tu solicitud...'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enlace relacionado (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        generator = kwargs.pop('generator', None)
        super().__init__(*args, **kwargs)
        # Ajustar campos según el generador
        if generator:
            if not generator.collect_text:
                self.fields.pop('text')
            if not generator.collect_url:
                self.fields.pop('url')


# ============= FORMULARIOS PARA SISTEMA DE FORMULARIOS =============

class FormForm(forms.ModelForm):
    """Formulario para crear/editar formularios"""

    class Meta:
        model = Form
        fields = ['title', 'description', 'theme', 'company', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.is_staff or user.is_superuser:
                self.fields['company'].queryset = Company.objects.all()
            else:
                user_companies = []
                if hasattr(user, 'company'):
                    user_companies.append(user.company.id)
                if hasattr(user, 'additional_companies'):
                    user_companies.extend(user.additional_companies.values_list('id', flat=True))
                self.fields['company'].queryset = Company.objects.filter(id__in=user_companies)


class FormQuestionForm(forms.ModelForm):
    """Formulario para crear/editar preguntas"""

    class Meta:
        model = FormQuestion
        fields = ['question_text', 'question_type', 'is_required', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class FormQuestionOptionForm(forms.ModelForm):
    """Formulario para crear/editar opciones de preguntas"""

    class Meta:
        model = FormQuestionOption
        fields = ['option_text', 'score', 'order']
        widgets = {
            'option_text': forms.TextInput(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class PublicFormResponseForm(forms.Form):
    """Formulario público para responder a un formulario"""
    
    respondent_name = forms.CharField(
        max_length=100,
        required=False,
        label='Nombre completo',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre (opcional)'})
    )
    respondent_email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Tu email (opcional)'})
    )

    def __init__(self, *args, **kwargs):
        form_obj = kwargs.pop('form', None)
        super().__init__(*args, **kwargs)

        if form_obj:
            for question in form_obj.questions.all():
                field_name = f'question_{question.id}'
                if question.question_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        label=question.question_text,
                        required=question.is_required,
                        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                    )
                elif question.question_type == 'number':
                    self.fields[field_name] = forms.DecimalField(
                        label=question.question_text,
                        required=question.is_required,
                        widget=forms.NumberInput(attrs={'class': 'form-control'})
                    )
                elif question.question_type == 'multiple_choice':
                    choices = [(option.id, option.option_text) for option in question.options.all()]
                    self.fields[field_name] = forms.ChoiceField(
                        label=question.question_text,
                        required=question.is_required,
                        choices=choices,
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                    )


class EmployeeRequestForm(forms.ModelForm):
    """Formulario para crear y editar solicitudes de empleados"""
    
    class Meta:
        model = EmployeeRequest
        fields = ['title', 'text', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la solicitud',
                'maxlength': '200'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Descripción detallada de la solicitud...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'text': 'Descripción',
            'status': 'Estado',
        }
        help_texts = {
            'title': 'Título descriptivo de la solicitud',
            'text': 'Describe detalladamente la solicitud del empleado',
            'status': 'Estado actual de la solicitud',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si es un usuario que no es agente/admin, solo puede crear borradores
        if user and not (user.is_staff or user.groups.filter(name='Agentes').exists()):
            self.fields['status'].choices = [('draft', 'Borrador')]
            self.fields['status'].initial = 'draft'
        
        # Agregar clases CSS adicionales
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        """Override save para asignar el usuario que crea la solicitud"""
        instance = super().save(commit=False)
        
        # Si es una nueva instancia y no tiene created_by, lo asignamos
        if not instance.pk and hasattr(self, 'user'):
            instance.created_by = self.user
        
        if commit:
            instance.save()
        return instance


class InternalAgreementForm(forms.ModelForm):
    """Formulario para crear y editar acuerdos internos"""
    
    class Meta:
        model = InternalAgreement
        fields = [
            'title', 'description', 'content', 'agreement_type', 'status', 
            'priority', 'effective_date', 'expiration_date', 'department', 
            'applies_to_all', 'signer_1', 'signer_2', 'tags', 'version'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del acuerdo interno',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción breve del acuerdo...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Contenido completo del acuerdo interno...'
            }),
            'agreement_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Departamento al que aplica (opcional)',
                'maxlength': '100'
            }),
            'applies_to_all': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'signer_1': forms.Select(attrs={
                'class': 'form-select'
            }),
            'signer_2': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiquetas separadas por comas',
                'maxlength': '500'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0',
                'maxlength': '20'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'content': 'Contenido',
            'agreement_type': 'Tipo de Acuerdo',
            'status': 'Estado',
            'priority': 'Prioridad',
            'effective_date': 'Fecha de Vigencia',
            'expiration_date': 'Fecha de Expiración',
            'department': 'Departamento',
            'applies_to_all': 'Aplica a todos los empleados',
            'signer_1': 'Primer Firmante',
            'signer_2': 'Segundo Firmante',
            'tags': 'Etiquetas',
            'version': 'Versión',
        }
        help_texts = {
            'title': 'Título descriptivo del acuerdo interno',
            'description': 'Descripción breve del propósito del acuerdo',
            'content': 'Contenido completo del acuerdo interno',
            'effective_date': 'Fecha en que el acuerdo entra en vigencia',
            'expiration_date': 'Fecha en que el acuerdo expira (opcional)',
            'department': 'Departamento específico al que aplica (dejar vacío si aplica a toda la empresa)',
            'applies_to_all': 'Marcar si el acuerdo aplica a todos los empleados de la empresa',
            'signer_1': 'Usuario que debe firmar el acuerdo como primer firmante',
            'signer_2': 'Usuario que debe firmar el acuerdo como segundo firmante',
            'tags': 'Etiquetas para facilitar búsquedas, separadas por comas',
            'version': 'Versión del acuerdo (ej: 1.0, 1.1, 2.0)',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si es un usuario que no es agente/admin, restringir algunos campos
        if self.user and not (self.user.is_staff or self.user.groups.filter(name='Agentes').exists()):
            # Los usuarios normales solo pueden crear borradores
            self.fields['status'].choices = [('draft', 'Borrador')]
            self.fields['status'].initial = 'draft'
        
        # Configuración del campo applies_to_all
        self.fields['applies_to_all'].widget.attrs.update({
            'onchange': 'toggleDepartmentField(this.checked)'
        })
        
        # Configurar queryset para los campos de firmantes
        # Solo mostrar usuarios que son staff o pertenecen al grupo Agentes
        from django.contrib.auth.models import User
        eligible_signers = User.objects.filter(
            models.Q(is_staff=True) | models.Q(groups__name='Agentes')
        ).distinct().order_by('first_name', 'last_name', 'username')
        
        self.fields['signer_1'].queryset = eligible_signers
        self.fields['signer_2'].queryset = eligible_signers
        self.fields['signer_1'].empty_label = "Seleccionar primer firmante..."
        self.fields['signer_2'].empty_label = "Seleccionar segundo firmante..."
        
        # Agregar clases CSS adicionales
        for field_name, field in self.fields.items():
            if field_name == 'applies_to_all':
                continue  # Este ya tiene su clase específica
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        """Validaciones personalizadas"""
        cleaned_data = super().clean()
        effective_date = cleaned_data.get('effective_date')
        expiration_date = cleaned_data.get('expiration_date')
        applies_to_all = cleaned_data.get('applies_to_all')
        department = cleaned_data.get('department')
        
        # Validar fechas
        if effective_date and expiration_date:
            if expiration_date <= effective_date:
                raise forms.ValidationError(
                    'La fecha de expiración debe ser posterior a la fecha de vigencia.'
                )
        
        # Validar departamento vs applies_to_all
        if not applies_to_all and not department:
            raise forms.ValidationError(
                'Si el acuerdo no aplica a todos, debe especificar un departamento.'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save para asignar el usuario creador"""
        instance = super().save(commit=False)
        
        if not instance.pk and self.user:  # Si es nuevo
            instance.created_by = self.user
        
        if commit:
            instance.save()
        return instance


# ==================== FORMULARIOS DE CONTROL DE ACTIVOS ====================

class AssetForm(forms.ModelForm):
    """Formulario para crear y editar activos"""
    
    class Meta:
        model = Asset
        fields = [
            'name', 'manufacturer', 'description', 'serial_number', 
            'status', 'assigned_to', 'purchase_date', 'purchase_price', 
            'warranty_expiry', 'location', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del activo'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fabricante o marca'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del activo'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de serie único'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación física del activo'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)'
            }),
        }
        labels = {
            'name': 'Nombre del Activo',
            'manufacturer': 'Fabricante',
            'description': 'Descripción',
            'serial_number': 'Número de Serie',
            'status': 'Estado',
            'assigned_to': 'Asignado a',
            'purchase_date': 'Fecha de Compra',
            'purchase_price': 'Precio de Compra',
            'warranty_expiry': 'Vencimiento de Garantía',
            'location': 'Ubicación',
            'notes': 'Notas',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios activos que son staff o tienen perfil
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name', 'username')
        
        # Hacer campo assigned_to opcional visualmente
        self.fields['assigned_to'].empty_label = "-- Sin asignar --"
    
    def clean_serial_number(self):
        """Validar que el número de serie sea único"""
        serial_number = self.cleaned_data.get('serial_number')
        if serial_number:
            # Excluir la instancia actual si estamos editando
            queryset = Asset.objects.filter(serial_number=serial_number)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    'Ya existe un activo con este número de serie.'
                )
        return serial_number
    
    def clean(self):
        """Validaciones personalizadas"""
        cleaned_data = super().clean()
        purchase_date = cleaned_data.get('purchase_date')
        warranty_expiry = cleaned_data.get('warranty_expiry')
        
        # Validar fechas
        if purchase_date and warranty_expiry:
            if warranty_expiry < purchase_date:
                raise forms.ValidationError(
                    'La fecha de vencimiento de garantía no puede ser anterior a la fecha de compra.'
                )
        
        return cleaned_data


class AssetAssignForm(forms.ModelForm):
    """Formulario específico para asignar activos a empleados"""
    
    reason = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo de la asignación/reasignación (opcional)'
        }),
        label='Motivo'
    )
    
    class Meta:
        model = Asset
        fields = ['assigned_to']
        widgets = {
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'assigned_to': 'Asignar a Usuario',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios activos
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name', 'username')
        
        # Opción para desasignar
        self.fields['assigned_to'].empty_label = "-- Desasignar activo --"


class AssetFilterForm(forms.Form):
    """Formulario para filtrar activos"""
    
    status = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Asset.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    
    assigned = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('assigned', 'Asignados'),
            ('unassigned', 'Sin asignar')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Asignación'
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, fabricante, serie...'
        }),
        label='Buscar'
    )


# ==========================================
# FORMULARIOS PARA TUTOR IA
# ==========================================

class AITutorForm(forms.ModelForm):
    """Formulario para crear y editar tutores IA"""
    
    class Meta:
        model = AITutor
        fields = [
            'title', 'objective', 'current_state', 'context', 
            'tutor_persona', 'status', 'is_private'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo de tu objetivo'
            }),
            'objective': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe claramente qué quieres lograr...'
            }),
            'current_state': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe dónde estás ahora en relación a tu objetivo...'
            }),
            'context': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Proporciona contexto adicional: experiencia, recursos, limitaciones...'
            }),
            'tutor_persona': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Un experimentado profesor de Django, un mentor senior de desarrollo web...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título del Objetivo',
            'objective': 'Objetivo',
            'current_state': 'Estado Actual',
            'context': 'Contexto',
            'tutor_persona': 'Tipo de Tutor',
            'status': 'Estado',
            'is_private': 'Tutor Privado',
        }
        help_texts = {
            'title': 'Un título claro y descriptivo',
            'objective': 'Sé específico sobre lo que quieres lograr',
            'current_state': 'Honesto assessment de tu situación actual',
            'context': 'Cualquier información relevante para personalizar la ayuda',
            'tutor_persona': 'Define qué tipo de tutor quieres (profesor, mentor, coach, etc.)',
            'is_private': 'Solo tú podrás ver este tutor si está marcado como privado'
        }


class AITutorProgressReportForm(forms.ModelForm):
    """Formulario para reportar progreso al Tutor IA"""
    
    class Meta:
        model = AITutorProgressReport
        fields = ['progress_description', 'challenges']
        widgets = {
            'progress_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe qué has logrado desde tu último reporte...'
            }),
            'challenges': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe los obstáculos o dificultades que has enfrentado (opcional)...'
            }),
        }
        labels = {
            'progress_description': 'Descripción del Avance',
            'challenges': 'Desafíos Encontrados',
        }
        help_texts = {
            'progress_description': 'Sé detallado sobre tus logros y acciones tomadas',
            'challenges': 'Incluye cualquier dificultad para recibir ayuda específica'
        }


class AITutorAttachmentForm(forms.ModelForm):
    """Formulario para subir adjuntos al Tutor IA"""
    
    class Meta:
        model = AITutorAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.xlsx,.xls,.ppt,.pptx'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción opcional del archivo...'
            }),
        }
        labels = {
            'file': 'Archivo',
            'description': 'Descripción',
        }
        help_texts = {
            'file': 'Sube documentos, imágenes o archivos relevantes para obtener recomendaciones',
            'description': 'Explica brevemente qué contiene el archivo'
        }
    
    def clean_file(self):
        """Validar el archivo subido"""
        file = self.cleaned_data.get('file')
        if file:
            # Validar tamaño (máximo 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar tipo de archivo
            allowed_extensions = [
                'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 
                'xlsx', 'xls', 'ppt', 'pptx'
            ]
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'Tipo de archivo no permitido. Tipos permitidos: {", ".join(allowed_extensions)}'
                )
        
        return file


class AITutorFilterForm(forms.Form):
    """Formulario para filtrar tutores IA"""
    
    status = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + AITutor.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    
    visibility = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('private', 'Solo mis tutores'),
            ('public', 'Tutores públicos')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Visibilidad'
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título u objetivo...'
        }),
        label='Buscar'
    )


class ExpenseReportForm(forms.ModelForm):
    """Formulario para crear y editar rendiciones de gastos"""
    
    class Meta:
        model = ExpenseReport
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Gastos viaje de trabajo - Enero 2025'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción general de los gastos...'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'title': 'Título de la rendición',
            'description': 'Descripción',
            'start_date': 'Fecha de inicio',
            'end_date': 'Fecha de fin',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es un nuevo formulario, establecer fechas por defecto
        if not self.instance.pk:
            from datetime import date
            today = date.today()
            self.fields['start_date'].initial = today
            self.fields['end_date'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin.')
        
        return cleaned_data


class ExpenseItemForm(forms.ModelForm):
    """Formulario para crear y editar items de gastos"""
    
    currency = forms.ChoiceField(
        choices=[
            ('USD', 'USD - Dólar estadounidense'),
            ('EUR', 'EUR - Euro'),
            ('CLP', 'CLP - Peso chileno'),
            ('ARS', 'ARS - Peso argentino'),
            ('COP', 'COP - Peso colombiano'),
            ('PEN', 'PEN - Sol peruano'),
            ('MXN', 'MXN - Peso mexicano'),
            ('BRL', 'BRL - Real brasileño'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Moneda',
        required=True
    )
    
    class Meta:
        model = ExpenseItem
        fields = ['date', 'category', 'description', 'amount', 'currency', 'vendor', 'location', 'notes', 'receipt_file', 'is_reimbursable']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Almuerzo con cliente'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'vendor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Restaurante El Buen Sabor'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Santiago, Chile'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas adicionales...'
            }),
            'receipt_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf'
            }),
            'is_reimbursable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'date': 'Fecha del gasto',
            'category': 'Categoría',
            'description': 'Descripción',
            'amount': 'Monto',
            'vendor': 'Proveedor/Comercio',
            'location': 'Ubicación',
            'notes': 'Notas adicionales',
            'receipt_file': 'Comprobante/Recibo',
            'is_reimbursable': 'Reembolsable',
        }
    
    def __init__(self, *args, **kwargs):
        expense_report = kwargs.pop('expense_report', None)
        super().__init__(*args, **kwargs)
        
        # Obtener la moneda por defecto del sistema
        from .models import SystemConfiguration
        try:
            config = SystemConfiguration.objects.first()
            default_currency = config.default_currency if config else 'USD'
        except:
            default_currency = 'USD'
        
        # Establecer la moneda por defecto del sistema para nuevos items
        if not self.instance.pk:
            self.fields['currency'].initial = default_currency
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return amount


class ExpenseCommentForm(forms.ModelForm):
    """Formulario para comentarios en rendiciones"""
    
    class Meta:
        model = ExpenseComment
        fields = ['comment', 'is_internal']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe tu comentario...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'comment': 'Comentario',
            'is_internal': 'Comentario interno (solo administradores)',
        }


class ExpenseReportFilterForm(forms.Form):
    """Formulario para filtrar rendiciones de gastos"""
    
    STATUS_CHOICES = [('', 'Todos los estados')] + ExpenseReport.STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    employee = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Empleado',
        empty_label='Todos los empleados'
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título o descripción...'
        }),
        label='Buscar'
    )


class VideoMeetingForm(forms.ModelForm):
    """Formulario para crear reuniones de video (sin archivos)"""
    
    class Meta:
        model = VideoMeeting
        fields = [
            'title', 'description', 'participants', 'company', 
            'scheduled_date', 'duration_minutes', 'meeting_url'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Reunión de planificación semanal'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción de la reunión, agenda, objetivos...'
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'multiple': True
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '60'
            }),
            'meeting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://zoom.us/j/... o https://meet.google.com/...'
            }),
        }
        labels = {
            'title': 'Título de la reunión',
            'description': 'Descripción',
            'participants': 'Participantes',
            'company': 'Empresa',
            'scheduled_date': 'Fecha y hora programada',
            'duration_minutes': 'Duración (minutos)',
            'meeting_url': 'URL de la reunión',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar participantes por empresa del usuario si no es administrador
        if user and not user.is_superuser:
            from .models import User
            if hasattr(user, 'employee') and user.employee and user.employee.company:
                company_users = User.objects.filter(
                    employee__company=user.employee.company
                ).order_by('first_name', 'last_name', 'username')
                self.fields['participants'].queryset = company_users
            else:
                self.fields['participants'].queryset = User.objects.filter(
                    id=user.id
                )
        
        # Si es un nuevo formulario, establecer algunos valores por defecto
        if not self.instance.pk:
            from datetime import datetime, timedelta
            from .models import Company
            
            # Establecer fecha por defecto (próxima hora)
            next_hour = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            self.fields['scheduled_date'].initial = next_hour.strftime('%Y-%m-%dT%H:%M')
            
            # Duración por defecto
            self.fields['duration_minutes'].initial = 60
            
            # Si el usuario tiene empresa, preseleccionarla
            if user and hasattr(user, 'employee') and user.employee and user.employee.company:
                self.fields['company'].initial = user.employee.company


class VideoMeetingEditForm(forms.ModelForm):
    """Formulario para editar reuniones de video con subida de múltiples archivos"""
    
    # Campo adicional para múltiples archivos (se manejará en la vista)
    recording_files = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.mp4,.avi,.mov,.mp3,.wav,.m4a,.webm',
        }),
        label='Archivos de grabación',
        help_text='Puedes subir múltiples archivos. Formatos: MP4, AVI, MOV, MP3, WAV, M4A, WebM (máx. 500MB c/u)'
    )
    
    class Meta:
        model = VideoMeeting
        fields = [
            'title', 'description', 'participants', 'company', 
            'scheduled_date', 'duration_minutes', 'meeting_url',
            'recording_file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Reunión de planificación semanal'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción de la reunión, agenda, objetivos...'
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'multiple': True
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '60'
            }),
            'meeting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://zoom.us/j/... o https://meet.google.com/...'
            }),
            'recording_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.mp4,.avi,.mov,.mp3,.wav,.m4a,.webm'
            }),
        }
        labels = {
            'title': 'Título de la reunión',
            'description': 'Descripción',
            'participants': 'Participantes',
            'company': 'Empresa',
            'scheduled_date': 'Fecha y hora programada',
            'duration_minutes': 'Duración (minutos)',
            'meeting_url': 'URL de la reunión',
            'recording_file': 'Archivo de grabación principal',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar participantes por empresa del usuario si no es administrador
        if user and not user.is_superuser:
            from .models import User
            if hasattr(user, 'employee') and user.employee and user.employee.company:
                company_users = User.objects.filter(
                    employee__company=user.employee.company
                ).order_by('first_name', 'last_name', 'username')
                self.fields['participants'].queryset = company_users
            else:
                self.fields['participants'].queryset = User.objects.filter(
                    id=user.id
                )
    
    def clean_recording_files(self):
        """Validar múltiples archivos"""
        files = self.files.getlist('recording_files')
        max_size = 500 * 1024 * 1024  # 500MB por archivo
        
        for file in files:
            if file.size > max_size:
                raise forms.ValidationError(
                    f'El archivo "{file.name}" es muy grande ({file.size / (1024*1024):.1f}MB). '
                    f'El tamaño máximo permitido es 500MB por archivo.'
                )
        
        return files


class MeetingTranscriptionForm(forms.ModelForm):
    """Formulario para editar manualmente la transcripción"""
    
    class Meta:
        model = VideoMeeting
        fields = ['transcription_text', 'ai_summary', 'key_points', 'action_items']
        widgets = {
            'transcription_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Transcripción completa de la reunión...'
            }),
            'ai_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Resumen ejecutivo de la reunión...'
            }),
            'key_points': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Puntos clave discutidos:\n- Punto 1\n- Punto 2\n- Punto 3'
            }),
            'action_items': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Elementos de acción:\n- [ ] Acción 1 - Responsable: Nombre\n- [ ] Acción 2 - Responsable: Nombre'
            }),
        }
        labels = {
            'transcription_text': 'Transcripción',
            'ai_summary': 'Resumen',
            'key_points': 'Puntos clave',
            'action_items': 'Elementos de acción',
        }


class MeetingNoteForm(forms.ModelForm):
    """Formulario para agregar notas a reuniones"""
    
    class Meta:
        model = MeetingNote
        fields = ['content', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu nota sobre la reunión...'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'content': 'Contenido de la nota',
            'is_private': 'Nota privada (solo yo puedo verla)',
        }


class MeetingFilterForm(forms.Form):
    """Formulario para filtrar reuniones"""
    
    STATUS_CHOICES = [('', 'Todos los estados')] + VideoMeeting.MEETING_STATUS_CHOICES
    TRANSCRIPTION_STATUS_CHOICES = [('', 'Todos los estados')] + VideoMeeting.TRANSCRIPTION_STATUS_CHOICES
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título o descripción...'
        }),
        label='Buscar'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    
    transcription_status = forms.ChoiceField(
        choices=TRANSCRIPTION_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado de transcripción'
    )
    
    company = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Empresa',
        empty_label='Todas las empresas'
    )
    
    organizer = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Organizador',
        empty_label='Todos los organizadores'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        from .models import Company, User
        
        if user and not user.is_superuser:
            # Filtrar por empresa del usuario
            if hasattr(user, 'employee') and user.employee and user.employee.company:
                self.fields['company'].queryset = Company.objects.filter(
                    id=user.employee.company.id
                )
                company_users = User.objects.filter(
                    employee__company=user.employee.company
                ).order_by('first_name', 'last_name', 'username')
                self.fields['organizer'].queryset = company_users
            else:
                self.fields['company'].queryset = Company.objects.none()
                self.fields['organizer'].queryset = User.objects.filter(id=user.id)
        else:
            # Administradores ven todas las empresas y usuarios
            self.fields['company'].queryset = Company.objects.all().order_by('name')
            self.fields['organizer'].queryset = User.objects.all().order_by(
                'first_name', 'last_name', 'username'
            )


class QuoteGeneratorForm(forms.ModelForm):
    """Formulario para generar citas temáticas con IA"""
    
    class Meta:
        model = QuoteGenerator
        fields = ['title', 'topic']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Citas Motivacionales del Día'
            }),
            'topic': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: "Dame citas que ha dicho Einstein sobre el amor", "Frases motivacionales de líderes empresariales", "Citas sobre el éxito y la perseverancia"',
                'rows': 3
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Campos requeridos
        self.fields['title'].required = True
        self.fields['topic'].required = True


class CountdownTimerForm(forms.ModelForm):
    """Formulario para crear y editar cuentas regresivas"""
    
    class Meta:
        model = CountdownTimer
        fields = ['title', 'description', 'target_date', 'is_active', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lanzamiento del nuevo producto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción opcional del evento...',
                'rows': 3
            }),
            'target_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Campos requeridos
        self.fields['title'].required = True
        self.fields['target_date'].required = True
        
        # Ayuda para los campos
        self.fields['title'].help_text = 'Nombre descriptivo para la cuenta regresiva'
        self.fields['target_date'].help_text = 'Fecha y hora del evento objetivo'
        self.fields['is_active'].help_text = 'Si está activo, la cuenta regresiva será visible'
        self.fields['is_private'].help_text = 'Si está marcada como privada, solo tú podrás verla'


class AbsenceTypeForm(forms.ModelForm):
    """Formulario para crear y editar tipos de ausencias"""
    
    class Meta:
        model = AbsenceType
        fields = ['name', 'description', 'requires_documentation', 'is_paid', 'max_days_per_year', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Vacaciones, Enfermedad, Permiso Personal'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción detallada del tipo de ausencia...',
                'rows': 3
            }),
            'requires_documentation': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_paid': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'max_days_per_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 30 días',
                'min': '1'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campos requeridos
        self.fields['name'].required = True
        
        # Ayuda para los campos
        self.fields['name'].help_text = 'Nombre único para identificar el tipo de ausencia'
        self.fields['description'].help_text = 'Descripción opcional para explicar cuándo usar este tipo'
        self.fields['requires_documentation'].help_text = 'Marcar si requiere documentos de respaldo (certificado médico, etc.)'
        self.fields['is_paid'].help_text = 'Marcar si la ausencia es con goce de sueldo'
        self.fields['max_days_per_year'].help_text = 'Límite anual de días (opcional). Dejar vacío si no tiene límite'
        self.fields['color'].help_text = 'Color para mostrar en calendarios y reportes'
        self.fields['is_active'].help_text = 'Solo los tipos activos estarán disponibles para crear ausencias'


class ProcedureForm(forms.ModelForm):
    """Formulario para crear y editar procedimientos"""
    
    class Meta:
        from .models import Procedure
        model = Procedure
        fields = [
            'title', 'description', 'url', 'attachment', 
            'company', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Proceso de Atención al Cliente'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del procedimiento...'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com (opcional)'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif'
            }),
            'company': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campos requeridos
        self.fields['title'].required = True
        self.fields['attachment'].required = False
        self.fields['company'].required = False
        
        # Ayuda para los campos
        self.fields['title'].help_text = 'Título descriptivo del procedimiento'
        self.fields['description'].help_text = 'Descripción detallada del procedimiento (opcional)'
        self.fields['url'].help_text = 'Enlace externo relacionado (opcional)'
        self.fields['attachment'].help_text = 'Archivo del procedimiento (PDF, DOC, etc.) - Opcional'
        self.fields['company'].help_text = 'Empresa a la que pertenece el procedimiento (opcional)'
        self.fields['is_active'].help_text = 'Solo los procedimientos activos serán visibles'
        
    def clean_attachment(self):
        """Validar el archivo adjunto"""
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Validar tamaño del archivo (máximo 50MB)
            if attachment.size > 50 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 50MB.')
            
            # Validar extensiones permitidas
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', 
                '.png', '.gif'
            ]
            
            file_extension = os.path.splitext(attachment.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'Tipo de archivo no permitido. Extensiones permitidas: {", ".join(allowed_extensions)}'
                )
        
        return attachment


class MonthlyCumplimientoForm(forms.ModelForm):
    """Formulario para crear y editar cumplimientos mensuales"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label="Seleccionar usuario...",
        to_field_name=None  # Usar la pk
    )
    
    class Meta:
        model = MonthlyCumplimiento
        fields = ['name', 'user', 'frequency_type', 'target_days', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejercicio diario, Lectura, Meditación, etc.'
            }),
            'frequency_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'target_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 31
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la meta...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre de la meta',
            'user': 'Usuario',
            'frequency_type': 'Tipo de frecuencia',
            'target_days': 'Días objetivo en el mes',
            'description': 'Descripción',
            'is_active': 'Activo',
        }
        help_texts = {
            'name': 'Nombre descriptivo para la meta de cumplimiento',
            'user': 'Usuario que debe cumplir esta meta',
            'frequency_type': 'Todos los días o un número específico de días',
            'target_days': 'Solo aplica para tipo "específico". Número de días que debe cumplir en el mes',
            'description': 'Información adicional sobre la meta',
            'is_active': 'Desmarcar para desactivar temporalmente esta meta',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si el tipo es 'daily', deshabilitar target_days
        if self.initial.get('frequency_type') == 'daily':
            self.fields['target_days'].widget.attrs['disabled'] = True
    
    def clean_target_days(self):
        """Validar target_days según el tipo de frecuencia"""
        frequency_type = self.cleaned_data.get('frequency_type')
        target_days = self.cleaned_data.get('target_days')
        
        if frequency_type == 'specific':
            if not target_days or target_days < 1:
                raise forms.ValidationError('Debe especificar al menos 1 día objetivo.')
            if target_days > 31:
                raise forms.ValidationError('No puede ser más de 31 días.')
        
        return target_days
    
    class Media:
        js = ('js/monthly_cumplimiento_form.js',)


class DailyCumplimientoForm(forms.ModelForm):
    """Formulario para marcar cumplimiento diario (vista pública móvil)"""
    
    class Meta:
        model = DailyCumplimiento
        fields = ['completed', 'notes']
        widgets = {
            'completed': forms.CheckboxInput(attrs={
                'class': 'form-check-input fs-1',
                'style': 'transform: scale(2);'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas opcionales sobre este día...'
            }),
        }
        labels = {
            'completed': '¿Cumplido hoy?',
            'notes': 'Notas (opcional)',
        }


class QRCodeForm(forms.ModelForm):
    """Formulario para generar códigos QR"""
    
    class Meta:
        model = QRCode
        fields = ['title', 'content', 'description', 'qr_type', 'size']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo del QR'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ingresa aquí el contenido que deseas convertir a QR...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción opcional del código QR'
            }),
            'qr_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'qr_type_select'
            }),
            'size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 128,
                'max': 512,
                'step': 32
            })
        }
        labels = {
            'title': 'Título',
            'content': 'Contenido',
            'description': 'Descripción',
            'qr_type': 'Tipo de QR',
            'size': 'Tamaño (px)'
        }
        help_texts = {
            'content': 'Según el tipo seleccionado, ingresa URL, texto, email, teléfono, etc.',
            'size': 'Tamaño en píxeles del código QR (recomendado: 256)'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.instance.created_by = user
        
        # Personalizar placeholders según el tipo
        self.fields['content'].widget.attrs.update({
            'data-url-placeholder': 'https://ejemplo.com',
            'data-text-placeholder': 'Tu texto aquí...',
            'data-email-placeholder': 'correo@ejemplo.com',
            'data-phone-placeholder': '+123456789',
            'data-sms-placeholder': '+123456789',
            'data-wifi-placeholder': 'WIFI:T:WPA;S:NombreRed;P:contraseña;;',
            'data-vcard-placeholder': 'BEGIN:VCARD\nVERSION:3.0\nFN:Nombre Completo\nORG:Empresa\nTEL:+123456789\nEMAIL:correo@ejemplo.com\nEND:VCARD'
        })

    def clean_content(self):
        content = self.cleaned_data.get('content')
        qr_type = self.cleaned_data.get('qr_type')
        
        if not content:
            raise forms.ValidationError('El contenido es obligatorio.')
        
        # Validaciones específicas por tipo
        if qr_type == 'url':
            if not (content.startswith('http://') or content.startswith('https://')):
                raise forms.ValidationError('La URL debe comenzar con http:// o https://')
        elif qr_type == 'email':
            from django.core.validators import validate_email
            try:
                validate_email(content)
            except forms.ValidationError:
                raise forms.ValidationError('Ingresa un email válido.')
        elif qr_type == 'phone' or qr_type == 'sms':
            if not content.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise forms.ValidationError('Ingresa un número de teléfono válido.')
        
        return content


class ContactCommentForm(forms.ModelForm):
    """Formulario para agregar comentarios a contactos"""
    
    class Meta:
        model = ContactComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario aquí...',
                'required': True
            }),
        }
        labels = {
            'content': 'Comentario'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        contact = kwargs.pop('contact', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.instance.user = user
        if contact:
            self.instance.contact = contact


class ContactAttachmentForm(forms.ModelForm):
    """Formulario para subir adjuntos a contactos"""
    
    class Meta:
        model = ContactAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif,.xls,.xlsx',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción opcional del archivo...'
            }),
        }
        labels = {
            'file': 'Archivo',
            'description': 'Descripción'
        }
        help_texts = {
            'file': 'Tipos permitidos: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, GIF, XLS, XLSX'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        contact = kwargs.pop('contact', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.instance.uploaded_by = user
        if contact:
            self.instance.contact = contact

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validar tamaño del archivo (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10 MB.')
            
            # Validar extensión
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.xls', '.xlsx']
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError('Tipo de archivo no permitido.')
        
        return file

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.file:
            instance.original_filename = instance.file.name
            instance.file_size = instance.file.size
        if commit:
            instance.save()
        return instance


class TicketImportForm(forms.Form):
    """Formulario para importar tickets desde Excel"""
    
    excel_file = forms.FileField(
        label='Archivo Excel',
        help_text='Archivo Excel con columnas: Título, Descripción',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
            'required': True
        })
    )
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        label='Empresa',
        help_text='Empresa a la que se asignarán todos los tickets',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        empty_label='Seleccione una empresa...'
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        label='Categoría',
        help_text='Categoría que se asignará a todos los tickets',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        empty_label='Seleccione una categoría...'
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Baja'),
            ('normal', 'Normal'),
            ('high', 'Alta'),
            ('urgent', 'Urgente')
        ],
        initial='normal',
        label='Prioridad',
        help_text='Prioridad que se asignará a todos los tickets',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            # Validar extensión
            if not file.name.lower().endswith(('.xlsx', '.xls')):
                raise forms.ValidationError('Solo se permiten archivos Excel (.xlsx, .xls)')
            
            # Validar tamaño (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 5 MB.')
        
        return file


class CrmQuestionForm(forms.ModelForm):
    """Formulario para crear y editar preguntas del CRM"""
    
    class Meta:
        model = CrmQuestion
        fields = [
            'company', 'question', 'person_name', 'person_email', 
            'answer'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe la pregunta aquí...',
                'required': True
            }),
            'person_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo de quien pregunta',
                'required': True
            }),
            'person_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
                'required': True
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe la respuesta aquí...',
                'id': 'id_answer'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Guardar el usuario para usarlo en la validación
        self._user = user
        
        # Configurar campos según el rol del usuario
        if user:
            from .utils import is_agent
            if is_agent(user):
                # Los agentes pueden ver todas las empresas
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
            else:
                # Los usuarios normales solo ven su empresa
                try:
                    user_company = user.profile.company
                except:
                    user_company = None
                    
                if user_company:
                    # Establecer la empresa del usuario por defecto
                    self.fields['company'].queryset = Company.objects.filter(id=user_company.id)
                    self.fields['company'].initial = user_company
                    # Hacer que solo aparezca una opción y sea readonly
                    self.fields['company'].widget.attrs.update({
                        'readonly': True,
                        'style': 'background-color: #f8f9fa; cursor: not-allowed;',
                        'onclick': 'return false;',
                        'onkeydown': 'return false;'
                    })
                    # Marcar que es un campo controlado para usuarios no agentes
                    self.fields['company'].help_text = 'Empresa asignada automáticamente'
                else:
                    self.fields['company'].queryset = Company.objects.none()
                
                # Establecer nombre y correo del usuario por defecto para no agentes
                if not self.instance.pk:  # Solo para nuevos registros
                    # Configurar nombre del usuario
                    user_full_name = user.get_full_name() or user.username
                    self.fields['person_name'].initial = user_full_name
                    self.fields['person_name'].widget.attrs.update({
                        'placeholder': f'Propuesto: {user_full_name}'
                    })
                    
                    # Configurar email del usuario
                    if user.email:
                        self.fields['person_email'].initial = user.email
                        self.fields['person_email'].widget.attrs.update({
                            'placeholder': f'Propuesto: {user.email}'
                        })
        
        # Configurar campos opcionales para respuesta
        if 'answer' in self.fields:
            self.fields['answer'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        # La validación de answered_by se maneja automáticamente en la vista
        return cleaned_data
    
    def clean_company(self):
        """Validar que usuarios no agentes no cambien la empresa"""
        company = self.cleaned_data.get('company')
        
        # Si hay un usuario asociado al formulario, validar permisos
        if hasattr(self, '_user'):
            from .utils import is_agent
            user = self._user
            
            if not is_agent(user):
                # Para usuarios no agentes, forzar su empresa
                try:
                    user_company = user.profile.company
                    if user_company:
                        # Siempre retornar la empresa del usuario, sin importar lo que venga en el POST
                        return user_company
                    else:
                        raise forms.ValidationError("No tienes una empresa asignada.")
                except:
                    raise forms.ValidationError("No tienes una empresa asignada.")
        
        return company
        
        return company


class CrmQuestionFilterForm(forms.Form):
    """Formulario para filtrar preguntas del CRM"""
    
    STATUS_CHOICES = [
        ('', 'Todos los estados'),
        ('answered', 'Respondidas'),
        ('pending', 'Pendientes'),
    ]
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        required=False,
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en preguntas, respuestas o nombres...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar empresas según el rol del usuario
        if user:
            from .utils import is_agent
            if is_agent(user):
                # Los agentes pueden ver todas las empresas
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
            else:
                # Los usuarios normales solo ven su empresa
                try:
                    user_company = user.profile.company
                except:
                    user_company = None
                    
                if user_company:
                    self.fields['company'].queryset = Company.objects.filter(id=user_company.id)
                else:
                    self.fields['company'].queryset = Company.objects.none()


class PublicCrmQuestionForm(forms.ModelForm):
    """Formulario público para que los clientes envíen preguntas"""
    
    class Meta:
        model = CrmQuestion
        fields = ['person_name', 'person_email', 'question']
        widgets = {
            'person_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo',
                'required': True
            }),
            'person_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu.email@ejemplo.com',
                'required': True
            }),
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe tu pregunta aquí...',
                'rows': 5,
                'required': True
            }),
        }
        labels = {
            'person_name': 'Tu Nombre',
            'person_email': 'Tu Email',
            'question': 'Tu Pregunta',
        }
        help_texts = {
            'person_name': 'Ingresa tu nombre completo',
            'person_email': 'Ingresa tu email para recibir notificaciones',
            'question': 'Describe tu pregunta de manera clara y detallada',
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Configurar campos obligatorios
        for field_name in ['person_name', 'person_email', 'question']:
            self.fields[field_name].required = True
    
    def clean_person_email(self):
        """Validar el formato del email"""
        email = self.cleaned_data.get('person_email')
        if email:
            # Validación básica adicional si es necesario
            if '@' not in email or '.' not in email.split('@')[-1]:
                raise forms.ValidationError('Ingresa un email válido.')
        return email
    
    def clean_question(self):
        """Validar que la pregunta tenga contenido suficiente"""
        question = self.cleaned_data.get('question', '').strip()
        if len(question) < 10:
            raise forms.ValidationError('La pregunta debe tener al menos 10 caracteres.')
        return question


class SupportMeetingForm(forms.ModelForm):
    """Formulario para crear y editar reuniones de soporte"""
    
    class Meta:
        model = SupportMeeting
        fields = ['company', 'date', 'description']
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'date': DateInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la reunión...',
                'rows': 5,
                'required': True
            }),
        }
        labels = {
            'company': 'Empresa',
            'date': 'Fecha',
            'description': 'Descripción',
        }
        help_texts = {
            'company': 'Selecciona la empresa para la cual es la reunión',
            'date': 'Fecha en que se realizó la reunión',
            'description': 'Descripción de la reunión',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obligatorios
        self.fields['company'].required = True
        self.fields['date'].required = True
        self.fields['description'].required = True
        
        # Ordenar empresas por nombre
        self.fields['company'].queryset = Company.objects.filter(is_active=True).order_by('name')
    
    def clean_description(self):
        """Validar que la descripción tenga contenido suficiente"""
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 10:
            raise forms.ValidationError('La descripción debe tener al menos 10 caracteres.')
        return description


class SupportMeetingPointForm(forms.ModelForm):
    """Formulario para agregar puntos a las reuniones de soporte"""
    
    class Meta:
        model = SupportMeetingPoint
        fields = ['description', 'status', 'is_selected']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe el punto tratado en la reunión...',
                'rows': 3,
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_selected': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'description': 'Descripción del punto',
            'status': 'Estado del punto',
            'is_selected': 'Seleccionar para crear como ticket',
        }
        help_texts = {
            'description': 'Describe detalladamente el punto tratado',
            'status': 'Estado actual del punto en la reunión',
            'is_selected': 'Marca esta casilla si quieres que este punto se convierta en ticket',
        }
    
    def clean_description(self):
        """Validar que la descripción tenga contenido suficiente"""
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 10:
            raise forms.ValidationError('La descripción del punto debe tener al menos 10 caracteres.')
        return description


class ScheduledTaskForm(forms.ModelForm):
    """Formulario para tareas programadas"""
    
    class Meta:
        model = ScheduledTask
        fields = ['name', 'frequency', 'frequency_unit', 'code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo de la tarea'
            }),
            'frequency': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Ejemplo: 10'
            }),
            'frequency_unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'code': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': '''# Ejemplo de código Python:
print("Ejecutando tarea programada...")

# Puedes usar cualquier código Python aquí
# Variables disponibles: timezone, datetime, User, request
# Ejemplo:
current_time = timezone.now()
print(f"Hora actual: {current_time}")

# Ejemplo con base de datos:
# users_count = User.objects.count()
# print(f"Total usuarios: {users_count}")'''
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nombre de la Tarea',
            'frequency': 'Frecuencia',
            'frequency_unit': 'Unidad de Tiempo',
            'code': 'Código Python a Ejecutar',
            'is_active': 'Activar Tarea',
        }
        help_texts = {
            'name': 'Nombre descriptivo para identificar la tarea',
            'frequency': 'Número que indica cada cuántas unidades se ejecuta',
            'frequency_unit': 'Unidad de tiempo (minutos, horas, días, meses)',
            'code': 'Código Python que se ejecutará automáticamente',
            'is_active': 'Marcar para activar la ejecución automática',
        }
    
    def clean_frequency(self):
        frequency = self.cleaned_data.get('frequency')
        if frequency and frequency < 1:
            raise forms.ValidationError('La frecuencia debe ser mayor a 0.')
        return frequency
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code:
            raise forms.ValidationError('El código no puede estar vacío.')
        
        # Validación básica de sintaxis Python
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            raise forms.ValidationError(f'Error de sintaxis en el código: {e}')
        
        return code


class EventForm(forms.ModelForm):
    """Formulario para crear y editar eventos"""
    
    event_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            },
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
        label='Fecha y Hora',
        help_text='Fecha y hora del evento'
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location', 'color', 'is_all_day']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del evento'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del evento...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación del evento'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_all_day': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'location': 'Ubicación',
            'color': 'Color',
            'is_all_day': 'Todo el día',
        }
        help_texts = {
            'title': 'Título del evento',
            'description': 'Descripción detallada del evento',
            'location': 'Lugar donde se realizará el evento',
            'color': 'Color para identificar el evento en el calendario',
            'is_all_day': 'Marcar si el evento dura todo el día',
        }


class TripForm(forms.ModelForm):
    """Formulario para crear y editar viajes"""
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            }
        ),
        label='Fecha de Inicio'
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            }
        ),
        label='Fecha de Fin'
    )
    
    class Meta:
        model = Trip
        fields = ['title', 'description', 'destination', 'start_date', 'end_date', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Viaje a Madrid 2025'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del viaje...'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Madrid, España'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título del Viaje',
            'description': 'Descripción',
            'destination': 'Destino Principal',
            'is_public': 'Hacer público',
        }
        help_texts = {
            'is_public': 'Permitir que otras personas vean este viaje mediante un enlace',
        }


class TripStopForm(forms.ModelForm):
    """Formulario para crear y editar paradas de viaje"""
    
    visit_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            }
        ),
        label='Fecha de Visita'
    )
    
    visit_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={
                'class': 'form-control',
                'type': 'time'
            }
        ),
        label='Hora de Visita'
    )
    
    class Meta:
        model = TripStop
        fields = ['name', 'description', 'address', 'latitude', 'longitude', 
                  'order', 'visit_date', 'visit_time', 'duration_minutes', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Museo del Prado'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción del lugar...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '40.416775'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '-3.703790'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '120'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas adicionales...'
            }),
        }


