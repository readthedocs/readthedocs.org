Privacy levels
--------------

.. include:: /shared/admonition-rtd-business.rst

Privacy levels allow you to set the visibility of your project and its versions.
This allows you to specify what information is available to the public and what is private.
Privacy can be controlled at the level of the project and each version,
and nothing more granular (eg. specific directories or URLs) can be controlled.

Project privacy
~~~~~~~~~~~~~~~

By default, only users that belong to your organization can see the dashboard of your project and its builds.
If you want users outside your organization to be able to see the dashboard of your project,
and the build output of *public versions* you can set the privacy level of your project to ``Public``.

You can set the project privacy level in your :term:`dashboard` by navigating to :menuselection:`Admin --> Settings`
and changing :guilabel:`Privacy level` to `Public`.

**Making a project public doesn't give access to any versions.**
So if you want all your versions to be accessible,
you need to configure those to be `Public` as well.

Version privacy
~~~~~~~~~~~~~~~

Each version of your documentation can be set to either `Public` or `Private`.
This allows you to control who can see the documentation for a specific version.

* Documentation for public versions is visible to everyone.
* Private versions are available only to people who have permissions to see them.
  They will not display on any list view, and will 404 when visited by people without viewing permissions.
  If you want to share your docs temporarily, see :doc:`/commercial/sharing`.

You can set the privacy level for each version in your :term:`dashboard` by navigating to :menuselection:`Versions --> $version ... Drop down --> Configure version` and changing :guilabel:`Privacy level` to `Public`.

Recommended workflow
~~~~~~~~~~~~~~~~~~~~

We recommend defaulting everything to private,
and only making versions public when you are ready to share them with the world.
This allows you to work on your documentation in private,
and only share it when you are ready.
