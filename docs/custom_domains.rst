Custom Domains and White Labeling
=================================

Once a project is imported into Read the Docs,
by default it's hosted under a subdomain on one of our domains.
If you need a custom domain, see :ref:`custom_domains:custom domain support`.

Subdomain support
-----------------

Every project has a subdomain that is available to serve its documentation.
If you go to ``<slug>.readthedocs.io``, it should show you the latest version of your documentation.
A good example is https://pip.readthedocs.io
For :doc:`/commercial/index` the subdomain looks like ``<slug>.readthedocs-hosted.com``.

Custom domain support
---------------------

You can also host your documentation from your own domain.

.. note::

   We don't currently support pointing subdomains or root domains to a project using A records.
   DNS A records require a static IP address and our IPs may change without notice.

.. tabs::

   .. tab:: Read the Docs Community

      In order to setup your custom domain, follow these steps:

      #. For a subdomain like ``docs.example.com``, add a CNAME record in your DNS that points the domain to ``readthedocs.io``.
         For a root domain like ``example.com`` use an ANAME or ALIAS record pointing to ``readthedocs.io``.
      #. Go the :guilabel:`Admin` tab of your project
      #. Click on :guilabel:`Domains`
      #. Enter your domain and click on :guilabel:`Add`

      By default, we provide a validated SSL certificate for the domain.
      This service is generously provided by Cloudflare.
      The SSL certificate issuance can take about one hour,
      you can see the status of the certificate on the domain page in your project.

      As an example, fabric's DNS record looks like this:

      .. prompt:: bash $, auto

         $ dig CNAME +short docs.fabfile.org
           readthedocs.io.

   .. tab:: Read the Docs for Business

      In order to setup your custom domain, follow these steps:

      #. Go the :guilabel:`Admin` tab of your project
      #. Click on :guilabel:`Domains`
      #. Enter your domain and click on :guilabel:`Add`
      #. Follow the steps shown on the domain page.
         This will require adding 2 DNS records, one pointing your custom domain to our servers,
         and another allowing us to provision an SSL certificate.

      By default, we provide a validated SSL certificate for the domain.
      The SSL certificate issuance can take a few days,
      you can see the status of the certificate on the domain page in your project.

      .. note::

         Some older setups configured a CNAME record pointing to ``<organization-slug>.users.readthedocs.com``.
         These domains will continue to resolve.


Strict Transport Security
+++++++++++++++++++++++++

By default, we do not return a `Strict Transport Security header`_ (HSTS) for user custom domains.
This is a conscious decision as it can be misconfigured in a not easily reversible way.
For both |org_brand| and |com_brand|, HSTS for custom domains can be set upon request.

We always return the HSTS header with a max-age of at least one year
for our own domains including ``*.readthedocs.io``, ``*.readthedocs-hosted.com``, ``readthedocs.org`` and ``readthedocs.com``.

.. _Strict Transport Security header: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security


Troubleshooting
+++++++++++++++

SSL certificate issue delays
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The status of your domain validation and certificate can always be seen on the details page for your domain
under :guilabel:`Admin` > :guilabel:`Domains` > :guilabel:`YOURDOMAIN.TLD (details)`.

* For |org_brand|, domains are usually validated and a certificate issued within minutes.
  However, if you setup the domain in Read the Docs without provisioning the necessary DNS changes
  and then update DNS hours or days later,
  this can cause a delay in validating because there is an exponential back-off in validation.
  Loading the domain details in the Read the Docs dashboard and saving the domain again will force a revalidation.
* For |com_brand|, domains can take up to a couple days to validate and issue a certificate.
  To avoid any downtime in moving a domain from somewhere else to Read the Docs,
  it is possible to validate the domain and provision the certificate before pointing your domain to Read the Docs.

Certificate authority authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Certificate authority authorization (CAA) is a security feature that allows domain owners to limit
which certificate authorities (CAs) can issue certificates for a domain.
This is done by setting CAA DNS records for your domain.
CAA records are typically on the root domain, not subdomains
since you can't have a CNAME and CAA record for the same subdomain.
Here's an example for palletsprojects.com:

.. prompt:: bash $, auto

    $ dig CAA +short palletsprojects.com
    0 issue "digicert.com"
    0 issue "comodoca.com"
    0 issue "letsencrypt.org"

If there are CAA records for your domain that do not allow the certificate authorities that Read the Docs uses,
you may see an error message like ``pending_validation: caa_error: YOURDOMAIN.TLD``
in the Read the Docs dashboard for your domain.
You will need to update your CAA records to allow us to issue the certificate.

* For |org_brand|, we use Cloudflare which uses Digicert as a CA. See the `Cloudflare CAA FAQ`_ for details.
* For |com_brand|, we use AWS Certificate Manager as a CA. See the `Amazon CAA guide`_ for details.

.. _Cloudflare CAA FAQ: https://support.cloudflare.com/hc/en-us/articles/115000310832-Certification-Authority-Authorization-CAA-FAQ
.. _Amazon CAA guide: https://docs.aws.amazon.com/acm/latest/userguide/setup-caa.html

.. note::

   If your custom domain was previously used in GitBook, contact GitBook support (via live chat in their website)
   to remove the domain name from their DNS Zone in order for your domain name to work with Read the Docs,
   else it will always redirect to GitBook.

Canonical URLs
--------------

Canonical URLs allow people to have consistent page URLs for domains.
This is mainly useful for search engines,
so that they can send people to the correct page.

Read the Docs uses these in two ways:

* We point all versions of your docs at the "latest" version as canonical
* We point at the user specified canonical URL, generally a custom domain for your docs.

Example
+++++++

Fabric hosts their docs on Read the Docs.
They mostly use their own domain for them ``http://docs.fabfile.org``.
This means that Google will index both ``http://fabric-docs.readthedocs.io`` and
``http://docs.fabfile.org`` for their documentation.

Fabric will want to set ``http://docs.fabfile.org`` as their canonical URL.
This means that when Google indexes ``http://fabric-docs.readthedocs.io``,
it will know that it should really point at ``http://docs.fabfile.org``.

Enabling
++++++++

You can set the canonical URL for your project in the Project Admin page.
Check your :guilabel:`Admin` > :guilabel:`Domains` page for the domains that we know about.

Implementation
++++++++++++++

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will set the value of the html_baseurl_ setting (if isn't already set) to your canonical domain.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

If you are using :doc:`MkDocs </intro/getting-started-with-mkdocs>`,
you can use the site_url_ setting.

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url

If you look at the source code for documentation built after you set your canonical URL,
you should see a bit of HTML like this:

.. code-block:: html

    <link rel="canonical" href="http://docs.fabfile.org/en/2.4/" />
