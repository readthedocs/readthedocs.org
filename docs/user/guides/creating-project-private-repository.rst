Creating a project from a private repository
============================================

.. include:: /shared/admonition-rtd-business.rst

On |com_brand|, projects can be connected to both private and public repositories.
There are two methods you can use to create a project from a private repository:

`Automatically create a project from a connected repository`_
    If you have a |git_providers_or| service connected to your account,
    projects can be created automatically from a connected private repository.
    We will handle the configuration of your repository to allow cloning
    and pushing status updates to trigger new builds for your project.

    We recommend this method for most projects.

`Manually create a project from a repository`_
    If your Git provider is unsupported or if your Read the Docs account is not connected to your provider,
    you can still manually create a project against a private repository.
    You will have to manually configure your Git provider and repository after project creation.

Automatically create a project from a connected repository
----------------------------------------------------------

.. Putting this section up front to provide a clear focus on automatic project
   connection before pointing users at manual connection

If your Read the Docs account has a connected |git_providers_or| account,
you should be able to automatically create a project from your repository.
Your account will need sufficient permissions to the repository to automatically configure it.

We recommend most users follow our :doc:`directions on automatically creating projects </intro/add-project>` from a connected repository.

Manually create a project from a repository
-------------------------------------------

In the case that automatic project creation isn't supported or doesn't work for your repository,
projects may be able to be manually created and configured.
You can still clone the repository with SSH but you will have to manually
configure the repository SSH keys and webhooks.

.. seealso::

    :doc:`/guides/setup/git-repo-manual`
        An overview of all of the steps required to manually add a project.
        This guide is useful for both projects using public and private repositories.

Creating a project manually
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /img/screenshots/business-project-manual-team-select.png
  :scale: 40%
  :align: right
  :alt: Select an organization team to create the project in.

#. Select :guilabel:`Add project` from the main dashboard.
#. Select :guilabel:`Configure manually` and then :guilabel:`Continue`.
#. Select the organization team you'd like to create the project for.
   You must be on a team with ``admin`` permission to do this.

In the next form page you will manually configure your project's repository details.

.. figure:: /img/screenshots/business-project-manual-form.png
  :scale: 40%
  :align: right
  :alt: Specify your project and repository configuration.

4. In the :guilabel:`Repository URL` field, provide the repository's SSH or Git URL.
   This URL usually starts with ``git@...``, for example ``git@github.com:readthedocs/readthedocs.org.git``.
#. In the :guilabel:`Default branch` field, provide the name of the default remote branch.
   This is usually ``main`` or ``master``.
#. The project's first build should fail to clone your repository.
   This is expected, your repository is not configured to allow access yet.

Configuring your repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each project is configured with an SSH key pair consisting of a public and private key.
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

Configuring repository webhooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your repository will also need to be configured to push updates via webhooks to Read the Docs on repository events.
Webhook updates are used to automatically trigger new builds for your project and synchronize your repository's branches and tags.

This step is the same for public repositories,
follow the directions for :doc:`manually configuring a Git repository integration </guides/setup/git-repo-manual>`.
