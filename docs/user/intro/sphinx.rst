
Deploying Sphinx on Read the Docs
=================================

.. meta::
   :description lang=en: Hosting Sphinx documentation on Read the Docs.

`Sphinx`_ is a powerful documentation generator that
has many features for writing technical documentation.
Sphinx is written in Python, and supports documentation written in reStructuredText and Markdown.

Minimal configuration required to build an existing Sphinx project on Read the Docs looks like this,
specifying a Python 3.x toolchain on Ubuntu, using the built-in :ref:`sphinx <config-file/v2:sphinx>` command,
and defining the location of the installation requirements:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: ubuntu-24.04
      tools:
        python: "3"

    sphinx:
      configuration: docs/conf.py

    python:
      install:
        - requirements: requirements.txt

.. _Sphinx: https://www.sphinx-doc.org

Quick start
-----------

- If you have an existing Sphinx project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to Sphinx, check out the official `Getting started with Sphinx`_ guide.
- For a step-by-step tutorial on Read the Docs using an example Sphinx project, take a look at the :doc:`/tutorial/index`.

.. _Getting started with Sphinx: https://www.sphinx-doc.org/en/master/usage/quickstart.html

Configuring Sphinx and Read the Docs Addons
-------------------------------------------

For optimal integration with Read the Docs, make the following optional configuration changes to your Sphinx config.

.. contents::
   :depth: 1
   :local:
   :backlinks: none

Set the canonical URL
~~~~~~~~~~~~~~~~~~~~~

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your `html_baseurl`_ to your Read the Docs canonical URL using a
:doc:`Read the Docs environment variable </reference/environment-variables>`:

.. code-block:: py
    :caption: conf.py

    html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

.. _html_baseurl: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_baseurl

Configure Read the Docs search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're using the `Read the Docs Sphinx Theme <https://sphinx-rtd-theme.readthedocs.io/en/stable/>`__,
:doc:`Server side search </server-side-search/index>` already works out of the box.

If you're using a different theme, enable :doc:`Server side search </server-side-search/index>`:

#. Add a snippet of JavaScript:

   .. code-block:: js
      :caption: readthedocs.js

      // Trigger the Read the Docs Addons Search modal when clicking on "Search docs" input from the topnav.
      // NOTE: The selector of the search input may need to be adjusted based on your theme.
      document.querySelector("[role='search'] input").addEventListener("focusin", () => {
         const event = new CustomEvent("readthedocs-search-show");
         document.dispatchEvent(event);
      });

#. Include it in your build:

    .. code-block:: py
        :caption: conf.py

         html_js_files = [
             ("readthedocs.js", {"defer": "defer"}),
         ]

Integrate the Read the Docs version menu into your site navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ref:`flyout-menu:Addons flyout menu` displays differently depending on which Sphinx theme your documentation uses.

- If you're using the `Read the Docs Sphinx Theme <https://sphinx-rtd-theme.readthedocs.io/en/stable/>`__, the :ref:`flyout-menu:Addons flyout menu` is already fully integrated into the theme. Use the theme options `flyout_display <https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html#confval-flyout_display>`__, `version_selector <https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html#confval-version_selector>`__, `language_selector <https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html#confval-language_selector>`__ to configure it.

- If you're using another theme, the flyout menu displays in the bottom right of the docs.

In either case, you can configure the flyout menu sorting and display options in :guilabel:`Settings`, under :guilabel:`Addons`.

Using Markdown with Sphinx
--------------------------

You can use `Markdown using MyST`_ and reStructuredText in the same Sphinx project.
We support this natively on Read the Docs, and you can also use it locally by installing ``myst-parser``:

.. prompt:: bash $

    pip install myst-parser

Then in your ``conf.py``:

.. code-block:: python

   extensions = ["myst_parser"]

You can now continue writing your docs in ``.md`` files and it will work with Sphinx.

.. seealso::

   `Getting started with MyST in Sphinx <https://myst-parser.readthedocs.io/en/latest/sphinx/intro.html>`_
     Learn how to use MyST to write Markdown documentation in your Sphinx project.

   :doc:`/guides/migrate-rest-myst`
     Start writing Markdown in your existing reStructuredText project, or migrate it completely.

.. _Markdown using MyST: https://myst-parser.readthedocs.io/en/latest/using/intro.html

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/full-feature

Demo
    https://test-builds.readthedocs.io/en/full-feature

Further reading
---------------

* `Sphinx documentation`_
* :doc:`RestructuredText primer <sphinx:usage/restructuredtext/basics>`
* `An introduction to Sphinx and Read the Docs for technical writers`_

.. _Sphinx documentation: https://www.sphinx-doc.org/
.. _An introduction to Sphinx and Read the Docs for technical writers: https://www.ericholscher.com/blog/2016/jul/1/sphinx-and-rtd-for-writers/
