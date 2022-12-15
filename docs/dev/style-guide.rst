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

* Use ``:menuselection:`` when referring to an item or sequence of items in navigation.
* Use ``:guilabel:`` when referring to a visual element on the screen - such as a button, drop down or input field.
* Use ``**bold text**`` when referring to a non-interactive text element, such as a header.
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

* ``open source`` should be lower case, unless you are definitely referring to `OSI's Open Source Definition <https://opensource.org/osd>`.
* ``git`` should be lower case.

Glossary
--------

Since the above Word List is for internal reference,
we also maintain a :doc:`/glossary` with terms that have canonical definitions in our docs.
Terms that can otherwise have multiple definitions
*or* have a particular meaning in Read the Docs context
should always be added to the :doc:`/glossary` and referenced using the ``:term:`` role.

Using a glossary helps us (authors) to have consistent definitions
but even more importantly,
it helps and includes readers by giving them quick and easy access to terms that they may be unfamiliar with.

Use an external link or Intersphinx reference when a term is clearly defined elsewhere.
