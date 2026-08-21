
Deploying MkDocs on Read the Docs
=================================

.. meta::
   :description lang=en: Hosting MkDocs sites on Read the Docs.

`MkDocs`_ is a fast, simple static site generator that's geared towards building project documentation.
MkDocs is written in Python, and supports documentation written in Markdown.
When using MkDocs, we recommend using the `Material for MkDocs`_ theme,
and this guide is mostly focused on the integration required to make it work well on Read the Docs.

Minimal configuration is required to build an existing MkDocs project on Read the Docs:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: "ubuntu-24.04"
      tools:
        python: "3"
      # We recommend using a requirements file for reproducible builds.
      # This is just a quick example to get started.
      # https://docs.readthedocs.io/page/guides/reproducible-builds.html
      jobs:
        pre_install:
          - pip install mkdocs-material

    mkdocs:
      configuration: mkdocs.yml

.. _MkDocs: https://www.mkdocs.org/
.. _Material for MkDocs: https://squidfunk.github.io/mkdocs-material

Configuring Material for MkDocs on Read the Docs
------------------------------------------------

In order to use the Material for MkDocs theme on Read the Docs,
you need to install and configure it.
In your `mkdocs.yml` file, set the theme to `material`:

.. code-block:: yaml
   :caption: mkdocs.yml

    theme:
      name: material

With these changes, your MkDocs project will use the Material for MkDocs theme when built on Read the Docs,
and should work with the configuration file shown above.

Quick start
-----------

- You can use our :ref:`MkDocs example project <examples:mkdocs>` as a reference to create a new MkDocs project.
- If you have an existing MkDocs project you want to host on Read the Docs, check out our :doc:`/intro/add-project` guide.
- If you're new to MkDocs, check out the official `Getting Started <https://www.mkdocs.org/getting-started/>`_ guide.

Configuring MkDocs and Read the Docs Addons
-------------------------------------------

There are some additional steps you can take to configure your MkDocs project to work better with Read the Docs,
and these apply to all MkDocs projects.

Set the canonical URL
~~~~~~~~~~~~~~~~~~~~~

A :doc:`canonical URL </canonical-urls>` allows you to specify the preferred version of a web page
to prevent duplicated content.

Set your MkDocs `site URL`_ to your Read the Docs canonical URL using a
:doc:`Read the Docs environment variable </reference/environment-variables>`:

.. code-block:: yaml
    :caption: mkdocs.yml

    site_url: !ENV READTHEDOCS_CANONICAL_URL

.. _site URL: https://www.mkdocs.org/user-guide/configuration/#site_url

Configuring Material for MkDocs and Read the Docs Addons
--------------------------------------------------------

`Material for MkDocs`_ is a powerful documentation theme on top of MkDocs.
The following steps are specific to integrating Material for MkDocs and Read the Docs.

.. contents::
   :local:
   :backlinks: none

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

To integrate the :ref:`flyout-menu:Addons flyout menu` version menu into your site navigation:

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

            // Check if we already added versions and remove them if so.
            // This happens when using the "Instant loading" feature.
            // See https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#instant-loading
            const currentVersions = document.querySelector(".md-version");
            if (currentVersions !== null) {
              currentVersions.remove();
            }
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
