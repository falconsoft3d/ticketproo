#!/bin/bash
echo "==============================================="
echo "=== INSTALADOR DE TICKETPROO EN UBUNTU ===="
echo "==============================================="

# Variables del proyecto TicketProo
PROJECT_NAME="ticketproo"
PROJECT_DIR="/opt/ticketproo"
APP_NAME="ticket_system"
REPO_URL="https://github.com/falconsoft3d/ticketproo.git"
PYTHON_USER="ticketproo"
DB_NAME="ticketproo_db"
DB_USER="ticketproo_user"
DB_PASSWORD="ticketproo_pass"

echo "==1== INICIANDO INSTALACIÓN DE TICKETPROO === "
sudo ln -svf /usr/bin/python3 /usr/bin/python

echo "==2== Actualizando el Sistema === "
sudo apt-get -qq update
sudo apt-get -qq upgrade -y

echo "==3== Instalando dependencias del sistema === "
sudo apt-get -qq install -y build-essential libpq-dev python3-dev python3-pip python3-venv
sudo apt-get -qq install -y git curl wget unzip

echo "==4== Instalando PostgreSQL Server === "
sudo apt-get -qq install -y postgresql postgresql-contrib

echo "==5== Instalando Nginx === "
sudo apt-get -qq install -y nginx

echo "==6== Instalando Redis (para Celery) === "
sudo apt-get -qq install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo "==7== Configurando PostgreSQL para TicketProo === "
sudo su - postgres -c "createuser -s $DB_USER"
sudo su - postgres -c "createdb $DB_NAME --owner $DB_USER"
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Creamos el usuario del sistema para TicketProo
echo "==8== Creando usuario del sistema === "
sudo adduser --system --quiet --shell=/bin/bash --home=/home/$PYTHON_USER --gecos 'TicketProo User' --group $PYTHON_USER
sudo usermod -aG www-data $PYTHON_USER

echo "==9== Creando directorio del proyecto === "
sudo mkdir -p $PROJECT_DIR
sudo chown $PYTHON_USER:$PYTHON_USER $PROJECT_DIR

echo "==10== Clonando proyecto TicketProo === "
sudo -u $PYTHON_USER git clone $REPO_URL $PROJECT_DIR

echo "==11== Creando entorno virtual === "
sudo -u $PYTHON_USER python3 -m venv $PROJECT_DIR/.venv
sudo -u $PYTHON_USER $PROJECT_DIR/.venv/bin/pip install --upgrade pip

echo "==12== Instalando dependencias de Python === "
sudo -u $PYTHON_USER $PROJECT_DIR/.venv/bin/pip install -r $PROJECT_DIR/requirements.txt

echo "==13== Configurando variables de entorno === "
sudo -u $PYTHON_USER tee $PROJECT_DIR/.env > /dev/null <<EOF
DEBUG=False
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
REDIS_URL=redis://localhost:6379/0
EOF

echo "==14== Configurando systemd para Gunicorn === "
sudo tee /etc/systemd/system/ticketproo.socket > /dev/null <<EOF
[Unit]
Description=TicketProo Gunicorn socket

[Socket]
ListenStream=/run/ticketproo.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
EOF

sudo tee /etc/systemd/system/ticketproo.service > /dev/null <<EOF
[Unit]
Description=TicketProo Gunicorn daemon
Requires=ticketproo.socket
After=network.target

[Service]
User=$PYTHON_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/.venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/.venv/bin/gunicorn \\
          --access-logfile - \\
          --workers 3 \\
          --bind unix:/run/ticketproo.sock \\
          $APP_NAME.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

echo "==15== Configurando Nginx para TicketProo === "
read -p 'Indique el dominio principal (ej: ticketproo.com): ' domain
read -p 'Indique la IP del servidor: ' serverip

sudo tee /etc/nginx/sites-available/ticketproo > /dev/null <<EOF
upstream ticketproo {
    server unix:/run/ticketproo.sock fail_timeout=0;
}

server {
    listen 80;
    server_name $domain www.$domain $serverip;

    keepalive_timeout 5;
    client_max_body_size 10M;

    # Logs
    access_log /var/log/nginx/ticketproo_access.log;
    error_log /var/log/nginx/ticketproo_error.log;

    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Main location
    location / {
        try_files \$uri @proxy_to_app;
    }

    location @proxy_to_app {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_pass http://ticketproo;
    }
}
EOF

# Activar el sitio
sudo ln -sf /etc/nginx/sites-available/ticketproo /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "==16== Ejecutando migraciones de Django === "
cd $PROJECT_DIR
sudo -u $PYTHON_USER $PROJECT_DIR/.venv/bin/python manage.py migrate

echo "==17== Recolectando archivos estáticos === "
sudo -u $PYTHON_USER $PROJECT_DIR/.venv/bin/python manage.py collectstatic --noinput

echo "==18== Configurando comandos de gestión === "
sudo -u $PYTHON_USER $PROJECT_DIR/.venv/bin/python manage.py setup_groups
sudo -u $PYTHON_USER $PROJECT_DIR/.venv/bin/python manage.py assign_admin_agent

echo "==19== Configurando Celery para tareas asíncronas === "
sudo tee /etc/systemd/system/ticketproo-celery.service > /dev/null <<EOF
[Unit]
Description=TicketProo Celery Worker
After=network.target

[Service]
Type=forking
User=$PYTHON_USER
Group=$PYTHON_USER
EnvironmentFile=$PROJECT_DIR/.env
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/celery multi start worker1 \\
    -A $APP_NAME \\
    --pidfile=/var/run/celery/%n.pid \\
    --logfile=/var/log/celery/%n%I.log \\
    --loglevel=INFO
ExecStop=$PROJECT_DIR/.venv/bin/celery multi stopwait worker1 \\
    --pidfile=/var/run/celery/%n.pid
ExecReload=$PROJECT_DIR/.venv/bin/celery multi restart worker1 \\
    -A $APP_NAME \\
    --pidfile=/var/run/celery/%n.pid \\
    --logfile=/var/log/celery/%n%I.log \\
    --loglevel=INFO

[Install]
WantedBy=multi-user.target
EOF

# Crear directorios para Celery
sudo mkdir -p /var/run/celery /var/log/celery
sudo chown $PYTHON_USER:$PYTHON_USER /var/run/celery /var/log/celery

echo "==20== Iniciando servicios === "
sudo systemctl daemon-reload
sudo systemctl enable ticketproo.socket
sudo systemctl start ticketproo.socket
sudo systemctl enable ticketproo.service
sudo systemctl start ticketproo.service
sudo systemctl enable ticketproo-celery.service
sudo systemctl start ticketproo-celery.service
sudo systemctl restart nginx

echo "==21== Configurando firewall === "
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo "==============================================="
echo "=== INSTALACIÓN DE TICKETPROO COMPLETADA ==="
echo "==============================================="
echo ""
echo "✓ Proyecto instalado en: $PROJECT_DIR"
echo "✓ Base de datos: PostgreSQL ($DB_NAME)"
echo "✓ Usuario del sistema: $PYTHON_USER"
echo "✓ Servidor web: Nginx + Gunicorn"
echo "✓ Dominio configurado: $domain"
echo "✓ IP del servidor: $serverip"
echo "✓ Redis y Celery configurados"
echo ""
echo "Comandos útiles:"
echo "- Ver logs de Gunicorn: sudo journalctl -u ticketproo.service -f"
echo "- Ver logs de Nginx: sudo tail -f /var/log/nginx/ticketproo_error.log"
echo "- Reiniciar aplicación: sudo systemctl restart ticketproo.service"
echo "- Ver estado: sudo systemctl status ticketproo.service"
echo ""
echo "La aplicación está disponible en:"
echo "- http://$serverip"
echo "- http://$domain (si el DNS está configurado)"
echo ""
echo "¡Instalación completada exitosamente!"