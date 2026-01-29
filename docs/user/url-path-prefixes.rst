URL path prefixes
=================

URL path prefixes allow you to customize the URL structure of your documentation,
giving you more control over how your documentation is organized and presented.

This is a |com_brand| feature available on Pro and higher plans.
Contact support to enable custom URL path prefixes for your project.

What are URL path prefixes?
---------------------------

By default, Read the Docs serves documentation from the following URL patterns:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Project type
     - Default URL pattern
   * - Multi-version project
     - ``/<language>/<version>/<filename>``
   * - Single version project
     - ``/<filename>``
   * - Subproject (multi-version)
     - ``/projects/<subproject-alias>/<language>/<version>/<filename>``
   * - Subproject (single version)
     - ``/projects/<subproject-alias>/<filename>``

URL path prefixes let you customize these URL patterns by:

* Adding a prefix to your project's documentation URLs
* Changing or removing the ``/projects/`` prefix used for subprojects

Use cases
---------

Here are some common scenarios where custom URL path prefixes are useful:

Proxy documentation behind your main website
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to serve your documentation as part of your main website
(for example, at ``https://example.com/docs/``),
you can configure your web server to proxy requests to Read the Docs
and use a custom prefix of ``/docs/`` to match.

Removing the ``/projects/`` prefix from subproject URLs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, subprojects are served from URLs like
``https://docs.example.com/projects/plugin/en/latest/``.
You can change this prefix to something shorter or remove it entirely,
so your subproject is served from ``https://docs.example.com/plugin/en/latest/``.

Organizing documentation with meaningful URL paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use prefixes to create a more meaningful URL structure.
For example, you could use ``/api/`` for API documentation
and ``/guides/`` for user guides.

Examples
--------

Adding a prefix to your project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's say you have a project ``example-docs`` with a Spanish translation ``example-docs-es``.

With the default URL structure, they are served from:

* ``https://example.com/en/latest/``
* ``https://example.com/es/latest/``

After configuring a custom prefix of ``/docs/`` for the main project, the URLs become:

* ``https://example.com/docs/en/latest/``
* ``https://example.com/docs/es/latest/``

Customizing the subproject prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's say you have a main project ``example-docs`` with a subproject ``example-plugin``.

With the default URL structure, they are served from:

* ``https://docs.example.com/en/latest/`` (main project)
* ``https://docs.example.com/projects/plugin/en/latest/`` (subproject)

After changing the subproject prefix from ``/projects/`` to ``/libs/``, the URLs become:

* ``https://docs.example.com/en/latest/`` (main project)
* ``https://docs.example.com/libs/plugin/en/latest/`` (subproject)

Getting started
---------------

URL path prefix customization is a |com_brand| feature.
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
