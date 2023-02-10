Documentation hosting features
==============================

This page provides a quick overview of the *hosting features* on Read the Docs.
These features are designed with documentation in mind,
and provide a good experience for your users.

.. seealso::

   :doc:`/reference/features`
    A complete list of our features.

Overview of hosting features
----------------------------

Custom domain support
  Documentation projects can use their own domain name.
  A project may define multiple domains,
  as well as define the *canonical domain* where all other domains will redirect.

  ⏩️ :doc:`Read more </custom-domains>`

Multiple documentation versions
  We support multiple versions and translations,
  integrated nicely into the URL of your documentation.
  This is served at ``/en/latest/`` by default.
  If you only have 1 version and translation,
  we also support :doc:`single version projects </single_version>` served at ``/``.

  ⏩️ :doc:`Read more </versions>`

Custom URL redirects
  Projects may define their own custom URL redirects,
  with advanced functionality like folder redirects.

  ⏩️ :doc:`Read more </user-defined-redirects>`

Content Delivery Network (CDN)
  Documentation projects are primarily static HTML pages along with media files.
  This allows us to cache them with our CDN,
  making them *load faster* for your users.

  ⬇️ :ref:`Read more <hosting:Content Delivery Network (CDN) and caching>`

Sitemaps
  Sitemaps are generated and hosted automatically,
  improving search engine optimization.
  This helps your users find content more effectively on your site.

  ⬇️ :ref:`Read more <hosting:Sitemaps>`

Custom ``404s Not Found`` pages
  A 404 page is served when we can't find a page on your site.
  We provide a default 404 page,
  but you can also customize it.

  ⬇️ :ref:`Read more <hosting:Custom Not Found (404) pages>`

Custom robots.txt
  `robots.txt`_ files allow you to customize how your documentation is indexed in search engines.
  We provide a default robots.txt file,
  but you can also customize it.

  ⬇️ :ref:`Read more <hosting:Custom robots.txt>`

Private documentation
  It is possible to host private and password protected documentation on Read the Docs for Business.

  ⏩️ :doc:`Read more </commercial/sharing>`
