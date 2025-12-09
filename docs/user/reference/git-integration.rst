Git integration (GitHub, GitLab, Bitbucket)
===========================================

Your Read the Docs account can be connected to your Git provider's account.
Connecting your account provides the following features:

🔑️ Easy login
  Log in to Read the Docs with your |git_providers_or| account.

🔁️ List your projects
  Select a project to automatically import from all your Git repositories and organizations.
  See: :doc:`/intro/add-project`.

⚙️ Automatic configuration
  Have your Git repository automatically configured with your Read the Docs :term:`webhook`,
  which allows Read the Docs to build your docs on every change to your repository.

🚥️ Commit status
  See your documentation build status as a commit status indicator on :doc:`pull request builds </pull-requests>`.

.. seealso::

   :ref:`intro/add-project:Manually add your project`
     Using a different provider? You can configure it manually.
     Read the Docs still supports other providers such as Gitea or GitHub Enterprise.

Getting started
---------------

✅️ Signed up with your Git provider?
  If you signed up or logged in to Read the Docs with your |git_providers_or|
  credentials, you're all done. Your account is connected.

  The rest of this guide explains how the automatic configuration works.

⏩️️ Signed up with your email address?
  If you have signed up to Read the Docs with your email address,
  you can add the connection to the Git provider afterward.
  You can also add a connection to an additional Git provider this way.

  Please follow :doc:`/guides/connecting-git-account` in this case.

Once you have your account connected,
you can follow the :doc:`/intro/add-project` guide to actually add your project to Read the Docs.

How automatic configuration works
---------------------------------

When your Read the Docs account is connected to |git_providers_or| and you :doc:`add a new Read the Docs project </intro/add-project>`:

* Read the Docs automatically creates a Read the Docs Integration that matches your Git provider.
* Read the Docs creates an incoming webhook with your Git provider, which is automatically added to your Git repository's settings using the account connection.

After project creation,
you can continue to configure the project.
All settings can be modified,
including the ones that were automatically created.

.. tip::

   A single Read the Docs account can connect to many different Git providers.
   This allows you to have a single login for all your various identities.

Read the Docs incoming webhook
------------------------------

.. note::

   When using our :ref:`reference/git-integration:GitHub App`, Read the Docs subscribes to all required events.
   You don't need to create a webhook on your repository.

Accounts with |git_providers_and| integration automatically have Read the Docs' incoming :term:`webhook` configured on all Git repositories that are imported.
Other setups can set up the webhook through :doc:`manual configuration </guides/setup/git-repo-manual>`.

When an incoming webhook notification is received,
Read the Docs ensures that it matches an existing project.
Once the webhook is validated,
an action is taken based on the information inside of the webhook.

Possible webhook action outcomes are:

* :doc:`Builds </builds>` the latest commit.
* Synchronizes your versions based on the latest tag and branch data in Git.
* Creates a :doc:`pull request build </pull-requests>`.
* Runs your :doc:`automation rules</automation-rules>`.

.. figure:: /img/screenshot-webhook.png
   :alt: Screenshot of the Dashboard view for the incoming webhook

   All calls to the incoming webhook are logged.
   Each call can trigger builds and version synchronization.

On |com_brand|,
Git integration makes it possible for us to synchronize your Git repository's access rights from your Git provider.
That way, the same access rights are effective on Read the Docs and you don't have to configure access in two places.
See more in our :ref:`sso_git_provider`.

How does the connection work?
-----------------------------

Read the Docs uses `OAuth`_ to connect to your account at |git_providers_or|.
You are asked to grant permissions for Read the Docs to perform a number of actions on your behalf.

At the same time, we use this process for authentication (login)
since we trust that |git_providers_or| have verified your user account and email address.

By granting Read the Docs the requested permissions,
we are issued a secret OAuth token from your Git provider.
Using the secret token,
we can automatically configure repositories during :doc:`project creation </intro/add-project>`.
We also use the token to send back build statuses and preview URLs for :doc:`pull requests </pull-requests>`.

.. _OAuth: https://en.wikipedia.org/wiki/OAuth

.. note::

   Access granted to Read the Docs can always be revoked.
   This is a function offered by all Git providers.

Git provider integrations
-------------------------

If your project is using :doc:`Organizations </commercial/organizations>` (|com_brand|) or :term:`maintainers <maintainer>` (|org_brand|),
then you need to be aware of *who* is setting up the integration for the project.

The Read the Docs user who sets up the project through the automatic import should also have admin rights to the Git repository.

A Git provider integration is active through the authentication of the user that creates the integration.
If this user is removed,
make sure to verify and potentially recreate all Git integrations for the project.

.. note::

   When using our :ref:`reference/git-integration:GitHub App`,
   If the original user who connected the repository to Read the Docs loses access to the project or repository,
   the GitHub App will still have access to the repository, and the integrations will continue to work.

Permissions for connected accounts
----------------------------------

Read the Docs does not generally ask for *write* permission to your repository code
(with one exception detailed below).
However, we do need permissions for authorizing your account
so that you can log in to Read the Docs with your connected account credentials.

.. tabs::

   .. tab:: GitHub

      Read the Docs requests the following permissions (more precisely, `OAuth scopes`_)
      when connecting your Read the Docs account to GitHub.

      .. _OAuth scopes: https://developer.github.com/apps/building-oauth-apps/understanding-scopes-for-oauth-apps/

      Read access to your email address (``user:email``)
          We ask for this so you can create a Read the Docs account and log in with your GitHub credentials.

      Administering webhooks (``admin:repo_hook``)
          We ask for this so we can create :term:`webhooks <webhook>` on your repositories when you import them into Read the Docs.
          This allows us to build the docs when you push new commits.

      Read access to your organizations (``read:org``)
          We ask for this so we know which organizations you have access to.
          This allows you to filter repositories by organization when importing repositories.

      Repository status (``repo:status``)
          Repository statuses allow Read the Docs to report the status
          (e.g. passed, failed, pending) of pull requests to GitHub.

      .. note::

          :doc:`Read the Docs for Business </commercial/index>`
          asks for one additional permission (``repo``) to allow access to private repositories
          and to allow us to set up SSH keys to clone your private repositories.
          Unfortunately, this is the permission for read/write control of the repository
          but there isn't a more granular permission
          that only allows setting up SSH keys for read access.

   .. tab:: GitHub App

      Read the Docs requests the following permissions when connecting your Read the Docs account to our :ref:`GitHub App <reference/git-integration:GitHub App>`.

      Account email addresses (read only)
          We ask for this so we can verify your email address and create a Read the Docs account.

      When installing the Read the Docs GitHub App in a repository, you will be asked to grant the following permissions:

      Repository permissions
        Commit statuses (read and write)
          This allows Read the Docs to report the status of the build to GitHub.
        Contents (read only)
          This allows Read the Docs to clone the repository and build the documentation.
        Metadata (read only)
          This allows Read the Docs to read the repository collaborators and the permissions they have on the repository.
          This is used to determine if the user can connect a repository to a Read the Docs project.
        Pull requests (read and write)
          This allows Read the Docs to subscribe to pull request events,
          and to create a comment on the pull request with information about the build.
        Checks (read and write)
          This allows Read the Docs to use the GitHub Checks API to report the status of the build.
          This isn't used yet, but we may use it in the future.

      Organization permissions
        Members (read only)
          This allows Read the Docs to read the organization members.

   .. tab:: Bitbucket

      We request permissions for:

      Administering your repositories (``repository:admin``)
        We ask for this so we can create :term:`webhooks <webhook>` on your repositories when you import them into Read the Docs.
        This allows us to build the docs when you push new commits.
        NB! This permission scope does **not** include any write access to code.

      Reading your account information including your email address
        We ask for this so you can create a Read the Docs account and log in with your Bitbucket credentials.

      Read access to your team memberships
        We ask for this so we know which organizations you have access to.
        This allows you to filter repositories by organization when importing repositories.

      Read access to your repositories
        We ask for this so we know which repositories you have access to.

      To read more about Bitbucket permissions, see `official Bitbucket documentation on API scopes`_

      .. _official Bitbucket documentation on API scopes: https://developer.atlassian.com/cloud/bitbucket/bitbucket-cloud-rest-api-scopes/


   .. tab:: GitLab

      Like the others, we request permissions for:

      * Reading your account information (``read_user``)
      * API access (``api``) which is needed to create webhooks in GitLab


.. _github-permission-troubleshooting:

GitHub permission troubleshooting
---------------------------------

**Repositories not in your list to import**.

Many organizations require approval for each OAuth application that is used,
or you might have disabled it in the past for your personal account.
This can happen at the personal or organization level,
depending on where the project you are trying to access has permissions from.

.. tabs::

   .. tab:: Personal Account

      You need to make sure that you have granted access to the Read the Docs `OAuth App`_ to your **personal GitHub account**.
      If you do not see Read the Docs in the `OAuth App`_ settings, you might need to disconnect and reconnect the GitHub service.

      .. seealso:: GitHub docs on `requesting access to your personal OAuth`_ for step-by-step instructions.

      .. _OAuth App: https://github.com/settings/applications
      .. _requesting access to your personal OAuth: https://docs.github.com/en/organizations/restricting-access-to-your-organizations-data/approving-oauth-apps-for-your-organization

   .. tab:: Organization Account

      You need to make sure that you have granted access to the Read the Docs OAuth App to your **organization GitHub account**.
      If you don't see "Read the Docs" listed, then you might need to connect GitHub to your social accounts as noted above.

      .. seealso:: GitHub doc on `requesting access to your organization OAuth`_ for step-by-step instructions.

      .. _requesting access to your organization OAuth: https://docs.github.com/en/github/setting-up-and-managing-your-github-user-account/managing-your-membership-in-organizations/requesting-organization-approval-for-oauth-apps

GitHub App
----------

.. warning::

   Our GitHub App is currently in beta, see our `blog post <https://about.readthedocs.com/blog/2025/06/announcing-our-github-app-beta/>`__ for more information.

We are in the process of migrating our GitHub OAuth application to a `GitHub App <https://docs.github.com/en/apps/overview>`__.
We have two GitHub Apps, one for each of our platforms:

- `Read the Docs Community <https://github.com/apps/read-the-docs-community>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business>`__

Features
~~~~~~~~

When using GitHub, Read the Docs uses a GitHub App to interact with your repositories.
This has the following benefits over using an OAuth application:

- More control over which repositories Read the Docs can access.
  You don't need to grant access to all your repositories in order to create an account or connect a project to a single repository.
- No need to create webhooks on your repositories.
  The GitHub App subscribes to all required events when you install it.
- No need to create a deploy key on your repository (|com_brand| only).
  The GitHub App can clone your private repositories using a temporal token.
- If the original user who connected the repository to Read the Docs loses access to the project or repository,
  the GitHub App will still have access to the repository.
- You can revoke access to the GitHub App at any time from your GitHub settings.
- Never out of sync with changes on your repository.
  The GitHub App subscribes to all required events and will always keep your project up to date with your repository.

Adding a project from a repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a project from a repository,
you need to install the Read the Docs GitHub App and grant access to that repository.
Use the links below to complete the installation and permissions,
then create the project from your **Read the Docs account**.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

Once you have installed the GitHub App, in Read the Docs, click on the :guilabel:`Projects` tab, and click on :guilabel:`Add project`,
search for the repository you want to create a project for, and then follow the instructions from there.

Connect a repository to an existing project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you manually added a project on Read the Docs,
or if you want to connect your project to a different repository,
you need to install the Read the Docs GitHub App and grant access to the repository you want to connect.
As with adding a project, complete installation and permissions via the links below,
and select the repository from your **project settings on Read the Docs**.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

Once you have installed the GitHub App, go to the :guilabel:`Settings` page of the project in Read the Docs,
and select the repository you want to connect from the :guilabel:`Connected repository` dropdown.

Manually migrating a project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We recommend using the migration page to migrate your projects from the old OAuth application to the new GitHub App.

- `Read the Docs Community <https://app.readthedocs.com/accounts/migrate-to-github-app/>`__
- `Read the Docs Business <https://app.readthedocs.com/accounts/migrate-to-github-app/>`__

But in case you need to manually migrate a project,
you can follow these steps:

- Go to the :guilabel:`Settings` page of your Read the Docs project,
  and click on the :guilabel:`Integrations` tab in Read the Docs, and delete all the integrations that are listed there.
- Go to the settings page of your GitHub repository,
  click on the GitHub :guilabel:`Webhooks` tab, and delete all the webhooks with URLs that start with:

  - ``https://readthedocs.org/api/v2/webhook/<your-project-slug>`` or ``https://app.readthedocs.org/api/v2/webhook/<your-project-slug>`` for Read the Docs Community.
  - ``https://readthedocs.com/api/v2/webhook/<your-project-slug>`` or ``https://app.readthedocs.com/api/v2/webhook/<your-project-slug>`` for Read the Docs Business.

- For projects using Read the Docs Business,
  go to the settings page of your GitHub repository,
  click on the GitHub :guilabel:`Deploy keys` tab, and delete the deploy with a title matching the format ``support@readthedocs.com (<your-project-slug>)``.
- :ref:`Connect the project to the repository <reference/git-integration:Connect a repository to an existing project>`.

Revoking access
~~~~~~~~~~~~~~~

.. warning::

   If you revoke access to the GitHub App with any of the methods below,
   all projects linked to that repository will stop working,
   but the projects and its documentation will still be available.
   If you grant access to the repository again,
   you will need to :ref:`manually connect your project to the repository <reference/git-integration:Connect a repository to an existing project>`.

You can revoke access to the Read the Docs GitHub App at any time from your GitHub settings.
All revocation options happen from your **account or organization settings**; no action is required inside Read the Docs until you decide to reconnect a project.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
- `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

There are three ways to revoke access to the Read the Docs GitHub App:

Revoke access to one or more repositories:
  Remove the repositories from the list of repositories that the GitHub App has access to.
Suspend the GitHub App:
  This will suspend the GitHub App and revoke access to all repositories.
  The installation and configuration will still be available,
  and you can re-enable the GitHub App at any time.
Uninstall the GitHub App:
  This will uninstall the GitHub App and revoke access to all repositories.
  The installation and configuration will be removed,
  and you will need to re-install the GitHub App and reconfigure it to use it again.

Security
~~~~~~~~

When cloning private repositories (|com_brand| only)
Read the Docs creates an `installation access token <https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#create-an-installation-access-token-for-an-app>`__,
which has read access to the `contents permission <https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps?apiVersion=2022-11-28#repository-permissions-for-contents>`__,
and it's scoped to the repository to be cloned.

This token is valid for one hour and GitHub automatically grants read access to the `metadata permission <https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps?apiVersion=2022-11-28#repository-permissions-for-metadata>`__,
which allows to query the repository collaborators, events, and other metadata.
By default, Read the Docs doesn't show this token during the build,
but the token is available during the whole build process.
Make sure to not print it in your build logs,
and that only trusted users are able to trigger builds on your project.

.. note::

   If your repository is public, Read the Docs will not create an installation access token.

.. note::

   The build log page is publicly accessible only if your project and version to build are marked as public.
   See more in :doc:`/commercial/privacy-level`.

Troubleshooting
~~~~~~~~~~~~~~~

Repository not found in the repository list
   Make sure you have installed the corresponding GitHub App in your GitHub account or organization,
   and have granted access to the repository your project will be connected to.

   - `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__
   - `Read the Docs Business <https://github.com/apps/read-the-docs-business/installations/new/>`__

   If you still can't see the repository in the list,
   you may need to wait a couple of minutes and refresh the page,
   or click on the "Refresh your repositories" button on the project creation page.

Repository is in the list, but isn't usable
   Make sure you have admin access to the repository you are trying to use for your project.
   If you are using |org_brand|, make sure your project is public,
   or use |com_brand| to create projects from private repositories.

   If you still can't use the repository for your project,
   you may need to wait a couple of minutes and refresh the page,
   or click on the "Refresh your repositories" button on the project creation page.
