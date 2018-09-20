# FROM readthedocs/build:latest
FROM python:2.7.13
# FROM python:3.6.1

RUN set -ex; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        elasticsearch \
        redis-server \
    ; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app
COPY requirements /usr/src/app/requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app/

RUN python manage.py migrate
RUN python manage.py createsuperuser --noinput \
      --username root \
      --email dev@localhost
RUN python manage.py collectstatic --noinput
RUN python manage.py loaddata test_data

CMD python manage.py runserver

EXPOSE 8000
