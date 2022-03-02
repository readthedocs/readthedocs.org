Allow Installation of System Packages
=====================================

Currently we don't allow executing arbitrary commands in the build process.
The more common use case is to install extra dependencies.

.. contents::
   :local:
   :depth: 3

Current status
--------------

There is a workaround when using Sphinx to run arbitrary commands,
this is executing the commands inside the ``conf.py`` file.
There isn't a workaround for MkDocs, but this problem is more common in Sphinx,
since users need to install some extra dependencies in order to use autodoc or build Jupyter Notebooks.

However, installation of some dependencies require root access,
or are easier to install using ``apt``.
Most of the CI services allow to use ``apt`` or execute any command with ``sudo``,
so users are more familiar with that workflow.

Some users use Conda instead of pip to install dependencies in order to avoid these problems,
but not all pip users are familiar with Conda, or want to migrate to Conda just to use Read the Docs.

Security concerns
-----------------

Builds are run in a Docker container,
but the app controlling that container lives in the same server.
Allowing to execute arbitrary commands with super user privileges may introduce some security issues.

Exposing ``apt install``
------------------------

For the previous reasons we won't allow to execute arbitrary commands with root (yet),
but instead allow only to install extra packages using ``apt``.

We would expose this through the config file.
Users will provide a list of packages to install, and under the hook we would run:

- ``apt update -y``
- ``apt install -y {packages}``

These commands will be run before the Python setup step and after the clone step.

.. note::

   All package names must be validated to avoid injection of extra options
   (like ``-v``).

Using ``docker exec``
---------------------

Currently we use ``docker exec`` to execute commands in a running container.
This command also allows to pass a user which is used to run the commands (#8058_).
We can run the ``apt`` commands in our current containers using a super user momentarily.

.. _#8058: https://github.com/readthedocs/readthedocs.org/pull/8058

Config file
-----------

The config file can add an additional mapping ``build.apt_packages`` to a list of packages to install.

.. code-block:: yaml

   version: 2

   build:
     apt_packages:
        - cmatrix
        - mysql-server

.. note::

   Other names that were considered were:

   - ``build.packages``
   - ``build.extra_packages``
   - ``build.system_packages``

   These were rejected to avoid confusion with existing keys,
   and to be explicit about the type of package.

Possible problems
-----------------

- Some users may require to pass some additional flags or install from a ppa.
- Some packages may require some additional setup after installation.

Other possible solutions
------------------------

- We can allow to run the containers as root doing something similar to what Travis does:
  They have one tool to convert the config file to a shell script (travis-build_),
  and another that spins a docker container, executes that shell script and streams the logs back (travis-worker_).

  .. _travis-build: https://github.com/travis-ci/travis-build
  .. _travis-worker: https://github.com/travis-ci/worker

- A similar solution could be implemented using `AWS Lambda`_.

  .. NOTE: Haven't done much research around this,
     but I remember David mentioned this a time ago.

  .. _AWS Lambda: https://aws.amazon.com/lambda/

This of course would require a large amount of work,
but may be useful for the future.
