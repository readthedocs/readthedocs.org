Preview Documentation from Pull Requests
========================================

Read the Docs allows you to build and preview your documentation from pull requests.
To enable this feature:

#. Go to your project dashboard
#. Go to :guilabel:`Admin > Advanced settings`
#. Enable the :guilabel:`Build pull requests for this project` option
#. Click on :guilabel:`Save`

Features
--------

- **Build on Pull Request Events:** We create and build a new version when a pull request is open,
  and when a new commit has been pushed.

- **Build Status Report:** When a build is triggered, a build pending notification is sent with a link to the build log.
  When the build finishes we send a success notification with the link to the preview or a failure notification with a link to the build log.

- **Warning Banner:** A warning banner is shown at the top of the documentation
  to let users know that this isn't the main documentation for the project.

  .. note:: Warning banners are available only for :doc:`Sphinx projects </intro/getting-started-with-sphinx>`.

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

By default all docs built from pull requests are private.
To change their privacy level:

#. Go to your project dashboard
#. Go to :guilabel:`Admin > Advanced settings`
#. Select your option in :guilabel:`Privacy level of builds from pull requests`
#. Click on :guilabel:`Save`

Privacy levels work the same way as for :ref:`normal versions <versions:privacy levels>`.

Limitations
-----------

- Builds from pull requests have the same memory and time limitations
  :doc:`as regular builds </builds>`.
- Only available for GitHub and GitLab.
- Additional formats like PDF and Epub aren't built to produce results quicker.
- Searches will default to the default experience for your tool.
  This is a feature we plan to add,
  but don't want to overwhelm our search indexes used in production.
- The built documentation is kept for 90 days after the pull request has been closed or merged.

Troubleshooting
---------------

#. **Pull Requests builds are not triggered**.
   We only support GitHub and GitLab currently.
   You need to make sure that your Read the Docs account is connected with that provider.
   You can check this by going to your :guilabel:`Username dropdown` > :guilabel:`Settings` > :guilabel:`Connected Services`.

#. **Build status is not being reported to your VCS provider**.
   You need to make sure that you have granted access to the Read the Docs
   OAuth App to your personal or organization GitHub account.
   Learn more about this in our :ref:`github-permission-troubleshooting` section.

   Also make sure your webhook is properly setup
   to handle events related to pull requests. You can setup or ``re-sync`` the webhook from your projects admin dashboard.
   Learn more about setting up webhooks from our :doc:`Webhook Documentation </webhooks>`.

.. _OAuth App: https://github.com/settings/applications
