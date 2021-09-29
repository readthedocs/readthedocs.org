#!/bin/bash
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
# **the script must be ran from a builder (build-default or build-large)** and
# it's required to set the following environment variables for an IAM user with
# permissions on ``build-tools`` S3's bucket:
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
# ARGUMENTS
#
#  $1 is the name of the tool (found by `asdf plugin list all`)
#  $2 is the version of the tool (found by `asdf list all <tool>`)

set -e

# Define variables
SLEEP=350
OS="ubuntu-20.04"
TOOL=$1
VERSION=$2

# https://stackoverflow.com/questions/59895/how-can-i-get-the-source-directory-of-a-bash-script-from-within-the-script-itsel
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Spin up a container with the Ubuntu 20.04 LTS image
CONTAINER_ID=$(docker run --user docs --rm --detach --volume ${SCRIPT_DIR}/python-build.diff:/tmp/python-build.diff readthedocs/build:$OS sleep $SLEEP)
echo "Running all the commands in Docker container: $CONTAINER_ID"

# Install the tool version requested
if [[ $TOOL == "python" ]]
then
    docker exec --env PYTHON_CONFIGURE_OPTS="--enable-shared" $CONTAINER_ID asdf install $TOOL $VERSION
else
    docker exec $CONTAINER_ID asdf install $TOOL $VERSION
fi

# Set the default version and reshim
docker exec $CONTAINER_ID asdf global $TOOL $VERSION
docker exec $CONTAINER_ID asdf reshim $TOOL

# Install dependencies for this version
if [[ $TOOL == "python" ]] && [[ ! $VERSION =~ (^miniconda.*|^mambaforge.*) ]]
then
    RTD_PIP_VERSION=21.2.4
    RTD_SETUPTOOLS_VERSION=57.4.0
    RTD_VIRTUALENV_VERSION=20.7.2

    if [[ $VERSION == "2.7.18" ]]
    then
        # Pin to the latest versions supported on Python 2.7
        RTD_PIP_VERSION=20.3.4
        RTD_SETUPTOOLS_VERSION=44.1.1
        RTD_VIRTUALENV_VERSION=20.7.2
    fi
    docker exec $CONTAINER_ID $TOOL -m pip install -U pip==$RTD_PIP_VERSION setuptools==$RTD_SETUPTOOLS_VERSION virtualenv==$RTD_VIRTUALENV_VERSION
fi

# Compress it as a .tar.gz without include the full path in the compressed file
docker exec $CONTAINER_ID tar --create --gzip --directory=/home/docs/.asdf/installs/$TOOL --file=$OS-$TOOL-$VERSION.tar.gz $VERSION

# Copy the .tar.gz from the container to the host
docker cp $CONTAINER_ID:/home/docs/$OS-$TOOL-$VERSION.tar.gz .

# Kill the container
docker container kill $CONTAINER_ID

# Upload the .tar.gz to S3
AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:9000}"
AWS_BUILD_TOOLS_BUCKET="${AWS_BUILD_TOOLS_BUCKET:-build-tools}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-admin}" \
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-password}" \
aws --endpoint-url $AWS_ENDPOINT_URL s3 cp $OS-$TOOL-$VERSION.tar.gz s3://$AWS_BUILD_TOOLS_BUCKET

# Delete the .tar.gz file from the host
rm $OS-$TOOL-$VERSION.tar.gz
