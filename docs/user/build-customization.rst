Build process customization
===========================

Read the Docs has a :doc:`well-defined build process </builds>` that works for many projects.
We also allow customization of builds in two ways:

`Extend the build process`_
    Keep using the default build process,
    adding your own commands.

`Override the build process`_
    This option gives you *full control* over your build.
    Read the Docs supports any tool that generates HTML.

Extend the build process
------------------------

In the normal build process,
the pre-defined jobs ``checkout``, ``system_dependencies``, ``create_environment``, ``install``, ``build`` and ``upload`` are executed.
Read the Docs also exposes these jobs,
which allows you to customize the build process by adding shell commands.

The jobs where users can customize our default build process are:

.. list-table::
   :header-rows: 1
   :widths: 25 75

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
     - No customizable jobs currently

.. note::

   The pre-defined jobs (``checkout``, ``system_dependencies``, etc) cannot be overridden or skipped.
   You can fully customize things in :ref:`build-customization:override the build process`.

These jobs are defined using the :doc:`/config-file/v2` with the :ref:`config-file/v2:build.jobs` key.
This example configuration defines commands to be executed *before* installing and *after* the build has finished:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     jobs:
       pre_install:
         - bash ./scripts/pre_install.sh
       post_build:
         - curl -X POST \
           -F "project=${READTHEDOCS_PROJECT}" \
           -F "version=${READTHEDOCS_VERSION}" https://example.com/webhooks/readthedocs/


User-defined job limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The current working directory is at the root of your project's cloned repository
* Environment variables are expanded for each individual command (see :doc:`/reference/environment-variables`)
* Each command is executed in a new shell process, so modifications done to the shell environment do not persist between commands
* Any command returning non-zero exit code will cause the build to fail immediately
  (note there is a special exit code to `cancel the build <cancel-build-based-on-a-condition>`_)
* ``build.os`` and ``build.tools`` are required when using ``build.jobs``


``build.jobs`` examples
~~~~~~~~~~~~~~~~~~~~~~~

We've included some common examples where using :ref:`config-file/v2:build.jobs` will be useful.
These examples may require some adaptation for each projects' use case,
we recommend you use them as a starting point.


Unshallow git clone
^^^^^^^^^^^^^^^^^^^

Read the Docs does not perform a full clone on ``checkout`` job to reduce network data and speed up the build process.
Because of this, extensions that depend on the full Git history will fail.
To avoid this, it's possible to unshallow the :program:`git clone`:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       post_checkout:
         - git fetch --unshallow || true


Cancel build based on a condition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a command exits with code ``183``,
Read the Docs will cancel the build immediately.
You can use this approach to cancel builds that you don't want to complete based on some conditional logic.

.. note:: Why 183 was chosen for the exit code?

   It's the word "skip" encoded in ASCII.
   Then it's taken the 256 modulo of it because
   `the Unix implementation does this automatically <https://tldp.org/LDP/abs/html/exitcodes.html>`_
   for exit codes greater than 255.

   .. code-block:: pycon

      >>> sum(list("skip".encode("ascii")))
      439
      >>> 439 % 256
      183


Here is an example that cancels builds from pull requests when there are no changes to the ``docs/`` folder compared to the ``origin/main`` branch:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.11"
     jobs:
       post_checkout:
         # Cancel building pull requests when there aren't changed in the docs directory or YAML file.
         # You can add any other files or directories that you'd like here as well,
         # like your docs requirements file, or other files that will change your docs build.
         #
         # If there are no changes (git diff exits with 0) we force the command to return with 183.
         # This is a special exit code on Read the Docs that will cancel the build immediately.
         - |
           if [ "$READTHEDOCS_VERSION_TYPE" = "external" ] && git diff --quiet origin/main -- docs/ .readthedocs.yaml;
           then
             exit 183;
           fi


This other example shows how to cancel a build if the commit message contains ``skip ci`` on it:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.11"
     jobs:
       post_checkout:
         # Use `git log` to check if the latest commit contains "skip ci",
         # in that case exit the command with 183 to cancel the build
         - (git --no-pager log --pretty="tformat:%s -- %b" -1 | grep -viq "skip ci") || exit 183


Generate documentation from annotated sources with Doxygen
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
         - pydoc-markdown --build --site-dir "$READTHEDOCS_OUTPUT/html"


Avoid having a dirty Git index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
         - python -m sphinx -b linkcheck -D linkcheck_timeout=1 docs/ $READTHEDOCS_OUTPUT/linkcheck


Support Git LFS (Large File Storage)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Install dependencies with Poetry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Projects managed with `Poetry <https://python-poetry.org/>`__,
can use the ``post_create_environment`` user-defined job to use Poetry for installing Python dependencies.
Take a look at the following example:


.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     jobs:
       post_create_environment:
         # Install poetry
         # https://python-poetry.org/docs/#installing-manually
         - pip install poetry
         # Tell poetry to not use a virtual environment
         - poetry config virtualenvs.create false
       post_install:
         # Install dependencies with 'docs' dependency group
         # https://python-poetry.org/docs/managing-dependencies/#dependency-groups
         - poetry install --with docs

   sphinx:
     configuration: docs/conf.py


Update Conda version
^^^^^^^^^^^^^^^^^^^^

Projects using Conda may need to install the latest available version of Conda.
This can be done by using the ``pre_create_environment`` user-defined job to update Conda
before creating the environment.
Take a look at the following example:


.. code-block:: yaml
   :caption: .readthedocs.yaml

    version: 2

    build:
      os: "ubuntu-22.04"
      tools:
        python: "miniconda3-4.7"
      jobs:
        pre_create_environment:
          - conda update --yes --quiet --name=base --channel=defaults conda

    conda:
      environment: environment.yml


.. _build_commands_introduction:

Override the build process
--------------------------

.. warning::

   This feature is in *beta* and could change without warning.
   We are currently testing `the new addons integrations we are building <rtd-blog:addons-flyout-menu-beta>`_
   on projects using ``build.commands`` configuration key.

If your project requires full control of the build process,
and :ref:`extending the build process <build-customization:extend the build process>` is not enough,
all the commands executed during builds can be overridden using the :ref:`config-file/v2:build.commands`.

As Read the Docs does not have control over the build process,
you are responsible for running all the commands required to install requirements and build your project.

Where to put files
~~~~~~~~~~~~~~~~~~

It is your responsibility to generate HTML and other formats of your documentation using :ref:`config-file/v2:build.commands`.
The contents of the ``$READTHEDOCS_OUTPUT/<format>/`` directory will be hosted as part of your documentation.

We store the the base folder name ``_readthedocs/`` in the environment variable ``$READTHEDOCS_OUTPUT`` and encourage that you use this to generate paths.

Supported :ref:`formats <downloadable-documentation:accessing offline formats>` are published if they exist in the following directories:

* ``$READTHEDOCS_OUTPUT/html/`` (required)
* ``$READTHEDOCS_OUTPUT/htmlzip/``
* ``$READTHEDOCS_OUTPUT/pdf/``
* ``$READTHEDOCS_OUTPUT/epub/``

.. note::

   Remember to create the folders before adding content to them.
   You can ensure that the output folder exists by adding the following command:

   .. code-block:: console

       mkdir -p $READTHEDOCS_OUTPUT/html/

Search support
~~~~~~~~~~~~~~

Read the Docs will automatically index the content of all your HTML files,
respecting the :ref:`search <config-file/v2:search>` option.

You can access the search from the Read the Docs :term:`dashboard`,
or by using the :doc:`/server-side-search/api`.

.. note::

   In order for Read the Docs to index your HTML files correctly,
   they should follow the conventions described at :doc:`rtd-dev:search-integration`.

``build.commands`` examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section contains examples that showcase what is possible with :ref:`config-file/v2:build.commands`.
Note that you may need to modify and adapt these examples depending on your needs.

Pelican
^^^^^^^

`Pelican <https://blog.getpelican.com/>`__ is a well-known static site generator that's commonly used for blogs and landing pages.
If you are building your project with Pelican you could use a configuration file similar to the following:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     commands:
       - pip install pelican[markdown]
       - pelican --settings docs/pelicanconf.py --output $READTHEDOCS_OUTPUT/html/ docs/


Docsify
^^^^^^^

`Docsify <https://docsify.js.org/>`__ generates documentation websites on the fly, without the need to build static HTML.
These projects can be built using a configuration file like this:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       nodejs: "16"
     commands:
       - mkdir --parents $READTHEDOCS_OUTPUT/html/
       - cp --recursive docs/* $READTHEDOCS_OUTPUT/html/

Asciidoc
^^^^^^^^

`Asciidoctor <https://asciidoctor.org/>`__ is a fast processor for converting and generating documentation from AsciiDoc source.
The Asciidoctor toolchain includes `Asciidoctor.js <https://docs.asciidoctor.org/asciidoctor.js/latest/>`__ which you can use with custom build commands.
Here is an example configuration file:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       nodejs: "20"
     commands:
       - npm install -g asciidoctor
       - asciidoctor -D $READTHEDOCS_OUTPUT/html index.asciidoc
