# 🚀 TicketProo - Guía de Despliegue con Docker y HTTPS

Esta guía te ayudará a desplegar TicketProo en producción usando Docker, PostgreSQL y certificados SSL automáticos con Let's Encrypt (Certbot).

## 📋 Prerrequisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Dominio apuntando a tu servidor (para certificados SSL reales)
- Al menos 2GB de RAM disponible
- 5GB de espacio en disco
- Puertos 80 y 443 abiertos en tu servidor

## 🐳 Instalación de Docker

### Ubuntu/Debian
```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Agregar clave GPG oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Agregar usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Reiniciar sesión o ejecutar:
newgrp docker

# Verificar instalación
docker --version
docker compose version
```

### CentOS/RHEL/Rocky Linux
```bash
# Instalar dependencias
sudo yum install -y yum-utils

# Agregar repositorio de Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar y habilitar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Reiniciar sesión o ejecutar:
newgrp docker

# Verificar instalación
docker --version
docker compose version
```

### macOS
```bash
# Instalar usando Homebrew
brew install --cask docker

# O descargar Docker Desktop desde:
# https://docs.docker.com/desktop/install/mac-install/

# Verificar instalación
docker --version
docker compose version
```

### Windows
```bash
# Instalar Docker Desktop desde:
# https://docs.docker.com/desktop/install/windows-install/

# O usar Chocolatey:
choco install docker-desktop

# Verificar instalación en PowerShell:
docker --version
docker compose version
```

### Verificación de Instalación
```bash
# Verificar que Docker funcione correctamente
docker run hello-world

# Verificar Docker Compose
docker compose version

# Ver información del sistema Docker
docker info
```

## 🗂️ Estructura de Archivos de Deploy

```
ticketproo/
├── Dockerfile                 # Imagen de la aplicación Django
├── docker-compose.yml         # Orquestación de servicios (web, db, nginx, certbot)
├── entrypoint.sh             # Script de inicialización
├── nginx.conf                # Configuración del proxy inverso con HTTPS
├── requirements.txt          # Dependencias Python
├── .dockerignore            # Archivos excluidos del build
├── .env.example             # Plantilla de variables de entorno
├── init-letsencrypt.sh      # Script para configurar SSL automáticamente
├── renew-ssl.sh             # Script para renovar certificados manualmente
└── ticket_system/
    └── settings_production.py  # Configuración para producción
```

## ⚙️ Configuración Inicial

### 1. Crear archivo de variables de entorno

```bash
# Copiar plantilla
cp .env.example .env

# Editar variables importantes
nano .env
```

**Variables críticas a modificar:**
```env
SECRET_KEY=tu-clave-super-secreta-muy-larga-y-aleatoria
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
POSTGRES_PASSWORD=password-seguro-para-bd
DOMAIN=tu-dominio.com
CERTBOT_EMAIL=admin@tu-dominio.com
CERTBOT_STAGING=0
```

### 2. Preparar directorios y permisos

```bash
# Crear directorios necesarios
mkdir -p logs certbot/conf certbot/www db_backup

# Dar permisos a los scripts
chmod +x entrypoint.sh
chmod +x init-letsencrypt.sh
chmod +x renew-ssl.sh
```

## 🚀 Despliegue

### Opción 1: Despliegue con HTTPS Automático (Recomendado para Producción)

```bash
# 1. Configurar variables de entorno para tu dominio
nano .env

# 2. Ejecutar script de configuración SSL
./init-letsencrypt.sh

# 3. Verificar estado de todos los servicios
docker-compose ps
```

### Opción 2: Despliegue Solo HTTP (Para Testing Local)

```bash
# 1. Comentar servicio certbot en docker-compose.yml temporalmente
# 2. Modificar nginx.conf para solo HTTP
# 3. Levantar servicios
docker-compose up -d --build
```

### Opción 3: Despliegue Paso a Paso

```bash
# 1. Construir la imagen
docker-compose build

# 2. Iniciar base de datos
docker-compose up -d db

# 3. Esperar a que PostgreSQL esté listo
docker-compose logs db

# 4. Iniciar aplicación web
docker-compose up -d web

# 5. Configurar SSL
./init-letsencrypt.sh
```

## 🔍 Verificación del Despliegue

### Chequear servicios
```bash
# Estado de contenedores
docker-compose ps

# Logs de cada servicio
docker-compose logs db
docker-compose logs web
docker-compose logs nginx

# Verificar conectividad de red
docker-compose exec web ping db
```

### Acceder a la aplicación
- **Aplicación HTTPS**: https://tu-dominio.com
- **Aplicación HTTP**: http://localhost (solo para testing)
- **Admin Django**: https://tu-dominio.com/admin/
- **Credenciales por defecto**: admin / admin123

### Verificar base de datos
```bash
# Conectar a PostgreSQL
docker-compose exec db psql -U postgres -d ticketproo

# Ver tablas
\dt

# Salir
\q
```

## 🛠️ Gestión y Mantenimiento

### Comandos Django útiles
```bash
# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Recolectar archivos estáticos
docker-compose exec web python manage.py collectstatic

# Acceder al shell de Django
docker-compose exec web python manage.py shell
```

### Backup de base de datos
```bash
# Crear backup
docker-compose exec db pg_dump -U postgres ticketproo > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose exec -T db psql -U postgres -d ticketproo < backup_20240101_120000.sql
```

### Monitoreo de logs
```bash
# Logs en tiempo real
docker-compose logs -f

# Logs de servicio específico
docker-compose logs -f web
docker-compose logs -f nginx

# Últimas 100 líneas
docker-compose logs --tail=100 web
```

## 🔒 Configuración de Seguridad y SSL

### 1. Configuración Automática con Let's Encrypt

El script `init-letsencrypt.sh` configura automáticamente:
- ✅ Certificados SSL válidos con Let's Encrypt
- ✅ Renovación automática cada 12 horas
- ✅ Redirección HTTP → HTTPS
- ✅ Security headers HSTS, CSP, etc.
- ✅ Configuración SSL moderna (TLS 1.2+)

```bash
# Para dominios reales
./init-letsencrypt.sh

# Para testing local (certificados auto-firmados)
# El script detecta 'localhost' automáticamente
```

### 2. Renovación Manual de Certificados

```bash
# Renovar certificados manualmente
./renew-ssl.sh

# Ver logs de certbot
docker-compose logs certbot
```

### 3. Verificar Configuración SSL

```bash
# Verificar certificados
openssl s_client -connect tu-dominio.com:443 -servername tu-dominio.com

# Test SSL con herramientas online
# https://www.ssllabs.com/ssltest/
```

### 2. Configurar firewall
```bash
# Permitir solo puertos necesarios
ufw allow 80/tcp   # HTTP (redirige a HTTPS)
ufw allow 443/tcp  # HTTPS
ufw allow 22/tcp   # SSH (si necesitas acceso remoto)
ufw enable
```

### 3. Cambiar credenciales por defecto
```bash
# Acceder al contenedor
docker-compose exec web python manage.py shell

# Cambiar password del admin
from django.contrib.auth.models import User
admin = User.objects.get(username='admin')
admin.set_password('nuevo-password-muy-seguro')
admin.save()
```

## 📊 Monitoreo y Performance

### Recursos del sistema
```bash
# Uso de recursos por contenedor
docker stats

# Espacio en disco usado
docker system df

# Limpiar recursos no utilizados
docker system prune
```

### Logs de aplicación
- **Django**: `./logs/django.log`
- **Nginx**: Dentro del contenedor en `/var/log/nginx/`

## 🚨 Solución de Problemas

### SSL/HTTPS Issues

#### Error: "SSL certificate problem"
```bash
# Verificar estado de certbot
docker-compose logs certbot

# Verificar configuración de nginx
docker-compose exec nginx nginx -t

# Renovar certificados manualmente
./renew-ssl.sh
```

#### Error: "Your connection is not private"
```bash
# Para localhost (testing)
# Esto es normal con certificados auto-firmados
# Haz clic en "Advanced" → "Proceed to localhost (unsafe)"

# Para dominios reales, verificar:
# 1. Dominio apunta a tu servidor
# 2. Puertos 80/443 abiertos
# 3. Certificados válidos
```

### Errores Generales

#### Error: "Database connection failed"
```bash
# Verificar estado de PostgreSQL
docker-compose logs db

# Reiniciar servicio de base de datos
docker-compose restart db
```

### Error: "Static files not found"
```bash
# Recolectar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput

# Reiniciar Nginx
docker-compose restart nginx
```

### Error: "Permission denied"
```bash
# Verificar permisos del entrypoint
chmod +x entrypoint.sh

# Reconstruir imagen
docker-compose build --no-cache web
```

### Contenedor no inicia
```bash
# Ver logs detallados
docker-compose logs web

# Acceder al contenedor para debug
docker-compose run --rm web bash
```

## 🔄 Actualización de la Aplicación

### Flujo de Desarrollo y Deploy

#### 1. Realizar Cambios en Desarrollo
```bash
# En tu máquina local, hacer cambios al código
nano tickets/models.py  # ejemplo de cambio

# Probar cambios localmente
python manage.py runserver

# Crear y aplicar migraciones si modificaste modelos
python manage.py makemigrations
python manage.py migrate
```

#### 2. Subir Cambios al Repositorio
```bash
# Agregar archivos modificados
git add .

# Hacer commit con mensaje descriptivo
git commit -m "Descripción de los cambios realizados"

# Subir al repositorio remoto
git push origin main
```

#### 3. Actualizar en Servidor de Producción
```bash
# Conectar al servidor (SSH)
ssh usuario@tu-servidor.com

# Ir al directorio del proyecto
cd /ruta/hacia/ticketproo

# Hacer backup de la base de datos ANTES de actualizar
docker-compose exec db pg_dump -U postgres ticketproo > backup_$(date +%Y%m%d_%H%M%S).sql

# Descargar cambios del repositorio
git pull origin main

# Parar servicios temporalmente
docker-compose down

# Reconstruir imagen con cambios
docker-compose build --no-cache web

# Iniciar servicios
docker-compose up -d

# Aplicar migraciones si es necesario
docker-compose exec web python manage.py migrate

# Recolectar archivos estáticos si cambiaste CSS/JS
docker-compose exec web python manage.py collectstatic --noinput

# Verificar que todo funcione
docker-compose logs -f web
```

#### 4. Deploy Automatizado (Alternativa Avanzada)
```bash
# Crear script de deploy automático
nano deploy.sh

# Contenido del script:
#!/bin/bash
set -e

echo "🚀 Iniciando deploy de TicketProo..."

# Backup de base de datos
echo "📦 Creando backup..."
docker-compose exec db pg_dump -U postgres ticketproo > backup_$(date +%Y%m%d_%H%M%S).sql

# Actualizar código
echo "📥 Descargando cambios..."
git pull origin main

# Reconstruir y deploy
echo "🔨 Reconstruyendo aplicación..."
docker-compose down
docker-compose build --no-cache web
docker-compose up -d

# Migraciones y archivos estáticos
echo "🔄 Aplicando migraciones..."
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

echo "✅ Deploy completado!"

# Hacer ejecutable:
chmod +x deploy.sh

# Usar el script:
./deploy.sh
```

### Comandos de Deploy Rápido

#### Deploy Básico (cambios de código sin migraciones)
```bash
git pull && docker-compose restart web
```

#### Deploy Completo (con posibles migraciones)
```bash
# Backup + Update + Rebuild
docker-compose exec db pg_dump -U postgres ticketproo > backup_$(date +%Y%m%d_%H%M%S).sql
git pull origin main
docker-compose down
docker-compose build --no-cache web
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

#### Deploy con Zero Downtime (Avanzado)
```bash
# 1. Construir nueva imagen sin parar servicios
docker-compose build web

# 2. Aplicar migraciones en caliente
docker-compose exec web python manage.py migrate

# 3. Reiniciar solo el servicio web
docker-compose restart web

# 4. Verificar
docker-compose ps
```

### Flujo de Trabajo Recomendado

#### Para Cambios Pequeños (CSS, templates, vistas)
```bash
# Local
git add . && git commit -m "Fix: corregir estilo del botón" && git push

# Servidor
git pull && docker-compose restart web
```

#### Para Cambios de Base de Datos (modelos)
```bash
# Local
python manage.py makemigrations
python manage.py migrate  # probar localmente
git add . && git commit -m "Add: nuevo campo en modelo Ticket" && git push

# Servidor
docker-compose exec db pg_dump -U postgres ticketproo > backup_$(date +%Y%m%d_%H%M%S).sql
git pull
docker-compose build --no-cache web
docker-compose down && docker-compose up -d
docker-compose exec web python manage.py migrate
```

#### Para Cambios de Dependencias (requirements.txt)
```bash
# Local
pip install nueva-libreria
pip freeze > requirements.txt
git add . && git commit -m "Add: nueva dependencia para emails" && git push

# Servidor
git pull
docker-compose build --no-cache web
docker-compose down && docker-compose up -d
```

### Verificación Post-Deploy
```bash
# Verificar estado de servicios
docker-compose ps

# Ver logs para detectar errores
docker-compose logs web

# Verificar conectividad
curl -I https://tu-dominio.com

# Verificar admin
curl -I https://tu-dominio.com/admin/

# Verificar base de datos
docker-compose exec web python manage.py dbshell
```

### Rollback en Caso de Problemas
```bash
# Si algo sale mal, volver a versión anterior
git log --oneline -5  # ver últimos commits
git checkout COMMIT_HASH_ANTERIOR

# Rebuild con versión anterior
docker-compose build --no-cache web
docker-compose down && docker-compose up -d

# Restaurar backup de BD si es necesario
docker-compose exec -T db psql -U postgres -d ticketproo < backup_20240921_120000.sql
```

## 📱 Configuración de Producción Avanzada

### Redis para cache y tareas (Opcional)
Agregar a `docker-compose.yml`:
```yaml
redis:
  image: redis:7-alpine
  container_name: ticketproo_redis
  restart: unless-stopped
```

### Configurar email SMTP
Actualizar `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker-compose logs`
2. Verifica la configuración en `.env`
3. Consulta la documentación de Django
4. Verifica que todos los puertos estén disponibles

---

## 🎉 ¡Felicidades!

Tu aplicación TicketProo debería estar funcionando en:
- **🌐 URL principal**: https://tu-dominio.com (¡con SSL automático!)
- **🔒 Panel admin**: https://tu-dominio.com/admin/
- **👤 Usuario**: admin
- **🔑 Password**: admin123 (¡cámbialo inmediatamente!)

### 🔐 Características de Seguridad Incluidas:
- ✅ **SSL/TLS automático** con Let's Encrypt
- ✅ **Renovación automática** de certificados cada 12 horas
- ✅ **HSTS** (HTTP Strict Transport Security)
- ✅ **Redirección HTTP → HTTPS** automática
- ✅ **Security headers** modernos
- ✅ **Rate limiting** en endpoints sensibles
- ✅ **Configuración SSL/TLS** moderna (A+ rating)

### 🛡️ Checklist de Seguridad Post-Deploy:
- [ ] Cambiar password del usuario admin
- [ ] Configurar dominio real (reemplazar localhost)
- [ ] Verificar certificados SSL en SSLLabs
- [ ] Configurar backups automáticos
- [ ] Configurar monitoreo de logs
- [ ] Actualizar SECRET_KEY en producción

**¡Tu aplicación está lista para producción con HTTPS automático!** 🚀