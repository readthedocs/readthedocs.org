mdBook
======

.. meta::
   :description lang=en: Learn how to host mdBook documentation on Read the Docs.

`mdBook`_ is a command line tool to create books with Markdown.

Minimal configuration is required to build an existing mdBook project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
        os: ubuntu-lts-latest
        tools:
            rust: latest
        commands:
            - cargo install mdbook
            # For an example book..
            # - mdbook init docs
            - mdbook build docs --dest-dir $READTHEDOCS_OUTPUT/html

.. _mdBook: https://rust-lang.github.io/mdBook/

Getting started
---------------

- If you have an existing mdBook project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to mdBook, check out the official `Getting started with mdBook`_ guide.

.. _Getting started with mdBook: https://rust-lang.github.io/mdBook/guide/creating.html

Configuring mdBook and Read the Docs Addons
-------------------------------------------

Adjust the flyout menu font size
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add a ``readthedocs.css`` to your build with the `additional-css <https://rust-lang.github.io/mdBook/format/configuration/renderers.html#html-renderer-options>`_ flag,
so that the font in the :ref:`flyout-menu:Addons flyout menu` matches the theme better.

.. code-block:: css
    :caption: readthedocs.css:

    :root {
        /* Increase the font size of the flyout menu */
        --readthedocs-flyout-font-size: 1.3rem;

        /* Increase the font size of the notifications */
        --readthedocs-notification-font-size: 1.3rem;

    }

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/mdbook

Demo
    https://test-builds.readthedocs.io/en/mdbook/

Further reading
---------------

* `mdBook documentation`_

.. _mdBook documentation: https://rust-lang.github.io/mdBook/
