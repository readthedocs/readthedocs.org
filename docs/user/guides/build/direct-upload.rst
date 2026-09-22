Direct upload
=============

Direct upload lets you build your documentation anywhere,
for example in GitHub Actions or in any other continuous integration service,
and upload the resulting files to Read the Docs for hosting.
This guide shows how to build your documentation in your own pipeline and upload it.

Documentation uploaded this way keeps all the hosting features you already know:
:doc:`versions </versions>`, :doc:`pull request previews </pull-requests>`,
:doc:`server side search </server-side-search/index>`, :doc:`Addons </addons>`,
:doc:`custom domains </custom-domains>` and :doc:`downloadable formats </offline-formats>`,
among others.

Direct upload is useful when:

* Your documentation tool is not supported by the Read the Docs build process.
* Your build needs tools, secrets or resources that are only available in your own environment.
* You already build the documentation in your continuous integration pipeline and want to reuse the result.

.. note::

   **Direct upload is currently a beta testing feature.** It has to be enabled on your project, and we ask that you give us feedback on it.
   :doc:`Contact support </support>` to enable it on your project.

Prerequisites
-------------

* A project on Read the Docs, with direct upload enabled by our support team.
* An :ref:`API token <api/v3:Token>` belonging to a user with admin access to the project.
  Store it as a secret in your continuous integration service.

.. note::

   We are working on project-scoped tokens,
   which give access to a single project instead of everything the user can access.
   They will be released soon, and we recommend switching to them once available.

Uploading from GitHub Actions
-----------------------------

Use the `upload action <https://github.com/readthedocs/upload-action>`__
after the step that builds your documentation:

.. code-block:: yaml
   :caption: .github/workflows/docs.yaml

   name: Docs

   on:
     push:
       branches: [main]
       tags: ["v*"]
     pull_request:

   jobs:
     docs:
       runs-on: ubuntu-latest
       # Pull requests from forks don't have access to secrets.
       # Do not use ``pull_request_target`` to work around this because it would run
       # the pull request's code with access to your token.
       if: github.event.pull_request.head.repo.full_name == github.repository
       steps:
         - uses: actions/checkout@v5

         # Build your documentation using the tool you are already using
         #
         # Building with Sphinx as example:
         #
         # - uses: actions/setup-python@v6
         #   with:
         #     python-version: "3.14"
         # - run: pip install -r docs/requirements.txt
         # - run: sphinx-build -b html docs/ _build/html

         - uses: readthedocs/upload-action@v1
           with:
             token: ${{ secrets.READTHEDOCS_TOKEN }}
             project-slug: <your-project-slug>
             html: _build/html

The workflow reads the API token from a secret named ``READTHEDOCS_TOKEN``.
Add it to your repository under :menuselection:`Settings --> Secrets and variables --> Actions`,
or follow `GitHub's guide on using secrets <https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions>`__.

The upload action detects the branch, tag or pull request from the workflow event,
so a push to ``main`` updates the ``main`` version,
a new tag creates a new version,
and a pull request creates a :doc:`pull request preview </pull-requests>`.


Uploading from any other environment
------------------------------------

The upload action is a thin wrapper around the `readthedocs-upload <https://pypi.org/project/readthedocs-upload/>`__ package,
a command line client that you can run from any continuous integration service or from your own computer.
It requires Python 3.10 or newer and reads the token from the ``READTHEDOCS_TOKEN`` environment variable:

.. code-block:: console

   $ export READTHEDOCS_TOKEN=<token>
   $ uvx --from readthedocs-upload readthedocs upload \
       --project-slug <your-project-slug> \
       --html _build/html

You can also install it with ``pip install readthedocs-upload``,
which makes the ``readthedocs`` command available.

Outside GitHub Actions, the client infers the version from the local Git checkout.
On other continuous integration services, pass the version explicitly:

.. code-block:: console

   $ readthedocs upload \
       --project-slug <your-project-slug> \
       --html _build/html \
       --version-name <branch, tag or pull request number> \
       --version-type <branch, tag or external> \
       --commit <full commit hash>

Run ``readthedocs upload --help`` to see all the options.

Uploading offline formats
-------------------------

PDF, ePub and zipped HTML files are optional, and each one points to a single file.
They are shown in the :term:`flyout menu` like any other :doc:`downloadable format </offline-formats>`:

.. tabs::

   .. code-tab:: yaml GitHub Actions

      - uses: readthedocs/upload-action@v1
        with:
          token: ${{ secrets.READTHEDOCS_TOKEN }}
          project-slug: <your-project-slug>
          html: _build/html
          pdf: _build/latex/documentation.pdf
          epub: _build/epub/documentation.epub

   .. code-tab:: console Command line

      $ readthedocs upload \
          --project-slug <your-project-slug> \
          --html _build/html \
          --pdf _build/latex/documentation.pdf \
          --epub _build/epub/documentation.epub

Limits
------

* The uploaded archive can be up to 1 GB.
* The upload has to complete within 30 minutes of starting it.
* A project can have at most 50 uploads in progress at the same time.

.. seealso::

   :doc:`/builds`
      How Read the Docs builds documentation when you don't use direct upload.
