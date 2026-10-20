Managing a GitHub App integration
=================================

.. note::
   This information is for the :doc:`../github-app` integration only.
   Ensure that your project is not using our :ref:`projects/integrations/webhook:GitHub incoming webhook` integration instead. 

Creating a GitHub App integration
---------------------------------

Our GitHub App intgration can only be created by connecting your project
to a repository using a GitHub App connected account.
Unlike our :doc:`../webhook:GitHub incoming webhook`,
this integration cannot be created manually.
This integration will automatically show as a project integration once
our GitHub App is installed for the repository on GitHub and the project is
connected to the repository.

Installing the GitHub App
-------------------------

To add a project from a repository,
you need to install the GitHub App and grant it access to that repository.
Use the link below for your platform to complete the installation and permissions,
then create the project from your **Read the Docs account**.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

Once you have installed the App, in Read the Docs click on the :guilabel:`Projects`
tab, click on :guilabel:`Add project`, search for the repository you want to
create a project for, and then follow the instructions from there.

Connecting a repository to an existing project
----------------------------------------------

If you added a project on Read the Docs manually,
or you want to point your project at a different repository,
you need to install the App and grant it access to the repository you want to connect.
As with adding a project, complete the installation and permissions using the link
below, then select the repository from your **project settings on Read the Docs**.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

Once you have installed the App, go to the :guilabel:`Settings` page of the project
in Read the Docs, and select the repository you want to connect from the
:guilabel:`Connected repository` dropdown.

Migrating a project
-------------------

We recommend using the migration page to move your projects from the old OAuth
application to the GitHub App.

- `Read the Docs Community <https://app.readthedocs.org/accounts/migrate-to-github-app/>`__
- `Read the Docs Business <https://app.readthedocs.com/accounts/migrate-to-github-app/>`__

If you need to migrate a project manually:

- Go to the :guilabel:`Settings` page of your Read the Docs project,
  click on the :guilabel:`Integrations` tab, and delete all the integrations listed there.
- Go to the settings page of your GitHub repository,
  click on the GitHub :guilabel:`Webhooks` tab, and delete all the webhooks with URLs
  that start with:

  - ``https://readthedocs.org/api/v2/webhook/<your-project-slug>`` or ``https://app.readthedocs.org/api/v2/webhook/<your-project-slug>`` for Read the Docs Community.
  - ``https://readthedocs.com/api/v2/webhook/<your-project-slug>`` or ``https://app.readthedocs.com/api/v2/webhook/<your-project-slug>`` for Read the Docs Business.

- For projects on Read the Docs Business,
  go to the settings page of your GitHub repository,
  click on the GitHub :guilabel:`Deploy keys` tab, and delete the key with a title
  matching the format ``support@readthedocs.com (<your-project-slug>)``.
- :ref:`integrations/github-app:connecting a repository to an existing project`.

Revoking access
---------------

.. warning::

   If you revoke access to the GitHub App with any of the methods below,
   all projects linked to that repository stop working,
   but the projects and their documentation stay available.
   If you grant access to the repository again,
   you need to
   :ref:`reconnect your project to the repository <integrations/github-app:connecting a repository to an existing project>`.

You revoke access from your **GitHub account or organization settings**, not from
Read the Docs.
Nothing has to be done inside Read the Docs until you decide to reconnect a project.

Manage your installations at
`github.com/settings/installations <https://github.com/settings/installations>`__,
or in your organization's settings.

There are three ways to revoke access:

Remove repositories
   Remove the repositories from the list of repositories the GitHub App has access to.

Suspend the GitHub App
   This suspends the App and revokes access to all repositories.
   The installation and its configuration stay available,
   and you can re-enable the App at any time.

Uninstall the GitHub App
   This uninstalls the App and revokes access to all repositories.
   The installation and its configuration are removed,
   and you need to install the App again and reconfigure it before you can use it.
