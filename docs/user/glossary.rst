Glossary
========

This page includes a number of terms that we use in our documentation,
so that you have a reference for how we're using them.

.. glossary::

   CI/CD
      CI/CD is a common way to write *Continuous Integration and Continuous Deployment*.
      In some scenarios, they exist as two separate platforms.
      Read the Docs is a combined CI/CD platform made for documentation.

   configuration file
      YAML configuration file (e.g. ``.readthedocs.yaml``) that configures the build process of your project on Read the Docs.

      .. seealso::

         :doc:`/config-file/index`
            Practical steps to add a configuration file to your documentation project.


   dashboard
      The "admin" site where Read the Docs projects are managed and configured.
      This varies for our two properties:

       * |com_brand|: https://app.readthedocs.com/dashboard/
       * |org_brand|: https://app.readthedocs.org/dashboard/

   default version
      Projects have a *default version*, usually the latest stable version of a project.
      The *default version* is the URL that is redirected to when a users loads the `/` URL for your project.

   diff
      A way to see the changes between two pieces of text,
      which shows the added and removed content with a green and red color respectively.

   discoverability
      A documentation page is said to be *discoverable* when a user that needs it can find it through various methods:
      Navigation, search, and links from other pages are the most typical ways of making content *discoverable*.

   Docs as Code
      A term used to describe the workflow of keeping documentation in a Git repository,
      along with source code.
      Popular in the open source software movement,
      and used by many technology companies.

   flyout menu
      Menu displayed on the documentation, readily accessible for readers, containing the list active versions, links to static downloads, and other useful links.
      Read more in our :doc:`/flyout-menu` page.

   GitOps
      Denotes the use of code maintained in Git to automate building, testing, and deployment of infrastructure.
      In terms of documentation,
      GitOps is applicable for Read the Docs,
      as the configuration for building documentation is stored in ``.readthedocs.yaml``,
      and rules for publication of documentation can be :doc:`automated </automation-rules>`.
      Similar to :term:`Docs as Code`.

   maintainer
      A *maintainer* is a special role that only exists on |org_brand|.
      The creator of a project on |org_brand| can invite other collaborators as *maintainers* with full ownership rights.

      The *maintainer* role does not exist on |com_brand|, which instead provides :doc:`/commercial/organizations`.

   pinning
      To *pin* a requirement means to explicitly specify which version should be used.
      *Pinning* software requirements is the most important technique to make a project :term:`reproducible`.

      When documentation builds,
      software dependencies are installed in their latest versions permitted by the pinning specification.
      Since software packages are frequently released,
      we are usually trying to avoid incompatibilities in a new release from suddenly breaking a documentation build.

      Examples of Python dependencies::

          # Exact pinning: Only allow Sphinx 5.3.0
          sphinx==5.3.0

          # Loose pinning: Lower and upper bounds result in the latest 5.3.x release
          sphinx>=5.3,<5.4

          # Very loose pinning: Lower and upper bounds result in the latest 5.x release
          sphinx>=5,<6

      Read the Docs recommends using **exact pinning**.

      See: :doc:`/guides/reproducible-builds`.

   pre-defined build jobs
      Commands executed by Read the Docs when performing the build process.
      They cannot be overwritten by the user.

   project home
      Page where you can access all the features of Read the Docs,
      from having an overview to browsing the latest builds or administering your project.

   project page
      Another name for :term:`project home`.

   reproducible
      A documentation project is said to be *reproducible* when its sources build correctly on Read the Docs over a period of many years.
      You can also think of being *reproducible* as being *robust* or *resillient*.

      Being "reproducible" is an important positive quality goal of documentation.

      When builds are not reproducible and break due to external factors,
      they need frequent troubleshooting and manual fixing.

      The most common external factor is that new versions of software dependencies are released.

      See: :doc:`/guides/reproducible-builds`.

   root URL
      Home URL of your documentation without the ``/<lang>`` and ``/<version>`` segments.
      For projects without custom domains, the one ending in ``.readthedocs.io/``
      (for example, ``https://docs.readthedocs.io`` as opposed to ``https://docs.readthedocs.io/en/latest``).

   slug
      A unique identifier for a project or version. This value comes from the
      project or version name, which is reduced to lowercase letters, numbers,
      and hyphens. You can retrieve your project or version slugs from
      :doc:`our API <api/v3>`.

   static website
      A static site or static website is a collection of HTML files, images, CSS and JavaScript that are served statically,
      as opposed to dynamic websites that generate a unique response for each request, using databases and user sessions.

      Static websites are highly portable, as they do not depend on the webserver.
      They can also be viewed offline.

      Documentation projects served on Read the Docs are *static websites*.

      Tools to manage and generate static websites are commonly known as *static site generators* and there is a big overlap with documentation tools.
      Some static site generators are also documentation tools,
      and some documentation tools are also used to generate normal websites.

      For instance, :doc:`Sphinx <sphinx:index>` is made for documentation but also used for blogging.

   subproject
      Project A can be configured such that when requesting a URL ``/projects/<subproject-slug>``,
      the root of project B is returned.
      In this case, *project B* is the subproject.
      Read more in :doc:`/subprojects`.

   user-defined build jobs
      Commands defined by the user that Read the Docs will execute when performing the build process.

   virtualenv
      The default way for Python projects to create an isolated environment. This ensures that a :doc:`reproducible set of dependencies </guides/reproducible-builds>` are installed so that you project builds the same way each time.

   webhook
      A webhook is a special URL that can be called from another service,
      usually with a secret token.
      It is commonly used to start a build or a deployment or to send a status update.

      There are two important types of webhooks for Read the Docs:

      * Git providers have webhooks which are special URLs that Read the Docs can call in order to notify about documentation builds.
      * Read the Docs has a unique webhook for each project that the Git provider calls when changes happen in Git.

      .. seealso::

         :doc:`/guides/setup/git-repo-manual`
            Manually configuration for Git repositories.

         :doc:`/build-notifications`
            Receive notifications when your documentation builds fail.
