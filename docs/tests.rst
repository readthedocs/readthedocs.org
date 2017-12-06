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

To target a specific environment::

    tox -e py27

The ``tox`` configuration has the following environments configured. You can
target a single environment to limit the test suite::

    py27
        Run our test suite using Python 2.7

    lint
        Run code linting using `Prospector`_. This currently runs `pylint`_,
        `pyflakes`_, `pep8`_ and other linting tools.

    docs
        Test documentation compilation with Sphinx.

.. _`Tox`: http://tox.readthedocs.io/en/latest/index.html
.. _`Prospector`: http://prospector.readthedocs.io/en/master/
.. _`pylint`: http://docs.pylint.org/
.. _`pyflakes`: https://github.com/pyflakes/pyflakes
.. _`pep8`: http://pep8.readthedocs.io/en/latest/index.html

Continuous Integration
----------------------

The RTD test suite is exercised by Travis CI on every push to our repo at
GitHub. You can check out the current build status:
https://travis-ci.org/rtfd/readthedocs.org
