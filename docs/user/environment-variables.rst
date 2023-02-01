.. _Environment Variables:

Configuring environment variables
=================================

Read the Docs allows you to define your own environment variables to be used in the build process.
This is useful for adding build secrets such as API tokens.

.. The following paragraph is difficult to balance.
.. We should ideally support environment variables in the Config File,
.. but as long as it's not supported then people can add environment variables in different ways.
.. Using the Dashboard is a good approach
.. but adding an environment variable with ``ENV=123 command --flag`` is possibly better.

Environment variables are defined in the :term:`dashboard` interface in :menuselection:`Admin --> Environment variables`.
In cases where the environment variable isn't a secret,
there are also :ref:`environment-variables:alternative approaches`.

Environment variables are configured and managed for a project's entire build environment `with 2 exceptions <Environment variables and build environments>`_.

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

In some scenarios, it's more feasible to define your build's environment variables using the ``.readthedocs.yaml`` :doc:`configuration file </config-file/index>`.
Using the :term:`dashboard` for administering environment variables may not be the right fit if you already know that you want to manage environment variables *as code*.

Consider the following scenario:

* The environment variable **is not** a secret.
* The environment variable is used just once for a custom command.

In this case, you can define the environment variable using :doc:`/build-customization`.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.11"
     jobs:
       post_build:
         - EXAMPLE_ENVIRONMENT_VARIABLE=foobar command --flag
