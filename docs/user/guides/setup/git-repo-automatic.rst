How to automatically configure a Git repository
===============================================

In this article, we explain how connecting your Read the Docs account to |git_providers_or|
makes Read the Docs able to automatically configure your imported Git repositories and your Read the Docs projects.

✅️ Signed up with your Git provider?
  If you signed up or logged in to Read the Docs with your |git_providers_or|
  credentials, you're all done. Your account is connected.

  The rest of this guide helps to understand how the automatic configuration works.

⏩️️ Signed up with your email address?
  If you have signed up to Read the Docs with your email address,
  you can add the connection to the Git provider afterwards.
  You can also add a connection to an additional Git provider this way.

  Please follow :doc:`/guides/connecting-git-account` in this case.

Automatic configuration
-----------------------

When your Read the Docs account is connected to |git_providers_or| and you import a Git repository,
the integration will automatically be configured on the Read the Docs project and on your Git repository.

Here is an outline of what happens:

#. A list of repositories that you have access to are automatically listed on Read the Docs' project import.
#. You choose a Git repository from the list (see :doc:`/intro/import-guide`).
#. Data about the repository is now fetched using the account connection and you are asked to confirm the setup.
#. When Read the Docs creates your project,
   it automatically sets up an integration with the Git provider,
   and creates an incoming webhook whereby Read the Docs is notified of all future changes to commits, branches and tags in the Git repository.
#. Your project's incoming webhook is automatically added to your Git repository's settings using the account connection.
#. Read the Docs also configures your project to use the Git provider's webhook via your account connection,
   so your project is ready to enable :doc:`Pull Request builds </guides/pull-requests>`.

After the import,
you can continue to configure the project.
All settings can be modified,
including the ones that were automatically created.

.. TODO: The following is for a feature reference.

.. If you are going to import repositories from |git_providers_or|,
.. we recommend that you connect your Read the Docs account to your Git provider.

.. Connecting your account allows for:

.. * Easy import of your repositories.
.. * Automatic configuration of your repository :doc:`/integrations`.
..   which allow Read the Docs to build your docs on every change to your repository
.. * Logging into Read the Docs with your |git_providers_or| credentials.


.. seealso::

   :ref:`intro/import-guide:Manually import your docs`
     Using a different provider?
     Read the Docs still supports other providers such as Gitea or GitHub Enterprise.
     In fact, any Git repository URL can be configured manually.


.. tip::

   A single Read the Docs account can connect to many different Git providers.
   This allows you to have a single login for all your various identities.


How does the connection work?
-----------------------------

Read the Docs uses `OAuth`_ to connect to your account at |git_providers_or|,
You are asked to grant permissions for Read the Docs to perform a number of actions on your behalf.

At the same time, we use this process for authentication (login)
since we trust that |git_providers_or| have verified your user account and email address.

By granting Read the Docs the requested permissions,
we are issued a secret OAuth token from your Git provider.

Using the secret token,
we can automatically configure the repository that you select in the :doc:`project import </intro/import-guide>`.
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

Permissions for connected accounts
----------------------------------

Read the Docs does not generally ask for *write* permission to your repository code
(with one exception detailed below)
and since we only connect to public repositories we don't need special permissions to read them.
However, we do need permissions for authorizing your account
so that you can login to Read the Docs with your connected account credentials
and to setup :doc:`/integrations`
which allow us to build your documentation on every change to your repository.


.. tabs::

   .. tab:: GitHub

      Read the Docs requests the following permissions (more precisely, `OAuth scopes`_)
      when connecting your Read the Docs account to GitHub.

      .. _OAuth scopes: https://developer.github.com/apps/building-oauth-apps/understanding-scopes-for-oauth-apps/

      Read access to your email address (``user:email``)
          We ask for this so you can create a Read the Docs account and login with your GitHub credentials.

      Administering webhooks (``admin:repo_hook``)
          We ask for this so we can create :term:`webhooks <webhook>` on your repositories when you import them into Read the Docs.
          This allows us to build the docs when you push new commits.

      Read access to your organizations (``read:org``)
          We ask for this so we know which organizations you have access to.
          This allows you to filter repositories by organization when importing repositories.

      Repository status (``repo:status``)
          Repository statuses allow Read the Docs to report the status
          (eg. passed, failed, pending) of pull requests to GitHub.
          This is used for a feature currently in beta testing
          that builds documentation on each pull request similar to a continuous integration service.

      .. note::

          :doc:`Read the Docs for Business </commercial/index>`
          asks for one additional permission (``repo``) to allow access to private repositories
          and to allow us to setup SSH keys to clone your private repositories.
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
        We ask for this so you can create a Read the Docs account and login with your Bitbucket credentials.

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
`````````````````````````````````

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
