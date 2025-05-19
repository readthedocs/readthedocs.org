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
  Have Read the Docs subscribe to your repository's events,
  allowing us to build your docs on every change to your repository,
  and keep in sync with your tags and branches.

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

When your Read the Docs account is connected to GitHub, and you :doc:`add a new Read the Docs project </intro/add-project>`:

* Read the Docs automatically connects your project with the GitHub repository,
  and subscribes to the repository's events.
* Read the Docs makes use of its :ref:`GitHub App <reference/git-integration:GitHub App>` to interact with your repository.

When your Read the Docs account is connected to GitLab or Bitbucket, and you :doc:`add a new Read the Docs project </intro/add-project>`:

* Read the Docs automatically creates a Read the Docs Integration that matches your Git provider.
* Read the Docs creates an incoming webhook with your Git provider, which is automatically added to your Git repository's settings using the account connection.
* Read the Docs creates an SSH key, which is automatically added to your Git repository (when adding private repositories on |com_brand|).

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

   When using GitHub, Read the Docs uses a GitHub App that subscribes to all required events.
   You don't need to create a webhook on your repository.

Accounts with GitLab and Bitbucket integrations automatically have Read the Docs' incoming :term:`webhook` configured on all repositories that are imported.
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
since we trust that the user who connects the account is the owner of Git provider account.

By granting Read the Docs the requested permissions,
we are issued a secret OAuth token from your Git provider.
In the case of GitLab and Bitbucket, we can use the secret token
to automatically configure repositories during :doc:`project creation </intro/add-project>`.
For GitHub, you need to install our :ref:`GitHub App <reference/git-integration:GitHub App>` in the repository you want to add.

.. _OAuth: https://en.wikipedia.org/wiki/OAuth

.. note::

   Access granted to Read the Docs can always be revoked.
   This is a function offered by all Git providers.

Git provider integrations
-------------------------

.. note::

   When using GitHub, Read the Docs uses a GitHub App to interact with your repositories.
   If the original user who connected the repository to Read the Docs loses access to the project or repository,
   the GitHub App will still have access to the repository, and the integrations will continue to work.

If your project is using :doc:`Organizations </commercial/organizations>` (|com_brand|) or :term:`maintainers <maintainer>` (|org_brand|),
then you need to be aware of *who* is setting up the integration for the project.

The Read the Docs user who sets up the project through the automatic import should also have admin rights to the Git repository.

A Git provider integration is active through the authentication of the user that creates the integration.
If this user is removed,
make sure to verify and potentially recreate all Git integrations for the project.

Permissions for connected accounts
----------------------------------

Read the Docs does not generally ask for *write* permission to your repository code
(with one exception detailed below).
However, we do need permissions for authorizing your account
so that you can log in to Read the Docs with your connected account credentials.

.. tabs::

   .. tab:: GitHub

      Read the Docs requests the following permissions when connecting your Read the Docs account to GitHub.

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

      Organization permissions
        Members (read only)
          This allows Read the Docs to read the organization members.


   .. tab:: GitHub (old OAuth app integration)

      .. note::

         Read the Docs used to use a GitHub OAuth application for integration,
         which is being deprecated and replaced by a `GitHub App <https://docs.github.com/en/apps/overview>`__.
         If you haven't migrated your projects to the new GitHub App,
         we will still use the OAuth application to interact with your repositories for now,
         but we recommend migrating to the GitHub App for a better experience and more granular permissions.

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


GitHub App
----------

Read the Docs used to use a GitHub OAuth application for integration,
which has been replaced by a `GitHub App <https://docs.github.com/en/apps/overview>`__.
If you haven't migrated your projects to the new GitHub App,
we will still use the OAuth application similar to the other Git providers to interact with your repositories,
we recommend migrating to the GitHub App for a better experience and more granular permissions.

We have two GitHub Apps, one for each of our platforms:

- `Read the Docs Community <https://github.com/apps/read-the-docs-community>`__.
- `Read the Docs for Business <https://github.com/apps/read-the-docs-business>`__.

Features
~~~~~~~~

When using GitHub, Read the Docs uses a GitHub App to interact with your repositories.
This has the following benefits over using an OAuth application (like the other Git providers):

- More control over which repositories Read the Docs can access.
  You don't need to grant access to all your repositories in order to create an account or import a single repository.
- No need to create webhooks on your repositories.
  The GitHub App subscribes to all required events when you install it.
- No need to create a deploy key on your repository (|com_brand| only).
  The GitHub App can clone your private repositories using a temporal token.
- If the original user who connected the repository to Read the Docs loses access to the project or repository,
  the GitHub App will still have access to the repository.
- You can revoke access to the GitHub App at any time from your GitHub settings.
- Never out of sync with changes on your repository.
  The GitHub App subscribes to all required events and will always keep your project up to date with your repository.

Revoking access
~~~~~~~~~~~~~~~

You can revoke access to the Read the Docs GitHub App at any time from your GitHub settings.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__.
- `Read the Docs for Business <https://github.com/apps/read-the-docs-business/installations/new/>`__.

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

.. warning::

   If you revoke access to the GitHub App with any of the above methods,
   all projects linked to that repository will stop working,
   but the projects and its documentation will still be available.
   If you grant access to the repository again,
   you will need to manually connect your project to the repository.

.. _github-permission-troubleshooting:

Troubleshooting
~~~~~~~~~~~~~~~

**Repository not in the list to import**

Make sure you have installed the corresponding GitHub App in your GitHub account or organization,
and have granted access to the repository you want to import.

- `Read the Docs Community <https://github.com/apps/read-the-docs-community/installations/new/>`__.
- `Read the Docs for Business <https://github.com/apps/read-the-docs-business/installations/new/>`__.

If you still can't see the repository in the list,
you may need to wait a couple of minutes and refresh the page,
or click on the "Refresh your repositories" button in the import page.

**Repository is in the list, but can't be imported**

Make sure you have admin access to the repository you are trying to import.
If you are using |org_brand|, make sure your project is public,
or use |com_brand| to import private repositories.

If you still can't import the repository,
you may need to wait a couple of minutes and refresh the page,
or click on the "Refresh your repositories" button in the import page.
