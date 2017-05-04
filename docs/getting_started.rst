Getting Started
===============

This document will show you how to get up and running with Read the Docs.
You will have your docs imported on Read the Docs in 5 minutes,
displayed beautifully for the world.

If you are already using Sphinx or Markdown for your docs, skip ahead to
:ref:`import-docs`.

Write Your Docs
---------------

You have two options for formatting your documentation:

* :ref:`in-rst`
* :ref:`in-markdown`

.. _in-rst:

In reStructuredText
~~~~~~~~~~~~~~~~~~~

There is `a screencast`_ that will help you get started if you prefer.

Sphinx_ is a tool that makes it easy to create beautiful documentation.
Assuming you have Python_ already, `install Sphinx`_::

    $ pip install sphinx sphinx-autobuild

Create a directory inside your project to hold your docs::

    $ cd /path/to/project
    $ mkdir docs

Run ``sphinx-quickstart`` in there::

    $ cd docs
    $ sphinx-quickstart

This quick start will walk you through creating the basic configuration; in most cases, you
can just accept the defaults. When it's done, you'll have an ``index.rst``, a
``conf.py`` and some other files. Add these to revision control.

Now, edit your ``index.rst`` and add some information about your project.
Include as much detail as you like (refer to the reStructuredText_ syntax
or `this template`_ if you need help). Build them to see how they look::

    $ make html

.. note:: You can use ``sphinx-autobuild`` to auto-reload your docs. Run ``sphinx-autobuild . _build_html`` instead.

Edit your files and rebuild until you like what you see, then commit your changes and push to your public repository.
Once you have Sphinx documentation in a public repository, you can start using Read the Docs.

.. _in-markdown:

In Markdown
~~~~~~~~~~~

You can use Markdown and reStructuredText in the same Sphinx project.
We support this natively on Read the Docs, and you can do it locally::

    $ pip install recommonmark

Then in your ``conf.py``:

.. code-block:: python

    from recommonmark.parser import CommonMarkParser

    source_parsers = {
        '.md': CommonMarkParser,
    }

    source_suffix = ['.rst', '.md']

.. note:: Markdown doesn't support a lot of the features of Sphinx,
          like inline markup and directives. However, it works for
          basic prose content. reStructuredText is the preferred
          format for technical documentation, please read `this blog post`_
          for motivation.

.. _this blog post: http://ericholscher.com/blog/2016/mar/15/dont-use-markdown-for-technical-docs/

.. _connect-account:

Sign Up and Connect an External Account
---------------------------------------

.. TODO Update this with GitLab support later

If you are going to import a repository from GitHub or Bitbucket, you should
connect your account to your provider first. Connecting your account allows for
easier importing and enables Read the Docs to configure your repository webhooks
automatically.

To connect your account, got to your *Settings* dashboard and select *Connected
Services*. From here, you'll be able to connect to your GitHub or Bitbucket
account. This process will ask you to authorize a connection to Read the Docs,
that allows us to read information about and clone your repositories.

.. _import-docs:

Import Your Docs
----------------

To import a repository, visit your dashboard_ and click Import_.

If you have a connected account, you will see a list of your repositories that
we are able to import. To import one of these projects, just click the import
icon next to the repository you'd like to import. This will bring up a form that
is already filled with your project's information. Feel free to edit any of
these properties, and the click **Next** to build your documentation.

Manually Import Your Docs
~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not have a connected account, you will need select **Import Manually**
and enter the information for your repository yourself. You will also need to
manually configure the webhook for your repository as well. When importing your
project, you will be asked for the repository URL, along with some other
information for you new project. The URL is normally the URL or path name you'd
use to checkout, clone, or branch your repository. Some examples:

* Git: ``http://github.com/ericholscher/django-kong.git``
* Mercurial: ``https://bitbucket.org/ianb/pip``
* Subversion: ``http://varnish-cache.org/svn/trunk``
* Bazaar: ``lp:pasta``

Add an optional homepage URL and some tags, and then click **Next**.

Once your project is created, you'll need to manually configure the repository
webhook if you would like to have new changesets to trigger builds for your
project on Read the Docs. Go to your project's **Integrations** page to
configure a new webhook, or see :ref:`our steps for webhook creation
<webhook-creation>` for more information on this process.

Within a few seconds your code will automatically be fetched from your public repository,
and the documentation will be built.
Check out our :doc:`builds` page to learn more about how we build your docs,
and to troubleshoot any issues that arise.

Read the Docs will host multiple versions of your code. You can read more about
how to use this well on our :doc:`versions` page.

If you have any more trouble, don't hesitate to reach out to us. The :doc:`support` page has more information on getting in touch.

.. _a screencast: https://www.youtube.com/watch?feature=player_embedded&v=oJsUvBQyHBs
.. _Python: https://www.python.org/
.. _Sphinx: http://sphinx-doc.org/
.. _Markdown: http://daringfireball.net/projects/markdown/syntax
.. _Mkdocs: http://www.mkdocs.org/
.. _install Sphinx: http://sphinx-doc.org/latest/install.html
.. _install Mkdocs: http://www.mkdocs.org/#installation
.. _reStructuredText: http://sphinx-doc.org/rest.html
.. _this template: http://docs.writethedocs.org/writing/beginners-guide-to-docs/#id1
.. _Sign up: http://readthedocs.org/accounts/signup
.. _log in: http://readthedocs.org/accounts/login
.. _dashboard: http://readthedocs.org/dashboard
.. _Import: http://readthedocs.org/dashboard/import
