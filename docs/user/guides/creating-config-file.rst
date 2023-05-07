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

