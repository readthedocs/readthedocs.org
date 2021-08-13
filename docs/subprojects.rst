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

Adding a Subproject
-------------------

In the admin dashboard for your project, select "Subprojects" from the menu.
From this page you can add a subproject by typing in the project slug.

Sharing a Custom Domain
-----------------------

Projects and subprojects can also be used to share a custom domain with a number
of projects. To configure this, one project should be established as the parent
project. This project will be configured with a custom domain. Projects can then
be added as subprojects to this parent project.

If the example project ``Foo`` was set up with a custom domain,
``docs.example.com``, the URLs for projects ``Foo`` and ``Bar`` would
respectively be at: https://docs.example.com/en/latest/ and
https://docs.example.com/projects/bar/en/latest/

Search
------

Projects that are configured as subprojects will share a search index with their
parent and sibling projects. This is currently the only way to share search
indexes between projects, we do not yet support sharing search indexes between
arbitrary projects.
