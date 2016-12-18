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

Once you have Docker set up, you will need to create the base image used for
container creation. The ``base`` image is found in our `container images repo`_.
It is the basic container image supported by our community site.

To get started, create the image using the `docker` command line tool. You can
name the image whatever you like here, ``rtfd-build`` is the default name, but
can be configured in your settings -- see `Configuration`_::

    docker build -t rtfd-build base/

When this process has completed, you should have a working image that Read the
Docs can use to start containers.

.. _`Docker`: http://docker.com
.. _`container images repo`: https://github.com/rtfd/readthedocs-docker-images

Configuration
-------------

There are several settings used to configure usage of virtual machines:

DOCKER_ENABLED
    True/False value used to enable the Docker build environment. Default:
    False

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

DOCKER_IMAGE
    Tag of a Docker image to use as a base image.

DOCKER_SOCKET
    URI of the socket to connect to the Docker daemon. Examples include:
    ``unix:///var/run/docker.sock`` and ``tcp://127.0.0.1:2375``

DOCKER_VERSION
    Version of the API to use for the Docker API client.
