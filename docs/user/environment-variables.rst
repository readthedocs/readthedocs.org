Environment Variables
=====================

Read the Docs supports environment variables when building your project.
There are two types of them:

* default environment variables
* user-defined environment variables

Both are merged together during the build process and exposed to all the commands executed when building the documentation.


Default environment variables
-----------------------------

Read the Docs builder sets the following environment variables when building your documentation:

.. csv-table:: Environment Variables
   :header: Environment variable, Description, Example value
   :widths: 15, 10, 30

   ``READTHEDOCS``, Whether the build is running inside Read the Docs, ``True``
   ``READTHEDOCS_VERSION``, The Read the Docs slug of the version which is being built, ``latest``
   ``READTHEDOCS_VERSION_NAME``, Corresponding version name as displayed in Read the Docs' version switch menu, ``stable``
   ``READTHEDOCS_VERSION_TYPE``, Type of the event triggering the build, ``branch`` | ``tag`` | ``external`` (for :doc:`pull request builds </pull-requests>`) | ``unknown``
   ``READTHEDOCS_PROJECT``, The Read the Docs' slug of the project which is being built, ``my-example-project``
   ``READTHEDOCS_LANGUAGE``, The Read the Docs' language slug of the project which is being built, ``en``

.. note::

   The term slug is used to refer to a unique string across projects/versions containing ASCII characters only.
   This value is used in the URLs of your documentation.


User-defined environment variables
----------------------------------

If extra environment variables are needed in the build process (like an API token),
you can define them from the project setting's page:

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

Also, you can read it from the :term:`user-defined build jobs` in the config file:

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
