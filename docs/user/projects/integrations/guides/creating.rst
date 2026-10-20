Creating an integration
=======================

There are :ref:`two configuration methods <projects/integrations/index:Configuration methods>`
for integrations, which one you use mostly depends on what connected services your account has
available:

`Automatically configured integration`_
    By adding a connected service account to your user and connecting your
    repository to your project, an integration will be automatically connected. 
    **This is recommended for most projects**.

`Manually configured integration`_
    Manually configured integrations can be used by any project using an
    unsupported provider or where no maintainer has a connected provider account.

Automatically configured integration
------------------------------------

Integrations that are automatically configured do not require any configuration
steps from project maintainers. Once a repository is connected to your project,
an integration will be created and the repository will be automatically
configured to use the integration and allow Read the Docs to clone the repository.

This will require that a project maintain has a connected service account for
the repository's provider.

.. TODO pointers to next steps. Link to connected repository page when it exists

Manually configured integration
-------------------------------

For some cases, projects will not be able to use automatically configured
integrations. If your repository's provider is not supported or you do not have
a connected service account for your provider, your project will have to use a
manually configured integration instead.

.. warning::
   Manual configuration is only recommended for advanced users.
   Project maintainers are responsible for all project and repository configuration.
   We recommend most projects use a connected repository and automaticallly
   configured integration.

To manually set up an integration for your project,
go to :guilabel:`Settings` > :guilabel:`Integrations` >  :guilabel:`Add integration`
and select the integration type you'd like to add.

.. list-table::
   :header-rows: 1
   :widths: 30 40 30
   :class: wy-table-wide

   * - Provider
     - Integration type
     - Support level
   * - GitHub
     - :ref:`projects/integrations/webhook:GitHub incoming webhook`
     - Fully supported
   * - GitLab
     - :ref:`projects/integrations/webhook:GitLab incoming webhook`
     - Fully supported
   * - Bitbucket
     - :ref:`projects/integrations/webhook:Bitbucket incoming webhook`
     - Fully supported
   * - Gitea (Forgejo, Codeberg)
     - :ref:`projects/integrations/webhook:GitHub incoming webhook`
     - Functional [1]_
   * - GitHub Enterprise
     - :ref:`projects/integrations/webhook:GitHub incoming webhook`
     - Functional [1]_
   * - Azure DevOps
     - :ref:`projects/integrations/webhook:Generic API incoming webhook`
     - Functional [1]_
   * - All other providers
     - :ref:`projects/integrations/webhook:Generic API incoming webhook`
     - Unknown

Manually configured integrations support triggering new builds and synchronizing versions,
but they **do not send a commit status** back to your provider and **do not support pull
request builds**.

.. [1] Integrations that are functional are known to work with manual
   configuration but are not officially supported or tested.

Configuring your provider
-------------------------

You need to configure your Git provider to send a webhook that alerts Read the Docs of changes.
Read the Docs will sync versions and build your documentation whenever a Git commit happens.

.. tabs::

   .. tab:: GitHub

      * Go to the :guilabel:`Settings` page for your **GitHub repository**
      * Click :guilabel:`Webhooks` > :guilabel:`Add webhook`
      * For **Payload URL**, use the URL of the integration on your **Read the Docs project**,
        found on the repository's :guilabel:`Admin` > :guilabel:`Integrations` page.
        You may need to prepend *https://* to the URL.
      * For **Content type**, both *application/json* and
        *application/x-www-form-urlencoded* work
      * Fill the **Secret** field with the value from the integration on Read the Docs
      * Select **Let me select individual events**,
        and mark **Branch or tag creation**, **Branch or tag deletion**, **Pull requests** and **Pushes** events
      * Ensure **Active** is enabled; it is by default
      * Finish by clicking **Add webhook**.  You may be prompted to enter your GitHub password to confirm your action.

      You can verify if the webhook is working at the bottom of the GitHub page under **Recent Deliveries**.
      If you see a Response 200, then the webhook is correctly configured.
      For a 403 error, it's likely that the Payload URL is incorrect.

   .. tab:: GitLab

      * Go to the :guilabel:`Settings` > :guilabel:`Webhooks` page for your GitLab repository
      * For **URL**, use the URL of the integration on **Read the Docs project**,
        found on the :guilabel:`Settings` > :guilabel:`Integrations`  page
      * Fill the **Secret token** field with the value from the integration on Read the Docs
      * Leave the default **Push events** selected,
        additionally mark **Tag push events** and **Merge request events**.
      * Finish by clicking **Add Webhook**

   .. tab:: Bitbucket

      * Go to the :guilabel:`Settings` > :guilabel:`Webhooks` > :guilabel:`Add webhook` page for your repository
      * For **URL**, use the URL of the integration on Read the Docs,
        found on the :guilabel:`Settings` > :guilabel:`Integrations`  page
      * Under **Triggers**, **Repository push** should be selected
      * Fill the **Secret** field with the value from the integration on Read the Docs
      * Finish by clicking **Save**

   .. tab:: Gitea

      * Go to the :guilabel:`Settings` > :guilabel:`Webhooks` page for your repository on your instance
      * Create a new webhook of type "Gitea"
      * For **URL**, use the URL of the integration on Read the Docs,
        found on the project's :guilabel:`Settings` > :guilabel:`Integrations` page
      * Leave the default **HTTP Method** as POST
      * For **Content type**, both *application/json* and
        *application/x-www-form-urlencoded* work
      * Fill the **Secret** field with the value from the integration on Read the Docs
      * Select **Choose events**,
        and mark **Branch or tag creation**, **Branch or tag deletion** and **Push** events
      * Ensure **Active** is enabled; it is by default
      * Finish by clicking **Add Webhook**
      * Test the webhook with :guilabel:`Delivery test`

   .. tab:: Others

      Other providers are supported through a generic webhook, see :doc:`../generic`.

.. seealso::

   :doc:`./troubleshooting-webhooks`
      How to discover and debug issues with a webhook integration.
