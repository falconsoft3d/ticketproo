## A continuación, se presenta una versión modificada del artículo de instalación, con el nombre de la aplicación cambiado a "ticketproo" y el nombre de usuario a "marlon".

## Instalación de dependencias del servidor

Primero, actualicemos los paquetes:

```bash
sudo apt-get update
sudo apt-get -y upgrade
```

### PostgreSQL

Instala las dependencias para usar **PostgreSQL** con Python/Django:

```bash
sudo apt-get -y install build-essential libpq-dev python-dev
```

Instala el servidor **PostgreSQL**:

```bash
sudo apt-get -y install postgresql postgresql-contrib
```

### NGINX

Instala **NGINX**, que se usará para servir archivos estáticos (css, js, imágenes) y también para ejecutar la aplicación Django detrás de un servidor proxy:

```bash
sudo apt-get -y install nginx
```

### Supervisor

**Supervisor** iniciará el servidor de la aplicación y lo gestionará en caso de caída o reinicio del servidor:

```bash
sudo apt-get -y install supervisor
```

Habilita y arranca Supervisor:

```bash
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### Python Virtualenv

La aplicación Django se desplegará dentro de un **Python Virtualenv**, para una mejor gestión de los requisitos:

```bash
sudo apt-get -y install python-virtualenv
```

-----

## Configuración de la base de datos PostgreSQL

Cambia de usuario:

```bash
su - postgres
```

Crea un usuario de base de datos y la base de datos de la aplicación:

```bash
createuser u_marlon
createdb ticketproo_prod --owner u_marlon
psql -c "ALTER USER u_marlon WITH PASSWORD '123'"
```

**NOTA:** ¡Asegúrate de elegir una contraseña segura\! Por simplicidad, se utiliza `123`.

Ahora podemos volver al usuario `root`, simplemente saliendo:

```bash
exit
```

-----

## Configuración del usuario de la aplicación

Crea un nuevo usuario con el siguiente comando:

```bash
adduser marlon
```

Se te harán algunas preguntas. Un ejemplo de la salida es el siguiente:

```bash
Adding user `marlon' ...
Adding new group `marlon' (1000) ...
Adding new user `marlon' (1000) with group `marlon' ...
Creating home directory `/home/marlon' ...
Copying files from `/etc/skel' ...
Enter new UNIX password:
Retype new UNIX password:
passwd: password updated successfully
Changing the user information for marlon
Enter the new value, or press ENTER for the default
  Full Name []:
  Room Number []:
  Work Phone []:
  Home Phone []:
  Other []:
Is the information correct? [Y/n]
```

Añade el usuario a la lista de sudoers:

```bash
gpasswd -a marlon sudo
```

Cambia al usuario recién creado:

```bash
su - marlon
```

-----

## Configuración de Python Virtualenv

En este punto, has iniciado sesión como el usuario `marlon`. Instalarás la aplicación Django en el directorio de inicio de este usuario, `/home/marlon`:

```bash
virtualenv .
```

Actívalo:

```bash
source bin/activate
```

Clona el repositorio:

```bash
git clone https://github.com/sibtc/ticketproo.git
```

Así es como debería verse el directorio `/home/marlon` en este momento:

```
marlon/
 |-- bin/
 |-- ticketproo/  <-- Django App (Git Repository)
 |-- include/
 |-- lib/
 |-- local/
 |-- pip-selfcheck.json
 +-- share/
```

Primero, abre el directorio `ticketproo`:

```bash
cd ticketproo
```

Instala las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

Ahora, necesitas establecer las credenciales de la base de datos en el archivo `settings.py`:

```python
settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ticketproo_prod',
        'USER': 'u_marlon',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '',
    }}
```

**NOTA:** Existen formas más seguras de manejar `SECRET_KEY`, credenciales de la base de datos, etc. Aquí se edita directamente el archivo `settings.py` por simplicidad. El objetivo de este tutorial es el proceso de despliegue en sí.

Migra la base de datos:

```bash
python manage.py migrate
```

Recopila los archivos estáticos:

```bash
python manage.py collectstatic
```

Prueba si todo está bien:

```bash
python manage.py runserver 0.0.0.0:8000
```

Accede a la dirección IP de tu servidor usando el puerto 8000. Por ejemplo, `107.170.28.172:8000`.

Esto es solo una prueba. No se utilizará `runserver` para ejecutar la aplicación, sino un servidor de aplicaciones adecuado para servirla de forma segura.

Presiona `CONTROL-C` para salir del servidor de desarrollo y continuemos.

-----

## Configuración de Gunicorn

Primero, instala **Gunicorn** dentro del entorno virtual:

```bash
pip install gunicorn
```

Crea un archivo llamado `gunicorn_start` dentro de la carpeta `bin/`:

```bash
vim bin/gunicorn_start
```

Añade la siguiente información y guárdala:

```
/home/marlon/bin/gunicorn_start
#!/bin/bash

NAME="ticketproo"
DIR=/home/marlon/ticketproo
USER=marlon
GROUP=marlon
WORKERS=3
BIND=unix:/home/marlon/run/gunicorn.sock
DJANGO_SETTINGS_MODULE=ticketproo.settings
DJANGO_WSGI_MODULE=ticketproo.wsgi
LOG_LEVEL=error

cd $DIR
source ../bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DIR:$PYTHONPATH

exec ../bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $WORKERS \
  --user=$USER \
  --group=$GROUP \
  --bind=$BIND \
  --log-level=$LOG_LEVEL \
  --log-file=-
```

Haz que el archivo `gunicorn_start` sea ejecutable:

```bash
chmod u+x bin/gunicorn_start
```

Crea un directorio llamado `run`, para el archivo de socket de Unix:

```bash
mkdir run
```

-----

## Configuración de Supervisor

Ahora, configurarás **Supervisor** para que se encargue de ejecutar el servidor Gunicorn.

Primero, crea una carpeta llamada `logs` dentro del entorno virtual:

```bash
mkdir logs
```

Crea un archivo para registrar los errores de la aplicación:

```bash
touch logs/gunicorn-error.log
```

Crea un nuevo archivo de configuración de Supervisor:

```bash
sudo vim /etc/supervisor/conf.d/ticketproo.conf
```

```
/etc/supervisor/conf.d/ticketproo.conf
[program:ticketproo]
command=/home/marlon/bin/gunicorn_start
user=marlon
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/marlon/logs/gunicorn-error.log
```

Vuelve a leer los archivos de configuración de Supervisor y haz que el nuevo programa esté disponible:

```bash
sudo supervisorctl reread
sudo supervisorctl update
```

Verifica el estado:

```bash
sudo supervisorctl status ticketproo
```

```
ticketproo                      RUNNING   pid 23381, uptime 0:00:15
```

Ahora puedes controlar tu aplicación usando Supervisor. Si quieres actualizar el código fuente de tu aplicación con una nueva versión, puedes extraer el código de GitHub y luego reiniciar el proceso:

```bash
sudo supervisorctl restart ticketproo
```

Donde `ticketproo` será el nombre de tu aplicación.

-----

## Configuración de NGINX

Añade un nuevo archivo de configuración llamado `ticketproo` dentro de `/etc/nginx/sites-available/`:

```bash
sudo vim /etc/nginx/sites-available/ticketproo
```

```
/etc/nginx/sites-available/ticketproo
upstream app_server {
    server unix:/home/marlon/run/gunicorn.sock fail_timeout=0;}server {
    listen 80;

    # añade aquí la dirección IP de tu servidor    # o un dominio que apunte a esa IP (como ejemplo.com o www.ejemplo.com)    server_name 107.170.28.172;

    keepalive_timeout 5;
    client_max_body_size 4G;

    access_log /home/marlon/logs/nginx-access.log;
    error_log /home/marlon/logs/nginx-error.log;

    location /static/ {
        alias /home/marlon/static/;
    }

    # comprueba si hay un archivo estático, si no lo encuentra, lo pasa al proxy de la app    location / {
        try_files $uri @proxy_to_app;
    }

    location @proxy_to_app {
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header Host $http_host;
      proxy_redirect off;
      proxy_pass http://app_server;
    }}
```

Crea un enlace simbólico al directorio `sites-enabled`:

```bash
sudo ln -s /etc/nginx/sites-available/ticketproo /etc/nginx/sites-enabled/ticketproo
```

Elimina el sitio web predeterminado de NGINX:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

Reinicia NGINX:

```bash
sudo service nginx restart
```

-----

## La prueba final

¡Listo\! En este punto, tu aplicación debería estar funcionando. Abre el navegador web y accede a ella:

Una prueba final que es recomendable es reiniciar la máquina y ver si todo se reinicia automáticamente:

```bash
sudo reboot
```

Espera unos segundos. Accede al sitio web a través del navegador. Si se carga con normalidad, significa que todo funciona como se esperaba. Todos los procesos se inician automáticamente.