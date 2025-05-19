Build process overview
======================

Once a project has been added and a build is triggered,
Read the Docs executes a set of :term:`pre-defined jobs <pre-defined build jobs>` to build and upload documentation.
This page explains in detail what happens behind the scenes,
and includes an overview of how you can change this process.

Understanding the build process
-------------------------------

Understanding how your content is built helps with debugging any problems you might hit.
It also gives you the knowledge to customize the build process.

.. note::

   All the steps are run inside a Docker container, using the image defined in :ref:`config-file/v2:build.os`.
   The build has access to all :doc:`pre-defined environment variables </reference/environment-variables>` and :doc:`custom environment variables </environment-variables>`.

The build process includes the following jobs:

:checkout:

   Checks out a project's code from the Git repository.
   On |com_brand|,
   this environment includes the SSH deploy key that gives access to the repository.

:system_dependencies:

   Installs operating system and runtime dependencies.
   This includes specific versions of a language (e.g. Python, Node.js, Go, Rust) and also ``apt`` packages.

   :ref:`config-file/v2:build.tools` can be used to define a language version,
   and :ref:`config-file/v2:build.apt_packages` to define ``apt`` packages.

:create_environment:

   Creates a Python environment to install all the dependencies in an isolated and reproducible way.
   Depending on what's defined by the project,
   a :term:`virtualenv` or a :ref:`conda environment <config-file/v2:conda>` will be used.

   .. note::

      This step is only executed if the :ref:`config-file/v2:sphinx` or :ref:`config-file/v2:mkdocs` keys are defined.

:install:

   Installs :doc:`default and project dependencies </build-default-versions>`.
   This includes any requirements you have configured in :ref:`config-file/v2:requirements file`.

   If the project has extra Python requirements,
   :ref:`config-file/v2:python.install` can be used to specify them.

   .. tip::

      We strongly recommend :doc:`pinning all the versions </guides/reproducible-builds>` required to build the documentation to avoid unexpected build errors.

   .. note::

      This step is only executed if the :ref:`config-file/v2:sphinx` or :ref:`config-file/v2:mkdocs` keys are defined.

:build:

   Runs the main command to build the documentation for each of the formats declared (:ref:`config-file/v2:formats`).
   It will use Sphinx (:ref:`config-file/v2:sphinx`) or MkDocs (:ref:`config-file/v2:mkdocs`) depending on the project.

:upload:

   Once the build process finishes successfully,
   the resulting artifacts (HTML, PDF, etc.) are uploaded to our servers.
   Our :doc:`CDN </reference/cdn>` is then purged so your docs are *always up to date*.

.. seealso::

    If you require additional build steps or customization,
    it's possible to run user-defined commands and :doc:`customize the build process </build-customization>`.

Cancelling builds
-----------------

There may be situations where you want to cancel a running build.
Cancelling builds allows your team to speed up review times and also help us reduce server costs and our environmental footprint.

A couple common reasons you might want to cancel builds are:

* the build has an external dependency that hasn't been updated
* there were no changes on the documentation files

For these scenarios,
Read the Docs supports three different mechanisms to cancel a running build:

:Manually:

   Project administrators can go to the build detail page
   and click :guilabel:`Cancel build`.

:Automatically:

   When Read the Docs detects a push to a version that is already building,
   it cancels the running build and starts a new build using the latest commit.

:Programmatically:

   You can use user-defined commands on ``build.jobs`` or ``build.commands`` (see :doc:`build-customization`)
   to check for your own cancellation condition and then return exit code ``183`` to cancel a build.
   You can exit with the code ``0`` to continue running the build.

   When this happens, Read the Docs will notify your :doc:`Git provider </reference/git-integration>` the build succeeded (✅),
   so the pull request doesn't have any failing checks.

   .. tip::

      Take a look at :ref:`build-customization:cancel build based on a condition` section for some examples.

Build resources
---------------

Every build has limited resources assigned to it.
Our build limits are:

.. tabs::

   .. tab:: |com_brand|

      * 30 minutes build time (upgradable)
      * 7GB of memory (upgradable)
      * Concurrent builds vary based on your pricing plan

      If you are having trouble with your documentation builds,
      you can reach our support at support@readthedocs.com.

   .. tab:: |org_brand|

      * 15 minutes build time
      * 7GB of memory
      * 2 concurrent builds
      * 5GB of disk storage (soft limit)

      We can increase build time on a per-project basis.
      Send an email to support@readthedocs.org providing a good reason why your documentation needs more resources.

      If your business is hitting build limits hosting documentation on Read the Docs,
      please consider :doc:`Read the Docs for Business </commercial/index>`
      which has options for additional build resources.
