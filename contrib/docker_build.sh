#!/bin/sh

username=`id -nu`
uid=`id -u`
gid=`id -g`

version=$1
[ -n "${version}" ] || version="latest"

docker build \
    -t readthedocs/build:dev \
    --build-arg username=${username} \
    --build-arg uid=${uid} \
    --build-arg gid=${gid} \
    --build-arg label=${version} \
    .
