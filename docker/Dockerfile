FROM python:3.6.7-alpine

WORKDIR /usr/src/app

COPY requirements docker/requirements

RUN apk update && \
  apk add --no-cache git build-base libxml2 libxml2-dev libxslt-dev \
  openjpeg-dev tiff-dev musl-dev postgresql-dev \
  rsync && \
  pip install --no-cache-dir -r docker/requirements/deploy.txt

COPY docker/scripts/createsuperuser.py docker/scripts/
COPY docker/entrypoints/web.sh docker/entrypoint.sh

RUN mkdir -p checkouts/readthedocs.org
WORKDIR /usr/src/app/checkouts/readthedocs.org

CMD ["../../docker/entrypoint.sh"]
