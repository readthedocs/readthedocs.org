Testing
=======

Before contributing to Read the Docs, make sure your patch passes our test suite
and your code style passes our code linting suite.

Read the Docs uses `Tox`_ to execute testing and linting procedures.
You can run tox from your :doc:`Docker development environment </development/install>`.

.. prompt:: bash

   inv docker.test

To target a specific environment:

.. prompt:: bash
   
   inv docker.test --arguments  "-e lint"

You can override any pytest's options by running the tests like:

.. prompt:: bash

   inv docker.test --arguments "-e py36 -- -x -k test_views"

See the list of available environments with:

.. prompt:: bash

   inv docker.test --arguments "-l"

.. _`Tox`: https://tox.readthedocs.io/en/latest/index.html

Pytest marks
------------

The Read the Docs code base is deployed as three instances:

- Main: where you can see the dashboard.
- Build: where the builds happen.
- Serve/proxito: It is in charge of serving the documentation pages.

Each instance has its own settings.
To make sure we test each part as close as possible to its real settings,
we use `pytest marks <https://docs.pytest.org/en/latest/mark.html>`__.
This allow us to run each set of tests with different settings files,
or skip some (like search tests)::


  DJANGO_SETTINGS_MODULE=custom.settings.file pytest -m mark
  DJANGO_SETTINGS_MODULE=another.settings.file pytest -m "not mark"

Current marks are:

- proxito (tests from the serve/proxito instance)

Tests without mark are from the main instance.

Continuous Integration
----------------------

The RTD test suite is exercised by Circle CI on every push to our repo at
GitHub. You can check out the current build status:
https://app.circleci.com/pipelines/github/readthedocs/readthedocs.org
