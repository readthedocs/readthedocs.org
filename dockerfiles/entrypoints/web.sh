#! /bin/sh

../../docker/common.sh

if [ -n "$INIT" ];
then
    echo "Performing initial tasks..."
    python3 manage.py migrate
    cat ../../docker/createsuperuser.py | python3 manage.py shell

    # collect static in background
    python3 manage.py collectstatic --no-input

    python3 manage.py loaddata test_data
fi

python3 manage.py runserver 0.0.0.0:8000
