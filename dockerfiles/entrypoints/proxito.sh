#! /bin/sh

source common.sh

if [ -n "${DOCKER_NO_RELOAD}" ]; 
then
    RELOAD='--noreload'
    echo "Running Docker with no reload"
else
    RELOAD=''
    echo "Running Docker with reload"
fi

python3 manage.py runserver 0.0.0.0:8000 $RELOAD
