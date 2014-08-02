cd readthedocs
export PYTHONPATH=`pwd`:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=settings.test
py.test
exit=$?
cd -
exit $exit
