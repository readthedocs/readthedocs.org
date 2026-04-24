
Deploying mdBook on Read the Docs
=================================

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
      jobs:
        install:
          - cargo install mdbook
        build:
          html:
            # For an example book..
            # - mdbook init docs
            - mdbook build docs --dest-dir $READTHEDOCS_OUTPUT/html

.. _mdBook: https://rust-lang.github.io/mdBook/

Getting started
---------------

- If you have an existing mdBook project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to mdBook, check out the official `Getting started with mdBook`_ guide.

.. _Getting started with mdBook: https://rust-lang.github.io/mdBook/guide/creating.html

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
