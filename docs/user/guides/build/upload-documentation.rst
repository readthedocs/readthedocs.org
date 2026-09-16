Uploading pre-built documentation
=================================

Read the Docs can host documentation that you build somewhere else,
for example in GitHub Actions or in any other continuous integration service.
This guide shows how to build your documentation in your own pipeline and upload the resulting files to Read the Docs.

Uploaded documentation keeps all the hosting features you already know:
:doc:`versions </versions>`, :doc:`pull request previews </pull-requests>`,
:doc:`server side search </server-side-search/index>`, :doc:`Addons </addons>`,
:doc:`custom domains </custom-domains>` and :doc:`downloadable formats </downloadable-documentation>`,
among others.

Uploading is useful when:

* Your documentation tool is not supported by the Read the Docs build process.
* Your build needs tools, secrets or resources that are only available in your own environment.
* You already build the documentation in your continuous integration pipeline and want to reuse the result.

.. note::

   Uploading pre-built documentation is enabled project by project for now.
   :doc:`Contact support </support>` to enable it on your project.

Prerequisites
-------------

* A project on Read the Docs, with uploading enabled by our support team.
* An :ref:`API token <api/v3:Token>` belonging to a user with admin access to the project.
  Store it as a secret in your continuous integration service.

.. note::

   We are working on project-scoped tokens,
   which give access to a single project instead of everything the user can access.
   They will be released soon, and we recommend switching to them once available.

Uploading from GitHub Actions
-----------------------------

Use the `Read the Docs upload action <https://github.com/readthedocs/upload-action>`__
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

         - uses: readthedocs/upload-action@main
           with:
             token: ${{ secrets.READTHEDOCS_TOKEN }}
             project-slug: <your-project-slug>
             html-dir: _build/html

.. note::

   The workflow reads the API token from a secret named ``READTHEDOCS_TOKEN``.
   Add it to your repository under :menuselection:`Settings --> Secrets and variables --> Actions`,
   or follow `GitHub's guide on using secrets <https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions>`__.

The action detects the branch, tag or pull request from the workflow event,
so a push to ``main`` updates the ``main`` version,
a new tag creates a new version,
and a pull request creates a :doc:`pull request preview </pull-requests>`.

.. warning::

   GitHub does not expose secrets to workflows triggered by pull requests from forks,
   so the upload fails on those.
   Skip the upload step on forks with a condition like
   ``if: github.event.pull_request.head.repo.full_name == github.repository``.
   Do not use ``pull_request_target`` to work around this,
   because it would run the pull request's code with access to your token.

Uploading from any other environment
------------------------------------

The action is a thin wrapper around the `Read the Docs command line client <https://github.com/readthedocs/readthedocs-cli>`__,
which you can run from any continuous integration service or from your own computer.
It requires Python 3.10 or newer and reads the token from the ``READTHEDOCS_TOKEN`` environment variable:

.. code-block:: console

   $ export READTHEDOCS_TOKEN=<token>
   $ uvx --from git+https://github.com/readthedocs/readthedocs-cli readthedocs upload \
       --project-slug <your-project-slug> \
       --html-dir _build/html

Outside GitHub Actions, the client infers the version from the local Git checkout.
On other continuous integration services, pass the version explicitly:

.. code-block:: console

   $ readthedocs upload \
       --project-slug <your-project-slug> \
       --html-dir _build/html \
       --version-name <branch, tag or pull request number> \
       --version-type <branch, tag or external> \
       --commit <full commit hash>

Run ``readthedocs upload --help`` to see all the options.

Uploading downloadable formats
------------------------------

PDF, ePub and zipped HTML files are optional, and each one points to a single file.
They are shown in the :term:`flyout menu` like any other :doc:`downloadable format </downloadable-documentation>`:

.. tabs::

   .. code-tab:: yaml GitHub Actions

      - uses: readthedocs/upload-action@main
        with:
          token: ${{ secrets.READTHEDOCS_TOKEN }}
          project-slug: <your-project-slug>
          html-dir: _build/html
          pdf: _build/latex/documentation.pdf
          epub: _build/epub/documentation.epub

   .. code-tab:: console Command line

      $ readthedocs upload \
          --project-slug <your-project-slug> \
          --html-dir _build/html \
          --pdf _build/latex/documentation.pdf \
          --epub _build/epub/documentation.epub

Limits
------

* The uploaded archive can be up to 1 GB.
* The upload has to complete within 30 minutes of starting it.
* A project can have at most 50 uploads in progress at the same time.

.. seealso::

   :doc:`/builds`
      How Read the Docs builds documentation when you don't upload it yourself.
