How to configure pull request builds
====================================

In this section, you can learn how to configure :doc:`pull request builds </pull-requests>`.

To enable pull request builds for your project,
your Read the Docs account needs to be connected to an account with a supported Git provider.
See `Limitations`_ for more information.

If your account is already connected:

#. Go to your project dashboard
#. Go to :guilabel:`Admin`, then :guilabel:`Settings`
#. Enable the :guilabel:`Build pull requests for this project` option
#. Click on :guilabel:`Save`

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
#. Go to :guilabel:`Admin`, then :guilabel:`Settings`
#. Select your option in :guilabel:`Privacy level of builds from pull requests`
#. Click on :guilabel:`Save`

Privacy levels work the same way as :ref:`normal versions <versions:Version states>`.

Limitations
-----------

- Pull requests are only available for **GitHub** and **GitLab** currently. Bitbucket is not yet supported.
- To enable this feature, your Read the Docs account needs to be connected to an
  account with your Git provider.
- Builds from pull requests have the same memory and time limitations
  :doc:`as regular builds </builds>`.
- Additional formats like PDF aren't built in order to reduce build time.
- Read the Docs doesn't index search on pull request builds. This means that Addons search and the Read the Docs Search API will return no results.
- The built documentation is kept for 90 days after the pull request has been closed or merged.

Troubleshooting
---------------

No new builds are started when I open a pull request
   The most common cause is that your repository's webhook is not configured to
   send Read the Docs pull request events. You'll need to re-sync your project's
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
