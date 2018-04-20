Version 2.3.7
-------------

:Date: April 19, 2018

* `@humitos <http://github.com/humitos>`_: Fix server_error_500 path on single version (`#3975 <https://github.com/rtfd/readthedocs.org/pull/3975>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Fix bookmark app lint failures (`#3969 <https://github.com/rtfd/readthedocs.org/pull/3969>`_)
* `@humitos <http://github.com/humitos>`_: Use latest setuptools (39.0.1) by default on build process (`#3967 <https://github.com/rtfd/readthedocs.org/pull/3967>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Fix exact redirects. (`#3965 <https://github.com/rtfd/readthedocs.org/pull/3965>`_)
* `@humitos <http://github.com/humitos>`_: Make `resolve_domain` work when a project is subproject of itself (`#3962 <https://github.com/rtfd/readthedocs.org/pull/3962>`_)
* `@humitos <http://github.com/humitos>`_: Remove django-celery-beat and use the default scheduler (`#3959 <https://github.com/rtfd/readthedocs.org/pull/3959>`_)
* `@xrmx <http://github.com/xrmx>`_: Fix some tests with postgres (`#3958 <https://github.com/rtfd/readthedocs.org/pull/3958>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Add advertising details docs (`#3955 <https://github.com/rtfd/readthedocs.org/pull/3955>`_)
* `@humitos <http://github.com/humitos>`_: Use pur to upgrade python packages (`#3953 <https://github.com/rtfd/readthedocs.org/pull/3953>`_)
* `@ze <http://github.com/ze>`_: Make adjustments to Projects page (`#3948 <https://github.com/rtfd/readthedocs.org/pull/3948>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Small change to Chinese language names (`#3947 <https://github.com/rtfd/readthedocs.org/pull/3947>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Don't share state in build task (`#3946 <https://github.com/rtfd/readthedocs.org/pull/3946>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Fixed footer ad width fix (`#3944 <https://github.com/rtfd/readthedocs.org/pull/3944>`_)
* `@humitos <http://github.com/humitos>`_: Allow extend Translation and Subproject form logic from corporate (`#3937 <https://github.com/rtfd/readthedocs.org/pull/3937>`_)
* `@humitos <http://github.com/humitos>`_: Resync valid webhook for project manually imported (`#3935 <https://github.com/rtfd/readthedocs.org/pull/3935>`_)
* `@humitos <http://github.com/humitos>`_: Resync webhooks from Admin (`#3933 <https://github.com/rtfd/readthedocs.org/pull/3933>`_)
* `@humitos <http://github.com/humitos>`_: Fix attribute order call (`#3930 <https://github.com/rtfd/readthedocs.org/pull/3930>`_)
* `@humitos <http://github.com/humitos>`_: Mention RTD in the Project URL of the issue template (`#3928 <https://github.com/rtfd/readthedocs.org/pull/3928>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Correctly report mkdocs theme name (`#3920 <https://github.com/rtfd/readthedocs.org/pull/3920>`_)
* `@xrmx <http://github.com/xrmx>`_: Fixup DJANGO_SETTINGS_SKIP_LOCAL in tests (`#3899 <https://github.com/rtfd/readthedocs.org/pull/3899>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Show an adblock admonition in the dev console (`#3894 <https://github.com/rtfd/readthedocs.org/pull/3894>`_)
* `@stsewd <http://github.com/stsewd>`_: Fix view docs link (`#3882 <https://github.com/rtfd/readthedocs.org/pull/3882>`_)
* `@xrmx <http://github.com/xrmx>`_: templates: mark a few more strings for translations (`#3869 <https://github.com/rtfd/readthedocs.org/pull/3869>`_)
* `@ze <http://github.com/ze>`_: Update quickstart from README (`#3847 <https://github.com/rtfd/readthedocs.org/pull/3847>`_)
* `@vidartf <http://github.com/vidartf>`_: Fix page redirect preview (`#3811 <https://github.com/rtfd/readthedocs.org/pull/3811>`_)
* `@stsewd <http://github.com/stsewd>`_: [RDY] Fix requirements file lookup (`#3800 <https://github.com/rtfd/readthedocs.org/pull/3800>`_)
* `@aasis21 <http://github.com/aasis21>`_: Documentation for build notifications using webhooks. (`#3671 <https://github.com/rtfd/readthedocs.org/pull/3671>`_)
* `@mashrikt <http://github.com/mashrikt>`_: [#2967] Scheduled tasks for cleaning up messages (`#3604 <https://github.com/rtfd/readthedocs.org/pull/3604>`_)
* `@stsewd <http://github.com/stsewd>`_: Show URLS for exact redirect (`#3593 <https://github.com/rtfd/readthedocs.org/pull/3593>`_)
* `@marcelstoer <http://github.com/marcelstoer>`_: Doc builder template should check for mkdocs_page_input_path before using it (`#3536 <https://github.com/rtfd/readthedocs.org/pull/3536>`_)
* `@Code0x58 <http://github.com/Code0x58>`_: Document creation of slumber user (`#3461 <https://github.com/rtfd/readthedocs.org/pull/3461>`_)

Version 2.3.6
-------------

:Date: April 05, 2018

* `@agjohnson <http://github.com/agjohnson>`_: Drop readthedocs- prefix to submodule (`#3916 <https://github.com/rtfd/readthedocs.org/pull/3916>`_)
* `@agjohnson <http://github.com/agjohnson>`_: This fixes two bugs apparent in nesting of translations in subprojects (`#3909 <https://github.com/rtfd/readthedocs.org/pull/3909>`_)
* `@humitos <http://github.com/humitos>`_: Use new django celery beat scheduler (`#3908 <https://github.com/rtfd/readthedocs.org/pull/3908>`_)
* `@humitos <http://github.com/humitos>`_: Use a proper default for `docker` attribute on UpdateDocsTask (`#3907 <https://github.com/rtfd/readthedocs.org/pull/3907>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Handle errors from publish_parts (`#3905 <https://github.com/rtfd/readthedocs.org/pull/3905>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Drop pdbpp from testing requirements (`#3904 <https://github.com/rtfd/readthedocs.org/pull/3904>`_)
* `@stsewd <http://github.com/stsewd>`_: Little improve on sync_versions (`#3902 <https://github.com/rtfd/readthedocs.org/pull/3902>`_)
* `@humitos <http://github.com/humitos>`_: Save Docker image data in JSON file only for DockerBuildEnvironment (`#3897 <https://github.com/rtfd/readthedocs.org/pull/3897>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Single analytics file for all builders (`#3896 <https://github.com/rtfd/readthedocs.org/pull/3896>`_)
* `@humitos <http://github.com/humitos>`_: Organize logging levels (`#3893 <https://github.com/rtfd/readthedocs.org/pull/3893>`_)

Version 2.3.5
-------------

:Date: April 05, 2018

* `@agjohnson <http://github.com/agjohnson>`_: Drop pdbpp from testing requirements (`#3904 <https://github.com/rtfd/readthedocs.org/pull/3904>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Resolve subproject correctly in the case of single version (`#3901 <https://github.com/rtfd/readthedocs.org/pull/3901>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Fixed footer ads again (`#3895 <https://github.com/rtfd/readthedocs.org/pull/3895>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Fix an Alabaster ad positioning issue (`#3889 <https://github.com/rtfd/readthedocs.org/pull/3889>`_)
* `@humitos <http://github.com/humitos>`_: Save Docker image hash in RTD environment.json file (`#3880 <https://github.com/rtfd/readthedocs.org/pull/3880>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Add ref links for easier intersphinx on yaml config page (`#3877 <https://github.com/rtfd/readthedocs.org/pull/3877>`_)
* `@rajujha373 <http://github.com/rajujha373>`_: Typo correction in docs/features.rst (`#3872 <https://github.com/rtfd/readthedocs.org/pull/3872>`_)
* `@gaborbernat <http://github.com/gaborbernat>`_: add description for tox tasks (`#3868 <https://github.com/rtfd/readthedocs.org/pull/3868>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Another CORS hotfix for the sustainability API (`#3862 <https://github.com/rtfd/readthedocs.org/pull/3862>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Fix up some of the logic around repo and submodule URLs (`#3860 <https://github.com/rtfd/readthedocs.org/pull/3860>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Fix linting errors in tests (`#3855 <https://github.com/rtfd/readthedocs.org/pull/3855>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Use gitpython to find a commit reference (`#3843 <https://github.com/rtfd/readthedocs.org/pull/3843>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Remove pinned CSS Select version (`#3813 <https://github.com/rtfd/readthedocs.org/pull/3813>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Use JSONP for sustainability API (`#3789 <https://github.com/rtfd/readthedocs.org/pull/3789>`_)
* `@rajujha373 <http://github.com/rajujha373>`_: #3718: Added date to changelog (`#3788 <https://github.com/rtfd/readthedocs.org/pull/3788>`_)
* `@xrmx <http://github.com/xrmx>`_: tests: mock test_conf_file_not_found filesystem access (`#3740 <https://github.com/rtfd/readthedocs.org/pull/3740>`_)

.. _version-2.3.4:

Version 2.3.4
-------------

* Release for static assets

Version 2.3.3
-------------

* `@davidfischer <http://github.com/davidfischer>`_: Fix linting errors in tests (`#3855 <https://github.com/rtfd/readthedocs.org/pull/3855>`_)
* `@humitos <http://github.com/humitos>`_: Fix linting issues (`#3838 <https://github.com/rtfd/readthedocs.org/pull/3838>`_)
* `@humitos <http://github.com/humitos>`_: Update instance and model when `record_as_success` (`#3831 <https://github.com/rtfd/readthedocs.org/pull/3831>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Reorder GSOC projects, and note priority order (`#3823 <https://github.com/rtfd/readthedocs.org/pull/3823>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Add temporary method for skipping submodule checkout (`#3821 <https://github.com/rtfd/readthedocs.org/pull/3821>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Remove pinned CSS Select version (`#3813 <https://github.com/rtfd/readthedocs.org/pull/3813>`_)
* `@humitos <http://github.com/humitos>`_: Use readthedocs-common to share linting files accross different repos (`#3808 <https://github.com/rtfd/readthedocs.org/pull/3808>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Use JSONP for sustainability API (`#3789 <https://github.com/rtfd/readthedocs.org/pull/3789>`_)
* `@humitos <http://github.com/humitos>`_: Define useful celery beat task for development (`#3762 <https://github.com/rtfd/readthedocs.org/pull/3762>`_)
* `@humitos <http://github.com/humitos>`_: Auto-generate conf.py compatible with Py2 and Py3 (`#3745 <https://github.com/rtfd/readthedocs.org/pull/3745>`_)
* `@humitos <http://github.com/humitos>`_: Task to remove orphan symlinks (`#3543 <https://github.com/rtfd/readthedocs.org/pull/3543>`_)
* `@stsewd <http://github.com/stsewd>`_: Fix regex for public bitbucket repo (`#3533 <https://github.com/rtfd/readthedocs.org/pull/3533>`_)
* `@humitos <http://github.com/humitos>`_: Documentation for RTD context sent to the Sphinx theme (`#3490 <https://github.com/rtfd/readthedocs.org/pull/3490>`_)
* `@stsewd <http://github.com/stsewd>`_: Show link to docs on a build (`#3446 <https://github.com/rtfd/readthedocs.org/pull/3446>`_)

Version 2.3.2
-------------

This version adds a hotfix branch that adds model validation to the repository
URL to ensure strange URL patterns can't be used.

Version 2.3.1
-------------

* `@humitos <http://github.com/humitos>`_: Update instance and model when `record_as_success` (`#3831 <https://github.com/rtfd/readthedocs.org/pull/3831>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Bump docker -> 3.1.3 (`#3828 <https://github.com/rtfd/readthedocs.org/pull/3828>`_)
* `@Doug-AWS <http://github.com/Doug-AWS>`_: Pip install note for Windows (`#3827 <https://github.com/rtfd/readthedocs.org/pull/3827>`_)
* `@himanshutejwani12 <http://github.com/himanshutejwani12>`_: Update index.rst (`#3824 <https://github.com/rtfd/readthedocs.org/pull/3824>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Reorder GSOC projects, and note priority order (`#3823 <https://github.com/rtfd/readthedocs.org/pull/3823>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Autolint cleanup for #3821 (`#3822 <https://github.com/rtfd/readthedocs.org/pull/3822>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Add temporary method for skipping submodule checkout (`#3821 <https://github.com/rtfd/readthedocs.org/pull/3821>`_)
* `@stsewd <http://github.com/stsewd>`_: Pin astroid to fix linter issue on travis (`#3816 <https://github.com/rtfd/readthedocs.org/pull/3816>`_)
* `@varunotelli <http://github.com/varunotelli>`_: Update install.rst dropped the Python 2.7 only part (`#3814 <https://github.com/rtfd/readthedocs.org/pull/3814>`_)
* `@xrmx <http://github.com/xrmx>`_: Update machine field when activating a version from project_version_detail (`#3797 <https://github.com/rtfd/readthedocs.org/pull/3797>`_)
* `@humitos <http://github.com/humitos>`_: Allow members of "Admin" Team to wipe version envs (`#3791 <https://github.com/rtfd/readthedocs.org/pull/3791>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Add sustainability api to CORS (`#3782 <https://github.com/rtfd/readthedocs.org/pull/3782>`_)
* `@durwasa-chakraborty <http://github.com/durwasa-chakraborty>`_: Fixed a grammatical error (`#3780 <https://github.com/rtfd/readthedocs.org/pull/3780>`_)
* `@humitos <http://github.com/humitos>`_: Trying to solve the end line character for a font file (`#3776 <https://github.com/rtfd/readthedocs.org/pull/3776>`_)
* `@stsewd <http://github.com/stsewd>`_: Fix tox env for coverage (`#3772 <https://github.com/rtfd/readthedocs.org/pull/3772>`_)
* `@bansalnitish <http://github.com/bansalnitish>`_: Added eslint rules (`#3768 <https://github.com/rtfd/readthedocs.org/pull/3768>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Use sustainability api for advertising (`#3747 <https://github.com/rtfd/readthedocs.org/pull/3747>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Add a sustainability API (`#3672 <https://github.com/rtfd/readthedocs.org/pull/3672>`_)
* `@humitos <http://github.com/humitos>`_: Upgrade django-pagination to a "maintained" fork (`#3666 <https://github.com/rtfd/readthedocs.org/pull/3666>`_)
* `@humitos <http://github.com/humitos>`_: Project updated when subproject modified (`#3649 <https://github.com/rtfd/readthedocs.org/pull/3649>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Anonymize IP addresses for Google Analytics (`#3626 <https://github.com/rtfd/readthedocs.org/pull/3626>`_)
* `@humitos <http://github.com/humitos>`_: Improve "Sharing" docs (`#3472 <https://github.com/rtfd/readthedocs.org/pull/3472>`_)
* `@humitos <http://github.com/humitos>`_: Upgrade docker-py to its latest version (docker==3.1.1) (`#3243 <https://github.com/rtfd/readthedocs.org/pull/3243>`_)
* `@humitos <http://github.com/humitos>`_: Upgrade all packages using `pur` tool (`#2916 <https://github.com/rtfd/readthedocs.org/pull/2916>`_)
* `@rixx <http://github.com/rixx>`_: Fix page redirect preview (`#2711 <https://github.com/rtfd/readthedocs.org/pull/2711>`_)

.. _version-2.3.0:

Version 2.3.0
-------------

.. warning::
    Version 2.3.0 includes a security fix for project translations. See
    :ref:`security-2.3.0` for more information

* `@stsewd <http://github.com/stsewd>`_: Fix tox env for coverage (`#3772 <https://github.com/rtfd/readthedocs.org/pull/3772>`_)
* `@humitos <http://github.com/humitos>`_: Try to fix end of file (`#3761 <https://github.com/rtfd/readthedocs.org/pull/3761>`_)
* `@berkerpeksag <http://github.com/berkerpeksag>`_: Fix indentation in docs/faq.rst (`#3758 <https://github.com/rtfd/readthedocs.org/pull/3758>`_)
* `@stsewd <http://github.com/stsewd>`_: Check for http protocol before urlize (`#3755 <https://github.com/rtfd/readthedocs.org/pull/3755>`_)
* `@rajujha373 <http://github.com/rajujha373>`_: #3741: replaced Go Crazy text with Search (`#3752 <https://github.com/rtfd/readthedocs.org/pull/3752>`_)
* `@humitos <http://github.com/humitos>`_: Log in the proper place and add the image name used (`#3750 <https://github.com/rtfd/readthedocs.org/pull/3750>`_)
* `@shubham76 <http://github.com/shubham76>`_: Changed 'Submit' text on buttons with something more meaningful (`#3749 <https://github.com/rtfd/readthedocs.org/pull/3749>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Fix tests for Git submodule (`#3737 <https://github.com/rtfd/readthedocs.org/pull/3737>`_)
* `@bansalnitish <http://github.com/bansalnitish>`_: Add eslint rules and fix errors (`#3726 <https://github.com/rtfd/readthedocs.org/pull/3726>`_)
* `@davidfischer <http://github.com/davidfischer>`_: Prevent bots indexing promos (`#3719 <https://github.com/rtfd/readthedocs.org/pull/3719>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Add argument to skip errorlist through knockout on common form (`#3704 <https://github.com/rtfd/readthedocs.org/pull/3704>`_)
* `@ajatprabha <http://github.com/ajatprabha>`_: Fixed #3701: added closing tag for div element (`#3702 <https://github.com/rtfd/readthedocs.org/pull/3702>`_)
* `@bansalnitish <http://github.com/bansalnitish>`_: Fixes internal reference (`#3695 <https://github.com/rtfd/readthedocs.org/pull/3695>`_)
* `@humitos <http://github.com/humitos>`_: Always record the git branch command as success (`#3693 <https://github.com/rtfd/readthedocs.org/pull/3693>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Show the project slug in the project admin (to make it more explicit what project is what) (`#3681 <https://github.com/rtfd/readthedocs.org/pull/3681>`_)
* `@humitos <http://github.com/humitos>`_: Upgrade django-taggit to 0.22.2 (`#3667 <https://github.com/rtfd/readthedocs.org/pull/3667>`_)
* `@stsewd <http://github.com/stsewd>`_: Check for submodules (`#3661 <https://github.com/rtfd/readthedocs.org/pull/3661>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Hotfix for adding logging call back into project sync task (`#3657 <https://github.com/rtfd/readthedocs.org/pull/3657>`_)
* `@agjohnson <http://github.com/agjohnson>`_: Fix issue with missing setting in oauth SyncRepo task (`#3656 <https://github.com/rtfd/readthedocs.org/pull/3656>`_)
* `@ericholscher <http://github.com/ericholscher>`_: Remove error logging that isn't an error. (`#3650 <https://github.com/rtfd/readthedocs.org/pull/3650>`_)
* `@humitos <http://github.com/humitos>`_: Project updated when subproject modified (`#3649 <https://github.com/rtfd/readthedocs.org/pull/3649>`_)
* `@aasis21 <http://github.com/aasis21>`_: formatting buttons in edit project text editor (`#3633 <https://github.com/rtfd/readthedocs.org/pull/3633>`_)
* `@humitos <http://github.com/humitos>`_: Filter by my own repositories at Import Remote Project (`#3548 <https://github.com/rtfd/readthedocs.org/pull/3548>`_)
* `@funkyHat <http://github.com/funkyHat>`_: check for matching alias before subproject slug (`#2787 <https://github.com/rtfd/readthedocs.org/pull/2787>`_)

Version 2.2.1
-------------

Version ``2.2.1`` is a bug fix release for the several issues found in
production during the ``2.2.0`` release.

 * `@agjohnson <http://github.com/agjohnson>`_: Hotfix for adding logging call back into project sync task (`#3657 <https://github.com/rtfd/readthedocs.org/pull/3657>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Fix issue with missing setting in oauth SyncRepo task (`#3656 <https://github.com/rtfd/readthedocs.org/pull/3656>`_)
 * `@humitos <http://github.com/humitos>`_: Tests for build notifications (`#3654 <https://github.com/rtfd/readthedocs.org/pull/3654>`_)
 * `@humitos <http://github.com/humitos>`_: Send proper context to celery email notification task (`#3653 <https://github.com/rtfd/readthedocs.org/pull/3653>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Remove error logging that isn't an error. (`#3650 <https://github.com/rtfd/readthedocs.org/pull/3650>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Update RTD security docs (`#3641 <https://github.com/rtfd/readthedocs.org/pull/3641>`_)
 * `@humitos <http://github.com/humitos>`_: Ability to override the creation of the Celery App (`#3623 <https://github.com/rtfd/readthedocs.org/pull/3623>`_)

Version 2.2.0
-------------

 * `@humitos <http://github.com/humitos>`_: Tests for build notifications (`#3654 <https://github.com/rtfd/readthedocs.org/pull/3654>`_)
 * `@humitos <http://github.com/humitos>`_: Send proper context to celery email notification task (`#3653 <https://github.com/rtfd/readthedocs.org/pull/3653>`_)
 * `@xrmx <http://github.com/xrmx>`_: Update django-formtools to 2.1 (`#3648 <https://github.com/rtfd/readthedocs.org/pull/3648>`_)
 * `@xrmx <http://github.com/xrmx>`_: Update Django to 1.9.13 (`#3647 <https://github.com/rtfd/readthedocs.org/pull/3647>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Fix a 500 when searching for files with API v1 (`#3645 <https://github.com/rtfd/readthedocs.org/pull/3645>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Update RTD security docs (`#3641 <https://github.com/rtfd/readthedocs.org/pull/3641>`_)
 * `@humitos <http://github.com/humitos>`_: Fix SVN initialization for command logging (`#3638 <https://github.com/rtfd/readthedocs.org/pull/3638>`_)
 * `@humitos <http://github.com/humitos>`_: Ability to override the creation of the Celery App (`#3623 <https://github.com/rtfd/readthedocs.org/pull/3623>`_)
 * `@humitos <http://github.com/humitos>`_: Update the operations team (`#3621 <https://github.com/rtfd/readthedocs.org/pull/3621>`_)
 * `@mohitkyadav <http://github.com/mohitkyadav>`_: Add venv to .gitignore (`#3620 <https://github.com/rtfd/readthedocs.org/pull/3620>`_)
 * `@stsewd <http://github.com/stsewd>`_: Remove hardcoded copyright year (`#3616 <https://github.com/rtfd/readthedocs.org/pull/3616>`_)
 * `@stsewd <http://github.com/stsewd>`_: Improve installation steps (`#3614 <https://github.com/rtfd/readthedocs.org/pull/3614>`_)
 * `@stsewd <http://github.com/stsewd>`_: Update GSOC (`#3607 <https://github.com/rtfd/readthedocs.org/pull/3607>`_)
 * `@Jigar3 <http://github.com/Jigar3>`_: Updated AUTHORS.rst (`#3601 <https://github.com/rtfd/readthedocs.org/pull/3601>`_)
 * `@stsewd <http://github.com/stsewd>`_: Pin less to latest compatible version (`#3597 <https://github.com/rtfd/readthedocs.org/pull/3597>`_)
 * `@Angeles4four <http://github.com/Angeles4four>`_: Grammar correction (`#3596 <https://github.com/rtfd/readthedocs.org/pull/3596>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Fix an unclosed tag (`#3592 <https://github.com/rtfd/readthedocs.org/pull/3592>`_)
 * `@aaksarin <http://github.com/aaksarin>`_: add missed fontawesome-webfont.woff2 (`#3589 <https://github.com/rtfd/readthedocs.org/pull/3589>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Force a specific ad to be displayed (`#3584 <https://github.com/rtfd/readthedocs.org/pull/3584>`_)
 * `@stsewd <http://github.com/stsewd>`_: Docs about preference for tags over branches (`#3582 <https://github.com/rtfd/readthedocs.org/pull/3582>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Rework homepage (`#3579 <https://github.com/rtfd/readthedocs.org/pull/3579>`_)
 * `@stsewd <http://github.com/stsewd>`_: Don't allow to create a subproject of a project itself  (`#3571 <https://github.com/rtfd/readthedocs.org/pull/3571>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Fix for build screen in firefox (`#3569 <https://github.com/rtfd/readthedocs.org/pull/3569>`_)
 * `@humitos <http://github.com/humitos>`_: Style using pre-commit (`#3560 <https://github.com/rtfd/readthedocs.org/pull/3560>`_)
 * `@humitos <http://github.com/humitos>`_: Use DRF 3.1 `pagination_class` (`#3559 <https://github.com/rtfd/readthedocs.org/pull/3559>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Analytics fixes (`#3558 <https://github.com/rtfd/readthedocs.org/pull/3558>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Upgrade requests version (`#3557 <https://github.com/rtfd/readthedocs.org/pull/3557>`_)
 * `@humitos <http://github.com/humitos>`_: Mount `pip_cache_path` in Docker container (`#3556 <https://github.com/rtfd/readthedocs.org/pull/3556>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Add a number of new ideas for GSOC (`#3552 <https://github.com/rtfd/readthedocs.org/pull/3552>`_)
 * `@humitos <http://github.com/humitos>`_: Fix Travis lint issue (`#3551 <https://github.com/rtfd/readthedocs.org/pull/3551>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Send custom dimensions for mkdocs (`#3550 <https://github.com/rtfd/readthedocs.org/pull/3550>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Promo contrast improvements (`#3549 <https://github.com/rtfd/readthedocs.org/pull/3549>`_)
 * `@humitos <http://github.com/humitos>`_: Allow git tags with `/` in the name and properly slugify (`#3545 <https://github.com/rtfd/readthedocs.org/pull/3545>`_)
 * `@humitos <http://github.com/humitos>`_: Allow to import public repositories on corporate site (`#3537 <https://github.com/rtfd/readthedocs.org/pull/3537>`_)
 * `@humitos <http://github.com/humitos>`_: Log `git checkout` and expose to users (`#3520 <https://github.com/rtfd/readthedocs.org/pull/3520>`_)
 * `@stsewd <http://github.com/stsewd>`_: Update docs (`#3498 <https://github.com/rtfd/readthedocs.org/pull/3498>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Switch to universal analytics (`#3495 <https://github.com/rtfd/readthedocs.org/pull/3495>`_)
 * `@stsewd <http://github.com/stsewd>`_: Move Mercurial dependency to pip.txt (`#3488 <https://github.com/rtfd/readthedocs.org/pull/3488>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Add docs on removing edit button (`#3479 <https://github.com/rtfd/readthedocs.org/pull/3479>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Convert default dev cache to local memory (`#3477 <https://github.com/rtfd/readthedocs.org/pull/3477>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Fix lint error (`#3402 <https://github.com/rtfd/readthedocs.org/pull/3402>`_)
 * `@techtonik <http://github.com/techtonik>`_: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/rtfd/readthedocs.org/pull/3302>`_)
 * `@jaraco <http://github.com/jaraco>`_: Fixed build results page on firefox (part two) (`#2630 <https://github.com/rtfd/readthedocs.org/pull/2630>`_)

Version 2.1.6
-------------

 * `@davidfischer <http://github.com/davidfischer>`_: Promo contrast improvements (`#3549 <https://github.com/rtfd/readthedocs.org/pull/3549>`_)
 * `@humitos <http://github.com/humitos>`_: Refactor run command outside a Build and Environment (`#3542 <https://github.com/rtfd/readthedocs.org/issues/3542>`_)
 * `@AnatoliyURL <http://github.com/AnatoliyURL>`_: Project in the local read the docs don't see tags. (`#3534 <https://github.com/rtfd/readthedocs.org/issues/3534>`_)
 * `@malarzm <http://github.com/malarzm>`_: searchtools.js missing init() call (`#3532 <https://github.com/rtfd/readthedocs.org/issues/3532>`_)
 * `@johanneskoester <http://github.com/johanneskoester>`_: Build failed without details (`#3531 <https://github.com/rtfd/readthedocs.org/issues/3531>`_)
 * `@danielmitterdorfer <http://github.com/danielmitterdorfer>`_: "Edit on Github" points to non-existing commit (`#3530 <https://github.com/rtfd/readthedocs.org/issues/3530>`_)
 * `@lk-geimfari <http://github.com/lk-geimfari>`_: No such file or directory: 'docs/requirements.txt' (`#3529 <https://github.com/rtfd/readthedocs.org/issues/3529>`_)
 * `@stsewd <http://github.com/stsewd>`_: Fix Good First Issue link (`#3522 <https://github.com/rtfd/readthedocs.org/pull/3522>`_)
 * `@Blendify <http://github.com/Blendify>`_: Remove RTD Theme workaround (`#3519 <https://github.com/rtfd/readthedocs.org/pull/3519>`_)
 * `@stsewd <http://github.com/stsewd>`_: Move project description to the top (`#3510 <https://github.com/rtfd/readthedocs.org/pull/3510>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Switch to universal analytics (`#3495 <https://github.com/rtfd/readthedocs.org/pull/3495>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Convert default dev cache to local memory (`#3477 <https://github.com/rtfd/readthedocs.org/pull/3477>`_)
 * `@nlgranger <http://github.com/nlgranger>`_: Github service: cannot unlink after deleting account (`#3374 <https://github.com/rtfd/readthedocs.org/issues/3374>`_)
 * `@andrewgodwin <http://github.com/andrewgodwin>`_: "stable" appearing to track future release branches (`#3268 <https://github.com/rtfd/readthedocs.org/issues/3268>`_)
 * `@skddc <http://github.com/skddc>`_: Add JSDoc to docs build environment (`#3069 <https://github.com/rtfd/readthedocs.org/issues/3069>`_)
 * `@chummels <http://github.com/chummels>`_: RTD building old "stable" docs instead of "latest" when auto-triggered from recent push (`#2351 <https://github.com/rtfd/readthedocs.org/issues/2351>`_)
 * `@cajus <http://github.com/cajus>`_: Builds get stuck in "Cloning" state (`#2047 <https://github.com/rtfd/readthedocs.org/issues/2047>`_)
 * `@gossi <http://github.com/gossi>`_: Cannot delete subproject (`#1341 <https://github.com/rtfd/readthedocs.org/issues/1341>`_)
 * `@gigster99 <http://github.com/gigster99>`_: extension problem (`#1059 <https://github.com/rtfd/readthedocs.org/issues/1059>`_)

Version 2.1.5
-------------

 * `@ericholscher <http://github.com/ericholscher>`_: Add GSOC 2018 page (`#3518 <https://github.com/rtfd/readthedocs.org/pull/3518>`_)
 * `@stsewd <http://github.com/stsewd>`_: Move project description to the top (`#3510 <https://github.com/rtfd/readthedocs.org/pull/3510>`_)
 * `@RichardLitt <http://github.com/RichardLitt>`_: Docs: Rename "Good First Bug" to "Good First Issue" (`#3505 <https://github.com/rtfd/readthedocs.org/pull/3505>`_)
 * `@stsewd <http://github.com/stsewd>`_: Fix regex for getting project and user (`#3501 <https://github.com/rtfd/readthedocs.org/pull/3501>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Check to make sure changes exist in BitBucket pushes (`#3480 <https://github.com/rtfd/readthedocs.org/pull/3480>`_)
 * `@andrewgodwin <http://github.com/andrewgodwin>`_: "stable" appearing to track future release branches (`#3268 <https://github.com/rtfd/readthedocs.org/issues/3268>`_)
 * `@cdeil <http://github.com/cdeil>`_: No module named pip in conda build (`#2827 <https://github.com/rtfd/readthedocs.org/issues/2827>`_)
 * `@Yaseenh <http://github.com/Yaseenh>`_: building project does not generate new pdf with changes in it (`#2758 <https://github.com/rtfd/readthedocs.org/issues/2758>`_)
 * `@chummels <http://github.com/chummels>`_: RTD building old "stable" docs instead of "latest" when auto-triggered from recent push (`#2351 <https://github.com/rtfd/readthedocs.org/issues/2351>`_)
 * `@KeithWoods <http://github.com/KeithWoods>`_: GitHub edit link is aggressively stripped (`#1788 <https://github.com/rtfd/readthedocs.org/issues/1788>`_)

Version 2.1.4
-------------

 * `@davidfischer <http://github.com/davidfischer>`_: Add programming language to API/READTHEDOCS_DATA (`#3499 <https://github.com/rtfd/readthedocs.org/pull/3499>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Remove our mkdocs search override (`#3496 <https://github.com/rtfd/readthedocs.org/pull/3496>`_)
 * `@humitos <http://github.com/humitos>`_: Better style (`#3494 <https://github.com/rtfd/readthedocs.org/pull/3494>`_)
 * `@humitos <http://github.com/humitos>`_: Update README.rst (`#3492 <https://github.com/rtfd/readthedocs.org/pull/3492>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Small formatting change to the Alabaster footer (`#3491 <https://github.com/rtfd/readthedocs.org/pull/3491>`_)
 * `@matsen <http://github.com/matsen>`_: Fixing "reseting" misspelling. (`#3487 <https://github.com/rtfd/readthedocs.org/pull/3487>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Add David to dev team listing (`#3485 <https://github.com/rtfd/readthedocs.org/pull/3485>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Check to make sure changes exist in BitBucket pushes (`#3480 <https://github.com/rtfd/readthedocs.org/pull/3480>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Use semvar for readthedocs-build to make bumping easier (`#3475 <https://github.com/rtfd/readthedocs.org/pull/3475>`_)
 * `@davidfischer <http://github.com/davidfischer>`_: Add programming languages (`#3471 <https://github.com/rtfd/readthedocs.org/pull/3471>`_)
 * `@humitos <http://github.com/humitos>`_: Remove TEMPLATE_LOADERS since it's the default (`#3469 <https://github.com/rtfd/readthedocs.org/pull/3469>`_)
 * `@Code0x58 <http://github.com/Code0x58>`_: Minor virtualenv upgrade (`#3463 <https://github.com/rtfd/readthedocs.org/pull/3463>`_)
 * `@humitos <http://github.com/humitos>`_: Remove invite only message (`#3456 <https://github.com/rtfd/readthedocs.org/pull/3456>`_)
 * `@maxirus <http://github.com/maxirus>`_: Adding to Install Docs (`#3455 <https://github.com/rtfd/readthedocs.org/pull/3455>`_)
 * `@stsewd <http://github.com/stsewd>`_: Fix a little typo (`#3448 <https://github.com/rtfd/readthedocs.org/pull/3448>`_)
 * `@stsewd <http://github.com/stsewd>`_: Better autogenerated index file (`#3447 <https://github.com/rtfd/readthedocs.org/pull/3447>`_)
 * `@stsewd <http://github.com/stsewd>`_: Better help text for privacy level (`#3444 <https://github.com/rtfd/readthedocs.org/pull/3444>`_)
 * `@msyriac <http://github.com/msyriac>`_: Broken link URL changed fixes #3442 (`#3443 <https://github.com/rtfd/readthedocs.org/pull/3443>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Fix git (`#3441 <https://github.com/rtfd/readthedocs.org/pull/3441>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Properly slugify the alias on Project Relationships. (`#3440 <https://github.com/rtfd/readthedocs.org/pull/3440>`_)
 * `@stsewd <http://github.com/stsewd>`_: Don't show "build ideas" to unprivileged users (`#3439 <https://github.com/rtfd/readthedocs.org/pull/3439>`_)
 * `@Blendify <http://github.com/Blendify>`_: Docs: Point Theme docs to new website (`#3438 <https://github.com/rtfd/readthedocs.org/pull/3438>`_)
 * `@humitos <http://github.com/humitos>`_: Do not use double quotes on git command with --format option (`#3437 <https://github.com/rtfd/readthedocs.org/pull/3437>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Hack in a fix for missing version slug deploy that went out a while back (`#3433 <https://github.com/rtfd/readthedocs.org/pull/3433>`_)
 * `@humitos <http://github.com/humitos>`_: Check versions used to create the venv and auto-wipe (`#3432 <https://github.com/rtfd/readthedocs.org/pull/3432>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Upgrade psycopg2 (`#3429 <https://github.com/rtfd/readthedocs.org/pull/3429>`_)
 * `@humitos <http://github.com/humitos>`_: Fix "Edit in Github" link (`#3427 <https://github.com/rtfd/readthedocs.org/pull/3427>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Add celery theme to supported ad options (`#3425 <https://github.com/rtfd/readthedocs.org/pull/3425>`_)
 * `@humitos <http://github.com/humitos>`_: Link to version detail page from build detail page (`#3418 <https://github.com/rtfd/readthedocs.org/pull/3418>`_)
 * `@humitos <http://github.com/humitos>`_: Move wipe button to version detail page (`#3417 <https://github.com/rtfd/readthedocs.org/pull/3417>`_)
 * `@humitos <http://github.com/humitos>`_: Show/Hide "See paid advertising" checkbox depending on USE_PROMOS (`#3412 <https://github.com/rtfd/readthedocs.org/pull/3412>`_)
 * `@benjaoming <http://github.com/benjaoming>`_: Strip well-known version component origin/ from remote version (`#3377 <https://github.com/rtfd/readthedocs.org/pull/3377>`_)
 * `@humitos <http://github.com/humitos>`_: Remove warnings from code (`#3372 <https://github.com/rtfd/readthedocs.org/pull/3372>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Add docker image from the YAML config integration (`#3339 <https://github.com/rtfd/readthedocs.org/pull/3339>`_)
 * `@humitos <http://github.com/humitos>`_: Show proper error to user when conf.py is not found (`#3326 <https://github.com/rtfd/readthedocs.org/pull/3326>`_)
 * `@humitos <http://github.com/humitos>`_: Simple task to finish inactive builds (`#3312 <https://github.com/rtfd/readthedocs.org/pull/3312>`_)
 * `@techtonik <http://github.com/techtonik>`_: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/rtfd/readthedocs.org/pull/3302>`_)
 * `@Riyuzakii <http://github.com/Riyuzakii>`_: changed <strong> from html to css (`#2699 <https://github.com/rtfd/readthedocs.org/pull/2699>`_)

Version 2.1.3
-------------

:date: Dec 21, 2017

 * `@ericholscher <http://github.com/ericholscher>`_: Upgrade psycopg2 (`#3429 <https://github.com/rtfd/readthedocs.org/pull/3429>`_)
 * `@humitos <http://github.com/humitos>`_: Fix "Edit in Github" link (`#3427 <https://github.com/rtfd/readthedocs.org/pull/3427>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Add celery theme to supported ad options (`#3425 <https://github.com/rtfd/readthedocs.org/pull/3425>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Only build travis push builds on master. (`#3421 <https://github.com/rtfd/readthedocs.org/pull/3421>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Add concept of dashboard analytics code (`#3420 <https://github.com/rtfd/readthedocs.org/pull/3420>`_)
 * `@humitos <http://github.com/humitos>`_: Use default avatar for User/Orgs in OAuth services (`#3419 <https://github.com/rtfd/readthedocs.org/pull/3419>`_)
 * `@humitos <http://github.com/humitos>`_: Link to version detail page from build detail page (`#3418 <https://github.com/rtfd/readthedocs.org/pull/3418>`_)
 * `@humitos <http://github.com/humitos>`_: Move wipe button to version detail page (`#3417 <https://github.com/rtfd/readthedocs.org/pull/3417>`_)
 * `@bieagrathara <http://github.com/bieagrathara>`_: 019 497 8360 (`#3416 <https://github.com/rtfd/readthedocs.org/issues/3416>`_)
 * `@bieagrathara <http://github.com/bieagrathara>`_: rew (`#3415 <https://github.com/rtfd/readthedocs.org/issues/3415>`_)
 * `@tony <http://github.com/tony>`_: lint prospector task failing (`#3414 <https://github.com/rtfd/readthedocs.org/issues/3414>`_)
 * `@humitos <http://github.com/humitos>`_: Remove extra 's' (`#3413 <https://github.com/rtfd/readthedocs.org/pull/3413>`_)
 * `@humitos <http://github.com/humitos>`_: Show/Hide "See paid advertising" checkbox depending on USE_PROMOS (`#3412 <https://github.com/rtfd/readthedocs.org/pull/3412>`_)
 * `@accraze <http://github.com/accraze>`_: Removing talks about RTD page (`#3410 <https://github.com/rtfd/readthedocs.org/pull/3410>`_)
 * `@humitos <http://github.com/humitos>`_: Pin pylint to 1.7.5 and fix docstring styling (`#3408 <https://github.com/rtfd/readthedocs.org/pull/3408>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Update style and copy on abandonment docs (`#3406 <https://github.com/rtfd/readthedocs.org/pull/3406>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Update changelog more consistently (`#3405 <https://github.com/rtfd/readthedocs.org/pull/3405>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Update prerelease invoke command to call with explicit path (`#3404 <https://github.com/rtfd/readthedocs.org/pull/3404>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Fix changelog command (`#3403 <https://github.com/rtfd/readthedocs.org/pull/3403>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Fix lint error (`#3402 <https://github.com/rtfd/readthedocs.org/pull/3402>`_)
 * `@julienmalard <http://github.com/julienmalard>`_: Recent builds are missing translated languages links (`#3401 <https://github.com/rtfd/readthedocs.org/issues/3401>`_)
 * `@stsewd <http://github.com/stsewd>`_: Remove copyright application (`#3400 <https://github.com/rtfd/readthedocs.org/pull/3400>`_)
 * `@humitos <http://github.com/humitos>`_: Show connect buttons for installed apps only (`#3394 <https://github.com/rtfd/readthedocs.org/pull/3394>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Fix display of build advice (`#3390 <https://github.com/rtfd/readthedocs.org/issues/3390>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Don't display the build suggestions div if there are no suggestions (`#3389 <https://github.com/rtfd/readthedocs.org/pull/3389>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Pass more data into the redirects. (`#3388 <https://github.com/rtfd/readthedocs.org/pull/3388>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Fix issue where you couldn't edit your canonical domain. (`#3387 <https://github.com/rtfd/readthedocs.org/pull/3387>`_)
 * `@benjaoming <http://github.com/benjaoming>`_: Strip well-known version component origin/ from remote version (`#3377 <https://github.com/rtfd/readthedocs.org/pull/3377>`_)
 * `@humitos <http://github.com/humitos>`_: Remove warnings from code (`#3372 <https://github.com/rtfd/readthedocs.org/pull/3372>`_)
 * `@JavaDevVictoria <http://github.com/JavaDevVictoria>`_: Updated python.setup_py_install to be true (`#3357 <https://github.com/rtfd/readthedocs.org/pull/3357>`_)
 * `@humitos <http://github.com/humitos>`_: Use default avatars for GitLab/GitHub/Bitbucket integrations (users/organizations) (`#3353 <https://github.com/rtfd/readthedocs.org/issues/3353>`_)
 * `@jonrkarr <http://github.com/jonrkarr>`_: Error in YAML configuration docs: default value for `python.setup_py_install` should be `true` (`#3334 <https://github.com/rtfd/readthedocs.org/issues/3334>`_)
 * `@humitos <http://github.com/humitos>`_: Show proper error to user when conf.py is not found (`#3326 <https://github.com/rtfd/readthedocs.org/pull/3326>`_)
 * `@MikeHart85 <http://github.com/MikeHart85>`_: Badges aren't updating due to being cached on GitHub. (`#3323 <https://github.com/rtfd/readthedocs.org/issues/3323>`_)
 * `@humitos <http://github.com/humitos>`_: Simple task to finish inactive builds (`#3312 <https://github.com/rtfd/readthedocs.org/pull/3312>`_)
 * `@techtonik <http://github.com/techtonik>`_: Fix Edit links if version is referenced by annotated tag (`#3302 <https://github.com/rtfd/readthedocs.org/pull/3302>`_)
 * `@humitos <http://github.com/humitos>`_: Remove/Update talks about RTD page (`#3283 <https://github.com/rtfd/readthedocs.org/issues/3283>`_)
 * `@gawel <http://github.com/gawel>`_: Regain pyquery project ownership (`#3281 <https://github.com/rtfd/readthedocs.org/issues/3281>`_)
 * `@dialex <http://github.com/dialex>`_: Build passed but I can't see the documentation (maze screen) (`#3246 <https://github.com/rtfd/readthedocs.org/issues/3246>`_)
 * `@makixx <http://github.com/makixx>`_: Account is inactive (`#3241 <https://github.com/rtfd/readthedocs.org/issues/3241>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Cleanup misreported failed builds (`#3230 <https://github.com/rtfd/readthedocs.org/issues/3230>`_)
 * `@cokelaer <http://github.com/cokelaer>`_: links to github are broken (`#3203 <https://github.com/rtfd/readthedocs.org/issues/3203>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Remove copyright application (`#3199 <https://github.com/rtfd/readthedocs.org/issues/3199>`_)
 * `@shacharoo <http://github.com/shacharoo>`_: Unable to register after deleting my account (`#3189 <https://github.com/rtfd/readthedocs.org/issues/3189>`_)
 * `@gtalarico <http://github.com/gtalarico>`_: 3 week old Build Stuck Cloning  (`#3126 <https://github.com/rtfd/readthedocs.org/issues/3126>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Regressions with conf.py and error reporting (`#2963 <https://github.com/rtfd/readthedocs.org/issues/2963>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Can't edit canonical domain (`#2922 <https://github.com/rtfd/readthedocs.org/issues/2922>`_)
 * `@virtuald <http://github.com/virtuald>`_: Documentation stuck in 'cloning' state (`#2795 <https://github.com/rtfd/readthedocs.org/issues/2795>`_)
 * `@Riyuzakii <http://github.com/Riyuzakii>`_: changed <strong> from html to css (`#2699 <https://github.com/rtfd/readthedocs.org/pull/2699>`_)
 * `@tjanez <http://github.com/tjanez>`_: Support specifying 'python setup.py build_sphinx' as an alternative build command (`#1857 <https://github.com/rtfd/readthedocs.org/issues/1857>`_)
 * `@bdarnell <http://github.com/bdarnell>`_: Broken edit links (`#1637 <https://github.com/rtfd/readthedocs.org/issues/1637>`_)

Version 2.1.2
-------------

 * `@agjohnson <http://github.com/agjohnson>`_: Update changelog more consistently (`#3405 <https://github.com/rtfd/readthedocs.org/pull/3405>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Update prerelease invoke command to call with explicit path (`#3404 <https://github.com/rtfd/readthedocs.org/pull/3404>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Fix lint error (`#3402 <https://github.com/rtfd/readthedocs.org/pull/3402>`_)
 * `@stsewd <http://github.com/stsewd>`_: Remove copyright application (`#3400 <https://github.com/rtfd/readthedocs.org/pull/3400>`_)
 * `@humitos <http://github.com/humitos>`_: Show connect buttons for installed apps only (`#3394 <https://github.com/rtfd/readthedocs.org/pull/3394>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Don't display the build suggestions div if there are no suggestions (`#3389 <https://github.com/rtfd/readthedocs.org/pull/3389>`_)
 * `@jonrkarr <http://github.com/jonrkarr>`_: Error in YAML configuration docs: default value for `python.setup_py_install` should be `true` (`#3334 <https://github.com/rtfd/readthedocs.org/issues/3334>`_)
 * `@humitos <http://github.com/humitos>`_: Simple task to finish inactive builds (`#3312 <https://github.com/rtfd/readthedocs.org/pull/3312>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Cleanup misreported failed builds (`#3230 <https://github.com/rtfd/readthedocs.org/issues/3230>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Remove copyright application (`#3199 <https://github.com/rtfd/readthedocs.org/issues/3199>`_)

Version 2.1.1
-------------

Release information missing

Version 2.1.0
-------------

 * `@ericholscher <http://github.com/ericholscher>`_: Revert "Merge pull request #3336 from rtfd/use-active-for-stable" (`#3368 <https://github.com/rtfd/readthedocs.org/pull/3368>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Revert "Do not split before first argument (#3333)" (`#3366 <https://github.com/rtfd/readthedocs.org/pull/3366>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Remove pitch from ethical ads page, point folks to actual pitch page. (`#3365 <https://github.com/rtfd/readthedocs.org/pull/3365>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Add changelog and changelog automation (`#3364 <https://github.com/rtfd/readthedocs.org/pull/3364>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Fix mkdocs search. (`#3361 <https://github.com/rtfd/readthedocs.org/pull/3361>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Email sending: Allow kwargs for other options (`#3355 <https://github.com/rtfd/readthedocs.org/pull/3355>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Try and get folks to put more tags. (`#3350 <https://github.com/rtfd/readthedocs.org/pull/3350>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Suggest wiping your environment to folks with bad build outcomes. (`#3347 <https://github.com/rtfd/readthedocs.org/pull/3347>`_)
 * `@humitos <http://github.com/humitos>`_: GitLab Integration (`#3327 <https://github.com/rtfd/readthedocs.org/pull/3327>`_)
 * `@jimfulton <http://github.com/jimfulton>`_: Draft policy for claiming existing project names. (`#3314 <https://github.com/rtfd/readthedocs.org/pull/3314>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: More logic changes to error reporting, cleanup (`#3310 <https://github.com/rtfd/readthedocs.org/pull/3310>`_)
 * `@safwanrahman <http://github.com/safwanrahman>`_: [Fix #3182] Better user deletion (`#3214 <https://github.com/rtfd/readthedocs.org/pull/3214>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Better User deletion (`#3182 <https://github.com/rtfd/readthedocs.org/issues/3182>`_)
 * `@RichardLitt <http://github.com/RichardLitt>`_: Add `Needed: replication` label (`#3138 <https://github.com/rtfd/readthedocs.org/pull/3138>`_)
 * `@josejrobles <http://github.com/josejrobles>`_: Replaced usage of deprecated function get_fields_with_model with new … (`#3052 <https://github.com/rtfd/readthedocs.org/pull/3052>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Don't delete the subprojects directory on sync of superproject (`#3042 <https://github.com/rtfd/readthedocs.org/pull/3042>`_)
 * `@andrew <http://github.com/andrew>`_: Pass query string when redirecting, fixes #2595 (`#3001 <https://github.com/rtfd/readthedocs.org/pull/3001>`_)
 * `@saily <http://github.com/saily>`_: Add GitLab repo sync and webhook support (`#1870 <https://github.com/rtfd/readthedocs.org/pull/1870>`_)
 * `@destroyerofbuilds <http://github.com/destroyerofbuilds>`_: Setup GitLab Web Hook on Project Import (`#1443 <https://github.com/rtfd/readthedocs.org/issues/1443>`_)
 * `@takotuesday <http://github.com/takotuesday>`_: Add GitLab Provider from django-allauth (`#1441 <https://github.com/rtfd/readthedocs.org/issues/1441>`_)

Version 2.0
-----------

 * `@ericholscher <http://github.com/ericholscher>`_: Email sending: Allow kwargs for other options (`#3355 <https://github.com/rtfd/readthedocs.org/pull/3355>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Try and get folks to put more tags. (`#3350 <https://github.com/rtfd/readthedocs.org/pull/3350>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Small changes to email sending to enable from email (`#3349 <https://github.com/rtfd/readthedocs.org/pull/3349>`_)
 * `@dplanella <http://github.com/dplanella>`_: Duplicate TOC entries (`#3345 <https://github.com/rtfd/readthedocs.org/issues/3345>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Small tweaks to ethical ads page (`#3344 <https://github.com/rtfd/readthedocs.org/pull/3344>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Fix python usage around oauth pagination (`#3342 <https://github.com/rtfd/readthedocs.org/pull/3342>`_)
 * `@tony <http://github.com/tony>`_: Fix isort link (`#3340 <https://github.com/rtfd/readthedocs.org/pull/3340>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Change stable version switching to respect `active` (`#3336 <https://github.com/rtfd/readthedocs.org/pull/3336>`_)
 * `@ericholscher <http://github.com/ericholscher>`_: Allow superusers to pass admin & member tests for projects (`#3335 <https://github.com/rtfd/readthedocs.org/pull/3335>`_)
 * `@humitos <http://github.com/humitos>`_: Do not split before first argument (`#3333 <https://github.com/rtfd/readthedocs.org/pull/3333>`_)
 * `@humitos <http://github.com/humitos>`_: Update docs for pre-commit (auto linting) (`#3332 <https://github.com/rtfd/readthedocs.org/pull/3332>`_)
 * `@humitos <http://github.com/humitos>`_: Take preferece of tags over branches when selecting the stable version (`#3331 <https://github.com/rtfd/readthedocs.org/pull/3331>`_)
 * `@humitos <http://github.com/humitos>`_: Add prospector as a pre-commit hook (`#3328 <https://github.com/rtfd/readthedocs.org/pull/3328>`_)
 * `@andrewgodwin <http://github.com/andrewgodwin>`_: "stable" appearing to track future release branches (`#3268 <https://github.com/rtfd/readthedocs.org/issues/3268>`_)
 * `@humitos <http://github.com/humitos>`_: Config files for auto linting (`#3264 <https://github.com/rtfd/readthedocs.org/pull/3264>`_)
 * `@mekrip <http://github.com/mekrip>`_: Build is not working (`#3223 <https://github.com/rtfd/readthedocs.org/issues/3223>`_)
 * `@skddc <http://github.com/skddc>`_: Add JSDoc to docs build environment (`#3069 <https://github.com/rtfd/readthedocs.org/issues/3069>`_)
 * `@jakirkham <http://github.com/jakirkham>`_: Specifying conda version used (`#2076 <https://github.com/rtfd/readthedocs.org/issues/2076>`_)
 * `@agjohnson <http://github.com/agjohnson>`_: Document code style guidelines (`#1475 <https://github.com/rtfd/readthedocs.org/issues/1475>`_)
