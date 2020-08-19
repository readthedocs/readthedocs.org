Single Sign-On
==============

.. note::

   This feature only exists on `Read the Docs for Business <https://readthedocs.com/>`__.


Single Sign-On is supported on |com_brand| for Pro and Enterprise plans.
:abbr:`SSO (Single Sign-On)` will allow you to grant permissions to your organization's projects in an easy way.

Currently, we support two different types of Single Sign-On:

* Authentication *and* authorization are managed by the Identity Provider (e.g. GitHub, Bitbucket or GitLab)
* Authentication (*only*) is managed by the Identity Provider (e.g. an active GSuite/Google ``@company.com`` with a verified email address)

.. note::

   SSO is currently in **Beta** and only GitHub, Bitbucket, GitLab and Google are supported for now.
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

By granting **read** (or more) permissions to a user in the VCS repository
you are giving access to read the documentation of the associated project on Read the Docs to that user.


Grant access to administrate a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By granting **write** permission to a user in the VCS repository
you are giving access to read the documentation *and* to be an administrator
of the associated project on Read the Docs to that user.


Grant access to import a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When SSO with VCS provider is enabled only owners of the Read the Docs organization can import projects.
Adding users as owners of your organization will give them permissions to import projects.

Note that to be able to import a project, that user must have **admin** permissions in the VCS repository associated.


Revoke access to a project
~~~~~~~~~~~~~~~~~~~~~~~~~~

If a user should not have access anymore to a project for any reason,
a VCS repository's admin (e.g. user with Admin role on GitHub for that specific repository)
can revoke access to the VCS repository and this will be automatically reflected in Read the Docs.

The same process is followed in case you need to remove **admin** access,
but still want that user to have access to read the documentation.
Instead of revoking access completely, just need lower down permissions to **read** only.


SSO with GSuite (Google email account)
--------------------------------------

Using your company's Google email address (e.g. ``employee@company.com``) allows you to
manage authentication for your organization's members.
As this Identity Provider does not provide authorization over each repositories/projects per user,
permissions are managed by the :ref:`internal Read the Docs's Teams <commercial/organizations:Team Types>` authorization system.

By default, users that Sign Up with a Google account do not have any permissions over any project.
However, you can define which Teams users matching your company's domain email address will auto-join when they Sign Up.
Read the following sections to learn how to grant read and admin access.


Grant access to read a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add a user under a "Read Only Team" to grant **read** permissions to all the projects under that Team.
This can be done under "your organization detail's page" > :guilabel:`Teams` > :guilabel:`Read Only` > :guilabel:`Invite Member`.

To avoid this repetitive task for each employee of your company,
the owner of the Read the Docs organization can mark one or many Teams for users matching the company's domain email
to join these Teams automaically when they Sign Up.

For example, you can create a "General Documentaion (Read Only)" team
with the projects that all employees of your company should have access to
and mark it as :guilabel:`Auto join users with an organization's email address to this team`.
Then all users that Sign Up with their ``employee@company.com`` email will automatically join this Team and have **read** access to those projects.


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


Revoke user's access to a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To revoke access to a project for a particular user, you should remove that user from the Team that contains that Project.
This can be done under "your organization detail's page" > :guilabel:`Teams` > :guilabel:`Read Only` and click :guilabel:`Remove` next to the user you want to revoke access.


Revoke user's access to all the projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By disabling the GSuite/Google account with email ``employee@company.com``,
you revoke access to all the projects that user had access and disable login on Read the Docs completely for that user.
