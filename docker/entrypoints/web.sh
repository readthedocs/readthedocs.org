#! /bin/sh

python manage.py migrate
cat ../../docker/scripts/createsuperuser.py | python manage.py shell
python manage.py collectstatic --no-input
python manage.py loaddata test_data

gunicorn readthedocs.wsgi:application -w 3 -b :8000
