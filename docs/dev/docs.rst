Building and contributing to documentation
==========================================

As one might expect,
the documentation for Read the Docs is built using Sphinx and hosted on Read the Docs.
The docs are kept in the ``docs/`` directory at the top of the source tree,
and are divided into developer and user-facing documentation.

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

#. create a virtual environment with Python 3.8
   (preferably the latest release, 3.8.12 at the time of writing),
   activate it, and upgrade pip:

   .. code-block:: console

      $ cd readthedocs.org
      $ python3.8 -m venv .venv
      $ source .venv/bin/activate
      (.venv) $ python -m pip install -U pip

#. install documentation requirements

   .. code-block:: console

      (.venv) $ pip install -r requirements/testing.txt
      (.venv) $ pip install -r requirements/docs.txt

#. build the documents

   To build the user-facing documentation:

   .. code-block:: console

      (.venv) $ cd docs
      (.venv) $ make livehtml

   To build the developer documentation:

   .. code-block:: console

      (.venv) $ cd docs
      (.venv) $ RTD_DOCSET=dev make livehtml

#. the documents will be available at http://127.0.0.1:4444/ and will rebuild each time you edit and save a file.
