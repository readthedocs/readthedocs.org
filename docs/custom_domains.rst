Custom Domains
==============

.. note:: These setup directions are for our community site.
          If you want to setup a custom domain under our `commercial hosting`_,
          please read our :ref:`commercial documentation <commercial/custom_domains:Custom Domains>`.

.. _commercial hosting: https://readthedocs.com

Read the Docs supports a number of custom domains for your convenience. Shorter URLs make everyone happy, and we like making people happy!

Subdomain Support
------------------

Every project has a subdomain that is available to serve its documentation. If you go to ``<slug>.readthedocs.io``, it should show you the latest version of documentation. A good example is https://pip.readthedocs.io

.. note:: If you have an old project that has an underscore (_) in the name, it will use a subdomain with a hyphen (-).
          `RFC 1035 <http://tools.ietf.org/html/rfc1035>`_ has more information on valid subdomains.

Custom Domain Support
---------------------

You can also host your documentation from your own domain by adding a domain to
your project:

* Add a CNAME record in your DNS that points the domain to: ``readthedocs.io``
* Add a project domain in the :guilabel:`Domains` project admin page for your project.

.. note::
    We don't currently support pointing subdomains or naked domains to a project
    using ``A`` records. It's best to point a subdomain, ``docs.example.com``
    for example, using a CNAME record.

Using pip as an example, https://pip.pypa.io resolves, but is hosted on our infrastructure.

As another example, fabric's dig record looks like this::

    -> dig docs.fabfile.org
    ...
    ;; ANSWER SECTION:
    docs.fabfile.org.   7200    IN  CNAME   readthedocs.io.

Custom Domain SSL
-----------------

By default, when you setup a custom domain to host documentation at Read the Docs,
we will attempt to provision a domain validated SSL certificate for the domain.
This service is generously provided by Cloudflare.

After configuring your custom domain on Read the Docs,
you can see the status of the certificate on the domain page in your project
admin dashboard (:guilabel:`Domains` > :guilabel:`Edit Domain`).

If your domain has configured CAA records, please do not forget to include
Cloudflare CAA entries, see their `Certification Authority Authorization (CAA)
FAQ <https://support.cloudflare.com/hc/en-us/articles/115000310832-Certification-Authority-Authorization-CAA-FAQ>`_.

.. note::

    Some older setups configured a CNAME record pointing to ``readthedocs.org``
    or another variation. While these continue to resolve,
    they do not yet allow us to acquire SSL certificates for those domains.
    Point the CNAME to ``readthedocs.io`` and re-request a certificate
    by saving the domain in the project admin (:guilabel:`Domains` >
    :guilabel:`Edit Domain`).

    If you change the CNAME record, the SSL certificate issuance can take about
    one hour.

.. important::

    Due to a limitation, a domain cannot be proxied on Cloudflare
    to another Cloudflare account that also proxies.
    This results in a "CNAME Cross-User Banned" error.
    In order to do SSL termination, we must proxy this connection.
    If you don't want us to do SSL termination for your domain --
    **which means you are responsible for the SSL certificate** --
    then set your CNAME to ``cloudflare-to-cloudflare.readthedocs.io``
    instead of ``readthedocs.io``.

    For more details, see this `previous issue`_.

    .. _previous issue: https://github.com/rtfd/readthedocs.org/issues/4395


Proxy SSL
---------

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

rtfd.org
---------

You can also use `rtfd.io` and `rtfd.org` for short URLs for Read the Docs. For example, https://pip.rtfd.io redirects to its documentation page. Any use of `rtfd.io` or `rtfd.org` will simply be redirected to `readthedocs.io`.
