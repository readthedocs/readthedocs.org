Deploying MyST Markdown on Read the Docs
========================================

.. meta::
   :description lang=en: Learn how to host MyST Markdown documentation on Read the Docs.

`MyST Markdown`_ is a set of open-source, community-driven tools designed for scientific communication,
including a powerful authoring framework that supports blogs, online books, scientific papers, reports and journal articles.

Minimal configuration is required to build an existing MyST Markdown project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: ubuntu-lts-latest
      tools:
        nodejs: "latest"
      jobs:
        install:
          # Install mystmd dependencies
          - npm install -g mystmd
        build:
          html:
            # Build the site
            - cd docs/ && myst build --html
          post_build:
            # Copy generated files into Read the Docs directory
            - mkdir --parents $READTHEDOCS_OUTPUT/html/
            - cp --recursive docs/_build/html/* $READTHEDOCS_OUTPUT/html/

.. _MyST Markdown: https://mystmd.org/

Getting started
---------------

- If you have an existing MyST Markdown project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to MyST Markdown, check out the official `MyST quickstart guide`_.

.. _MyST quickstart guide: https://mystmd.org/guide/quickstart

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/mystmd

Demo
    https://test-builds.readthedocs.io/en/mystmd/

Further reading
---------------

* `MyST Markdown documentation`_

.. _MyST Markdown documentation: https://mystmd.org/guide
