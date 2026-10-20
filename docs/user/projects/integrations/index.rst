Integrations
============

Project integrations are how Git hosting providers, like GitHub and GitLab,
interact directly with projects on Read the Docs.
They are responsible for repository configuration, synchronization, and performing actions on your Read the Docs project.

How they work
-------------

Each integration configures a direct connection to your repository provider,
which allows your provider to notify your project of changes and events for the
project's repository, including:

* There is a new commit to the repository
* There is a new branch or tag created on the repository
* A pull request is created or updated

If an integration is notified of any of these events,
the integration can perform actions such as:

* :doc:`Building </builds>` the latest commit.
* Synchronizing your :doc:`versions </versions>` from the latest branch and tag data in Git.
* Creating a :doc:`pull request build </pull-requests>`.
* Running your :doc:`automation rules </automation-rules>`.
* :ref:`Synchronizing user permissions <sso_git_provider>` from your repository (|com_brand| only)

Configuration methods
---------------------

There are two ways that integrations can be configured for a project:

`Automatically configured`_
    The repository and project are automatically configured, no manual set up is
    required.

`Manually configured`_
    All configuration of the project and repository will be managed by project
    maintainers

Automatically configured
~~~~~~~~~~~~~~~~~~~~~~~~

For projects using a :term:`connected repository` with a supported Git provider,
integrations can be automatically configured for the project.

This will set up the provider repository with everything that is needed and **no
further configuration steps will be required**. This is the recommended
configuration method for most projects.

This method requires a maintainer of the project *to have a connected service
account with the repository provider* so that the project can be configured with
a connected repository.

Projects using a manual repository URL must use
`a manually configured integration <Manually configured>`_ instead.

.. seealso::

   :doc:`/intro/add-project`
      Add your project and create its Git integration.

   :doc:`/guides/connecting-git-account`
      Create or remove a connected service, which is what lets Read the Docs
      configure new Git integrations for you.

Manually configured
~~~~~~~~~~~~~~~~~~~

For projects using an unsupported Git provider,
or using a manually configured repository URL, 
integrations will need to be manually configured and managed.
An integration created manually *will not* configure the provider repository,
**several setup steps are required on the provider to use the integration**.

Integration types
-----------------

.. These will directly reference the names used in our UI for the Project
   integration types. They are a bit wordy but it's at least accurate and
   explicit for now.

There are multiple integration types available for projects,
each supporting different services and APIs:

:doc:`./github-app`
   Our GitHub App integration provides granular permissions and several features not
   supported by other integrations or providers.
   This integration is the recommended type for repositories hosted on GitHub.

:ref:`projects/integrations/webhook:GitHub incoming webhook`
   Our legacy GitHub integration, best for projects not yet using our GitHub App integration.
   Several other providers use an identical API and can reuse this integration.

:ref:`projects/integrations/webhook:GitLab incoming webhook`
   Our primary integration for GitLab.

:ref:`projects/integrations/webhook:Bitbucket incoming webhook`
   Our primary integration for Bitbucket.

:ref:`projects/integrations/webhook:Generic API incoming webhook`
   For providers that do not have a supported integration type.
   This integration consumes a generic and configurable API request,
   but is only useful for triggering project builds.

.. toctree::
   :hidden:

   ./github-app
   ./webhook

Using integrations
------------------

.. TODO tune this copy, it's sloppy.

To start using an integraiton, you may only need to create a project.
However if you need to configure an integration manually at all,
the following guides will help you understand how to manage your project's
integration.

:doc:`./guides/creating`
    How to create an integration and configure a repository to use the
    integration.

:doc:`./guides/creating-generic`
    How to create a generic API integration and configure a repository to use
    the integration.

:doc:`./guides/managing-github-app`
    How to manage a GitHub App integration, including how to accept permisions
    and install the application for your repository and organizaiton.

.. toctree::
   :glob:
   :hidden:

   ./guides/creating
   ./guides/creating-generic
   ./guides/managing*

Troubleshooting
---------------

If you run into any trouble or errors with your integration or project,
follow some of the troubleshooting steps for your integration:

:doc:`./guides/troubleshooting-webhooks`
    Troubleshooting problems with any of the :doc:`./webhook`,

:doc:`./guides/troubleshooting-github-app`
    Troubleshooting problems with :doc:`./github-app` integrations.

.. toctree::
   :glob:
   :hidden:

   Webhook integrations <./guides/troubleshooting-webhooks>
   GitHub App integrations <./guides/troubleshooting-github-app>
