Custom script
=============

The Custom Script addon allows you to inject a custom JavaScript file into your documentation at serve time.
This enables you to modify or enhance frozen documentation without rebuilding it.

.. note::

   The Custom Script addon is not currently exposed in the user interface.
   If you would like to use this feature,
   please :doc:`contact support </support>`.

Using custom scripts
--------------------

This addon allows specifying a URL to a JavaScript file that will be injected into all pages of your documentation.
The script can be hosted on Read the Docs itself (as a relative URL) or on an external server (as an absolute URL).

Common use cases for custom scripts include:

* Fixing bugs or adding features to frozen documentation
* Injecting analytics or tracking code
* Customizing the appearance or behavior of specific documentation versions

Accessing Addons data from your script
--------------------------------------

Custom scripts are loaded asynchronously after the initial page load,
which means the ``readthedocs-addons-data-ready`` event has already been fired by the time your script executes.
To access the Addons data from your custom script,
check the ``window.ReadTheDocsEventData`` object first,
then subscribe to the event for future updates (for example, when the URL changes in a single-page application):

.. code-block:: javascript

    function handleReadTheDocsData(data) {
      // Access the Addons data here
      console.log("Project slug:", data.projects.current.slug);

      // You can filter by version to apply changes selectively
      if (data.versions.current.slug === "v3.0") {
        // Do something specific for version v3.0
      }
    }

    // The event "readthedocs-addons-data-ready" has been already fired when this script is run.
    // We need to check for `window.ReadTheDocsEventData` first, and if it's available
    // use that data to call the handler.
    if (window.ReadTheDocsEventData !== undefined) {
      handleReadTheDocsData(window.ReadTheDocsEventData.data());
    }

    // After that, we subscribe to the Read the Docs Addons event to access data
    // on future dispatchs (e.g. when a URL changes on a SPA)
    document.addEventListener("readthedocs-addons-data-ready", function (event) {
      handleReadTheDocsData(event.detail.data());
    });
