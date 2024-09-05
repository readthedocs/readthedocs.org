Sphinx
======

.. meta::
   :description lang=en: Hosting Sphinx documentation on Read the Docs.

Sphinx is a powerful documentation generator that
has many features for writing technical documentation.

Minimal configuration required to build an existing Sphinx project on Read the Docs looks like this,
specifying a python 3.x toolchain on Ubuntu, using the built-in :ref:`mkdocs <config-file/v2:sphinx>` command,
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

Quick start
-----------

- If you have an existing Sphinx project you want to host on Read the Docs, check out our :doc:`/intro/import-guide` guide.

- If you're new to Sphinx, check out the official `Getting started with Sphinx`_ guide.

- For a step by step tutorial on Read the Docs using an example Sphinx project, take a look at the :doc:`/tutorial/index`.

.. _Getting started with Sphinx: https://www.sphinx-doc.org/en/master/usage/quickstart.html


Configuring Sphinx and Read the Docs addons
--------------------------------------------------------

For optimal integration with Read the Docs, make the optional following configuration changes to your Spinx config.

.. contents::
   :depth: 1
   :local:
   :backlinks: none

Set the canonical URL
~~~~~~~~~~~~~~~~~~~~~

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your `html_baseurl`_  to your Read the Docs canonical URL using a
:doc:`Read the Docs environment variable </reference/environment-variables>`:

.. code-block:: py
    :caption: conf.py

    html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")


.. _html_baseurl: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_baseurl

Configure Read the Docs search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrate the Read the Docs version menu into your site navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using Markdown with Sphinx
--------------------------

You can use `Markdown using MyST`_ and reStructuredText in the same Sphinx project.
We support this natively on Read the Docs, and you can do it locally:

.. prompt:: bash $

    pip install myst-parser

Then in your ``conf.py``:

.. code-block:: python

   extensions = ["myst_parser"]

You can now continue writing your docs in ``.md`` files and it will work with Sphinx.
Read the `Getting started with MyST in Sphinx`_ docs for additional instructions.

.. _Getting started with MyST in Sphinx: https://myst-parser.readthedocs.io/en/latest/sphinx/intro.html
.. _Markdown using MyST: https://myst-parser.readthedocs.io/en/latest/using/intro.html

Example repository and demo
---------------------------

Example repo::
    https://github.com/readthedocs/test-builds/tree/sphinx-7.0.x

Demo::
    https://test-builds.readthedocs.io/en/sphinx-7.0.x

Further reading
---------------

* `Sphinx documentation`_
* :doc:`RestructuredText primer <sphinx:usage/restructuredtext/basics>`
* `An introduction to Sphinx and Read the Docs for technical writers`_

.. _Sphinx documentation: https://www.sphinx-doc.org/
.. _An introduction to Sphinx and Read the Docs for technical writers: https://www.ericholscher.com/blog/2016/jul/1/sphinx-and-rtd-for-writers/

