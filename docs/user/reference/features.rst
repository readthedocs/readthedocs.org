=================
Feature reference
=================

.. TODO: Continue to add more features here.

Hosting features
----------------

Custom domain support
  Documentation projects can use their own domain name.
  A project may define multiple domains,
  as well as define the *canonical domain* where all other domains will redirect.

  ⏩️ :doc:`/custom-domains`

Multiple documentation versions
  We support multiple versions and translations,
  integrated nicely into the URL of your documentation.
  This is served at ``/en/latest/`` by default.
  If you only have 1 version and translation,
  we also support :doc:`single version projects </single_version>` served at ``/``.

  ⏩️ :doc:`/versions`

Custom URL redirects
  Projects may define their own custom URL redirects,
  with advanced functionality like folder redirects.

  ⏩️ :doc:`/user-defined-redirects`

Content Delivery Network (CDN)
  Documentation projects are primarily static HTML pages along with media files.
  This allows us to cache them with our CDN,
  making them *load faster* for your users.

  ⬇️ :doc:`/reference/cdn`

Sitemaps
  Sitemaps are generated and hosted automatically,
  improving search engine optimization.
  This helps your users find content more effectively on your site.

  ⬇️ :doc:`/reference/sitemaps`

Custom ``404s Not Found`` pages
  A 404 page is served when we can't find a page on your site.
  We provide a default 404 page,
  but you can also customize it.

  ⬇️ :doc:`/reference/404-not-found`

Custom robots.txt
  `robots.txt` files allow you to customize how your documentation is indexed in search engines.
  We provide a default robots.txt file,
  but you can also customize it.

  ⬇️ :doc:`/reference/robots`

Private documentation
  It is possible to host private and password protected documentation on Read the Docs for Business.

  ⏩️ :doc:`/commercial/sharing`

.. The TOC here will be refactored once we reorganize the files in docs/user/.
.. Probably, all feature reference should be in this directory!
.. In upcoming work, redirects will be added for old URL destinations.
.. In fact, this whole page will become a proper index page with more explanation of what sort of reference can
.. be found.

.. toctree::
   :maxdepth: 1
   :hidden:

   ../features
   analytics
   /feature-flags
   /server-side-search/index
   /badges
   /reference/cdn
   /reference/404-not-found
   /reference/robots
   /reference/sitemaps
