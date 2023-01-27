Glossary
========

.. glossary::

   dashboard
      `Main page <https://readthedocs.org/dashboard>`_ where you can see all your projects with their build status
      and import a new project.

   flyout menu
      Menu displayed on the documentation, readily accessible for readers, containing the list active versions, links to static downloads, and other useful links.
      Read more in our :doc:`/flyout-menu` page.

   GitOps
      A popular term,
      denoting the use of code, branches and tags maintained in Git in order to automate building, testing, and deployment.
      GitOps is often used for infrastructure such as maintaining the configuration code for infrastructure in Git.
      In terms of documentation,
      GitOps is applicable for Read the Docs,
      as the configuration for building documentation is stored in ``.readthedocs.yaml``,
      and rules for publication of documentation can be :doc:`automated </automation-rules>`.

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
