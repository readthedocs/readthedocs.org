#! /bin/sh


python3 manage.py migrate
cat ../../docker/scripts/createsuperuser.py | python3 manage.py shell
python3 manage.py collectstatic --no-input
python3 manage.py loaddata test_data

python3 manage.py runserver 0.0.0.0:8000
