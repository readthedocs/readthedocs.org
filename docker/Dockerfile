FROM ubuntu:18.04

ARG GITHUB_TOKEN

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

WORKDIR /usr/src/app

RUN apt-get -y update
RUN apt-get -y install \
        curl \
        g++ \
        git-core \
        libevent-dev \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        build-essential \
        python3-pip \
        python3-dev \
        postgresql-client \
        libmysqlclient-dev \
        libfreetype6 \
        libjpeg-dev \
        sqlite

RUN pip3 install --upgrade pip

COPY docker/scripts/createsuperuser.py docker/scripts/

RUN mkdir checkouts; cd checkouts

COPY requirements readthedocs.org/requirements

# We need the latest version to use Azurite
# 1.7.2 introduced AZURE_EMULATED_MODE and AZURE_CUSTOM_DOMAIN
# https://github.com/jschneier/django-storages/blob/master/CHANGELOG.rst#172-2019-09-10
RUN sed -i '/django-storages==1.7.1/d' readthedocs.org/requirements/pip.txt

RUN pip install --no-cache-dir -r readthedocs.org/requirements/docker.txt

# We clone the -ext here only to install the requirements at this point.
# -ext is also mounted as volume from the upper directory
RUN git clone https://${GITHUB_TOKEN}@github.com/readthedocs/readthedocs-ext
RUN pip install --no-cache-dir -e readthedocs-ext

# We need the latest version to use Azurite
# 1.7.2 introduced AZURE_EMULATED_MODE and AZURE_CUSTOM_DOMAIN
# https://github.com/jschneier/django-storages/blob/master/CHANGELOG.rst#172-2019-09-10
RUN pip install --no-cache-dir -U django-storages[azure]==1.7.2

# Avoid incompatibility about
# TypeError: __init__() got an unexpected keyword argument 'token_credential'
RUN pip install --no-cache-dir -U azure-storage-blob==1.5.0
RUN pip install --no-cache-dir -U azure-storage-common==1.4.2

WORKDIR /usr/src/app/checkouts/readthedocs.org
