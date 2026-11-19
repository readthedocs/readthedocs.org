Connected services
==================

Connected services link your user account on Read the Docs
with your account on another service using `one of our supported providers <Providers_>`_.
Users can have more than one connected service and multiple accounts for each provider.
Any of these accounts can be used to authenticate to your Read the Docs user.

When you connect a service, you authorize Read the Docs to act on your behalf using your connected account.
Support for connected service features varies between providers
and between |org_brand| and |com_brand|.

Providers
---------

The following providers and services can be linked to user accounts:

GitHub App
    This is our primary provider for connecting a GitHub account,
    it supports all of our features and provides granular repository permissions.
    *This is the recommended provider for connecting a GitHub account*.

GitHub OAuth
    The legacy provider for connecting a GitHub account.
    It is still supported,
    however new features such as GitHub commenting will not be available using this provider.
    *We recommend users migrate to our GitHub App provider*.

GitLab
    A full provider for GitLab, supports all features including pull request builds.

Bitbucket
    A basic provider for Bitbucket which supports cloning and building documentation,
    but features like pull request builds and pull request comments are not available.

Google (|com_brand| only)
    A :doc:`single sign-on </commercial/single-sign-on>` authentication provider for Google Workspace.
    This provider only supports authentication features,
    there are no repository or building features supported with this provider.

SAML (|com_brand| only)
    A :doc:`single sign-on </commercial/single-sign-on>` authentication provider for SAML sources.
    This provider only supports authentication features,
    there are no repository or building features supported with this provider.

Features
--------

The providers above have varying support for platform features:

.. This uses prose style lists in the definition lists for provider support
   because a table is too cramped for everything we need to fit. Some of the
   concepts will be better explained here or on the provider page.

Authentication and login
    Use your provider account to log in to your Read the Docs account.

    Supported by GitHub App, GitHub OAuth, GitLab, Bitbucket, Google [1]_, and SAML [1]_.

Automatic project configuration
    List the repositories your provider account has permissions to access
    and automatically create and configure projects from any of these repositories.

    Supported by GitHub App, GitHub OAuth, GitLab, and Bitbucket.

Pull request builds
    Creates a temporary build from a pull request or merge request.

    Supported by GitHub App, GitHub OAuth, and GitLab.

Single sign-on (|com_brand| only)
    For organizations with :doc:`single sign-on authentication enabled </commercial/single-sign-on>`,
    access to projects and documentation is controlled through connected service accounts.

    For single sign-on using |git_providers_or|,
    the project's repository determines access to the connected service accounts.
    Access checks include both authentication (can the user log in)
    and authorization (does the user have access to this repository).

    Single sign-on using Google or SAML only performs authentication checks for accounts on these services.
    Organizations can configure teams to control user authorization to projects.

    Supported by GitHub App, GitHub OAuth, GitLab, Bitbucket, Google, and SAML.
    :doc:`Provider support for single sign-on </commercial/single-sign-on>`

.. [1] Google and SAML providers are only supported on |com_brand|

Integrations
------------

When an :doc:`automatically configured project integration </projects/integrations/index>` is created,
a connected service account of the user creating the integration will be used
by the integration to configure the project and repository.
From then on, interactions between the project and repository will reuse this
connected service account.

To maintain a working project integration, there always needs to be at least one user
with the correct permissions and a connected service account for your repository provider.
If the connected service is disconnected for any reason,
the project will instead use a connected service account from another user with access to the repository.
On |org_brand|, the next available project maintainer will be used,
and on |com_brand| the next available organization owner will be used.
If there are no users remaining with a connected service account,
the project may fail to continue building.

Security
--------

Each of the providers uses different permissions and levels of control.
Some providers require broad permissions at the account level,
especially to support private repositories.
We list :doc:`all of the permissions and OAuth scopes <./providers>`
required by each of our providers.

.. toctree::
   :hidden:

   Permissions </account/user/providers>
