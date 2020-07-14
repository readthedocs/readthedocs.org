Single Sign-On
==============

.. note::

   This feature only exists on `Read the Docs for Business <https://readthedocs.com/>`__.


Single Sign-On is supported on |com_brand| for Pro and Enterprise plans.
:abbr:`SSO (Single Sign-On)` will allow you to grant permissions to your organization's projects in an easy way.

Currently, we support two different types of Single Sign-On:

* Authentication *and* authorization are managed by the Identity Provider (e.g. GitHub, Bitbucket or GitLab)
* Authentication is managed by the Identity Provider (e.g. a ``@company.com`` verified email address)

.. note::

   SSO is currently in **Beta** and only GitHub and Company Email are supported for now.
   If you would like to apply for the Beta, please `contact us <mailto:support@readthedocs.com>`_.

.. contents::
   :local:
   :depth: 2


SSO with VCS provider (GitHub, Bitbucket or GitLab)
---------------------------------------------------

Using an Identity Provider that supports authentication and authorization allows you to manage
"who have access to what projects on Read the Docs" directly from the provider itself.
In case you want a user to have access to your documentation project under Read the Docs,
that user just needs to be granted permissions in the VCS repository associated with it.

Note the users created under Read the Docs must have their GitHub, Bitbucket or GitLab
:doc:`account connected </connected-accounts>` in order to make SSO to work.

.. note::

   You can read more about `granting permissions on GitHub`_.

   .. _granting permissions on GitHub: https://docs.github.com/en/github/setting-up-and-managing-organizations-and-teams/repository-permission-levels-for-an-organization


Grant access to read the documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By granting **read** (or more) permissions to a user under VCS provider
you are giving access to read the documentation of the associated project on Read the Docs to that user.


Grant access to administrate a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By granting **write** permission to a user under VCS provider
you are giving access to read the documentation *and* to be an administrator
of the associated project on Read the Docs to that user.


Grant access to import a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When SSO with VCS provider is enabled only owners of the Read the Docs organization can import projects.
Adding users as owners of your organization will give them permissions to import projects.

Note that to be able to import a project, that user must have **admin** permissions in the VCS repository associated.


SSO with your company email address
-----------------------------------

Using your company's email address (e.g. ``employee@company.com``) allows you to
"grant **read** access to all the projects under your organization to users with a ``@company.com`` verified email address".


Grant access to administer a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add a user under an "Admin Team" to grant **admin** permissions to all the projects under that Team.
This can be done under "your organization detail's page" > :guilabel:`Teams` > :guilabel:`Admins` > :guilabel:`Invite Member`.


Grant access to users to import a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Making the user member of any "Admin Team" under your organization (as mentioned in the previous section),
they will be granted access to import a project.

Note that to be able to import a project, that user must have **admin** permissions in the GitHub, Bitbucket or GitLab repository associated,
and their social account connected with Read the Docs.
