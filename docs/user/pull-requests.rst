Pull request previews
=====================

Your project can be configured to build and host documentation for every new
pull request. Previewing changes during review makes it
easier to catch formatting and display issues before they go live.

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

    :doc:`/guides/pull-requests`
        A guide to configuring pull request builds on Read the Docs.

Security
--------

If pull request previews are enabled for your project,
anyone who can open a pull request on your repository will be able to trigger a build of your documentation.
For this reason, pull request previews are served from a different domain than your main documentation
(``org.readthedocs.build`` and ``com.readthedocs.build``).

Builds from pull requests have access to environment variables that are marked as *Public* only,
if you have environment variables with private information, make sure they aren't marked as *Public*.
See :ref:`environment-variables:Environment variables and build process` for more information.

On |com_brand| you can set pull request previews to be private or public,
if you didn't import your project manually, the privacy level of pull request previews will match your repository.
Public pull request previews are available to anyone with the link to the preview,
while private previews are only available to users with access to the Read the Docs project.

.. warning::

   If you set the privacy level of pull request previews to *Private*,
   make sure that only trusted users can open pull requests in your repository.

   Setting pull request previews to private on a public repository can allow a malicious user
   to access read-only APIs using the user's session that is reading the pull request preview.
   Similar to `GHSA-pw32-ffxw-68rh <https://github.com/readthedocs/readthedocs.org/security/advisories/GHSA-pw32-ffxw-68rh>`__.
