Troubleshooting webhook integrations
====================================

Our :doc:`webhook integrations <../webhook>` include:

* :ref:`projects/integrations/webhook:GitHub incoming webhook`
* :ref:`projects/integrations/webhook:GitLab incoming webhook`
* :ref:`projects/integrations/webhook:Bitbucket incoming webhook`
* :ref:`projects/integrations/webhook:Generic API incoming webhook`

.. seealso::
   :doc:`troubleshooting-github-app`
      Troubleshooting steps for project using our :doc:`../github-app` integration
      instead of one of our webhook integrations.

Inspecting webhook requests
---------------------------

If you are experiencing problems with an existing webhook integration,
you may be able to use the integration detail page to help debug the issue.
Each webhook integration stores the webhook request from the repository provider.
You'll find a list of these exchanges in any of the integration detail pages.

.. figure:: /img/screenshots/community-project-webhook-activity.png
   :alt: A list of requests to a webhook integration.

   A list of requests to a webhook integration.

My project isn't automatically building
---------------------------------------

If your project isn't automatically building,
start by `inspecting webhook requests to the integration <Inspecting webhook requests>`_
If there is no recent activity on your Read the Docs project webhook integration, then it's likely
that your Git provider is not configured correctly. If there is payload
information on your Read the Docs project, you might need to verify that your
versions are configured to build correctly.

Error: Webhook activation failed
--------------------------------

If your repository is not configured correctly, you may encounter the following error:

``Webhook activation failed. Make sure you have the necessary permissions``

Make sure your provider account has the correct permissions for the repository.

If your repository provider is GitHub and the repository is part of a GitHub organization,
check that you have granted access to the Read the Docs `OAuth App`_ to your organization.
A similar workflow is required for other supported providers.

.. _OAuth App: https://github.com/settings/applications

Repairing webhook scopes
------------------------

There are several problems that can manifest when a repository webhook
does not have the correct scopes or permissions.
The first repair to try in these cases would be to update any missing scopes.

If the integration is automatically configured and has a connected repository,
try re-syncing the webhook from the integration detail page.
Automatically configured integrations will have a button for re-syncing the webhook.
This will update the repository webhook if the connected repository link is still valid.

If the integration is manually configured,
one of the repository admins will need to manually verify the webhook scopes.
The :ref:`steps for manual integration creation <integration-create-manual>`
list the necessary scopes for each provider webhook.
You can review these directions on your existing repository webhook
and update any missing scopes or permissions.

Pull request builds not starting
--------------------------------

If your provider supports pull request builds but a pull request build does not start,
the most common issue is that the repository webhook is missing necessary scopes or permissions.

Start by attempting to `repair webhook scopes <Repairing webhook scopes>`_
and if that doesn't solve the problem, try recreating the webhook and
integration for your provider.

Build status is not reported
----------------------------

Similar to pull request builds not starting,
if a build is successful but its status is never updated with your provider,
the most common issue is that the repository webhook is missing necessary scopes or permissions.

Start by attempting to `repair webhook scopes <Repairing webhook scopes>`_
and if that doesn't solve the problem, try recreating the webhook and
integration for your provider.
