How to enable offline formats
=============================

This guide provides a step-by-step guide to enabling offline formats of your documentation.

They are automatically built by Read the Docs during our default build process,
as long as you have the configuration enabled to turn this on.

.. note:: Offline formats are currently only available for Sphinx-based documentation when using the Read the Docs build process.

Enabling offline formats
------------------------

Offline formats are enabled by the :ref:`config-file/v2:formats` key in our config file.
A simple example is here:

.. code-block:: yaml

   # Build PDF & ePub
   formats:
     - epub
     - pdf

Verifying offline formats
-------------------------

You can verify that offline formats are building in your :guilabel:`Project dashboard` > :guilabel:`Downloads`:

.. image::  /_static/images/guides/offline-formats.jpg
    :width: 75%

Deleting offline formats
------------------------

The entries in the Downloads section of your project dashboard reflect the
formats specified in your config file for each active version.

This means that if you wish to remove downloadable content for a given version,
you can do so by removing the matching :ref:`config-file/v2:formats` key from
your config file.
