How to set up single sign-on (SSO) with SAML
============================================

.. include:: /shared/admonition-rtd-business.rst

.. note::

   This feature is in beta, and will be available for **Enterprise** plans only.
   Contact :doc:`support </support>` to enable this feature for your organization.

   **At the moment only Okta is supported as a SAML identity provider.**

This how-to guide will provide instructions on how to enable :abbr:`SSO (single sign-on)` using Okta as a SAML identity provider.
If you want more information on this feature, please read :doc:`/commercial/single-sign-on`

Prerequisites
-------------

.. include:: /shared/organization-permissions.rst

Create a SAML application in Okta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable SSO with Okta, you need to create a new SAML application in your Okta account.

.. vale RTD.features = NO

1. Log in to your Okta account.
2. Click on :guilabel:`Applications`.
3. Click on :guilabel:`Create App Integration`.
4. Choose :guilabel:`SAML 2.0`, and click :guilabel:`Next`.
5. Fill in the following fields with the information from `your SAML integration <https://app.readthedocs.com/organizations/choose/organization_saml/>`__:

   * :guilabel:`App name`: Read the Docs
   * :guilabel:`App logo`: Optionally you can use the `Read the Docs logo <https://brand-guidelines.readthedocs.org/_images/logo-wordmark-vertical-compact-dark.png>`__.
   * :guilabel:`App visibility`: (optional)
   * :guilabel:`Single Sign On URL`: ``https://app.readthedocs.com/accounts/saml/<organization-slug>/acs/`` (replace ``<organization-slug>`` with your organization slug)
   * :guilabel:`Audience URI (SP Entity ID)`: ``https://app.readthedocs.com/accounts/saml/<organization-slug>/metadata/`` (replace ``<organization-slug>`` with your organization slug)
   * :guilabel:`Name ID format`: ``EmailAddress``
   * :guilabel:`Application username`: ``Email``
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

.. vale RTD.features = YES

Enable SAML on your Read the Docs organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have created the SAML application in Okta, you need to enable SAML on Read the Docs.

1. Copy the Metadata URL from the Okta application you just created.

   * On Okta, click on the :guilabel:`Applications`.
   * Click on the Read the Docs application.
   * Click on the :guilabel:`Sign On` tab.
   * Copy the :guilabel:`Metadata URL`.

2. Go you your `organization's SAML settings page <https://app.readthedocs.com/organizations/choose/organization_saml/>`__.
3. Paste the Metadata URL in the :guilabel:`Metadata URL` field.
4. Leave the domain field empty.
5. Click :guilabel:`Save`.

Attaching the email domain your organization uses to enforce SAML is currently done by the Read the Docs team,
contact :doc:`support </support>` using an account that's an owner of the organization.

Configure a team for users to join automatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you have enabled SAML on your organization,
a team named "SAML Users" will be created automatically,
and all users that sign up with SAML will be automatically joined to this team.
You can delete this team, or configure a different team or teams for users to join automatically.

To configure a team for users to join automatically:

1. Navigate to the `teams management page <https://app.readthedocs.com/organizations/choose/organization_team_list/>`__.
2. Click the :guilabel:`<team name>`.
3. Click :guilabel:`Edit team`
4. Enable *Auto join users with an organization's email address to this team*.
5. Click :guilabel:`Save`

User management
---------------

New users
~~~~~~~~~

After enabling the SAML integration,
all users with an email domain matching the one in your SAML integration will be required to sign up using SAML.
After they sign up, they will be automatically joined to your organization within the teams you have configured to auto-join users.

Existing users
~~~~~~~~~~~~~~

Existing users with email addresses from your configured domain will not be required to sign in using SAML,
but they won't be automatically joined to your organization.

If you want to enforce SAML for existing users, you have the following options:

- Users can delete their accounts, and sign up again using SAML.
- Users can link their existing accounts to their SAML identity by following this link while logged in their Read the Docs account:
  ``https://app.readthedocs.com/accounts/saml/<organization-slug>/login/?process=connect`` (replace ``<organization-slug>`` with your organization slug).
  You can find this link in your `organization's SAML settings page <https://app.readthedocs.com/organizations/choose/organization_saml/>`__.

Outside collaborators
~~~~~~~~~~~~~~~~~~~~~

You can still add outside collaborators that don't use SAML and manage their access.
There are two ways to manage this access:

* Using :doc:`teams </guides/manage-read-the-docs-teams>` to provide access for ongoing contribution.
* Using :doc:`sharing </commercial/sharing>` to provide short-term access requiring a login.

Revoke user's access to all the projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By disabling access to the SAML integration to a user,
you revoke access to all the projects their linked Read the Docs user had access to,
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
     Information about choosing a single sign-on approach
