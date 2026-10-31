How to configure pull request builds
====================================

In this section, you can learn how to configure :doc:`pull request builds </pull-requests>`.

Pull request builds are enabled by default on new projects.
Your Read the Docs project needs to be connected to a repository from a supported Git provider.
See `Limitations`_ for more information.

To enable or disable pull request builds:

#. Go to your project dashboard
#. Go to :guilabel:`Settings`, then :guilabel:`Pull request builds`
#. Enable or disable the :guilabel:`Build pull requests for this project` option
#. Click on :guilabel:`Update`

.. tip::

   Pull requests opened before enabling pull request builds will not trigger new builds automatically.
   Push a new commit to the pull request to trigger its first build.

.. note::

   The previous method of pull request previews using a GitHub workflow that called `@readthedocs/actions <https://github.com/readthedocs/actions/>`__ is now deprecated.
   If you used that method, you should remove its configuration.

Build overview
--------------

You can enable a build overview comment to be added to your pull requests when changes are detected between the pull request and the latest version of the documentation.
This comment includes a list of the files that changed, and links to view the built documentation.

.. seealso::
    :ref:`visual-diff:Show build overview in pull requests`
        How to configure your project to enable build overviews

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

- Pull request builds are only available for **GitHub** and **GitLab** currently. Bitbucket is not yet supported.
- To enable this feature, your Read the Docs project needs to be connected to a repository from a supported Git provider.
- If your project is using our :doc:`/projects/integrations/github-app` integration, you don't need to configure a webhook.
  For GitLab, and projects using the :ref:`projects/integrations/webhook:Github incoming webhook` integration,
  you may need to make sure that your webhook is configured to send pull request events, not just push events.
- Builds from pull requests have the same memory and time limitations
  :doc:`as regular builds </builds>`.
- Additional formats like PDF aren't built in order to reduce build time.
- Read the Docs doesn't index search on pull request builds. This means that Addons search and the Read the Docs Search API will return no results.
- The built documentation is kept for 90 days after the pull request has been closed or merged.
- The build overview comment is only available for projects connected to a :doc:`/projects/integrations/github-app` integration.

Troubleshooting
---------------

No new builds are started when I open a pull request
   When this happens, this usually indicates there is a problem with the project integration.
   Some of the following steps may help.

   .. TODO link this to a connected repository page when it exists instead. We
      don't have a good explanation of this anywhere yet.

   - Ensure the project is connected to your provider through either a :doc:`/projects/integrations/github-app`
     or :doc:`webhook </projects/integrations/webhook>` integration.
   - Ensure the project repository is using a connected repository to the correct repository.
   - Projects using the :doc:`GitHub or GitLab webhook integration </projects/integrations/webhook>`
     may need to update their integration and webhook.
     You can try :ref:`repairing the webhook scopes <projects/integrations/guides/troubleshooting-webhooks:Repairing webhook scopes>`.
   - Your connected service account is disconnected or needs to be repaired.

Build status is not being reported to your Git provider
   When a pull request build for your project starts,
   but the build status in the pull request is never updated,
   this usually indicates a :ref:`a general problem with the repository webhook <projects/integrations/guides/troubleshooting-webhooks:Build status is not reported>`.

.. seealso::
   :doc:`/projects/integrations/guides/troubleshooting-webhooks`
      Debugging problems with webhook integrations

.. _GitHub OAuth App: https://github.com/settings/applications
