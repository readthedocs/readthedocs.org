Custom domains
==============

You can serve your documentation project from your own domain,
for instance ``docs.example.com``.
This is great for maintaining a consistent brand for your product and its documentation.

.. _default-subdomain:

.. rubric:: Default subdomains

*Without a custom domain configured*,
your project's documentation is served from a Read the Docs domain using a unique subdomain for your project:

* ``{project name}.readthedocs.io`` for |org_brand|.
* ``{organization name}-{project name}.readthedocs-hosted.com`` for |com_brand|.
  The addition of the organization name allows multiple organizations to have projects with the same name.

.. seealso::

    :doc:`/guides/custom-domains`
        Information on creating and managing custom domains,
        and common configurations you might use to set up your domain

How custom domains work
-----------------------

To use a custom domain, two actions are needed from you:

#.  Enter the domain in your Read the Docs project's :guilabel:`Admin`
#.  Update your DNS provider with a new DNS entry. The name and value of the DNS entry is found in Read the Docs' :guilabel:`Admin`.

Once the new DNS record has propagated,
Read the Docs automatically issues an SSL certificate through Cloudflare and starts serving your documentation.

Your documentation can have multiple secondary domains but only one **canonical** domain name.
Additional domains or subdomains will redirect to the canonical domain.

To make this work, Read the Docs generates a special text that you are responsible for copy-pasting to your domain's DNS.
In most cases, the ``CNAME`` record is used.
This is all that's needed for a web browser to resolve your domain name to Read the Docs' servers and for our servers to match the right documentation project.
You can find step-by-step instructions for this in :doc:`/guides/custom-domains`.

Read the Docs uses a :doc:`/reference/cdn` to host and serve your documentation pages.
This final step isn't changed by a custom domain
and therefore the response times are unaffected as the delivery of resources happens through the same CDN setup.

Considerations for custom domain usage
--------------------------------------

Some open source projects have seen their domains expire.
Even prominent ones.
**It's important that you give the responsibility for managing your domain to someone reliable in your organization.**

The **canonical domain** feature allows you to have several domains and the canonical domain will be indexed by search engines.
The domain that you choose as your canonical domain is by far the most important one.
If you lose the canonical domain,
someone else can set up a website that search results will end up referring to.

.. seealso::

   In a URL, both the domain and the path (``https://<domain>/<path>``) are important.
   In combination, they are referred to as the *canonical URL* of a resource.

   Most documentation projects are versioned.
   Therefore, it's important to ensure that incoming links and search engine results point to the canonical URL of the resource
   and not a specific version that becomes outdated.

   To learn more about canonical URLs, see: :doc:`/canonical-urls`
