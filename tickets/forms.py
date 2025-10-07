from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserProfile, 
    UserNote, TimeEntry, Project, Company, SystemConfiguration, Document, UrlManager, WorkOrder, Task,
    ChatRoom, ChatMessage, Command, ContactFormSubmission, Meeting, MeetingAttendee, MeetingQuestion, OpportunityActivity,
    Course, CourseClass, Contact, BlogCategory, BlogPost, BlogComment
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
        fields = ['title', 'description', 'category', 'priority', 'company']
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
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
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
        fields = ['title', 'description', 'category', 'priority', 'company']
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
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
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
        fields = ['title', 'description', 'category', 'company', 'project', 'priority', 'status', 'assigned_to', 'hours', 'is_public_shareable']
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
            'assigned_to': 'Asignar a',
            'hours': 'Horas estimadas/trabajadas',
            'is_public_shareable': 'Permitir compartir públicamente',
        }

class UserManagementForm(UserCreationForm):
    """Formulario para crear usuarios con selección de rol"""
    
    ROLE_CHOICES = [
        ('Usuarios', 'Usuario Regular'),
        ('Agentes', 'Agente de Soporte'),
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
        ('Usuarios', 'Usuario Regular'),
        ('Agentes', 'Agente de Soporte'),
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
            except UserProfile.DoesNotExist:
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
            
            profile.company = company
            profile.precio_hora = precio_hora
            profile.coste_hora = coste_hora
            profile.cargo = cargo
            profile.descripcion_cargo = descripcion_cargo
            profile.save()
            
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
        fields = ['phone', 'bio', 'cargo', 'descripcion_cargo', 'company', 'enable_public_contact_form']
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
    
    class Meta:
        model = UserNote
        fields = ['title', 'description', 'user', 'tickets', 'is_private']
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
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Título de la Nota',
            'description': 'Descripción',
            'user': 'Usuario Asociado',
            'tickets': 'Tickets Relacionados',
            'is_private': 'Nota Privada (solo visible para agentes)',
        }
        help_texts = {
            'title': 'Breve descripción del motivo de la nota',
            'description': 'Detalle completo de la interacción, observaciones o comentarios internos',
            'user': 'Usuario al que se asocia esta nota',
            'tickets': 'Selecciona los tickets relacionados con esta nota (opcional)',
            'is_private': 'Si está marcada, solo los agentes podrán ver esta nota',
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
    
    class Meta:
        model = TimeEntry
        fields = ['project', 'ticket', 'work_order', 'task', 'notas']
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
    
    def clean_notas(self):
        notas = self.cleaned_data.get('notas')
        if notas:
            notas = notas.strip()
            if len(notas) > 500:
                raise forms.ValidationError('Las notas no pueden exceder 500 caracteres.')
        return notas
    
    def clean_notas(self):
        notas = self.cleaned_data.get('notas')
        if notas:
            notas = notas.strip()
            if len(notas) > 500:
                raise forms.ValidationError('Las notas no pueden exceder 500 caracteres.')
        return notas



class CompanyForm(forms.ModelForm):
    """Formulario para crear y editar empresas"""
    
    class Meta:
        model = Company
        fields = ['name', 'description', 'address', 'phone', 'email', 'website', 'color', 'logo', 'public_token', 'is_active']
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
        }
        labels = {
            'name': 'Nombre de la Empresa',
            'description': 'Descripción',
            'address': 'Dirección',
            'phone': 'Teléfono',
            'email': 'Email de Contacto',
            'website': 'Sitio Web',
            'color': 'Color Identificativo',
            'public_token': 'Token Público',
            'is_active': 'Empresa Activa',
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
            'default_currency'
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
        }
        labels = {
            'site_name': 'Nombre del sitio',
            'allow_user_registration': 'Permitir registro de usuarios',
            'default_ticket_priority': 'Prioridad por defecto de tickets',
            'default_currency': 'Moneda por defecto',
        }
        help_texts = {
            'site_name': 'Nombre que aparece en el encabezado del sistema',
            'allow_user_registration': 'Permite que nuevos usuarios se registren en el sistema',
            'default_ticket_priority': 'Prioridad asignada automáticamente a nuevos tickets',
            'default_currency': 'Moneda utilizada para mostrar valores en el sistema',
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
            'placeholder': 'Ingrese la contraseña'
        }),
        label='Contraseña',
        help_text='La contraseña se almacenará de forma segura y encriptada',
        required=True
    )
    
    class Meta:
        model = UrlManager
        fields = ['title', 'url', 'username', 'password', 'description', 'category', 'is_active']
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
                'placeholder': 'nombre_usuario'
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
        }
        labels = {
            'title': 'Título',
            'url': 'URL',
            'username': 'Usuario',
            'description': 'Descripción',
            'category': 'Categoría',
            'is_active': 'Activo',
        }
        help_texts = {
            'title': 'Nombre descriptivo para identificar esta URL',
            'url': 'Dirección web completa (debe incluir http:// o https://)',
            'username': 'Nombre de usuario para acceder a esta URL',
            'description': 'Información adicional sobre el propósito de esta URL',
            'category': 'Categoría para organizar las URLs',
            'is_active': 'Desmarcar si la URL ya no está en uso',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance_pk = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
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
        username = self.cleaned_data.get('username', '').strip()
        
        if not username:
            raise forms.ValidationError('El nombre de usuario es requerido.')
        
        return username
    
    def clean_password(self):
        """Validar la contraseña"""
        password = self.cleaned_data.get('password', '')
        
        # Si estamos creando un nuevo registro, la contraseña es obligatoria
        if not self.instance_pk or not hasattr(self.instance_pk, 'pk'):
            if not password:
                raise forms.ValidationError('La contraseña es requerida.')
        
        # Si hay contraseña, validar longitud mínima
        if password and len(password) < 3:
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
        fields = ['title', 'description', 'company', 'duration', 'location', 'status', 'allow_questions', 'require_email']
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
            'company': forms.Select(attrs={
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
        
        # Configurar choices de empresa
        from .models import Company
        companies = Company.objects.all().order_by('name')
        company_choices = [('', '---------')] + [(c.id, c.name) for c in companies]
        self.fields['company'].choices = company_choices
        self.fields['company'].required = False
        
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
            'name', 'email', 'phone', 'position', 'company', 
            'status', 'source', 'notes', 'contact_date'
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
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer valores por defecto para nuevos contactos
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['contact_date'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')
        
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
