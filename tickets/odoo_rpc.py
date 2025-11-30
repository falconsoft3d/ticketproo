"""
Funciones auxiliares para conectarse a Odoo mediante XML-RPC
"""
import xmlrpc.client
from typing import Optional, Dict, List, Any, Tuple
from django.utils import timezone


def test_connection(connection_obj) -> Tuple[bool, str]:
    """
    Prueba la conexión a Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    try:
        # Construir URL completa
        url = f"{connection_obj.url.rstrip('/')}"
        if connection_obj.port and connection_obj.port != 80:
            url = f"{url}:{connection_obj.port}"
        
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        version = common.version()
        
        if not version:
            return False, "No se pudo obtener la versión de Odoo"
        
        # Intentar autenticar
        uid = common.authenticate(
            connection_obj.database,
            connection_obj.username,
            connection_obj.password,
            {}
        )
        
        if not uid:
            return False, "Error de autenticación: usuario o contraseña incorrectos"
        
        # Actualizar estado de conexión
        connection_obj.connection_status = 'success'
        connection_obj.last_tested_at = timezone.now()
        connection_obj.save()
        
        return True, f"Conexión exitosa. Odoo versión: {version.get('server_version', 'Desconocida')}"
        
    except xmlrpc.client.Fault as e:
        error_msg = f"Error XML-RPC: {str(e)}"
        connection_obj.connection_status = 'failed'
        connection_obj.last_tested_at = timezone.now()
        connection_obj.save()
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Error de conexión: {str(e)}"
        connection_obj.connection_status = 'failed'
        connection_obj.last_tested_at = timezone.now()
        connection_obj.save()
        return False, error_msg


def authenticate(connection_obj) -> Optional[int]:
    """
    Autentica con Odoo y retorna el UID
    
    Args:
        connection_obj: Instancia de OdooConnection
    
    Returns:
        Optional[int]: UID del usuario o None si falla
    """
    try:
        url = f"{connection_obj.url.rstrip('/')}"
        if connection_obj.port and connection_obj.port != 80:
            url = f"{url}:{connection_obj.port}"
        
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(
            connection_obj.database,
            connection_obj.username,
            connection_obj.password,
            {}
        )
        return uid
    except Exception as e:
        print(f"Error de autenticación: {e}")
        return None


def get_models_proxy(connection_obj):
    """
    Obtiene el proxy de models para ejecutar operaciones
    
    Args:
        connection_obj: Instancia de OdooConnection
    
    Returns:
        ServerProxy: Proxy de models o None si falla
    """
    try:
        url = f"{connection_obj.url.rstrip('/')}"
        if connection_obj.port and connection_obj.port != 80:
            url = f"{url}:{connection_obj.port}"
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        return models
    except Exception as e:
        print(f"Error obteniendo proxy: {e}")
        return None


def search_records(connection_obj, model: str, domain: List = None, 
                  limit: int = None, offset: int = 0) -> List[int]:
    """
    Busca registros en Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        model: Nombre del modelo (ej: 'product.product')
        domain: Lista de tuplas con el dominio de búsqueda
        limit: Límite de registros a retornar
        offset: Offset para paginación
    
    Returns:
        List[int]: Lista de IDs de registros encontrados
    """
    if domain is None:
        domain = []
    
    try:
        uid = authenticate(connection_obj)
        if not uid:
            return []
        
        models = get_models_proxy(connection_obj)
        if not models:
            return []
        
        kwargs = {'offset': offset}
        if limit:
            kwargs['limit'] = limit
        
        ids = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            model,
            'search',
            [domain],
            kwargs
        )
        return ids
    except Exception as e:
        print(f"Error buscando registros: {e}")
        return []


def read_records(connection_obj, model: str, ids: List[int], 
                fields: List[str] = None) -> List[Dict]:
    """
    Lee registros de Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        model: Nombre del modelo
        ids: Lista de IDs a leer
        fields: Lista de campos a leer (None = todos)
    
    Returns:
        List[Dict]: Lista de diccionarios con los datos
    """
    try:
        uid = authenticate(connection_obj)
        if not uid:
            return []
        
        models = get_models_proxy(connection_obj)
        if not models:
            return []
        
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        
        records = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            model,
            'read',
            [ids],
            kwargs
        )
        return records
    except Exception as e:
        print(f"Error leyendo registros: {e}")
        return []


def create_record(connection_obj, model: str, values: Dict) -> Optional[int]:
    """
    Crea un registro en Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        model: Nombre del modelo
        values: Diccionario con los valores del registro
    
    Returns:
        Optional[int]: ID del registro creado o None si falla
    """
    try:
        uid = authenticate(connection_obj)
        if not uid:
            return None
        
        models = get_models_proxy(connection_obj)
        if not models:
            return None
        
        record_id = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            model,
            'create',
            [values]
        )
        return record_id
    except Exception as e:
        print(f"Error creando registro: {e}")
        raise Exception(f"Error creando registro: {str(e)}")


def write_record(connection_obj, model: str, record_id: int, 
                values: Dict) -> bool:
    """
    Actualiza un registro en Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        model: Nombre del modelo
        record_id: ID del registro a actualizar
        values: Diccionario con los valores a actualizar
    
    Returns:
        bool: True si fue exitoso, False si falló
    """
    try:
        uid = authenticate(connection_obj)
        if not uid:
            return False
        
        models = get_models_proxy(connection_obj)
        if not models:
            return False
        
        result = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            model,
            'write',
            [[record_id], values]
        )
        return result
    except Exception as e:
        print(f"Error actualizando registro: {e}")
        return False


def get_model_fields(connection_obj, model: str) -> Dict[str, Dict]:
    """
    Obtiene los campos disponibles de un modelo en Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        model: Nombre del modelo
    
    Returns:
        Dict[str, Dict]: Diccionario con información de los campos
    """
    try:
        uid = authenticate(connection_obj)
        if not uid:
            return {}
        
        models = get_models_proxy(connection_obj)
        if not models:
            return {}
        
        fields = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            model,
            'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'required']}
        )
        return fields
    except Exception as e:
        print(f"Error obteniendo campos: {e}")
        return {}


def get_available_models(connection_obj, search_term: str = '') -> List[Dict[str, Any]]:
    """
    Obtiene la lista de modelos disponibles en Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        search_term: Término de búsqueda para filtrar modelos (opcional)
    
    Returns:
        List[Dict]: Lista de diccionarios con información de los modelos
    """
    try:
        uid = authenticate(connection_obj)
        if not uid:
            return []
        
        models = get_models_proxy(connection_obj)
        if not models:
            return []
        
        # Construir el dominio de búsqueda
        domain = [('transient', '=', False)]
        if search_term:
            domain.append(('model', 'ilike', search_term))
        
        # Buscar modelos en ir.model
        model_ids = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            'ir.model',
            'search',
            [domain],
            {'limit': 500, 'order': 'name'}
        )
        
        if not model_ids:
            return []
        
        # Leer información de los modelos
        model_records = models.execute_kw(
            connection_obj.database,
            uid,
            connection_obj.password,
            'ir.model',
            'read',
            [model_ids],
            {'fields': ['model', 'name', 'info', 'state']}
        )
        
        return model_records
        
    except Exception as e:
        print(f"Error obteniendo modelos: {e}")
        return []


def backup_database(connection_obj, master_password: str, backup_format: str = 'zip') -> Tuple[bool, Any, str]:
    """
    Crea un backup de la base de datos de Odoo
    
    Args:
        connection_obj: Instancia de OdooConnection
        master_password: Master password de Odoo para operaciones de base de datos
        backup_format: Formato del backup ('zip' o 'dump')
    
    Returns:
        Tuple[bool, Any, str]: (éxito, datos del backup en base64, mensaje de error)
    """
    import base64
    
    try:
        url = f"{connection_obj.url.rstrip('/')}"
        if connection_obj.port and connection_obj.port != 80:
            url = f"{url}:{connection_obj.port}"
        
        # Conectar al servicio de base de datos
        db = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/db')
        
        # Crear el backup
        backup_data = db.dump(
            master_password,
            connection_obj.database,
            backup_format
        )
        
        if not backup_data:
            return False, None, "No se recibieron datos del backup"
        
        return True, backup_data, "Backup creado exitosamente"
        
    except xmlrpc.client.Fault as e:
        error_msg = str(e.faultString)
        if 'Access Denied' in error_msg or 'AccessDenied' in error_msg:
            return False, None, "Master password incorrecto"
        return False, None, f"Error XML-RPC: {error_msg}"
        
    except Exception as e:
        return False, None, f"Error creando backup: {str(e)}"
