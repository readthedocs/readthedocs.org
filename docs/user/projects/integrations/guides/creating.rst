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

.. _integration-create-automatic:

Automatically configured integration
------------------------------------

Integrations that are automatically configured do not require any configuration
steps from project maintainers. Once a repository is connected to your project,
an integration will be created and the repository will be automatically
configured to use the integration and allow Read the Docs to clone the repository.

This will require that a project maintain has a connected service account for
the repository's provider.

.. TODO pointers to next steps. Link to connected repository page when it exists

.. _integration-create-manual:

Manually configured integration
-------------------------------

For some cases, projects will not be able to use automatically configured
integrations. If your repository's provider is not supported or you do not have
a connected service account for your provider, your project will have to use a
manually configured integration instead.

There will be several set up steps required for your provider,
which are normally managed by automatically configured integrations:

- Configuring a webhook on your provider for your repository,
  pointing to the integration that you will create
- Private repositories will also need to be configured with an SSH key or deploy key in order to allow cloning.
  (|com_brand| only).

.. warning::
   Manual configuration is only recommended for advanced users.
   Project maintainers are responsible for all project and repository configuration.
   We recommend most projects use a connected repository and automatically
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

Configuring the repository webhook
----------------------------------

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

      Other providers are supported through a :doc:`generic webhook </projects/integrations/guides/creating-generic>`.


Configuring an SSH key
----------------------

.. note::
   Private repositories are only supported on |com_brand|.
   You can skip this step if your are using a public repository
   or your project is hosted on |org_brand|.

Each project using a private repository is configured with an SSH key pair consisting of a public and private key.
Your repository will need to be configured with the public SSH key
in order to allow builds to clone your repository.

.. figure:: /img/screenshots/business-project-ssh-key.png
   :scale: 40%
   :align: right
   :alt: Project SSH key details.

#. Go to the :menuselection:`Settings --> SSH keys` page for your project.
#. Click on the fingerprint of the SSH key.
#. Copy the text from the :guilabel:`Public SSH key` field
#. Next, configure your repository with this key,
   we've provided instructions for common Git providers:

.. tabs::

   .. tab:: GitHub

      For GitHub, you can use
      `deploy keys with read only access <https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys>`__.

      #. Go to your project on GitHub
      #. Click on :guilabel:`Settings`
      #. Click on :guilabel:`Deploy Keys`
      #. Click on :guilabel:`Add deploy key`
      #. Put a descriptive title and paste the public key you copied above.
      #. Click on :guilabel:`Add key`

   .. tab:: GitLab

      For GitLab, you can use `deploy keys with read only access <https://docs.gitlab.com/ee/user/project/deploy_keys/index.html>`__.

      #. Go to your project on GitLab
      #. Click on :guilabel:`Settings`
      #. Click on :guilabel:`Repository`
      #. Expand the :guilabel:`Deploy Keys` section
      #. Put a descriptive title and paste the public key you copied above.
      #. Click on :guilabel:`Add key`

   .. tab:: Bitbucket

      For Bitbucket, you can use `access keys with read only access <https://confluence.atlassian.com/bitbucket/access-keys-294486051.html>`__.

      #. Go your project on Bitbucket
      #. Click on :guilabel:`Repository Settings`
      #. Click on :guilabel:`Access keys`
      #. Click on :guilabel:`Add key`
      #. Put a descriptive label and paste the public key you copied above.
      #. Click on :guilabel:`Add SSH key`

   .. tab:: Azure DevOps

      For Azure DevOps, you can use `SSH key authentication <https://docs.microsoft.com/en-us/azure/devops/repos/git/use-ssh-keys-to-authenticate?view=azure-devops>`__.

      #. Go your Azure DevOps page
      #. Click on :guilabel:`User settings`
      #. Click on :guilabel:`SSH public keys`
      #. Click on :guilabel:`New key`
      #. Put a descriptive name and paste the public key you copied above.
      #. Click on :guilabel:`Add`

   .. tab:: Others

      If you are using a provider not listed here,
      you should still be able to configure your repository with your project's SSH key.
      Refer to your provider's documentation for managing SSH keys on private repositories.

.. seealso::

   :doc:`./troubleshooting-webhooks`
      How to discover and debug issues with a webhook integration.
