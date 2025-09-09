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
- In order to have pull request build links automatically added to your pull requests, you must configure an automation to accomplish this with your Git provider. For example, see `these instructions <https://github.com/readthedocs/actions/blob/v1/preview/README.md>`_ to configure with GitHub Actions.

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

Pull request build links (such as those generated from `the official GitHub Action <https://github.com/readthedocs/actions/blob/v1/preview/README.md>`_) return a 404 error
   This means that a build is not being triggered.

   Verify your repository's webhook is properly synced with Read the Docs, and configured to send pull request events. For GitHub, you can check this by visiting the "Webhooks" section of the repository's "Settings" page. For your Read the Docs webhook, under "Which events would you like to trigger this webhook?", choose "Send Me Everything," or manually select push events and all events relevant to pull requests.

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
