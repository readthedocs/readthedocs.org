Webhook integrations
====================

Several of the integrations that we support are incoming webhook integrations,
referring to the fact that these integrations accept inbound requests
from providers and take actions on these events.

Our webhook integrations each have varying support for features:

* `GitHub incoming webhook`_
* `GitLab incoming webhook`_
* `Bitbucket incoming webhook`_
* `Generic API incoming webhook`_

The way that each of these integrations works is by pointing a webhook from your
provider to the unique URL that is established by the webhook integration.
This URL accepts data on repository events and can trigger events and actions for your project.

All integrations are created with a secret token,
which offers a way to verify that a webhook request is legitimate.
Every request from the project's provider is recorded for the integration,
so you can confirm what your provider is sending.

.. seealso::

   :doc:`./guides/creating`
      Creating an integration for your project.

   :doc:`./guides/troubleshooting-webhooks`
      Troubleshooting problems with webhook integrations.

GitHub incoming webhook
-----------------------

This integration is our original integraiton for GitHub support.
It is still supported but we recommend GitHub users use our :doc:`./github-app` integration instead.
Several of our newest features only work on GitHub and only when using our GitHub App integration.

:Supported:
   - Triggering new builds
   - Commit events
   - Branch and tag events
   - Pull request builds
:Not supported:
   - Pull request comments
:Configuration methods:
   Automatic or manual
:Payload validation: 
   `Supported <https://developer.github.com/webhooks/securing/>`__

.. seealso::

   :doc:`./guides/managing-github-app`
      How to manage a GitHub App integration for your project.

GitLab incoming webhook
-----------------------

:Supported:
   - Triggering new builds
   - Commit events
   - Branch and tag events
   - Pull request builds
:Unsupported:
   - Pull request comments
:Configuration methods:
   Automatic or manual
:Payload validation: 
   `Supported <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#validate-payloads-by-using-a-secret-token>`__

For pull request builds to work,
the webhook has to be configured to send merge request events, not only push events.

Bitbucket incoming webhook
--------------------------

:Supported:
   - Triggering new builds
   - Commit events
   - Branch and tag events
:Unsupported:
   - Pull request builds
   - Pull request comments
:Configuration methods:
   Automatic or manual
:Payload validation: 
   `Supported <https://support.atlassian.com/bitbucket-cloud/docs/manage-webhooks/#Secure-webhooks>`__

Generic API incoming webhook
----------------------------

Repositories that are not hosted with a supported provider can use our
generic API incoming webhook integration.

:Supported:
   - Triggering new builds
:Unsupported:
   - Commit events
   - Branch and tag events
   - Pull request builds
   - Pull request comments
   - Commit status reporting
:Configuration methods:
   Manual only
:Payload validation: 
   Requires manual configuration

.. seealso::
   :doc:`./guides/creating-generic`
      How to create and configure a generic API integration.
