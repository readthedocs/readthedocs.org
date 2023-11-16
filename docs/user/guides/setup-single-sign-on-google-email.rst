How to setup Single Sign-On (SSO) with Google Workspace
=======================================================

.. include:: /shared/admonition-rtd-business.rst

This how-to guide will provide instructions on how to enable :abbr:`SSO (Single Sign-on)` with Google Workspace.
If you want more information on this feature,
please read :doc:`/commercial/single-sign-on`

Prerequisites
-------------

.. include:: /shared/organization-permissions.rst

Connect your Google account to Read the Docs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable the Google Workspace integration,
you need to connect your Google account to Read the Docs.

The domain attached to your Google account will be used to match users that sign up with a Google account to your organization.

User setup
~~~~~~~~~~

Using this setup,
all users who have access to the configured Google Workspace will be granted a subset of permissions on your organization automatically on account creation.

You can still add outside collaborators and manage their access.
There are two ways to manage this access:

* Using :doc:`teams </guides/manage-read-the-docs-teams>` to provide access for ongoing contribution.
* Using :doc:`sharing </commercial/sharing>` to provide short-term access requiring a login.

Enabling SSO
------------

By default, users that sign up with a Google account do not have any permissions over any project.
However, you can define which teams users matching your company's domain email address will auto-join when they sign up.

1. Navigate to the `authorization setting page <https://readthedocs.com/organizations/choose/organization_sso/>`__.
2. Select **Google** in the :guilabel:`Provider` drop-down.
3. Press :guilabel:`Save`.

Configure team for all users to join
------------------------------------

You can mark one or many teams that users are automatically joined when they sign up with a matching email address.
Configure this option by:

1. Navigate to the `teams management page <https://readthedocs.com/organizations/choose/organization_team_list/>`__.
2. Click the :guilabel:`<team name>`.
3. Click :guilabel:`Edit team`
4. Enable *Auto join users with an organization's email address to this team*.
5. Click :guilabel:`Save`

With this enabled,
all users that sign up with their ``employee@company.com`` email will automatically join this team.
These teams can have either *read-only* or *admin* permissions over a set of projects.

Revoke user's access to all the projects
----------------------------------------

By disabling the Google Workspace account with email ``employee@company.com``,
you revoke access to all the projects that user had access and disable login on Read the Docs completely for that user.

.. seealso::

   :doc:`/guides/manage-read-the-docs-teams`
     Additional user management options
   :doc:`/commercial/single-sign-on`
     Information about choosing a Single Sign-on approach
