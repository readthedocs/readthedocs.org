#! /bin/sh

../../docker/common.sh

watchmedo auto-restart \
  --patterns="*.py" \
  --ignore-patterns="*.#*.py;./user_builds/*;./public_*;./private_*;*.pyo;*.pyc;*flycheck*.py;./media/*;./.tox/*" \
  --ignore-directories \
  --recursive \
  --signal=SIGTERM \
  --kill-after=5 \
  --interval=5 \
  -- \
  python3 -m celery worker -A readthedocs.worker -Ofair -c 2 -Q builder,celery,default,build01 -l DEBUG
