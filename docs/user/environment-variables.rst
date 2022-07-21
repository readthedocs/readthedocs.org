Environment Variables
=====================

Read the Docs supports two types of environment variables in project builds:

* `Default environment variables`_
* `User-defined environment variables`_

Both are merged together during the build process and are exposed to all of the executed commands. There are two exceptions for user-defined environment variables however:

* User-defined variables are not available during the checkout step of the :doc:`build process </builds>`
* User-defined variables that are not marked as public will not be available in :doc:`pull request builds </pull-requests>`

Default environment variables
-----------------------------

Read the Docs builders set the following environment variables automatically for each documentation build:

.. envvar:: READTHEDOCS

    Whether the build is running inside Read the Docs.

    :Default: ``True``

.. envvar:: READTHEDOCS_VERSION

    The :term:`slug` of the version being built, such as ``latest``, ``stable``,
    or a branch name like ``feature-1234``. For :doc:`pull request builds </pull-requests>`,
    the value will be the pull request number.

.. envvar:: READTHEDOCS_VERSION_NAME

    The verbose name of the version being built, such as ``latest``, ``stable``,
    or a branch name like ``feature/1234``.

.. envvar:: READTHEDOCS_VERSION_TYPE

    The type of the version being built.

    :Values: ``branch``, ``tag``, ``external`` (for :doc:`pull request builds </pull-requests>`), or ``unknown``

.. envvar:: READTHEDOCS_PROJECT

    The :term:`slug` of the project being built. For example, ``my-example-project``.

.. envvar:: READTHEDOCS_LANGUAGE

    The locale name, or the identifier for the locale, for the project being built.
    This value comes from the project's configured language.

    :Examples: ``en``, ``it``, ``de_AT``, ``es``, ``pt_BR``

User-defined environment variables
----------------------------------

If extra environment variables are needed in the build process (like an API token),
you can define them from the project's settings page:

#. Go to your project's :guilabel:`Admin` > :guilabel:`Environment Variables`
#. Click on :guilabel:`Add Environment Variable`
#. Fill the ``Name`` and ``Value``
#. Check the :guilabel:`Public` option if you want to expose this environment variable
   to :doc:`builds from pull requests </pull-requests>`.

   .. warning::

      If you mark this option, any user that can create a pull request
      on your repository will be able to see the value of this environment variable.

#. Click on :guilabel:`Save`

.. note::

   Once you create an environment variable,
   you won't be able to see its value anymore.

After adding an environment variable,
you can read it from your build process,
for example in your Sphinx's configuration file:

.. code-block:: python
   :caption: conf.py

   import os
   import requests

   # Access to our custom environment variables
   username = os.environ.get('USERNAME')
   password = os.environ.get('PASSWORD')

   # Request a username/password protected URL
   response = requests.get(
       'https://httpbin.org/basic-auth/username/password',
       auth=(username, password),
   )

You can also use any of these variables from :term:`user-defined build jobs` in your project's configuration file:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: ubuntu-22.04
     tools:
       python: 3.10
     jobs:
       post_install:
         - curl -u ${USERNAME}:${PASSWORD} https://httpbin.org/basic-auth/username/password
