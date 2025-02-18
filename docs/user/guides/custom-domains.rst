How to manage custom domains
============================

This guide describes how to host your documentation using your own domain name, such as ``docs.example.com``.

.. contents:: Contents
    :local:

Adding a custom domain
----------------------

To setup your :doc:`custom domain </custom-domains>`, follow these steps:

#. Go the :guilabel:`Admin` tab of your project.
#. Click on :guilabel:`Domains`.
#. Enter the domain where you want to serve the documentation from (e.g. ``docs.example.com``).
#. Mark the :guilabel:`Canonical` option if you want use this domain
   as your :doc:`canonical domain </canonical-urls>`.
#. Click on :guilabel:`Add`.
#. At the top of the next page you'll find the value of the DNS record that you need to point your domain to.
   For |org_brand| this is ``readthedocs.io``, and for :doc:`/commercial/index`
   the record is in the form of ``<hash>.domains.readthedocs.com``.
   If you are using Cloudflare, make sure to disable the proxy status (orange cloud) for the CNAME record.

 .. note::

    For a subdomain like ``docs.example.com`` add a CNAME record,
    and for a root domain like ``example.com`` use an ANAME or ALIAS record.

.. warning::

   If you delete a domain, make sure to also remove the DNS records for that domain.
   Otherwise, another user may add the same domain to their project and serve that content from your domain (domain hijacking).

We provide a validated SSL certificate for the domain,
managed by `Cloudflare <https://www.cloudflare.com/>`_.
The SSL certificate issuance should happen within a few minutes,
but might take up to one hour.
See `SSL certificate issue delays`_ for more troubleshooting options.

To see if your DNS change has propagated, you can use a tool like ``dig`` to inspect your domain from your command line.
As an example, our blog's DNS record looks like this:

.. prompt:: bash $, auto

   $ dig +short CNAME blog.readthedocs.com
     readthedocs.io.

.. warning::

   We don't support pointing subdomains or root domains to a project using A records.
   DNS A records require a static IP address and our IPs may change without notice.


Removing a custom domain
------------------------

To remove a custom domain:

#. Go the :guilabel:`Admin` tab of your project.
#. Click on :guilabel:`Domains`.
#. Click the :guilabel:`Remove` button next to the domain.
#. Click :guilabel:`Confirm` on the confirmation page.
#. Remove the DNS record for the domain from your DNS provider.

.. warning::

    Once a domain is removed,
    your previous documentation domain is no longer served by Read the Docs,
    and any request for it will return a 404 Not Found!

.. warning::

   If you delete a domain, make sure to also remove the DNS records for that domain.
   Otherwise, another user may add the same domain to their project and serve that content from your domain (domain hijacking).

Strict Transport Security (HSTS) and other custom headers
---------------------------------------------------------

By default, we do not return a `Strict Transport Security header`_ (HSTS) for user custom domains.
This is a conscious decision as it can be misconfigured in a not easily reversible way.
For both |org_brand| and |com_brand|, HSTS and other custom headers can be set upon request.

We always return the HSTS header with a max-age of at least one year
for our own domains including ``*.readthedocs.io``, ``*.readthedocs-hosted.com``, ``readthedocs.org`` and ``readthedocs.com``.

.. note::

   Please contact :doc:`/support` if you want to add a custom header to your domain.

.. _Strict Transport Security header: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security

Multiple documentation sites as sub-folders of a domain
-------------------------------------------------------

You may host multiple documentation repositories as **sub-folders of a single domain**.
For example, ``docs.example.org/projects/repo1`` and ``docs.example.org/projects/repo2``.
This is `a way to boost the SEO of your website <https://moz.com/blog/subdomains-vs-subfolders-rel-canonical-vs-301-how-to-structure-links-optimally-for-seo-whiteboard-friday>`_.

.. seealso::

   :doc:`/subprojects`
      Further information about hosting multiple documentation repositories, using the :term:`subproject` feature.


Troubleshooting
---------------

"Error 1014: CNAME Cross-User Banned" when using Cloudflare
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs uses Cloudflare to manage SSL certificates for custom domains,
CDN caching, and other features that require the domain to be completely managed by our Cloudflare account.

If you see an "Error 1014: CNAME Cross-User Banned" message,
it means that the domain is already managed by another Cloudflare account.
To fix this, you need to:

#. Log in your Cloudflare account (https://www.cloudflare.com/).
#. Select your domain.
#. Click on "DNS".
#. Find your CNAME record and click on "Edit".
#. Uncheck the "Proxy status" (orange cloud) option.
#. Leave everything else unchanged.
#. Click on save.

SSL certificate issue delays
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The status of your domain validation and certificate can always be seen on the details page for your domain
under :guilabel:`Admin` > :guilabel:`Domains` > :guilabel:`YOURDOMAIN.TLD (details)`.

Domains are usually validated and a certificate issued within minutes.
However, if you setup the domain in Read the Docs without provisioning the necessary DNS changes
and then update DNS hours or days later,
this can cause a delay in validating because there is an exponential back-off in validation.

.. tip::

    Loading the domain details in the Read the Docs dashboard and saving the domain again will force a revalidation.

Disallowed DNS configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to prevent some common cases of domain hijacking, we disallow some DNS configurations:

- CNAME records pointing to another CNAME record
  (``doc.example.com -> docs.example.com -> readthedocs.io``).
- CNAME records pointing to the APEX domain
  (``www.example.com -> example.com -> readthedocs.io``).

This prevents attackers from taking over unused domains with CNAME records pointing to domains that are on Read the Docs.

.. warning::

   Users shouldn't rely on these restrictions to prevent domain hijacking.
   We recommend regularly reviewing your DNS records,
   removing any that are no longer needed or that don't exist on Read the Docs,
   or registering all valid domains in your project.

The validation process period has ended
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you add a new custom domain, you have 30 days to complete the configuration.
Once that period has ended, we will stop trying to validate your domain.
If you still want to complete the configuration,
go to your domain and click on :guilabel:`Save` to restart the process.

Migrating from GitBook
~~~~~~~~~~~~~~~~~~~~~~

If your custom domain was previously used in GitBook, contact GitBook support (via live chat in their website)
to remove the domain name from their DNS Zone in order for your domain name to work with Read the Docs,
otherwise it will always redirect to GitBook.
