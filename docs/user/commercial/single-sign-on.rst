Choosing a Single Sign-On approach
==================================

.. include:: /shared/admonition-rtd-business.rst

Single sign-on is supported on |com_brand| for all users.
:abbr:`SSO (single sign-on)` will allow you to grant permissions to your organization's projects in an easy way.

Currently, we support two different types of single sign-on:

* Authentication *and* authorization are managed by the identity provider (e.g. GitHub, Bitbucket or GitLab)
* Authentication (*only*) is managed by the identity provider (e.g. an active Google Workspace account with a verified email address)

Users can log out by using the :ref:`Log Out <versions:Logging out>` link in the RTD flyout menu.

.. contents::
   :local:
   :depth: 2


Single Sign-on with GitHub, Bitbucket or GitLab
-----------------------------------------------

Using an identity provider that supports authentication and authorization allows organization owners to manage
who has access to projects on Read the Docs,
directly from the provider itself.
If a user needs access to your documentation project on Read the Docs,
that user just needs to be granted permissions in the git repository associated with the project.

Once you enable this option,
your existing Read the Docs teams will not be used.
All authentication will be done using your git provider,
including any two-factor authentication and additional Single Sign-on that they support.

SSO with Google Workspace
-------------------------

.. note:: Google Workspace was formerly called G Suite

This feature allows you to restrict access to users with a specific email address (e.g. ``employee@company.com``),
where ``company.com`` is a registered Google Workspace domain.
As this identity provider does not provide authorization over each project a user has access to,
permissions are managed by the :ref:`internal Read the Docs's teams <commercial/organizations:Team Types>` authorization system.
