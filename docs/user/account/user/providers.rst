Provider permissions
====================

Each provider has its own set of permissions or scopes required to interact with
repositories and APIs and when configuring :doc:`project integrations </projects/integrations/index>`.
These permissions are all requested against your account
as you connect a new service account.

GitHub App
~~~~~~~~~~

The GitHub App provider will progressively ask for required permissions,
but when initially adding a new connected service
only account level permissions needed for authentication will be requested:

Account email addresses (read only)
   Used to create a Read the Docs account and enables authentication with your GitHub credentials.

Later on, when creating a project or connecting a repository to an existing project,
additional permissions will be granted as our GitHub App is installed for repositories and organizations.

GitHub OAuth
~~~~~~~~~~~~

This is our legacy provider for GitHub,
it is still supported but we recommend users use the GitHub App provider instead.
When adding a connected service, the following `GitHub OAuth scopes`_ will be requested:

.. _GitHub OAuth scopes: https://developer.github.com/apps/building-oauth-apps/understanding-scopes-for-oauth-apps/

Read access to email addresses (``user:email``)
   Used to create a Read the Docs account and enables authentication with your GitHub credentials.

Managing project integrations (``admin:repo_hook``)
   Required to create a :doc:`project integration </projects/integrations/index>`
   and configure repositories for building.

Read access to organizations (``read:org``)
   Used to determine which organizations your GitHub account has access to.

Repository status (``repo:status``)
   Used to report the build status of pull request builds to GitHub.

Repository access (``repo``) (|com_brand| only)
   On :doc:`Read the Docs Business </commercial/index>` connected services,
   this additional scope is requested for GitHub accounts.
   This is needed to configure the repositories with deploy keys
   so that the repository can be cloned.
   Unfortunately, this permission includes
   *read and write access for any repository the user has access to*.
   We recommend users use our GitHub App provider to avoid this permissive scope,
   which grants granular permissions and uses temporary tokens for cloning access.

GitLab
~~~~~~

The following `GitLab access token scopes`_ are requested for your user account
when adding a connected service:

.. _`GitLab access token scopes`: https://docs.gitlab.com/security/tokens/access_token_scopes/

Reading account information (``read_user``)
   Used to create a Read the Docs account and enables authentication with your GitLab credentials.

API access (``api``)
   Required to create a :doc:`project integration </projects/integrations/index>`
   and configure repositories for building.
   While we do not use this scope to write to repositories,
   *this scope still includes read and write permissions to repositories the account has access to.*

Bitbucket
~~~~~~~~~

The following `Bitbucket API scopes`_ are requested for your user account when
adding a connected service:

.. _`Bitbucket API scopes`: https://developer.atlassian.com/cloud/bitbucket/bitbucket-cloud-rest-api-scopes/

Read access to repositories (``repository``)
   Used to list repositories your account has access to.

Administering repositories (``repository:admin``)
   Required to create a :doc:`project integration </projects/integrations/index>`
   and configure repositories for building.
   *This scope does not include write access to repositories.*

Reading account information (``account``)
   Used to create a Read the Docs account,
   enable authentication with your Bitbucket credentials,
   and determine which workspaces you have access to.

Google
~~~~~~

This provider is only available on |com_brand| and is only used for authentication.
The following `Google API scopes`_ are requested for your user account when
adding a connected service:

.. _`Google API scopes`: https://developers.google.com/identity/protocols/oauth2/scopes

Reading account information (``profile`` and ``email``)
   Used to create a Read the Docs account and
   enable authentication with your Google credentials.

SAML
~~~~

This provider is only available on |com_brand| and is only used for authentication.
Necessary permissions may depend on the SAML provider used,
however only account information is required for this provider to function.

.. seealso::
   :doc:`/guides/set-up-single-sign-on-saml`
      Learn how to configure SAML providers for single sign-on.
