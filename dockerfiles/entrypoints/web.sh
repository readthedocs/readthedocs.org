#! /bin/sh

../../docker/common.sh

if [ -n "$INIT" ];
then
    echo "Performing initial tasks..."
    python3 manage.py migrate
    cat ../../docker/createsuperuser.py | python3 manage.py shell
    python3 manage.py collectstatic --no-input
    python3 manage.py loaddata test_data
fi

if [ -n "${DOCKER_NO_RELOAD}" ]; 
then
    RELOAD='--noreload'
    echo "Running Docker with no reload"
else
    RELOAD=''
    echo "Running Docker with reload"
fi

python3 manage.py runserver 0.0.0.0:8000 $RELOAD
