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

.. note::

   If you have an old project that has an underscore (_) in the name,
   it will use a subdomain with a hyphen (-).
   `RFC 1035 <https://tools.ietf.org/html/rfc1035>`_ has more information on valid subdomains.


Custom domain support
---------------------

You can also host your documentation from your own domain.

.. note::

   We don't currently support pointing subdomains or naked domains to a project using ``A`` records.
   It's best to point a subdomain, ``docs.example.com`` for example, using a CNAME record.

.. tabs::

   .. tab:: Read the Docs Community
      
      In order to setup your custom domain, follow these steps:

      #. Add a CNAME record in your DNS that points the domain to ``readthedocs.io``
      #. Go the :guilabel:`Admin` tab of your project
      #. Click on :guilabel:`Domains`
      #. Enter your domain and click on :guilabel:`Add`

      By default, we provide a validated SSL certificate for the domain.
      This service is generously provided by Cloudflare.
      The SSL certificate issuance can take about one hour,
      you can see the status of the certificate on the domain page in your project.

      For example, https://pip.pypa.io resolves, but is hosted on our infrastructure.
      As another example, fabric's dig record looks like this:

      .. prompt:: bash $, auto

         $ dig docs.fabfile.org
         ...
         ;; ANSWER SECTION:
         docs.fabfile.org.   7200    IN  CNAME   readthedocs.io.

      .. note::

         Some older setups configured a CNAME record pointing to ``readthedocs.org`` or another variation.
         While these continue to resolve,
         they do not yet allow us to acquire SSL certificates for those domains.
         Follow the new setup to have a SSL certificate.

      .. warning:: Notes for Cloudflare users

         - If your domain has configured CAA records, please do not forget to include
           Cloudflare CAA entries, see their `Certification Authority Authorization (CAA)
           FAQ <https://support.cloudflare.com/hc/en-us/articles/115000310832-Certification-Authority-Authorization-CAA-FAQ>`__.

         - Due to a limitation,
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

Proxy SSL
---------

.. note::

   This is only available for the community version

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
