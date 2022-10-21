Custom Domains
==============

Custom domains allow you to serve your documentation from your own domain.
This is great for maintaining a consistent brand for your documentation and application.

By default, your documentation is served from a Read the Docs :ref:`subdomain <hosting:subdomain support>` using the project's :term:`slug`:

* ``<slug>.readthedocs.io`` for |org_brand|
* ``<slug>.readthedocs-hosted.com`` for |com_brand|.

For example if you import your project and it gets the :term:`slug` ``example-docs``, it will be served from ``https://example-docs.readthedocs.io``.

How does it work?
-----------------

If you own a domain and would like to use it for your documentation, Read the Docs requires only :ref:`a single edit <adding_domain>` to the DNS settings of the domain.
After this, your documentation will be served from your domain and SSL will also be configured automatically.

In case you change your domain name, your documentation can have multiple secondary domains but only one canonical domain name.
Additional domains or subdomains will redirect to the canonical domain.

.. seealso::

    :doc:`/guides/custom-domains`
        Information on creating and managing custom domains, and common configurations you might use to set up your domain
