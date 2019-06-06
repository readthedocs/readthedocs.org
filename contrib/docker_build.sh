#!/bin/sh

uid=`id -u`
gid=`id -g`

version=$1
[ -n "${version}" ] || version="latest"

docker build \
    --no-cache \
    -t readthedocs/build-dev:${version} \
    --build-arg uid=${uid} \
    --build-arg gid=${gid} \
    --build-arg label=${version} \
    .
