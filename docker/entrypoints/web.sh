#! /bin/sh

# pip install -r requirements/deploy.txt
# pip install -e ../readthedocs-ext/

python manage.py migrate
cat ../../docker/scripts/createsuperuser.py | python manage.py shell
python manage.py collectstatic --no-input
python manage.py loaddata test_data

python manage.py runserver 0.0.0.0:8000
