Documentation Hosting Features
==============================

The main way that users interact with your documentation is via the hosted HTML that we serve.
We support a number of important features that you would expect for a documentation host.

.. contents:: Contents
   :local:
   :depth: 1

Content Delivery Network (CDN)
------------------------------

A CDN is used for making documentation pages faster for your users.
This is done by caching the documentation page content in multiple data centers around the world,
and then serving docs from the data center closest to the user.

We support CDN's on both of our sites,
as we talk about below.

.. tabs::
   
   .. tab:: |org_brand|

      On |org_brand|,
      we are able to provide a CDN to all the projects that we host.
      This service is graciously sponsored by `CloudFlare`_.

      We bust the cache on the CDN when the following actions happen:

      * Your Project is saved
      * Your Domain is saved
      * A new version is built


   .. tab:: |com_brand|

      On |com_brand|,
      we offer a CDN as part of our Enterprise plan.
      Please contact support@readthedocs.com to discuss how we can enable this for you.

.. _CloudFlare: https://www.cloudflare.com/

Sitemaps
--------

`Sitemaps <https://www.sitemaps.org/>`__ allows us to inform search engines about URLs that are available for crawling
and communicate them additional information about each URL of the project:

* when it was last updated,
* how often it changes,
* how important it is in relation to other URLs in the site, and
* what translations are available for a page.

Read the Docs automatically generates a sitemap for each project that hosts
to improve results when performing a search on these search engines.
This allow us to prioritize results based on the version number, for example
to show ``stable`` as the top result followed by ``latest`` and then all the project's
versions sorted following `semantic versioning`_.

.. _semantic versioning: https://semver.org/

Custom Not Found (404) Pages
----------------------------

If you want your project to use a custom page for not found pages instead of the "Maze Found" default,
you can put a ``404.html`` at the top level of your project's HTML output.

When a 404 is returned,
Read the Docs checks if there is a ``404.html`` in the root of your project's output
corresponding to the *current* version
and uses it if it exists.
Otherwise, it tries to fall back to the ``404.html`` page
corresponding to the *default* version of the project.

We recommend the `sphinx-notfound-page`_ extension,
which Read the Docs maintains.
It automatically creates a ``404.html`` page for your documentation,
matching the theme of your project.
See its documentation_ for how to install and customize it.

.. _sphinx-notfound-page: https://pypi.org/project/sphinx-notfound-page
.. _documentation: https://sphinx-notfound-page.readthedocs.io/

Custom robots.txt Pages
-----------------------

`robots.txt`_ files allow you to customize how your documentation is indexed in search engines.
We automatically generate one for you,
which automatically hides versions which are set to :ref:`versions:Hidden`.

The ``robots.txt`` file will be served from the **default version** of your Project.
This is because the ``robots.txt`` file is served at the top-level of your domain,
so we must choose a version to find the file in.
The **default version** is the best place to look for it.

Sphinx and Mkdocs both have different ways of outputting static files in the build:

Sphinx
~~~~~~

Sphinx uses `html_extra_path`_ option to add static files to the output.
You need to create a ``robots.txt`` file and put it under the path defined in ``html_extra_path``.

MkDocs
~~~~~~

MkDocs needs the ``robots.txt`` to be at the directory defined at `docs_dir`_ config.

.. _robots.txt: https://developers.google.com/search/reference/robots_txt
.. _html_extra_path: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_extra_path
.. _docs_dir: https://www.mkdocs.org/user-guide/configuration/#docs_dir
