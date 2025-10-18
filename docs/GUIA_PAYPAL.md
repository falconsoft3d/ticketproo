# Sistema de Enlaces de Pago PayPal

## Descripción General

El sistema de Enlaces de Pago PayPal permite crear enlaces únicos para vender productos o servicios digitales con pago seguro a través de PayPal. Cada enlace puede incluir un archivo adjunto que el cliente podrá descargar solo después de completar el pago.

## Características Principales

1. **Creación de Enlaces de Pago**
   - Nombre del producto/servicio
   - Descripción detallada
   - Precio en euros (EUR)
   - Archivo adjunto opcional
   - Fecha de expiración opcional
   - Asociación con empresa (opcional)

2. **Gestión de Enlaces**
   - Lista con filtros por estado, empresa, búsqueda
   - Edición de enlaces activos
   - Cancelación de enlaces
   - Eliminación (solo enlaces no pagados)

3. **Página Pública de Pago**
   - URL única e intransferible
   - Información del producto
   - Botón de pago PayPal integrado
   - Pago seguro con cifrado SSL

4. **Entrega Automática**
   - Verificación automática del pago
   - Descarga protegida del archivo
   - Contador de descargas
   - Información del pagador

## Configuración Inicial

### 1. Obtener Credenciales de PayPal

#### Modo Sandbox (Pruebas)
1. Accede a https://developer.paypal.com
2. Inicia sesión con tu cuenta PayPal
3. Ve a "Dashboard" → "My Apps & Credentials"
4. En la sección "Sandbox", crea una nueva App o usa una existente
5. Copia el **Client ID** y **Secret**

#### Modo Live (Producción)
1. En el mismo panel, ve a la sección "Live"
2. Crea una App para producción
3. Copia el **Client ID** y **Secret**

### 2. Configurar en TicketProo

1. Ve al menú **Configuración** → **Configuración General**
2. Expande la sección **"Configuración de PayPal"**
3. Completa los campos:
   - **PayPal Habilitado**: Marca la casilla
   - **Modo**: Selecciona "sandbox" para pruebas o "live" para producción
   - **Client ID**: Pega tu Client ID
   - **Client Secret**: Pega tu Secret
   - **Webhook ID**: (opcional, para webhooks avanzados)
4. Guarda los cambios

### 3. Configurar BASE_URL (Importante)

En tu archivo `settings.py` o variables de entorno, asegúrate de tener:

```python
BASE_URL = 'https://tudominio.com'  # Sin barra final
```

Esto es necesario para generar las URLs públicas correctamente.

## Uso del Sistema

### Crear un Enlace de Pago

1. Ve a **Doc** → **Enlaces de Pago PayPal**
2. Haz clic en **"Nuevo Enlace de Pago"**
3. Completa el formulario:
   - **Nombre del Producto**: Ej. "Plantilla WordPress Premium"
   - **Importe**: Ej. 49.99 EUR
   - **Descripción**: Descripción detallada del producto
   - **Archivo Adjunto**: Sube el archivo que el cliente descargará (ZIP, PDF, etc.)
   - **Nombre del Archivo**: Nombre descriptivo para la descarga
   - **Fecha de Expiración**: (opcional) Fecha hasta la cual el enlace estará activo
   - **Empresa**: (opcional) Asociar con una empresa
   - **Notas Internas**: Notas privadas para tu referencia
4. Haz clic en **"Crear Enlace"**

### Compartir el Enlace

1. Una vez creado, se genera una **URL pública** única
2. Copia la URL usando el botón de copiar
3. Comparte la URL con tu cliente por:
   - Email
   - WhatsApp
   - SMS
   - Redes sociales
   - Cualquier medio de comunicación

### Proceso de Pago (Cliente)

1. El cliente accede a la URL
2. Ve la información del producto:
   - Nombre y descripción
   - Precio
   - Información del archivo incluido
3. Hace clic en el botón de PayPal
4. Completa el pago en PayPal (login o tarjeta)
5. Después del pago:
   - Se muestra mensaje de éxito
   - Aparece botón de descarga del archivo
   - Puede descargar el archivo las veces que necesite

### Gestión de Enlaces

#### Ver Detalles
- Haz clic en "Ver" en cualquier enlace
- Verás toda la información:
  - Estado del pago
  - Información del pagador (si está pagado)
  - Número de descargas
  - URL pública
  - Toda la configuración

#### Editar Enlace
- Solo enlaces activos (no pagados)
- Puedes cambiar:
  - Nombre del producto
  - Descripción
  - Precio
  - Archivo adjunto
  - Fecha de expiración

#### Cancelar Enlace
- Para enlaces activos que ya no quieres ofrecer
- El enlace seguirá visible pero marcado como cancelado
- Los clientes no podrán pagar

#### Eliminar Enlace
- Solo enlaces no pagados
- Acción irreversible
- Elimina el enlace y su archivo adjunto

## Estados de los Enlaces

1. **Activo** (Verde)
   - Enlace disponible para pagos
   - Clientes pueden acceder y pagar
   - Se muestra URL pública

2. **Pagado** (Verde con check)
   - Pago completado exitosamente
   - No se puede editar ni eliminar
   - Archivo disponible para descarga
   - Muestra información del pagador

3. **Expirado** (Gris)
   - Fecha de expiración alcanzada
   - No se puede pagar
   - Se marca automáticamente

4. **Cancelado** (Rojo)
   - Cancelado manualmente
   - No se puede pagar
   - Se puede reactivar editando

## Seguridad

### Protección de Archivos
- Los archivos solo son descargables después del pago
- URLs de descarga protegidas con token único
- Verificación de estado de pago antes de cada descarga

### Verificación de Pagos
- Verificación directa con PayPal
- Captura de información del pagador
- ID de transacción almacenado

### URLs Únicas
- Cada enlace tiene un token UUID único
- No se pueden adivinar las URLs
- Tokens no secuenciales

## Notificaciones

### Información Capturada
Cuando un cliente completa el pago, se guarda:
- Nombre del pagador
- Email del pagador
- ID de transacción PayPal
- Fecha y hora del pago

### Seguimiento
- Contador de descargas por enlace
- Historial de pagos
- Información del pagador para soporte

## Mejores Prácticas

### 1. Nombres Descriptivos
Usa nombres claros que identifiquen el producto:
- ✅ "eBook: Guía Completa de Django"
- ✅ "Plantilla Landing Page Responsive"
- ❌ "Producto 1"

### 2. Descripciones Detalladas
Incluye toda la información relevante:
- Qué incluye el producto
- Formato del archivo
- Requisitos previos
- Política de devoluciones

### 3. Archivos Comprimidos
Para múltiples archivos:
- Usa archivos ZIP
- Incluye un README.txt con instrucciones
- Organiza los archivos en carpetas

### 4. Precios Claros
- Usa decimales completos: 49.99 en lugar de 49.9
- Considera gastos de PayPal en tu precio
- Revisa los precios antes de compartir

### 5. Fechas de Expiración
- Úsalas para ofertas limitadas
- Promociones temporales
- Productos con contenido que expira

### 6. Notas Internas
Usa las notas para:
- Campaña de marketing asociada
- Cliente específico (si el enlace es personalizado)
- Recordatorios de seguimiento

## Comisiones de PayPal

PayPal cobra comisiones por transacción:
- **España/Europa**: 3.4% + 0.35 EUR
- **Internacional**: Varía según país

**Ejemplo**: Venta de 50 EUR
- Comisión PayPal: (50 × 0.034) + 0.35 = 2.05 EUR
- Recibes: 47.95 EUR

> **Tip**: Añade las comisiones a tu precio o indícalo claramente en la descripción.

## Solución de Problemas

### El botón de PayPal no aparece
1. Verifica que PayPal esté habilitado en Configuración
2. Revisa que el Client ID sea correcto
3. Comprueba la consola del navegador (F12)
4. Verifica tu conexión a internet

### El pago se completó pero no se marca como pagado
1. Verifica la configuración del webhook (si lo usas)
2. Revisa los logs del servidor
3. Verifica que el enlace esté en estado "active"
4. Contacta con soporte técnico

### No puedo descargar el archivo
1. Verifica que el pago esté completado
2. Comprueba que el archivo exista en el servidor
3. Revisa los permisos del directorio media/
4. Intenta desde otro navegador

### Modo Sandbox vs Live
- **Sandbox**: Solo para pruebas, usa dinero ficticio
- **Live**: Pagos reales, usa cuentas PayPal reales
- No mezcles credenciales de sandbox con live

## API y Webhooks Avanzados

El sistema incluye endpoints para integración avanzada:

### Endpoints Disponibles
- `POST /paypal/create-order/` - Crear orden
- `POST /paypal/capture-order/` - Capturar pago
- `POST /paypal/webhook/` - Recibir notificaciones

### Configurar Webhooks (Opcional)
1. En PayPal Developer, ve a tu App
2. Añade webhook URL: `https://tudominio.com/paypal/webhook/`
3. Selecciona eventos:
   - `CHECKOUT.ORDER.APPROVED`
   - `PAYMENT.CAPTURE.COMPLETED`
4. Copia el Webhook ID y añádelo en la configuración

## Reportes y Estadísticas

### Información Disponible
- Total de enlaces creados
- Enlaces activos vs pagados
- Total de descargas
- Ingresos por enlace
- Información de pagadores

### Filtros
- Por estado (activo, pagado, expirado, cancelado)
- Por empresa
- Por fecha de creación
- Por búsqueda de texto

## Soporte

### Documentación de PayPal
- Developer: https://developer.paypal.com/docs/
- API Reference: https://developer.paypal.com/api/rest/

### Recursos Adicionales
- Dashboard PayPal: https://www.paypal.com/
- PayPal Developer Dashboard: https://developer.paypal.com/dashboard/

### Contacto
Para problemas técnicos o preguntas sobre la integración, contacta con el equipo de soporte técnico.

---

**Fecha de última actualización**: Enero 2025
**Versión del documento**: 1.0
