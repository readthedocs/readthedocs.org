Installation
=============

Installing RTD is pretty simple. Here is a step by step plan on how to do it.

First, obtain Python_ and virtualenv_ if you do not already have them. Using a
virtual environment will make the installation easier, and will help to avoid
clutter in your system-wide libraries. You will also need Git_ in order to
clone the repository.

.. _Python: http://www.python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Git: http://git-scm.com/

Once you have these, create a virtual environment somewhere on your disk, then
activate it::

    virtualenv rtd
    cd rtd
    source bin/activate

Create a folder in here, and clone the repository::

    mkdir checkouts
    cd checkouts
    git clone http://github.com/rtfd/readthedocs.org.git

Next, install the dependencies using ``pip`` (included with virtualenv_)::

    cd readthedocs.org
    pip install -r pip_requirements.txt

This may take a while, so go grab a beverage. When it's done, build your
database::

    ./manage.py syncdb

This will prompt you to create a superuser account for Django. Do that. Then::

    ./manage.py migrate

If you like, you can load up some test projects::

    ./manage.py loaddata test_data
    ./manage.py update_repos

Or you can skip it and start with a fresh, empty site. Finally, you're ready to
start the webserver::

    ./manage.py runserver

Visit http://127.0.0.1:8000/ in your browser to see how it looks; you can use
the admin interface via http://127.0.0.1:8000/admin (logging in with the
superuser account you just created).


What's available
----------------

After registering with the site (or creating yourself a superuser account),
you will be able to log in and view the `dashboard <http://readthedocs.org/dashboard/>`_

From the dashboard you can either create new documentation, or import your existing
docs provided that they are in a git or mercurial repo.


Creating new Docs
^^^^^^^^^^^^^^^^^

One of the goals of `readthedocs.org <http://readthedocs.org>`_ is to make it
easy for any open source developer to get high quality hosted docs with great
visibility!  We provide a simple editor and two sample pages whenever
a new project is created.  From there its up to you to fill in the gaps - we'll
build the docs, give you access to history on every revision of your files,
and we plan on adding more features in the weeks and months to come.


Importing existing docs
^^^^^^^^^^^^^^^^^^^^^^^

The other side of `readthedocs.org <http://readthedocs.org>`_ is hosting the
docs you've already built.  Simply provide us with the clone url to your repo,
we'll pull your code, extract your docs, and build them!  We make available
a post-commit webhook that can be configured to update the docs on our site
whenever you commit to your repo, effectively letting you 'set it and forget it'.

Caveats
-------

We are auto-importing and generating ``conf.py`` files, so projects with special
extensions, themes, or templates won't work correctly. This is because of the
possibility of code execution within the python files. We are planning to support
popular themes and white list users that we trust to have these abilities.
