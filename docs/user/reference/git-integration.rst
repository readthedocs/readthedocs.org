Git provider account connection
===============================

Your Read the Docs account can be connected to your Git provider's account.
Connecting your account allows you to:

* Log in to Read the Docs with your |git_providers_or| credentials.

* Select a project to automatically import from all your Git repositories and organizations.
  See: :doc:`/intro/import-guide`.

* Have your Git repository automatically configured with your Read the Docs :term:`webhook`,
  which allows Read the Docs to build your docs on every change to your repository.


.. note::

   **Are you using GitHub Enterprise?**
      We offer customized enterprise plans for organizations.
      Please contact support@readthedocs.com.

   **Other Git providers**
      We also generally support all Git providers through :doc:`manual configuration </guides/setup/git-repo-manual>`.

Read the Docs incoming webhook
------------------------------

Accounts with |git_providers_and| integration automatically have Read the Docs' incoming :term:`webhook` configured on all Git repositories that are imported.
Other setups can setup the webhook through :doc:`manual configuration </guides/setup/git-repo-manual>`.

When an incoming :term:`webhook` notification is received,
we match it to a Read the Docs project.
The matching project will then process your build and publish the documentation.

The webhook takes care of the following:

* :doc:`Builds </builds>` the latest commit.
* Synchronizes your versions based on the latest tag and branch data in Git.
* Runs your :doc:`automation rules</automation-rules>`.
* Auto-cancels any currently running builds of the same version.
* :ref:`webhook_figure`

.. _webhook_figure:

.. figure:: /img/screenshot-webhook.png
   :alt: Screenshot of the Dashboard view for the incoming webhook

   All calls to the incoming webhook are logged.
   Each call can trigger builds and version synchronization.


Other features enabled by Git integration
-----------------------------------------

.. seealso::

   :doc:`/pull-requests`
      Your Read the Docs project will automatically be configured to send back build notifications,
      which can be viewed as commit statuses and on pull requests.

   :ref:`sso_git_provider`
      Git integration makes it possible for us to synchronize your Git repository's access rights from your Git provider.
      That way, the same access rights are effective on Read the Docs and you don't have to configure access in two places.
