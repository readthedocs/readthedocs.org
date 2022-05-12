Subprojects
===========

Projects can be configured in a nested manner, by configuring a project as a
*subproject* of another project. This allows for documentation projects to share
a search index and a namespace or custom domain, but still be maintained
independently.

For example, a parent project, ``Foo`` is set up with a subproject, ``Bar``. The
documentation for ``Foo`` will be available at:

https://foo.readthedocs.io/en/latest/

The documentation for ``Bar`` will be available under this same path:

https://foo.readthedocs.io/projects/bar/en/latest/

Adding a subproject
-------------------

In the admin dashboard for your project, select "Subprojects" from the menu.
From this page you can add a subproject by typing in the project slug.

Subproject aliases
~~~~~~~~~~~~~~~~~~

You can use an alias for the subproject when it is created. This allows you to override the URL that is used to access it, giving more configurability to how you want to structure your projects.

Sharing a custom domain
-----------------------

Projects and subprojects can also be used to share a custom domain with a number
of projects. To configure this, one project should be established as the parent
project. This project will be configured with a custom domain. Projects can then
be added as subprojects to this parent project.

If the example project ``Foo`` was set up with a custom domain,
``docs.example.com``, the URLs for projects ``Foo`` and ``Bar`` would
respectively be at: https://docs.example.com/en/latest/ and
https://docs.example.com/projects/bar/en/latest/

Custom domain on subprojects
----------------------------

Adding a custom domain to a subproject is not allowed,
since your documentation will always be served from
the domain of the parent project.

Search
------

Search on the parent project will include results from its subprojects.
If you search on the ``v1`` version of the parent project,
results from the ``v1`` version of its subprojects will be included,
or from the default version for subprojects that don't have a ``v1`` version.

This is currently the only way to share search results between projects,
we do not yet support sharing search results between sibling subprojects or arbitrary projects.
