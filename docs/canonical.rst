Canonical URLs
==============

Canonical URLs allow people to have consistent page URLs for domains.
This is mainly useful for search engines,
so that they can send people to the correct page.

Read the Docs uses these in two ways:

* We point all versions of your docs at the "latest" version as canonical
* We point at the user specified canonical URL, generally a custom domain for your docs.

Example
-------

Fabric hosts their docs on Read the Docs.
They mostly use their own domain for them ``http://docs.fabfile.org``.
This means that Google will index both ``http://fabric.readthedocs.org`` and ``http://docs.fabfile.org`` for their documentation.

Fabric will want to set ``http://docs.fabfile.org`` as their canonical URL.
This means that when Google indexes ``http://fabric.readthedocs.org``, it will know that it should really point at ``http://docs.fabfile.org``.

Turning them on
---------------

You can set the canonical URL for your project in the Project Admin page. Check your `dashboard`_ for a list of your projects.

Implementation
--------------

If you look at the source code for documentation built after you set your canonical URL,
you should see a bit of HTML like this:

.. code-block:: html

    <link rel="canonical" href="http://pip.readthedocs.org/en/latest/installing.html">

Links
-----

This is a good explanation of the usage of canonical URLs in search engines: 

http://www.mattcutts.com/blog/seo-advice-url-canonicalization/

This is a good explanation for why canonical pages are good for SEO:

http://moz.com/blog/canonical-url-tag-the-most-important-advancement-in-seo-practices-since-sitemaps

.. _dashboard: https://readthedocs.org/dashboard/
