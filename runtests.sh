#!/bin/sh

(
    python_path=`pwd`
    if [ -z "${PYTHON_PATH}" ]; then
        python_path="${python_path}:${PYTHONPATH}"
    fi
    export PYTHONPATH=$python_path
    export DJANGO_SETTINGS_MODULE=readthedocsinc.settings.test

    cd readthedocs
    rm -rf rtd_tests/builds/

    coverage run -m py.test $*
)
