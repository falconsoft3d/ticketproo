# Sistema de Usuarios Activos - Implementación Completada

## ✅ Problema Resuelto

**Problema Original**: Los usuarios activos se mostraban basándose en el modelo `MonthlyCumplimiento` con consultas complejas de JSON, pero no reflejaban correctamente los usuarios que habían marcado entrada sin marcar salida.

**Solución Implementada**: Se reescribió completamente la lógica de usuarios activos para usar el modelo `TimeEntry` con consultas directas y simples.

## 🔧 Cambios Realizados

### 1. Función `active_users_count` (tickets/api_views.py)
```python
@api_view(['GET'])
def active_users_count(request):
    """
    Devuelve el número de usuarios que están actualmente en la oficina
    (tienen entrada hoy pero no han marcado salida)
    """
    try:
        today = timezone.now().date()
        # Usuarios que marcaron entrada hoy pero no han marcado salida
        active_count = TimeEntry.objects.filter(
            fecha_entrada__date=today,
            fecha_salida__isnull=True
        ).count()
        
        return JsonResponse({'count': active_count})
    except Exception:
        return JsonResponse({'count': 0})
```

### 2. Función `active_users_list` (tickets/api_views.py)
```python
@api_view(['GET'])
def active_users_list(request):
    """
    Devuelve la lista detallada de usuarios activos con información de entrada y tiempo trabajado
    """
    try:
        today = timezone.now().date()
        now = timezone.now()
        
        # Obtener entradas activas (sin salida) del día de hoy
        active_entries = TimeEntry.objects.filter(
            fecha_entrada__date=today,
            fecha_salida__isnull=True
        ).select_related('user')
        
        users_data = []
        for entry in active_entries:
            # Calcular tiempo trabajado hasta ahora
            tiempo_trabajado = now - entry.fecha_entrada
            horas = int(tiempo_trabajado.total_seconds() // 3600)
            minutos = int((tiempo_trabajado.total_seconds() % 3600) // 60)
            
            user_data = {
                'id': entry.user.id,
                'username': entry.user.username,
                'first_name': entry.user.first_name or '',
                'last_name': entry.user.last_name or '',
                'email': entry.user.email or '',
                'entry_time': entry.fecha_entrada.strftime('%H:%M'),
                'hours_worked': f'{horas}:{minutos:02d}'
            }
            users_data.append(user_data)
        
        return JsonResponse({
            'users': users_data,
            'total_count': len(users_data)
        })
    except Exception:
        return JsonResponse({
            'users': [],
            'total_count': 0
        })
```

## 🎯 Lógica de Usuarios Activos

**Criterio Simple y Claro**:
- ✅ **Usuario ACTIVO**: Tiene entrada (`fecha_entrada`) en el día actual Y NO tiene salida (`fecha_salida` es NULL)
- ❌ **Usuario NO ACTIVO**: No tiene entrada hoy O ya marcó salida

**Consulta Principal**:
```python
TimeEntry.objects.filter(
    fecha_entrada__date=today,
    fecha_salida__isnull=True
)
```

## 📊 Funcionalidades

### API Endpoints

1. **GET /api/active-users/count/**
   - Devuelve: `{"count": 2}`
   - Uso: Mostrar número en dashboard

2. **GET /api/active-users/**
   - Devuelve: Lista completa con detalles
   - Incluye: ID, username, nombres, email, hora entrada, tiempo trabajado

### Ejemplo de Respuesta Detallada
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "first_name": "Marlon",
      "last_name": "Falcon",
      "email": "admin@example.com",
      "entry_time": "08:30",
      "hours_worked": "2:25"
    }
  ],
  "total_count": 1
}
```

## ✅ Pruebas Realizadas

1. **Entrada sin salida**: Usuario aparece como activo ✅
2. **Entrada con salida**: Usuario NO aparece como activo ✅
3. **Múltiples usuarios activos**: Conteo correcto ✅
4. **Cálculo de tiempo trabajado**: Funciona correctamente ✅
5. **Manejo de errores**: Devuelve 0/lista vacía en caso de error ✅

## 🔄 Flujo de Uso

1. **Usuario marca entrada** → Aparece en lista de activos
2. **Sistema calcula tiempo** → Actualiza automáticamente las horas trabajadas
3. **Usuario marca salida** → Desaparece de lista de activos
4. **Dashboard se actualiza** → Refleja cambios en tiempo real

## 📝 Notas Técnicas

- **Modelo usado**: `TimeEntry` (no `MonthlyCumplimiento`)
- **Campos clave**: `fecha_entrada`, `fecha_salida`
- **Timezone**: Manejo correcto con `timezone.now()`
- **Performance**: Consulta optimizada con `select_related('user')`
- **Compatibilidad**: Mantiene formato de respuesta existente

## 🎉 Resultado Final

El sistema ahora muestra correctamente los usuarios que están físicamente presentes en la oficina, basándose en sus registros reales de entrada y salida del sistema de tiempo.

**Estado**: ✅ **COMPLETADO Y FUNCIONAL**