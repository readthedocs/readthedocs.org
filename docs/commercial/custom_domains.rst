Custom Domains
==============

Subdomain support
-----------------

Once a project is imported under Read the Docs,
by default it's hosted under a subdomain on one of our domains.
If you need a custom domain, continue on custom domain setup.

Custom domains
--------------

Projects can also be hosted under a custom domain.
If you'd prefer to use your own domain name instead of our default hosting domain,
you can still host with us.


We require two steps from your side:

* Add a CNAME record in your DNS that points to our servers ``<organization-slug>.users.readthedocs.com``
* Set your project's Privacy Level to *Public* from **Project Admin > Advance Settings**.
* Add a Domain in the **Project Admin > Domains** page for your project.

.. note:: The domain that should be used is the actual subdomain that you want your docs served on.
          Generally it will be ``docs.projectname.com``.


Custom domain SSL
-----------------

We do support SSL for CNAMEs on our side.
Please, `contact our support team`_ to setup it.

.. note:: SSL is required for *private* projects.

.. _contact our support team: mailto:support@readthedocs.com
