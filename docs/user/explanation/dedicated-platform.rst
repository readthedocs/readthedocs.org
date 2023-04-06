.. This page seeks to put out lots of pointers to other articles in the documentation
.. while giving an introduction that can be read consecutively.
.. TODO:
.. - Links and references!
.. - Diagram in life-cycle section
..
.. There are other reasons that we could cover:
.. - Code: If you write docs as code, you want this
.. - When you should NOT choose a dedicated documentation CI/CD: You just need a README in your Git repo! You need WYSIWYG so badly that you're probably better off with Confluence, GitBook or Google Docs.
.. - A dedicated platform helps to solve tasks that you otherwise end up writing and maintaining your own scripts and CI tools for.
.. - Always evolving: Read the Docs develops new features on-demand. So you get a dedicated platform that's maintained and has new features added.
.. - Community: Related to the above, but perhaps worth mentioning that a lot of people are building tools and extensions that run on the platform etc.
.. - Batteries included / integrations: Flyout menu, search, SSL certificate

Choosing a dedicated documentation platform
===========================================

This is an introduction to the most common benefits of choosing a dedicated platform for building and publishing documentation projects.
In other words,
we dive into some of the reasons behind Read the Docs' existence and vision.

Let us start with a high-level overview:

🧭️️️ :ref:`lifecycle`
    A dedicated documentation platform has all the features to handle a variety of challenges and complexities that documentation projects meet during their lifecycle.

🛠️ :ref:`documentation_tools`
    By choosing a tool-agnostic dedicated platform,
    you can use the documentation tools that you want.

🚢️️ :ref:`workflows`
    A dedicated CI/CD platform publishes your documentation automatically and versions it so you can focus on applying your own workflow and keep the documentation aligned with your product.

.. The following sections are about using a dedicated platform as a first-choice in order to free up space for other tasks.
.. These paragraphs can benefit from being shortened and organized, but they are intended as the summary of the introduction.

Using Read the Docs
allows you to focus on other critical tasks,
such as choosing documentation tools, structuring your documentation and having the perfect workflow.
Not to mention *writing the documentation itself*!

If we observe a documentation project simply from the outside,
we might only see the documentation as one or more deliverables, such as:
A website, a PDF document, or an API documentation.
But in order to get there,
a dedicated documentation platform is a reliable first choice.

A dedicated platform helps to solve tasks that you otherwise end up writing and maintaining your own scripts and CI tools for.

.. seealso::

    `Comparison with GitHub Pages <https://about.readthedocs.com/comparisons/github-pages/>`__
        On our website, we have a list of common tasks that developers and DevOps teams have to solve themselves on a generic CI.

Simply put, the role of a *dedicated documentation platform* is to offer a compelling set of features that documentation projects and their organizations or communities need.

Read the Docs does exactly this in two versions:
|org_brand| and |com_brand|. :ref:`Read more about their differences <com_org_differences>`.

.. Keeping this list commented out for now.
.. The seealso about GitHub pages is better, since this is largely marketing content.
.. It's also nice to not break up the reading flow with a long list. Should delete...
.. * ✅️ Publishing a static website
.. * ✅️ Adding a fast cache layer for the website
.. * ✅️ Maintaining SSL
.. * ✅️ Notifications when things go wrong
.. * ✅️ Versioning
.. * ✅️ Letting users switch between versions
.. * ✅️ Offering additional formats (PDFs, ebooks)
.. * ✅️ Custom 404 pages
.. * ✅️ Building a fast search index
.. * ✅️ Having APIs to access documentation contents and integrate them elsewhere
.. * ✅️ Redirecting users that visit old URLs
.. * ✅️ Inviting a dedicated documentation team to manage all this
.. * ✅️ Manage access to private documentation projects
.. * ...this list is longer, and it is incidentally also the list of features that were built for Read the Docs.

.. _lifecycle:

Features for the lifecycle of a documentation project
-----------------------------------------------------

Read the Docs is a platform with over a decade of experience in automating documentation tools.
The platform handles your current challenges or challenges that you face down the road.
The right features are available when you need them.

Example: Automated versioning and redirects
    Once a documentation project is bootstrapped,
    the software product might change its version and remove or add features.
    Old versions of the product still need to be able to refer to their original documentation while new versions should not be unnecessarily complicated by documenting old features.

    That is why Read the Docs supports versioning out-of-the-box and also gives you a mature set of options for creating :doc:`user-defined redirects </user-defined-redirects>`.

    As your documentation grows and pages are moved around, versioning and redirects become critical.

Example: Analytics
    Documentation websites benefit from knowing which pages are popular and how people discover them through online search.

    This may not be an immediate requirement for a documentation project,
    but the need often arises.
    And why should every documentation project have to implement their own analytics solution?
    For this, you can use :doc:`/reference/analytics`.

.. seealso::

    :doc:`/reference/features`
        A practical way to understand Read the Docs is to look at our :doc:`list of features </reference/features>`.
        All these features ultimately sustain the life-cycle of a documentation project.

.. insert life-cycle diagram.
.. new product + documentation project => new documentation pages => more product versions => more readers => more reader inputs => breaking changes => legacy product versions

.. _documentation_tools:

Freedom to choose documentation tools
-------------------------------------

One of the big choices facing new documentation project is to choose between the many documentation tools that exist.
Read the Docs was originally built for Sphinx,
but has since then evolved into a generic documentation building platform.

In the :doc:`build process </builds>`,
your documentation tool is called according to your own configuration and Read the Docs will then gather, version and publish files written by the documentation tool.
Whatever documentation tool you choose to build with,
your static website and additional :doc:`offline formats </downloadable-documentation>` can be versioned and published at your project's :doc:`domain </custom-domains>`

A documentation tool simply needs to be able to run on Linux inside a Docker container.
Most documentation frameworks will do this.
Some popular choices include:

.. TODO: expand the list and add links

* Sphinx
* MkDocs
* Jupyter Book
* ...and any other tool that will install and run in a Docker container.
* ...and plugins/extensions for all of the above!

.. _workflows:

Agile workflows with Continuous Integration and Deployment (CI/CD)
------------------------------------------------------------------

Automating your `build and deploy process </builds>`,
enables documentation writers to suggest changes, share previews, receive feedback and implement feedback quickly and iteratively.
Making your documentation project's workflow *agile* is supported by Read the Docs through a number of features.
Here are some examples:

.. these examples need more love. They could be more focused on practical tasks, rather than just the abstract topic.

Example: Automatic Git integration
    Many software projects already have a Git workflow,
    while many other types of projects have recently discovered the benefits of using Git.
    A dedicated documentation CI/CD will hook into your Git repository and be notified of changes so it can build and publish your documentation.
    This includes a number of additional options,
    such as support for private repositories,
    storing Read the Docs configuration in the Git repository (configuration as code)
    and managing access through GitHub SSO.

Example: Automatic previews
    When someone opens a *pull request*,
    Read the Docs will automatically build and display these changes,
    allowing your workflow to continue undisturbed.
    No need to email screenshots or attachments.
    No need to upload a temporary version somewhere.

Example: Automatic deploys with version tagging
    Read the Docs enables you to only have to do things once.
    You can *tag* your new version in Git and then have Read the Docs automatically see your change and publish a new version,
    keeping old versions active.

.. seealso::

    :doc:`/explanation/continuous-documentation`
        A more technical introduction to CI/CD for documentation projects.

    :ref:`Diátaxis methodology <diataxis>`
        Having an agile workflow enables your documentation project to *grow organically*.
        This is one of the core principles of the Diatáxis Methodology,
        which presents a universal structure and agile workflow methodology for documentation projects.

.. Types of documentation projects
.. -------------------------------

.. Software projects
.. ~~~~~~~~~~~~~~~~~

.. Scientific writing and academic projects
.. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _com_org_differences:

Differences between Community and Business
------------------------------------------

While many of our features are available on both of these platforms, there
are some key differences between our two platforms.

.. seealso::

   `Our website: Comparison of Community and all subscription plans <https://about.readthedocs.org/pricing/>`__
      Refer to the complete table of features included in all of the Read the Docs solutions available.

|org_brand|
~~~~~~~~~~~

|org_brand| is exclusively for free and open source software, content and projects.
We support open source communities by providing free documentation building and hosting
services, for projects of all sizes.

Important points:

* Open source project hosting is always free
* All documentation sites include advertising
* Only supports public VCS repositories
* All documentation is publicly accessible to the world
* Less build time and fewer build resources (memory & CPU)
* Email support included only for issues with our platform
* Documentation is organized by projects

You can sign up for an account at https://readthedocs.org.

|com_brand|
~~~~~~~~~~~

|com_brand| is meant for companies and users who have more complex requirements
for their documentation project. This can include commercial projects with
private source code, projects that can only be viewed with authentication, and
even large scale projects that are publicly available.

Important points:

* Hosting plans require a paid subscription plan
* There is no advertising on documentation sites
* Allows importing private and public repositories from VCS
* Supports private versions that require authentication to view
* Supports team authentication, including SSO with Google, GitHub, GitLab, and Bitbucket
* More build time and more build resources (memory & CPU)
* Includes 24x5 email support, with 24x7 SLA support available
* Documentation is organized by organization, giving more control over permissions

You can sign up for an account at https://readthedocs.com.

Questions?
~~~~~~~~~~

If you have a question about which platform would be best,
email us at support@readthedocs.org.
