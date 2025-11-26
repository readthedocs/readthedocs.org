Deploying Zensical on Read the Docs
===================================

.. meta::
   :description lang=en: Learn how to host Zensical sites on Read the Docs.

Zensical_ is a modern static site generator designed to simplify building and
maintaining project documentation. It's built by the creators of Material for MkDocs
and shares the same core design principles and philosophy – batteries included,
easy to use, with powerful customization options.

Minimal configuration is required to build an existing Zensical project on Read the Docs:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
    os: ubuntu-24.04
    tools:
        python: latest
    jobs:
      # We recommend using a requirements file for reproducible builds.
      # This is just a quick example to get started.
      # https://docs.readthedocs.io/page/guides/reproducible-builds.html
      install:
        - pip install zensical
      build:
        html:
          - zensical build
      post_build:
        - mkdir -p $READTHEDOCS_OUTPUT/html/
        - cp --recursive site/* $READTHEDOCS_OUTPUT/html/

.. _Zensical: https://zensical.org/

Quick start
-----------

- If you have an existing Zensical project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to Zensical, check out the official `Getting Started <https://zensical.org/docs/get-started/>`_ guide.

Configuring Zensical and Read the Docs Addons
---------------------------------------------

There are some additional steps you can take to configure your Zensical project to work better with Read the Docs.

.. contents::
   :local:
   :backlinks: none

Set the canonical URL
~~~~~~~~~~~~~~~~~~~~~

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your Zensical `site URL`_ to your Read the Docs canonical URL using a
:doc:`Read the Docs environment variable </reference/environment-variables>`:

.. code-block:: toml
    :caption: zensical.toml

    [project]
    # Note: variable interpolation is not yet supported in Zensical configuration files,
    # so you can use the explicit value for now.
    site_url = "https://your-project.readthedocs.io/"

.. _site URL: https://zensical.org/docs/setup/basics/#site_url

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/zensical

Demo
    https://test-builds.readthedocs.io/en/zensical/

Further reading
---------------

* `Zensical documentation`_
* `Markdown syntax guide`_

.. _Zensical documentation: https://zensical.org/
.. _Markdown syntax guide: https://daringfireball.net/projects/markdown/syntax
