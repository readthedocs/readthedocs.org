=================
Feature reference
=================

.. TODO: Continue to add more features here.

Hosting features
----------------

⏩️ :doc:`/custom-domains`
  Documentation projects can use their own domain name.
  A project may define multiple domains,
  as well as define the *canonical domain* where all other domains will redirect.


⏩️ :doc:`/versions`
  We support multiple versions and translations,
  integrated nicely into the URL of your documentation.
  This is served at ``/en/latest/`` by default.
  If you only have 1 version and translation,
  we also support :doc:`single version projects </single_version>` served at ``/``.


⏩️ :doc:`/user-defined-redirects`
  Projects may define their own custom URL redirects,
  with advanced functionality like folder redirects.

⏩️ :doc:`/reference/cdn`
  Documentation projects are primarily static HTML pages along with media files.
  This allows us to cache them with our CDN,
  making them *load faster* for your users.


⏩️ :doc:`/reference/sitemaps`
  Sitemaps are generated and hosted automatically,
  improving search engine optimization.
  This helps your users find content more effectively on your site.


⏩️ :doc:`/reference/404-not-found`
  A 404 page is served when we can't find a page on your site.
  We provide a default 404 page,
  but you can also customize it.


⏩️ :doc:`/reference/robots`
  `robots.txt` files allow you to customize how your documentation is indexed in search engines.
  We provide a default robots.txt file,
  but you can also customize it.


⏩️ :doc:`/commercial/sharing`
  It is possible to host private and password protected documentation on Read the Docs for Business.

.. The TOC here will be refactored once we reorganize the files in docs/user/.
.. Probably, all feature reference should be in this directory!
.. In upcoming work, redirects will be added for old URL destinations.
.. In fact, this whole page will become a proper index page with more explanation of what sort of reference can
.. be found.

.. toctree::
   :maxdepth: 1
   :glob:

   ../features
   analytics
   /server-side-search/index
   /automation-rules
   /user-defined-redirects
   /badges
   /reference/cdn
   /reference/404-not-found
   /reference/robots
   /reference/sitemaps
   /security-log

   /config-file/index
   /integrations
   /versions
   /hosting

   /builds
   /build-customization
   /environment-variables
   /flyout-menu
   /canonical-urls
   /feature-flags
   /commercial/organizations
   /commercial/privacy-level
   /commercial/sharing
   /commercial/single-sign-on
