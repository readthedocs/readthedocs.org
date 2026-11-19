Integrations
============

Project integrations are how Git hosting providers, like GitHub and GitLab,
interact directly with projects on Read the Docs.
They are responsible for repository configuration, synchronization,
and performing actions on your Read the Docs project.
Project can use more than one integration,
using any mix of `supported integration types <Integration types_>`_.

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
* :ref:`Synchronizing user permissions <sso_git_provider>` from your repository (|com_brand| only).

Configuration methods
---------------------

There are two ways that integrations can be configured for a project:

`Automatically configured`_
    All of the configuration steps required to clone and interact with the
    repository are handled by the integration.

`Manually configured`_
    No configuration steps are managed by the integration, project maintainers
    are responsible for setting up the project and repository.

Automatically configured
~~~~~~~~~~~~~~~~~~~~~~~~

For projects using a :term:`connected repository`,
integrations can be automatically configured for the project.
Projects *created* using a connected repository will start off with an integration already.
The integration will handle all of the configuration steps required for
the project and repository to interact.

This method requires a project maintainer (or organization admin on |com_brand|) to have a
:doc:`connected service account </account/user/connected-services>`,
which a project integration may use to interact with the project's repository.
Where a connected service account links a Read the Docs user to a remote service account,
project integrations link a *project to a repository*.

**This is the recommended configuration method for most projects.**
Projects using a manual repository URL must use
`a manually configured integration <Manually configured_>`_ instead.

.. seealso::

   :doc:`/intro/add-project`
      Add your project and create a project integration.

   :doc:`/guides/connecting-git-account`
      How to manage connected services for your user.

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
each supporting different services and APIs.
Integrations can all be created automatically or manually,
with the exception of our GitHub App integration.
The supported integration types are:

:doc:`./github-app`
   Our GitHub App integration provides granular permissions and several features not
   supported by other integrations or providers, like GitHub pull request commenting.
   This integration is the recommended type for repositories hosted on GitHub.
   These integrations are only ever automatically configured,
   it's not possible to create a GitHub App integration manually.

:ref:`projects/integrations/webhook:GitHub incoming webhook`
   Our legacy GitHub integration, best for projects not yet using our GitHub App integration
   or users using a GitHub OAuth :doc:`connected service account </account/user/connected-services>`.
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

Most project integrations should be created and used seamlessly,
without maintenance required after initial setup.
However, if your project is manually configured
or you encounter any problems with the integration or your repository,
the following guides will help explain how to manage project integrations.

:doc:`./guides/creating`
    How to create an integration
    and configure a repository to use the integration.

:doc:`./guides/creating-generic`
    How to create a generic API integration
    and configure a repository to use the integration.

:doc:`./guides/managing-github-app`
    How to manage a GitHub App integration,
    including how to accept permissions and install the application for your repository and organization.

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
    How to troubleshoot problems with :doc:`webhook integrations <./webhook>`.

:doc:`./guides/troubleshooting-github-app`
    How to troubleshoot problems with :doc:`GitHub App integrations <./github-app>`.

.. toctree::
   :glob:
   :hidden:

   Webhook integrations <./guides/troubleshooting-webhooks>
   GitHub App integrations <./guides/troubleshooting-github-app>
