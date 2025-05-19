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
