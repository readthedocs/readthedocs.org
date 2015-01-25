#
# readthedocs.org - base image
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

ENV     PYTHONPATH  /rtd/
WORKDIR /rtd/readthedocs
