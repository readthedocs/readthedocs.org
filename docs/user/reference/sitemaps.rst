Sitemap support
===============

`Sitemaps <https://www.sitemaps.org/>`__ allow you to inform search engines about URLs that are available for crawling.
This makes your content more :term:`discoverable <discoverability>`,
and improves your :doc:`Search Engine Optimization (SEO) </guides/technical-docs-seo-guide>`.

How it works
------------

The ``sitemap.xml`` file is read by search engines to index your documentation.
It contains information such as:

* When a URL was last updated.
* How often that URL changes.
* How important this URL is in relation to other URLs on the site.
* What translations are available for a page.

Read the Docs automatically generates a ``sitemap.xml`` for your project.
The sitemap includes :ref:`public and not hidden versions <versions:Version states>` of your documentation and when they were last updated,
sorted by version number.

This allows search engines to prioritize results based on the version number,
sorted by `semantic versioning`_.

Custom ``sitemap.xml``
----------------------

You can control the sitemap that is used via the ``robots.txt`` file.
Our :doc:`/reference/robots` allows you to host a custom version of this file.

An example would look like::

  User-agent: *
  Allow: /

  Sitemap: https://docs.example.com/en/stable/sitemap.xml

.. _semantic versioning: https://semver.org/
