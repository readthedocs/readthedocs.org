GitHub App
==========

Our GitHub App integration consists of a GitHub App (one for each platform, readthedocs.org and readthedocs.com),
which can be installed on a user's account or organization.

After installing the GitHub App, users can grant access to all repositories or select specific repositories,
this allows Read the Docs to access the repositories and perform actions on them, such as reporting build statuses,
and subscribe to events like push and pull request events.

Unlike our other Git integrations, this doesn't rely on user's OAuth2 tokens to interact with the repositories, instead it makes use of the installation.
As long as the installation is active and has access to the repositories, Read the Docs can perform actions on them.

Installations can be `suspended <https://docs.github.com/en/apps/maintaining-github-apps/suspending-a-github-app-installation>`__,
which means that the GitHub App is still installed but cannot access any resources, this action is reversible.
Installations can also be uninstalled, which means that the GitHub App is removed from the account or organization,
and cannot access any resources, this action is irreversible.

You can read more about GitHub Apps in `GitHub's documentation <https://docs.github.com/en/apps/overview>`__.

Modeling
--------

Since we no longer make use of user's OAuth2 tokens, we need to keep track of all the installations of our GitHub App in the database (``GitHubAppInstallation`` model).
Each remote repository has a foreign key to the installation that has access to it,
so we can use that installation to perform actions on the repository.

Keeping data in sync
--------------------

Once a GitHub app is installed, GitHub will send webhook events to our application (``readthedocs.oauth.views``) related to the installation
(even when the installation is uninstalled or revoked), repositories, and organizations.
This allows us to always have the ``RemoteRepository`` and ``RemoteOrganization`` models and its permissions in sync with GitHub.

The only use case for using the user's OAuth2 token is to get all the installations the user has access to,
this helps us to keep permissions in sync with GitHub.

Security
--------

- All webhooks are signed with a secret, which we verify before processing each event.
- Since we make use of the installation to perform actions on the repositories instead of the user's OAuth2 token,
  we make sure that only users with admin permissions on the repository can link the repository to a Read the Docs project.
- Once we lose access to a repository (e.g. the installation is uninstalled or revoked, or the project was deselected from the installation),
  we remove the remote repository from the database, as we don't want to keep the relation between the project and the repository.
  This is to prevent connecting the repository to the project again without the user's consent if they grant access to the repository again.
