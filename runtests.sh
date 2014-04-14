cd readthedocs
DJANGO_SETTINGS_MODULE=settings.test ./manage.py test --logging-clear-handlers ./
exit=$?
cd -
exit $exit
