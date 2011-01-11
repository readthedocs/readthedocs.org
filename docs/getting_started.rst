Getting Started
===============

It's really easy to start using RTD for your project's documentation. This
section shows you how.

If you are already using Sphinx_ for your docs, skip ahead to
:ref:`import-docs`.


Write Your Docs
---------------

Install Sphinx_, and create a directory inside your project to hold your docs::

    $ cd /path/to/project
    $ mkdir docs

Run ``sphinx-quickstart`` in there::

    $ cd docs
    $ sphinx-quickstart

This will walk you through creating the basic configuration; in most cases, you
can just accept the defaults. When it's done, you'll have an ``index.rst``, a
``conf.py`` and some other files. Add these to revision control.

Now, edit your ``index.rst`` and add some information about your project.
Include as much detail as you like (refer to the reStructuredText_ syntax
if you need help). Build them to see how they look::

    $ make html

Edit and rebuild until you like what you see, then commit and/or push your
changes to your public repository.


.. _import-docs:

Import Your Docs
----------------

`Sign up`_ for an account and `log in`_. Visit your dashboard_ and click
Import_ to add your project to the site. Fill in the name and description, then
specify where your repository is located. This is normally the URL or path name
you'd use to checkout, clone, or branch your code. Some examples:

* Git: ``http://github.com/ericholscher/django-kong.git``
* Subversion: ``http://varnish-cache.org/svn/trunk``
* Mercurial: ``https://bitbucket.org/ianb/pip``
* Bazaar: ``lp:pasta``

Add an optional homepage URL and some keywords, then click "Create".

Within a few minutes your code will automatically be fetched from your public
repository, and the documentation will be built.

If you want to keep your code updated as you commit, configure your code repository to hit our `Post Commit Hooks`_. Otherwise your project will get rebuilt nightly.

.. _Sphinx: http://sphinx.pocoo.org/
.. _reStructuredText: http://sphinx.pocoo.org/rest.html
.. _Sign up: http://readthedocs.org/accounts/register
.. _log in: http://readthedocs.org/accounts/login
.. _dashboard: http://readthedocs.org/dashboard
.. _Import: http://readthedocs.org/dashboard/import
.. _Post Commit Hooks: http://readthedocs.org/d
