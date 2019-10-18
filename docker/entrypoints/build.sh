#! /bin/sh

python3 -m celery worker -A readthedocs.worker -Ofair -c 2 -Q builder,celery,default,build01 -l DEBUG
