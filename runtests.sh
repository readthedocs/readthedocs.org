#!/bin/sh

(
    python_path=`pwd`
    if [ -n "${PYTHON_PATH}" ]; then
        python_path="${python_path}:${PYTHONPATH}"
    fi
    export PYTHONPATH=$python_path
    if [ -z "${DJANGO_SETTINGS_MODULE}" ]; then
        export DJANGO_SETTINGS_MODULE=settings.test
    fi

    cd readthedocs
    rm -rf rtd_tests/builds/

    coverage run -m pytest $*
)
