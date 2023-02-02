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

      We invalidate and refresh the cache on the CDN when the following actions happen:

      * Your Project is saved.
      * Your Domain is saved.
      * A new version is built.


   .. tab:: |com_brand|

      On |com_brand|,
      we offer a CDN as part of our **Pro plan** and above.
      Please contact support@readthedocs.com to discuss how we can enable this for you.

      We invalidate and refresh the cache on the CDN when the following actions happen:

      * Your project is saved.
      * Your domain is saved.
      * A version or branch is built.

.. _Cloudflare: https://www.cloudflare.com/

Built-in content
----------------

A number of content files are automatically generated and hosted together with your site.
You can read more about these files and how to customize them in this section.

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
