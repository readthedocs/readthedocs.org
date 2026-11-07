Creating a project from a private repository
============================================

.. include:: /shared/admonition-rtd-business.rst

.. TODO roll most of this page into a single creating a project guide. There
   should be a guide for creating a project from a public repository too, but no
   need to keep these separate.

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

Configuring an integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, you will need to :doc:`create an integration </projects/integrations/guides/creating>`
in order to configure your repository and project to work together.
This will create the repository webhook and SSH keys needed to clone the repository.

.. seealso::
   :doc:`/projects/integrations/guides/creating`
      All of the steps needed to connect your project to a repository and start building.
