
Deploying Markdoc on Read the Docs
==================================

.. meta::
   :description lang=en: Hosting Markdoc documentation on Read the Docs.

`Markdoc`_ is a powerful documentation framework that allows you to write documentation in a flavor of Markdown.

Minimal configuration is required to build an existing Markdoc project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: ubuntu-24.04
      tools:
        nodejs: "22"
      jobs:
        install:
          # Install dependencies
          - cd docs/ && npm install
        build:
          # Build the site
          - cd docs/ && npm run build
          # Copy generated files into Read the Docs directory
          - mkdir --parents $READTHEDOCS_OUTPUT/html/
          - cp --verbose --recursive docs/out/* $READTHEDOCS_OUTPUT/html/

.. _Markdoc: https://markdoc.io/

Example configuration
---------------------

In order to build a Markdoc project on Read the Docs,
you need to generate static HTML from the Next.js build:

.. code-block:: js
   :caption: next.config.js

   const withMarkdoc = require('@markdoc/next.js');

   const nextConfig = {
       // Optional: Export HTML files instead of a Node.js server
       output: 'export',

       // Optional: Change links `/me` -> `/me/` and emit `/me.html` -> `/me/index.html`
       trailingSlash: true,

       // Use Canonical URL, but only the path and with no trailing /
       // End result is like: `/en/latest`
       basePath: process.env.READTHEDOCS_CANONICAL_URL
         ? new URL(process.env.READTHEDOCS_CANONICAL_URL).pathname.replace(/\/$/, "")
         : "",
   }

   module.exports =
       withMarkdoc({mode: 'static'})({
           pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdoc'],
           ...nextConfig,
   });

Limitations
-----------

All Read the Docs features are supported for Markdoc projects.
There may be some Markdoc features that depend on server-side rendering that are not supported.

Getting started
---------------

- If you have an existing Markdoc project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to Markdoc, check out the official `Getting started with Markdoc`_ guide.

.. _Getting started with Markdoc: https://markdoc.io/docs/getting-started

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/markdoc

Demo
    https://test-builds.readthedocs.io/en/markdoc/

Further reading
---------------

* `Markdoc documentation`_

.. _Markdoc documentation: https://markdoc.io/docs
