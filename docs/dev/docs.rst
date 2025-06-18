Building and contributing to documentation
==========================================

As one might expect,
the documentation for Read the Docs is built using Sphinx and hosted on Read the Docs.
The docs are kept in the ``docs/`` directory at the top of the source tree,
and are divided into developer and user-facing documentation.

Contributing through the GitHub UI
----------------------------------

If you're making small changes to the documentation,
you can verify those changes through the documentation generated when you open a PR and can be accessed using the GitHub UI.

#. Click the checkmark next to your commit and it will expand to have multiple options.

#. Click the "details" link next to the "docs/readthedocs.org:docs" item:

   .. image:: /img/details_link.png

#. Navigate to the section of the documentation you worked on to verify your changes.

Contributing from your local machine
------------------------------------

If you're making large changes to the documentation,
you may want to verify those changes locally before pushing upstream.

#. Clone the `readthedocs.org` repository:

   .. code-block:: console

      $ git clone --recurse-submodules https://github.com/readthedocs/readthedocs.org/

#. Create a virtual environment with Python 3.8
   (preferably the latest release),
   activate it, and upgrade pip:

   .. code-block:: console

      $ cd readthedocs.org
      $ python3.8 -m venv .venv
      $ source .venv/bin/activate
      (.venv) $ python -m pip install -U pip

#. Install the documentation requirements:

   .. code-block:: console

      (.venv) $ pip install -r requirements/testing.txt
      (.venv) $ pip install -r requirements/docs.txt

#. Build the documents:

   To build the user-facing documentation:

   .. code-block:: console

      (.venv) $ cd docs
      (.venv) $ make livehtml

   To build the developer documentation:

   .. code-block:: console

      (.venv) $ cd docs
      (.venv) $ PROJECT=dev make livehtml

#. Check the changes locally at http://127.0.0.1:4444/ (rebuilds each time you edit and save a file).
