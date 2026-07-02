How to configure pull request builds
====================================

In this section, you can learn how to configure :doc:`pull request builds </pull-requests>`.

To enable pull request builds for your project,
your Read the Docs project needs to be connected to a repository from a supported Git provider.
See `Limitations`_ for more information.

#. Go to your project dashboard
#. Go to :guilabel:`Settings`, then :guilabel:`Pull request builds`
#. Enable the :guilabel:`Build pull requests for this project` option
#. Click on :guilabel:`Update`

.. tip::

   Pull requests opened before enabling pull request builds will not trigger new builds automatically.
   Push a new commit to the pull request to trigger its first build.

.. note::

   The previous method of pull request previews using a GitHub workflow that called `@readthedocs/actions <https://github.com/readthedocs/actions/>`__ is now deprecated.
   If you used that method, you should remove its configuration.

Privacy levels
--------------

.. note::

   Privacy levels are only supported on :doc:`/commercial/index`.

If you didn’t import your project manually and your repository is public,
the privacy level of pull request previews will be set to *Public*,
otherwise it will be set to *Private*.
Public pull request previews are available to anyone with the link to the preview,
while private previews are only available to users with access to the Read the Docs project.

.. warning::

   If you set the privacy level of pull request previews to *Private*,
   make sure that only trusted users can open pull requests in your repository.

   Setting pull request previews to private on a public repository can allow a malicious user
   to access read-only APIs using the user's session that is reading the pull request preview.
   Similar to `GHSA-pw32-ffxw-68rh <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-pw32-ffxw-68rh>`__.

To change the privacy level:

#. Go to your project dashboard
#. Go to :guilabel:`Settings`, then :guilabel:`Pull request builds`
#. Select your option in :guilabel:`Privacy level of builds from pull requests`
#. Click on :guilabel:`Update`

Privacy levels work the same way as :ref:`normal versions <versions:Version states>`.

Build overview
--------------

You can enable a build overview comment to be added to your pull requests when changes are detected between the pull request and the latest version of the documentation.
This comment includes a list of the files that changed, and links to view the built documentation.
See :ref:`visual-diff:Show build overview in pull requests` for more information.

Limitations
-----------

- Pull requests are only available for **GitHub** and **GitLab** currently. Bitbucket is not yet supported.
- To enable this feature, your Read the Docs project needs to be connected to a repository from a supported Git provider.
- If your project is using our :ref:`reference/git-integration:GitHub App`, you don't need to configure a webhook.
  For GitLab, and projects using our old GitHub integration, you need to make sure that your webhook is configured to send pull request events, not just push events.
- Builds from pull requests have the same memory and time limitations
  :doc:`as regular builds </builds>`.
- Additional formats like PDF aren't built in order to reduce build time.
- Read the Docs doesn't index search on pull request builds. This means that Addons search and the Read the Docs Search API will return no results.
- The built documentation is kept for 90 days after the pull request has been closed or merged.
- The build overview comment is only available for projects connected to a :ref:`reference/git-integration:GitHub App`.

Troubleshooting
---------------

No new builds are started when I open a pull request
   The most common cause when using GitHub is that your Read the Docs project is not
   :ref:`connected to the corresponding repository on GitHub <reference/git-integration:Connect a repository to an existing project>`.

   If you are using our old GitHub integration,
   make sure that your repository's webhook is configured to
   send pull request events. You can re-sync your project's
   webhook integration to reconfigure the Read the Docs webhook.

   To re-sync your project's webhook, go to your project's admin dashboard,
   :guilabel:`Integrations`, and then select the webhook integration for your
   provider. Follow the directions to re-sync the webhook, or create a new
   webhook integration.

   You may also notice this behavior if your Read the Docs account is not
   connected to your Git provider account, or if it needs to be reconnected.
   You can (re)connect your account by going to your :guilabel:`<Username dropdown>`,
   :guilabel:`Settings`, then to :guilabel:`Connected Services`.

Build status is not being reported to your Git provider
   If opening a pull request does start a new build, but the build status is not
   being updated with your Git provider, then your connected account may have out
   dated or insufficient permissions.

   Make sure that you have granted access to the Read the Docs `GitHub OAuth App`_ for
   your personal or organization GitHub account.

.. seealso::
   - :ref:`guides/setup/git-repo-manual:Debugging webhooks`
   - :ref:`github-permission-troubleshooting`

.. _GitHub OAuth App: https://github.com/settings/applications
