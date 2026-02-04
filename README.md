# Django base

## Instalación

```
sudo apt install python3 python3-pip python3-venv python-is-python3 apache2 libapache2-mod-wsgi-py3 git -y

#clonar
git clone git@github.com:sebastianeula2015/base_django.git

#crear entorno virtual
python -m venv venv
source venv/bin/activate

#instalar requirements.txt
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver 0.0.0.0:8088 &

```
## Deploy apache
 
```
#base_django.conf

<VirtualHost *:80>
    ServerName mantenimiento.uncuyo.edu.ar
    DocumentRoot /var/www/html/base_django/

    WSGIDaemonProcess base_django user=www-data group=www-data threads=5 python-home=/var/www/html/base_django/venv
    WSGIScriptAlias / /var/www/html/base_django/src/wsgi.py
    WSGIProcessGroup base_django

    <Directory /var/www/html/base_django>
        Require all granted
<Files wsgi.py>
Require all granted
</Files>
    </Directory>

Alias /static/ /var/www/html/base_django/static/

<Directory /var/www/html/base_django/static/>
    Require all granted
</Directory>

    ErrorLog ${APACHE_LOG_DIR}/base_django.log
    CustomLog ${APACHE_LOG_DIR}/base_django.log combined
</VirtualHost>


```

## Ejemplo para usar simple_history en los modelos

```python
from django.db import models
from simple_history.models import HistoricalRecords

class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    history = HistoricalRecords()

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    history = HistoricalRecords()
```

### Para modelos ya existentes:

```bash
python manage.py populate_history --auto
```

### Para modelos de terceros

```python
from simple_history import register
from django.contrib.auth.models import User

register(User)
```
