Read the Docs: your documentation infrastructure layer
======================================================

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting started

   Tutorial </tutorial/index>
   /intro/add-project
   /intro/doctools
   /examples

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Project setup and configuration

   /config-file/index
   /config-file/v2
   /addons
   /intro/accounts
   /automation-rules
   /guides/reproducible-builds

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Build process

   /builds
   /build-customization
   /guides/build/direct-upload
   /reference/git-integration
   /pull-requests
   /build-notifications
   /environment-variables
   /reference/environment-variables

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Hosting documentation

   /versions
   /subprojects
   /localization
   /versioning-schemes
   /custom-domains
   /url-path-prefixes
   /doc-notifications
   /canonical-urls
   /reference/cdn
   /reference/sitemaps
   /reference/404-not-found
   /reference/robots
   /reference/llms-txt
   /reference/markdown-for-agents

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reading documentation

   /offline-formats
   /visual-diff
   /link-previews
   /guides/embedding-content
   /server-side-search/index
   /server-side-search/syntax
   /flyout-menu

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Maintaining projects

   /user-defined-redirects
   /traffic-analytics
   /search-analytics
   /security-log
   /badges
   /explanation/documentation-structure
   /guides/best-practice/links
   /security-implications
   /reference/main-content-detection
   /reference/agent-skills
   /custom-script

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Business features

   /commercial/index
   /commercial/organizations
   /commercial/single-sign-on
   /commercial/sharing
   /commercial/subscriptions
   /commercial/privacy-level

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: How-to guides

   Project setup and configuration </guides/setup/index>
   Build process </guides/build/index>
   Upgrading and maintaining projects </guides/maintenance/index>
   Content, themes and SEO </guides/content/index>
   Security and access </guides/access/index>
   Account management </guides/management/index>
   Best practice </guides/best-practice/index>
   Troubleshooting problems </guides/troubleshooting/index>

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   /api/index
   /faq
   /changelog
   /about/index
   Developer Documentation <https://dev.readthedocs.io>
   Read the Docs website <https://about.readthedocs.com>

.. meta::
   :description lang=en: Connect your Git repository and treat docs like code. Read the Docs runs builds, previews, and authentication so you can focus on writing great docs.

.. Adds a hidden link for the purpose of validating Read the Docs' Mastodon profile
.. raw:: html

   <a style="display: none;" rel="me" href="https://fosstodon.org/@readthedocs">Mastodon</a>

Connect your Git repository and treat docs like code.
Read the Docs runs the builds, previews, and authentication,
so you ship documentation from the same pull requests as your code.

.. grid:: 2
    :gutter: 2

    .. grid-item-card:: Build on every push
        :link: /builds
        :link-type: doc

        A webhook from GitHub, GitLab, or Bitbucket triggers a build
        in an isolated environment defined in ``.readthedocs.yaml``.
        Pick the OS and Python or Node version, and run any build command.
        Sphinx, MkDocs, Docusaurus, or any tool that outputs HTML.

    .. grid-item-card:: Preview pull requests
        :link: /pull-requests
        :link-type: doc

        Each pull request builds to its own URL, posts a status check,
        and shows a visual diff of the rendered pages against production.

    .. grid-item-card:: Version from branches and tags
        :link: /versions
        :link-type: doc

        Each branch or tag becomes a version at its own URL,
        like ``/en/stable/`` or ``/en/v2.0/``.
        Automation rules activate versions as you tag releases,
        and translations ship the same way.

    .. grid-item-card:: Host with everything built in
        :link: /custom-domains
        :link-type: doc

        CDN hosting on your own domain with HTTPS,
        redirects, server-side search with an API,
        and traffic and search analytics.

    .. grid-item-card:: Serve docs to AI agents
        :link: /reference/llms-txt
        :link-type: doc

        ``llms.txt``, Markdown through ``Accept: text/markdown`` content negotiation,
        and agent skills make your docs usable from any AI tool.

    .. grid-item-card:: Control who reads your docs
        :link: /commercial/index
        :link-type: doc

        On |com_brand|, build from private repositories and gate access per project,
        with single sign-on through GitHub, GitLab, Bitbucket, Google Workspace, or SAML.

|org_brand| is free for open source projects and has hosted them since 2010.
|com_brand| adds private repositories, access control, and team management
for engineering and docs teams.
`Compare plans <https://about.readthedocs.com/pricing/>`_.

.. grid:: 2

    .. grid-item::

        .. button-link:: https://app.readthedocs.org/dashboard/import/
            :color: primary
            :expand:

            Add a project on Community

    .. grid-item::

        .. button-link:: https://app.readthedocs.com/dashboard/import/
            :color: info
            :expand:

            Add a project on Business

First time here?
----------------

We have a few places for you to get started:

.. descriptions here are active

:doc:`/tutorial/index`
  Follow the Read the Docs tutorial.

:doc:`/intro/doctools`
  Quick start for MkDocs and Docusaurus.

:doc:`/examples`
  Start your journey with an example project to learn how to use Read the Docs.

Project setup and configuration
-------------------------------

Start with the basics of setting up your project:

:doc:`/config-file/index`
  Learn how to configure your project with a ``.readthedocs.yaml`` file.

:doc:`/guides/reproducible-builds`
  Keep your builds working by making them reproducible.

Build process
-------------

Build your documentation with ease:

:doc:`/builds`
  Understand how documentation builds happen.

:doc:`/pull-requests`
  Preview your documentation on every pull request.

Hosting documentation
---------------------

Learn more about our hosting features:

:doc:`/versions`
  Give your readers multiple versions of your documentation.

:doc:`/subprojects`
  Host multiple projects under a single domain.

:doc:`/localization`
  Translate your documentation into multiple languages.

:doc:`/versioning-schemes`
  Learn about different URL versioning schemes.

:doc:`/custom-domains`
  Brand your documentation on your own domain.

Maintaining projects
--------------------

All the tools you need as your project matures:

:doc:`/user-defined-redirects`
  Redirect your old URLs to new ones.

:doc:`/traffic-analytics`
  Learn more about how users are interacting with your documentation.

:doc:`/security-log`
  Keep track of security events in your project.

Business features
-----------------

Our Business hosting has everything your business needs:

:doc:`/commercial/organizations`
  Manage permissions across multiple teams.

:doc:`/commercial/single-sign-on`
  Stay secure with single sign-on.

:doc:`/commercial/sharing`
  Share your private docs easily with contractors or customers.

How-to guides
-------------

Step-by-step guides for common tasks:

:doc:`/guides/pull-requests`
  Configure pull request builds for your project.

:doc:`/guides/build/direct-upload`
  Build your documentation in your own CI and upload it to Read the Docs with direct upload.

:doc:`All how-to guides </guides/index>`
  Browse all our how-to guides.

Reference
---------

More detailed information about Read the Docs:

:doc:`/api/index`
  Integrate Read the Docs into your other workflows.

:doc:`/changelog`
  See what's new in Read the Docs.

:doc:`/about/index`
  Learn more about Read the Docs and our company.
