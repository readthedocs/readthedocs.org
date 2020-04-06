Development Standards
=====================

These are build standards that are adhered to by the core development team while
developing Read the Docs and related services. If you are a new contributor to
Read the Docs, it might a be a good idea to follow these guidelines as well. The
:doc:`standard installation instructions <install>` do cover what it takes to
get started with a local installation of Read the Docs and can be used for local
development by non-core team.

.. warning::

   Take into account that Core team does not offer support on this setup currently.


Core team standards
-------------------

Core team members expect to have a development environment that closely
approximates our production environment, in order to spot bugs and logical
inconsistencies before they make their way to production.

Currently, core team members are migrating to a Docker Compose based
solution that is not yet recommended for contributing to development.

This solution gives us many features that allows us to have an
environment closer to production:

Celery runs as a separate process
    Avoids masking bugs that could be introduced by Celery tasks in a race conditions.

Celery runs multiple processes
    We run celery with multiple worker processes to discover race conditions
    between tasks.

Docker for builds
    Docker is used for a build backend instead of the local host build backend.
    There are a number of differences between the two execution methods in how
    processes are executed, what is installed, and what can potentially leak
    through and mask bugs -- for example, local SSH agent allowing code check
    not normally possible.

Serve documentation under a subdomain
    There are a number of resolution bugs and cross-domain behavior that can
    only be caught by using `USE_SUBDOMAIN` setting.

PostgreSQL as a database
    It is recommended that Postgres be used as the default database whenever
    possible, as SQLite has issues with our Django version and we use Postgres
    in production.  Differences between Postgres and SQLite should be masked for
    the most part however, as Django does abstract database procedures, and we
    don't do any Postgres-specific operations yet.

Celery is isolated from database
    Celery workers on our build servers do not have database access and need
    to be written to use API access instead.

Use NGINX as web server
    All the site is served via NGINX with the ability to change some configuration locally.

Azurite as Django storage backend
    All static and media files are served using Azurite --an emulator of Azure Blob Storage,
    which is the one used in production.

Serve documentation via El Proxito
    Documentation is proxied by NGINX to El Proxito and proxied back to NGINX to be served finally.
    El Proxito is a small application put in front of the documentation to serve files
    from the Django Storage Backend.

Search enabled by default
    Elasticsearch is properly configured and enabled by default.
    Besides, all the documentation indexes are updated after a build is finished.


Set up your environment
-----------------------

After cloning ``readthedocs.org`` repository, you need to


#. install `Docker <https://www.docker.com/>`_ following `their installation guide <https://docs.docker.com/install/>`_.

#. install the requirements from ``common`` submodule:

   .. prompt:: bash

      pip install -r common/dockerfiles/requirements.txt

#. build the Docker image for the servers:

   .. warning::

      This command could take a while to finish since it will download several Docker images.

   .. prompt:: bash

      inv docker.build

   .. tip::

      If you pass ``GITHUB_TOKEN`` environment variable to this command,
      it will add support for readthedocs-ext.

#. pull down Docker images for the builders:

   .. prompt:: bash

      inv docker.pull --only-latest

#. start all the containers:

   .. prompt:: bash

      inv docker.up  --init  # --init is only needed the first time

#. go to http://community.dev.readthedocs.io to access your local instance of Read the Docs.


Working with Docker Compose
---------------------------

We wrote a wrapper with ``invoke`` around ``docker-compose`` to have some shortcuts and
save some work while typing docker compose commands. This section explains these ``invoke`` commands:

``inv docker.build``
    Builds the generic Docker image used by our servers (web, celery, build and proxito).

``inv docker.up``
    Starts all the containers needed to run Read the Docs completely.

    * ``--no-search`` can be passed to disable search
    * ``--init`` is used the first time this command is ran to run initial migrations, create an admin user,
      setup Azurite containers, etc
    * ``--no-reload`` makes all celery processes and django runserver
      to use no reload and do not watch for files changes

``inv docker.shell``
    Opens a shell in a container (web by default).

    * ``--running`` the shell is open in a container that it's already running
    * ``--container`` specifies in which container the shell is open

``inv docker.manage {command}``
    Executes a Django management command in a container.

    .. tip::

       Useful when modifying models to run ``makemigrations``.

``inv docker.down``
    Stops and removes all containers running.

    * ``--volumes`` will remove the volumes as well (database data will be lost)

``inv docker.restart {containers}``
    Restarts the containers specified (automatically restarts NGINX when needed).

``inv docker.attach {container}``
    Grab STDIN/STDOUT control of a running container.

    .. tip::

       Useful to debug with ``pdb``. Once the program has stopped in your pdb line,
       you can run ``inv docker.attach web`` and jump into a pdb session
       (it also works with ipdb and pdb++)

``inv docker.test``
    Runs all the test suites inside the container.

    * ``--arguments`` will pass arguments to Tox command (e.g. ``--arguments "-e py36 -- -k test_api"``)

``inv docker.pull``
    Downloads and tags all the Docker images required for builders.

    * ``--only-latest`` does not pull ``stable`` and ``testing`` images.

Adding a new Python dependency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Docker image for the servers is built with the requirements defined in the ``master`` branch.
In case you need to add a new Python dependency while developing,
you can use the ``common/dockerfiles/entrypoints/common.sh`` script as shortcut.

This script is run at startup on all the servers (web, celery, builder, proxito) which
allows you to test your dependency without re-building the whole image.
To do this, add the ``pip`` command required for your dependency in ``common.sh`` file:

.. code-block:: bash

   # common.sh
   pip install my-dependency==1.2.3

Once the PR that adds this dependency was merged into ``master``, you can rebuild the image
so the dependency is added to the Docker image itself and it's not needed to be installed
each time the container spins up.


Debugging Celery
~~~~~~~~~~~~~~~~

In order to step into the worker process, you can't use ``pdb`` or ``ipdb``, but
you can use ``celery.contrib.rdb``:

.. code-block:: python

    from celery.contrib import rdb; rdb.set_trace()

When the breakpoint is hit, the Celery worker will pause on the breakpoint and
will alert you on STDOUT of a port to connect to. You can open a shell into the container
with ``inv docker.shell celery`` (or ``build``) and then use ``telnet`` or ``netcat``
to connect to the debug process port:

.. prompt:: bash

    nc 127.0.0.1 6900

The ``rdb`` debugger is similar to ``pdb``, there is no ``ipdb`` for remote
debugging currently.
