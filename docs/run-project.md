# config

```sh
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

# .env
DEBUG=True
SECRET_KEY=una-clave-cualquiera-para-desarrollo
ALLOWED_HOSTS=127.0.0.1,localhost

python manage.py migrate
python manage.py createsuperuser
```

# runserver

```sh

source venv/Scripts/activate
python manage.py runserver

# http://127.0.0.1:8000/
superuser123
superuser123@gmail.com
P45s_123

python manage.py seed_repositorio --count 50

# referencia https://repositorio.eesppamm.edu.pe/browse?type=dateissued
```
