How to connect your Read the Docs account to your Git provider
==============================================================

In this how to article,
we cover how to connect an account on |git_providers_or| with your Read the Docs account.
This is relevant if you have signed up for Read the Docs with your email
or want to connect additional providers.

If you are going to import repositories from |git_providers_or|,
you should connect your Read the Docs account to your Git provider first.

.. note::

   If you signed up or logged in to Read the Docs with your |git_providers_or| credentials,
   you're all done. Your account is connected ✅️.
   You only need this how-to if you want to connect additional Git providers.

Adding a connection
-------------------

To connect your Read the Docs account with a Git provider,
go to the main login menu: :guilabel:`<Username dropdown>` > :guilabel:`Settings` > :guilabel:`Connected Services`.

From here, you'll be able to connect to your |git_providers_or|
account. This process will ask you to authorize an integration with Read the Docs.

.. figure:: /img/oauth_github_dialog.png
   :width: 300px
   :align: center
   :alt: Screenshot of example OAuth dialog on GitHub

   An example of how your OAuth dialog on GitHub may look.

After approving the request,
you will be taken back to Read the Docs.
You will now see the account appear in the list of connected services.

.. figure:: /img/screenshot_connected_services.png
   :width: 600px
   :align: center
   :alt: Screenshot of Read the Docs "Connected Services" page with multiple services connected

   Connected Services [#f1]_ [#f2]_ shows the list of Git providers that

Now your connection is ready and you will be able to import and configure Git repositories with just a few clicks.

.. seealso::

   :doc:`/reference/git-integration`
     Learn how the connected account is used for automatically configuring Git repositories and Read the Docs projects
     and which **permissions** that are required from your Git provider.

Removing a connection
---------------------

You may at any time delete the connection from Read the Docs.
Delete the connection makes Read the Docs forget the immediate access,
but you should also disable our OAuth Application from your Git provider.

* On GitHub, navigate to `Authorized OAuth Apps`_.
* On Bitbucket, navigate to `Application Authorizations`_.
* On GitLab, navigate to `Applications`_

.. _Authorized OAuth Apps: https://github.com/settings/applications
.. _Application Authorizations: https://bitbucket.org/account/settings/app-authorizations/
.. _Applications: https://gitlab.com/-/profile/applications

.. [#f1] `Connected Services on readthedocs.org <https://app.readthedocs.org/accounts/social/connections/>`_
.. [#f2] `Connected Services on readthedocs.com <https://app.readthedocs.com/accounts/social/connections/>`_
