#! /bin/sh

source common.sh

python3 ../../docker/scripts/wait_for_search.py

CMD='python3 -m celery worker -A readthedocs.worker -Ofair -c 2 -Q web,web01,reindex -l DEBUG'

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
