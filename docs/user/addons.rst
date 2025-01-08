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

#. Go to the new :term:`dashboard`:
#. Click on a project name.
#. Go to :guilabel:`Settings`
#. In the left bar, go to :guilabel:`Addons`.
#. Configure each Addon individually.

Addons data and customization
-----------------------------

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

The event.detail.data() object contains all the Addons configuration, including:

* ``addons`` - Individual addon configurations
* ``builds.current`` - Details about the current build
* ``projects.current`` - Current project details
* ``projects.translations`` - Available translations
* ``versions.current`` - Details about the current version
* ``versions.active`` - List of all active versions

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
                    "build": "https://readthedocs.org/projects/docs/builds/26773762/",
                    "project": "https://readthedocs.org/projects/docs/",
                    "version": "https://readthedocs.org/projects/docs/version/stable/edit/"
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
                    "builds": "https://readthedocs.org/projects/docs/builds/",
                    "documentation": "https://docs.readthedocs.io/en/stable/",
                    "downloads": "https://readthedocs.org/projects/docs/downloads/",
                    "home": "https://readthedocs.org/projects/docs/",
                    "versions": "https://readthedocs.org/projects/docs/versions/"
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
                            "edit": "https://readthedocs.org/projects/docs/version/stable/edit/"
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
                        "edit": "https://readthedocs.org/projects/docs/version/stable/edit/"
                    },
                    "documentation": "https://docs.readthedocs.io/en/stable/",
                    "vcs": "https://github.com/readthedocs/readthedocs.org/tree/11.18.0/"
                },
                "verbose_name": "stable"
            }
        }

You can see a live example of this in our `Addons API response for these docs <https://docs.readthedocs.io/_/addons/?client-version=0.22.0&api-version=1&project-slug=docs&version-slug=stable>`_.

Example: Creating a Version Selector
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
