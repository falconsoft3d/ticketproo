# Integración de WhatsApp - Sistema de Respuestas Automatizadas

## 📋 Descripción

Esta integración permite configurar respuestas automáticas en WhatsApp basadas en palabras clave. El sistema detecta mensajes entrantes y responde automáticamente según las reglas configuradas.

## 🚀 Características Implementadas

### 1. **Dashboard Principal** (`/whatsapp/`)
- Vista general del estado de conexión
- Estadísticas de mensajes (total, auto-respuestas, palabras clave)
- Lista de palabras clave activas
- Historial de mensajes recientes
- Botones para conectar/desconectar WhatsApp

### 2. **Gestión de Palabras Clave**
- **Crear palabra clave**: Define palabras o frases que activarán respuestas
- **Editar palabra clave**: Modifica palabras y respuestas existentes
- **Eliminar palabra clave**: Quita palabras clave del sistema

#### Opciones de Configuración:
- **Palabra Clave**: El texto que activará la respuesta
- **Respuesta**: El mensaje automático a enviar
- **Coincidencia Exacta**: Si debe ser exactamente la palabra (no parte de otra)
- **Sensible a Mayúsculas**: Si diferencia mayúsculas/minúsculas
- **Prioridad**: Orden de evaluación (mayor = se evalúa primero)
- **Estado**: Activa/Inactiva

### 3. **Historial de Mensajes** (`/whatsapp/messages/`)
- Lista completa de todos los mensajes
- Filtrado por tipo (recibidos, auto-respuestas, enviados)
- Muestra qué palabra clave activó cada respuesta
- Paginación de 50 mensajes por página

### 4. **Modelos de Base de Datos**

#### `WhatsAppConnection`
- Gestiona la conexión del usuario con WhatsApp
- Almacena el estado (conectado, desconectado, esperando QR)
- Guarda el código QR para escaneo

#### `WhatsAppKeyword`
- Define palabras clave y respuestas
- Configuración de matching (exacto, case-sensitive)
- Contador de usos
- Sistema de prioridades

#### `WhatsAppMessage`
- Registra todos los mensajes
- Tipo de mensaje (recibido, auto-respuesta, enviado)
- Vincula con palabra clave que lo activó

## 📍 Ubicación en el Menú

La integración está disponible en el menú **Compartir** con las siguientes opciones:
- **Dashboard**: Vista principal de WhatsApp
- **Nueva Palabra Clave**: Crear nueva regla de respuesta
- **Mensajes**: Ver historial completo

## 🔧 Estado Actual de Implementación

### ✅ Completado:
1. Modelos de base de datos (migración 0158 aplicada)
2. Vistas de Django para todas las operaciones CRUD
3. Templates HTML con diseño Bootstrap 5
4. URLs configuradas
5. Integración en el menú principal
6. Admin de Django configurado

### ⏳ Pendiente (Backend de WhatsApp Web):
Esta implementación incluye toda la **interfaz de usuario** y la **estructura de datos**, pero aún requiere la integración con la **API de WhatsApp Web** para:
- Generar el código QR real
- Establecer conexión con WhatsApp Web
- Recibir mensajes entrantes
- Enviar respuestas automáticas
- Detectar palabras clave en mensajes
- Actualizar el estado de conexión

### 🔌 Opciones para Completar la Integración:

#### Opción 1: Usar `whatsapp-web.js` (Node.js)
```bash
npm install whatsapp-web.js
```
Crear un servicio Node.js que:
- Se comunique con Django vía API REST
- Gestione la conexión de WhatsApp
- Escuche mensajes y los envíe a Django para procesamiento

#### Opción 2: Usar `yowsup` (Python)
```bash
pip install yowsup
```
Integración directa en Python, pero requiere registro manual.

#### Opción 3: Usar APIs comerciales
- Twilio WhatsApp API
- WhatsApp Business API oficial
- MessageBird, Vonage, etc.

## 📖 Flujo de Uso

### Para el Usuario:
1. **Conectar WhatsApp**:
   - Ir a "Compartir" → "WhatsApp" → "Dashboard"
   - Clic en "Conectar"
   - Escanear código QR con WhatsApp

2. **Configurar Palabras Clave**:
   - Crear nueva palabra clave (ej: "hola")
   - Definir respuesta (ej: "¡Hola! ¿En qué puedo ayudarte?")
   - Ajustar opciones de matching

3. **Monitorear Mensajes**:
   - Ver estadísticas en Dashboard
   - Revisar historial de mensajes
   - Ver cuántas veces se usó cada palabra clave

### Ejemplos de Configuración:

**Ejemplo 1: Saludo**
- Palabra: `hola`
- Respuesta: `¡Hola! ¿En qué puedo ayudarte?`
- Coincidencia exacta: No
- Case sensitive: No

**Ejemplo 2: Horarios**
- Palabra: `horario`
- Respuesta: `Nuestro horario es de Lunes a Viernes, 9:00 AM - 6:00 PM`
- Prioridad: 10

**Ejemplo 3: Precios**
- Palabra: `precio`
- Respuesta: `Tenemos diferentes productos. ¿Cuál te interesa?`

## 🎨 Interfaz Visual

- **Dashboard**: Cards con estadísticas + tablas de palabras clave y mensajes
- **Formularios**: Diseño limpio con Bootstrap 5, ejemplos de uso incluidos
- **Historial**: Tabla paginada con badges de colores por tipo de mensaje
- **Código QR**: Mostrado en formato ASCII en el dashboard cuando está pendiente

## 🔐 Seguridad

- Todas las vistas requieren autenticación (`@login_required`)
- Cada usuario tiene su propia conexión de WhatsApp
- Las palabras clave son privadas por usuario
- Los mensajes se asocian a la conexión del usuario

## 📊 Admin de Django

Todos los modelos están registrados en el admin con:
- Búsqueda avanzada
- Filtros por fecha, estado, usuario
- Campos readonly cuando corresponde
- Badges de colores para estados
- Ordenamiento personalizado

## 🚀 Próximos Pasos Sugeridos

1. **Implementar backend de WhatsApp Web**:
   - Crear servicio de conexión
   - Implementar detección de palabras clave
   - Enviar auto-respuestas

2. **Mejorar matching de palabras clave**:
   - Soporte para expresiones regulares
   - Variables en respuestas (nombre, fecha, etc.)
   - Respuestas múltiples aleatorias

3. **Analytics avanzados**:
   - Gráficos de uso por hora/día
   - Palabras clave más populares
   - Tiempo de respuesta promedio

4. **Funciones adicionales**:
   - Programar mensajes
   - Broadcast a múltiples contactos
   - Integración con tickets del sistema

## 📝 Notas Técnicas

- Los modelos usan `get_or_create` para crear conexión automáticamente
- El estado de conexión se gestiona con choices (`connected`, `disconnected`, `qr_pending`)
- Los mensajes se registran con timestamp automático
- La prioridad de palabras clave afecta el orden de evaluación

## 🆘 Soporte

Para cualquier duda sobre la implementación, revisar:
- `tickets/models.py`: Líneas ~8868 (modelos de WhatsApp)
- `tickets/views.py`: Líneas ~19267 (vistas de WhatsApp)
- `tickets/admin.py`: Líneas con WhatsApp (admin)
- `templates/tickets/whatsapp_*.html`: Templates de interfaz
