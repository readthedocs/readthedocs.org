How to enable offline formats
=============================

This guide provides **step-by-step instructions to enabling offline formats** of your documentation.

They are automatically built by Read the Docs during our default build process,
as long as you have the configuration enabled to turn this on.

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


Continue learning
-----------------

.. seealso::

   Other pages in our documentation are relevant to this feature,
   and might be a useful next step.


   * :doc:`/downloadable-documentation` - Overview of this feature.
   * :ref:`config-file/v2:formats` - Configuration file options for offline formats.

   ..
      TODO: Link to our build customization page on this once we write it.
