How to setup single sign-on (SSO) with GitHub, GitLab, or Bitbucket
===================================================================

.. include:: /shared/admonition-rtd-business.rst

This how-to guide will provide instructions on how to enable :abbr:`SSO (single sign-on)` with GitHub, GitLab, or Bitbucket.
If you want more information on this feature,
please read :doc:`/commercial/single-sign-on`

Prerequisites
-------------

.. include:: /shared/organization-permissions.rst

User setup
~~~~~~~~~~

Users in your organization must have their GitHub, Bitbucket, or GitLab
:doc:`account connected </guides/connecting-git-account>`,
otherwise they won't have access to any project on Read the Docs after performing this change.
You can read more about `granting permissions on GitHub`_ in their documentation.

.. _granting permissions on GitHub: https://docs.github.com/en/github/setting-up-and-managing-organizations-and-teams/repository-permission-levels-for-an-organization

Enabling SSO
------------

You can enable this feature in your organization by:

1. Navigate to the `authorization setting page <https://app.readthedocs.com/organizations/choose/organization_sso/>`__.
2. Select :guilabel:`GitHub, GitLab or Bitbucket` on the :guilabel:`Provider` dropdown.
3. Select :guilabel:`Save`

.. warning::
    Once you enable this option,
    your existing Read the Docs :doc:`teams </guides/manage-read-the-docs-teams>` will not be used.
    While testing you can enable SSO and then disable it without any data loss.

Grant access to read private documentation
------------------------------------------

By granting **read** permissions to a user in your git repository,
you are giving the user access to read the documentation of the associated project on Read the Docs.
By default, private git repositories are built as private documentation websites.
Having **read** permissions to the git repository translates to having **view** permissions to a private documentation website.

Grant access to administer a project
------------------------------------

By granting **admin** permission to a user in the git repository,
you are giving the user access to read the documentation *and* to be an administrator of the associated project on Read the Docs.

Grant access to import a project
--------------------------------

When SSO with a Git provider is enabled, only owners of the Read the Docs organization can import projects.

To be able to import a project,
a user must have:

#. **admin** permissions in the associated Git repository.
#. Ownership rights to the Read the Docs organization

Revoke access to a project
--------------------------

If a user should not have access to a project,
you can revoke access to the git repository,
and this will be automatically reflected in Read the Docs.

The same process is followed in case you need to remove admin access,
but still want that user to have access to read the documentation.
Instead of revoking access completely,
downgrade their permissions to *read only*.

.. seealso::
    To learn more about choosing a single sign-on approach,
    please read :doc:`/commercial/single-sign-on`.
