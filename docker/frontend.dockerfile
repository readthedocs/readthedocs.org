FROM ubuntu:bionic

ENV LANG C.UTF-8

# install latest python and nodejs
RUN apt-get update && \
    apt-get install -y \
      nodejs \
      npm \
      gettext \
      git \
      sudo \
      build-essential \
      python3 \
      python3-dev \
      python3-pip \
      libxml2-dev \
      libxslt1-dev \
      zlib1g-dev

RUN bash -c "pip3 install pip setuptools --upgrade --force-reinstall"
RUN bash -c "pip3 install virtualenv"
RUN bash -c "npm install -g bower"

# RUN adduser --system --shell /bin/bash --home "/repo" rtd

# A volume used to share `pex`/`whl` files and fixtures with docker host
VOLUME /repo

# do the time-consuming base install commands
CMD /bin/bash -c "/usr/local/bin/virtualenv -p python3 rtd \
    && source rtd/bin/activate \
    && cd /repo \
    && pip install -r requirements.txt \
    && npm install \
    && bower --allow-root install \
    && npm run vendor \
    && npm run build"
