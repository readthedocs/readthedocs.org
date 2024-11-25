
Antora
======

.. meta::
   :description lang=en: Hosting Antora documentation on Read the Docs.

`Antora`_ is a powerful documentation framework that allows you to write documentation in AsciiDoc.

Minimal configuration is required to build an existing Antora project on Read the Docs.

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
        os: ubuntu-22.04
        tools:
            nodejs: "20"
        commands:
            - npm i -g -D -E antora
            - antora -v
            - antora --fetch antora-playbook.yml --to-dir $READTHEDOCS_OUTPUT/html

.. _Antora: https://antora.org/

Example configuration
---------------------

In order to build an Antora project on Read the Docs,
you need a playbook file that specifies the sources and UI bundle to use:

.. code-block:: yaml
   :caption: antora-playbook.yml

   site:
     title: Antora Demo site on Read the Docs
     start_page: component-b::index.adoc

   content:
     sources:
     - url: https://gitlab.com/antora/demo/demo-component-a.git
       branches: HEAD
     - url: https://gitlab.com/antora/demo/demo-component-b.git
       branches: [v2.0, v1.0]
       start_path: docs

   ui:
     bundle:
       url: https://gitlab.com/antora/antora-ui-default/-/jobs/artifacts/HEAD/raw/build/ui-bundle.zip?job=bundle-stable
       snapshot: true

Quick start
-----------

- If you have an existing Antora project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.

- If you're new to Antora, check out the official `Install and Run Antora Quickstart`_ guide.

.. _Install and Run Antora Quickstart: https://docs.antora.org/antora/latest/install-and-run-quickstart/

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/antora

Demo
    https://test-builds.readthedocs.io/en/antora/

Further reading
---------------

* `Antora documentation`_

.. _Antora documentation: https://docs.antora.org
