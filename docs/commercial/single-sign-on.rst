Single Sign-On
==============

.. note::

   This feature only exists on `Read the Docs for Business <https://readthedocs.com/>`__.


Single sign-on is supported on |com_brand| for all users.
:abbr:`SSO (single sign-on)` will allow you to grant permissions to your organization's projects in an easy way.

Currently, we support two different types of single sign-on:

* Authentication *and* authorization are managed by the identity provider (e.g. GitHub, Bitbucket or GitLab)
* Authentication (*only*) is managed by the identity provider (e.g. an active Google Workspace account with a verified email address)

Users can log out by using the :ref:`Log Out <versions:Logging out>` link in the RTD flyout menu.

.. contents::
   :local:
   :depth: 2


SSO with VCS provider (GitHub, Bitbucket or GitLab)
---------------------------------------------------

Using an identity provider that supports authentication and authorization allows you to manage
who has access to projects on Read the Docs, directly from the provider itself.
If a user needs access to your documentation project on Read the Docs,
that user just needs to be granted permissions in the VCS repository associated with the project.

You can enable this feature in your organization by going to
your organization's detail page > :guilabel:`Settings` > :guilabel:`Authorization`
and selecting :guilabel:`GitHub, GitLab or Bitbucket` as provider.

Note the users created under Read the Docs must have their GitHub, Bitbucket or GitLab
:doc:`account connected </connected-accounts>` in order to make SSO work. 
You can read more about `granting permissions on GitHub`_.

.. warning:: Once you enable this option, your existing Read the Docs teams will not be used. 

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

When SSO with a VCS provider is enabled, only owners of the Read the Docs organization can import projects.
Adding users as owners of your organization will give them permissions to import projects.

Note that to be able to import a project, that user must have **admin** permissions in the VCS repository associated.


Revoke access to a project
~~~~~~~~~~~~~~~~~~~~~~~~~~

If a user should not have access anymore to a project, for any reason,
a VCS repository's admin (e.g. user with Admin role on GitHub for that specific repository)
can revoke access to the VCS repository and this will be automatically reflected in Read the Docs.

The same process is followed in case you need to remove **admin** access,
but still want that user to have access to read the documentation.
Instead of revoking access completely, just need lower down permissions to **read** only.


SSO with Google Workspace
-------------------------

.. note:: Google Workspace was formerly called G Suite

Using your company's Google email address (e.g. ``employee@company.com``) allows you to
manage authentication for your organization's members.
As this identity provider does not provide authorization over each repositories/projects per user,
permissions are managed by the :ref:`internal Read the Docs's teams <commercial/organizations:Team Types>` authorization system.

By default, users that sign up with a Google account do not have any permissions over any project.
However, you can define which teams users matching your company's domain email address will auto-join when they sign up.
Read the following sections to learn how to grant read and admin access.

You can enable this feature in your organization by going to
your organization's detail page > :guilabel:`Settings` > :guilabel:`Authorization`
and selecting :guilabel:`Google` as provider and specifying your Google Workspace domain in the :guilabel:`Domain` field.


Grant access to read a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add a user under a read-only team to grant **read** permissions to all the projects under that team.
This can be done under your organization's detail page > :guilabel:`Teams` > :guilabel:`Read Only` > :guilabel:`Invite Member`.

To avoid this repetitive task for each employee of your company,
the owner of the Read the Docs organization can mark one or many teams for users matching the company's domain email
to join these teams automaically when they sign up.

For example, you can create a team with the projects that all employees of your company should have access to
and mark it as :guilabel:`Auto join users with an organization's email address to this team`.
Then all users that sign up with their ``employee@company.com`` email will automatically join this team and have **read** access to those projects.


Grant access to administer a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add a user under an admin team to grant **admin** permissions to all the projects under that team.
This can be done under your organization's detail page > :guilabel:`Teams` > :guilabel:`Admins` > :guilabel:`Invite Member`.


Grant access to users to import a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Making the user member of any admin team under your organization (as mentioned in the previous section),
they will be granted access to import a project.

Note that to be able to import a project, that user must have **admin** permissions in the GitHub, Bitbucket or GitLab repository associated,
and their social account connected with Read the Docs.


Revoke user's access to a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To revoke access to a project for a particular user, you should remove that user from the team that contains that project.
This can be done under your organization's detail page > :guilabel:`Teams` > :guilabel:`Read Only` and click :guilabel:`Remove` next to the user you want to revoke access.


Revoke user's access to all the projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By disabling the Google Workspace account with email ``employee@company.com``,
you revoke access to all the projects that user had access and disable login on Read the Docs completely for that user.
