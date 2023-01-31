.. _Environment Variables:

Configuring environment variables
=================================

Read the Docs allows you to define your own environment variables to be used in the build process.
This is useful for adding your project's build secrets,
in case your build needs to access API tokens.

In many cases,
it is also easier or more feasible to define your build's environment variables using the Read the Docs :term:`dashboard` interface in
:menuselection:`Admin --> Environment variables`
rather than the ``.readthedocs.yaml`` :doc:`configuration file </config-file/index>`.

Environment variables are configured and managed for your projects entire build `with 2 exceptions <Environment variables and build environments>`_.

.. seealso::

   :doc:`/guides/environment-variables`
     A practical example of adding and accessing custom environment variables.

   :doc:`/reference/environment-variables`
     Reference to all pre-defined environment variables for your build environments.

   :ref:`Public API reference: Environment variables <api/v3:Environment Variables>`
     Reference for managing custom environments via Read the Docs' API.

Environment variables and build environments
--------------------------------------------

When a :doc:`build process </builds>` is started,
:doc:`pre-defined environment variables </reference/environment-variables>` and custom environment variables are added *at each step* of the build process.

The two layers are merged together during the build process and are exposed to all of the executed commands,
with pre-defined variables taking precedence over custom environment variables.

There are two noteworthy exceptions for custom environment variables however:

Build checkout step
  Custom environment variables are **not** available during the checkout step of the :doc:`build process </builds>`
Pull Request builds
  Custom environment variables that are not marked as :guilabel:`Public` will not be available in :doc:`pull request builds </pull-requests>`

Alternative approaches
----------------------
