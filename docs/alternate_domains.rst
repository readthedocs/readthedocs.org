Alternate Domains
=================

Read the Docs supports a number of custom domains for your convenience. Shorter URLs make everyone happy, and we like making people happy!

Subdomain Support
------------------

Every project has a subdomain that is available to serve its documentation. If you go to <slug>.readthedocs.io, it should show you the latest version of documentation. A good example is http://pip.readthedocs.io

.. note:: If you have an old project that has an underscore (_) in the name, it will use a subdomain with a hyphen (-).
          `RFC 1035 <http://tools.ietf.org/html/rfc1035>`_ has more information on valid subdomains.

CNAME Support
-------------

If you have your own domain, you can still host with us.
This requires two steps:

* Add a CNAME record in your DNS that point to our servers `readthedocs.io`
* Add a Domain object in the **Project Admin > Domains** page for your project.

.. note:: The ``Domain`` that should be used is the actual subdomain that you want your docs served on.
          Generally it will be `docs.projectname.org`.

Using pip as an example, http://www.pip-installer.org resolves, but is hosted on our infrastructure.

As another example, fabric's dig record looks like this::

    -> dig docs.fabfile.org
    ...
    ;; ANSWER SECTION:
    docs.fabfile.org.   7200    IN  CNAME   readthedocs.io.

.. note:: We used to map your projects documentation from the subdomain that you pointed your CNAME to.
          This wasn't workable at scale,
          and now we require you to set the domain you want to resolve on your project.

CNAME SSL
---------

We don't support SSL for CNAMEs on our side,
but you can enable support if you have your own server.
SSL requires having a secret key,
and if we hosted the key for you,
it would no longer be secret.

To enable SSL:

* Have a server listening on 443 that you control
* Add a domain that you wish to point at Read the Docs
* Enable proxying to us, with a custom ``X-RTD-SLUG`` header

An example nginx configuration for pip would look like:

.. code-block:: nginx
   :emphasize-lines: 9

    server {
        server_name docs.pip-installer.org;
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

You can also use `rtfd.io` and `rtfd.org` for short URLs for Read the Docs. For example, http://pip.rtfd.io redirects to its documentation page. Any use of `rtfd.io` or `rtfd.org` will simply be redirected to `readthedocs.io`.
