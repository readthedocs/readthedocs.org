``llms.txt`` support
====================

The `llms.txt` files describe how large language model crawlers can use your documentation.
They're useful for:

* Signaling which parts of your site should be avoided by AI-focused crawlers.
* Documenting how models can attribute your content.
* Sharing links (like a sitemap) that help LLM-powered crawlers discover content responsibly.

Read the Docs automatically generates one for you with a configuration that works for most projects.
By default, the automatically created ``llms.txt``:

* Hides versions which are set to :ref:`Hidden <versions:Version states>` from being indexed by LLM crawlers.
* Allows crawling of all other versions.

.. warning::

   ``llms.txt`` files are a signal to cooperating crawlers,
   but they aren't a guarantee that your pages will not be ingested.
   If you require *private* documentation, please see :doc:`/commercial/sharing`.

How it works
------------

You can customize this file to add more rules to it.
The ``llms.txt`` file will be served from the **default version** of your project.
This is because the ``llms.txt`` file is served at the top-level of your domain,
so we must choose a version to find the file in.
The **default version** is the best place to look for it.

Tool integration
----------------

Documentation tools will have different ways of generating an ``llms.txt`` file.
We have examples for some of the most popular tools below.

.. tabs::

   .. tab:: Sphinx

      Sphinx uses the `html_extra_path`_ configuration value to add static files to its final HTML output.
      You need to create a ``llms.txt`` file and put it under the path defined in ``html_extra_path``.

   .. tab:: MkDocs

      MkDocs needs the ``llms.txt`` to be at the directory defined by the `docs_dir`_ configuration value.

.. _html_extra_path: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_extra_path
.. _docs_dir: https://www.mkdocs.org/user-guide/configuration/#docs_dir

.. seealso::

   :doc:`/reference/robots`
