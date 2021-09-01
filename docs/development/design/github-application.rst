==================
GitHub Application
==================

GitHub offers two different ways to access users' data from its own platform:
OAuth Application and GitHub Application. Depending on the applications
needings, GitHub recommends using one or the other.

Read the Docs currently uses the OAuth Application to support "Login with
GitHub" and "Import Project". They require different level of permissions, but
OAuth Application does not really allow us to manage them in a granular way.

Based on our needs and the GitHub recommendations in
https://docs.github.com/en/developers/apps/getting-started-with-apps/about-apps#determining-which-integration-to-build
we should use a GitHub Application for Read the Docs::

  Only as me? -> NO
  Act as an App -> NO
  Access Everything? -> NO
  -> GitHub Application

Or in case we need to act as an App, we end in the same route::

  Only as me? -> NO
  Act as an App -> YES
  -> GitHub Application

This document explains some problems we have found in our current implementation
using OAuth Application and explore the recommended way using GitHub
Application. It goes through the work required and touches a little about its
implementation.


Problems with current implementation
------------------------------------

* We request permissions that are too permissive at Sign Up

  Even if our application will never require some of these scopes (because it's
  a read user --and will never import a project), we ask for too many permissions.

* OAuth Application does not provide granular permissions

  We have to ask for ``read`` scope. It gives us read & write permissions to
  *all the repositories of this user*. This makes some users/organizations to
  don't want to user our platform.

  Besides, ``admin:repo_hook`` scope is also required to be able to create a
  webhook for pushes and trigger a new build.

* Repositories from an GitHub Organization does not appear in the "Import
  Project" list

  Organizations with OAuth App access restriction enabled, require users using
  our OAuth Application to request permissions to the GitHub Organization's
  owner to accept our OAuth App.


Goals
-----

* Reduce as much as possible granted permissions for our GitHub Application
* Do not require access to *all the users'/organizations' repositories*
* Allow Read the Docs GitHub Application only to specific repositories
* Support GitHub Application *and* OAuth Application at the same time during the
  migration time
* Support all the GitHub features current using OAuth Application
   * GitHub SSO
   * Pull Request builder
   * Trigger a build on push
* Don't require SSH key to clone private repositories


Non Goals
---------

* Escalate permissions as they are needed
* Migrate all current OAuth Application users to GitHub Application users at
  once
* Implement something similar to GitHub Application for other VCS providers
  (GitLab and Bitbucket)


Context related to GitHub Application
-------------------------------------

Considering there are too much confusion around GitHub Application and OAuth
Application, and copy&paste some context from its official documentation trying
to mitigate it and have a better understanding of this design doc.

  GitHub Apps are first-class actors within GitHub. A GitHub App acts on its own
  behalf, taking actions via the API directly using its own identity, which
  means you don't need to maintain a bot or service account as a separate user.

  GitHub Apps can be installed directly on organizations and user accounts and
  granted access to specific repositories. They come with built-in webhooks and
  narrow, specific permissions. When you set up your GitHub App, you can select
  the repositories you want it to access

  To install a GitHub App, you must be an organization owner or have admin
  permissions in a repository.

  Don't build an OAuth App if you want your application to act on a single
  repository. With the repo OAuth scope, OAuth Apps can act on all of the
  authenticated user's repositories.

(from  https://docs.github.com/en/developers/apps/getting-started-with-apps/about-apps)

  You can install GitHub Apps in your personal account or organizations you own.
  If you have admin permissions in a repository, you can install GitHub Apps on
  organization accounts. If a GitHub App is installed in a repository and requires
  organization permissions, the organization owner must approve the application.

  Account owners can use a GitHub App in one account without granting access to
  another ... A GitHub App remains installed if the person who set it up leaves
  the organization.

  The installation token from a GitHub App loses access to resources if an admin
  removes repositories from the installation.

  Installation access tokens are limited to specified repositories with the
  permissions chosen by the creator of the app.

  GitHub Apps can request separate access to issues and pull requests without
  accessing the actual contents of the repository.

  A GitHub App receives a webhook event when an installation is changed or
  removed. This tells the app creator when they've received more or less access to
  an organization's resources.

  A GitHub App can request an installation access token by using a private key
  with a JSON web token format out-of-band.

  An installation token identifies the app as the GitHub Apps bot, such as
  @jenkins-bot.

  GitHub Apps can authenticate on behalf of the user, which is called
  user-to-server requests. The flow to authorize is the same as the OAuth App
  authorization flow. User-to-server tokens can expire and be renewed with a
  refresh token

(from https://docs.github.com/en/developers/apps/getting-started-with-apps/differences-between-github-apps-and-oauth-apps)


GitHub Application requirements
-------------------------------

:Repository permissions:
   - Metadata: Read-only (mandatory)
   - Contents: Read-only
   - Commit statuses: Read & Write
   - Pull requests: Read-only

:Organization permissions:
   - Members: Read-only

:User permissions:
   - Email addresses: Read-only

:Events subscribed:
   - Meta (When this App is deleted and the associated hook is removed)
   - Create (Branch or tag created)
   - Delete (Branch or tag deleted)
   - Push (Git push to a repository)
   - Pull request (Pull request opened, closed, reopened, ...)


Authentication as GitHub Application
------------------------------------

https://docs.github.com/en/developers/apps/building-github-apps/authenticating-with-github-apps

Generate the JWT on Python:

.. code:: python

   import datetime
   import jwt
   GITHUB_APP_ID = 134302

   # content of PEM file downloaded from GH Application settings
   private_key = b'''-----BEGIN RSA PRIVATE KEY-----'''

   jwt.encode({"iat": datetime.datetime.utcnow() - datetime.timedelta(seconds=60), "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5), "iss": GITHUB_APP_ID}, private_key, algorithm="RS256")

Use the token generated in the previous step as authorization in the cURL command:

.. code:: bash

   $ curl -H "Authorization: Bearer <JWT>" -H "Accept: application/vnd.github.v3+json" https://api.github.com/app


.. note::

   For some reason this is not working and I'm getting:

   .. code:: text

     'Issued at' claim ('iat') must be an Integer representing the time that the assertion was issued


SSH keys are not required to clone private repositories
-------------------------------------------------------

When asking for ``contents`` (repository permission) we are able to clone
private repositories by using GitHub Application installation access tokens:

.. code:: bash

   git clone https://x-access-token:<token>@github.com/owner/repo.git

(from
https://docs.github.com/en/developers/apps/building-github-apps/authenticating-with-github-apps#http-based-git-access-by-an-installation)


Handling webhooks
-----------------

GitHub Application has *only one webhook* where it will receive all the events
for all the installations. The body contains all the information about the
particular installation that triggered the event. With this data, we will create
an access token and perform the query/actions we need.

There are some events that need to map to particular ``Project`` in our
database. For example, "a push to ``main`` branch in repository
``readthedocs/blog``" should "trigger a build for ``latest`` version on
``read-the-docs-blog`` project". For these cases we can use use
``repository.id`` field from the body to get the ``RemoteRepository.remote_id``
and from there get the ``Project``.


Remote* models re-sync
----------------------

Currently, we are using 2 endpoints to sync all the ``Remote*`` models:

* ``https://api.github.com/user/repos`` (https://docs.github.com/en/rest/reference/repos#list-repositories-for-the-authenticated-user)
* ``https://api.github.com/org/{org}/repos`` (https://docs.github.com/en/rest/reference/repos#list-organization-repositories)

However, this endpoints won't return the same data when using GitHub Application
since we won't be authenticated as a user anymore and the ``permission.admin:
boolean`` field won't come in the response.

Instead, we will have to iterate over,

* all repositories accessible to the app installation

  * ``https://api.github.com/installation/repositories`` (https://docs.github.com/en/rest/reference/apps#list-repositories-accessible-to-the-app-installation)
* iterate over each repository checking for user's permission

  * ``https://api.github.com/repos/{owner}/{repo}/collaborators/{username}/permission`` (https://docs.github.com/en/rest/reference/repos#get-repository-permissions-for-a-user)

By doing this, we will keep our ``Remote*`` table very small because we will
only track repositories that users gave us permissions. Then, only these
repositories will be shown in the "Import Project" page.

Once they created a new repository under their organization, if they haven't given us
access to "All repositories",
they will need to go to the GitHub Application installation configuration and grant access to the
new repository. This will send us a webhook (``installation_repositories``,
https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#installation_repositories)
and we can automatically do a re-sync of ``Remote*`` models.

Need more research
------------------

* Does django-allauth support GitHub Application for Login?

  Using the Client ID for the GitHub Application (instead the OAuth
  application), should make it to work:
  https://docs.github.com/en/developers/apps/building-github-apps/identifying-and-authorizing-users-for-github-apps#web-application-flow

* How do we use Client ID for GitHub Application for new users and Client ID for
  OAuth application for current/existing users?

* Should we keep using our OAuth Application for login and GitHub Application
  for the rest? Is it possible?

  Related: https://docs.github.com/en/developers/apps/getting-started-with-apps/migrating-oauth-apps-to-github-apps
  Related: https://github.com/readthedocs/readthedocs-ops/issues/532


Questions
---------

* How are we going to handle other VCS providers (GitLab and Bitbucket)?

  GitLab and Bitbucket does not offer another option than OAuth Application. We
  need to maintain the implementation that we currently have for them.

* Does it worth the effort integrating GitHub Application without being able to
  use the same for other services?

  GitHub is the most VCS provider used in our platform. Because of this, if the
  we can provide a better UX to most of our users I'd call it a win.

* Do we need to support both, GitHub Application and GitHub OAuth, at the same time?

  Yes. Current users will keep using GitHub OAuth for a long period of time. We
  could notify them encouraging them to migrate to our new GitHub Application.
  However, this will take a non-trivial amount of time.
