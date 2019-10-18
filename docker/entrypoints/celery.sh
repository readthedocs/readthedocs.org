#! /bin/sh

python3 -m celery worker -A readthedocs.worker -Ofair -c 2 -Q web,web01,reindex -l DEBUG
