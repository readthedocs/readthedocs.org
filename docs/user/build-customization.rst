Build customization
===================

Read the Docs has a :ref:`well-defined build process <builds>` that works for many projects,
but we offer additional customization to support more uses of our platform.
This page explains how to extend the build process, using user-defined jobs to execute custom commands.

In the normal build process,
the pre-defined jobs ``checkout``, ``system_dependencies``, ``create_environment``, ``install``, ``build`` and ``upload`` are executed.
However, Read the Docs exposes extra jobs to users so they can customize the build process by running shell commands.
These extra jobs are:

.. list-table::

   * - Step
     - Customizable jobs
   * - Checkout
     - ``post_checkout``
   * - System dependencies
     - ``pre_system_dependencies``, ``post_system_dependencies``
   * - Create environment
     - ``pre_create_environment``, ``post_create_environment``
   * - Install
     - ``pre_install``, ``post_install``
   * - Build
     - ``pre_build``, ``post_build``
   * - Upload
     - There is no customizable jobs currently

.. note::

   Currently, the default jobs (e.g. ``checkout``, ``system_dependencies``, etc) executed by Read the Docs are not possible to override or skip.


These jobs can be declared by using a :doc:`/config-file/index` with the :ref:`config-file/v2:build.jobs` key on it.
Let's say the project requires commands to be executed *before* installing any dependency into the Python environment and *after* the build has finished.
In that case, a config file similar to this one can be used:

.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_install:
         - bash ./scripts/pre_install.sh
       post_build:
         - curl -X POST \
           -F "project=${READTHEDOCS_PROJECT}" \
           -F "version=${READTHEDOCS_VERSION}" https://example.com/webhooks/readthedocs/


There are some caveats to knowing when using user-defined jobs:

* ``PWD`` environment variable is the root of the cloned repository
* Environment variables are expanded in the commands (see :doc:`environment-variables`)
* Each command is executed in a new shell process, so modifications done to the shell environment are not persistent between commands
* Any command returning non-zero exit code makes the build to fail immediately
* ``build.os`` and ``build.tools`` are required when using ``build.jobs``


Examples
--------

We've included some common examples where using :ref:`config-file/v2:build.jobs` will be useful.
These examples may require some adaptation for each projects' use case,
we recommend you use them as a starting point.


Unshallow clone
~~~~~~~~~~~~~~~

Read the Docs does not perform a full clone on ``checkout`` job to reduce network data and speed up the build process.
Because of this, extensions that depend on the full Git history will fail.
To avoid this, it's possible to unshallow the clone done by Read the Docs:

.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       post_checkout:
         - git fetch --unshallow


Generate documentation from annotated sources with Doxygen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's possible to run Doxygen as part of the build process to generate documentation from annotated sources:

.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - doxygen


Use MkDocs extensions with extra required steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are some MkDocs extensions that require specific commands to be run to generate extra pages before performing the build.
For example, `pydoc-markdown <http://niklasrosenstein.github.io/pydoc-markdown/>`_

.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - pydoc-markdown --build --site-dir "$PWD/_build/html"


Avoid having a dirty ``git`` index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs needs to modify some files before performing the build to be able to integrate with some of its features.
Because of this reason, it could happen the Git index gets dirty (it will detect modified files).
In case this happens and the project is using any kind of extension that generates a version based on Git metadata (like `setuptools_scm <https://github.com/pypa/setuptools_scm/>`_),
this could cause an invalid version number to be generated.
In that case, the Git index can be updated to ignore the files that Read the Docs has modified.

.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_install:
         - git update-index --assume-unchanged environment.yml docs/conf.py


Perform a check for broken links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sphinx comes with a `linkcheck <https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder>`_ builder that checks for broken external links included in the project's documentation.
This helps ensure that all external links are still valid and readers aren't linked to non-existent pages.


.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - python -m sphinx -b linkcheck docs/ _build/linkcheck
