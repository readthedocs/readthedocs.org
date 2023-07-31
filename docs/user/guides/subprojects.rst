How to manage subprojects
=========================

This guide shows you how to manage subprojects,
which is a way to host multiple projects under a "main project".

.. seealso::

   :doc:`/subprojects`
      Read more about what the subproject feature can do and how it works.

Adding a subproject
-------------------

In the admin dashboard for your project, select :guilabel:`Subprojects` from the left menu.
From this page you can add a subproject by choosing a project from the :guilabel:`Subproject` dropdown
and typing an alias in the :guilabel:`Alias` field.

Immediately after adding the subproject, it will be hosted at the URL displayed in the updated list of subprojects.

.. image:: /img/screenshot_subprojects_list.png
    :alt: Screenshot of a subproject immediately visible in the list after creation


.. note::

   |org_brand|
      You need to be *maintainer* of a subproject in order to choose it from your main project.

   |com_brand|
      You need to have *admin access* to the subproject in order to choose it from your main project.


Editing a subproject
--------------------

You can edit a subproject at any time by clicking :guilabel:`📝️` in the list of subprojects.
On the following page, it's possible to both change the subproject and its alias
using the :guilabel:`Subproject` dropdown and the :guilabel:`Alias` field.
Click :guilabel:`Update subproject` to save your changes.

The documentations served at ``/projects/<subproject-alias>/`` will be updated immediately when you save your changes.


Deleting a subproject
---------------------

You can delete a subproject at any time by clicking :guilabel:`📝️` in the list of subprojects.
On the edit page, click :guilabel:`Delete subproject`.

Your subproject will be removed immediately and will be served from it's own domain:

* Previously it was served at: `<main-project-domain>/projects/<subproject-alias>/`
* Now it will be served at `<subproject-domain>/`

**Deleting a subproject only removes the reference from the main project.**
It does not completely remove that project.
