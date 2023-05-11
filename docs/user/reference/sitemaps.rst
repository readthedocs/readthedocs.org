``sitemap.xml`` support
=======================

`Sitemaps <https://www.sitemaps.org/>`__ allow you to inform search engines about URLs that are available for crawling.
This makes your content more :term:`discoverable <discoverability>`,
and improves your :doc:`Search Engine Optimization (SEO) </guides/technical-docs-seo-guide>`.

How it works
------------

The ``sitemap.xml`` file is read by search engines in order to index your documentation.
It contains information such as:

* When a URL was last updated.
* How often that URL changes.
* How important this URL is in relation to other URLs in the site.
* What translations are available for a page.

Read the Docs automatically generates a ``sitemap.xml`` for your project,

By default the sitemap includes:

* Each version of your documentation and when it was last updated, sorted by version number.

This allows search engines to prioritize results based on the version number,
sorted by `semantic versioning`_.

Custom ``sitemap.xml``
----------------------

If you need a custom sitemap,
please let us know by contacting :doc:`/support`.

.. _semantic versioning: https://semver.org/
.. _GitHub issue #5391: https://github.com/readthedocs/readthedocs.org/issues/5391
