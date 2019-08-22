Autobuild Documentation for Pull Requests
=========================================

Read the Docs allows autobuilding documentation for pull/merge requests for GitHub or GitLab projects.
This feature is currently available under a :doc:`Feature Flag </guides/feature-flags>`.
So, you can enable this feature by sending us an `email <mailto:support@readthedocs.org>`_ including your project URL.

Features
========

- **Build on Pull/Merge Request Event:** We create a ecternal version and trigger a build for that version
  when we receive pull/merge request open event from the webhook.
  We also trigger a new build when a new commit has been added to the Pull/Merge Request.

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

Troubleshooting
===============

After the feature is enabled on your project if everything does not work as expected,
some common causes might be:

1. Project repository should be from GitHub or GitLab. This feature is only available for GitHub or GitLab.
   So, if your projects provider is not GitHub or GitLab This feature will not work.

2. Social Account (GitHub, Gitlab) is not connected with Read the Docs account.
   if your project repository provider is GitHub or GitLab you need to make sure
   that you Read the Docs account is connected with that providers social account.
   you can check this by going to your `profile settings`_.

3. Webhook is not properly setup. You need to make sure your webhook is properly setup
   to handle events. you can setup or ``re-sync`` the webhook from you projects admin dashboard.
   Learn more about setting up webhooks from our :doc:`Webhook Documentation </webhooks>`.

If you have tried all the above troubleshooting and still getting issues,
please let us know by opening an `issue`_ on our GitHub Repository.

.. _profile settings: https://readthedocs.org/accounts/social/connections/
.. _issue: https://github.com/readthedocs/readthedocs.org/issues/new
