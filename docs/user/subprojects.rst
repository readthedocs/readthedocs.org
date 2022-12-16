Subprojects: host multiple projects on a single domain
=====================================================

Projects can be configured in a nested manner, by configuring a project as a
*subproject* of another project. This allows for documentation projects to share
a search index and a namespace or custom domain, but still be maintained
independently.

This is useful for:

* Organizations that need all their projects visible in one documentation portal or landing page
* Projects that document and release several packages or extensions
* Organizations or projects that want to have a common search function for several sets of documentation

For example, a parent project, ``foo`` is set up with a subproject, ``bar``. The
documentation for ``foo`` will be available at:

https://foo.readthedocs.io/en/latest/

The documentation for ``bar`` will be available under this same path:

https://foo.readthedocs.io/projects/bar/en/latest/

.. seealso::

   :doc:`/guides/subprojects`


Sharing a custom domain
-----------------------

Projects and subprojects can also be used to share a custom domain with a number
of projects. To configure this, one project should be established as the parent
project. This project will be configured with a custom domain. Projects can then
be added as subprojects to this parent project.

If the example project ``foo`` was set up with a custom domain,
``docs.example.com``, the URLs for projects ``foo`` and ``bar`` would
respectively be at: 

* `foo`: https://docs.example.com/en/latest/
* `bar`: https://docs.example.com/projects/bar/en/latest/

Custom domain on subprojects
----------------------------

Adding a custom domain to a subproject is not allowed,
since your documentation will always be served from
the domain of the parent project.

Separate release cycles
-----------------------

When several projects are documented in the same space, it's common that they follow separate release cycles.

We recommend that the documentation follows the release cycle of whatever it is documenting.
By using subprojects, you can present your documentation for several projects with separate release cycles.
This is solved by having the :term:`flyout menu` active for the project that's viewed.

When the user navigates to a subproject,
they are presented with a :term:`flyout menu` matching the subproject's versions and :doc:`/downloadable-documentation`.

Search
------

Search on the parent project will include results from its subprojects.
If you search on the ``v1`` version of the parent project,
results from the ``v1`` version of its subprojects will be included,
or from the default version for subprojects that don't have a ``v1`` version.

This is currently the only way to share search results between projects,
we do not yet support sharing search results between sibling subprojects or arbitrary projects.
