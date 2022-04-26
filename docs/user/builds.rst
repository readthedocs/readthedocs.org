Build process
=============

Once a project has been imported into Read the Docs and a push is done (or a build is manually triggered),
Read the Docs executes specific pre-defined jobs to build the project's documentation and update the hosted version with up-to-date content.
This page explains in details what happens behind the scenes.


Understanding what's going on
-----------------------------

Understanding how your content is built helps with debugging the problems that may appear in the process.
It also allows you customize the steps of the build process.

.. note::

   All the steps are ran inside a Docker container with the image the project defines in :ref:`config-file/v2:build.os`.


The following are the pre-defined jobs executed by default by Read the Docs:

:checkout:

   Checks out project's code from the URL's repository defined for this project.
   It will use `git clone`, `hg clone`, etc depending on the version control system you choose.

:system_dependencies:

   Installs operating system & system-level dependencies.
This includes specific version of languages (e.g. Python, Node.js, Go, Rust) and also ``apt`` packages.

   At this point, :ref:`config-file/v2:build.tools` can be used to define a  language version,
   and :ref:`config-file/v2:build.apt_packages` to define ``apt`` packages.

:create_environment:

   Creates a Python environment to install all the dependencies in an isolated and reproducible way.
   Depending on what's defined by the project a virtualenv or a conda environment (:ref:`config-file/v2:conda`) will be used.

:install:

   Install :ref:`default common dependencies <build-default-versions>`.

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

The Read the Docs builder sets the following environment variables when building your documentation:

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

   If extra environment variables are needed in the build process (like an API token),
   you can add them going to :guilabel:`Admin` > :guilabel:`Environment Variables` in your project.
   See :doc:`/environment-variables`.
