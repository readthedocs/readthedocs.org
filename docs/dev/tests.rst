Testing
=======

Before contributing to Read the Docs, make sure your patch passes our test suite
and your code style passes our code linting suite.

Read the Docs uses `Tox`_ to execute testing and linting procedures. Tox is the
only dependency you need to run linting or our test suite, the remainder of our
requirements will be installed by Tox into environment specific virtualenv
paths. Before testing, make sure you have Tox installed:

.. prompt:: bash

   pip install tox

Running tests
-------------

The test suite is split into separate tox environments
that match the CI pipeline:

.. prompt:: bash

   tox -e py312          # Core tests (no search, no proxito)
   tox -e search         # Search tests (requires Elasticsearch)
   tox -e proxito        # Proxito tests

To run all test suites at once:

.. prompt:: bash

   tox -e py312,search,proxito

To run a subset of tests:

.. prompt:: bash

   tox -e py312 -- -k test_celery

.. tip::

   Install ``tox-uv`` alongside tox for faster virtualenv creation
   and dependency resolution:

   .. prompt:: bash

      pip install tox tox-uv

Tox environments
~~~~~~~~~~~~~~~~

The ``tox`` configuration has the following environments configured.
You can target a single environment to limit the test suite:

py312
    Core tests — excludes search, proxito, and embed API markers.

search
    Search tests — requires an Elasticsearch instance.

proxito
    Proxito tests — uses ``readthedocs.settings.proxito.test``.

pre-commit
    Run linting and formatting checks via pre-commit.

migrations
    Check for missing Django migrations.

docs
    Build user documentation with Sphinx.

docs-dev
    Build developer documentation with Sphinx.

.. _`Tox`: https://tox.readthedocs.io/en/latest/index.html


Pytest marks
------------

The Read the Docs code base is deployed as three instances:

- Main: where you can see the dashboard.
- Build: where the builds happen.
- Serve/proxito: it is in charge of serving the documentation pages.

Each instance has its own Django settings.
To make sure we test each part as close as possible to its real settings,
we use `pytest marks <https://docs.pytest.org/en/latest/mark.html>`__
and separate tox environments.

Current marks are:

- ``search`` — tests that require Elasticsearch
- ``proxito`` — tests for the serve/proxito instance
- ``embed_api`` — tests for the embed API

Tests without a mark are from the main instance.

Continuous integration
----------------------

The CI pipeline runs on Circle CI for every push.
Tests are split into parallel jobs:

- **checks** — pre-commit linting + migration checks
- **tests** — core tests (no Elasticsearch needed)
- **tests-proxito** — proxito tests
- **tests-search** — search tests (requires Elasticsearch, runs after the above pass)
- **tests-embedapi** — embed API tests across multiple Sphinx versions

You can check out the current build status:
https://app.circleci.com/pipelines/github/readthedocs/readthedocs.org
