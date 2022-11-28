Hosting Integrations
====================

This page explains the manual steps required to integrate all the hosting features when overriding the build process by using ``build.commands`` configuration
(see :doc:`build-customization`).
As Read the Docs does not have control over the build process,
it cannot install and inject the required extensions to automatically integrate them.
You are encourage to read this document and understand the "behind the scenes" to integrate these features by yourself.
This can be done by running user-defined commands in the build process or by creating a doctool extensions
that execute these actions as part of the build itself.

These are all the hosting features that Read the Docs provides by default:

`Flyout menu`_
   Menu displaying on all documentation pages containing the list of active versions,
   downloadable formats and other useful links.
   Read more at :doc:`flyout-menu`.

`Search index`_
   Smart search index powered by Elasticsearch able to differentiate between regular text,
   function names in code, and search in all subprojects, among others.
   Read more at :doc:`server-side-search`.

`Search as you type`_
   Level up your search by providing immediate feedback while the user is typing.
   Read more at :doc:`advanced-search.html#enable-search-as-you-type-in-your-documentation`.

`Version warning`_
   Banner displayed on old versions when there is a newer version available,
   communicating readers they may be careful since they are reading an older version of the documentation.
   Read more at :doc:`versions#version-warning`.

`External (pull request) version warning`_
   Benner displayed on versions of the documentation built from an external version (pull request),
   warning readers this is not the final version of this documentation.
   Read more at :doc:`pull-requests`.

.. TODO: write a new page explaining this and link it from here.
`Telemetry`_
   Build data stored by Read the Docs (e.g. Python packages installed) for better understanding about
   how users use the platform and keep it stable.
   Read more in our blog post
   `Knowing more about how people use our service <https://blog.readthedocs.com/knowing-more-about-ourselves/>`_


`Advertisement`_
   Ad shown on documentation pages that helps Read the Docs to be sustainable.
   Read more at :doc:`advertising`.


.. TODO: explain "Visual diff" when we have it available for our users.


Flyout menu
-----------

Displying the flyout menu requires adding some Javascript and CSS files in each of the documentation pages.
These files have to be added inside the ``<head>`` tag:

.. code-block:: html
   :linenos:
   :emphasize-lines: 22,23

   <script
     crossorigin="anonymous"
     integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4="
     src="https://code.jquery.com/jquery-3.6.0.min.js">
   </script>
   <script
     async="async"
     src="/_/static/javascript/readthedocs-doc-embed.js">
   </script>

   <link
     rel="stylesheet"
     href="/_/static/css/readthedocs-doc-embed.css"
     type="text/css" />
   <link
     rel="stylesheet"
     type="text/css"
     href="/_/static/css/badge_only.css" />

   <script type="text/javascript">
   READTHEDOCS_DATA = {
     "project": "<your project slug>",
     "version": "<the version of your project>",
   }
   </script>

Note that you have to change the highlighted lines with your project and version slugs.

Besides including these files,
a ``div`` tag is required to define *where* the flyout menu will be displayed.
This tag has to be added inside the ``<body>`` tag:

.. code-block:: html

   <!-- Manually added to show the Read the Docs flyout -->
   <div id="readthedocs-embed-flyout"></div>
