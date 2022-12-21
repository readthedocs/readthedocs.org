Connecting your Git repository
==============================

In this article, we explain how connecting your Read the Docs account to one of the supported Git providers
automatically configures your Git repository and your Read the Docs project.

If you are going to import repositories from GitHub, Bitbucket, or GitLab,
we recommend that you connect your Read the Docs account to your repository provider.
This is already done in cases where your sign-up for Read the Docs was handled through your Git provider.
If you have signed up to Read the Docs with your email address,
you can add the connection to the Git provider afterwards.

Connecting your account allows for:

* Easy import of your repositories
* Automatic configuration of your repository :doc:`/integrations`
  which allow Read the Docs to build your docs on every change to your repository
* Logging into Read the Docs with your GitHub, Bitbucket, or GitLab credentials

.. seealso::

   :doc:`/guides/connecting-git-account`
     Here are the steps to connect your Read the Docs account to your Git repository provider.

   :ref:`intro/import-guide:Manually import your docs`
     Using a different provider?
     Read the Docs still supports other providers such as Gitea or GitHub Enterprise.
     In fact, any Git repository URL can be configured manually.


.. tip::

   A single Read the Docs account can connect to many different Git providers.
   This means that you can gather all your documentation projects under the same roof.


Permissions for connected accounts
----------------------------------

Read the Docs does not generally ask for *write* permission to your repository code
(with one exception detailed below)
and since we only connect to public repositories we don't need special permissions to read them.
However, we do need permissions for authorizing your account
so that you can login to Read the Docs with your connected account credentials
and to setup :doc:`/integrations`
which allow us to build your documentation on every change to your repository.


GitHub
~~~~~~

Read the Docs requests the following permissions (more precisely, `OAuth scopes`_)
when connecting your Read the Docs account to GitHub.

.. _OAuth scopes: https://developer.github.com/apps/building-oauth-apps/understanding-scopes-for-oauth-apps/

Read access to your email address (``user:email``)
    We ask for this so you can create a Read the Docs account and login with your GitHub credentials.

Administering webhooks (``admin:repo_hook``)
    We ask for this so we can create webhooks on your repositories when you import them into Read the Docs.
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

Bitbucket
~~~~~~~~~

..
    Read your account information
    Read your repositories
    Administer your repositories
    Read your team membership information
    Read and modify your repositories' webhooks


For similar reasons to those above for GitHub, we request permissions for:

* Reading your account information including your email address
* Read access to your team memberships
* Read access to your repositories
* Read and write access to webhooks

GitLab
~~~~~~

Like the others, we request permissions for:

* Reading your account information (``read_user``)
* API access (``api``) which is needed to create webhooks in GitLab
