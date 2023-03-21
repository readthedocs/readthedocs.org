How to use a .readthedocs.yaml file in a sub-folder
===================================================

This guide shows how to configure a Read the Docs project to use a custom path for the ``.readthedocs.yaml`` build configuration.
*Monorepos* that have multiple documentation projects in the same Git repository can benefit from this feature.

By default,
Read the Docs will use the ``.readthedocs.yaml`` at the top level of your Git repository.
This is typically not sufficient for Monorepos layouts
when their nested documentation projects need fundamentally different build configurations.

.. seealso::

   `sphinx-multiproject <https://sphinx-multiproject.readthedocs.io/en/latest/>`__
   If you are only using Sphinx projects and want to share the same build configuration,
   you can also use the ``sphinx-multiproject`` extension.

Implementation considerations
-------------------------------

This feature is currently *project-wide*.
A custom build configuration file path is applied to all versions of your documentation.

.. warning::

   Changing the configuration path will apply to all versions.
   Different versions of the project may not be able to build again if this path is changed.

Adding an additional project from the same repository
-----------------------------------------------------

Once you have added the first project from the :ref:`Import Wizard <intro/import-guide:Automatically import your docs>`,
it will show as if it has already been imported and cannot be imported again.
In order to add another project with the same repository,
you will need to use the :ref:`Manual Import <intro/import-guide:Manually import your docs>`.

Setting the custom build configuration file
-------------------------------------------

Once you have added a Git repository to a project that needs a custom configuration file path,
navigate to :menuselection:`Admin --> Advanced Settings` and add the path to the :guilabel:`Build configuration file` field.

.. image:: /img/screenshot-howto-build-configuration-file.png
   :alt: Screenshot of where to find the :guilabel:`Build configuration file` setting.

After pressing :guilabel:`Save`,
you need to ensure that relevant versions of your documentation are built again.

.. tip::

   We recommend that you set up the first 1-2 projects and try to configure them as much as possible before scaling up.

Next steps
----------

Once you have the first couple of Read the Docs project configured with a custom path for the ``.readthedocs.yaml` file,
you can add all the other projects and build their configurations independently.

Everything in the Read the Docs projects will work independently as well,
meaning that you can have different sets of maintainers,
different sets of redirect rules,
different custom domains etc.

Other tips
----------

For a monorepo,
it's not desirable to have changes in unrelated sub-folders trigger new builds.

Therefore,
you should consider setting up :ref:`conditional build cancellation rules <build-customization:Cancel build based on a condition>`.
This is done in the build configuration file,
so you can write different rules for each documentation project in the Monorepo 💯️
