Custom Domains
==============

Custom domains allow you to serve your documentation from your own domain.
For instance, this could be ``docs.example.com``.
This is great for maintaining a consistent brand for your documentation and application.

*By default*, your documentation is served from a Read the Docs :ref:`subdomain <hosting:subdomain support>` using the project's :term:`slug`:

* ``<slug>.readthedocs.io`` for |org_brand|
* ``<slug>.readthedocs-hosted.com`` for |com_brand|.

.. seealso::

    :doc:`/guides/custom-domains`
        Information on creating and managing custom domains, and common configurations you might use to set up your domain

How do custom domains work?
---------------------------

To use a custom domain, you enter the domain in your Read the Docs project's :guilabel:`Admin` and update your DNS provider with a new DNS entry.

These two actions are all that are needed. Once the DNS record has propagated, Read the Docs automatically issues an SSL certificate through Cloudflare and starts serving your documentation.

.. mermaid::

    graph TD
        subgraph rtd [On Read the Docs]
          A(fa:fa-pencil Add docs.example.com as Custom domain)
          A-->AA(fa:fa-spinner Your project is rebuilt with<br>docs.example.com as a canonical domain)
        end
        subgraph dns [On your domain's DNS administration]
          B(fa:fa-pencil Edit DNS entry for docs.example.com)
        end

        rtd & dns-->C(fa:fa-spinner Wait for DNS propogation<br>Usually just a few minutes)

        direction LR
        subgraph automatic [The rest is handled automatically]
          direction TB
          D(Visit https://docs.example.com)
          D-->E(fa:fa-lock SSL Certificate issued<br>dynamically)
          E-->F(fa:fa-check Read the Docs matches<br>docs.example.com with<br>your project<br>)
        end

        C-->automatic


Your documentation can have multiple secondary domains but only one **canonical** domain name.
Additional domains or subdomains will redirect to the canonical domain.

To make this work, Read the Docs generates a special text that you are responsible for copy-pasting to your domain's DNS.
In most cases, the ``CNAME`` record is used.
This is all that's needed for a web browser to resolve your domain name to Read the Docs' servers and for our servers to match the right documentation project.
You can find step-by-step instructions for this in :doc:`/guides/custom-domains`.


Considerations for custom domain usage
--------------------------------------

Some Open Source projects have seen their domains expire. Even prominent ones.
**It's important that you give the responsibility for managing your domain to someone reliable in your organization.**

The **canonical domain** feature allows you to have several domains and the canonical domain will be indexed by search engines.
The domain that you choose as your canonical domain is by far the most important one.
If you lose the canonical domain, someone else can set up a website that search results will end up referring to.


Canonical URLs
--------------

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. warning::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.

Implementation
^^^^^^^^^^^^^^

The canonical URL is set in HTML with a ``link`` element.
For example, this page has a canonical URL of:

.. code-block:: html

   <link rel="canonical" href="https://docs.readthedocs.io/en/stable/canonical-urls.html" />

Sphinx
^^^^^^

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will set the value of the html_baseurl_ setting (if isn't already set) to your canonical domain.
If you already have ``html_baseurl`` set, you need to ensure that the value is correct.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

MkDocs
^^^^^^

For :doc:`MkDocs </intro/getting-started-with-mkdocs>` this isn't done automatically,
but you can use the site_url_ setting to set a similar value.

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url
