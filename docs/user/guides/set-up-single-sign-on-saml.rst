How to set up Single Sign-On (SSO) with SAML
============================================

.. include:: /shared/admonition-rtd-business.rst

.. note::

   This feature is in beta, and will be available for **Enterprise** plans only.
   Contact :doc:`support </support>` to enable this feature for your organization.

   **At the moment only Okta is supported as a SAML identity provider.**

This how-to guide will provide instructions on how to enable :abbr:`SSO (Single Sign-on)` using Okta as a SAML identity provider.
If you want more information on this feature, please read :doc:`/commercial/single-sign-on`

Prerequisites
-------------

.. include:: /shared/organization-permissions.rst

Create a new SAML application in Okta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable SSO with Okta, you need to create a new SAML application in your Okta account.

1. Log in to your Okta account.
2. Click on :guilabel:`Applications`.
3. Click on :guilabel:`Create App Integration`.
4. Choose :guilabel:`SAML 2.0`, and click :guilabel:`Next`.
5. Fill in the following fields with the information from `your SAML integration <https://readthedocs.com/organizations/choose/organization_saml/>`__:

   * :guilabel:`App name`: Read the Docs
   * :guilabel:`App logo`: Optionally you can use the `Read the Docs logo <https://brand-guidelines.readthedocs.org/_images/logo-wordmark-vertical-compact-dark.png>`__.
   * :guilabel:`App visibility`: (optional)
   * :guilabel:`Single Sign On URL`: ``https://readthedocs.com/accounts/saml/<organization-slug>/acs/`` (replace ``<organization-slug>`` with your organization slug)
   * :guilabel:`Audience URI (SP Entity ID)`: ``https://readthedocs.com/accounts/saml/<organization-slug>/metadata/`` (replace ``<organization-slug>`` with your organization slug)
   * :guilabel:`Name ID format`: ``EmailAddress``
   * Leave the rest of the fields as default.

6. Add the following "attribute statements" to be used when creating a new user:

   .. csv-table::
      :header: "Name", "Format", "Value"

      "user.id", "Basic", "user.id"
      "user.firstName", "Basic", "user.firstName"
      "user.lastName", "Basic", "user.lastName"

7. Click :guilabel:`Next`.
8. Select ``This is an internal app that we have created``.
9. Click :guilabel:`Finish`.

User setup
~~~~~~~~~~

Using this setup, all users who have access to the configured Okta application will automatically join to your Read the Docs organization when they sign up.
Existing users will not be automatically joined to the organization.

You can still add outside collaborators and manage their access.
There are two ways to manage this access:

* Using :doc:`teams </guides/manage-read-the-docs-teams>` to provide access for ongoing contribution.
* Using :doc:`sharing </commercial/sharing>` to provide short-term access requiring a login.

Enabling SSO
------------

Enabling SSO is currently done by the Read the Docs team,
contact :doc:`support </support>` to enable this feature for your organization.

By default, users that sign up with SAML do not have any permissions over any project.
However, you can define which teams users will auto-join when they sign up.

After enabling the SAML integration,
all users with email addresses from your configured domain will be required to signup using SAML.

.. warning::

   Existing users with email addresses from your configured domain will not be required to sign up using SAML,
   but they won't be automatically joined to your organization.

Configure team for all users to join
------------------------------------

You can mark one or more teams that users will automatically join when they sign up with a matching email address.
Configure this option by:

1. Navigate to the `teams management page <https://readthedocs.com/organizations/choose/organization_team_list/>`__.
2. Click the :guilabel:`<team name>`.
3. Click :guilabel:`Edit team`
4. Enable *Auto join users with an organization's email address to this team*.
5. Click :guilabel:`Save`

With this enabled,
all users that sign up with SAML will automatically join this team.
These teams can have either *read-only* or *admin* permissions over a set of projects.

Revoke user's access to all the projects
----------------------------------------

By disabling access to the SAML integration to a user,
you revoke access to all the projects the linked Read the Docs user had access to,
and disable login on Read the Docs completely for that user.

.. warning::

   If the user signed up to Read the Docs previously to enabling SAML on your organization,
   they may still have access to their account and projects if they were manually added to a team.

   To completely revoke access to a user, remove them from all the teams they are part of.

.. warning::

   If the user was already signed in to Read the Docs when their access was revoked,
   they may still have access to documentation pages until their session expires.
   This is three days for the dashboard and documentation pages.

   To completely revoke access to a user, remove them from all the teams they are part of.

.. seealso::

   :doc:`/guides/manage-read-the-docs-teams`
     Additional user management options
   :doc:`/commercial/single-sign-on`
     Information about choosing a Single Sign-on approach
