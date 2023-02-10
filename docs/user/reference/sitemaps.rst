Sitemaps
========

`Sitemaps <https://www.sitemaps.org/>`__ allow you to inform search engines about URLs that are available for crawling.
This helps make your content more discoverable,
and improve your Search Engine Optimization (SEO).

How it works
------------

The ``sitemap.xml`` file is read by search engines in order to index your documentation.
It contains information such as:

* When a URL was last updated.
* How often that URL changes.
* How important this URL is in relation to other URLs in the site.
* What translations are available for a page.

Read the Docs automatically generates a sitemap for your project,
to improve results when performing a search on these search engines.

By default our Sitemap includes:

* Each version of your documentation and when it was last updated, sorted by version number.

This allows search engines to prioritize results based on the version number,
sorted by `semantic versioning`_.

Custom ``sitemap.xml``
----------------------

If you need a custom sitemap,
please let us know by contacting :doc:`/support`.
It's on our long term roadmap,
but hearing that users want it is a great way to have us prioritize it.

.. _semantic versioning: https://semver.org/
.. _GitHub issue #5391: https://github.com/readthedocs/readthedocs.org/issues/5391
