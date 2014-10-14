Running tests
=============

Read the Docs ships with a test suite that tests the application. You should run these tests when you are doing development before committing code.

They can be run easily::

    pip install coverage 
    ./runtests.sh

This should print out a bunch of information and pass with 0 errors.

Continuous Integration
----------------------

The RTD test suite is exercised by Travis CI on every push to our repo at
GitHub. You can check out the current build status:
https://travis-ci.org/rtfd/readthedocs.org
