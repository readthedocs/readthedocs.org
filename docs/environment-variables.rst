Environment Variables
=====================

Read the Docs provides a way to define environment variables for your project to be used in the build process.
They will be exposed to all the commands executed when building your documentation.

For example, it may happen that your documentation depends on an authenticated service to be built properly.
In this case, you will require some secrets to access these services.

To define an environment variable, you need to

#. Go to your project's :guilabel:`Admin` > :guilabel:`Environment Variables`
#. Click on :guilabel:`Add Environment Variable`
#. Fill the ``Name`` and ``Value`` (your secret)
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
for example in your Sphinx's ``conf.py`` file:

.. code-block:: python

   # conf.py
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
