Read the Docs Addons
====================

**Read the Docs Addons** is a group of features for documentation readers and maintainers that you can add to any documentation set hosted on Read the Docs.
They are used in the rendered documentation,
and can be accessed via hotkeys or on screen UI elements.

:doc:`Visual diff </visual-diff>`
    Highlight changed output from pull requests

:doc:`Link previews </link-previews>`
    See the content the link points to before clicking on it

:doc:`Documentation notification </doc-notifications>`
    Alert users to various documentation states

:doc:`Flyout </flyout-menu>`
    Easily switch between versions and translations

:doc:`Non-stable notification </versions>`
    Notify readers that they are reading docs from a non stable release

:doc:`Latest version notification </versions>`
    Notify readers that they are reading docs from a development version

:doc:`Search as you type </server-side-search/index>`
    Get search results faster

:doc:`Traffic analytics </traffic-analytics>`
    See what pages your users are reading

:doc:`Search analytics </search-analytics>`
    Understand what your users are searching for

Configuring Read the Docs Addons
--------------------------------

Individual configuration options for each addon are available in :guilabel:`Settings`.

#. Go to the new :term:`dashboard`.
#. Click on a project name.
#. Go to :guilabel:`Settings`.
#. In the left bar, go to :guilabel:`Addons`.
#. Configure each Addon individually.

Integrating with Addons
-----------------------

Integrate with Search as you type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To configure your site to use :doc:`Read the Docs search </server-side-search/index>` instead of the default search, adapt the following block of JavaScript to your own site:

    .. code-block:: js
        :caption: javascript/readthedocs.js

        // TODO: Change me if needed
        const selector = "input[type='search']";

        document.addEventListener("DOMContentLoaded", function(event) {
            // Trigger Read the Docs' search addon instead of the default search
            document.querySelector(selector).addEventListener("click", (e) => {
                const event = new CustomEvent("readthedocs-search-show");
                document.dispatchEvent(event);
            });
        });

.. note::   Depending on the tool you are using,
            you may need to change the selector to match the search input field.
            You will also need to ensure that the JavaScript file is included in your documentation build.

Addons data and customization
-----------------------------

Addons can be customized using CSS variables and the data used by Addons can be accessed using a custom event.

CSS variable customization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Addons use CSS custom properties (`CSS variables <https://developer.mozilla.org/en-US/docs/Web/CSS/--*>`_) to allow for easy customization.
To customize addons, add CSS variable definitions to your theme's CSS:

.. code-block:: css

    :root {
        /* Reduce Read the Docs' flyout font a little bit */
        --readthedocs-flyout-font-size: 0.7rem;

        /* Reduce Read the Docs' notification font a little bit */
        --readthedocs-notification-font-size: 0.8rem;

        /* This customization is not yet perfect because we can't change the `line-height` yet. */
        /* See https://github.com/readthedocs/addons/issues/197 */
        --readthedocs-search-font-size: 0.7rem;
    }

CSS variables reference
^^^^^^^^^^^^^^^^^^^^^^^

.. Got this with: grep -ho -- '--readthedocs-[a-zA-Z0-9-]*' *.css | sort -u

.. dropdown:: Click to see all available CSS variables

    **Global variables**

    - ``--readthedocs-font-size``

    **Flyout menu**

    - ``--readthedocs-flyout-background-color``
    - ``--readthedocs-flyout-color``
    - ``--readthedocs-flyout-current-version-color``
    - ``--readthedocs-flyout-font-family``
    - ``--readthedocs-flyout-font-size``
    - ``--readthedocs-flyout-header-font-size``
    - ``--readthedocs-flyout-item-link-color``
    - ``--readthedocs-flyout-link-color``
    - ``--readthedocs-flyout-section-heading-color``

    **Notifications**

    - ``--readthedocs-notification-background-color``
    - ``--readthedocs-notification-color``
    - ``--readthedocs-notification-font-family``
    - ``--readthedocs-notification-font-size``
    - ``--readthedocs-notification-link-color``
    - ``--readthedocs-notification-title-background-color``
    - ``--readthedocs-notification-title-color``
    - ``--readthedocs-notification-toast-font-size``

    **Search**

    - ``--readthedocs-search-backdrop-color``
    - ``--readthedocs-search-color``
    - ``--readthedocs-search-content-background-color``
    - ``--readthedocs-search-content-border-color``
    - ``--readthedocs-search-filters-border-color``
    - ``--readthedocs-search-font-family``
    - ``--readthedocs-search-font-size``
    - ``--readthedocs-search-footer-background-color``
    - ``--readthedocs-search-footer-code-background-color``
    - ``--readthedocs-search-footer-code-border-color``
    - ``--readthedocs-search-input-background-color``
    - ``--readthedocs-search-result-section-border-color``
    - ``--readthedocs-search-result-section-color``
    - ``--readthedocs-search-result-section-highlight-color``
    - ``--readthedocs-search-result-section-subheading-color``

You can find default values and full CSS in our `Addons source <https://github.com/readthedocs/addons/tree/main/src>`_.

Custom event integration
~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs provides a custom event ``readthedocs-addons-data-ready`` that allows you to access the Addons data and integrate it into your theme or documentation.
The event provides access to the version data, project information, and other Addons configuration.

To use the custom event:

1. Add the required meta tag to your HTML template:

   .. code-block:: html

      <meta name="readthedocs-addons-api-version" content="1" />

2. Add a JavaScript event listener to handle the data:

   .. code-block:: javascript

      document.addEventListener(
        "readthedocs-addons-data-ready",
        function (event) {
          // Access the addons data
          const config = event.detail.data();

          // Example: Create a version selector
          const versions = config.versions.active.map(version => ({
            slug: version.slug,
            url: version.urls.documentation
          }));

          // Use the data to build your UI
          console.log('Available versions:', versions);
        }
      );

Event data reference
^^^^^^^^^^^^^^^^^^^^

The ``event.detail.data()`` object contains all the Addons configuration, including:

* ``addons`` - Individual addon configurations
* ``builds.current`` - Details about the current build
* ``projects.current`` - Current project details
* ``projects.translations`` - Available translations
* ``versions.current`` - Details about the current version
* ``versions.active`` - List of all active and not hidden versions

.. dropdown:: Click to see an example of the Addons data

    .. code-block:: json

        {
        "addons": {
            "Most of this config is currently for internal use.": "We are working on making this more public.",
        },
        "api_version": "1",
        "builds": {
            "current": {
                "commit": "6db46a36ed3da98de658b50c66b458bbfa513a4e",
                "created": "2025-01-07T16:02:16.842871Z",
                "duration": 78,
                "error": "",
                "finished": "2025-01-07T16:03:34.842Z",
                "id": 26773762,
                "project": "docs",
                "state": {
                    "code": "finished",
                    "name": "Finished"
                },
                "success": true,
                "urls": {
                    "build": "https://app.readthedocs.org/projects/docs/builds/26773762/",
                    "project": "https://app.readthedocs.org/projects/docs/",
                    "version": "https://app.readthedocs.org/projects/docs/version/stable/edit/"
                },
                "version": "stable"
            }
        },
        "domains": {
            "dashboard": "readthedocs.org"
        },
        "projects": {
            "current": {
                "created": "2016-12-20T06:26:09.098922Z",
                "default_branch": "main",
                "default_version": "stable",
                "external_builds_privacy_level": "public",
                "homepage": null,
                "id": 74581,
                "language": {
                    "code": "en",
                    "name": "English"
                },
                "modified": "2024-11-13T17:09:09.007795Z",
                "name": "docs",
                "privacy_level": "public",
                "programming_language": {
                    "code": "py",
                    "name": "Python"
                },
                "repository": {
                    "type": "git",
                    "url": "https://github.com/readthedocs/readthedocs.org"
                },
                "single_version": false,
                "slug": "docs",
                "subproject_of": null,
                "tags": [
                    "docs",
                    "python",
                    "sphinx-doc"
                ],
                "translation_of": null,
                "urls": {
                    "builds": "https://app.readthedocs.org/projects/docs/builds/",
                    "documentation": "https://docs.readthedocs.io/en/stable/",
                    "downloads": null,
                    "home": "https://app.readthedocs.org/projects/docs/",
                    "versions": "https://app.readthedocs.org/projects/docs/versions/"
                },
                "users": [
                    {
                        "username": "eric"
                    },
                    {
                        "username": "davidfischer"
                    },
                    {
                        "username": "humitos"
                    },
                    {
                        "username": "plaindocs"
                    },
                    {
                        "username": "agj"
                    },
                    {
                        "username": "stsewd"
                    }
                ],
                "versioning_scheme": "multiple_versions_with_translations"
            },
            "translations": []
        },
        "readthedocs": {
            "analytics": {
                "code": "UA-17997319-1"
            }
        },
        "versions": {
            "active": [
                {
                    "active": true,
                    "aliases": [],
                    "built": true,
                    "downloads": {
                        "epub": "https://docs.readthedocs.io/_/downloads/en/stable/epub/",
                        "htmlzip": "https://docs.readthedocs.io/_/downloads/en/stable/htmlzip/"
                    },
                    "hidden": false,
                    "id": 2604018,
                    "identifier": "6db46a36ed3da98de658b50c66b458bbfa513a4e",
                    "privacy_level": "public",
                    "ref": "11.18.0",
                    "slug": "stable",
                    "type": "tag",
                    "urls": {
                        "dashboard": {
                            "edit": "https://app.readthedocs.org/projects/docs/version/stable/edit/"
                        },
                        "documentation": "https://docs.readthedocs.io/en/stable/",
                        "vcs": "https://github.com/readthedocs/readthedocs.org/tree/11.18.0/"
                    },
                    "verbose_name": "stable"
                }
            ],
            "current": {
                "active": true,
                "aliases": [],
                "built": true,
                "downloads": {
                    "epub": "https://docs.readthedocs.io/_/downloads/en/stable/epub/",
                    "htmlzip": "https://docs.readthedocs.io/_/downloads/en/stable/htmlzip/"
                },
                "hidden": false,
                "id": 2604018,
                "identifier": "6db46a36ed3da98de658b50c66b458bbfa513a4e",
                "privacy_level": "public",
                "ref": "11.18.0",
                "slug": "stable",
                "type": "tag",
                "urls": {
                    "dashboard": {
                        "edit": "https://app.readthedocs.org/projects/docs/version/stable/edit/"
                    },
                    "documentation": "https://docs.readthedocs.io/en/stable/",
                    "vcs": "https://github.com/readthedocs/readthedocs.org/tree/11.18.0/"
                },
                "verbose_name": "stable"
            }
        }

You can see a live example of this in our `Addons API response for these docs <https://docs.readthedocs.io/_/addons/?client-version=0.22.0&api-version=1&project-slug=docs&version-slug=stable>`_.

Example: creating a version selector
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's a complete example showing how to create a version selector using the Addons data:

.. code-block:: javascript

    document.addEventListener(
      "readthedocs-addons-data-ready",
      function (event) {
        const config = event.detail.data();

        // Create the version selector HTML
        const versionSelector = `
          <div class="version-selector">
            <select onchange="window.location.href=this.value">
              <option value="${config.versions.current.urls.documentation}">
                ${config.versions.current.slug}
              </option>
              ${config.versions.active
                .filter(v => v.slug !== config.versions.current.slug)
                .map(version => `
                  <option value="${version.urls.documentation}">
                    ${version.slug}
                  </option>
                `).join('')}
            </select>
          </div>
        `;

        // Insert the version selector into your page
        document.querySelector('#your-target-element')
          .insertAdjacentHTML('beforeend', versionSelector);
      }
    );

Diving deeper
-------------

You can read more about all of the Addons functionality by diving into each Addon above.
If you are a developer and would like to integrate with our Addons or use our existing data,
you can :doc:`reach out </support>` to us and we would love to work with you.
