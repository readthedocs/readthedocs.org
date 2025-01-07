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

Addons can be customized using CSS variables and the data used by Addons can be accessed using a custom event.

CSS Variable Customization
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

You can find the full list of available CSS variables in the `Addons source <https://github.com/readthedocs/addons/tree/main/src>`_ until we have a full list in the documentation.

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
* ``builds`` - Build information
    * ``current`` - Details about the current build
* ``projects`` - Project information
    * ``current`` - Current project details
    * ``translations`` - Available translations
* ``versions`` - Information about project versions
    * ``current`` - Details about the current version
    * ``active`` - List of all active versions

You can see a live example of this in our `Addons API response for these docs <https://docs.readthedocs.io/_/addons/?client-version=0.22.0&api-version=1&project-slug=docs&version-slug=stable`_.

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
