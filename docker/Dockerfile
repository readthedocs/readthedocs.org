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

RUN mkdir checkouts; cd checkouts

COPY requirements readthedocs.org/requirements

RUN pip install --no-cache-dir -r readthedocs.org/requirements/docker.txt

# We clone the -ext here only to install the requirements at this point.
# -ext is also mounted as volume from the upper directory
RUN git clone --single-branch --depth 1 https://${GITHUB_TOKEN}@github.com/readthedocs/readthedocs-ext
RUN pip install --no-cache-dir -e readthedocs-ext

WORKDIR /usr/src/app/checkouts/readthedocs.org
