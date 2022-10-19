Preview Documentation from Pull Requests
========================================

Your project can be configured to build and host documentation for every new
pull request. Previewing changes to your documentation during review makes it
easier to catch documentation formatting and display issues introduced in pull
requests.

Features
--------

Build on pull request events
    We create and build a new version when a pull request is opened,
    and rebuild the version whenever a new commit is pushed.

Build status report
    Your project's pull request build status will show as one of your pull
    request's checks. This status will update as the build is running, and will
    show a success or failure status when the build completes.

    .. figure:: /_static/images/github-build-status-reporting.gif
       :align: center
       :alt: GitHub build status reporting for pull requests.
       :figwidth: 80%

       GitHub build status reporting

Warning banner
    A warning banner is shown at the top of documentation pages
    to let readers know that this version isn't the main version for the project.

    .. note:: Warning banners are available only for :doc:`Sphinx projects </intro/getting-started-with-sphinx>`.

.. seealso::

   Eager to get started? Read :doc:`/guides/pull-requests`
