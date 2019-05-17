#!/bin/sh

username=`id -nu`
uid=`id -u`
gid=`id -g`

docker build \
    -t readthedocs/build:latest-dev \
    --build-arg uid=${uid} \
    --build-arg gid=${gid} \
    .
