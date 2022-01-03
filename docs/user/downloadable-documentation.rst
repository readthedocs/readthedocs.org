Downloadable Documentation
==========================

Read the Docs supports building multiple formats for Sphinx-based projects:

* PDF
* ePub
* Zipped HTML

This means that every commit that you push will automatically update your PDFs as well as your HTML.

This is enabled by the :ref:`config-file/v2:formats` key in our config file.
A simple example is here:

.. code-block:: yaml

   # Build PDF & ePub
   formats:
     - epub
     - pdf

If you want to see an example,
you can download the Read the Docs documentation in the following formats:

    * `PDF`_ 
    * `ePub`_ 
    * `Zipped HTML`_ 
    
.. _PDF: https://docs.readthedocs.io/_/downloads/en/latest/pdf/
.. _ePub: https://docs.readthedocs.io/_/downloads/en/latest/epub/
.. _Zipped HTML: https://docs.readthedocs.io/_/downloads/en/latest/htmlzip/

Use cases
---------

This functionality is great for anyone who needs documentation when they aren't connected to the internet.
Users who are about to get on a plane can grab a PDF and have the entire doc set ready for their trip.

The other value is having the entire docset in a single file.
You can send a user an email with a single PDF or ePub and they'll have all the docs in one place.

Deleting downloadable content
-----------------------------

The entries in the Downloads section of your project dashboard reflect the
formats specified in your config file for each active version.

This means that if you wish to remove downloadable content for a given version,
you can do so by removing the matching :ref:`config-file/v2:formats` key from
your config file.
