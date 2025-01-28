Subprojects
===========

In this article, you can learn more about how several documentation projects can be combined and presented to the reader on the same website.

Read the Docs can be configured to make other *projects* available on the website of the *main project* as **subprojects**.
This allows for documentation projects to share a search index and a namespace or custom domain,
but still be maintained independently.

This is useful for:

* Organizations that need all their projects visible in one documentation portal or landing page
* Projects that document and release several packages or extensions
* Organizations or projects that want to have a common search function for several sets of documentation

For a main project ``example-project``, a subproject ``example-project-plugin`` can be made available as follows:

* Main project: ``https://example-project.readthedocs.io/en/latest/``
* Subproject: ``https://example-project.readthedocs.io/projects/plugin/en/latest/``

.. seealso::

   :doc:`/guides/subprojects`
     Learn how to create and manage subprojects

   :doc:`/guides/intersphinx`
     Learn how to use references between different Sphinx projects, for instance between subprojects


Sharing a custom domain
-----------------------

Projects and subprojects can be used to share a custom domain.
To configure this, one project should be established as the main project and configured with a custom domain.
Other projects are then added as subprojects to the main project.

If the example project ``example-project`` was set up with a custom domain,
``docs.example.com``, the URLs for projects ``example-project`` and ``example-project-plugin`` with alias ``plugin`` would
respectively be at:

* ``example-project``: ``https://docs.example.com/en/latest/``
* ``example-project-plugin``: ``https://docs.example.com/projects/plugin/en/latest/``

Using aliases
-------------

Adding an alias for the subproject allows you to override the URL that is used to access it,
giving more control over how you want to structure your projects.
You can choose an alias for the subproject when it is created.

You can set your subproject's project name and :term:`slug` however you want,
but we suggest prefixing it with the name of the main project.

Typically, a subproject is created with a ``<mainproject>-`` prefix,
for instance if the main project is called ``example-project`` and the subproject is called ``plugin``,
then the subproject's Read the Docs project :term:`slug` will be ``example-project-plugin``.
When adding the subproject,
the alias is set to ``plugin`` and the project's URL becomes
``example-project.readthedocs.io/projects/plugin``.

When you add a subproject,
the subproject will not be directly available anymore from its own domain.
For instance, ``example-project-plugin.readthedocs.io/`` will redirect to ``example-project.readthedocs.io/projects/plugin``.

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
