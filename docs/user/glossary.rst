Glossary
========

.. glossary::

   dashboard
      `Main page <https://readthedocs.org/dashboard>`_ where you can see all your projects with their build status
      and import a new project.

   flyout menu
      Menu displayed on the documentation, readily accessible for readers, containing the list active versions, links to static downloads, and other useful links.
      Read more in our :doc:`/flyout-menu` page.

   permalink
      A permalink or "permanent link" is a term commonly used in blogging and in media outlets.
      It's a URL that is intended to remain unchanged for many years into the future,
      yielding a hyperlink that is less susceptible to link rot.
      The term applies to documentation projects,
      but rather than being a technical feature,
      it's more about keeping a gentle and long-term management of the documentation structure.


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
      and hypens. You can retreive your project or version slugs from
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
