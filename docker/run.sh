#!/bin/bash

pip install -r requirements.txt

python manage.py migrate

python manage.py shell < docker/create_superuser.py

python manage.py collectstatic --noinput
python manage.py loaddata test_data

python manage.py runserver 0.0.0.0:8000
