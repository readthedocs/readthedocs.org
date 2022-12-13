How to setup Single Sign-On (SSO) with GitHub, GitLab, or Bitbucket
===================================================================

.. include:: /shared/admonition-rtd-business.rst

This how-to guide will provide instructions on how to enable :abbr:`SSO (Single Sign-on)` with GitHub, GitLab, or Bitbucket.
If you want more information on this feature,
please read :doc:`/commercial/single-sign-on`

Prerequisites
-------------

Organization permissions
~~~~~~~~~~~~~~~~~~~~~~~~~

To change your Organization's settings,
you need to be an *owner* of that organization.

You can validate your ownership of the Organization with these steps:

* Navigate to :guilabel:`Username dropdown` > :guilabel:`Organizations` > :guilabel:`<Organization name>`
* Look at the **Owners** UI elements on the right menu.

If you'd like to to modify this setting and are not an owner,
you can ask an existing organization owner to follow this guide.

User setup
~~~~~~~~~~

Users in your organization must have their GitHub, Bitbucket, or GitLab
:doc:`account connected </connected-accounts>`,
otherwise they will lose access to all repositories.

Enabling SSO
------------

You can enable this feature in your organization by:
* Navigate to :guilabel:`<Username dropdown>` > :guilabel:`Organizations` > :guilabel:`<Username name>` > :guilabel:`Settings` > :guilabel:`Authorization`
* Select :guilabel:`GitHub, GitLab or Bitbucket` on the *Provider* dropdown.
* Select :guilabel:`Save`

The users in your organization **must connect**  their GitHub, Bitbucket or GitLab
:doc:`account connected </connected-accounts>`,
otherwise they will lose access to all repositories.
You can read more about `granting permissions on GitHub`_ in their documentation.

.. warning:: Once you enable this option, your existing Read the Docs teams will not be used.

.. _granting permissions on GitHub: https://docs.github.com/en/github/setting-up-and-managing-organizations-and-teams/repository-permission-levels-for-an-organization

Grant access to read the documentation
--------------------------------------

By granting **read** permissions to a user in your git repository,
you are giving the user access to read the documentation of the associated project on Read the Docs.

Grant access to administer a project
------------------------------------

By granting **write** permission to a user in the git repository,
you are giving the user access to read the documentation *and* to be an administrator of the associated project on Read the Docs.

Grant access to import a project
--------------------------------

When SSO with a VCS provider is enabled, only owners of the Read the Docs organization can import projects.
Adding users as owners of your organization will give them permissions to import projects.

To be able to import a project,
that user must have **admin** permissions in the VCS repository associated.

Revoke access to a project
--------------------------

If a user should not have access to a project,
you can revoke access to the git repository,
and this will be automatically reflected in Read the Docs.

The same process is followed in case you need to remove admin access,
but still want that user to have access to read the documentation.
Instead of revoking access completely,
just need their permissions to read only.

.. seealso::
    To learn more about choosing a Single Sign-on approach,
    please read :doc:`/commercial/single-sign-on`.
