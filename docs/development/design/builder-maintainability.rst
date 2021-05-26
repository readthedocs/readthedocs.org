Builder Maintainability
=======================

.. contents::
   :local:
   :depth: 2

This document extends the proposal done by Manuel at `Future Builder`_ to replace the last 3 goals:

* Allow us to add a feature with a defined contract without worry about breaking old builds
* Introduce ``build.builder: 2`` config (does not install pre-defined packages) for these new features
* Motivate users to migrate to ``v2`` to finally deprecate this magic by educating users


It proposes a way to version the current "magical" builder so we can freeze its current status and
extend it if needed by doing a new release of it.
Besides, it removes the needing of using ``build.builder: 2`` since the *new builder* will extend the "magical" builder behavior
and just override what's required.

.. _Future Builder: https://github.com/readthedocs/readthedocs.org/pull/8190


Goals
-----

* Keep the current "magical" builder working as-is (freeze this version)
* Make "magical" builder maintainable over time
* Allow users to specify a version of the "magical" builder
* Define a code API to split in a modularized way the builder's code
* Use the API to extend builder's code to support the "new builder"
* Split the builders' code in: ``BuilderBase``, ``SphinxMagicalBuilder`` and ``SphinxDummyBuilder``
* Fail the build when mixing config for commands (e.g. ``sphinx.fail_on_warning``, ``submodules``, etc)
  with the new builder (e.g. ``build.jobs`` and ``build.commands``)
* Fail the build of new projects if users doesn't pin the version of the builder
* Fail the build if new builder is used without pinning the builder version
* Set current "magical" builder version as default for current projects
* Move the build process out from Read the Docs core on their own packages


"Magic" currently executed by our builder
-----------------------------------------

This section describes all the "magic" that Read the Docs does on behalf of the user in the build process.
The magic is split in two different scenarios: environment and tool.

.. note::

   This section is strongly related with a similar research done by Santos at `Explicit Builders`_

   .. _Explicit Builders: https://github.com/readthedocs/readthedocs.org/pull/8103/


Environment: virtualenv
~~~~~~~~~~~~~~~~~~~~~~~

Magic happening at virtualenv setup process:

- Creates virtualenv
- Tries possible pip's requirement files if not defined
- Install package: repository itself
- Updates pip and installs setuptools
  (uses feature flag: ``DONT_INSTALL_LATEST_PIP``)
- Installs *core* dependencies
  (uses feature flag: ``DEFAULT_TO_MKDOCS_0_17_3``, ``USE_MKDOCS_LATEST``, ``USE_SPHINX_LATEST``, ``USE_SPHINX_RTD_EXT_LATEST``)
- Install requirements file (uses feature flag: ``PIP_ALWAYS_UPGRADE``)

.. note::

   All this magic lives in the `readthedocs/doc_builder/python_environments.py`_ file.

.. _readthedocs/doc_builder/python_environments.py: https://github.com/readthedocs/readthedocs.org/blob/master/readthedocs/doc_builder/python_environments.py


Environment: conda
~~~~~~~~~~~~~~~~~~

Magic happening at conda environment setup process:

- Creates conda environment
- Install package: repository itself
- Updates conda (uses feature flag: ``CONDA_USES_MAMBA``)
- Installs mamba  (uses feature flag: ``CONDA_USES_MAMBA``)
- Installs *core* dependencies
- Append conda core requirements to environment file (uses feature flag: ``CONDA_APPEND_CORE_REQUIREMENTS``)

.. note::

   All this magic lives in the `readthedocs/doc_builder/python_environments.py`_ file.

.. _readthedocs/doc_builder/python_environments.py: https://github.com/readthedocs/readthedocs.org/blob/master/readthedocs/doc_builder/python_environments.py


Tool: Sphinx
~~~~~~~~~~~~

Magic happening at Sphinx build process:

- Creates a ``index.rst`` if it doesn't exist
- Searches for different ``conf.py`` paths if not provided
- Creates ``conf.py`` based on a template if it does not exist
- Appends default content to ``conf.py``
  (uses feature flags: ``ALL_VERSIONS_IN_HTML_CONTEXT``, ``ALL_VERSIONS_IN_HTML_CONTEXT``, ``DONT_OVERWRITE_SPHINX_CONTEXT``, ``DISABLE_SERVER_SIDE_SEARCH``)
- Call build command with specific arguments
  (uses feature flags: ``SPHINX_PARALLEL``, ``USE_SPHINX_BUILDERS``)
- Move the output (and change the filename) to a specific path
- Emulates ``make all-pdf`` based on the backend engine: ``pdflatex`` or ``latexmk``:
  - ``pdflatex``:
    - calls ``pdflatex`` over all tex files (two passes!)
    - calls ``makeindex`` over all tex files
  - ``latexmk``:
    - calls ``extractbb`` for each image file
    - finds the correct ``latexmkrc`` file based on language
    - execute ``latexmk`` with specific options

.. note::

   All this magic lives in the `readthedocs/doc_builder/backends/sphinx.py`_ file.

.. _readthedocs/doc_builder/backends/sphinx.py: https://github.com/readthedocs/readthedocs.org/blob/master/readthedocs/doc_builder/backends/sphinx.py


Tool: MkDocs
~~~~~~~~~~~~

Magic happening at MkDocs building process:

- Creates a ``index.md`` if it doesn't exist
- Default to ``mkdocs.yaml`` file config at the root level if not defined
- Creates a default ``mkdocs.yaml`` file if it doesn't exist
- Requires parsing (outside Docker container) ``mkdocs.yaml`` to modify some configs
- Default the ``docs_dir`` to ``docs``
- Generates ``readthedocs-data.js`` with project's data
  (uses feature flag: ``ENABLE_MKDOCS_SERVER_SIDE_SEARCH``, ``DISABLE_SERVER_SIDE_SEARCH``)
- Add ``extra_css`` and ``extra_javascript`` with our custom files
  (e.g. ``readhedocs-data.js``, ``readthedocs-doc-embed.js``, ``readthedocs-analytics.js``, ``badge_only.css``, ``readthedocs-doc-embed.css``)
- Remove MkDocs ``google_analytics`` config
- Override MkDocs ``theme`` config (uses feature flag: ``MKDOCS_THEME_RTD``)
- Call build command with specific arguments
- Move the HTML output to a specific path

.. note::

   All this magic lives in the `readthedocs/doc_builder/backends/mkdocs.py`_ file.

.. _readthedocs/doc_builder/backends/mkdocs.py: https://github.com/readthedocs/readthedocs.org/blob/master/readthedocs/doc_builder/backends/mkdocs.py


Make "magical" builder maintainable
-----------------------------------

This document understands the "magical" builder as a core and *key product* of Read the Docs.
It has been used for +10 years now and it's the only way users have to use the platform.
However, maintaining it over this time has produced builds to be broken after an update and
also it made impossible to add a new feature because it's not backward compatible;
producing the adoption of multiple feature flags that become unmaintaible at this point.
On the other hand, the time spent thinking about how to make everything keep working the same way
while introducing a new feature that works for *all the use cases* has been exponentially increased over time.

Some of these problems can be solved by:

- Freezing the "magical" builder as-is (and stop adding new features)
- Versioning the "magical" builder and allow users to pin to a version

Either way, the initial step would be to freeze/version the current state and breaking it out
from Read the Docs into its own repository, converted into a Python package.
On the build process, the builder will be treat as a regular dependency:
``readthedocs-sphinx-magical-builder==1.0.0`` or ``readthedocs-mkdocs-magical-builder==1.0.0``.

The current "magical" builder state (e.g. version 1.0.0) will be installed by default if the user does not specify it,
allowing us to add breaking changes to the builder without worrying about breaking old projects/builds while giving new features
to users whom will be able to opt-in to the new version of the "magical" builder (e.g. ``2.0.0``).


Builder's code API and breakout into packages
---------------------------------------------


``readthedocs-base-builder``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   class BuilderBase:

       def __init__(self, environment, doctool):
           # Virtualenv or Conda for now.
           # In the future this could be Rust/Nodejs/Ruby/etc environment.
           self.environment = environment

           # SphinxBuilder or MkDocs class for now.
           # In the future this could be HugoBuilder, PelicanBuilder, etc.
           self.doctool = doctool

       # .. other pre/post and jobs methods

       def pre_create_envirnoment(self):
           self.environment.pre_create_environment()

       def create_environment(self):
           self.environment.create_environment()

       def post_create_envirnoment(self):
           self.environment.post_create_environment()
           self.doctool.post_create_environment()

       # .. other pre/post and jobs methods

       def run(self):
           # Executes all the steps in order to perform the build
           pass


   class Virtualenv(PythonEnvironment):

       def create_environment(self):
           return 'python3.9 -m virtualenv --system-site-packages env'

       def post_create_environment(self):
           # Updates pip and install setuptools
           return 'pip install -U pip setuptools'


   class Conda(PythonEnvironment):

       def pre_create_environment(self):
           # Append Read the Docs core dependencies to conda's environment file
           pass

       def create_environment(self):
           return 'conda env create -f environment.yaml`


``readthedocs-sphinx-magical-builder``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   class SphinxMagicalBuilder(BuilderBase):

       # .. other pre/post and job methods

       def post_create_environment(self):
           # Install Read the Docs core dependencies
           return 'pip install mock==1.0.1 pillow==5.4.1 alabaster>=0.7,<0.8,!=0.7.5 commonmark==0.8.1 recommonmark==0.5.0 '
                  'sphinx sphinx-rtd-theme readthedocs-sphinx-ext'

       def pre_build(self):
           # Create ``index.rst`` if not found
           # Generate ``conf.py`` if not found
           # Append settings to ``conf.py``
           # etc
           pass

       def build(self):
           return 'sphinx-build -T -j auto -E -b html -d _build/doctrees -D language=en . _build/html'

       # .. other pre/post and job methods


``readthedocs-mkdocs-magical-builder``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   class MkDocsMagicalBuilder(BuilderBase):

       # .. other pre/post and job methods

       def post_create_environment(self):
           # Install Read the Docs core dependencies
           return 'pip install mock==1.0.1 pillow==5.4.1 alabaster>=0.7,<0.8,!=0.7.5 commonmark==0.8.1 recommonmark==0.5.0 '
                  'mkdocs==0.17.3'

       def pre_build(self):
           # Creates ``mkdocs.yaml`` file if not found
           # Generates ``readthedocs-data.js`` with project's data
           # Updates some configs in ``mkdocs.yaml``
           pass

       def build(self):
           return 'mkdocs build --clean --site-dir docs/ --config-file mkdocs.yaml'

       # .. other pre/post and job methods


The new non-"magical" builder
-----------------------------

Users that don't want to use the "magical" builder will be able to install a different builder: ``readthedocs-sphinx-builder==1.0.0``.
This builder won't execute any pre/post jobs on behalf of the user and won't share code with the "magical" builder package.
It will only contains the normal steps to build a Sphinx project and will fail if the project doesn't follow the standard structure.
Any non-standard requirement can be supported by overriding the proper ``build.job.`` step.


Un-answered questions
---------------------

* Do we really need ``build.version: 2``?
* How do we allow people to *remove all our magic* without ``build.version: 2``?
* Should ``build.commands`` do not execute *any* ``readthedocs_`` methods?
* If ``build.jobs.install`` is overwritten with ``conda env create -f environment.yaml``,
  should we execute our ``readthedocs_pre_install`` that appends our *core* requirements?
* Overwritting the job itself should remove automatic pre/post hooks?
* If we decide to use ``build.version: 2`` to remove all the magic,
  how we communicate to users what's the magic removed?
* How users will decide what builder to use?
  Should this be a config like ``build.builder: readthedocs-sphinx-magical-builder==1.0.0``?
  Maybe a Python class path ``readthedocs.builder.sphinx.SphinxMagicalBuilder`` that we can import?
