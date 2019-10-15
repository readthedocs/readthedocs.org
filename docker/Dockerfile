FROM python:3.6.7-alpine

ARG GITHUB_TOKEN

WORKDIR /usr/src/app

COPY requirements docker/requirements

RUN apk update && \
  apk add --no-cache git build-base libxml2 libxml2-dev libxslt-dev \
  openjpeg-dev tiff-dev musl-dev postgresql-dev libffi-dev openssh-client && \
  pip install --upgrade pip


COPY docker/scripts/createsuperuser.py docker/scripts/

RUN mkdir checkouts
RUN git clone https://${GITHUB_TOKEN}@github.com/readthedocs/readthedocs.org

# FIXME: Remove orjson that does not compile on Alpine Linux
RUN sed -i '/orjson==2.0.7/d' readthedocs.org/requirements/pip.txt

RUN pip install --no-cache-dir -r readthedocs.org/requirements/deploy.txt

RUN git clone https://${GITHUB_TOKEN}@github.com/readthedocs/readthedocs-ext
RUN pip install --no-cache-dir -e readthedocs-ext

# We need the latest version to use Azurite
# 1.7.2 introduced AZURE_EMULATED_MODE and AZURE_CUSTOM_DOMAIN
# https://github.com/jschneier/django-storages/blob/master/CHANGELOG.rst#172-2019-09-10
RUN pip install -U django-storages[azure]

WORKDIR /usr/src/app/checkouts/readthedocs.org
