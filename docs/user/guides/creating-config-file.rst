================================
Creating your configuration file
================================

As part of the initial setup for your Read the Docs site, you need to create a 
**configuration file** called ``.readthedocs.yaml``.

The configuration file like a personalized guidebook that tells the platform 
what specific settings for your project. Every project is unique, and by using 
a configuration file, you can tailor the behavior of Read the Docs to match 
your specific needs.

This how-to guide covers
#. Where to put your configuration file
#. The required parts of your configuration file

This should be enough to get you started!

.. tip::
   
   The complete list of all possible ``.readthedocs.yaml`` settings, including 
   the optional settings not covered in on this page, is found on 
   :doc:`the configuration file reference page </docs/user/config-file/index.rst>`.

####################################
Where to put your configuration file
####################################

The ``.readthedocs.yaml`` file should be placed in the **root directory**. The 
root directory is the top-most location of your repository.

To make the file, navigate to your root directory and create a new 
file with the name ``.readthedocs.yaml``.

*************************
The config file is hidden
*************************

The ``.`` at the beginning of the file indicates that the file is hidden. If 
the file browser you are using is not configured to show hidden files, you may 
not be able to see the file after you create it!

If you cannot see ``.readthedocs.yaml`` after creating it, use your favorite 
search engine to find instructions on showing hidden files for your specific 
operating system.

#############################################
The required parts of your configuration file
#############################################

The configuration file is a YAML file. YAML files are a "map": a collection of
key-value pairs that can be nested. This is not unlike a JSON file or ``dict``
object in Python.

This page won't explain the structure of YAML files, but many resources exist 
online.

***********
File header
***********

As a best practice, begin your file by providing the following.

#. The name of the file
#. A quick explanation of what the file is
#. A link to 
   :doc:`the configuration file reference page </docs/user/config-file/index.rst>`.

.. code-block:: yaml
   :linenos:

   # .readthedocs.yaml
   # Read the Docs configuration file
   # See https://docs.readthedocs.io/en/stable/config-file/v2.html for details
   # <--Remove this comment and leave this line blank-->

************************************
Version of configuration file schema
************************************

The version key tells the system how to read the rest of the configuration 
file. The current and only supported version is **version 2**.

.. code-block:: yaml
   :linenos:
   :lineno-start: 5

   version: 2
   # <--Remove this comment and leave this line blank-->

*******************
Python requirements
*******************

The ``python`` key contains several sub-keys, but only one sub-key is required:
``requirements``. However, since ``requirements`` is required, ``python`` is 
too.

The ``requirements`` key is a file path that points to a text (``.txt``) file
that lists the Python packages you want Read the Docs to install.