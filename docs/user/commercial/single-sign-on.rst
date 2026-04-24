Single sign-on (SSO)
====================

.. include:: /shared/admonition-rtd-business.rst

Single sign-on is an optional feature on |com_brand| for all users.
By default,
you will use :doc:`teams </guides/manage-read-the-docs-teams>` within Read the Docs to manage user authorization.
:abbr:`SSO (single sign-on)` will allow you to grant permissions to your organization's projects in an easy way.

Currently, we support two different types of single sign-on:

* Authentication *and* authorization are managed by the identity provider (GitHub, Bitbucket or GitLab)
* Authentication (*only*) is managed by the identity provider (Google Workspace account with a verified email address)

.. _sso_git_provider:

Single sign-on with GitHub, Bitbucket, or GitLab
------------------------------------------------

Using an identity provider that supports authentication and authorization allows organization owners to manage
who has access to projects on Read the Docs,
directly from the provider itself.
If a user needs access to your documentation project on Read the Docs,
that user just needs to be granted permissions in the Git repository associated with the project.

Once you enable this option,
your existing Read the Docs teams will not be used.
All authentication will be done using your git provider,
including any two-factor authentication and additional single sign-on that they support.

Learn how to configure this SSO method with our :doc:`/guides/setup-single-sign-on-github-gitlab-bitbucket`.

.. _sso_google_workspace:

SSO with Google Workspace
-------------------------

This feature allows you to easily manage access to users with a specific email address (e.g. ``employee@company.com``),
where ``company.com`` is a registered Google Workspace domain.
As this identity provider does not provide information about which projects a user has access to,
permissions are managed by the :ref:`internal Read the Docs's teams <commercial/organizations:Team Types>` authorization system.

This feature is only available on the **Pro plan** and above.
Learn how to configure this SSO method with our :doc:`/guides/setup-single-sign-on-google-email`.

.. _sso_saml:

SSO with SAML
-------------

.. note::

   This feature is in beta, and will be available for **Enterprise** plans only.
   Contact :doc:`support </support>` to enable this feature for your organization.

   **At the moment only Okta is supported as a SAML identity provider.**

This feature allows you to easily manage access to users that are part of your identity provider.
As SAML doesn't provide information about which projects a user has access to,
permissions are managed by the :ref:`internal Read the Docs's teams <commercial/organizations:Team Types>` authorization system.
Learn how to configure this SSO method with our :doc:`guide </guides/set-up-single-sign-on-saml>`.

Requesting additional providers
-------------------------------

We are always interested in hearing from our users about what authentication needs they have.
You can reach out to our :doc:`/support` to talk with us about any additional authentication needs you might have.

.. tip::
   Many additional providers can be supported via GitHub, Bitbucket, and GitLab SSO.
   We will depend on those sites in order to authenticate you,
   so you can use all your existing SSO methods already configured on those services.
