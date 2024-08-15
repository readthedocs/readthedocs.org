Mkdocs on Read the Docs
=======================

MkDocs is a fast, simple and downright gorgeous static site generator that's geared towards building project documentation.

.. TODO The code comments here are pre-addons right? cos there is no manipulation


.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: ubuntu-22.04
     tools:
       python: "3"
     # Since Read the Docs manipulates that `mkdocs.yml` and it does not support `!ENV`,
     # we use `build.commands` here because we need `!ENV` in our `mkdocs.yml`.
     #
     commands:
       # Install Material for MkDocs Insiders
       # https://squidfunk.github.io/mkdocs-material/insiders/getting-started/
       #
       # Create GH_TOKEN environment variable on Read the Docs
       # https://docs.readthedocs.io/en/stable/guides/private-python-packages.html
       - pip install mkdocs-material
       - mkdocs build --site-dir $READTHEDOCS_OUTPUT/html

Configuring Mkdocs and Read the Docs addons
-------------------------------------------

To get the best integration with Read the Docs,
you need to make the following configuration changes to your Mkdocs config:

#. Set the site URL using a :doc:`Read the Docs environment variable </reference/environment-variables>`:

    .. code-block:: yaml
        :caption: mkdocs.yml

        site_url: !ENV READTHEDOCS_CANONICAL_URL

#. Configure search to use Read the Docs search instead of Mkdocs search:

    .. code-block:: js
        :caption: javascript/readthedocs.js

        document.addEventListener("DOMContentLoaded", function(event) {
        // Trigger Read the Docs' search addon instead of Material MkDocs default
        document.querySelector(".md-search__input").addEventListener("focus", (e) => {
                const event = new CustomEvent("readthedocs-search-show");
                document.dispatchEvent(event);
            });
        });

#. Include ``javascript/readthedocs.js`` in the Mkdocs build:

    .. code-block:: yaml
        :caption: mkdocs.yml

        extra_javascript:
            - javascript/readthedocs.js


Integrating Read the Docs version menu into your site navigation
-----------------------------------------------------------------

To integrate the version menu into your site navigation

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

#. Make sure that ``javascript/readthedocs.js`` is included in the Mkdocs build:

    .. code-block:: yaml
        :caption: mkdocs.yml

        extra_javascript:
            - javascript/readthedocs.js

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   /intro/getting-started-with-mkdocs
