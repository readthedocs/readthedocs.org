=================
Feature reference
=================

.. TODO: Continue to add more features here.

⏩️ :doc:`/custom-domains`
  Documentation projects can use their own domain name.
  A project may define multiple domains,
  as well as define the *canonical domain* where all other domains will redirect.

⏩️ :doc:`/reference/git-integration`
  Read the Docs integrates with |git_providers_and|.
  This makes your Git repositories easy to import and configure automatically.

  Note that we also support other Git providers through :doc:`manual configuration </guides/setup/git-repo-manual>`.

⏩️ :doc:`/versions`
  We support multiple versions and translations,
  integrated nicely into the URL of your documentation.
  This is served at ``/en/latest/`` by default.
  If you only have 1 version and translation,
  we also support :doc:`single version projects </single-version>` served at ``/``.

⏩️ :doc:`/pull-requests`
  Your project can be configured to build and host documentation for every new pull request.
  Previewing changes during review makes it easier to catch formatting and display issues.

⏩️ :doc:`/build-notifications`
  Build notifications can alert you when your builds fail so you can take immediate action.

⏩️ :doc:`/reference/analytics`
  Traffic and Search analytics are built into the platform.
  This allows you to easily see what the most popular pages are,
  and what people are searching for.

⏩️ :doc:`/user-defined-redirects`
  Projects may define their own custom URL redirects,
  with advanced functionality like folder redirects.

⏩️ :doc:`/commercial/sharing`
  It is possible to host private and password protected documentation on Read the Docs for Business.

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

.. The TOC here will be refactored once we reorganize the files in docs/user/.
.. Probably, all feature reference should be in this directory!
.. In upcoming work, redirects will be added for old URL destinations.
.. In fact, this whole page will become a proper index page with more explanation of what sort of reference can
.. be found.

.. toctree::
   :maxdepth: 1
   :caption: Hosting Features

   /custom-domains
   /reference/git-integration
   /versions
   /pull-requests
   /build-notifications
   /user-defined-redirects
   /reference/analytics
   /commercial/sharing
   /reference/cdn
   /reference/sitemaps
   /reference/404-not-found
   /reference/robots

.. Move these to the above TOC once they're in the fancy list above

.. toctree::
   :maxdepth: 1
   :caption: Business features

   /commercial/organizations
   /commercial/privacy-level
   /commercial/single-sign-on

.. toctree::
   :maxdepth: 1
   :caption: Additional features

   /automation-rules
   /badges
   /canonical-urls
   /flyout-menu
   /reference/environment-variables
   /security-log
   /server-side-search/index
   /single-version
   /science
