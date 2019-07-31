Custom Domains
==============

Subdomain support
-----------------

Once a project is imported under Read the Docs,
by default it's hosted under a subdomain on one of our domains.
If you need a custom domain, continue on custom domain setup.


Serving documentation with a custom domain
------------------------------------------

Projects can also be hosted under a custom domain.
If you'd prefer to use your own domain name instead of our default hosting domain,
you can still host with us.


We require two steps from your side:

* Add a CNAME record in your DNS that points to our servers ``<organization-slug>.users.readthedocs.com``
* Set your project's Privacy Level to *Public* from :guilabel:`Admin` > :guilabel:`Advance Settings`.
* Add a Domain in the :guilabel:`Admin` > :guilabel:`Domains` page for your project.

.. note:: The domain that should be used is the actual subdomain that you want your docs served on.
          Generally it will be ``docs.projectname.com``.


Custom domain SSL
-----------------

We require SSL for custom domains.
During the setup process, you will need to add a record to your DNS
which will allow us to issue an SSL certificate for your custom domain.
