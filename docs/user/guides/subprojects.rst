How To Add a Subproject
=======================

This guide shows you how to add a subproject to your main project.

.. seealso::

   :doc:`/subprojects`
      Read more about what the subproject feature can do and how it works.

Adding a subproject
-------------------

In the admin dashboard for your project, select :guilabel:`Subprojects` from the menu.
From this page you can add a subproject by typing in the project slug.

.. note::

   * On |org_brand|, you need to be maintainer of a subproject in order to choose it from your main project.
   * On |com_brand|, you need to have admin access to the subproject in order to choose it from your main project.

Subproject aliases
~~~~~~~~~~~~~~~~~~

You can choose an alias for the subproject when it is created.
This allows you to override the URL that is used to access it,
giving more control over how you want to structure your projects.

You can set your subproject's project name and :term:`slug` however you want,
but we suggest prefixing it with the name of the main project.

Typically, a subproject is created with a ``<mainproject>-`` prefix,
for instance if the main project is called ``foo`` and the subproject is called ``bar``,
then the subproject's Read the Docs project name will be ``foo-bar``.
When adding the subproject,
the alias is set to ``bar`` and the project's URL becomes
``foo.readthedocs.io/projects/bar``.
