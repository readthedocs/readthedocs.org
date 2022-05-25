Preview Documentation from Pull Requests
========================================

Your project can be configured to build and host documentation for every new
pull request. Previewing changes to your documentation during review makes it
easier to catch documentation formatting and display issues introduced in pull
requests.

Features
--------

Build on pull request events
    We create and build a new version when a pull request is opened,
    and rebuild the version whenever a new commit is pushed.

Build status report
    Your project's pull request build status will show as one of your pull
    request's checks. This status will update as the build is running, and will
    show a success or failure status when the build completes.

    .. figure:: /_static/images/github-build-status-reporting.gif
       :align: center
       :alt: GitHub build status reporting for pull requests.
       :figwidth: 80%

       GitHub build status reporting

Warning banner
    A warning banner is shown at the top of documentation pages
    to let readers know that this version isn't the main version for the project.

    .. note:: Warning banners are available only for :doc:`Sphinx projects </intro/getting-started-with-sphinx>`.

Configuration
-------------

To enable this feature for your project,
your Read the Docs account needs to be connected to an account with a supported VCS provider.
See `Limitations`_ for more information.

If your account is already connected:

#. Go to your project dashboard
#. Go to :guilabel:`Admin`, then :guilabel:`Advanced settings`
#. Enable the :guilabel:`Build pull requests for this project` option
#. Click on :guilabel:`Save`

Privacy levels
--------------

.. note::

   Privacy levels are only supported on :doc:`/commercial/index`.

By default, all docs built from pull requests are private.
To change their privacy level:

#. Go to your project dashboard
#. Go to :guilabel:`Admin`, then :guilabel:`Advanced settings`
#. Select your option in :guilabel:`Privacy level of builds from pull requests`
#. Click on :guilabel:`Save`

Privacy levels work the same way as :ref:`normal versions <versions:privacy levels>`.

Limitations
-----------

- Only available for **GitHub** and **GitLab** currently. Bitbucket is not yet supported.
- To enable this feature, your Read the Docs account needs to be connected to an
  account with your VCS provider.
- Builds from pull requests have the same memory and time limitations
  :doc:`as regular builds </builds>`.
- Additional formats like PDF and EPUB aren't built, to reduce build time.
- Search queries will default to the default experience for your tool.
  This is a feature we plan to add,
  but don't want to overwhelm our search indexes used in production.
- The built documentation is kept for 90 days after the pull request has been closed or merged.

Troubleshooting
---------------

No new builds are started when I open a pull request
   The most common cause is that your repository's webhook is not configured to
   send Read the Docs pull request events. You'll need to re-sync your project's
   webhook integration to reconfigure the Read the Docs webhook.

   To resync your project's webhook, go to your project's admin dashboard,
   :guilabel:`Integrations`, and then select the webhook integration for your
   provider. Follow the directions on to re-sync the webhook, or create a new
   webhook integration.

   You may also notice this behavior if your Read the Docs account is not
   connected to your VCS provider account, or if it needs to be reconnected.
   You can (re)connect your account by going to your :guilabel:`Username dropdown`,
   :guilabel:`Settings`, then to :guilabel:`Connected Services`.


Build status is not being reported to your VCS provider
   If opening a pull request does start a new build, but the build status is not
   being updated with your VCS provider, then your connected account may have out
   dated or insufficient permisisons.

   Make sure that you have granted access to the Read the Docs `OAuth App`_ for
   your personal or organization GitHub account. You can also try reconnecting
   your account with your VCS provider.

.. seealso::
   - :ref:`integrations:Debugging webhooks`
   - :ref:`github-permission-troubleshooting`

.. _OAuth App: https://github.com/settings/applications
