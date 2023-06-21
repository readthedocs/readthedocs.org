.. This page seeks to put out lots of pointers to other articles in the documentation
.. while giving an introduction that can be read consecutively.
.. TODO:
.. - Tiny screenshots possible? It would be nice if examples of features had little screenshots.

.. Inspiration for items to cover:
.. - Code: If you write docs as code, you want this
.. - When you should NOT choose a dedicated documentation CI/CD: You just need a README in your Git repo! You need WYSIWYG so badly that you're probably better off with Confluence, GitBook or Google Docs.
.. - A dedicated platform helps to solve tasks that you otherwise end up writing and maintaining your own scripts and CI tools for.
.. - Always evolving: Read the Docs develops new features on-demand. So you get a dedicated platform that's maintained and has new features added.
.. - Community: Related to the above, but perhaps worth mentioning that a lot of people are building tools and extensions that run on the platform etc.
.. - Reader features: Alternative name for "Batteries included" is "Reader features"
.. - Use-cases: The list would be really nice to wrap up with a set of use-cases. Software projects, onboarding docs, science, books etc.

.. TODO: This article is kind of a "long-read" intended to read and share with other decision-makers.
.. It's not far from a "white paper", although it lacks case studies.
.. One way to help the reader would perhaps be to add a little box
..    Reading time: 15 minutes
..    Content: An elaborated case for why Read the Docs as a dedicated platform makes sense.
..             If you are interested in understanding why to use Read the Docs for the first time, this is a great starting point.


Read the Docs: An all-in-one documentation solution
===================================================

This page covers the benefits of using an all-in-one documentation platform.
There are a number of approaches to writing and deploying documentation,
but using a platform built for this purpose provides you with a number of benefits that generic platforms do not.

The role of a *dedicated documentation platform* is to offer a compelling set of features that documentation projects and their organizations need.
This article gives a broad introduction to those features and their importance:

🧭️️️ :ref:`lifecycle`
    Documentation has a unique lifecycle, our platform handles a variety of challenges and complexities that documentation projects require, like versioning.

🛠️ :ref:`documentation_tools`
   Support for a variety of documentation tools allows you the flexibility to choose the best tool for your project.

🚢️️ :ref:`workflows`
    Our platform works like a :term:`CI/CD platform <CI/CD>`, publishing and versioning your documentation automatically.
    You save time not writing your own scripts and deployment workflows,
    and get a reliable and reproducible process.

🔋️ :ref:`batteries_included`
    Read the Docs continues to develop new projects and ideas,
    bringing additional powers to documentation projects that are hosted on the platform.

Using Read the Docs allows you to focus on other critical tasks,
such as choosing structuring and writing your documentation itself!

.. seealso::

    `Comparison with GitHub Pages <https://about.readthedocs.com/comparisons/github-pages/>`__
        On our website, we have a list of common tasks that teams have to solve themselves on a generic CI.

.. _lifecycle:

Features for the lifecycle of a documentation project
-----------------------------------------------------

Read the Docs is a platform with over a decade of experience in automating documentation tools.
The platform handles your current challenges or challenges that you face down the road.
The right features are available when you need them.

Some features respond to external factors,
while other features respond to the natural development of a documentation project.
The combined set of features make it possible to bootstrap a small documentation project and turn it into a mature enterprise product.

.. figure:: /img/documentation-lifecycle.svg
   :alt: A diagram of external effects to a documentation's lifecycle

   The number of effects on a lifecycle are many.
   Some are caused by external factors,
   changes to the product or project,
   changes in the team,
   vision etc.

Example: Automated versioning and redirects
    Once a documentation project is bootstrapped,
    the software product might change its version and remove or add features.
    Old versions of the product still need to be able to refer to their original documentation while new versions should not be unnecessarily complicated by documenting old features.

    As your documentation grows and pages are moved around, versioning and redirects become critical.

    :doc:`Versioning </versions>` is a core part of documentation projects on our platform.
    And on top of versioning support,
    Read the Docs offers a mature set of :doc:`user-defined redirects </user-defined-redirects>`.

Example: Analytics
    Documentation websites benefit from knowing which pages are popular and how people discover them through online search.

    This may not be an immediate requirement for a documentation project,
    but the need often arises.
    And why should every documentation project have to implement their own analytics solution?
    For this, you can use :doc:`/reference/analytics`.

Example: Cloud hosting (CDN)
    Read the Docs deploys and hosts your documentation.
    Part of this package is to host documentation projects with a CDN in front of them,
    so you never have to worry about incoming traffic.

    We also have intelligent caching,
    so you don't have to worry about when to invalidate your cloud cache when your project is updated.

    Read more in :doc:`/reference/cdn`.

.. seealso::

    :doc:`/reference/features`
        A practical way to understand Read the Docs is to look at our :doc:`list of features </reference/features>`.
        All these features ultimately sustain the lifecycle of a documentation project.


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
Some examples include:

* :doc:`Sphinx <sphinx:index>`
* `MkDocs <https://www.mkdocs.org/>`__ and `Material for MkDocs <https://squidfunk.github.io/mkdocs-material/>`__
* `Jupyter Book <https://jupyterbook.org>`__
* `Pelican <https://getpelican.com/>`__
* `Docusaurus <https://docusaurus.io/>`__
* `Docsy for Hugo <https://www.docsy.dev/>`__
* `Asciidoctor <https://asciidoctor.org/>`__
* ...and any other tool that will install and run in a Docker container.
* ...and plugins/extensions/themes for all of the above.

.. _workflows:

Move faster by integrating the building and deployment of documentation
-----------------------------------------------------------------------

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

    `Diátaxis Framework <https://diataxis.fr>`__
        Having an agile workflow enables your documentation project to *grow organically*.
        This is one of the core principles of the Diatáxis Methodology,
        which presents a universal structure and agile workflow methodology for documentation projects.


.. _batteries_included:

Better documentation reader experience
--------------------------------------

Read the Docs offers a number of features that are visible to readers of your documentation.
This gives you the ability to provide a nicer experience to your readers,
while also providing many benefits to the authors and maintainers.

Example: Integrated :doc:`server side search </server-side-search/index>`
    Many documentation tools include a small JavaScript-based search utilities.
    Some don't.
    In any case,
    Read the Docs parses and indexes your HTML and offers a search form and search result dialogue that fits in any documentation project.
    Search results can be delivered faster than JavaScript-based search tools and we also offer searches across multiple projects,
    which is great for organizations.

Example: :doc:`Flyout menu </flyout-menu>`
    By default,
    an MkDocs and Sphinx project hosted on Read the Docs will have a little :term:`flyout menu` at the bottom of the screen.
    The menu always contains the latest list of releases and alternative formats,
    as well as convenient links to edit the project on |git_providers_or|.

    .. note::

        As of April 2023, we are testing a new version of the :term:`flyout menu`,
        which integrates with any documentation project.
        Please contact :doc:`/support` for more information.

.. TODO: Split this into an include:: since we are repeating it

.. seealso::

    :doc:`/reference/features`
        A practical way to understand Read the Docs is to look at our :doc:`list of features </reference/features>`.
        All these features ultimately sustain the lifecycle of a documentation project.


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
