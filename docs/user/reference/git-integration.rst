Git provider integrations
=========================

Your Read the Docs account can be connected to your Git provider's account.
Connecting your account provides the following features:

🔑️ Easy login
  Log in to Read the Docs with your |git_providers_or| account.

🔁️ List your projects
  Select a project to automatically import from all your Git repositories and organizations.
  See: :doc:`/intro/import-guide`.

⚙️ Automatic configuration
  Have your Git repository automatically configured with your Read the Docs :term:`webhook`,
  which allows Read the Docs to build your docs on every change to your repository.

🚥️ Commit status
  See your documentation build status as a commit status indicator on :doc:`pull request builds </pull-requests>`.

.. note::

   **Are you using GitHub Enterprise?**
      We offer customized enterprise plans for organizations.
      Please contact support@readthedocs.com.

   **Other Git providers**
      We also generally support all Git providers through :doc:`manual configuration </guides/setup/git-repo-manual>`.

.. figure:: /img/screenshot-webhook.png
   :alt: Screenshot of the Dashboard view for the incoming webhook

   All calls to the incoming webhook are logged.
   Each call can trigger builds and version synchronization.

Read the Docs incoming webhook
------------------------------

Accounts with |git_providers_and| integration automatically have Read the Docs' incoming :term:`webhook` configured on all Git repositories that are imported.
Other setups can setup the webhook through :doc:`manual configuration </guides/setup/git-repo-manual>`.

When an incoming webhook notification is received,
we ensure that it matches an existing Read the Docs project.
Once we have validated the webhook,
we take an action based on the information inside of the webhook.

Possible webhook actions outcomes are:

* :doc:`Builds </builds>` the latest commit.
* Synchronizes your versions based on the latest tag and branch data in Git.
* Runs your :doc:`automation rules</automation-rules>`.
* Auto-cancels any currently running builds of the same version.

Other features enabled by Git integration
-----------------------------------------

We have additional documentation around features provided by our Git integrations:

.. seealso::

   :doc:`/pull-requests`
      Your Read the Docs project will automatically be configured to send back build notifications,
      which can be viewed as commit statuses and on pull requests.

   :ref:`sso_git_provider`
      Git integration makes it possible for us to synchronize your Git repository's access rights from your Git provider.
      That way, the same access rights are effective on Read the Docs and you don't have to configure access in two places.
