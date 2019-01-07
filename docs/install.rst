Installation
============

Here is a step by step guide on how to install Read the Docs.
It will get you to a point of having a local running instance.

Requirements
------------

First, obtain `Python 3.6`_ and virtualenv_ if you do not already have them.
Using a virtual environment is strongly recommended,
since it will help you to avoid clutter in your system-wide libraries.

Additionally Read the Docs depends on:

* `Git`_ (version >=2.17.0)
* `Mercurial`_ (only if you need to work with mercurial repositories)
* `Pip`_ (version >1.5)
* `Redis`_
* `Elasticsearch`_ (only if you want full support for searching inside the site)

    * Ubuntu users could install this package by following :doc:`/custom_installs/elasticsearch`.

.. note::

    If you plan to import Python 2 projects to your RTD,
    then you'll need to install Python 2 with virtualenv in your system as well.

In order to get all the dependencies successfully installed,
you need these libraries.

.. tabs::
   
   .. tab:: Mac OS

      If you are having trouble on OS X Mavericks
      (or possibly other versions of OS X) with building ``lxml``,
      you probably might need to use Homebrew_ to ``brew install libxml2``,
      and invoke the install with::
      
          CFLAGS=-I/usr/local/opt/libxml2/include/libxml2 \
          LDFLAGS=-L/usr/local/opt/libxml2/lib \
          pip install -r requirements.txt

   .. tab:: Ubuntu

      Install::

         sudo apt-get install build-essential
         sudo apt-get install python-dev python-pip python-setuptools
         sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

      If you don't have redis installed yet, you can do it with::
         
         sudo apt-get install redis-server

   .. tab:: CentOS/RHEL 7

      Install::

         sudo yum install python-devel python-pip libxml2-devel libxslt-devel

   .. tab:: Other OS

      On other operating systems no further dependencies are required,
      or you need to find the proper equivalent libraries.


.. _Python 3.6: http://www.python.org/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _Git: http://git-scm.com/
.. _Mercurial: https://www.mercurial-scm.org/
.. _Pip: https://pip.pypa.io/en/stable/
.. _Homebrew: http://brew.sh/
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Redis: https://redis.io/


Get and run Read the Docs
-------------------------

Clone the repository somewhere on your disk and enter to the repository::

    git clone https://github.com/rtfd/readthedocs.org.git
    cd readthedocs.org

Create a virtual environment and activate it::

    virtualenv venv
    source venv/bin/activate

Next, install the dependencies using ``pip``
(make sure you are inside of the virtual environment)::

    pip install -r requirements.txt

This may take a while, so go grab a beverage.
When it's done, build the database::

    python manage.py migrate

Then create a superuser account for Django::

    python manage.py createsuperuser

Now let's properly generate the static assets::

    python manage.py collectstatic

Now you can optionally load a couple users and test projects::

    python manage.py loaddata test_data

.. note::

    If you do not opt to install test data, you'll need to create an account for
    API use and set ``SLUMBER_USERNAME`` and ``SLUMBER_PASSWORD`` in order for
    everything to work properly.
    This can be done by using ``createsuperuser``, then attempting a manual login to
    create an ``EmailAddress`` entry for the user, then you can use ``shell_plus`` to
    update the object with ``primary=True``, ``verified=True``.

Finally, you're ready to start the web server::

    python manage.py runserver

Visit http://127.0.0.1:8000/ in your browser to see how it looks;
you can use the admin interface via http://127.0.0.1:8000/admin
(logging in with the superuser account you just created).

For builds to properly work as expected,
it is necessary the port you're serving on
(i.e. ``python manage.py runserver 0.0.0.0:8080``)
match the port defined in ``PRODUCTION_DOMAIN``.
You can use ``readthedocs/settings/local_settings.py`` to modify this
(by default, it's ``localhost:8000``).

While the web server is running,
you can build the documentation for the latest version of any project using the ``update_repos`` command.
For example to update the ``pip`` repo::

    python manage.py update_repos pip

.. note::

    If you have problems building successfully a project,
    probably is because some missing libraries for ``pdf`` and ``epub`` generation.
    You can uncheck this on the advanced settings of your project.

What's available
----------------

After registering with the site (or creating yourself a superuser account),
you will be able to log in and view the `dashboard <http://localhost:8000/dashboard/>`_.

Importing your docs
~~~~~~~~~~~~~~~~~~~

One of the goals of readthedocs.org is to make it easy for any open source developer to get high quality hosted docs with great visibility!
Simply provide us with the clone URL to your repo, we'll pull your code, extract your docs, and build them!

We make available a post-commit webhook that can be configured to update the docs whenever you commit to your repo.
See our :doc:`/intro/import-guide` page to learn more.

Further steps
-------------

By now you can trigger builds on your local environment, 
to encapsulate the build process inside a Docker container,
see :doc:`development/buildenvironments`.

For building this documentation,
see :doc:`docs`.

And for setting up for the front end development, see :doc:`development/standards`.
