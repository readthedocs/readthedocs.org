.. _Environment Variables:

Environment variable overview
=============================

Read the Docs allows you to define your own environment variables to be used in the build process.
It also defines a set of :doc:`default environment variables </reference/environment-variables>` with information about your build.
These are useful for different purposes:

* Custom environment variables are useful for adding build secrets such as API tokens.
* Default environment variables are useful for varying your build specifically for Read the Docs or specific types of builds on Read the Docs.

.. The following introduction is difficult to balance.
.. We should ideally support environment variables in the Config File,
.. but as long as it's not supported then people can add environment variables in different ways.
.. Using the Dashboard is a good approach
.. but adding an environment variable with ``ENV=123 command --flag`` in the build process is possibly better.

Custom environment variables are defined in the :term:`dashboard` interface in :menuselection:`Admin --> Environment variables`.
Environment variables are defined for a project's entire build process,
:ref:`with 2 important exceptions <custom_env_var_exceptions>`.

Aside from storing secrets,
there are :ref:`other patterns <environment-variables:Patterns of using environment variables>` that take advantage of environment variables,
like reusing the same *monorepo* configuration in multiple documentation projects.
In cases where the environment variable isn't a secret,
like a build tool flag,
you should also be aware of the :ref:`alternatives to environment variables <environment-variables:Alternatives to environment variables>`.

.. seealso::

   :doc:`/guides/environment-variables`
     A practical example of adding and accessing custom environment variables.

   :doc:`/reference/environment-variables`
     Reference to all pre-defined environment variables for your build environments.

   :ref:`Public API reference: Environment variables <api/v3:Environment Variables>`
     Reference for managing custom environments via Read the Docs' API.

Environment variables and build process
---------------------------------------

When a :doc:`build process </builds>` is started,
:doc:`pre-defined environment variables </reference/environment-variables>` and custom environment variables are added *at each step* of the build process.
The two sets of environment variables are merged together during the build process and are exposed to all of the executed commands,
with pre-defined variables taking precedence over custom environment variables.

.. _custom_env_var_exceptions:

There are two noteworthy exceptions for *custom environment variables*:

Build checkout step
  Custom environment variables are **not** available during the checkout step of the :doc:`build process </builds>`
Pull request builds
  Custom environment variables that are not marked as :guilabel:`Public` will not be available in :doc:`pull request builds </pull-requests>`

.. the presence of this section is intended to evolve into a better explanation
.. with a few more scenarios,
.. once there is better options for environment variables in config files

Limitations
-----------

- Individual environment variables are limited to 48 KB in size.
- The total size of all environment variables in a project is limited to 256 KB.

Patterns of using environment variables
---------------------------------------

Aside from storing secrets,
environment variables are also useful if you need to make either your :doc:`.readthedocs.yaml </config-file/v2>` or the commands called in the :doc:`build process </builds>`
behave depending on :doc:`pre-defined environment variables </reference/environment-variables>` or your own custom environment variables.

Example: Multiple projects from the same Git repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have the need to build multiple documentation websites from the same Git repository,
you can use an environment variable to configure the behavior of your :doc:`build commands </build-customization>`
or Sphinx ``conf.py`` file.

An example of this is found in *the documentation project that you are looking at now*.
Using the Sphinx extension `sphinx-multiproject`_,
the following configuration code decides whether to build the *user* or *developer* documentation.
This is defined by the ``PROJECT`` environment variable:

.. code-block:: python
   :caption: Read the Docs' conf.py [1]_ is used to build 2 documentation projects.

   from multiproject.utils import get_project

   # (...)

   multiproject_projects = {
       "user": {
           "use_config_file": False,
           "config": {
               "project": "Read the Docs user documentation",
           },
       },
       "dev": {
           "use_config_file": False,
           "config": {
               "project": "Read the Docs developer documentation",
           },
       },
   }


   docset = get_project(multiproject_projects)

.. _sphinx-multiproject: https://sphinx-multiproject.readthedocs.io/
.. [1] https://github.com/readthedocs/readthedocs.org/blob/main/docs/conf.py

Alternatives to environment variables
-------------------------------------

In some scenarios, it's more feasible to define your build's environment variables using the ``.readthedocs.yaml`` :doc:`configuration file </config-file/index>`.
Using the :term:`dashboard` for administering environment variables may not be the right fit if you already know that you want to manage environment variables *as code*.

Consider the following scenario:

* The environment variable **is not** a secret.

  **and**
* The environment variable is used just once for a custom command.

In this case, you can define the environment variable *as code* using :doc:`/build-customization`.
The following example shows how a non-secret single-purpose environment variable can also be used.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.12"
     jobs:
       post_build:
         - EXAMPLE_ENVIRONMENT_VARIABLE=foobar command --flag
