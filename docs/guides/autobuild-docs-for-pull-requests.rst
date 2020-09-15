Autobuild Documentation for Pull Requests
=========================================

Read the Docs allows autobuilding documentation for pull/merge requests for GitHub or GitLab projects.
You can enable it by: 

.. tabs::

   .. tab:: |org_brand|

      You can turn PR builds on and off via an admin setting:

      * Go to :guilabel:`Admin > Advanced settings`
      * Enable the :guilabel:`Build pull requests for this project` option

   .. tab:: |com_brand|

      This feature is enabled by a feature flag currently in testing.
      You can reach our support at support@readthedocs.com to ask for it to be enabled.

      Once it is enabled you can turn it off and on by:

      * Go to :guilabel:`Admin > Advanced settings`
      * Enable the :guilabel:`Build pull requests for this project` option

Features
--------

- **Build on Pull/Merge Request Event:** We create an external version and trigger a build for that version
  when we receive pull/merge request open event from the webhook.
  We also trigger a new build when a new commit has been pushed to the Pull/Merge Request.

- **Warning Banner for Pull/Merge Request Documentation:** While building documentation for pull/merge requests
  we add a warning banner at the top of those documentations to let the users know that
  this documentation was generated from pull/merge requests and is not the main documentation for the project.

- **Send Build Status Notification:** We send build status reports to the status API of the provider (e.g. GitHub, GitLab).
  When a build is triggered for a pull/merge request we send build pending notification with the build URL
  and after the build has finished we send success notification if the build succeeded without any error
  or failure notification if the build failed.

.. figure:: ../_static/images/guides/github-build-status-reporting.gif
    :align: center
    :alt: GitHub Build Status Reporting for Pull Requests.
    :figwidth: 80%
    :target: ../_static/images/guides/github-build-status-reporting.gif

    GitHub Build Status Reporting for Pull Requests

Limitations
-----------

Auto-builds for pull/merge requests have
:doc:`the same limitations as regular documentation builds </builds>`.

Currently we don't index search for pull request builds.
Searches will default to the default experience for your tool.
This is a feature we plan to add,
but don't want to overwhelm our search indexes used in production.

Troubleshooting
---------------

After the feature is enabled on your project,
you might hit one of these issues:

#. **Pull Requests builds are not triggering**.
   We only support GitHub and GitLab currently. You need to make sure
   that your Read the Docs account is connected with that providers social account.
   You can check this by going to your `profile settings`_.

#. **Build status is not being reported on your Pull/Merge Request**.
   You need to make sure that you have granted access to the Read the Docs
   `OAuth App`_ to your/organizations GitHub account. If you do not see "Read the Docs"
   among the `OAuth App`_, you might need to disconnect and reconnect to GitHub service.
   Also make sure your webhook is properly setup
   to handle events. You can setup or ``re-sync`` the webhook from your projects admin dashboard.
   Learn more about setting up webhooks from our :doc:`Webhook Documentation </webhooks>`.

If you have tried all the above troubleshooting and still getting issues,
please let us know by sending us an `email <mailto:support@readthedocs.org>`__.

.. _profile settings: https://readthedocs.org/accounts/social/connections/
.. _OAuth App: https://github.com/settings/applications
