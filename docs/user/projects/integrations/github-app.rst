GitHub App
==========

This integration uses a `GitHub App <https://docs.github.com/en/apps/overview>`__
for connecting your repositories to Read the Docs.

:Supported features:
   - Triggering new builds
   - Commit events
   - Branch and tag events
   - Pull request builds
   - Pull request comments
:Configuration methods:
   Automatic only

Differences with GitHub integrations
------------------------------------

This integration supersedes our :ref:`projects/integrations/webhook:GitHub incoming webhook` integration,
and differs in how projects operate and features supported on GitHub:

- You control which repositories Read the Docs can access.
  You don't need to grant access to all of your repositories to create an
  account or to connect a project to a single repository.
- All repository management is handled by the integration,
  there is no manual configuration option for repositories and projects.
- Repositories are cloned using a temporary token instead of a long-lived deploy key.
- If the original user who connected the repository loses access to the project
  or to the repository, the integration will keep working.

Permissions
-----------

Read the Docs requests the following account level permissions when you install
our GitHub App:

Account email addresses (read only)
   We ask for this so we can verify your email address and create a Read the Docs account.

When you install the GitHub App on a repository, you are asked to grant the following
repository permissions:

Commit statuses (read and write)
   This allows Read the Docs to report the status of the build to GitHub.

Contents (read only)
   This allows Read the Docs to clone the repository and build the documentation.

Metadata (read only)
   This allows Read the Docs to read the repository collaborators and the
   permissions they have on the repository.
   This is used to determine if the user can connect a repository to a Read the Docs project.

Pull requests (read and write)
   This allows Read the Docs to subscribe to pull request events,
   and to create a comment on the pull request with information about the build.

Checks (read and write)
   This allows Read the Docs to use the GitHub Checks API to report the status of
   the build.
   This isn't used yet, but we may use it in the future.

And the following organization permissions:

Members (read only)
   This allows Read the Docs to read the organization members.

Security
--------

When Read the Docs clones a private repository (|com_brand| only),
it creates an `installation access token <https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#create-an-installation-access-token-for-an-app>`__,
which has read access to the `contents permission <https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps?apiVersion=2022-11-28#repository-permissions-for-contents>`__,
and it is scoped to the repository being cloned.

This token is valid for one hour.
GitHub automatically grants it read access to the `metadata permission <https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps?apiVersion=2022-11-28#repository-permissions-for-metadata>`__,
which allows querying the repository collaborators, events, and other metadata.

By default Read the Docs doesn't show this token during the build,
but the token is available for the whole build process.
Make sure it isn't printed in your build logs,
and that only trusted users are able to trigger builds on your project.

.. note::

   If your repository is public, Read the Docs does not create an installation access token.

.. seealso::

   :doc:`/guides/pull-requests`
      How to configure pull request builds.
