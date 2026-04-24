
Deploying VitePress on Read the Docs
====================================

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
                html:
                    # The site was created by running `vitepress init`
                    # and following the official guide
                    # https://vitepress.dev/guide/getting-started
                    - vitepress build docs
                    - mkdir -p $READTHEDOCS_OUTPUT/
                    - mv docs/.vitepress/dist $READTHEDOCS_OUTPUT/html

.. _VitePress: https://vitepress.dev/

Getting started
---------------

- If you have an existing VitePress project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to VitePress, check out the official `Getting started with VitePress`_ guide.

.. _Getting started with VitePress: https://vitepress.vuejs.org/guide/getting-started.html

Using the proper base path
--------------------------

To ensure that your VitePress site works correctly on Read the Docs,
you need to set the ``base`` option in your VitePress configuration to the correct base path:

.. code-block:: js
   :caption: .vitepress/config.js

    import { defineConfig } from 'vitepress'

    // https://vitepress.dev/reference/site-config
    export default defineConfig({
        // Use Canonical URL, but only the path and with no trailing /
        // End result is like: `/en/latest`
        base: process.env.READTHEDOCS_CANONICAL_URL
        ? new URL(process.env.READTHEDOCS_CANONICAL_URL).pathname.replace(/\/$/, "")
        : "",

    title: "My Awesome Project",
    description: "A VitePress Site",
    })

Example repository and demo
---------------------------

Production example from DbToolsBundle
    https://dbtoolsbundle.readthedocs.io/en/stable/

Example repository
    https://github.com/readthedocs/test-builds/tree/vitepress

Demo
    https://test-builds.readthedocs.io/en/vitepress/

Further reading
---------------

* `VitePress documentation`_

.. _VitePress documentation: https://vitepress.dev/
