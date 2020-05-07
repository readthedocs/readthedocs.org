Custom Domains
==============

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

      As an example, fabric's dig record looks like this:

      .. prompt:: bash $, auto

         $ dig +short docs.fabfile.org
         readthedocs.io.
         104.17.33.82
         104.17.32.82

      .. admonition:: Certificate Authority Authorization (CAA)

         If your custom domain — either the subdomain you're using or the root domain — has configured CAA records,
         please do not forget to include Cloudflare CAA entries to allow them to issue a certificate for your custom domain.
         See the `Cloudflare CAA FAQ`_ for details.
         We need a record that looks like this: ``0 issue "digicert.com"`` in response to ``dig +short CAA <domain>``

         .. _Cloudflare CAA FAQ: https://support.cloudflare.com/hc/en-us/articles/115000310832-Certification-Authority-Authorization-CAA-FAQ

      .. admonition:: Notes for Cloudflare users

         Due to a limitation,
         a domain cannot be proxied on Cloudflare to another Cloudflare account that also proxies.
         This results in a "CNAME Cross-User Banned" error.
         In order to do SSL termination, we must proxy this connection.
         If you don't want us to do SSL termination for your domain —
         **which means you are responsible for the SSL certificate** —
         then set your CNAME to ``cloudflare-to-cloudflare.readthedocs.io`` instead of ``readthedocs.io``.
         For more details, see `this previous issue`_.

         .. _this previous issue: https://github.com/readthedocs/readthedocs.org/issues/4395

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

      .. admonition:: Certificate Authority Authorization (CAA)

         If your custom domain — either the subdomain you're using or the root domain — has configured CAA records,
         please do not forget to include AWS Certificate Manager CAA entries to allow them to issue a certificate for your custom domain.
         See the `Amazon CAA guide`_ for details.

         .. _Amazon CAA guide: https://docs.aws.amazon.com/acm/latest/userguide/setup-caa.html

Proxy SSL
---------

.. warning::

   This option is deprecated,
   we already issue SSL certificates for all domains.

If you would prefer to do your own SSL termination
on a server you own and control,
you can do that although the setup is a bit more complex.

Broadly, the steps are:

* Have a server listening on 443 that you control
* Procure an SSL certificate for your domain and provision it
  and the private key on your server.
* Add a domain that you wish to point at Read the Docs
* Enable proxying to us, with a custom ``X-RTD-SLUG`` header

An example nginx configuration for pip would look like:

.. code-block:: nginx
   :emphasize-lines: 9

    server {
        server_name pip.pypa.io;
        location / {
            proxy_pass https://pip.readthedocs.io:443;
            proxy_set_header Host $http_host;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-RTD-SLUG pip;
            proxy_connect_timeout 10s;
            proxy_read_timeout 20s;
        }
    }
