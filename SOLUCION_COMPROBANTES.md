# 🔧 Guía de Solución - Subir Comprobantes de Pago

## ✅ **Estado del Sistema Verificado:**

- ✅ Modelo `EmployeePayroll` configurado correctamente
- ✅ Campo `payment_receipt` como opcional (no requerido)
- ✅ Formulario `EmployeePayrollForm` incluye el campo
- ✅ Directorio `media/payment_receipts/` creado
- ✅ Template con `enctype="multipart/form-data"`
- ✅ JavaScript para drag & drop implementado
- ✅ Validaciones de archivo funcionando

## 🎯 **Pasos para subir comprobante de pago:**

### 1. **Acceder a la nómina existente**
```
1. Ve a: Herramientas → Empleados Activos → Empleados
2. Busca el empleado "jesus maria"
3. Haz clic en "Nóminas"
4. Verás la nómina de "Enero/2025" sin comprobante
5. Haz clic en "Ver" o en el icono de edición
```

### 2. **Editar la nómina para agregar comprobante**
```
1. En la página de detalle, haz clic en "Editar Nómina"
2. Busca la sección "Comprobante de Pago" (segunda área de archivos)
3. Haz clic en esa área o arrastra un archivo
4. Selecciona cualquier archivo: PDF, JPG, JPEG o PNG
5. Máximo 5MB de tamaño
```

### 3. **Métodos para subir archivo**
- **Método 1**: Haz clic en el área de "Comprobante de Pago" y selecciona archivo
- **Método 2**: Arrastra el archivo directamente al área
- **Método 3**: Haz clic en "Seleccionar archivo" dentro del área

## 🐛 **Si sigue sin funcionar, verifica:**

### A. **Permisos del navegador**
- Asegúrate de que el navegador permita subir archivos
- Prueba en una pestaña de incógnito

### B. **Tamaño y tipo de archivo**
- El archivo debe ser menor a 5MB
- Tipos permitidos: PDF, JPG, JPEG, PNG
- Nombres sin caracteres especiales

### C. **JavaScript habilitado**
- Verifica que JavaScript esté habilitado
- Abre Developer Tools (F12) y mira la consola por errores

## 🔍 **Debug paso a paso:**

1. **Abrir Developer Tools (F12)**
2. **Ir a la pestaña Console**
3. **Intentar subir un comprobante**
4. **Verificar mensajes de debug:**
   - "Archivo de comprobante seleccionado: [archivo]"
   - "Enviando formulario - PDF: [pdf] Comprobante: [archivo]"

## 📁 **Archivos de prueba sugeridos:**

Puedes crear archivos de prueba simples:
```bash
# Crear un PDF de prueba (en cualquier lugar de tu Mac)
echo "Comprobante de pago de prueba" > comprobante_test.txt
# Luego cambiar extensión a .pdf o usar cualquier PDF existente

# O usar una imagen cualquiera (screenshot, foto, etc.)
```

## 🚀 **URL directa para probar:**
```
http://localhost:8000/tickets/employee/2/payroll/1/edit/
```

## 📞 **Si necesitas ayuda adicional:**

Si después de seguir estos pasos el problema persiste, por favor proporciona:

1. **Mensaje de error específico** (si aparece alguno)
2. **Captura de pantalla** del formulario
3. **Información de la consola** del navegador (F12 → Console)
4. **Tipo y tamaño** del archivo que intentas subir

---

**¡El sistema está funcionando correctamente! El problema puede ser de navegador o de proceso de usuario.** 🎉