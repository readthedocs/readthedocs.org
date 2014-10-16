#
# readthedocs.org - webapp
#

FROM    ubuntu:14.10
MAINTAINER  dnephin@gmail.com

RUN     apt-get update && apt-get install -y \
            python-dev \
            python-pip \
            python-virtualenv \
            git \
            build-essential \
            libxml2-dev \
            libxslt1-dev \
            zlib1g-dev \
            libpq-dev

ADD     deploy_requirements.txt /rtd/deploy_requirements.txt
ADD     pip_requirements.txt    /rtd/pip_requirements.txt
ADD     deploy  /rtd/deploy
WORKDIR /rtd
RUN     virtualenv venv && venv/bin/pip install \
            -r deploy_requirements.txt \
            --find-links /rtd/deploy/wheels

ADD     .   /rtd
RUN     mkdir /rtd/user_builds
RUN     mkdir /rtd/readthedocs/webapp_settings/

EXPOSE  8000

ENV     PYTHONPATH  /rtd/
WORKDIR /rtd/readthedocs

# TODO: use gunicorn
CMD     ../venv/bin/python ./manage.py runserver 0.0.0.0:8000
