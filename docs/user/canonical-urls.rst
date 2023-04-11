Canonical URLs
==============

A `canonical URL`_
allows you to specify the preferred version of a web page to prevent duplicated content.
Here are some examples of when a canonical URL is used:

- Search engines use your canonical URL to link users to the correct version and domain of your documentation.
- Many popular chat clients and social media networks generate link previews,
  using your canonical URL as the final destination.

If canonical URLs aren't used,
it's easy for outdated documentation to be the top search result for various pages in your documentation.
This is not a perfect solution for this problem,
but generally people finding outdated documentation is a big problem,
and this is one of the suggested ways to solve it from search engines.

.. _canonical URL: https://developers.google.com/search/docs/advanced/crawling/consolidate-duplicate-urls

.. tip::

   In most cases, Read the Docs will automatically generate a canonical URL for Sphinx projects.
   Most Sphinx users do not need to take further action.

.. seealso::

   :doc:`/guides/canonical-urls`
      More information on how to enable canonical URLs in your project.

How Read the Docs generates canonical URLs
------------------------------------------

The canonical URL takes the following into account:

* The default version of your project (usually "latest" or "stable").
* The canonical :doc:`custom domain </custom-domains>` if you have one,
  otherwise the default :ref:`subdomain <default-subdomain>` will be used.

For example, if you have a project named ``example-docs``
with a custom domain ``https://docs.example.com``,
then your documentation will be served at ``https://example-docs.readthedocs.io`` and ``https://docs.example.com``.
Without specifying a canonical URL, a search engine like Google will index both domains.

You'll want to use ``https://docs.example.com`` as your canonical domain.
This means that when Google indexes a page like ``https://example-docs.readthedocs.io/en/latest/``,
it will know that it should really point at ``https://docs.example.com/en/latest/``,
thus avoiding duplicating the content.

.. note::

   If you want your custom domain to be set as the canonical, you need to set ``Canonical:  This domain is the primary one where the documentation is served from`` in the :guilabel:`Admin` > :guilabel:`Domains` section of your project settings.

Implementation
--------------

A canonical URL is automatically specified in the HTML output with a ``<link>`` element.
For instance, regardless of whether you are viewing this page on ``/en/latest`` or ``/en/stable``,
the following HTML header data will be present:

.. code-block:: html

   <link rel="canonical" href="https://docs.readthedocs.io/en/stable/canonical-urls.html" />
