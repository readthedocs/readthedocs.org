==================
Build Environments
==================

Read the Docs uses container virtualization to encapsulate documentation build
processes. Each build spins up a new virtual machine using our base image,
which is an image with the minimum necessary components required to build
documentation. Virtual machines are limiting in CPU time and memory, which aims
to reduce excessive usage of build resources.

Setup
-----

Build environments use `Docker`_ to handle container virtualization. To perform
any development on the Docker build system, you will need to set up `Docker`_ on
your host system. Setup of Docker will vary by system, and so is out of the
scope of this documentation.

Once you have Docker set up, you will need to pull down our build image. These
images are found on our `Docker Hub repository`_, the source comes from our
`container image repo`_.

To get started using Docker for build environments, you'll need to pull down at
least one build image. For example, to pull down our latest image::

    docker pull readthedocs/build:latest

The default image used by our build servers is :djangosetting:`DOCKER_IMAGE`.
This would be a good place to start testing as the ``latest`` version could
operate differently. See ``DOCKER_IMAGE`` below for setting this configuration
option.

After this image is downloaded, you can update your settings to use the new
image -- see `Configuration`_.

.. _`Docker`: http://docker.com
.. _`Docker Hub repository`: https://hub.docker.com/r/readthedocs/build/
.. _`container image repo`: https://github.com/rtfd/readthedocs-docker-images

Configuration
-------------

There are several settings used to configure usage of virtual machines:

DOCKER_ENABLE
    True/False value used to enable the Docker build environment.

    Default: :djangosetting:`DOCKER_ENABLE`

DOCKER_LIMITS
    A dictionary of limits to virtual machines. These limits include:

        time
            An integer representing the total allowed time limit (in
            seconds) of build processes. This time limit affects the parent
            process to the virtual machine and will force a virtual machine
            to die if a build is still running after the allotted time
            expires.

        memory
            The maximum memory allocated to the virtual machine. If this
            limit is hit, build processes will be automatically killed.
            Examples: '200m' for 200MB of total memory, or '2g' for 2GB of
            total memory.

    Default: :djangosetting:`DOCKER_LIMITS`

DOCKER_IMAGE
    Tag of a Docker image to use as a base image.

    Default: :djangosetting:`DOCKER_IMAGE`

DOCKER_SOCKET
    URI of the socket to connect to the Docker daemon. Examples include:
    ``unix:///var/run/docker.sock`` and ``tcp://127.0.0.1:2375``.

    Default: :djangosetting:`DOCKER_SOCKET`

DOCKER_VERSION
    Version of the API to use for the Docker API client.

    Default: :djangosetting:`DOCKER_VERSION`
