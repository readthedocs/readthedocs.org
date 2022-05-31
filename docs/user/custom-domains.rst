Custom Domains
==============

Custom domains allow you to serve your documentation from your own domain.

By default, your documentation is served from a Read the Docs :ref:`subdomain <hosting:subdomain support>` using the project's slug:
``<slug>.readthedocs.io`` or ``<slug>.readthedocs-hosted.com`` for |com_brand|.
For example if you import your project as ``docs``, it will be served from ``https://docs.readthedocs.io``.

.. contents::
    :local:

Adding a custom domain
----------------------

To setup your custom domain, follow these steps:

#. Go the :guilabel:`Admin` tab of your project.
#. Click on :guilabel:`Domains`.
#. Enter your domain.
#. Mark the :guilabel:`Canonical` option if you want use this domain
   as your :doc:`canonical domain </canonical-urls>`.
#. Click on :guilabel:`Add`.
#. At the top of the next page you'll find the value of the DNS record that you need to point your domain to.
   For |org_brand| this is ``readthedocs.io``, and for :doc:`/commercial/index`
   the record is in the form of ``<hash>.domains.readthedocs.com``.

   .. note::

      For a subdomain like ``docs.example.com`` add a CNAME record,
      and for a root domain like ``example.com`` use an ANAME or ALIAS record.

By default, we provide a validated SSL certificate for the domain,
this service is provided by Cloudflare.
The SSL certificate issuance can take about one hour,
you can see the status of the certificate on the domain page in your project.

As an example, our blog's DNS record looks like this:

.. prompt:: bash $, auto

   $ dig +short blog.readthedocs.com CNAME
     readthedocs.io.

.. warning::

   We don't support pointing subdomains or root domains to a project using A records.
   DNS A records require a static IP address and our IPs may change without notice.

Strict Transport Security
-------------------------

By default, we do not return a `Strict Transport Security header`_ (HSTS) for user custom domains.
This is a conscious decision as it can be misconfigured in a not easily reversible way.
For both |org_brand| and |com_brand|, HSTS for custom domains can be set upon request.

We always return the HSTS header with a max-age of at least one year
for our own domains including ``*.readthedocs.io``, ``*.readthedocs-hosted.com``, ``readthedocs.org`` and ``readthedocs.com``.

.. _Strict Transport Security header: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security

Legacy domains on |com_brand|
-----------------------------

Some older setups configured a CNAME record pointing to
``<organization-slug>.users.readthedocs.com``,
these domains will continue to resolve.

Previously you were asked to add two records,
this process has been simplified.
If you have doubts about deleting some of the old records,
please reach out to :ref:`support <support:user support>`.

Multiple documentation sites as sub-folders of a domain
-------------------------------------------------------

You may host multiple documentation repositories as **sub-folders of a single domain**.
For example, ``docs.example.org/projects/repo1`` and ``docs.example.org/projects/repo2``.
This is `a way to boost the SEO of your website <https://moz.com/blog/subdomains-vs-subfolders-rel-canonical-vs-301-how-to-structure-links-optimally-for-seo-whiteboard-friday>`_.

See :doc:`subprojects` for more information.

Troubleshooting
---------------

SSL certificate issue delays
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The status of your domain validation and certificate can always be seen on the details page for your domain
under :guilabel:`Admin` > :guilabel:`Domains` > :guilabel:`YOURDOMAIN.TLD (details)`.

Domains are usually validated and a certificate issued within minutes.
However, if you setup the domain in Read the Docs without provisioning the necessary DNS changes
and then update DNS hours or days later,
this can cause a delay in validating because there is an exponential back-off in validation.
Loading the domain details in the Read the Docs dashboard and saving the domain again will force a revalidation.

Certificate authority authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Certificate authority authorization (CAA) is a security feature that allows domain owners to limit
which certificate authorities (CAs) can issue certificates for a domain.
This is done by setting CAA DNS records for your domain.

The readthedocs domains that you'll point your domains to already
have the proper CAA records.

.. tabs::

  .. tab:: |org_brand|

     .. prompt:: bash $, auto

        $ dig +short readthedocs.io CAA
          0 issue "digicert.com; cansignhttpexchanges=yes"
          0 issuewild "digicert.com; cansignhttpexchanges=yes"
          0 issue "comodoca.com"
          0 issue "letsencrypt.org"
          0 issuewild "comodoca.com"
          0 issuewild "letsencrypt.org"

  .. tab:: |com_brand|

     .. prompt:: bash $, auto

        $ dig +short 0acba22b.domains.readthedocs.com CAA
          proxy-fallback.readthedocs-hosted.com.
          0 issue "digicert.com"
          0 issue "comodoca.com"
          0 issue "letsencrypt.org"

In case that there are CAA records for your domain that do not allow the certificate authorities that Read the Docs uses,
you may see an error message like ``pending_validation: caa_error: YOURDOMAIN.TLD``
in the Read the Docs dashboard for your domain.
You will need to update your CAA records to allow us to issue the certificate.

We use Cloudflare, which uses Digicert as a CA. See the `Cloudflare CAA FAQ`_ for details.

.. _Cloudflare CAA FAQ: https://support.cloudflare.com/hc/en-us/articles/115000310832-Certification-Authority-Authorization-CAA-FAQ

.. note::

   If your custom domain was previously used in GitBook, contact GitBook support (via live chat in their website)
   to remove the domain name from their DNS Zone in order for your domain name to work with Read the Docs,
   else it will always redirect to GitBook.
