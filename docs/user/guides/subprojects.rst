How to manage subprojects
=========================

This guide shows you how to manage subprojects, 
which are a way to host multiple projects under a "main project".

.. seealso::

   :doc:`/subprojects`
      Read more about what the subproject feature can do and how it works.

Adding a subproject
-------------------

In the admin dashboard for your project, select :guilabel:`Subprojects` from the menu.
From this page you can add a subproject by typing in the project slug.

Immediately after adding the subproject, its default version will be visible from the link displayed in the list of subprojects.

.. note::

   * On |org_brand|, you need to be maintainer of a subproject in order to choose it from your main project.
   * On |com_brand|, you need to have admin access to the subproject in order to choose it from your main project.

Editing a subproject
--------------------

You can edit a subproject at any time by clicking :guilabel:`|:memo:|` in the list of subprojects.
On the following page, it's possible to both change the alias and source project.
Click :guilabel:`Update subproject` to save your changes.

The documentations served at``/projects/<subproject-alias>/`` will be updated immediately when you save your changes.


Deleting a subproject
---------------------

You can delete a subproject at any time by clicking :guilabel:`|:memo:|` in the list of subprojects.
On the edit page, click :guilabel:`Delete subproject`.

Your subproject will be removed immediately and will be served from it's own domain:

* Previously it was served at: `<source-project-domain>/projects/<subproject-alias>/`
* Now it will be served at `<subproject-domain>/`

**Deleting a subproject does not mean to completely remove that project**.
It only removes the reference from the main project.
