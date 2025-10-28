# 🚨 GUÍA DE SOLUCIÓN: Error de Migración Duplicada en PostgreSQL

## ❌ **Problema Identificado:**
```
django.db.utils.ProgrammingError: column "public_token" of relation "tickets_qrcode" already exists
```

La migración `0237_auto_20251028_1455` está intentando agregar una columna que ya existe de la migración `0236_add_public_token`.

---

## 🛠️ **SOLUCIÓN 1: Automática (Recomendada)**

### Paso 1: Ejecutar el comando de reparación
```bash
cd ~/ticketproo
python manage.py fix_migration_duplicate
```

### Paso 2: Ejecutar migraciones normalmente
```bash
python manage.py migrate
```

---

## 🛠️ **SOLUCIÓN 2: Manual (Si la automática no funciona)**

### Paso 1: Marcar migración como aplicada sin ejecutarla
```bash
cd ~/ticketproo
python manage.py migrate tickets 0237 --fake
```

### Paso 2: Continuar con las migraciones restantes
```bash
python manage.py migrate
```

---

## 🛠️ **SOLUCIÓN 3: Usando PostgreSQL directamente**

### Paso 1: Conectar a PostgreSQL
```bash
psql -h localhost -U tu_usuario -d tu_database
```

### Paso 2: Verificar que la columna existe
```sql
\d tickets_qrcode
```

### Paso 3: Si la columna existe, marcar migración como aplicada
```bash
# Salir de psql con \q
python manage.py migrate tickets 0237 --fake
python manage.py migrate
```

---

## 🔍 **VERIFICACIÓN POST-SOLUCIÓN**

### Comprobar estado de migraciones:
```bash
python manage.py showmigrations tickets
```

### Verificar que el servidor funciona:
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 📋 **ARCHIVOS MODIFICADOS EN ESTA SOLUCIÓN:**

1. **`tickets/migrations/0237_auto_20251028_1455.py`** - Modificada para verificar antes de agregar
2. **`tickets/management/commands/fix_migration_duplicate.py`** - Comando de reparación automática
3. **`requirements.txt`** - Agregado `psutil==6.1.0` para el monitor del sistema

---

## 🚀 **DESPUÉS DE LA SOLUCIÓN:**

Una vez resuelto el problema de migración, el sistema tendrá:

✅ **Sistema de respaldo compatible con PostgreSQL**
✅ **Monitor del sistema con 8 KPIs en tiempo real**  
✅ **Base de datos sincronizada correctamente**
✅ **Todas las funcionalidades operativas**

---

## 📞 **SI NECESITAS AYUDA:**

Si alguna solución no funciona, ejecuta este comando para obtener más información:

```bash
python manage.py dbshell
\d tickets_qrcode
\q
python manage.py showmigrations tickets | tail -10
```

Y comparte la salida para diagnóstico adicional.

---

**🎯 RECOMENDACIÓN:** Usa la **Solución 1** (comando automático) ya que es la más segura y maneja todos los casos edge.