Webhook integrations
====================

Several of the project integration types are incoming webhook integrations.
These integrations accept inbound requests from external services such as |git_providers_or|
and use the request information to trigger changes on projects,
like building a version, starting a pull request build, or synchronizing the repository versions.

The webhook integration types include:

* `GitHub incoming webhook`_
* `GitLab incoming webhook`_
* `Bitbucket incoming webhook`_
* `Generic API incoming webhook`_

Each webhook integration has a unique URL that accepts requests
and expects a request payload format specific to the service it supports.
These services each have their own support for *webhooks*,
which send outbound requests to the integration URL on changes and commits to a repository.
This allows the repository to alert projects immediately
instead of the project polling the repository for new changes.

All webhook integrations are created with a secret token,
which offers a way to verify that a webhook request is legitimate.
Every request into a webhook integration is also recorded
so you can confirm the data sent and debug issues with the integration.

.. seealso::

   :doc:`./guides/creating`
      Creating an integration for your project.

   :doc:`./guides/troubleshooting-webhooks`
      Troubleshooting problems with webhook integrations.

GitHub incoming webhook
-----------------------

This is our legacy integration for GitHub support.
It is still supported but we recommend GitHub users use our :doc:`./github-app` integration instead.
Several of our newest features, like GitHub commenting,
only work on GitHub and only when using our GitHub App integration.
This integration is not used when using a GitHub App connected service account to link your project and repository.

:Supported:
   - Triggering new builds
   - Version synchronization with branches and tags
   - Pull request builds
:Configuration methods:
   - Automatically configured
   - Manually configured

This integration primarily supports GitHub,
however several other providers like Gitea and Forgejo
use a compatible webhook payload and can also use this integration.

.. seealso::
   :ref:`Creating manually configured integrations <projects/integrations/guides/creating:Manually configured integration>`
      How to use the GitHub incoming webhook integration with other providers.

GitLab incoming webhook
-----------------------

GitLab is only supported through a webhook integration,
and some merge request features like merge trains
are not supported in pull request builds.

:Supported:
   - Triggering new builds
   - Version synchronization with branches and tags
   - Pull request builds
:Configuration methods:
   - Automatically configured
   - Manually configured

Bitbucket incoming webhook
--------------------------

Bitbucket support is limited and is only supported using a webhook integration.

:Supported:
   - Triggering new builds
   - Version synchronization with branches and tags
:Not supported:
   - Pull request builds
:Configuration methods:
   - Automatically configured
   - Manually configured

Generic API incoming webhook
----------------------------

Repositories that are not hosted with a supported provider can use our
generic API incoming webhook integration.

:Supported:
   - Triggering new builds
:Not supported:
   - Version synchronization with branches and tags
   - Pull request builds
:Configuration methods:
   - Manually configured only

.. seealso::
   :doc:`./guides/creating-generic`
      How to create and configure a generic API integration.
