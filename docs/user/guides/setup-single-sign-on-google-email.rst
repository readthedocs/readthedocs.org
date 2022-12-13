How to setup Single Sign-On (SSO) with Google Workspace
=======================================================

.. include:: /shared/admonition-rtd-business.rst

This how-to guide will provide instructions on how to enable :abbr:`SSO (Single Sign-on)` with Google Workspace.
If you want more information on this feature,
please read :doc:`/commercial/single-sign-on`

Prerequisites
-------------

Organization permissions
~~~~~~~~~~~~~~~~~~~~~~~~

To change your :ref:`Organization <commercial/organization:Organizations>`'s settings,
you need to be an *owner* of that organization.

You can validate your ownership of the Organization with these steps:

* Navigate to :guilabel:`Username dropdown` > :guilabel:`Organizations` > :guilabel:`<Organization name>`
* Look at the **Owners** UI elements on the right menu.

If you'd like to to modify this setting and are not an owner,
you can ask an existing organization owner to follow this guide.

User setup
~~~~~~~~~~

Using this setup,
all users who have access to the configured Google Workspace will be granted a subset of permissions on your organization automatically on account creation.
.. tip::

   You can still add outside collaborators and manage their access. Organizations may for instance wish to give read-access to onboarding documents or grant temporary write access to external consultants.
   
.. seealso::

   :doc:`/commercial/sharing`
     Read more about methods for sharing **read** access to private sets of documentation without requiring a login for Read the Docs or your SSO provider.

Enabling SSO
------------

By default, users that sign up with a Google account do not have any permissions over any project.
However, you can define which teams users matching your company's domain email address will auto-join when they sign up.

You can enable this feature in your organization:

* Navigate to :guilabel:`<Username dropdown>` > :guilabel:`Organizations` > :guilabel:`<Username name>` > > :guilabel:`Settings` > :guilabel:`Authorization`
* Select :guilabel:`Google` as the *Provider*
* Specify your Google Workspace domain as the *Domain*.

Configure team for all users to join
------------------------------------

You can mark one or many teams that users are automatically joined when they sign up with a matching email address.
Configure this option by:

* Navigating to :guilabel:`<Username dropdown>` > :guilabel:`Organizations` > :guilabel:`<Organization name>` > :guilabel:`Teams` > :guilabel:`<Team name>`
* Click :guilabel:`Edit team`
* Enable *Auto join users with an organization's email address to this team*.
* Click :guilabel:`Save`

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
