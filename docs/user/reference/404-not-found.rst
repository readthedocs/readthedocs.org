``404 Not Found`` pages
=======================

If you want your project to use a custom or branded ``404 Not Found`` page,
you can put a ``404.html`` or ``404/index.html`` at the top level of your project's HTML output.

How it works
------------

When our servers return a ``404 Not Found`` error,
we check if there is a ``404.html`` or ``404/index.html`` in the root of your project's output.

The following locations are checked, in order:

* ``/404.html`` or ``404/index.html`` in the *current* documentation version.
* ``/404.html`` or ``404/index.html`` in the *default* documentation version.

Tool integration
----------------

Documentation tools will have different ways of generating a ``404.html`` or ``404/index.html`` file.
We have examples for some of the most popular tools below.

.. tabs::

   .. tab:: Sphinx

      We recommend the `sphinx-notfound-page`_ extension,
      which Read the Docs maintains.
      It automatically creates a ``404.html`` page for your documentation,
      matching the theme of your project.
      See its documentation_ for how to install and customize it.

      If you want to create a custom ``404.html``,
      Sphinx uses the `html_extra_path`_ option to add static files to the output.
      You need to create a ``404.html`` file and put it under the path defined in ``html_extra_path``.

      If you are using the ``DirHTML`` builder,
      no further steps are required.
      Sphinx will automatically apply the ``<page-name>/index.html`` folder structure to your 404 page:
      ``404/index.html``.
      Read the Docs also detects 404 pages named this way.

   .. tab:: MkDocs

      MkDocs automatically generates a ``404.html`` which Read the Docs will use.
      However, assets will not be loaded correctly unless you define the `site_url`_ configuration value as your site's
      :doc:`canonical base URL </canonical-urls>`.

.. _sphinx-notfound-page: https://pypi.org/project/sphinx-notfound-page
.. _html_extra_path: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_extra_path
.. _documentation: https://sphinx-notfound-page.readthedocs.io/
.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url
