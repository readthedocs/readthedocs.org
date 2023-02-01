.. old label
.. _Documentation Hosting Features:

Hosting features provided by Read the Docs
==========================================

This article provides a quick overview and reference to how documentation is *hosted* on Read the Docs.
Hosting is optimized with documentation in mind and a number of special features are provided,
some of which may be customized.

.. seealso::

   :doc:`/reference/features`
    A complete list of our features.

Overview of hosting features
----------------------------

Subdomain support
  Every project has a subdomain that is available to serve its documentation based on it's :term:`slug`.
  If you go to ``<slug>.readthedocs.io``, it should show you the latest version of your documentation,
  for example https://docs.readthedocs.io.
  For :doc:`/commercial/index` the subdomain looks like ``<slug>.readthedocs-hosted.com``.

Custom domain support
  Documentation projects can also use their own domains.
  A project may define multiple domains,
  as well as define the *canonical domain* where all other domains will redirect.

  ⏩️ :doc:`Read more </custom-domains>`

Multiple documentation versions
  We allow for multiple versions and translations to be hosted,
  integrated nicely into the URL of your documentation.
  If you only have 1 version and translation,
  we support :doc:`single version projects </single_version>`.

  ⏩️ :doc:`Read more </versions>`

Redirect support
  Projects may define their own custom URL redirects rules that trigger in the HTTP layer.

  ⏩️ :doc:`Read more </user-defined-redirects>`

Content Delivery Network (CDN)
  Documentation projects are by nature static HTML pages and assets.
  Hence contents are delivered through a speedy distributed cloud proxy.

  ⬇️ :ref:`Read more <hosting:Content Delivery Network (CDN) and caching>`

Sitemaps
  Sitemaps are generated and hosted automatically,
  improving search engine crawling.

  ⬇️ :ref:`Read more <hosting:Sitemaps>`

Custom 404s
  A 404 page is provided by default. It may be replaced with a projects own 404 page.

  ⬇️ :ref:`Read more <hosting:Custom Not Found (404) pages>`

Automatic and custom robots.txt
  `robots.txt`_ files allow you to customize how your documentation is indexed in search engines.
  We automatically generate one for you, but you can also customize it.

  ⬇️ :ref:`Read more <hosting:Custom robots.txt>`


Content Delivery Network (CDN) and caching
------------------------------------------

A CDN is used for making documentation pages faster for your users.
This is done by caching the documentation page content in multiple data centers around the world,
and then serving docs from the data center closest to the user.

We support CDNs on both of our sites:

.. tabs::

   .. tab:: |org_brand|

      On |org_brand|,
      we are able to provide a CDN to all the projects that we host.
      This service is graciously sponsored by `Cloudflare`_.

      We bust the cache on the CDN when the following actions happen:

      * Your Project is saved
      * Your Domain is saved
      * A new version is built


   .. tab:: |com_brand|

      On |com_brand|,
      we offer a CDN as part of our **Pro plan** and above.
      Please contact support@readthedocs.com to discuss how we can enable this for you.

      We invalidate and refresh the cache on the CDN when the following actions happen:

      * Your project is saved
      * Your domain is saved
      * A version or branch is built

.. _Cloudflare: https://www.cloudflare.com/

Built-in content
----------------

A number of content files can be said to be "built-in",
since they are automatically generated and hosted together with your site.

They are also possible to customize.

Custom Not Found (404) pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want your project to use a custom page for not found pages instead of the "Maze Found" default,
you can put a ``404.html`` at the top level of your project's HTML output.

When a 404 is returned,
Read the Docs checks if there is a ``404.html`` in the root of your project's output
corresponding to the *current* version
and uses it if it exists.
Otherwise, it tries to fall back to the ``404.html`` page
corresponding to the *default* version of the project.

Sphinx and Mkdocs both have different ways of outputting static files in the build:

.. tabs::

   .. tab:: Sphinx

      We recommend the `sphinx-notfound-page`_ extension,
      which Read the Docs maintains.
      It automatically creates a ``404.html`` page for your documentation,
      matching the theme of your project.
      See its documentation_ for how to install and customize it.

      If you want to write the entire ``404.html`` from scratch,
      Sphinx uses `html_extra_path`_ option to add static files to the output.
      You need to create a ``404.html`` file and put it under the path defined in ``html_extra_path``.

   .. tab:: MkDocs

      MkDocs generates a ``404.html`` which Read the Docs will use.
      However, assets will not be loaded correctly unless you define the `site_url`_ configuration value as your site's
      :ref:`canonical base URL <canonical-urls:MkDocs>`.

.. _sphinx-notfound-page: https://pypi.org/project/sphinx-notfound-page
.. _documentation: https://sphinx-notfound-page.readthedocs.io/
.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url

Custom robots.txt
~~~~~~~~~~~~~~~~~

`robots.txt`_ files allow you to customize how your documentation is indexed in search engines.
We automatically generate one for you,
which automatically hides versions which are set to :ref:`versions:Hidden`.

The ``robots.txt`` file will be served from the **default version** of your Project.
This is because the ``robots.txt`` file is served at the top-level of your domain,
so we must choose a version to find the file in.
The **default version** is the best place to look for it.

Sphinx and Mkdocs both have different ways of outputting static files in the build:

.. tabs::

   .. tab:: Sphinx

      Sphinx uses the `html_extra_path`_ configuration value to add static files to its final HTML output.
      You need to create a ``robots.txt`` file and put it under the path defined in ``html_extra_path``.

   .. tab:: MkDocs

      MkDocs needs the ``robots.txt`` to be at the directory defined by the `docs_dir`_ configuration value.

.. _robots.txt: https://developers.google.com/search/reference/robots_txt
.. _html_extra_path: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_extra_path
.. _docs_dir: https://www.mkdocs.org/user-guide/configuration/#docs_dir

Sitemaps
~~~~~~~~

`Sitemaps <https://www.sitemaps.org/>`__ allows us to inform search engines about URLs that are available for crawling
and communicate them additional information about each URL of the project:

* When it was last updated.
* How often it changes.
* How important it is in relation to other URLs in the site.
* What translations are available for a page.

Read the Docs automatically generates a sitemap for each project that hosts
to improve results when performing a search on these search engines.
This allow us to prioritize results based on the version number, for example
to show ``stable`` as the top result followed by ``latest`` and then all the project's
versions sorted following `semantic versioning`_.

If you need a custom sitemap, please let us know in `GitHub issue #5391`_.

.. _semantic versioning: https://semver.org/
.. _GitHub issue #5391: https://github.com/readthedocs/readthedocs.org/issues/5391
