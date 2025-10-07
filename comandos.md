# para el server
```
source .venv/bin/activate
python manage.py runserver 8000
lsof -ti:8000
kill -9 71529 80202
```