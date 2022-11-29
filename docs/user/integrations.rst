Connecting git repositories
===========================

Read the Docs is a *Continuous Documentation Deployment* platform for your software project.
Every time you change something in your documentation, Read the Docs will detect your change and build your documentation.
This happens using *webhooks*.

Integrations are configured with your repository provider,
such as GitHub, Bitbucket or GitLab,
and with each change to your repository, Read the Docs is notified by the webhook.

When we receive an integration notification, we determine if the change is related to an active version for your project.
If it is, a build is triggered for that version.


.. seealso::

    :doc:`/guides/git-integrations`
        Information on setting up your Git repository to make Read the Docs automatically build your documentation project.
