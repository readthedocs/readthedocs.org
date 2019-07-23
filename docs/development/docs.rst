Building and Contributing to Documentation
==========================================

As one might expect,
the documentation for Read the Docs is built using Sphinx and hosted on Read the Docs.
The docs are kept in the ``docs/`` directory at the top of the source tree.

You can build the docs by first ensuring this project is set up locally according to the :doc:`Installation Guide <install>`.
Follow the instructions just up to the point of activating the virtual environment and then continue here.

Next, install the documentation dependencies using ``pip`` (make sure you are inside of the virtual environment)::

    pip install -r requirements/local-docs-build.txt

This installs ``Sphinx``, amongst other things.

After that is done, build the documentation by running::

	# in the docs directory
	make html

Please follow these guidelines when updating our docs.
Let us know if you have any questions or something isn't clear.

The brand
---------

We are called **Read the Docs**.
The *the* is not capitalized.

We do however use the acronym **RTD**.

Titles
------

For page titles, or Heading1 as they are sometimes called, we use title-case.

If the page includes multiple sub-headings (H2, H3),
we usually use sentence-case unless the titles include terminology that is supposed to be capitalized.

Content
-------

* Do not break the content across multiple lines at 80 characters,
  but rather break them on semantic meaning (e.g. periods or commas).
  Read more about this `here <http://rhodesmill.org/brandon/2012/one-sentence-per-line/>`_.
* If you are cross-referencing to a different page within our website,
  use the ``doc`` role and not a hyperlink.
* If you are cross-referencing to a section within our website,
  use the ``ref`` role with the label from the `autosectionlabel extension <http://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html>`__.
