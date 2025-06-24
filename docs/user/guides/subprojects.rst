Managing subprojects
====================

Subprojects can be used to nest projects together under a single parent project,
which is most commonly used to share a single custom domain across multiple projects.

.. seealso::

   :doc:`/subprojects`
      Learn what the subproject feature can do, how it works,
      and how to use custom domains and subproject aliases.

Adding a subproject
-------------------

The following steps can be used to connect two existing projects together:

* Go to :menuselection:`Settings --> Subprojects` for the project that will act
  as your **parent project**.
* Click :guilabel:`Add subproject`

* Choose a project to connect as a subproject using the :guilabel:`Subproject` dropdown

.. note::

   For users of |org_brand|
      You need to be *maintainer* of a subproject in order to choose it from your main project.

   For users of |com_brand|
      You need to have *admin access* to the subproject in order to choose it from your main project.

.. figure:: /img/screenshots/community-project-subproject-create.png
    :align: center
    :alt: Project subproject creation

    Project subproject creation

* If you would like the subproject to use a different name in the URL structure
  of your built documentation, you can alter that subproject :guilabel:`Alias`
  field -- otherwise leave this blank.
* Click on :guilabel:`Add subproject`

After adding the subproject, the URL the project is served from will by changed to
the URL displayed in the updated list of subprojects.

.. figure:: /img/screenshots/community-project-subproject-list.png
    :align: center
    :alt: Project subproject list with a new subproject added

    Project subproject list with a new subproject added

.. |button-edit| image:: /img/screenshots/community-edit-button.png
    :height: 1.5em
    :alt: Configure button
.. |button-delete| image:: /img/screenshots/community-delete-button.png
    :height: 1.5em
    :alt: Delete button

Updating a subproject
---------------------

You can update a subproject by clicking the configure button |button-edit| in the list of subprojects.
On the following page, it's possible to change both the subproject and its alias
using the :guilabel:`Subproject` dropdown and the :guilabel:`Alias` field.
Click :guilabel:`Update subproject` to save your changes.

The URL the subproject documentation is served from will be updated after you save your changes.

Deleting a subproject
---------------------

You can delete a subproject connection by clicking the delete button |button-delete| in the list of subprojects.
Confirm the deletion on the popup that shows to delete the subproject connection.

The subproject connection will be removed
and the project that was configured as a subproject will return to being served from it's own domain.
**This will not remove either project, only the subproject relationship will be removed.**
