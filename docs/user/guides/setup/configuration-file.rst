================================
Creating your configuration file
================================

As part of the initial setup for your Read the Docs site, you need to create a
**configuration file** called ``.readthedocs.yaml``.

The configuration file is like a personalized guidebook that tells the platform what specific settings to use for your project.
By using a configuration file,
you can tailor the behavior of Read the Docs to match your project's specific needs.

In addition that that,
using a configuration file can capture important configuration options that might otherwise break in the future if left undefined.

This how-to guide covers:

#. Where to put your configuration file.
#. What to add to your configuration file.

This should be enough to get you started!

.. tip::

   The complete list of all possible ``.readthedocs.yaml`` settings, including
   the optional settings not covered in on this page, is found on
   :doc:`the configuration file reference page </config-file/index>`.

####################################
Where to put your configuration file
####################################

The ``.readthedocs.yaml`` file should be placed in the top-most directory of your project's repository.

Add a new file with the exact name ``.readthedocs.yaml`` in the repository's root directory.
We will get to the contents of the file in a moment.


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
   :doc:`the configuration file reference page </config-file/index>`.

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
