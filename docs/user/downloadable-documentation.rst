Offline formats (PDF, ePub, HTML)
=================================

This page will provide an overview of a core Read the Docs feature: building docs in multiple formats.

Read the Docs supports the following formats by default:

* PDF
* ePub
* Zipped HTML

This means that every commit that you push will automatically update your offline formats as well as your documentation website.

Use cases
---------

This functionality is great for anyone who needs documentation when they aren't connected to the internet.
Users who are about to get on a plane can grab a single file and have the entire documentation during their trip.
Many academic and scientific projects benefit from these additional formats.

PDF versions are also helpful to automatically **create printable versions of your documentation**.
The source of your documentation will be structured to support both online and offline formats.
This means that a documentation project displayed as a website can be downloaded as a PDF,
ready to be printed as a report or a book.

Offline formats also support having the entire documentation in a single file.
Your entire documentation can now be delivered as an email attachment,
uploaded to an eReader,
or accessed and searched locally without online latency.
This makes your documentation project **easy to redistribute or archive**.

Accessing offline formats
-------------------------

You can download offline formats in the :guilabel:`Project dashboard` > :guilabel:`Downloads`:

.. image::  /_static/images/guides/offline-formats.jpg
    :width: 75%

When you are browsing a documentation project,
they can also be accessed directly from the :doc:`/flyout-menu`.

Examples
--------

If you want to see an example,
you can download the Read the Docs documentation in the following formats:

    * `PDF`_
    * `ePub`_
    * `Zipped HTML`_

.. _PDF: https://docs.readthedocs.io/_/downloads/en/latest/pdf/
.. _ePub: https://docs.readthedocs.io/_/downloads/en/latest/epub/
.. _Zipped HTML: https://docs.readthedocs.io/_/downloads/en/latest/htmlzip/

Continue learning
-----------------

Downloadable documentation formats are built by your documentation framework.
They are then published by Read the Docs and included in your :term:`Flyout menu`.
Therefore, it's your framework that decides exactly how each output is built and which formats are supported:

Sphinx
   All output formats are built mostly lossless from the documentation source,
   meaning that your documentation source (reStructuredText or Markdown/MyST) is built from scratch for each output format.

MkDocs and Docsify + more
   The common case for most documentation frameworks is that several alternative extensions exist supporting various output formats.
   Most of the extensions export the HTML outputs as another format (for instance PDF) through a conversion process.

Because Sphinx supports the generation of offline formats through an official process,
we are also able to support it officially.
Other alternatives can also work,
provided that you identify which extension you want to use and configure the environment for it to run.
**Other formats aren't natively supported by Read the Docs,
but support is coming soon.**

.. seealso::

   Other pages in our documentation are relevant to this feature,
   and might be a useful next step.

   * :doc:`/guides/enable-offline-formats` - Guide to enabling and disabling this feature.
   * :ref:`config-file/v2:formats` - Configuration file options for offline formats.
