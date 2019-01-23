I Need Secrets (or Environment Variables) in my Build
=====================================================

It may happen that your documentation depends on an authenticated service to be built properly.
In this case, you will require some secrets to access these services.

Read the Docs provides a way to define environment variables for your project to be used in the build process.
All these variables will be exposed to all the commands executed when building your documentation.

To define an environment variable, you need to

#. Go to your project :guilabel:`Admin` > :guilabel:`Environment Variables`
#. Click on "Add Environment Variable" button
#. Input a ``Name`` and ``Value`` (your secret needed here)
#. Click "Save" button

.. note::

   Values will never be exposed to users, even to owners of the project.
   Once you create an environment variable you won't be able to see its value anymore because of security purposes.

After adding an environment variable from your project's admin, you can access it from your build process using Python,
for example:

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
