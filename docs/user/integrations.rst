..
   Some points we want to cover in this article:
   * Talk about the benefits of always up to date docs
   * Discuss versioning in here, since it relies directly on Git?
   * Have a small diagram that shows (You --push--> GitHub --webhook--> RTD --Build docs--> Deploy
       (Perhaps reuse this: https://about.readthedocs.com/images/homepage.png)


Connecting git repositories
===========================

Read the Docs is a *Continuous Documentation Deployment* platform for your software project.
Every time you change something in your documentation, Read the Docs will detect your change and build your documentation.
This happens using *webhooks*.

The Continuous Integration and Continuous Deployment features are configured with your repository provider,
such as GitHub, Bitbucket or GitLab,
and with each change to your repository, Read the Docs is notified by the webhook.

When we receive an integration notification, we determine if the change is related to an active version for your project.
If it is, a build is triggered for that version.

Continuous Deployment for Documentation
---------------------------------------

TBC



.. seealso::

    :doc:`/guides/git-integrations`
        Information on setting up your Git repository to make Read the Docs automatically build your documentation project.
