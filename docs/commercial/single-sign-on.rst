Single Sign-On (SSO)
====================

Single Sign-On (or SSO) allows you to manage your organization's membership via a third-party identity provider.
This means your team can access your organization's documentation without having to remember another password.


Managing users access
---------------------

Once SSO is activated for your organization,
a new Team named "Single Sign-On Access" will be created automatically.
Users logged in via SSO will be granted access to all the projects' documentation this team has access to
--which has no projects by default.

To grant access to SSO users to documentation of some projects,
any organization's owners can add projects to this new team to granularly grant permissions.

All the members you already have in your organization will keep working in the same way as usually.
Members of a particular team will still have dashboard admin and documentation access to all the projects from that team.
However, if a project belongs to the default "Single Sign-On Access" team,
this project's documentation can be accessed only by logging in using their SSO account.


Providers
---------

.. note::

   We currently only support Auth0_, but we are working to expand to other providers as well.


Auth0
~~~~~

Contact our `support team`_ for more information about SSO and we will guide you through the process.


.. _Auth0: https://auth0.com/
.. _support team: mailto:support@readthedocs.com
