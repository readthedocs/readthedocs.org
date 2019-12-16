#! /bin/bash

../../docker/common.sh

CMD='python3 -m celery worker -A readthedocs.worker -Ofair -c 2 -Q builder,celery,default,build01 -l DEBUG'

if [ -n "${DOCKER_NO_RELOAD}" ]; then
  echo "Running Docker with no reload"
  $CMD
else
  echo "Running Docker with reload"
  watchmedo auto-restart \
  --patterns="*.py" \
  --ignore-patterns="*.#*.py;./user_builds/*;./public_*;./private_*;*.pyo;*.pyc;*flycheck*.py;./media/*;./.tox/*" \
  --ignore-directories \
  --recursive \
  --signal=SIGTERM \
  --kill-after=5 \
  --interval=5 \
  -- \
  $CMD
fi

