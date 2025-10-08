# para el server
```
source .venv/bin/activate
python manage.py runserver 8000
lsof -ti:8000
kill -9 71529 80202
```

## Forma de actualizar
```
source ~/bin/activate
cd ticketproo

python manage.py makemigrations
python manage.py migrate
python manage.py setup_groups

cp ~/ticketproo/ticket_system/settings.py ~/old_settings.py
cp ~/old_settings.py ~/ticketproo/ticket_system/settings.py

sudo systemctl daemon-reload
sudo systemctl restart urban-train
sudo systemctl status urban-train

python manage.py runserver 0.0.0.0:8000
```