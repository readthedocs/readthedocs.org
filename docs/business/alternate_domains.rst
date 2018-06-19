Alternate Domains
=================

Read the Docs supports a number of custom domains for your convenience.

Subdomain support
-----------------

Every project has a subdomain that is available to serve its documentation.
If you go to ``<organization-slug-project-slug>.readthedocs-hosted.com``,
it should show you the latest version of documentation.


CNAME Support
-------------

If you have your own domain, you can still host with us.
This requires two steps:

* Add a CNAME record in your DNS that points to our servers ``<organization-slug>.users.readthedocs.com``
* Add a Domain in the **Project Admin > Domains** page for your project.

.. note:: The Domain that should be used is the actual subdomain that you want your docs served on.
          Generally it will be ``docs.projectname.com``.

CNAME SSL
---------

We do support SSL for CNAMEs on our side.
Please, `contact our support team`_ to setup it.

.. _contact our support team: mailto:support@readthedocs.com
