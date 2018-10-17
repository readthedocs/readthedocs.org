Installation
============

Here is a step by step plan on how to install Read the Docs.
It will get you to a point of having a local running instance.


First, obtain `Python 3.6`_ and virtualenv_ if you do not already have them. Using a
virtual environment will make the installation easier, and will help to avoid
clutter in your system-wide libraries. You will also need Git_ in order to
clone the repository. If you plan to import Python 2.7 project to your RTD then you'll
need to install Python 2.7 with virtualenv in your system as well.


.. _Python 3.6: http://www.python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Git: http://git-scm.com/
.. _Homebrew: http://brew.sh/
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _PostgreSQL: https://www.postgresql.org/
.. _Redis: https://redis.io/

.. note::

    Requires Git version >=2

.. note::

    If you are having trouble on OS X Mavericks (or possibly other versions of
    OS X) with building ``lxml``, you probably might need to use Homebrew_
    to ``brew install libxml2``, and invoke the install with::

        CFLAGS=-I/usr/local/opt/libxml2/include/libxml2 \
        LDFLAGS=-L/usr/local/opt/libxml2/lib \
        pip install -r requirements.txt

.. note::

    Linux users may find they need to install a few additional packages
    in order to successfully execute ``pip install -r requirements.txt``.
    For example, a clean install of Ubuntu 14.04 LTS will require the
    following packages::

        sudo apt-get install build-essential
        sudo apt-get install python-dev python-pip python-setuptools
        sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

    CentOS/RHEL 7 will require::

        sudo yum install python-devel python-pip libxml2-devel libxslt-devel

    Users of other Linux distributions may need to install the equivalent
    packages, depending on their system configuration.

.. note::

   If you want full support for searching inside your Read the Docs
   site you will need to install Elasticsearch_.

   Ubuntu users could install this package by following :doc:`/custom_installs/elasticsearch`.

.. note::

   Besides the Python specific dependencies, you will also need Redis_.

   Ubuntu users could install this package as following::

        sudo apt-get install redis-server


You will need to verify that your pip version is higher than 1.5 you can do this as such::

    pip --version

If this is not the case please update your pip version before continuing::

    pip install --upgrade pip

Once you have these, create a virtual environment somewhere on your disk, then
activate it::

    virtualenv rtd
    cd rtd
    source bin/activate

Create a folder in here, and clone the repository::

    mkdir checkouts
    cd checkouts
    git clone https://github.com/rtfd/readthedocs.org.git

Next, install the dependencies using ``pip`` (included inside of virtualenv_)::

    cd readthedocs.org
    pip install -r requirements.txt

This may take a while, so go grab a beverage. When it's done, build your
database::

    python manage.py migrate

Then please create a superuser account for Django::

    python manage.py createsuperuser

Now let's properly generate the static assets::

    python manage.py collectstatic

By now, it is the right time to load in a couple users and a test project::

    python manage.py loaddata test_data

.. note::

    If you do not opt to install test data, you'll need to create an account for
    API use and set ``SLUMBER_USERNAME`` and ``SLUMBER_PASSWORD`` in order for
    everything to work properly.
    This can be done by using ``createsuperuser``, then attempting a manual login to
    create an ``EmailAddress`` entry for the user, then you can use ``shell_plus`` to
    update the object with ``primary=True``, ``verified=True``.

Finally, you're ready to start the webserver::

    python manage.py runserver

Visit http://127.0.0.1:8000/ in your browser to see how it looks; you can use
the admin interface via http://127.0.0.1:8000/admin (logging in with the
superuser account you just created).

For builds to properly kick off as expected, it is necessary the port
you're serving on (i.e. ``runserver 0.0.0.0:8080``) match the port defined
in ``PRODUCTION_DOMAIN``. You can utilize ``local_settings.py`` to modify this.
(By default, it's ``localhost:8000``)

While the webserver is running, you can build documentation for the latest version of
a project called 'pip' with the ``update_repos`` command.  You can replace 'pip'
with the name of any added project::

    python manage.py update_repos pip

What's available
----------------

After registering with the site (or creating yourself a superuser account),
you will be able to log in and view the `dashboard <http://localhost:8000/dashboard/>`_.

Importing your docs
^^^^^^^^^^^^^^^^^^^

One of the goals of readthedocs.org is to make it easy for any open source developer to get high quality hosted docs with great visibility!
Simply provide us with the clone URL to your repo, we'll pull your code, extract your docs, and build them!
We make available a post-commit webhook that can be configured to update the docs whenever you commit to your repo.
See :doc:`/intro/import-guide` to learn more.
