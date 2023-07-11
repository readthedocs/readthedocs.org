..
   Some points we want to cover in this article:
   * Talk about the benefits of always up to date docs
   * Discuss versioning in here, since it relies directly on Git?
   * Have a small diagram that shows (You --push--> GitHub --webhook--> RTD --Build docs--> Deploy
       (Perhaps reuse this: https://about.readthedocs.com/images/homepage.png)



Continuous Documentation Deployment
===================================

Read the Docs is a *Continuous Documentation Deployment* platform for your software project.
Every time you change something in your documentation, Read the Docs will detect your change and build your documentation.

The Continuous Integration and Continuous Deployment (CI/CD) features are configured with your repository provider,
such as GitHub, Bitbucket or GitLab.
With each change committed to your repository, we are notified by the configured *webhook*.

When we receive a *webhook* notification, we match it to a project's *Integration*.
When a webhook is received, the matching project will then:

* :doc:`Build </builds>` the latest commit.
* Synchronize your versions based on the latest tag and branch data in Git.
* Run your :doc:`automation rules</automation-rules>`.
* Auto-cancel any currently running builds of the same version.
* Add a log entry to the integration's :guilabel:`Recent Activity`.

Continuous Documentation for software projects
----------------------------------------------

Documentation fits into any CI/CD pipeline by following a process known as *Documentation as Code (Docs as code)*.
The primary method of doing this is by maintaining documentation alongside the source code,
meaning that the documentation's life cycle is the same as your software project.
By managing these changes in the same life cycle,
you can benefit from **documentation and source code being part of the same code review process**.

Having an automated and short feedback loop for your documentation allows you to
keep it updated with minimal effort.
This allows more iteration on documentation,
and increases overall value from the documentation you write.

As part of this quick feedback loop,
You can preview documentation changes immediately using :doc:`pull request previews </pull-requests>`.

Automated versioning
--------------------

With Read the Docs' automated CI/CD pipeline, you will be able to fully align your project's **release cycle** with your documentation.
For instance, a new version of a software project can build and publish a :doc:`new documentation version </versions>`.

When you release a new version for your project,
you are likely also adding a version tag to your Git repository.
These Git events can be configured to build and publish your documentation automatically with :doc:`/automation-rules`.
If you use a versioning schema, you can configure it as part of the automation process.

Whether you choose to handle versioning automatically or with manual control is up to you.

Read the Docs will store your version history and make it possible for users to visit archived versions of your documentation.
Your version setup is ultimately captured by the :term:`flyout menu`.


.. seealso::

    :doc:`/guides/setup/git-repo-manual`
        Information on setting up your Git repository to make Read the Docs automatically build your documentation project.
    :doc:`/automation-rules`
        Information on setting up your Git repository to make Read the Docs automatically build your documentation project.
    :doc:`/flyout-menu`
        Discover the functionality of the Flyout menu and the ways that it can be customized.
