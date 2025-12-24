from rest_framework import serializers
from .models import Ticket, Category, Company, Project
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer para información básica del usuario"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorías"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color']


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para empresas"""
    class Meta:
        model = Company
        fields = ['id', 'name', 'description', 'color']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer para proyectos"""
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'color', 'status']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer para tickets"""
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    
    # IDs para escritura
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    company_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    project_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    assigned_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Campos calculados simples
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'title', 'description', 'priority', 'status', 
            'ticket_type', 'hours', 'is_approved', 'created_at', 'updated_at',
            'created_by', 'assigned_to', 'category', 'company', 'project',
            'category_id', 'company_id', 'project_id', 'assigned_to_id',
            'priority_display', 'status_display', 'type_display'
        ]
        read_only_fields = ['id', 'ticket_number', 'created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Remover los IDs antes de crear
        category_id = validated_data.pop('category_id', None)
        company_id = validated_data.pop('company_id', None)
        project_id = validated_data.pop('project_id', None)
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        
        # Crear el ticket
        ticket = Ticket.objects.create(**validated_data)
        
        # Asignar relaciones
        if category_id:
            try:
                ticket.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        if company_id:
            try:
                ticket.company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        
        if project_id:
            try:
                ticket.project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        
        if assigned_to_id:
            try:
                ticket.assigned_to = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                pass
        
        ticket.save()
        return ticket
    
    def update(self, instance, validated_data):
        # Manejar IDs para actualización
        category_id = validated_data.pop('category_id', None)
        company_id = validated_data.pop('company_id', None)
        project_id = validated_data.pop('project_id', None)
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        
        # Actualizar campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar relaciones
        if category_id is not None:
            if category_id == 0:
                instance.category = None
            else:
                try:
                    instance.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    pass
        
        if company_id is not None:
            if company_id == 0:
                instance.company = None
            else:
                try:
                    instance.company = Company.objects.get(id=company_id)
                except Company.DoesNotExist:
                    pass
        
        if project_id is not None:
            if project_id == 0:
                instance.project = None
            else:
                try:
                    instance.project = Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    pass
        
        if assigned_to_id is not None:
            if assigned_to_id == 0:
                instance.assigned_to = None
            else:
                try:
                    instance.assigned_to = User.objects.get(id=assigned_to_id)
                except User.DoesNotExist:
                    pass
        
        instance.save()
        return instance


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear tickets"""
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'priority', 'ticket_type', 'hours',
            'category_id', 'company_id', 'project_id'
        ]
        extra_kwargs = {
            'category_id': {'source': 'category', 'required': False, 'allow_null': True},
            'company_id': {'source': 'company', 'required': False, 'allow_null': True},
            'project_id': {'source': 'project', 'required': False, 'allow_null': True},
        }


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listas de tickets"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'title', 'priority', 'status', 'ticket_type',
            'created_at', 'updated_at', 'created_by_name', 'assigned_to_name',
            'category_name', 'company_name', 'is_approved', 'priority_display', 'status_display'
        ]
    
    def create(self, validated_data):
        # Remover los IDs antes de crear
        category_id = validated_data.pop('category_id', None)
        company_id = validated_data.pop('company_id', None)
        project_id = validated_data.pop('project_id', None)
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        
        # Crear el ticket
        ticket = Ticket.objects.create(**validated_data)
        
        # Asignar relaciones
        if category_id:
            try:
                ticket.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        if company_id:
            try:
                ticket.company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        
        if project_id:
            try:
                ticket.project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        
        if assigned_to_id:
            try:
                ticket.assigned_to = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                pass
        
        ticket.save()
        return ticket
    
    def update(self, instance, validated_data):
        # Manejar IDs para actualización
        category_id = validated_data.pop('category_id', None)
        company_id = validated_data.pop('company_id', None)
        project_id = validated_data.pop('project_id', None)
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        
        # Actualizar campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar relaciones
        if category_id is not None:
            if category_id == 0:
                instance.category = None
            else:
                try:
                    instance.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    pass
        
        if company_id is not None:
            if company_id == 0:
                instance.company = None
            else:
                try:
                    instance.company = Company.objects.get(id=company_id)
                except Company.DoesNotExist:
                    pass
        
        if project_id is not None:
            if project_id == 0:
                instance.project = None
            else:
                try:
                    instance.project = Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    pass
        
        if assigned_to_id is not None:
            if assigned_to_id == 0:
                instance.assigned_to = None
            else:
                try:
                    instance.assigned_to = User.objects.get(id=assigned_to_id)
                except User.DoesNotExist:
                    pass
        
        instance.save()
        return instance