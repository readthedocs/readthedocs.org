#!/bin/bash
#
#
# Script to compile a tool version and upload it to the cache.
#
# This script automates the process to build and upload a Python/Node/Rust/Go
# version and upload it to S3 making it available for the builders. When a
# pre-compiled version is available in the cache, builds are faster because they
# don't have to donwload and compile the requested version.
#
#
# LOCAL DEVELOPMENT ENVIRONMENT
#
# https://docs.readthedocs.io/en/latest/development/install.html
#
# You can run this script from you local environment to create cached version
# and upload them to MinIO (S3 emulator). For this, it's required that you have
# the MinIO instance running before executing this script command:
#
#   inv docker.up
#
#
# PRODUCTION ENVIRONMENT
#
# To create a pre-compiled cached version and make it available on production,
# we use a CircleCI job
# (https://github.com/readthedocs/readthedocs-docker-images/blob/main/.circleci/config.yml)
# It requires to set several environment variables for an IAM user with
# permissions on ``readthedocs(inc)-build-tools-prod`` S3's bucket. These
# variables are defined via the CircleCI UI under the `readthedocs-docker-image`
# project.
#
# Note that if for some reason, you need to run this command *outside CircleCI*
# you can find more information in this comment:
# https://github.com/readthedocs/readthedocs-ops/issues/1155#issuecomment-1082615972
#
# USAGE
#
#  ./scripts/compile_version_upload.sh $TOOL $VERSION
#
# ARGUMENTS
#
#  $TOOL is the name of the tool (found by `asdf plugin list all`)
#  $VERSION is the version of the tool (found by `asdf list all <tool>`)
#
# EXAMPLES
#
#  ./scripts/compile_version_upload.sh python 3.9.7
#  ./scripts/compile_version_upload.sh nodejs 14.17.6

set -e # Stop on errors
set -x # Echo commands

# Define variables
SLEEP=350 # Container timeout
OS="${OS:-ubuntu-22.04}" # Docker image name

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
    if [[ $VERSION == "3.6.15" ]]
    then
        # Special command for Python 3.6.15
        # See https://github.com/pyenv/pyenv/issues/1889#issuecomment-833587851
        docker exec --user root $CONTAINER_ID apt-get update
        docker exec --user root $CONTAINER_ID apt-get install --yes clang
        docker exec --env PYTHON_CONFIGURE_OPTS="--enable-shared" --env CC=clang $CONTAINER_ID asdf install $TOOL $VERSION
    else
        docker exec --env PYTHON_CONFIGURE_OPTS="--enable-shared" $CONTAINER_ID asdf install $TOOL $VERSION
    fi
else
    docker exec $CONTAINER_ID asdf install $TOOL $VERSION
fi

# Set the default version and reshim
docker exec $CONTAINER_ID asdf global $TOOL $VERSION
docker exec $CONTAINER_ID asdf reshim $TOOL

# Install dependencies for this version
#
# TODO: pin all transitive dependencies with pip-tools or similar. We can find
# the current versions by running `pip freeze` in production and stick with them
# for now to avoid changing versions.
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

if [[ -z $CIRCLECI ]]
then
    # Upload the .tar.gz to S3 development environment
    echo "Uploading to dev environment"

    AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:9000}"
    AWS_BUILD_TOOLS_BUCKET="${AWS_BUILD_TOOLS_BUCKET:-build-tools}"
    AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-admin}"
    AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-password}"

    aws --endpoint-url $AWS_ENDPOINT_URL s3 cp $OS-$TOOL-$VERSION.tar.gz s3://$AWS_BUILD_TOOLS_BUCKET

    # Delete the .tar.gz file from the host
    rm $OS-$TOOL-$VERSION.tar.gz
else
    echo "Skip uploading .tar.gz file because it's being run from inside CircleCI."
    echo "It should be uploaded by orbs/aws automatically."
fi
