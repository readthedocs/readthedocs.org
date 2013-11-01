Alternate Domains
=================

Read the Docs supports a number of custom domains for your convenience. Shorter urls make everyone happy, and we like making people happy!

Subdomain Support
------------------

Every project has a subdomain that is available to serve it's documentation. If you go to <slug>.readthedocs.org, it should show you the latest version of documentation. A good example is http://pip.readthedocs.org

CNAME Support
-------------

If you have your own domain, you can still host with us. If you point a CNAME record in your DNS to the subdomain for your project, it should magically serve your latest documentation on the custom domain. Using pip as another example, http://www.pip-installer.org resolves, but is hosted on our infrastructure.

As an example, fabric's dig record looks like this::

    -> dig docs.fabfile.org
    ...
    ;; ANSWER SECTION:
    docs.fabfile.org.   7200    IN  CNAME   fabric.readthedocs.org.


RTFD.org
---------

You can also use <slug>.rtfd.org as a short URL for the front page of your subdomain'd site. For example, http://pip.rtfd.org redirects to it's documentation page. We're looking for more fun ways to use this domain, so feel free to suggest an idea.
