Your documentation infrastructure layer
=======================================

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
   :caption: AI and agents

   /reference/llms-txt
   /reference/markdown-for-agents
   /reference/agent-skills
   /reference/main-content-detection

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
   :description lang=en: Automate building, versioning, and hosting of your technical documentation continuously on Read the Docs.

.. Adds a hidden link for the purpose of validating Read the Docs' Mastodon profile
.. raw:: html

   <a style="display: none;" rel="me" href="https://fosstodon.org/@readthedocs">Mastodon</a>

Connect your Git repository and treat docs like code.
Read the Docs builds, versions, and hosts your documentation automatically.

Get started
-----------

.. grid:: 1 1 3 3
    :gutter: 3

    .. grid-item-card:: Add your project
        :link: /intro/add-project
        :link-type: doc

        Already have documentation?
        Connect your repository and get your first build.

    .. grid-item-card:: Choose your tool
        :link: /intro/doctools
        :link-type: doc

        Quick starts for Sphinx, MkDocs, Docusaurus, and more.

    .. grid-item-card:: Follow the tutorial
        :link: /tutorial/index
        :link-type: doc

        Starting from nothing?
        Build and host a Sphinx project step by step.

Or browse :doc:`example projects </examples>` to see how other projects are configured.

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

AI and agents
-------------

Make your documentation easy for AI assistants and coding agents to use:

:doc:`/reference/llms-txt`
  Serve an ``llms.txt`` file that gives AI models a structured view of your documentation.

:doc:`/reference/markdown-for-agents`
  Serve Markdown instead of HTML to agents that ask for it, with no configuration.

:doc:`/reference/agent-skills`
  Give your coding agent skills for the Read the Docs API and configuration file.

:doc:`/reference/main-content-detection`
  How Read the Docs finds the main content of a page for search, Markdown, and other features.

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
