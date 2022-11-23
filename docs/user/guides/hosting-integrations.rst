Hosting Integrations
====================

Read the Docs performs some actions by default when building documentation for its users to.
These actions integrate the documentation project with multiple hosting features Read the Docs offers.
However, when using ``build.commands`` configuration (see :doc:`build-customization`),
the build process is overriden completely and it's the user responsibility to integrate these features.
This page explains how to manually integrate these features when Read the Docs cannot do it automatically.

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

`Telemetry`_

   .. TODO: write a new page explaining this and link it from here.

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

Note that you have to change lines 24-25 with your project and version slugs.

Besides including these files,
a ``div`` tag is required to define *where* the flyout menu will be displayed.
This tag has to be added inside the ``<body>`` tag:

.. code-block:: html

   <!-- Manually added to show the Read the Docs flyout -->
   <div id="readthedocs-embed-flyout"></div>
