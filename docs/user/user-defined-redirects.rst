Custom and built-in redirects on Read the Docs
==============================================

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


Limitations
-----------

- By default, redirects only apply on pages that don't exist.
  **Forced redirects** allow you to apply redirects on existing pages,
  but incur a small performance penalty, so aren't enabled by default.
  You can ask for them to be enabled via support.
- Only :ref:`user-defined-redirects:page redirects` and :ref:`user-defined-redirects:exact redirects`
  can redirect to URLs outside Read the Docs,
  just include the protocol in ``To URL``, e.g ``https://example.com``.

Built-in redirects
------------------

This section explains the redirects that are automatically active for all projects and how they are useful.
Built-in redirects are especially useful for creating and sharing incoming links,
which is discussed indepth in :doc:`/guides/best-practice/links`.

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

.. TODO: Remove this once the feature is default on .com

This redirect is currently only active on |org_brand| (``<slug>.readthedocs.io`` and :doc:`custom domains </custom-domains>`).

Root language redirects on |com_brand| can be enabled by contacting :doc:`support </support>`.

For example, accessing the English language of the project will redirect you to the its version (``stable``)::

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

Prefix redirects
~~~~~~~~~~~~~~~~

The most useful and requested feature of redirects was when migrating to Read the Docs from an old host.
You would have your docs served at a previous URL,
but that URL would break once you moved them.
Read the Docs includes a language and version slug in your documentation,
but not all documentation is hosted this way.

Say that you previously had your docs hosted at ``https://docs.example.com/dev/``,
you move ``docs.example.com`` to point at Read the Docs.
So users will have a bookmark saved to a page at ``https://docs.example.com/dev/install.html``.

You can now set a *Prefix Redirect* that will redirect all 404's with a prefix to a new place.
The example configuration would be::

    Type: Prefix Redirect
    From URL: /dev/

Your users query would now redirect in the following manner::

        docs.example.com/dev/install.html ->
        docs.example.com/en/latest/install.html

Where ``en`` and ``latest`` are the default language and version values for your project.

.. note::

   If you were hosting your docs without a prefix, you can create a ``/`` Prefix Redirect,
   which will prepend ``/$lang/$version/`` to all incoming URLs.


Page redirects
~~~~~~~~~~~~~~

A more specific case is when you move a page around in your docs.
The old page will start 404'ing,
and your users will be confused.
*Page Redirects* let you redirect a specific page.

Say you move the ``example.html`` page into a subdirectory of examples: ``examples/intro.html``.
You would set the following configuration::

    Type: Page Redirect
    From URL: /example.html
    To URL: /examples/intro.html

**Page Redirects apply to all versions of your documentation.**
Because of this,
the ``/`` at the start of the ``From URL`` doesn't include the ``/$lang/$version`` prefix (e.g.
``/en/latest``), but just the version-specific part of the URL.
If you want to set redirects only for some languages or some versions, you should use
:ref:`user-defined-redirects:exact redirects` with the fully-specified path.

Exact redirects
~~~~~~~~~~~~~~~

*Exact Redirects* are for redirecting a single URL,
taking into account the full URL (including language and version).

You can also redirect a subset of URLs by including the ``$rest`` keyword
at the end of the ``From URL``.

Exact redirects examples
^^^^^^^^^^^^^^^^^^^^^^^^

Redirecting a single URL
````````````````````````

Say you're moving ``docs.example.com`` to Read the Docs and want to redirect traffic
from an old page at ``https://docs.example.com/dev/install.html`` to a new URL
of ``https://docs.example.com/en/latest/installing-your-site.html``.

The example configuration would be::

    Type: Exact Redirect
    From URL: /dev/install.html
    To URL:   /en/latest/installing-your-site.html

Your users query would now redirect in the following manner::

        docs.example.com/dev/install.html ->
        docs.example.com/en/latest/installing-your-site.html

Note that you should insert the desired language for "en" and version for "latest" to
achieve the desired redirect.

Redirecting a whole sub-path to a different one
```````````````````````````````````````````````

*Exact Redirects* could be also useful to redirect a whole sub-path to a different one by using a special ``$rest`` keyword in the "From URL".
Let's say that you want to redirect your readers of your version ``2.0`` of your documentation under ``/en/2.0/`` because it's deprecated,
to the newest ``3.0`` version of it at ``/en/3.0/``.

This example would be::

  Type: Exact Redirect
  From URL: /en/2.0/$rest
  To URL: /en/3.0/

The readers of your documentation will now be redirected as::

  docs.example.com/en/2.0/dev/install.html ->
  docs.example.com/en/3.0/dev/install.html

Similarly, if you maintain several branches of your documentation (e.g. ``3.0`` and
``latest``) and decide to move pages in ``latest`` but not the older branches, you can use
*Exact Redirects* to do so.

Migrating your documentation to another domain
``````````````````````````````````````````````

You can use an exact redirect to migrate your documentation to another domain,
for example::

  Type: Exact Redirect
  From URL: /$rest
  To URL: https://newdocs.example.com/
  Force Redirect: True

Then all pages will redirect to the new domain, for example
``https://docs.example.com/en/latest/install.html`` will redirect to
``https://newdocs.example.com/en/latest/install.html``.

Sphinx redirects
~~~~~~~~~~~~~~~~

We also support redirects for changing the type of documentation Sphinx is building.
If you switch between *HTMLDir* and *HTML*, your URLs will change.
A page at ``/en/latest/install.html`` will be served at ``/en/latest/install/``,
or vice versa.
The built in redirects for this will handle redirecting users appropriately.
