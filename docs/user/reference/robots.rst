``robots.txt`` support
======================

The `robots.txt`_ files allow you to customize how your documentation is indexed in search engines.
It's useful for:

* Hiding various pages from search engines
* Disabling certain web crawlers from accessing your documentation
* Disallowing any indexing of your documentation

Read the Docs automatically generates one for you with a configuration that works for most projects.
By default, the automatically created ``robots.txt``:

* Hides versions which are set to :ref:`Hidden <versions:Version states>` from being indexed.
* Allows indexing of all other versions.

.. warning::

   ``robots.txt`` files are respected by most search engines,
   but they aren't a guarantee that your pages will not be indexed.
   Search engines may choose to ignore your ``robots.txt`` file,
   and index your docs anyway.

   If you require *private* documentation, please see :doc:`/commercial/sharing`.

How it works
------------

You can customize this file to add more rules to it.
The ``robots.txt`` file will be served from the **default version** of your project.
This is because the ``robots.txt`` file is served at the top-level of your domain,
so we must choose a version to find the file in.
The **default version** is the best place to look for it.

Tool integration
----------------

Documentation tools will have different ways of generating a ``robots.txt`` file.
We have examples for some of the most popular tools below.

.. tabs::

   .. tab:: Sphinx

      Sphinx uses the `html_extra_path`_ configuration value to add static files to its final HTML output.
      You need to create a ``robots.txt`` file and put it under the path defined in ``html_extra_path``.

   .. tab:: MkDocs

      MkDocs needs the ``robots.txt`` to be at the directory defined by the `docs_dir`_ configuration value.

.. _robots.txt: https://developers.google.com/search/reference/robots_txt
.. _html_extra_path: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_extra_path
.. _docs_dir: https://www.mkdocs.org/user-guide/configuration/#docs_dir

.. seealso::

   :doc:`/guides/technical-docs-seo-guide`
