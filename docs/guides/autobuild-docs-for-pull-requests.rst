Autobuild Documentation for Pull Requests
=========================================

Read the Docs allows autobuilding documentation for pull/merge requests for GitHub or GitLab projects.
This feature is currently available under a :doc:`Feature Flag </guides/feature-flags>`.
So, you can enable this feature by sending us an `email <mailto:support@readthedocs.org>`_ including your project URL.

Troubleshooting
===============

After the feature is enabled on your project if everything does not work as expected,
some common issues might be:

1. Social Account (GitHub, Gitlab) is not connected with Read the Docs account.
   if your project repository provider is GitHub or GitLab you need to make sure
   that you Read the Docs account is connected with that providers social account.
   you can check this by going to your `profile settings`_.

2. Webhook is not properly setup. You need to make sure your webhook is properly setup
   to handle events. you can ``re-sync`` the webhook from you projects admin dashboard.
   Learn more about setting up webhooks from our :doc:`Webhook Documentation </webhooks>`.


.. _profile settings: https://readthedocs.org/accounts/social/connections/
