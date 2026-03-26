Redirects
=========

Over time, a documentation project may want to rename and move contents around.
Redirects allow changes in a documentation project to happen without bad user experiences.

If you do not manage URL structures,
users will eventually encounter 404 File Not Found errors.
While this may be acceptable in some cases,
the bad user experience of a 404 page is usually best to avoid.

`Built-in redirects`_ ⬇️
    Allows for simple and long-term sharing of external references to your documentation.

`User-defined redirects`_ ⬇️
    Makes it easier to move contents around

.. seealso::

   :doc:`/guides/redirects`
     This guide shows you how to add redirects with practical examples.
   :doc:`/guides/best-practice/links`
     Information and tips about creating and handling external references.
   :doc:`/guides/deprecating-content`
     A guide to deprecating features and other topics in a documentation.

Built-in redirects
------------------

This section explains the redirects that are automatically active for all projects and how they are useful.
Built-in redirects are especially useful for creating and sharing incoming links,
which is discussed in depth in :doc:`/guides/best-practice/links`.

.. _page_redirects:

Page redirects at ``/page/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can link to a specific page and have it redirect to your default version,
allowing you to create links on external sources that are always up to date.
This is done with the ``/page/`` URL prefix.

For instance, you can reach the page you are reading now by going to https://docs.readthedocs.io/page/guides/best-practice/links.html.

Another way to handle this is the ``latest`` version.
You can set your ``latest`` version to a specific version and just always link to ``latest``.
You can reach this page by going to https://docs.readthedocs.io/en/latest/guides/best-practice/links.html.

.. _root_url_redirect:

Root URL redirect at ``/``
~~~~~~~~~~~~~~~~~~~~~~~~~~

A link to the root of your documentation (`<slug>.readthedocs.io/`) will redirect to the  :term:`default version`,
as set in your project settings.

This works for both readthedocs.io (|org_brand|), readthedocs-hosted.com (|com_brand|), and :doc:`custom domains </custom-domains>`.

For example::

    docs.readthedocs.io -> docs.readthedocs.io/en/stable/

.. warning::

   You cannot use the root redirect to reference specific pages.
   ``/`` *only* redirects to the default version,
   whereas ``/some/page.html`` will *not* redirect to ``/en/latest/some/page.html``.
   Instead, use :ref:`page_redirects`.

You can choose which is the :term:`default version` for Read the Docs to display.
This usually corresponds to the most recent official release from your project.

Root language redirect at ``/<lang>/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A link to the root language of your documentation (``<slug>.readthedocs.io/en/``)
will redirect to the  :term:`default version` of that language.

For example, accessing the English language of the project will redirect you to the its default version (``stable``)::

   https://docs.readthedocs.io/en/ -> https://docs.readthedocs.io/en/stable/

Shortlink with ``https://<slug>.rtfd.io``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Links to ``rtfd.io`` are treated the same way as ``readthedocs.io``.
They are intended to be easy and short for people to type.

You can reach these docs at https://docs.rtfd.io.

.. old label
.. _User-defined Redirects:

User-defined redirects
----------------------

Page redirects
~~~~~~~~~~~~~~

*Page Redirects* let you redirect a page across all versions of your documentation.

.. note::

   Since pages redirects apply to all versions,
   ``From URL`` doesn't need to include the ``/<language>/<version>`` prefix (e.g. ``/en/latest``),
   but just the version-specific part of the URL.
   If you want to set redirects only for some languages or some versions, you should use
   :ref:`user-defined-redirects:exact redirects` with the fully-specified path.

Exact redirects
~~~~~~~~~~~~~~~

*Exact Redirects* take into account the full URL (including language and version),
allowing you to create a redirect for a specific version or language of your documentation.

Clean/HTML URLs redirects
~~~~~~~~~~~~~~~~~~~~~~~~~

If you decide to change the style of the URLs of your documentation,
you can use *Clean URL to HTML* or *HTML to clean URL* redirects to redirect users to the new URL style.

For example, if a previous page was at ``/en/latest/install.html``,
and now is served at ``/en/latest/install/``, or vice versa,
users will be redirected to the new URL.

Limitations and observations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- |org_brand| users are limited to 100 redirects per project,
  and |com_brand| users have a number of redirects limited by their plan.
- By default, redirects only apply on pages that don't exist.
  **Forced redirects** allow you to apply redirects on existing pages.
- Redirects aren't applied on :doc:`previews of pull requests </pull-requests>`.
  You should treat these domains as ephemeral and not rely on them for user-facing content.
- You can redirect to URLs outside Read the Docs,
  just include the protocol in ``To URL``, e.g ``https://example.com``.
- A wildcard can be used at the end of ``From URL`` (suffix wildcard) to redirect all pages matching a prefix.
  Prefix and infix wildcards are not supported.
- If a wildcard is used in ``From URL``,
  the part of the URL that matches the wildcard can be used in ``To URL`` with the ``:splat`` placeholder.
- Redirects without a wildcard match paths with or without a trailing slash,
  e.g. ``/install`` matches ``/install`` and ``/install/``.
- The order of redirects matters.
  If multiple redirects match the same URL,
  the first one will be applied.
  The order of redirects :ref:`can be changed from your project's dashboard <guides/redirects:Changing the order of redirects>`.
- If an infinite redirect is detected, a 404 error will be returned,
  and no other redirects will be applied.

Examples
~~~~~~~~

Redirecting a page
``````````````````

Say you move the ``example.html`` page into a subdirectory of examples: ``examples/intro.html``.
You can create a redirect with the following configuration::

    Type: Page Redirect
    From URL: /example.html
    To URL: /examples/intro.html

Users will now be redirected:

- From ``https://docs.example.com/en/latest/example.html``
  to ``https://docs.example.com/en/latest/examples/intro.html``.
- From ``https://docs.example.com/en/stable/example.html``
  to ``https://docs.example.com/en/stable/examples/intro.html``.

If you want this redirect to apply to a specific version of your documentation,
you can create a redirect with the following configuration::

    Type: Exact Redirect
    From URL: /en/latest/example.html
    To URL: /en/latest/examples/intro.html

.. note::

   Use the desired version and language instead of ``latest`` and ``en``.

Redirecting a directory
```````````````````````

Say you rename the ``/api/`` directory to ``/api/v1/``.
Instead of creating a redirect for each page in the directory,
you can use a wildcard to redirect all pages in that directory::

    Type: Page Redirect
    From URL: /api/*
    To URL: /api/v1/:splat

Users will now be redirected:

- From ``https://docs.example.com/en/latest/api/``
  to ``https://docs.example.com/en/latest/api/v1/``.
- From ``https://docs.example.com/en/latest/api/projects.html``
  to ``https://docs.example.com/en/latest/api/v1/projects.html``.

If you want this redirect to apply to a specific version of your documentation,
you can create a redirect with the following configuration::

    Type: Exact Redirect
    From URL: /en/latest/api/*
    To URL: /en/latest/api/v1/:splat

.. note::

   Use the desired version and language instead of ``latest`` and ``en``.

Redirecting a directory to a single page
````````````````````````````````````````

Say you put the contents of the ``/examples/`` directory into a single page at ``/examples.html``.
You can use a wildcard to redirect all pages in that directory to the new page::

    Type: Page Redirect
    From URL: /examples/*
    To URL: /examples.html

Users will now be redirected:

- From ``https://docs.example.com/en/latest/examples/``
  to ``https://docs.example.com/en/latest/examples.html``.
- From ``https://docs.example.com/en/latest/examples/intro.html``
  to ``https://docs.example.com/en/latest/examples.html``.

If you want this redirect to apply to a specific version of your documentation,
you can create a redirect with the following configuration::

    Type: Exact Redirect
    From URL: /en/latest/examples/*
    To URL: /en/latest/examples.html

.. note::

   Use the desired version and language instead of ``latest`` and ``en``.

Redirecting a page to the latest version
````````````````````````````````````````

Say you want your users to always be redirected to the latest version of a page,
your security policy (``/security.html``) for example.
You can use a wildcard with a forced redirect to redirect all versions of that page to the latest version::

    Type: Page Redirect
    From URL: /security.html
    To URL: https://docs.example.com/en/latest/security.html
    Force Redirect: True

Users will now be redirected:

- From ``https://docs.example.com/en/v1.0/security.html``
  to ``https://docs.example.com/en/latest/security.html``.
- From ``https://docs.example.com/en/v2.5/security.html``
  to ``https://docs.example.com/en/latest/security.html``.

.. note::

   ``To URL`` includes the domain, this is required,
   otherwise the redirect will be relative to the current version,
   resulting in a redirect to ``https://docs.example.com/en/v1.0/en/latest/security.html``.

Redirecting an old version to a new one
```````````````````````````````````````

Let's say that you want to redirect your readers of your version ``2.0`` of your documentation under ``/en/2.0/`` because it's deprecated,
to the newest ``3.0`` version of it at ``/en/3.0/``.
You can use an exact redirect to do so::

  Type: Exact Redirect
  From URL: /en/2.0/*
  To URL: /en/3.0/:splat

Users will now be redirected:

- From ``https://docs.example.com/en/2.0/dev/install.html``
  to ``https://docs.example.com/en/3.0/dev/install.html``.

.. note::

   For this redirect to work, your old version must be disabled,
   if the version is still active, you can use the ``Force Redirect`` option.

Creating a shortlink
````````````````````

Say you want to redirect ``https://docs.example.com/security`` to ``https://docs.example.com/en/latest/security.html``,
so it's easier to share the link to the page.
You can create a redirect with the following configuration::

    Type: Exact Redirect
    From URL: /security
    To URL: /en/latest/security.html

Users will now be redirected:

- From ``https://docs.example.com/security`` (no trailing slash)
  to ``https://docs.example.com/en/latest/security.html``.
- From ``https://docs.example.com/security/`` (trailing slash)
  to ``https://docs.example.com/en/latest/security.html``.

Migrating your docs to Read the Docs
````````````````````````````````````

Say that you previously had your docs hosted at ``https://docs.example.com/dev/``,
and choose to migrate to Read the Docs with support for multiple versions and translations.
Your documentation will now be served at ``https://docs.example.com/en/latest/``,
but your users may have bookmarks saved with the old URL structure, for example ``https://docs.example.com/dev/install.html``.

You can use an exact redirect with a wildcard to redirect all pages from the old URL structure to the new one::

   Type: Exact Redirect
   From URL: /dev/*
   To URL: /en/latest/:splat

Users will now be redirected:

- From ``https://docs.example.com/dev/install.html``
  to ``https://docs.example.com/en/latest/install.html``.

Migrating your documentation to another domain
``````````````````````````````````````````````

You can use an exact redirect with the force option to migrate your documentation to another domain,
for example::

  Type: Exact Redirect
  From URL: /*
  To URL: https://newdocs.example.com/:splat
  Force Redirect: True

Users will now be redirected:

- From ``https://docs.example.com/en/latest/install.html``
  to ``https://newdocs.example.com/en/latest/install.html``.

Changing your Sphinx builder from ``html`` to ``dirhtml``
`````````````````````````````````````````````````````````

When you change your Sphinx builder from ``html`` to ``dirhtml``,
all your URLs will change from ``/page.html`` to ``/page/``.
You can create a redirect of type ``HTML to clean URL`` to redirect all your old URLs to the new style.
