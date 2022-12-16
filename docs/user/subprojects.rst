Subprojects: host multiple projects on a single domain
======================================================

Projects can be configured in a nested manner, by configuring a project as a
*subproject* of another project. This allows for documentation projects to share
a search index and a namespace or custom domain, but still be maintained
independently.

This is useful for:

* Organizations that need all their projects visible in one documentation portal or landing page
* Projects that document and release several packages or extensions
* Organizations or projects that want to have a common search function for several sets of documentation

For example, a parent project, ``example-project`` is set up with a subproject, ``plugin``. The
documentation for ``example-project`` will be available at:

https://example-project.readthedocs.io/en/latest/

The documentation for ``plugin`` will be available under this same path:

https://example-project.readthedocs.io/projects/plugin/en/latest/

.. seealso::

   :doc:`/guides/subprojects`

Sharing a custom domain
-----------------------

Projects and subprojects can be used to share a custom domain.
To configure this, one project should be established as the main project.
This project will be configured with a custom domain.
Other projects are then added as subprojects to the main project.

If the example project ``foo`` was set up with a custom domain,
``docs.example.com``, the URLs for projects ``foo`` and ``bar`` would
respectively be at:

* `foo`: https://docs.example.com/en/latest/
* `bar`: https://docs.example.com/projects/bar/en/latest/

.. note::

   The terms "parent" and "child" are also used,
   where the main project is the parent and all subprojects are a child.
   You can **not** have a child of a child,
   meaning that you cannot add a subproject to a subproject.

Using aliases
-------------

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

When you add a subproject,
the subproject will not be directly available anymore from its own domain.
For instance, ``subproject.readthedocs.io/`` will redirect to ``mainproject.readthedocs.io/projects/subproject``.

Custom domain on subprojects
----------------------------

Adding a custom domain to a subproject is not allowed,
since your documentation will always be served from
the domain of the parent project.

Separate release cycles
-----------------------

By using subprojects,
you can present the documentation of several projects
even though they have separate release cycles.

Your main project may have its own versions and releases,
while all of its subprojects maintain their own individual versions and releases.
We recommend that documentation follows the release cycle of whatever it is documenting,
meaning that your subprojects should be free to follow their own release cycle.

This is solved by having an individual :term:`flyout menu` active for the project that's viewed.
When the user navigates to a subproject,
they are presented with a flyout menu matching the subproject's versions and :doc:`/downloadable-documentation`.

Search
------

Search on the parent project will include results from its subprojects.
If you search on the ``v1`` version of the parent project,
results from the ``v1`` version of its subprojects will be included,
or from the default version for subprojects that don't have a ``v1`` version.

This is currently the only way to share search results between projects,
we do not yet support sharing search results between sibling subprojects or arbitrary projects.
