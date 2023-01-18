Incoming links: Best practices and redirects
============================================

Once you start to publish documentation,
it will inevitably be referenced in external sources.

Sources of incoming links vary greatly depending on the type of documentation project that is published.
They can include everything from old emails to GitHub issues, wiki articles, software comments, PDF publications, StackOverflow answers etc.
Most of these incoming sources are either unmanageable or not in your control.

Read the Docs makes it easier to create and manage incoming links by redirecting certain URLs automatically
and giving you access to define your own redirects.

In this article,
we explain how our built-in redirects work and what we consider "best practice" for managing incoming links.

.. seealso::

   :doc:`/versions`
     Read more about how to handle versioned documentation and URL structures.

   :doc:`/user-defined-redirects`
     If you delete or move a page,
     you can setup a redirect in place of the old location and choose where users should be redirected.


Built-in redirect rules
-----------------------

This article explains the redirects that are automatically active for all Read the Docs projects and how they are useful.
Automatic redirects on Read the Docs are supported long-term.

Page redirects at ``/page/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can link to a specific page and have it redirect to your default version.
This is done with the ``/page/`` URL prefix.
You can reach this page by going to https://docs.readthedocs.io/page/automatic-redirects.html.

This allows you to create links on external sources that are always up to date.

Another way to handle this is the ``latest`` version.
You can set your ``latest`` version to a specific version and just always link to ``latest``.
You can reach this page by going to https://docs.readthedocs.io/en/latest/automatic-redirects.html.


Root URL redirect at ``/``
~~~~~~~~~~~~~~~~~~~~~~~~~~

A link to the root of your documentation (`<slug>.readthedocs.io/`) will redirect to the  :term:`default version`,
as set in your project settings.

This works for both readthedocs.io (|org_brand|), readthedocs-hosted.com (|com_brand|), and :doc:`custom domains </custom-domains>`.

For example::

    docs.readthedocs.io -> docs.readthedocs.io/en/latest/
    www.pip-installer.org -> www.pip-installer.org/en/latest/

.. warning::

   This only works for the root URL, not for internal pages.
   It's designed to redirect people from `/` to the default version of your documentation,
   since serving up a 404 here would be bad user experience.

.. note::
   If the "develop" branch was designated as the default version,
   then ``http://pip.readthedocs.io/`` would redirect to ``http://pip.readthedocs.io/en/develop``.
   But, it's not a universal redirecting solution.
   So, for example, a link to an internal page like
   ``http://pip.readthedocs.io/usage.html`` doesn't redirect to ``http://pip.readthedocs.io/en/latest/usage.html``.

   The reasoning behind this is that RTD organizes the URLs for docs so that multiple translations and multiple versions of your docs can be organized logically and consistently for all projects that RTD hosts.
   For the way that RTD views docs,
   ``http://pip.readthedocs.io/en/latest/`` is the root directory for your default documentation in English, not ``http://pip.readthedocs.io/``.
   Just like ``http://pip.readthedocs.io/en/develop/`` is the root for your development documentation in English.

Among all the multiple versions of docs,
you can choose which is the "default" version for Read the Docs to display,
which usually corresponds to the git branch of the most recent official release from your project.

Shortlink with ``https://*.rtfd.io``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Links to ``rtfd.io`` are treated the same way as ``readthedocs.io``.
They redirect the root URL to the default version of the project.
They are intended to be easy and short for people to type.

You can reach these docs at https://docs.rtfd.io.

Best practice: "permalink" your pages
-------------------------------------

You might be familiar with :term:`permalinks <permalink>` from blogging.
The idea is that a blog post receives a unique link as soon as it's published and that the link does not change afterward.
Incoming sources can reference the blog post even though the blog changes structure or the post title changes.

When creating an external link to a specific documentation page,
chances are that the page is moved as the documentation changes over time.

How should a permalink look for a documentation project?
Firstly, you should know that a *permalink* does not really exist in documentation but it is the result of careful actions to avoid breaking incoming links.

As a documentation owner,
you most likely want users clicking on incoming links to see the latest version of the page.

Good practice ✅
~~~~~~~~~~~~~~~~

* Use `page redirects <Redirecting to a page>`_ if you are linking to the page in the default version of the default language.
* If you move a page that likely has incoming references, :doc:`create a redirect rule </user-defined-redirects>`.
* Links from other Sphinx projects should use :doc:`intersphinx </guides/intersphinx>`.
* Use minimal page :term:`slugs <slug>` that do not attract renaming suggestions.
* When possible,
  keep original file names rather than going for low-impact URL renaming.
  Renaming an article's title is great for the reader and great for SEO,
  but this does not have to involve the URL.
* Try to get your understanding of ``latest`` and *default version* right from the beginning and ensure you don't change them later on.
* Keep development versions hidden so people do not find them on search engines by mistake.
  Publishing documentation at the wrong URL can be costly if the URL starts circulating.

Questionable practice 🟡
~~~~~~~~~~~~~~~~~~~~~~~~

* Avoid using specific versions in links unless you really mean that users should see that exact version.
  Versions get outdated.
  You can use a :ref:`version warning <versions:Version warning>` to ensure the reader is aware.
* Avoid using a public ``latest`` for development versions and do not make your *default version* a development branch.
  Publishing development branches can mean that users are reading instructions for unreleased software or draft documentation.

.. tip::

   404 pages are okay!
   If documentation pages have been removed or moved,
   it can make the maintainer of the referring website aware that they need to update their link.
   Users will be aware that the documentation still exist but has changed.

   The default Read the Docs 404 page is designed to be helpful,
   but you can also design your own, see :ref:`hosting:Custom Not Found (404) Pages`.
