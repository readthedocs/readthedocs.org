Connecting Your Account
=======================

If you are going to import repositories from GitHub, Bitbucket, or GitLab,
you should connect your Read the Docs account to your repository host first.
Connecting your account allows for:

* Easier importing of your repositories
* Automatically configure your repository :doc:`webhooks`
  which allow Read the Docs to build your docs on every change to your repository
* Log into Read the Docs with your GitHub, Bitbucket, or GitLab credentials

If you signed up or logged in to Read the Docs with your GitHub, Bitbucket, or GitLab
credentials, you're all done. Your account is connected.

To connect your unconnected account, go to your *Settings* dashboard
and select `Connected Services <https://readthedocs.org/accounts/social/connections/>`_.
From here, you'll be able to connect to your GitHub, Bitbucket or GitLab
account. This process will ask you to authorize a connection to Read the Docs,
that allows us to read information about and clone your repositories.


Permissions for connected accounts
----------------------------------

Read the Docs does not generally ask for write permission to your repositories' code
(with one exception detailed below)
and since we only connect to public repositories we don't need special permissions to read them.
However, we do need permissions for authorizing your account
so that you can login to Read the Docs with your connected account credentials
and to setup :doc:`webhooks`
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


Bitbucket
~~~~~~~~~

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
