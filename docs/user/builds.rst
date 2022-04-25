Build process
=============

Once a project has been imported into Read the Docs and a push is done (or a build is manually triggered),
Read the Docs executes specific pre-defined commands to build the project's documentation and update the hosted version with up-to-date content.
This page explains in details what happens behind the scenes.


Understanding what's going on
-----------------------------

Understanding how Read the Docs builds projects helps with debugging the problems that may appear in the process.
It should also allow users to take advantage of certain things that happen during the build process:

.. note::

   It's important to know that all the steps are ran inside a Docker container with the image the project defined in :ref:`config-file/v2:build.os`.


The following are the pre-defined commands executed by default by Read the Docs:

:checkout:

   Checks out project's code from the URL's repository defined for this project.
   It will use `git clone`, `hg clone`, etc depending on the VCS backend.

:system_dependencies:

   Installs OS/system dependencies.
   This includes specific version of languages (e.g. Python, NodeJS, Go, Rust) and also OS packages.

   At this point, :ref:`config-file/v2:build.tools` can be used to defined languages versions,
   and :ref:`config-file/v2:build.apt_packages` to define APT packages.

:create_environment:

   Creates a Python environment to install all the dependencies in an isolated and reproducible way.
   Depending on what's defined by the project a Virtualenv or a Conda environment (:ref:`config-file/v2:conda`) will be used.

:install:

   Install :ref:`default common dependencies <build-default-versions>` to build project's documentation.

   At this point, if the project has extra Python requirements than the default ones,
   :ref:`config-file/v2:python.install` can be used for this.

   .. tip::

    We strongly recommend :ref:`pinning all the versions <guides/reproducible-builds:pinning dependencies>` required to build the documentation.
    This avoid unexpected build errors when a third party dependency release a new backward incompatible version.

:build:

   Runs the main command to build the documentation for each of the formats declared (:ref:`config-file/v2:formats`).
   It will use Sphinx (:ref:`config-file/v2:sphinx`) or MkDocs (:ref:`config-file/v2:mkdocs`) depending on the project.

:upload:

   Once the build process has finished and succeed,
   Read the Docs uploads the resulting artifacts to the storage and purge the cache so the newer version of the documentation is served.


If this process is not enough for the projects needs,
there are some extra steps that are required to build the documentation,
or simply the needing to execute extra commands to improve Read the Docs' integration with other services,
it's possible to hook user-defined commands and :ref:`customize the build process <build-customization>`..


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


Default environment variables
-----------------------------

The builder sets the following Read the Docs specific environment variables when building your documentation:

.. csv-table:: Environment Variables
   :header: Environment variable, Description, Example value
   :widths: 15, 10, 30

   ``READTHEDOCS``, Whether the build is running inside RTD, ``True``
   ``READTHEDOCS_VERSION``, The RTD slug of the version which is being built, ``latest``
   ``READTHEDOCS_VERSION_NAME``, Corresponding version name as displayed in RTD's version switch menu, ``stable``
   ``READTHEDOCS_VERSION_TYPE``, Type of the event triggering the build, ``branch`` | ``tag`` | ``external`` (for :doc:`pull request builds </pull-requests>`) | ``unknown``
   ``READTHEDOCS_PROJECT``, The RTD slug of the project which is being built, ``my-example-project``
   ``READTHEDOCS_LANGUAGE``, The RTD language slug of the project which is being built, ``en``

.. note::

   The term slug is used to refer to a unique string across projects/versions containing ASCII characters only.
   This value is used in the URLs of your documentation.


.. tip::

   In case extra environment variables are needed to the build process (like secrets, tokens, etc),
   you can add them going to :guilabel:`Admin` > :guilabel:`Environment Variables` in your project.
   See :doc:`/environment-variables`.
