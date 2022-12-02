Canonical URLs
==============

A `canonical URL`_
allows you to specify the preferred version of a web page to prevent duplicated content.
They are mainly used by search engines to link users to the correct
version and domain of your documentation.

If canonical URL's aren't used,
it's easy for outdated documentation to be the top search result for various pages in your documentation.
This is not a perfect solution for this problem,
but generally people finding outdated documentation is a big problem,
and this is one of the suggested ways to solve it from search engines.

.. _canonical URL: https://developers.google.com/search/docs/advanced/crawling/consolidate-duplicate-urls

How Read the Docs generates canonical URLs
------------------------------------------

The canonical URL takes into account:

* The default version of your project (usually "latest" or "stable").
* The canonical :doc:`custom domain </custom-domains>` if you have one,
  otherwise the default :ref:`subdomain <hosting:subdomain support>` will be used.

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

The canonical URL is set in HTML with a ``link`` element.
For example, this page has a canonical URL of:

.. code-block:: html

   <link rel="canonical" href="https://docs.readthedocs.io/en/stable/canonical-urls.html" />

Sphinx
~~~~~~

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will set the value of the html_baseurl_ setting (if isn't already set) to your canonical domain.
If you already have ``html_baseurl`` set, you need to ensure that the value is correct.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

Mkdocs
~~~~~~

For :doc:`MkDocs </intro/getting-started-with-mkdocs>` this isn't done automatically,
but you can use the site_url_ setting to set a similar value.

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url

.. warning::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.
