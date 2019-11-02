Installation
============

.. meta::
   :description lang=en: Install a local development instance of Read the Docs with our step by step guide.

Here is a step by step guide on how to install Read the Docs.
It will configure a local instance that can build and host documentation.

Requirements
------------

First, obtain `Python 3.6`_ and virtualenv_ if you do not already have them.
Using a virtual environment is strongly recommended,
since it will help you to avoid clutter in your system-wide libraries.

.. warning::
    Python 3.7 and newer are not currently supported. Some dependencies of Read
    the Docs do not work with these versions. Python 3.6 is the latest supported
    Python version.

Additionally, Read the Docs depends on:

* `Git`_ (version >=2.17.0)
* `Mercurial`_ (only if you need to work with Mercurial repositories)
* `Pip`_ (version >1.5)
* `Redis`_
* `Elasticsearch`_ (only if you want full support for searching inside the site)

    * Follow :doc:`/development/search` documentation for more instruction.

.. note::

    To build Python 2.x or 3.x projects in Read the Docs, make sure you install
    the appropriate Python version (2.x or 3.x) with virtualenv.

In order to install all the dependencies successfully, you need additional
libraries:

.. tabs::

   .. tab:: Mac OS

      If you are having trouble on OS X Mavericks (or possibly other versions of
      MacOS) building ``lxml``, you might need to use Homebrew_ to upgrade the
      XML library:

      .. code:: console

         $ brew install libxml2
         $ export CFLAGS=-I/usr/local/opt/libxml2/include/libxml2
         $ export LDFLAGS=-L/usr/local/opt/libxml2/lib
         $ pip install -r requirements.txt

   .. tab:: Ubuntu 18.04

      .. note::
         Ubuntu 18.04 LTS is the only version of Ubuntu that the core team
         supports. Newer releases should work, however might require slightly
         different packages and/or additional steps.

      Install the needed development libraries and headers with:

      .. code:: console

         $ sudo apt-get install build-essential
         $ sudo apt-get install python-dev python-pip python-setuptools
         $ sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

      If you don't have redis installed yet, you can do it with:

      .. code:: console

         $ sudo apt-get install redis-server

   .. tab:: CentOS/RHEL 7

      .. note::
         CentOS/RHEL and variants are not officially supported by the core team.

      Install the needed development libraries and headers with:

      .. code:: console

         $ sudo yum install python-devel python-pip libxml2-devel libxslt-devel

   .. tab:: Other OS

      Other operating systems and distributions might require additional steps
      to install Read the Docs. These are outside the scope of this document and
      are not officially supported by the core team.

Database
~~~~~~~~

By default, SQLite is used as the database backend and does not need any
additional configuration or setup steps. You will need to set up a database if
you run into problems during database migrations, or if you are using an
unsupported database.

.. tabs::

    .. tab:: SQLite

        .. warning::
            Read the Docs uses ``Django 1.11.x``, which has a `bug`_ that breaks
            database migrations if an unsupported version of the SQLite library
            is used. SQLite versions ``3.26.0`` and newer are not supported.

        If an unsupported version of the SQLite library is installed, you will
        need to configure a different database or install an older version of
        SQLite. We recommend installing PostgreSQL.

    .. tab:: PostgreSQL

        PostgreSQL is the recommended database backend, however SQLite will work
        for most development cases. You'll need to make sure you have the
        necessary Python PostgreSQL dependencies and the correct database
        settings configured in order to use a PostgreSQL server instance.

        .. tabs::

            .. tab:: On your host system

                Installation of PostgreSQL on your host system is outside the
                scope of this document. Most operating systems or Linux
                distributions have an easily installable version of PostgreSQL
                server.

            .. tab:: Docker

                If you have Docker installed already, you can run a server
                inside a container.

                .. warning::
                    This example is not meant as a thorough installation guide
                    and is only recommended for development purposes.

                .. code:: console

                    $ docker pull postgres:10-alpine
                    $ docker run -d --name postgres -p 5432:5432 postgres:10-alpine
                    $ docker exec postgres createuser -h 127.0.0.1 -U postgres docs
                    $ docker exec postgres createdb -h 127.0.0.1 -U postgres -O docs docs

                To connect to the server:

                :Host: ``127.0.0.1``
                :User: ``docs``
                :Database: ``docs``
                :Password: None

        You'll need to install the ``psycopg2`` Python package to allow Django to
        use the database:

        .. code:: console

            $ python -m pip install psycopg2

        This requires the PostgreSQL client libraries to be installed on your
        system. If you do not have these, you can instead use:

        .. code:: console

            $ python -m pip install psycopg2-binary

        Finally, you'll need to change the :std:setting:`DATABASES` Django
        setting using a ``local_settings.py`` file after cloning the Read the
        Docs repository. Configure this setting to use your new PostgreSQL
        instance before configuring a user or running migrations.


.. _Python 3.6: http://www.python.org/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _Git: http://git-scm.com/
.. _Mercurial: https://www.mercurial-scm.org/
.. _Pip: https://pip.pypa.io/en/stable/
.. _Homebrew: http://brew.sh/
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Redis: https://redis.io/
.. _bug: https://code.djangoproject.com/ticket/29182


Get and run Read the Docs
-------------------------

Clone the repository somewhere on your disk and enter to the repository:

.. code:: console

    $ git clone --recurse-submodules https://github.com/readthedocs/readthedocs.org.git
    $ cd readthedocs.org

Create a virtual environment and activate it:

.. code:: console

    $ virtualenv --python=python3 venv
    $ source venv/bin/activate

Next, install the dependencies using ``pip``
(make sure you are inside of the virtual environment):

.. code:: console

    $ pip install -r requirements.txt

This may take a while, so go grab a beverage.
When it's done, build the database:

.. code:: console

    $ python manage.py migrate

Then create a superuser account for Django:

.. code:: console

    $ python manage.py createsuperuser

Now let's properly generate the static assets:

.. code:: console

    $ python manage.py collectstatic

Now you can optionally load a couple users and test projects:

.. code:: console

    $ python manage.py loaddata test_data

.. note::

    If you do not opt to install test data, you'll need to create an account for
    API use and set ``SLUMBER_USERNAME`` and ``SLUMBER_PASSWORD`` in order for
    everything to work properly.
    This can be done by using ``createsuperuser``, then attempting a manual login to
    create an ``EmailAddress`` entry for the user, then you can use ``shell_plus`` to
    update the object with ``primary=True``, ``verified=True``.

Finally, you're ready to start the web server:

.. code:: console

    $ python manage.py runserver

Visit http://localhost:8000/ in your browser to see how it looks.
You can use the admin interface via http://localhost:8000/admin
(logging in with the superuser account you just created).

For builds to properly work as expected,
it is necessary that the port you're serving on
(i.e. ``python manage.py runserver 8000``)
matches the port defined in ``PRODUCTION_DOMAIN``.
You can use ``readthedocs/settings/local_settings.py`` to modify this
(by default, it's ``localhost:8000``).

While the web server is running, you can build the documentation for the latest
version of any project using the ``update_repos`` command. For example to
update the ``pip`` repo:

.. code:: console

    $ python manage.py update_repos pip

.. note::

    If you have problems building a project successfully,
    it is probably because of some missing libraries for ``pdf`` and ``epub`` generation.
    You can uncheck this on the advanced settings of your project.

Next steps
----------

After registering with the site (or creating yourself a superuser account),
you will be able to log in and view the `dashboard <http://localhost:8000/dashboard/>`_.
You are now ready to start building docs and contributing to Read the Docs!

Importing your docs
~~~~~~~~~~~~~~~~~~~

You can start testing your instance by building some of the example
documentation projects that were configured when you imported the fixture data,
or you can import new projects. You can also import and Sphinx or Mkdocs
project, especially projects that have already set up their repository on
https://readthedocs.org.

Contributing
~~~~~~~~~~~~

By now you can trigger builds on your local environment, and should be able to
make changes to most of Read the Docs. See our docs on :doc:`contributing to
Read the Docs </contribute>` for more information on how to help.

Additionally, there is more configuration you can do if you would like to
contribute to all parts of Read the Docs.

Use Docker for builds
    By default, Read the Docs will use your local environment and your system
    binaries to build projects. However, this means that you can only use Python
    versions that you have installed on your host system, and it means that PDF
    output likely doesn't work unless you have all of the LaTeX dependencies
    installed.

    To build projects inside using Docker, and more closely replicate how Read
    the Docs builds projects for our community site, see
    :doc:`buildenvironments`.

Index to Elasticsearch
    Search results might be different on your instance if you did not set up
    `Elasticsearch`_. Follow the :doc:`search development guide </development/search>`
    for more instruction.

Make front end and UI changes
    To set up for front end development, see :doc:`front-end`.

Make documentation updates
    To contribute to this documentation, see :doc:`docs`.
