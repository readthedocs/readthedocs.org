.. Next steps: Show an example pattern for a monorepo layout or link to an example project

How to use a .readthedocs.yaml file in a sub-folder
===================================================

This guide shows how to configure a Read the Docs project to use a custom path for the ``.readthedocs.yaml`` build configuration.
`Monorepos <https://en.wikipedia.org/wiki/Monorepo>`__ that have multiple documentation projects in the same Git repository can benefit from this feature.

By default,
Read the Docs will use the ``.readthedocs.yaml`` at the top level of your Git repository.
But if a Git repository contains multiple documentation projects that need different build configurations,
you will need to have a ``.readthedocs.yaml`` file in multiple sub-folders.

.. seealso::

   `sphinx-multiproject <https://sphinx-multiproject.readthedocs.io/en/latest/>`__
       If you are only using Sphinx projects and want to share the same build configuration,
       you can also use the ``sphinx-multiproject`` extension.

   :doc:`/guides/environment-variables`
       You might also be able to reuse the same configuration file across multiple projects,
       using only environment variables.
       This is possible if the configuration pattern is very similar and the documentation tool is the same.

Implementation considerations
-----------------------------

This feature is currently *project-wide*.
A custom build configuration file path is applied to all versions of your documentation.

.. warning::

   Changing the configuration path will apply to all versions.
   Different versions of the project may not be able to build again if this path is changed.

Adding an additional project from the same repository
-----------------------------------------------------

Once you have added the first project from the :ref:`Import Wizard <intro/add-project:Automatically add your project>`,
you will need to repeat this process again to add the additional project from the same repository.

Setting the custom build configuration file
-------------------------------------------

Once you have added a Git repository to a project that needs a custom configuration file path,
navigate to :menuselection:`Admin --> Settings` and add the path to the :guilabel:`Build configuration file` field.

.. image:: /img/screenshot-howto-build-configuration-file.png
   :alt: Screenshot of where to find the :guilabel:`Build configuration file` setting.

After pressing :guilabel:`Save`,
you need to ensure that relevant versions of your documentation are built again.

.. tip::

   Having multiple different build configuration files can be complex.
   We recommend setting up 1-2 projects in your Monorepo and getting them to build and publish successfully before adding additional projects to the equation.

Next steps
----------

Once you have your monorepo pattern implemented and tested and it's ready to roll out to all your projects,
you should also consider the Read the Docs project setup for these individual projects.

Having individual projects gives you the full flexibility of the Read the Docs platform to make individual setups for each project.

For each project, it's now possible to configure:

* Sets of maintainers (or :doc:`organizations </commercial/organizations>` on |com_brand|)
* :doc:`Custom redirect rules </guides/custom-domains>`
* :doc:`Custom domains </guides/custom-domains>`
* :doc:`Automation rules </automation-rules>`
* :doc:`Traffic analytics </traffic-analytics>`
* Additional documentation tools with individual :doc:`build processes </build-customization>`:
  One project might use :doc:`Sphinx <sphinx:index>`,
  while another project setup might use `Asciidoctor <https://asciidoctor.org/>`__.

...and much more. *All* settings for a Read the Docs project is available for each individual project.

.. seealso::

   :doc:`/guides/subprojects`
      More information on nesting one project inside another project.
      In this setup, it is still possible to use the same monorepo for each subproject.

Other tips
----------

For a monorepo,
it's not desirable to have changes in unrelated sub-folders trigger new builds.

Therefore,
you should consider setting up :ref:`conditional build cancellation rules <build-customization:Cancel build based on a condition>`.
The configuration is added in each ``.readthedocs.yaml``,
making it possible to write one conditional build rules per documentation project in the Monorepo 💯️
