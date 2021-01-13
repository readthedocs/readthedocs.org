Preview Documentation from Pull Requests
========================================

Read the Docs allows to build and preview your documentation from pull/merge requests.
You can enable it by: 

#. Go to your project dashboard
#. Go to :guilabel:`Admin > Advanced settings`
#. Enable the :guilabel:`Build pull requests for this project` option
#. Click on :guilabel:`Save`

Features
--------

- **Build on Pull/Merge Request Events:** We create and build a new version when a pull/merge request is open,
  and when a new commit has been pushed.

- **Warning Banner:** A warning banner is shown at the top of the documentation
  to let users know that this isn't the main documentation for the project.

  .. note:: This feature is available only for :doc:`Sphinx projects </intro/getting-started-with-sphinx>`.

- **Build Status Report:** When a build is triggered, a build pending notification is send with a link to the build log,
  and when the build is done we send a success notification with the link to the preview or a failure notification with a link to the build log.

.. figure:: /_static/images/github-build-status-reporting.gif
   :align: center
   :alt: GitHub Build Status Reporting for Pull Requests.
   :figwidth: 80%
   :target: ../_static/images/guides/github-build-status-reporting.gif

   GitHub build status reporting

Privacy levels
--------------

.. note::

   Privacy levels are only supported on :doc:`/commercial/index`.

All docs built from a pull/merge requests are private by default.
Currently, this can't be changed, but we are planning to support this.

Limitations
-----------

- Auto-builds for pull/merge requests have
  :doc:`the same limitations as regular documentation builds </builds>`.
- Only available for GitHub and GitLab.
- Additional formats like PDF and Epub aren't build.
- Searches will default to the default experience for your tool.
  This is a feature we plan to add,
  but don't want to overwhelm our search indexes used in production.
- The built documentation is kept for 90 days after the pull/merge request has been closed or merged.

Troubleshooting
---------------

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

.. _profile settings: https://readthedocs.org/accounts/social/connections/
.. _OAuth App: https://github.com/settings/applications
