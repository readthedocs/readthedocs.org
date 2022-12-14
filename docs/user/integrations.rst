..
   Some points we want to cover in this article:
   * Talk about the benefits of always up to date docs
   * Discuss versioning in here, since it relies directly on Git?
   * Have a small diagram that shows (You --push--> GitHub --webhook--> RTD --Build docs--> Deploy
       (Perhaps reuse this: https://about.readthedocs.com/images/homepage.png)


Building documentation on every git commit
==========================================

Read the Docs is a *Continuous Documentation Deployment* platform for your software project.
Every time you change something in your documentation, Read the Docs will detect your change and build your documentation.
This happens using *webhooks*.

The Continuous Integration and Continuous Deployment (CI/CD) features are configured with your repository provider,
such as GitHub, Bitbucket or GitLab,
and with each change committed to your repository, Read the Docs is notified by the webhook.

When we receive an integration notification, we determine if the change is related to an active version for your project.
If it is, a build is triggered for that version.

Continuous Documentation for software projects
----------------------------------------------

Documentation fits into any CI/CD pipeline through the idea and objectives of *Documentation as Code*.
A straight-forward method to achieve this is by maintaining documentation alongside the source code,
meaning that the documentation's life cycle is contained within the same git repository as the source code.

When changes happen to the source code, changes should also happen to the documentation.
By managing these changes in the same life cycle,
you can benefit from **documentation and source code being part of the same code review process**.

Having an automated and short feedback loop for your documentation allows you to
keep it updated with minimal effort.
This allows more iteration on documentation,
and increases overall value from the documentation you write.

Continuous Documentation for all projects
-----------------------------------------

All categories of documentation benefit from being *continuously* built and published through Read the Docs.

If you are managing your documentation in git,
you will be able to preview changes and see accepted changes published immediately using :doc:`/pull-requests`.

Automated versioning
--------------------

With Read the Docs' automated CI/CD pipeline, you will be able to fully align your project's **release cycle** with your documentation.
For instance, a new version of a software project can build and publish a new version of its documentation.

Read the Docs is notified of all changes to your git branches and git tags.
When you release a **new version** for your project,
you are likely also adding a version tag to your git repository.

Read the Docs is notified of changes to git tags and branches.
These events can be configured to build and publish your documentation when new tags or branches are added in your repository.
If you use a versioning schema, you can choose or define the schema and automate this process.

Whether you choose to handle versioning automatically or with manual control is up to you.

Read the Docs will store your version history and make it possible for users to visit archived versions of your documentation.
Your version setup is ultimately captured by the :term:`flyout menu`.


.. seealso::

    :doc:`/guides/git-integrations`
        Information on setting up your Git repository to make Read the Docs automatically build your documentation project.
    :doc:`/automation-rules`
        Information on setting up your Git repository to make Read the Docs automatically build your documentation project.
    :doc:`/flyout-menu`
        Discover the functionality of the Flyout menu and the ways that it can be customized.
