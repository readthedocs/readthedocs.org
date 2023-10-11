Custom domains
==============

By configuring a *custom domain* for your project,
your project can serve documentation from a domain you control,
for instance ``docs.example.com``.
This is great for maintaining a consistent brand for your product and its documentation.

.. _default-subdomain:

.. rubric:: Default subdomains

*Without a custom domain configured*,
your project's documentation is served from a Read the Docs domain using a unique subdomain for your project:

* ``<project name>.readthedocs.io`` for |org_brand|.
* ``<organization name>-<project name>.readthedocs-hosted.com`` for |com_brand|.
  The addition of the organization name allows multiple organizations to have projects with the same name.

.. seealso::

   :doc:`/guides/custom-domains`
      How to create and manage custom domains for your project.

Features
--------

Automatic SSL
   SSL certificates are automatically issued through Cloudflare for every custom domain.
   No extra set up is required beyond configuring your project's custom domain.

CDN caching
   Response caching is provided through a :doc:`CDN </reference/cdn>` for all documentation projects,
   including projects using a custom domain.
   CDN caching improves page response time for your documentation's users,
   and the CDN edge network provides low latency response times regardless of location.

Multiple domains
   Projects can be configured to be served from multiple domains,
   which always includes the :ref:`project's default subdomain <default-subdomain>`.
   Only one domain can be configured as the canonical domain however,
   and any requests to non-canonical domains and subdomains will redirect to the canonical domain.

Canonical domains
   The canonical domain configures the primary domain the documentation will serve from,
   and also sets the domain search engines use for search results when hosting from multiple domains.
   Projects can only have one canonical domain,
   which is the :ref:`project's default subdomain <default-subdomain>` if no other canonical domain is defined.

.. seealso::

   :doc:`/canonical-urls`
      How canonical domains affect your project's canonical URL,
      and why canonical URLs are important.

   :doc:`/subprojects`
      How to share a custom domain between multiple projects.
