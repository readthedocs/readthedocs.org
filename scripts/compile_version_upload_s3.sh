#!/bin/sh
#
#
# Script to compile a languge version and upload it to the cache.
#
# This script automates the process to build and upload a Python/Node/Rust/Go
# version and upload it to S3 making it available for the builders. When a
# pre-compiled version is available in the cache, builds are faster because they
# don't have to donwload and compile.
#
# LOCAL DEVELOPMENT ENVIRONMENT
# https://docs.readthedocs.io/en/latest/development/install.html
#
# You can run this script from you local environment to create cached version
# and upload them to MinIO. For this, it's required that you have the MinIO
# instance running before executing this script command:
#
#   inv docker.up
#
#
# PRODUCTION ENVIRONMENT
#
# To create a pre-compiled cached version and make it available on production,
# the script has to be ran from a builder (build-default or build-large) and
# it's required to set the following environment variables for an IAM user with
# permissions on ``language`` S3's bucket:
#
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY
#   AWS_ENDPOINT_URL
#
#
# USAGE
#
#  ./scripts/compile_version_upload.sh python 3.9.6
#
#

# Define variables
SLEEP=1200
OS="ubuntu20"
LANGUAGE=$1
VERSION=$2

# Spin up a container with the Ubuntu 20.04 LTS image
CONTAINER_ID=$(docker run --user docs --detach readthedocs/build:$OS sleep $SLEEP)
echo "Running all the commands in Docker container: $CONTAINER_ID"

# Install the language version requested
if [[ $LANGUAGE -eq "python" ]]
then
    docker exec $CONTAINER_ID --env PYTHON_CONFIGURE_OPTS="--enable-shared" asdf install $LANGUAGE $VERSION
else
    docker exec $CONTAINER_ID asdf install $LANGUAGE $VERSION
fi

# Set the default version and reshim
docker exec $CONTAINER_ID asdf global $LANGUAGE $VERSION
docker exec $CONTAINER_ID asdf reshim $LANGUAGE

# Install dependencies for this version
if [[ $LANGUAGE -eq "python" ]]
then
    docker exec $CONTAINER_ID $LANGUAGE -m pip install -U pip==21.2.4 setuptools==57.4.0 virtualenv==20.7.2
fi

# Compress it as a .tar.gz without include the full path in the compressed file
docker exec $CONTAINER_ID tar --create --verbose --gzip --directory=/home/docs/.asdf/installs/$LANGUAGE --file=$OS-$LANGUAGE-$VERSION.tar.gz $VERSION

# Copy the .tar.gz from the container to the host
docker cp $CONTAINER_ID:/home/docs/$OS-$LANGUAGE-$VERSION.tar.gz .

# Kill the container
docker container kill $CONTAINER_ID

# Upload the .tar.gz to S3
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-admin}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-admin}"
AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:9000}"
AWS_LANGUAGES_BUCKET="${AWS_LANGUAGES_BUCKET:-languages}"
aws --endpoint-url $AWS_ENDPOINT_URL s3 cp $OS-$LANGUAGE-$VERSION.tar.gz s3://$AWS_LANGUAGES_BUCKET

# Delete the .tar.gz file from the host
rm $OS-$LANGUAGE-$VERSION.tar.gz
