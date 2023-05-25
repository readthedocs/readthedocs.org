Build Notifications and Webhooks
================================

Read the Docs features a number of build notification mechanisms.
Build notifications can alert you when your builds fail so you can take immediate action.

Email notifications:
  Read the Docs allows you to configure emails that can be sent on failing builds.
  This makes sure you know when your builds have failed.

Build Status Webhooks:
  Build notifications can happen via :term:`webhooks <webhook>`.
  This means that we are able to support a wide variety of services that receive notifications.

  Slack and Discord are supported through ready-made templates.

  Webhooks can be customized through your own template and a variety of variable substitutions.

.. seealso::
    :doc:`/guides/build-notifications`
        All the practical steps for setting up build notifications

    :doc:`pull-requests`
        Similarly to build notifications, you can also configure automated feedback for your pull requests.
