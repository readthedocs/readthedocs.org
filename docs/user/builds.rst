Build process
=============

Once a project has been imported and a build is triggered,
Read the Docs executes specific :term:`pre-defined jobs <pre-defined build jobs>` to build the project's documentation and update the hosted content.
This page explains in detail what happens behind the scenes,
and an overview of how you can change this process.


Understanding what's going on
-----------------------------

Understanding how your content is built helps with debugging the problems that may appear in the process.
It also allows you customize the steps of the build process.

.. note::

   All the steps are run inside a Docker container with the image the project defines in :ref:`config-file/v2:build.os`,
   and all the :doc:`/environment-variables` defined are exposed to them.


The following are the pre-defined jobs executed by Read the Docs:

:checkout:

   Checks out project's code from the URL's repository defined for this project.
   It will use `git clone`, `hg clone`, etc depending on the version control system you choose.

:system_dependencies:

   Installs operating system & system-level dependencies.
   This includes specific version of languages (e.g. Python, Node.js, Go, Rust) and also ``apt`` packages.

   At this point, :ref:`config-file/v2:build.tools` can be used to define a language version,
   and :ref:`config-file/v2:build.apt_packages` to define ``apt`` packages.

:create_environment:

   Creates a Python environment to install all the dependencies in an isolated and reproducible way.
   Depending on what's defined by the project a virtualenv or a conda environment (:ref:`config-file/v2:conda`) will be used.

:install:

   Install :doc:`default common dependencies <build-default-versions>`.

   If the project has extra Python requirements,
   :ref:`config-file/v2:python.install` can be used to specify them.

   .. tip::

    We strongly recommend :ref:`pinning all the versions <guides/reproducible-builds:pinning dependencies>` required to build the documentation to avoid unexpected build errors.

:build:

   Runs the main command to build the documentation for each of the formats declared (:ref:`config-file/v2:formats`).
   It will use Sphinx (:ref:`config-file/v2:sphinx`) or MkDocs (:ref:`config-file/v2:mkdocs`) depending on the project.

:upload:

   Once the build process finishes successfully,
   the resulting artifacts are uploaded to our servers, and the CDN is purged so the newer version of the documentation is served.


.. seealso::

    If there are extra steps required to build the documentation,
    or you need to execute additional commands to integrate with other tools,
    it's possible to run user-defined commands and :doc:`customize the build process <build-customization>`.


When to cancel builds
---------------------

There may be situations where you want to cancel a particular running build.
Cancelling running builds will allow your team to speed up review times and also help us reduce server costs and ultimately,
our environmental footprint.

Consider the following scenarios:

* the build has an external dependency that hasn't been updated
* there were no changes on the documentation files
* many other use cases that can be solved with custom logic

For these scenarios,
Read the Docs supports three different mechanisms to cancel a running build:

:Manually:

   Once a build was triggered,
   project administrators can go to the build detail page
   and click the button "Cancel build".

:Automatically:

   When Read the Docs detects a push to a branch that it's currently building the documentation,
   it cancels the running build and start a new build using the latest commit from the new push.

:Programatically:

   You can use user-defined commands on ``build.jobs`` or ``build.commands`` (see :doc:`build-customization`)
   to check for a condition and exit it with the code ``183`` if you want to cancel the running build or ``0``, otherwise.

   In this case, Read the Docs will communicate to your Git platform (GitHub/GitLab) that the build succeeded (green tick ✅)
   so the pull request is in a mergeable state.

   .. tip::

      Take a look at :ref:`build-customization:cancel build based on a condition` section for some examples.


Build resources
---------------

Every build has limited resources to avoid misuse of the platform.
Currently, these build limits are:

.. tabs::

   .. tab:: |org_brand|

      * 15 minutes build time
      * 3GB of memory
      * 2 concurrent builds

      We can increase build limits on a per-project basis.
      Send an email to support@readthedocs.org providing a good reason why your documentation needs more resources.

      If your business is hitting build limits hosting documentation on Read the Docs,
      please consider :doc:`Read the Docs for Business </commercial/index>`
      which has much higher build resources.

   .. tab:: |com_brand|

      * 30 minutes build time
      * 7GB of memory
      * Concurrent builds vary based on your pricing plan

      If you are having trouble with your documentation builds,
      you can reach our support at support@readthedocs.com.
