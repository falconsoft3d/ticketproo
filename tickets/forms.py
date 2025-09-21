from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import (
    Ticket, TicketAttachment, Category, TicketComment, UserProfile, 
    UserNote, TimeEntry, Project, Company, SystemConfiguration, Document
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
        fields = ['name', 'description', 'color', 'status', 'start_date', 'end_date', 'is_active']
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

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'status', 'company', 'hours']
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
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
            'status': 'Estado',
            'company': 'Empresa',
            'hours': 'Horas estimadas/trabajadas',
        }


class UserTicketForm(forms.ModelForm):
    """Formulario simplificado para usuarios regulares al crear tickets"""
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

class UserTicketEditForm(forms.ModelForm):
    """Formulario para editar tickets por usuarios regulares"""
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
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'company', 'priority', 'status', 'assigned_to', 'hours', 'is_public_shareable']
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
        fields = ['phone', 'bio', 'cargo', 'descripcion_cargo', 'company']
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
        }
        labels = {
            'phone': 'Teléfono',
            'bio': 'Biografía',
            'cargo': 'Cargo',
            'descripcion_cargo': 'Descripción del Cargo',
            'company': 'Empresa',
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
        empty_label="Seleccionar proyecto",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Proyecto',
        help_text='Selecciona el proyecto en el que vas a trabajar'
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
        super().__init__(*args, **kwargs)
        # Asegurar que solo se muestren proyectos activos
        self.fields['project'].queryset = Project.objects.filter(
            is_active=True, 
            status='active'
        ).order_by('name')


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
    """Formulario para editar registros de horario (solo notas)"""
    
    class Meta:
        model = TimeEntry
        fields = ['notas']
        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comentarios sobre la jornada laboral...',
            }),
        }
        labels = {
            'notas': 'Notas de la jornada',
        }
        help_texts = {
            'notas': 'Describe las actividades realizadas, observaciones o comentarios relevantes',
        }
    
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
        fields = ['name', 'description', 'address', 'phone', 'email', 'website', 'color', 'is_active']
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


class SystemConfigurationForm(forms.ModelForm):
    """Formulario para configurar el sistema"""
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'site_name',
            'allow_user_registration',
            'default_ticket_priority'
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
        }
        labels = {
            'site_name': 'Nombre del sitio',
            'allow_user_registration': 'Permitir registro de usuarios',
            'default_ticket_priority': 'Prioridad por defecto de tickets',
        }
        help_texts = {
            'site_name': 'Nombre que aparece en el encabezado del sistema',
            'allow_user_registration': 'Permite que nuevos usuarios se registren en el sistema',
            'default_ticket_priority': 'Prioridad asignada automáticamente a nuevos tickets',
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
