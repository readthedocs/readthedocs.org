cd readthedocs
DJANGO_SETTINGS_MODULE=settings.test ./manage.py test rtd_tests --logging-clear-handlers
exit=$?
cd -
exit $exit
