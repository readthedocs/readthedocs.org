``llms.txt`` support
====================

The `llms.txt`_ file is a standard for providing LLM-friendly content to AI assistants and other language models.
It allows you to provide a custom file that:

* Gives AI models structured information about your documentation
* Helps AI understand your project's structure and content
* Provides a more focused view of your documentation for AI consumption

Read the Docs supports serving custom ``llms.txt`` files from your documentation.

How it works
------------

The ``llms.txt`` file will be served from the **default version** of your project at ``https://your-project.readthedocs.io/llms.txt``.
This is because the ``llms.txt`` file is served at the top-level of your domain,
so we must choose a version to find the file in.
The **default version** is the best place to look for it.

If you also provide a ``llms-full.txt`` file, Read the Docs will serve it from
``https://your-project.readthedocs.io/llms-full.txt`` using the same rules.

To use this feature:

1. Create a ``llms.txt`` file in your documentation source
2. Configure your documentation tool to include it in the build output
3. Read the Docs will automatically serve it at the root of your domain

.. note::

   The ``llms.txt`` file will only be served if:

   * Your default version is **public**
   * Your default version is **active**
   * Your default version has been **built**
   * The ``llms.txt`` file exists in your build output

Tool integration
----------------

Documentation tools will have different ways of generating a ``llms.txt`` file.
We have examples for some of the most popular tools below.

.. tabs::

   .. tab:: Sphinx

      Sphinx uses the `html_extra_path`_ configuration value to add static files to its final HTML output.
      You need to create a ``llms.txt`` file and put it under the path defined in ``html_extra_path``.

      You can also use the `sphinx-llm`_ extension to automatically generate an ``llms.txt`` file from your documentation.

   .. tab:: MkDocs

      MkDocs needs the ``llms.txt`` to be at the directory defined by the `docs_dir`_ configuration value.

      You can also use the `mkdocs-llmstxt`_ plugin to automatically generate an ``llms.txt`` file from your documentation.

Alternative: Using redirects
-----------------------------

If you want to serve your ``llms.txt`` file from a versioned path (like ``/en/latest/llms.txt``),
you can create an :doc:`exact redirect </guides/redirects>` from ``/llms.txt`` to ``/en/latest/llms.txt``.
This gives you more control over which version serves the file.

.. _llms.txt: https://llmstxt.org/
.. _html_extra_path: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_extra_path
.. _docs_dir: https://www.mkdocs.org/user-guide/configuration/#docs_dir
.. _sphinx-llm: https://pypi.org/project/sphinx-llm/
.. _mkdocs-llmstxt: https://github.com/pawamoy/mkdocs-llmstxt

.. seealso::

   :doc:`/guides/redirects`
