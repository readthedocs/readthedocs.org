
Deploying Starlight on Read the Docs
====================================

.. meta::
   :description lang=en: Learn how to host Starlight documentation on Read the Docs.

.. "Astro" isn't in our shared Vale dictionary (common/vale/RTD/CustomSpelling.yml);
   disable spelling for this page until it's added there.
.. vale RTD.CustomSpelling = NO

`Starlight`_ is a documentation framework built on top of the `Astro`_ web framework.

Minimal configuration is required to build an existing Starlight project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
        os: ubuntu-lts-latest
        tools:
            nodejs: "latest"
        jobs:
            install:
                - npm install
            build:
                html:
                    # The site was created by running
                    # `npm create astro@latest -- --template starlight`
                    # and following the official guide
                    # https://starlight.astro.build/getting-started/
                    - npm run build
                    - mkdir -p $READTHEDOCS_OUTPUT/
                    - mv dist $READTHEDOCS_OUTPUT/html

.. _Starlight: https://starlight.astro.build/
.. _Astro: https://astro.build/

Getting started
---------------

- If you have an existing Starlight project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to Starlight, check out the official `Getting started with Starlight`_ guide.

.. _Getting started with Starlight: https://starlight.astro.build/getting-started/

Using the proper base path
--------------------------

To ensure that your Starlight site works correctly on Read the Docs,
you need to set the ``site`` and ``base`` options in your Astro configuration:

.. code-block:: js
   :caption: astro.config.mjs

    import { defineConfig } from 'astro/config';
    import starlight from '@astrojs/starlight';

    // https://astro.build/config
    export default defineConfig({
        // Use the Read the Docs canonical URL so links and assets
        // resolve under the version path (e.g. `/en/latest/`)
        site: process.env.READTHEDOCS_CANONICAL_URL,
        base: process.env.READTHEDOCS_CANONICAL_URL
            ? new URL(process.env.READTHEDOCS_CANONICAL_URL).pathname
            : '/',
        integrations: [
            starlight({
                title: 'My Docs',
            }),
        ],
    });

.. note::

   Links starting with ``/`` in your content are not prefixed with the base path.
   Use relative links (e.g. ``./guides/example/``) so they work under the version path.

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/starlight

Demo
    https://test-builds.readthedocs.io/en/starlight/

Further reading
---------------

* `Starlight documentation`_
* `Astro documentation`_

.. _Starlight documentation: https://starlight.astro.build/
.. _Astro documentation: https://docs.astro.build/
