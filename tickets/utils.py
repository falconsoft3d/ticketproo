from django.contrib.auth.models import Group

def is_agent(user):
    """
    Verifica si un usuario pertenece al grupo de Agentes
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Agentes').exists()

def is_regular_user(user):
    """
    Verifica si un usuario pertenece al grupo de Usuarios
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Usuarios').exists()

def get_user_role(user):
    """
    Obtiene el rol del usuario
    """
    if not user.is_authenticated:
        return None
    
    if is_agent(user):
        return 'agent'
    elif is_regular_user(user):
        return 'user'
    else:
        return 'unassigned'

def assign_user_to_group(user, group_name):
    """
    Asigna un usuario a un grupo específico
    """
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return True
    except Group.DoesNotExist:
        return False
