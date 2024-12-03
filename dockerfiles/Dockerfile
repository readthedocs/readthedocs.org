FROM ubuntu:24.04

ARG GITHUB_USER
ARG GITHUB_TOKEN

ENV DEBIAN_FRONTEND noninteractive
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get -y update
RUN apt-get -y install \
        curl \
        g++ \
        gettext \
        git-core \
        libevent-dev \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        locales \
        build-essential \
        python3-pip \
        python3-dev \
        postgresql-client \
        libmysqlclient-dev \
        libfreetype6 \
        libjpeg-dev \
        sqlite3 \
        netcat-traditional \
        telnet \
        lsb-release \
        npm \
        rclone

# Dependencies for django-allauth SAML support.
# See:
# - https://github.com/SAML-Toolkits/python3-saml#installation
# - https://github.com/xmlsec/python-xmlsec#linux-debian
RUN apt-get -y install \
      pkg-config \
      libxml2-dev \
      libxmlsec1-dev \
      libxmlsec1-openssl

# Gets the MinIO mc client used to add buckets upon initialization
# If this client should have issues running inside this image, it is also
# fine to defer it to a separate image.
# The current minio/mc Docker image could be a lot smaller
RUN curl --disable https://dl.min.io/client/mc/release/linux-amd64/archive/mc.RELEASE.2022-06-11T21-10-36Z -o /usr/bin/mc && \
    chmod +x /usr/bin/mc

RUN npm install -g nodemon

# Uncomment en_US.UTF-8 locale and generate it
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

# Install ``uv`` package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"
# Explicitly set the name of the virtual environment directory,
# so it doesn't collide with a virtual environment created outside of the container.
ENV VIRTUAL_ENV="/.venv"
RUN uv venv $VIRTUAL_ENV

# Ensure that ``python`` is in the PATH so that ``./manage.py`` works
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /tmp

ARG PRUNE_PACKAGE_CACHE=0
COPY requirements/docker.txt docker.txt
RUN uv pip sync docker.txt

# Install readthedocs-ext only if GITHUB_TOKEN is provided
WORKDIR /usr/src/app/checkouts/
RUN if [ -n "$GITHUB_TOKEN" ] ; \
        then \
        git clone --depth 1 https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/readthedocs/readthedocs-ext ; \
        uv pip install --no-cache-dir -e readthedocs-ext ; \
        fi

RUN git clone --depth 1 https://github.com/readthedocs/ext-theme ; \
    uv pip install --no-cache-dir -e ext-theme

# Required by polymorphic
RUN uv pip install --no-cache-dir -U setuptools

WORKDIR /usr/src/app/checkouts/readthedocs.org
