Custom Domains
==============

Custom domains allow you to serve your documentation from your own domain.
For instance, this could be ``docs.example.com``.
This is great for maintaining a consistent brand for your documentation and application.

*By default*, your documentation is served from a Read the Docs :ref:`subdomain <hosting:subdomain support>` using the project's :term:`slug`:

* ``<slug>.readthedocs.io`` for |org_brand|
* ``<slug>.readthedocs-hosted.com`` for |com_brand|.

For example if you import your project and it gets the :term:`slug` ``example-docs``, it will be served from ``https://example-docs.readthedocs.io``.

How does it work?
-----------------

To begin using a custom domain, you will need to create a new custom domain for your project and add a DNS record for your new custom domain.
Once the DNS record has propagated, an SSL certificate will be automatically issued for your custom domain and your documentation will be configured to serve using the new domain and certificate.

In case you change your domain name, your documentation can have multiple secondary domains but only one canonical domain name.
Additional domains or subdomains will redirect to the canonical domain.

What to consider
----------------

Some Open Source projects have seen their domains expire. Even prominent ones.
It's important that you allocate the responsibility of your domain to a reliable actor in your organization.
The domain will feature in search indexing and if you lose the domain, domain sharks may exploit this.


.. seealso::

    :doc:`/guides/custom-domains`
        Information on creating and managing custom domains, and common configurations you might use to set up your domain
