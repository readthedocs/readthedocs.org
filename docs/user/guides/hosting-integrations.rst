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
   :linenos:

   <!-- Manually added to show the Read the Docs flyout -->
   <div id="readthedocs-embed-flyout"></div>


Telemetry
---------

Read the Docs expects the file ``_build/json/telemetry.json`` once the build has finished.
This file contains a list of doctool extensions/plugins installed to perform the build
and also the HTML theme used.

The data is organized in a JSON file as follows:

.. code-block:: json
   :linenos:

   {
     "extensions": [
       "module.extension"
     ],
     "html_theme": "name"
   }


Advertisement
-------------

Advertisement makes Read the Docs sustainable and free for Open Source projects.
Similarly to the flyout_, it requires including the same Javascript and stylesheet files
(you can copy the code from the previous section),
plus a ``div`` specifying *where* the Ad should be shown:

.. NOTE: should we tell people to integrate it using the ``readthedocs-doc-embed.js`` file,
   or should they use the EthicalAds client directly?

.. code-block:: html
   :linenos:

   <!-- Manually added to show Ethical Ads -->
   <div id="rtd-stickybox-container">
     <div class="raised" data-ea-publisher="readthedocs" data-ea-type="image" data-ea-style="stickybox"></div>
   </div>


.. note::

   Make sure to not include the Javascript and stylesheet twice when integrating the Flyout_ and Advertisement_.
   That chunk of HTML code is exactly the same and shared between both.
   They should be included only once in the page.


External (pull request) version warning
---------------------------------------

On each build built from a pull requests,
a warning banner is added to communicate readers this particular version of the documentation is not in production
and it's still under review.

Read the Docs adds the following HTML to create the warning admonition:

.. NOTE: we should standardize this by providing the CSS as well and making it sticky (maybe at the top).
   Now, it's injected at a particular place in the HTML structure --which won't be general for all the doctools.
   Besides, we are inject it using a Sphinx extension that may differ what's the outputed HTML (based on docutils version).

.. code-block:: html
   :lienos:
   :emphasize-lines: 5,7

   <div class="admonition warning">
     <p class="admonition-title">Warning</p>
     <p>
       This page
       <a class="reference external" href="https://readthedocs.org/projects/<project-slug>/builds/<build-id>/">was created </a>
       from a pull request
       (<a class="reference external" href="https://github.com/<gh-username>/<gh-repository>/pull/pr-number">#PRNUMBER</a>).
     </p>
   </div>

Note in the highlighted lines there are some placeholders for:

* Read the Docs' project slug
* Read the Docs' build id
* GitHub username
* GitHub pull request number

These placeholders should be replaced by the real values.


Version warning
---------------

Read the Docs adds a warning banner at the top of each documentation page
when the reader visits an old page when there is a newer version of the same page available.

.. NOTE: this has the same non-standardized issue as the "External version warning"


.. code-block:: html
   :lienos:
   :emphasize-lines: 5,7

   <div class="admonition warning">
     <p class="admonition-title">Warning</p>
     <p>
       This page documents version
       <a class="reference" href="https://<slug>.readthedocs.io/<lang>/<version>"><version></a>.
       The latest version is
       <a class="reference" href="https://<slug>.readthedocs.io/<lang>/<version>"><version></a>.
     </p>
   </div>

Note in the highlighted lines there are some placeholders for:

* Read the Docs' project slug
* Read the Docs' language
* Read the Docs' current version (old)
* Read the Docs' new version
