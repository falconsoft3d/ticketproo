# 🚀 TicketProo Swarm - Professional Deployment

Sistema de gestión de tickets con deployment profesional usando **Docker Swarm + Traefik + Ansible**.

## ✨ Características

- 🔄 **Alta Disponibilidad**: Múltiples réplicas con failover automático
- 🔒 **SSL Automático**: Certificados Let's Encrypt gestionados por Traefik
- ⚖️ **Load Balancing**: Distribución automática de carga
- 📊 **Escalado**: Horizontal scaling con un comando
- 🔧 **Infrastructure as Code**: Todo automatizado con Ansible
- 🐳 **Zero Downtime**: Rolling updates sin interrupciones

## 📋 Requisitos

### Servidor
- **OS**: Ubuntu 20.04+ / Debian 11+
- **RAM**: Mínimo 2GB (Recomendado 4GB+)
- **CPU**: 2 cores mínimo
- **Storage**: 20GB+ SSD
- **Puertos**: 80, 443, 2377, 7946 abiertos

### Local
- **Ansible**: `pip install ansible`
- **Docker**: Para build de imágenes
- **SSH Key**: Acceso sin contraseña al servidor

## ⚡ Quick Start

### 1. Configurar Inventario
```bash
# Editar configuración del servidor
nano ansible/inventory/hosts.yml

# Cambiar:
# - ansible_host: TU-IP-SERVIDOR
# - domain_name: tu-dominio.com
# - email: tu-email@dominio.com
```

### 2. Configurar DNS
Crear registros A en tu proveedor DNS:
```
@ -> IP-SERVIDOR
www -> IP-SERVIDOR
traefik -> IP-SERVIDOR (opcional)
```

### 3. Deploy One-Click
```bash
chmod +x deploy-swarm.sh
./deploy-swarm.sh
```

## 🏗️ Arquitectura

```
Internet
    ↓
[ Traefik ] ← SSL Automático
    ↓
[ Docker Swarm ]
    ├── Web (3 réplicas)
    ├── Worker (2 réplicas)  
    ├── PostgreSQL (1 réplica)
    ├── Redis (1 réplica)
    └── Nginx (2 réplicas)
```

### Servicios Deployados

| Servicio | Réplicas | Puerto | Función |
|----------|----------|---------|---------|
| **Traefik** | 1 | 80, 443 | Proxy + SSL |
| **Web** | 3 | 8000 | Django App |
| **Worker** | 2 | - | Celery Tasks |
| **PostgreSQL** | 1 | 5432 | Base de Datos |
| **Redis** | 1 | 6379 | Cache + Queue |
| **Nginx** | 2 | 80 | Static Files |

## 🎛️ Gestión de Servicios

### Ver Estado
```bash
# Estado de stacks
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker stack ls"

# Estado de servicios
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service ls"

# Estado detallado de un servicio
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service ps ticketproo_web"
```

### Logs
```bash
# Logs de aplicación web
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service logs ticketproo_web --tail 100"

# Logs de Traefik
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service logs traefik_traefik --tail 100"

# Logs de base de datos
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service logs ticketproo_db --tail 100"
```

### Escalado
```bash
# Escalar web a 5 réplicas
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service scale ticketproo_web=5"

# Escalar workers a 3 réplicas
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service scale ticketproo_worker=3"

# Ver escalado actual
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service ls"
```

### Updates
```bash
# Rolling update de la aplicación
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service update --image ticketproo:latest ticketproo_web"

# Update con configuración específica
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service update --env-add NEW_VAR=value ticketproo_web"
```

## 🔧 Comandos Útiles

### Backup Base de Datos
```bash
# Crear backup
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker exec \$(docker ps -q -f name=ticketproo_db) pg_dump -U ticketproo_user ticketproo_db > /opt/backup-\$(date +%Y%m%d).sql"

# Listar backups
ansible ticketproo -i ansible/inventory/hosts.yml -a "ls -la /opt/backup-*.sql"
```

### Mantenimiento
```bash
# Limpiar imágenes no usadas
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker system prune -f"

# Ver uso de recursos
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker stats --no-stream"

# Ver uso de volúmenes
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker system df"
```

### Debug
```bash
# Conectar a contenedor web
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker exec -it \$(docker ps -q -f name=ticketproo_web) bash"

# Ejecutar comando Django
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker exec \$(docker ps -q -f name=ticketproo_web) python manage.py shell"

# Ver configuración de un servicio
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service inspect ticketproo_web"
```

## 🔒 Seguridad

### Secrets Management
Los datos sensibles se gestionan con Docker Secrets:
```bash
# Ver secrets
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker secret ls"

# Rotar secret
ansible ticketproo -i ansible/inventory/hosts.yml -a "echo 'new-secret' | docker secret create postgres_password_v2 -"
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service update --secret-rm postgres_password --secret-add postgres_password_v2 ticketproo_db"
```

### SSL/TLS
- Certificados SSL automáticos con Let's Encrypt
- Renovación automática cada 60 días
- Grade A+ en SSL Labs
- HSTS habilitado

### Network Security
- Red overlay interna para servicios
- Solo Traefik expuesto públicamente
- Firewall automático entre servicios

## 📊 Monitoreo

### Health Checks
Todos los servicios tienen health checks configurados:
- **Web**: HTTP check en `/health/`
- **Database**: `pg_isready`
- **Redis**: `redis-cli ping`

### Métricas (Opcional)
Para habilitar Prometheus + Grafana:
```bash
# Deploy stack de monitoring
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-monitoring.yml
```

## 🆘 Troubleshooting

### Servicio no inicia
```bash
# Ver logs detallados
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service logs ticketproo_web --details"

# Ver eventos del servicio
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service ps ticketproo_web --no-trunc"
```

### SSL no funciona
```bash
# Ver logs de Traefik
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker service logs traefik_traefik | grep acme"

# Verificar configuración
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker exec \$(docker ps -q -f name=traefik) cat /letsencrypt/acme.json"
```

### Base de datos
```bash
# Conectar a PostgreSQL
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker exec -it \$(docker ps -q -f name=ticketproo_db) psql -U ticketproo_user ticketproo_db"

# Ver conexiones activas
ansible ticketproo -i ansible/inventory/hosts.yml -a "docker exec \$(docker ps -q -f name=ticketproo_db) psql -U ticketproo_user -d ticketproo_db -c 'SELECT * FROM pg_stat_activity;'"
```

## 🔄 Disaster Recovery

### Backup Completo
```bash
# Ejecutar playbook de backup
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/backup.yml

# Backup incluye:
# - Base de datos PostgreSQL
# - Volúmenes Docker
# - Configuración de servicios
# - Certificados SSL
```

### Restore
```bash
# Restore desde backup
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/restore.yml -e "backup_date=20251221"
```

---

## 🎉 Deployment Exitoso

Una vez completado el deployment:

- ✅ **Aplicación**: https://tu-dominio.com
- ✅ **Admin**: https://tu-dominio.com/admin/
- ✅ **Traefik Dashboard**: https://traefik.tu-dominio.com
- ✅ **Alta Disponibilidad**: 3 réplicas activas
- ✅ **SSL**: Certificados automáticos
- ✅ **Escalabilidad**: Ready para producción

**¡TicketProo está listo para manejar miles de usuarios! 🚀**