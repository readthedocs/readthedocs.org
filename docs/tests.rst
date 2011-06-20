Running tests
=============

Currently RTD isn't well tested. This is a problem, and it is being worked on. However, we do have a basic test suite. To run the tests, you need simply need to run::

    ./manage.py test rtd_tests

This should spit out a bunch of info, build a couple projects, and eventually pass.

Continuous Integration
----------------------

The fine folks over at `Django CMS <https://www.django-cms.org/>`_ have been nice enough to sponsor our CI setup on their hudson instance. You can check out the current build status: http://ci.django-cms.org/job/readthedocs.org/
