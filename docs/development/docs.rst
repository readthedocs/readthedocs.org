Building and Contributing to Documentation
==========================================

As one might expect,
the documentation for Read the Docs is built using Sphinx and hosted on Read the Docs.
The docs are kept in the ``docs/`` directory at the top of the source tree.

Contributing through the Github UI
----------------------------------

If you're making small changes to the documentation,
you can verify those changes through the documentation generated when you open a PR and can be accessed using the Github UI.

#. click the checkmark next to your commit and it will expand to have multiple options

#. click the "details" link next to the "docs/readthedocs.org:docs" item

   .. image:: /img/details_link.png

#. navigate to the section of the documentation you worked on to verify your changes

Contributing from your local machine
------------------------------------

If you're making large changes to the documentation,
you may want to verify those changes locally before pushing upstream.

#. clone the `readthedocs.org` repository:

   .. code-block:: console

      $ git clone --recurse-submodules https://github.com/readthedocs/readthedocs.org/

#. create a virtual environment with Python 3.6
   (preferably the latest release, 3.6.15 at the time of writing),
   activate it, and upgrade both pip and setuptools:

   .. code-block:: console

      $ cd readthedocs.org
      $ python3.6 -m venv .venv
      $ source .venv/bin/activate
      (.venv) $ python -m pip install -U pip setuptools

#. install documentation requirements

   .. code-block:: console

      (.venv) $ pip install -r requirements/testing.txt
      (.venv) $ pip install -r requirements/docs.txt

#. build the documents

   .. code-block:: console

      (.venv) $ cd docs
      (.venv) $ make livehtml

#. the documents will be available at http://127.0.0.1:4444/ and will rebuild each time you edit and save a file.

Guidelines
----------

Please follow these guidelines when updating our docs.
Let us know if you have any questions or something isn't clear.

The brand
^^^^^^^^^

We are called **Read the Docs**.
The *the* is not capitalized.

We do however use the acronym **RTD**.

Titles
^^^^^^

For page titles, or Heading1 as they are sometimes called, we use title-case.

If the page includes multiple sub-headings (H2, H3),
we usually use sentence-case unless the titles include terminology that is supposed to be capitalized.

Content
^^^^^^^

* Do not break the content across multiple lines at 80 characters,
  but rather break them on semantic meaning (e.g. periods or commas).
  Read more about this `here <https://rhodesmill.org/brandon/2012/one-sentence-per-line/>`_.
* If you are cross-referencing to a different page within our website,
  use the ``doc`` role and not a hyperlink.
* If you are cross-referencing to a section within our website,
  use the ``ref`` role with the label from the `autosectionlabel extension <http://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html>`__.
