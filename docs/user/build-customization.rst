Build customization
===================

Read the Docs has a :ref:`well-defined build process <builds>` that may not be enough for all the use cases.
This page explains how to customize Read the Docs build process to get the most of it and support custom build processes.

In the normal build process the jobs ``checkout``, ``system_dependencies``, ``create_environment``, ``install``, ``build`` and ``upload`` are executed.
However, Read the Docs exposes in-between jobs to users so they can customize the build process by running shell commands.
These in-between jobs are:

:post_checkout:

:pre_system_dependencies:

:post_system_dependencies:

:pre_create_environment:

:post_create_environment:

:pre_install:

:post_install:

:pre_build:

:post_build:


These jobs can be declared by using a :ref:`config-file/index` with the :ref:`config-file/v2:build.jobs` key on it.
Let's say the project requires a mandatory command to be executed *before* installing any dependency into the Python environment and *after* the build has finished.
In that case, a config file similar to this one can be used:

.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_install:
         - echo "Executing pre_install step..."
         - bash ./scripts/pre_install.sh
       post_build:
         - echo "Executing post_build step..."
         - curl -X POST \
           -F "project=${READTHEDOCS_PROJECT}" \
           -F "version=${READTHEDOCS_VERSION}" https://my.company.com/webhooks/readthedocs/

.. note::

   Currently, the default jobs (e.g. ``checkout``, ``system_dependencies``, etc) executed by Read the Docs are not possible to overwritte or skip.


Examples
--------

This is a non-exahustive list of common examples where using :ref:`config-file/v2:build.jobs` will be useful.
Also note that these examples may require some adaption for each projects' use case.
They are listed here just as a guide.


Unshallow clone
~~~~~~~~~~~~~~~

Read the Docs does not perform a full clone on ``checkout`` step to reduce network data and speed up the build process.
Because of this reason, if there are extensions in the build process that depend on the full history, they will fail.
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
Because of this reason, it could happen the git index gets dirty (e.i. it will detect modified files).
In case this happens and the project is using any kind of extension that generates a version based on git metadata (like `setuptools_scm <https://github.com/pypa/setuptools_scm/>`_),
this could case a miss generated version number.
In that case, the git index can be updated to ignore the files that Read the Docs has modified.

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
This could be a good addition to the build process to be sure that all the external links are valid over time and readers don't find a dead end when clicking on them.


.. code:: yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - python -m sphinx -b linkcheck docs/ _build/linkcheck
