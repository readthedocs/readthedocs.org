#! /bin/sh

../../docker/common.sh

python3 manage.py migrate
cat ../../docker/scripts/createsuperuser.py | python3 manage.py shell

# collect static in background
python3 manage.py collectstatic --no-input &

python3 manage.py loaddata test_data

python3 manage.py runserver 0.0.0.0:8000
