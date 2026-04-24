
Deploying Antora on Read the Docs
=================================

.. meta::
   :description lang=en: Hosting Antora documentation on Read the Docs.

`Antora`_ is a static site generator for creating documentation sites from AsciiDoc content.

Minimal configuration is required to build an existing Antora project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
        os: ubuntu-lts-latest
        tools:
            nodejs: latest
        jobs:
          install:
            - npm i -g @antora/cli@3.1 @antora/site-generator@3.1
          build:
            html:
              - antora --fetch antora-playbook.yml --to-dir $READTHEDOCS_OUTPUT/html

.. _Antora: https://antora.org/

Getting Started
---------------

- If you have an existing Antora project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to Antora, check out the official `Getting Started with Antora`_ guide.

.. _Getting Started with Antora: https://docs.antora.org/antora/latest/install-and-run-quickstart/

Example Repository and Demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/antora

Demo
    https://test-builds.readthedocs.io/en/antora/

Further Reading
---------------

* `Antora documentation`_

.. _Antora documentation: https://docs.antora.org/antora/latest/
