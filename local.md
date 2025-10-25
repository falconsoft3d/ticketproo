# Comandos Locales de Desarrollo

# Activar entorno virtual y correr servidor
```
source .venv/bin/activate
http://localhost:8000/public-time/8qgAxa2JQGID0EQgcjDuwnC-0-WEOaag8Ln7N5-_qJk/
```

# Comandos para manejar el servidor en el puerto 8000
```
# Iniciar servidor
python manage.py runserver
# Detener servidor
# (Usar Ctrl+C en la terminal donde se está ejecutando)
# Encontrar procesos en el puerto 8000
lsof -ti:8000
# Matar procesos en el puerto 8000
kill -9 <PID1> <PID2>
# O matar todos los procesos en el puerto 8000 de una vez
lsof -ti:8000 | xargs kill -9
```