# 🗄️ Sistema de Respaldo y Restauración de Base de Datos

## 📋 **Resumen de Compatibilidad**

El sistema de respaldo implementado es **compatible con múltiples tipos de base de datos**:

### ✅ **Bases de Datos Soportadas**

| Base de Datos | Estado | Método de Respaldo | Requisitos |
|---------------|--------|--------------------|------------|
| **SQLite** | ✅ Completamente soportado | Copia directa del archivo | Ninguno adicional |
| **PostgreSQL** | ✅ Completamente soportado | pg_dump / psql | pg_dump y psql instalados |
| **MySQL** | ⚠️ Pendiente implementación | mysqldump / mysql | mysqldump y mysql instalados |
| **Oracle** | ⚠️ Pendiente implementación | expdp / impdp | Oracle Client instalado |

---

## 🔧 **Configuración Actual del Proyecto**

El proyecto **TicketPro** está configurado para detectar automáticamente el tipo de base de datos:

```python
# En settings.py
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # PostgreSQL en producción/Docker
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # SQLite en desarrollo local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

---

## 🐘 **Configuración para PostgreSQL**

### **1. Requisitos del Sistema**

Para usar PostgreSQL, necesitas instalar las herramientas de línea de comandos:

#### **En Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-client
```

#### **En CentOS/RHEL:**
```bash
sudo yum install postgresql
```

#### **En macOS:**
```bash
brew install postgresql
```

#### **En Windows:**
Descargar e instalar PostgreSQL desde [postgresql.org](https://www.postgresql.org/download/windows/)

### **2. Variables de Entorno**

Para usar PostgreSQL, configura la variable `DATABASE_URL`:

```bash
# Formato de DATABASE_URL para PostgreSQL
export DATABASE_URL="postgresql://usuario:contraseña@host:puerto/nombre_bd"

# Ejemplo
export DATABASE_URL="postgresql://admin:mi_password@localhost:5432/ticketproo_db"
```

### **3. Configuración Docker (Recomendado)**

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ticketproo_db
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: mi_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    environment:
      DATABASE_URL: "postgresql://admin:mi_password@db:5432/ticketproo_db"
    depends_on:
      - db

volumes:
  postgres_data:
```

---

## 🔄 **Diferencias en el Proceso de Respaldo**

### **SQLite (Desarrollo Local)**
- **Respaldo**: Copia directa del archivo `db.sqlite3`
- **Restauración**: Reemplazo directo del archivo
- **Ventajas**: Simple, rápido, sin dependencias
- **Desventajas**: No adecuado para producción con múltiples usuarios

### **PostgreSQL (Producción)**
- **Respaldo**: Usa `pg_dump` para crear un dump SQL
- **Restauración**: Recrea la BD y usa `psql` para importar
- **Ventajas**: Robusto, escalable, transaccional
- **Desventajas**: Requiere herramientas adicionales

---

## 🚀 **Migración de SQLite a PostgreSQL**

### **Paso 1: Crear Respaldo en SQLite**
1. Accede a **Herramientas** → **Base de Datos** → **Crear Respaldo**
2. Descarga el archivo ZIP generado

### **Paso 2: Configurar PostgreSQL**
1. Instala PostgreSQL y las herramientas de cliente
2. Crea una nueva base de datos
3. Configura la variable `DATABASE_URL`

### **Paso 3: Migrar Datos**
```bash
# Ejecutar migraciones
python manage.py migrate

# Cargar datos desde respaldo SQLite
python manage.py loaddata datos_exportados.json
```

### **Paso 4: Verificar Funcionamiento**
1. El sistema detectará automáticamente PostgreSQL
2. Los respaldos nuevos usarán `pg_dump`
3. La interfaz mostrará "Base de datos: PostgreSQL"

---

## 🛠️ **Comandos de Administración**

### **Crear Respaldo Manual (PostgreSQL)**
```bash
# Comando directo
pg_dump -h localhost -U usuario -d nombre_bd > respaldo.sql

# Con compresión
pg_dump -h localhost -U usuario -d nombre_bd | gzip > respaldo.sql.gz
```

### **Restaurar Manual (PostgreSQL)**
```bash
# Desde SQL plano
psql -h localhost -U usuario -d nombre_bd < respaldo.sql

# Desde comprimido
gunzip -c respaldo.sql.gz | psql -h localhost -U usuario -d nombre_bd
```

---

## 🔒 **Consideraciones de Seguridad**

### **Para PostgreSQL:**
1. **Autenticación sin Contraseña**: Configurar `.pgpass` o variables de entorno
2. **Permisos de Usuario**: El usuario debe poder crear/eliminar bases de datos
3. **Conexiones de Red**: Configurar `pg_hba.conf` apropiadamente
4. **Respaldos Encriptados**: Considerar encriptar los archivos ZIP

### **Variables de Entorno Seguras:**
```bash
# Para evitar contraseñas en comandos
export PGPASSWORD="mi_contraseña_segura"
export PGUSER="usuario_respaldos"
export PGHOST="servidor_bd"
export PGPORT="5432"
```

---

## 📊 **Monitoreo y Rendimiento**

### **Tamaños de Respaldo Típicos:**
- **SQLite pequeña** (< 100MB): 1-5 segundos
- **SQLite mediana** (100MB-1GB): 5-30 segundos
- **PostgreSQL pequeña** (< 100MB): 5-15 segundos
- **PostgreSQL mediana** (100MB-1GB): 30-120 segundos
- **PostgreSQL grande** (> 1GB): Varios minutos

### **Optimizaciones:**
- Respaldos comprimidos automáticamente (ZIP)
- Exclusión de tablas temporales
- Respaldos incrementales (futura implementación)

---

## 🚨 **Solución de Problemas**

### **Error: "pg_dump not found"**
```bash
# Verificar instalación
which pg_dump
pg_dump --version

# Agregar al PATH si es necesario
export PATH=$PATH:/usr/lib/postgresql/15/bin
```

### **Error: "FATAL: password authentication failed"**
```bash
# Verificar credenciales
psql -h localhost -U usuario -d postgres -c "SELECT version();"

# Configurar autenticación
echo "*:*:*:usuario:contraseña" >> ~/.pgpass
chmod 600 ~/.pgpass
```

### **Error: "permission denied to create database"**
```sql
-- Otorgar permisos de superusuario
ALTER USER usuario WITH SUPERUSER;

-- O crear usuario específico para respaldos
CREATE USER backup_user WITH CREATEDB;
```

---

## 📈 **Roadmap Futuro**

### **Próximas Funcionalidades:**
- [ ] Soporte para MySQL
- [ ] Soporte para Oracle
- [ ] Respaldos incrementales
- [ ] Programación automática de respaldos
- [ ] Compresión avanzada
- [ ] Encriptación de respaldos
- [ ] Respaldos remotos (S3, Google Cloud)
- [ ] Métricas de rendimiento
- [ ] Notificaciones por email

---

## 🎯 **Conclusión**

El sistema de respaldo de **TicketPro** es **completamente compatible con PostgreSQL** y detecta automáticamente el tipo de base de datos configurada. Solo necesitas:

1. ✅ Instalar las herramientas PostgreSQL (`pg_dump`, `psql`)
2. ✅ Configurar la variable `DATABASE_URL`
3. ✅ Verificar permisos de usuario
4. ✅ El sistema funcionará automáticamente

**¡El respaldo funcionará tanto en SQLite como en PostgreSQL sin cambios adicionales!** 🎉