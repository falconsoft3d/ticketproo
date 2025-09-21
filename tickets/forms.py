from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket, TicketAttachment, Category, TicketComment

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


class TicketForm(forms.ModelForm):
    """Formulario básico para crear/editar tickets (usado por agentes)"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Seleccionar categoría"

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'status', 'hours']
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
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'category': 'Categoría',
            'priority': 'Prioridad',
            'status': 'Estado',
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
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'status', 'assigned_to', 'hours', 'is_public_shareable']
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
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')
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
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')
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
