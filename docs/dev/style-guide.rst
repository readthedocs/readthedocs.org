Documentation Style Guide
=========================

This document will serve as the canonical place to define how we write documentation at Read the Docs.
The goal is to have a shared understanding of how things are done,
and document the conventions that we follow.

Let us know if you have any questions or something isn't clear.

The brand
---------

We are called **Read the Docs**.
The ``the`` is not capitalized.

We do however use the acronym **RTD**.

Titles
------

For page titles we use sentence case.
This means only proper nouns and the first word are capitalized::

# Good ✅
How we handle support on Read the Docs.

# Bad 🔴
How we Handle Support on Read the Docs

If the page includes multiple sub-headings (H2, H3),
we use sentence case there as well.

Content
-------

* Do not break the content across multiple lines at 80 characters,
  but rather break them on semantic meaning (e.g. periods or commas).
  Read more about this `here <https://rhodesmill.org/brandon/2012/one-sentence-per-line/>`_.
* If you are cross-referencing to a different page within our website,
  use the ``doc`` role and not a hyperlink.
* If you are cross-referencing to a section within our website,
  use the ``ref`` role with the label from the `autosectionlabel extension <http://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html>`__.

Word List
---------

We have a specific way that we write common words:

* ``open source`` should be lower case.
* ``git`` should be lower case.
