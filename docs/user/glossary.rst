Glossary
========

This page includes a number of terms that we use in our documentation,
so that you have a reference for how we're using them.

.. glossary::

   dashboard
      The "admin" site where Read the Docs projects are managed and configured.
      This varies for our two properties:

       * |com_brand|: https://readthedocs.com/dashboard/.
       * |org_brand|: https://readthedocs.org/dashboard/.

   default version
      Projects have a *default version*, usually the latest stable version of a project.
      The *default version* is the URL that is redirected to when a users loads the `/` URL for your project.

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

   pre-defined build jobs
      Commands executed by Read the Docs when performing the build process.
      They cannot be overwritten by the user.

   profile page
      Page where you can see the projects of a certain user.

   project home
      Page where you can access all the features of Read the Docs,
      from having an overview to browsing the latest builds or administering your project.

   project page
      Another name for :term:`project home`.

   slug
      A unique identifier for a project or version. This value comes from the
      project or version name, which is reduced to lowercase letters, numbers,
      and hyphens. You can retrieve your project or version slugs from
      :doc:`our API <api/v3>`.

   subproject
      Project A can be configured such that when requesting a URL ``/projects/<subproject-slug>``,
      the root of project B is returned.
      In this case, *project B* is the subproject.
      Read more in :doc:`/subprojects`.

   root URL
      Home URL of your documentation without the ``/<lang>`` and ``/<version>`` segments.
      For projects without custom domains, the one ending in ``.readthedocs.io/``
      (for example, ``https://docs.readthedocs.io`` as opposed to ``https://docs.readthedocs.io/en/latest``).

   user-defined build jobs
      Commands defined by the user that Read the Docs will execute when performing the build process.
