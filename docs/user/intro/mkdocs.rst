.. _material:

Material for MkDocs
===================

.. meta::
   :description lang=en: Hosting Material for MkDocs sites on Read the Docs.

`MkDocs`_ is a fast, simple static site generator that's geared towards building project documentation.
`Material for MkDocs`_ is a powerful documentation framework on top of MkDocs.
Mkdocs is written in Python, and supports documentation written in Markdown.

.. note::

    This page is explicitly about Material for MkDocs. We're working on a guide for plain MkDocs as well.

Minimal configuration required to build an existing Material for MkDocs project on Read the Docs looks like this,
specifying a python toolchain on Ubuntu, defining the location of the installation requirements, and using the built-in
:ref:`mkdocs <config-file/v2:mkdocs>` command:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: ubuntu-24.04
      tools:
        python: "3"

    python:
      install:
        - requirements: requirements.txt

    mkdocs:
      configuration: mkdocs.yml

.. _MkDocs: https://www.mkdocs.org/
.. _Material for MkDocs: https://squidfunk.github.io/mkdocs-material


Quick start
-----------

- If you have an existing Material for MkDocs project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.

- If you're new to Material for MkDocs, check out the official `Getting started with Material for MkDocs`_ guide.

.. _Getting started with Material for MkDocs: https://squidfunk.github.io/mkdocs-material/getting-started/

Configuring Material for MkDocs and Read the Docs addons
--------------------------------------------------------

For optimal integration with Read the Docs, make the optional following configuration changes to your Material for MkDocs config.

.. contents::
   :depth: 1
   :local:
   :backlinks: none

Set the canonical URL
~~~~~~~~~~~~~~~~~~~~~

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your MkDocs `site URL`_  to your Read the Docs canonical URL using a
:doc:`Read the Docs environment variable </reference/environment-variables>`:

.. code-block:: yaml
    :caption: mkdocs.yml

    site_url: !ENV READTHEDOCS_CANONICAL_URL

.. _Site URL: https://www.mkdocs.org/user-guide/configuration/#site_url


Configure Read the Docs search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To configure your site to use :doc:`Read the Docs search </server-side-search/index>` instead of the default search:

#. Add the following block of JavaScript:

    .. code-block:: js
        :caption: javascript/readthedocs.js

        document.addEventListener("DOMContentLoaded", function(event) {
        // Trigger Read the Docs' search addon instead of Material MkDocs default
        document.querySelector(".md-search__input").addEventListener("focus", (e) => {
                const event = new CustomEvent("readthedocs-search-show");
                document.dispatchEvent(event);
            });
        });

#. Include ``javascript/readthedocs.js`` in your MkDocs configuration:

    .. code-block:: yaml
        :caption: mkdocs.yml

        extra_javascript:
            - javascript/readthedocs.js


Integrate the Read the Docs version menu into your site navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To integrate the :ref:`flyout-menu:Addons flyout menu` version menu into your site navigation

#. Override the ``main.html`` template to include the data in the ``meta`` attribute:

    .. code-block:: html
        :caption: overrides/main.html


        {% extends "base.html" %}

        {% block site_meta %}
        {{ super() }}
        <meta name="readthedocs-addons-api-version" content="1" />
        {% endblock %}

#. Parse the version data into a dropdown menu using JS in ``javascript/readthedocs.js``:

    .. code-block:: js
        :caption: javascript/readthedocs.js

        // Use CustomEvent to generate the version selector
        document.addEventListener(
                "readthedocs-addons-data-ready",
                function (event) {
                const config = event.detail.data();
                const versioning = `
        <div class="md-version">
        <button class="md-version__current" aria-label="Select version">
            ${config.versions.current.slug}
        </button>

        <ul class="md-version__list">
        ${ config.versions.active.map(
            (version) => `
            <li class="md-version__item">
            <a href="${ version.urls.documentation }" class="md-version__link">
                ${ version.slug }
            </a>
                    </li>`).join("\n")}
        </ul>
        </div>`;

            document.querySelector(".md-header__topic").insertAdjacentHTML("beforeend", versioning);
        });

#. Make sure that ``javascript/readthedocs.js`` is included in your MkDocs configuration:

    .. code-block:: yaml
        :caption: mkdocs.yml

        extra_javascript:
            - javascript/readthedocs.js

Example repository and demo
---------------------------

Example repository
    https://github.com/readthedocs/test-builds/tree/mkdocs-material

Demo
    https://test-builds.readthedocs.io/en/mkdocs-material/

Further reading
---------------

* `Material for MkDocs documentation`_
* `Markdown syntax guide`_
* `Writing your docs with MkDocs`_

.. _Material for MkDocs documentation: https://squidfunk.github.io/mkdocs-material/setup/
.. _Markdown syntax guide: https://daringfireball.net/projects/markdown/syntax
.. _Writing your docs with MkDocs: https://www.mkdocs.org/user-guide/writing-your-docs/
