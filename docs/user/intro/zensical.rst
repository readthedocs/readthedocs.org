Deploying Zensical on Read the Docs
===================================

.. meta::
   :description lang=en: Learn how to host Zensical sites on Read the Docs.

Zensical_ is a static site generator for project documentation,
built by the creators of Material for MkDocs.

Read the Docs builds your Zensical site on every push,
previews your pull requests,
and hosts every version of your documentation.

Minimal configuration is required to build an existing Zensical project on Read the Docs:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: ubuntu-24.04
      tools:
        python: latest
      jobs:
        # For reproducible builds, install with uv:
        # https://docs.readthedocs.com/platform/stable/build-customization.html#install-dependencies-with-uv
        install:
          - pip install zensical
        build:
          html:
            - zensical build
        post_build:
          # Copy the built site into the directory Read the Docs publishes.
          - mkdir -p $READTHEDOCS_OUTPUT/html/
          - cp --recursive site/* $READTHEDOCS_OUTPUT/html/

For a complete example, see our `Zensical example repository`_.

.. _Zensical: https://zensical.org/
.. _Zensical example repository: https://github.com/readthedocs/test-builds/tree/zensical

Getting started
---------------

Add your project to publish your documentation.
If you're new to Zensical, see the official `Get started with Zensical`_ guide.

.. _Get started with Zensical: https://zensical.org/docs/get-started/

.. grid:: 2

    .. grid-item::

        .. button-link:: https://app.readthedocs.org/dashboard/import/
            :color: primary
            :expand:

            Add a project on Community

    .. grid-item::

        .. button-link:: https://app.readthedocs.com/dashboard/import/
            :color: info
            :expand:

            Add a project on Business

Production examples
-------------------

Projects using Zensical on Read the Docs:

DDEV
    https://docs.ddev.com/en/stable/

PDM
    https://pdm-project.org/en/latest/

cmd2
    https://cmd2.readthedocs.io/en/stable/

Set the canonical URL
---------------------

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your Zensical `site URL`_ to your Read the Docs canonical URL:

.. code-block:: toml
    :caption: zensical.toml

    [project]
    site_url = "https://<slug>.readthedocs.io/"

.. note::

   Zensical doesn't support variable interpolation in its configuration file,
   so you need to set the value explicitly
   instead of using the :envvar:`READTHEDOCS_CANONICAL_URL` environment variable.

.. _site URL: https://zensical.org/docs/setup/basics/#site_url

.. seealso::

   :doc:`/addons`
     Configuring Addons, like the version flyout menu.
