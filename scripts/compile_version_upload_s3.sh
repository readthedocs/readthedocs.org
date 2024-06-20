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
# You also need the "awscli" PyPi package in your local Python environment.
#
#   pip install awscli
#
# Note: The version that used is currently simply the latest. If there are issues in
# the future, we can consider fetching the 'mc' client from MinIO instead.
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
SLEEP=900 # Container timeout
OS="${OS:-ubuntu-24.04}" # Docker image name

TOOL=$1
VERSION=$2

# https://stackoverflow.com/questions/59895/how-can-i-get-the-source-directory-of-a-bash-script-from-within-the-script-itsel
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Spin up a container with the latest Ubuntu LTS image
CONTAINER_ID=$(docker run --user docs --rm --detach --volume ${SCRIPT_DIR}/python-build.diff:/tmp/python-build.diff readthedocs/build:$OS sleep $SLEEP)
echo "Running all the commands in Docker container: $CONTAINER_ID"

# TODO: uncomment this to show the asdf version on the build output.
# I'm commenting it now because it's failing for some reason and that I'm not able to solve.
#    OCI runtime exec failed: exec failed: container_linux.go:380: starting container process caused: exec: "asdf": executable file not found in $PATH: unknown
#
# Run "asdf version" from inside the container
# echo -n 'asdf version: '
# docker exec --user root $CONTAINER_ID asdf version

# Update asdf to the latest stable release
docker exec $CONTAINER_ID asdf update
# Update all asdf plugins to the latest commit
# (we require this to be able to compile newer versions)
docker exec $CONTAINER_ID asdf plugin update --all

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
    # Virtualenv 20.21.1 is the latest version that supports Python 3.7 till 3.12.
    # When adding a new version of Python, we need to pin a compatible version of
    # virtualenv for that version of Python.
    RTD_VIRTUALENV_VERSION=20.21.1

    if [[ $VERSION == 2.7.* || $VERSION == 3.6.* ]]
    then
        # Pin to the latest versions supported on Python 2.7 and 3.6.
        RTD_VIRTUALENV_VERSION=20.7.2
    fi
    docker exec $CONTAINER_ID $TOOL -m pip install -U virtualenv==$RTD_VIRTUALENV_VERSION
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

    export AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:9000}"
    export AWS_BUILD_TOOLS_BUCKET="${AWS_BUILD_TOOLS_BUCKET:-build-tools}"
    export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-admin}"
    export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-password}"

    aws --endpoint-url $AWS_ENDPOINT_URL s3 cp $OS-$TOOL-$VERSION.tar.gz s3://$AWS_BUILD_TOOLS_BUCKET

    # Delete the .tar.gz file from the host
    rm $OS-$TOOL-$VERSION.tar.gz
else
    echo "Skip uploading .tar.gz file because it's being run from inside CircleCI."
    echo "It should be uploaded by orbs/aws automatically."
fi
