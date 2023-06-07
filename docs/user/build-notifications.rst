Build notifications via webhooks and email
==========================================

Build notifications can alert you when your builds fail so you can take immediate action.
We offer the following methods for being notified:

Email notifications:
  Read the Docs allows you to configure build notifications via email.
  When builds fail,
  configured email addresses are notified.

Build Status Webhooks:
  Build notifications can happen via :term:`webhooks <webhook>`.
  This means that we are able to support a wide variety of services that receive notifications.

  Slack and Discord are supported through ready-made templates.

  Webhooks can be customized through your own template and a variety of variable substitutions.

.. seealso::
    :doc:`/guides/build/email-notifications`
        Enable email notifications on failed builds,
        so you always know that your docs are deploying successfully.

    :doc:`/guides/build/webhooks`
        Steps for setting up build notifications via webhooks,
        including examples for popular platforms like Slack and Discord.

    :doc:`pull-requests`
        Similarly to build notifications, you can also configure automated feedback for your pull requests.
