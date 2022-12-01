Custom Domains
==============

Custom domains allow you to serve your documentation from your own domain.
For instance, this could be ``docs.example.com``.
This is great for maintaining a consistent brand for your documentation and application.

*By default*, your documentation is served from a Read the Docs :ref:`subdomain <hosting:subdomain support>` using the project's :term:`slug`:

* ``<slug>.readthedocs.io`` for |org_brand|
* ``<slug>.readthedocs-hosted.com`` for |com_brand|.

How do custom domains work?
---------------------------

To use a custom domain, you enter the domain in your Read the Docs project's :guilabel:`Admin` and update your DNS provider with a new DNS entry.

These two actions are all that are needed. Once the DNS record has propagated, Read the Docs automatically issues an SSL certificate through Cloudflare and starts serving your documentation.

.. mermaid::

    graph LR
        subgraph rtd [On Read the Docs]
          A(Add docs.example.com as Custom domain)
        end
        subgraph dns [On your domain's DNS administration]
          B(Edit DNS entry for docs.example.com)
        end

        A & B-->C(fa:fa-spinner Wait for DNS propogation)

        direction TB
        subgraph automatic [Automatic handling]
          direction TB
          D(SSL Certificate is issued)
          D-->E(Resolving docs.example.com now works)
        end

        C-->automatic


Your documentation can have multiple secondary domains but only one **canonical** domain name.
Additional domains or subdomains will redirect to the canonical domain.

To make this work, Read the Docs generates a special text that you are responsible for copy-pasting to your domain's DNS.
In most cases, the ``CNAME`` record is used.
This is all that's needed for a web browser to resolve your domain name to Read the Docs' servers and for our servers to match the right documentation project.
You can find step-by-step instructions for this in :doc:`/guides/custom-domains`.


What to consider
----------------

Some Open Source projects have seen their domains expire. Even prominent ones.
**It's important that you give the responsibility for managing your domain to someone reliable in your organization.**

The **canonical domain** feature allows you to have several domains and the canonical domain will be indexed by search engines.
The domain that you choose as your canonical domain is by far the most important one.
If you lose the canonical domain, someone else can set up a website that search results will end up referring to.

.. seealso::

    :doc:`/guides/custom-domains`
        Information on creating and managing custom domains, and common configurations you might use to set up your domain
