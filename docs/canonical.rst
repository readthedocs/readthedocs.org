Canonical URLs
==============

Canonical URLs allow people to have consistent page URLs for domains.
This is mainly useful for search engines,
so that they can send people to the correct page.

Read the Docs uses these in two ways:

* We point all versions of your docs at the "latest" version as canonical
* We point at the user specififed canonical URL, generally a custom domain for your docs.

You can set the canonical URL for your project in the Edit Project page.

Implementation
--------------

If you look at the source code for documentation built after you set your canonical URL,
you should see a bit of HTML like this:

.. code-block: html

    <link rel="canonical" href="http://pip.readthedocs.org/en/latest/installing.html">

Links
-----

This is a good explanation of the usage of canonical URLs in search engines: 

http://www.mattcutts.com/blog/seo-advice-url-canonicalization/

This is a good explanation for why canonical pages are good for SEO:

http://moz.com/blog/canonical-url-tag-the-most-important-advancement-in-seo-practices-since-sitemaps
