Account authentication methods
==============================

Read the Docs supports several authentication methods for creating an account and logging in.
The method you choose depends on your preferences and the security requirements of your organization.

These authentication methods are not mutually exclusive;
you can use multiple methods to access your account.

Email and password
------------------

You can create an account on Read the Docs using your email address and a password.
This method works well for individual users and small teams,
but it limits the functionality available to you.

VCS provider authentication
---------------------------

You can also create an account on Read the Docs using a VCS authentication provider: GitHub, GitLab, or Bitbucket.
This method is more secure and convenient than using an email and password,
and provides access to additional features like automatic repository syncing.

VCS provider authentication is required for the following features:

* :doc:`/pull-requests`
* Automatic repository syncing for easy project creation
* Automatic webhook creation on project creation

.. seealso::

   :doc:`/guides/connecting-git-account`
     Learn how to connect your Read the Docs account with a Git provider.

Google authentication
---------------------

.. include:: /shared/admonition-rtd-business.rst

Read the Docs supports Google authentication for organizations.
Google authentication works well for users already using Google services,
and easily integrates into your existing workflow.

Google provides authentication, but not authorization.
This means that you can log in to Read the Docs with this method,
but we aren't able to determine which projects you have access to automatically.

.. seealso::

   :ref:`sso_google_workspace`
    Learn how to configure Google authentication for your organization.

SAML authentication
-------------------

.. include:: /shared/admonition-rtd-business.rst

Read the Docs supports SAML authentication for organizations.
SAML authentication is a secure way to authenticate users and manage access to your organization's projects.
This is only available on Enterprise plans,
and requires custom integration to be enabled.

SAML provides authentication, but not authorization.
This means that users can log in to Read the Docs with this method,
but we aren't able to determine which projects each user has access to automatically.

.. seealso::

   :ref:`sso_saml`
    Learn how to configure SAML authentication for your organization.

Two-factor authentication
-------------------------

Read the Docs supports two-factor authentication (2FA) for added security on all authentication methods.
If you have 2FA enabled on your account, you will be prompted to enter a code
when logging in.

.. seealso::

    :doc:`/guides/management/2fa`
      Learn how to enable and disable two-factor authentication on your account.
