Custom Domains
==============

Custom domains allow you to serve your documentation from your own domain.
This is great for maintaining a consistent brand for your documentation and application.

By default, your documentation is served from a Read the Docs :ref:`subdomain <hosting:subdomain support>` using the project's :term:`slug`:

* ``<slug>.readthedocs.io`` for |org_brand|
* ``<slug>.readthedocs-hosted.com`` for |com_brand|.

For example if you import your project and it gets the :term:`slug` ``example-docs``, it will be served from ``https://example-docs.readthedocs.io``.

.. contents:: Contents
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
managed by `Cloudflare <https://www.cloudflare.com/>`_.
The SSL certificate issuance should happen within a few minutes,
but might take up to one hour.
See `SSL certificate issue delays`_ for more troubleshooting options.

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

.. warning::

    Once a domain is removed,
    your previous documentation domain is no longer served by Read the Docs,
    and any request for it will return a 404 Not Found!

Strict Transport Security (HSTS) and other custom headers
---------------------------------------------------------

By default, we do not return a `Strict Transport Security header`_ (HSTS) for user custom domains.
This is a conscious decision as it can be misconfigured in a not easily reversible way.
For both |org_brand| and |com_brand|, HSTS and other custom headers can be set upon request.

We always return the HSTS header with a max-age of at least one year
for our own domains including ``*.readthedocs.io``, ``*.readthedocs-hosted.com``, ``readthedocs.org`` and ``readthedocs.com``.

Please contact :doc:`support` if you want to add a custom header to your domain.

.. _Strict Transport Security header: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security

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

.. tip::

    Loading the domain details in the Read the Docs dashboard and saving the domain again will force a revalidation.

Migrating from GitBook
~~~~~~~~~~~~~~~~~~~~~~

If your custom domain was previously used in GitBook, contact GitBook support (via live chat in their website)
to remove the domain name from their DNS Zone in order for your domain name to work with Read the Docs,
else it will always redirect to GitBook.
