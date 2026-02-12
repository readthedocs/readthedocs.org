URL path prefixes
=================

URL path prefixes allow you to customize the URL structure of your documentation,
giving you more control over how your documentation is organized and presented.

.. note::

   This is a |com_brand| feature available on Pro and higher plans.
   Contact :doc:`Read the Docs support </support>` to enable custom URL path prefixes for your project.

What are URL path prefixes?
---------------------------

By default, Read the Docs serves documentation from the following URL patterns:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Project type
     - Default URL pattern
   * - Multi-version with translations
     - ``/<language>/<version>/<filename>``
   * - Multi-version without translations
     - ``/<version>/<filename>``
   * - Single version without translations
     - ``/<filename>``
   * - Subproject (multi-version with translations)
     - ``/projects/<subproject-alias>/<language>/<version>/<filename>``
   * - Subproject (multi-version without translations)
     - ``/projects/<subproject-alias>/<version>/<filename>``
   * - Subproject (single version without translations)
     - ``/projects/<subproject-alias>/<filename>``

URL path prefixes let you customize these URL patterns by:

* Adding a prefix to your project's documentation URLs
* Changing or removing the ``/projects/`` prefix used for subprojects

Use cases
---------

Here are some common scenarios where custom URL path prefixes are useful:

Proxy documentation behind your main website
   If you want to serve your documentation as part of your main website
   (for example, at ``https://example.com/docs/``),
   you can configure your web server to proxy requests to Read the Docs
   and use a custom prefix of ``/docs/`` to match.
   Your documentation would then be served from ``https://example.com/docs/en/latest/``
   instead of ``https://example.com/en/latest/``.

Remove or customize the ``/projects/`` prefix from subproject URLs
   By default, subprojects are served from URLs like
   ``https://docs.example.com/projects/plugin/en/latest/``.
   You can change this prefix to something shorter or remove it entirely,
   so your subproject is served from ``https://docs.example.com/plugin/en/latest/``
   or ``https://docs.example.com/libs/plugin/en/latest/``.

Organize documentation with meaningful URL paths
   You can use prefixes to create a more meaningful URL structure.
   For example, you could use ``/api/`` for API documentation
   and ``/guides/`` for user guides.

Getting started
---------------

To enable this feature for your project:

#. Ensure you have a Pro plan or higher subscription.
#. Contact :doc:`Read the Docs support </support>`
   with your project name and desired URL structure.
#. Our support team will configure the custom prefixes for your project.

.. tip::

   When planning your URL structure,
   consider how it will affect existing links to your documentation.
   You may need to set up :doc:`redirects </user-defined-redirects>`
   to ensure old URLs continue to work.

.. seealso::

   :doc:`/subprojects`
      Learn how to set up subprojects and share a custom domain

   :doc:`/custom-domains`
      Configure a custom domain for your documentation

   :doc:`/versioning-schemes`
      Learn about different URL versioning schemes
