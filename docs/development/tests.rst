Testing
=======

Before contributing to Read the Docs, make sure your patch passes our test suite
and your code style passes our code linting suite.

Read the Docs uses `Tox`_ to execute testing and linting procedures. Tox is the
only dependency you need to run linting or our test suite, the remainder of our
requirements will be installed by Tox into environment specific virtualenv
paths. Before testing, make sure you have Tox installed::

    pip install tox

To run the full test and lint suite against your changes, simply run Tox. Tox
should return without any errors. You can run Tox against all of our
environments by running::

    tox

By default, tox won't run tests from search,
in order to run all test including the search tests,
you need to override tox's posargs.
If you don't have any additional arguments to pass,
you can also set the ``TOX_POSARGS`` environment variable to an empty string::

    TOX_POSARGS='' tox

.. note::

   If you need to override tox's posargs, but you still don't want to run the search tests,
   you need to include ``-m 'not search'`` to your command::

       tox -- -m 'not search' -x

.. warning::

   Running tests for search needs an Elasticsearch :ref:`instance running locally <development/search:Installing and running Elasticsearch>`.

To target a specific environment::

    tox -e py36

The ``tox`` configuration has the following environments configured. You can
target a single environment to limit the test suite:

py36
    Run our test suite using Python 3.6

lint
    Run code linting using `Prospector`_. This currently runs `pylint`_,
    `pyflakes`_, `pep8`_ and other linting tools.

docs
    Test documentation compilation with Sphinx.

.. _`Tox`: https://tox.readthedocs.io/en/latest/index.html
.. _`Prospector`: https://prospector.readthedocs.io/en/master/
.. _`pylint`: https://pylint.readthedocs.io/
.. _`pyflakes`: https://github.com/pyflakes/pyflakes
.. _`pep8`: https://pep8.readthedocs.io/en/latest/index.html


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

- search (tests that require Elastic Search)
- proxito (tests from the serve/proxito instance)

Tests without mark are from the main instance.

Continuous Integration
----------------------

The RTD test suite is exercised by Travis CI on every push to our repo at
GitHub. You can check out the current build status:
https://travis-ci.org/readthedocs/readthedocs.org
