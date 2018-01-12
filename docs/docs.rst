Building and Contributing to Documentation
==========================================

As one might expect,
the documentation for Read the Docs is built using Sphinx and hosted on Read the Docs.
The docs are kept in the ``docs/`` directory at the top of the source tree.

You can build the docs by installing ``Sphinx`` and running::

	# in the docs directory
	make html

Please follow these guidelines when updating our docs.
Let us know if you have any questions or if something isn't clear.

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
  but rather broken them on semantic meaning (e.g. periods or commas).
* If you are cross-referencing to a different page within our website,
  use the ``doc`` directive and not a hyperlink.
