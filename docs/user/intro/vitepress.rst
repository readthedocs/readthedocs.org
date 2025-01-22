VitePress
=========

.. meta::
   :description lang=en: Learn how to host VitePress documentation on Read the Docs.

`VitePress`_ is a static site generator with a focus on performance and simplicity.

Minimal configuration is required to build an existing VitePress project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
    os: ubuntu-lts-latest
    tools:
        nodejs: "latest"
    jobs:
        install:
        - npm install vitepress
        build:
        # The site was created by running `vitepress init`
        # and following the official guide
        # https://vitepress.dev/guide/getting-started
        - vitepress build docs
        - mkdir -p $READTHEDOCS_OUTPUT/
        - mv docs/.vitepress/dist $READTHEDOCS_OUTPUT/html

.. _VitePress: https://vitepress.dev/

.. button-link:: https://dbtoolsbundle.readthedocs.io/en/stable/
   :color: secondary


   🔗 DbToolsBundle uses VitePress and Read the Docs

Getting started
---------------

- If you have an existing VitePress project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to VitePress, check out the official `Getting started with VitePress`_ guide.

.. _Getting started with VitePress: https://vitepress.vuejs.org/guide/getting-started.html


Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/vitepress

Demo
    https://test-builds.readthedocs.io/en/vitepress/

Further reading
---------------

* `VitePress documentation`_

.. _VitePress documentation: https://vitepress.vuejs.org/
