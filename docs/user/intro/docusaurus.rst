
Deploying Docusaurus on Read the Docs
=====================================

.. meta::
   :description lang=en: Hosting Docusaurus sites on Read the Docs.

`Docusaurus`_ is a static-site generator that builds a single-page application with fast client-side navigation and out-of-the-box documentation features.

Minimal configuration required to build a Docusaurus project on Read the Docs looks like this,
specifying a Node.js toolchain on Ubuntu, using multiple :ref:`build <config-file/v2:build>` jobs to install the requirements,
build the site, and copy the output to $READTHEDOCS_OUTPUT:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2
    build:
      os: "ubuntu-22.04"
      tools:
        nodejs: "18"
      jobs:
        # "docs/" was created following the Docusaurus tutorial:
        # npx create-docusaurus@latest docs classic
        # but you can just use your existing Docusaurus site
        install:
          # Install Docusaurus dependencies
          - cd docs/ && npm install
        build:
          html:
            # Build the site
            - cd docs/ && npm run build
            # Copy generated files into Read the Docs directory
            - mkdir --parents $READTHEDOCS_OUTPUT/html/
            - cp --recursive docs/build/* $READTHEDOCS_OUTPUT/html/

.. _Docusaurus: https://docusaurus.io/

Limitations
-----------

.. csv-table:: Limitations
   :header: "Feature", "Description", "Supported"

   "Search", "Provides full-text search capabilities.", "Not supported"
   "Files changed", "Ability to see what HTML files change in pull request previews.", "Not supported"

Quick start
-----------

- If you have an existing Docusaurus project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to Docusaurus, check out the official `Fast Track`_ guide.

.. _Fast Track: https://docusaurus.io/docs#fast-track

Configuring Docusaurus and Read the Docs Addons
-----------------------------------------------

For optimal integration with Read the Docs, make the following optional configuration changes to your Docusaurus config.

.. contents::
   :depth: 1
   :local:
   :backlinks: none

Configure trailing slashes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For proper operation on Read the Docs, you need to set ``trailingSlash: true`` in your Docusaurus configuration.
This ensures that URLs like ``/docs/intro`` are handled as ``/docs/intro/`` and the corresponding ``index.html`` file is served correctly.

Without this setting (or if set to ``false``), you will need to configure redirects to ensure proper URL resolution.

.. code-block:: js
    :caption: docusaurus.config.js

    export default {
        // Required for compatibility with Read the Docs
        trailingSlash: true,
    };

Set the canonical URL
~~~~~~~~~~~~~~~~~~~~~

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your Docusaurus `url`_ to your Read the Docs canonical URL using `dotenv <https://www.npmjs.com/package/dotenv>`__ and a
:doc:`Read the Docs environment variable </reference/environment-variables>`:

.. code-block:: js
    :caption: docusaurus.config.js

    import 'dotenv/config';

    export default {
        url: process.env.READTHEDOCS_CANONICAL_URL,
    };

.. _url: https://docusaurus.io/docs/configuration#syntax-to-declare-docusaurus-config

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/docusaurus

Demo
    https://test-builds.readthedocs.io/en/docusaurus/
