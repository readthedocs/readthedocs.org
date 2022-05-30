Build customization
===================

Read the Docs has a :doc:`well-defined build process <builds>` that works for many projects,
but we offer additional customization to support more uses of our platform.
This page explains how to extend the build process using :term:`user-defined build jobs` to execute custom commands,
and also how to override the build process completely:

`Extend the build process`_
    If you are using Sphinx or Mkdocs and need to execute additional commands.

`Override the build process`_
    If you want full control over your build or are not using Sphinx or Mkdocs.


Extend the build process
------------------------

In the normal build process,
the pre-defined jobs ``checkout``, ``system_dependencies``, ``create_environment``, ``install``, ``build`` and ``upload`` are executed.
However, Read the Docs exposes extra jobs to users so they can customize the build process by running shell commands.
These extra jobs are:

.. list-table::
   :header-rows: 1

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
     - There are no customizable jobs currently

.. note::

   Currently, the pre-defined jobs (``checkout``, ``system_dependencies``, etc) executed by Read the Docs cannot be overridden or skipped.


These jobs can be declared by using a :doc:`/config-file/index` with the :ref:`config-file/v2:build.jobs` key on it.
Let's say the project requires commands to be executed *before* installing any dependency into the Python environment and *after* the build has finished.
In that case, a config file similar to this one can be used:

.. code-block:: yaml
   :caption: .readthedocs.yaml

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

* The current working directory is at the root of your project's cloned repository
* Environment variables are expanded in the commands (see :doc:`environment-variables`)
* Each command is executed in a new shell process, so modifications done to the shell environment do not persist between commands
* Any command returning non-zero exit code will cause the build to fail immediately
* ``build.os`` and ``build.tools`` are required when using ``build.jobs``


Examples
++++++++

We've included some common examples where using :ref:`config-file/v2:build.jobs` will be useful.
These examples may require some adaptation for each projects' use case,
we recommend you use them as a starting point.


Unshallow clone
~~~~~~~~~~~~~~~

Read the Docs does not perform a full clone on ``checkout`` job to reduce network data and speed up the build process.
Because of this, extensions that depend on the full Git history will fail.
To avoid this, it's possible to unshallow the clone done by Read the Docs:

.. code-block:: yaml
   :caption: .readthedocs.yaml

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

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
       # Note that this HTML won't be automatically uploaded,
       # unless your documentation build includes it somehow.
         - doxygen


Use MkDocs extensions with extra required steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are some MkDocs extensions that require specific commands to be run to generate extra pages before performing the build.
For example, `pydoc-markdown <http://niklasrosenstein.github.io/pydoc-markdown/>`_

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - pydoc-markdown --build --site-dir "$PWD/_build/html"


Avoid having a dirty Git index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs needs to modify some files before performing the build to be able to integrate with some of its features.
Because of this reason, it could happen the Git index gets dirty (it will detect modified files).
In case this happens and the project is using any kind of extension that generates a version based on Git metadata (like `setuptools_scm <https://github.com/pypa/setuptools_scm/>`_),
this could cause an invalid version number to be generated.
In that case, the Git index can be updated to ignore the files that Read the Docs has modified.

.. code-block:: yaml
   :caption: .readthedocs.yaml

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


.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - python -m sphinx -b linkcheck docs/ _build/linkcheck


Support Git LFS (Large File Storage)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case the repository contains large files that are tracked with Git LFS,
there are some extra steps required to be able to download their content.
It's possible to use ``post_checkout`` user-defined job for this.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       post_checkout:
         # Download and uncompress the binary
         # https://git-lfs.github.com/
         - wget https://github.com/git-lfs/git-lfs/releases/download/v3.1.4/git-lfs-linux-amd64-v3.1.4.tar.gz
         - tar xvfz git-lfs-linux-amd64-v3.1.4.tar.gz
         # Modify LFS config paths to point where git-lfs binary was downloaded
         - git config filter.lfs.process "`pwd`/git-lfs filter-process"
         - git config filter.lfs.smudge  "`pwd`/git-lfs smudge -- %f"
         - git config filter.lfs.clean "`pwd`/git-lfs clean -- %f"
         # Make LFS available in current repository
         - ./git-lfs install
         # Download content from remote
         - ./git-lfs fetch
         # Make local files to have the real content on them
         - ./git-lfs checkout


Install Node.js dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's possible to install Node.js together with the required dependencies by using :term:`user-defined build jobs`.
To setup it, you need to define the version of Node.js to use and install the dependencies by using ``build.jobs.post_install``:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.9"
       nodejs: "16"
     jobs:
       post_install:
         # Install dependencies defined in your ``package.json``
         - npm ci
         # Install any other extra dependencies to build the docs
         - npm install -g jsdoc


Override the build process
--------------------------

.. warning::

   This feature is in a *beta phase* and could suffer incompatible changes or even removed completely in the near feature.
   It does not yet support some of the Read the Docs' integrations like the :term:`flyout menu`, search and ads.
   However, integrating all of them is part of the plan.
   Use it under your own responsibility.


When :ref:`extending the build process <build-customization:extend the build process>` is not enough for a particular use case,
all the default commands can be overwritten to execute only the commands defined by the project on its config file.
This can be achieve by using :ref:`config-file/v2:build.commands` key as shown in the following example building a `Pelican <https://blog.getpelican.com/>`_ site:


.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     commands:
       - pip install pelican[markdown]
       - pelican --settings docs/pelicanconf.py --output output/ docs/


As Read the Docs does not have control over the build process,
you are responsible to run all the commands required to install the requirements and build the documentation properly.
Once the build process finishes, the ``output/`` folder will be hosted.
