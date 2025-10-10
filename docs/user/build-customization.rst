Build process customization
===========================

Read the Docs has a :doc:`well-defined build process </builds>` that works for many projects.
We also allow customization of builds in two ways:

Customize our standard build process
   Keep using the default commands for MkDocs or Sphinx,
   but extend or override the ones you need.

Define a build process from scratch
   This option gives you *full control* over your build.
   Read the Docs supports any tool that generates HTML.

Extend or override the build process
------------------------------------

In the normal build process, the pre-defined jobs ``checkout``, ``system_dependencies``,  and ``upload`` are executed.
If you define a :ref:`config-file/v2:sphinx` or :ref:`config-file/v2:mkdocs` configuration,
the ``create_environment``, ``install``, and ``build`` jobs will use the default commands for the selected tool.
If no tool configuration is specified, these jobs won't execute anything by default.

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
     - ``pre_create_environment``, ``create_environment``, ``post_create_environment``
   * - Install
     - ``pre_install``, ``install``, ``post_install``
   * - Build
     - ``pre_build``, ``build``, ``post_build``
   * - Upload
     - No customizable jobs currently

.. note::

   Any other pre-defined jobs (``checkout``, ``system_dependencies``, ``upload``) cannot be overridden or skipped.

These jobs are defined using the :doc:`configuration file </config-file/v2>` with the :ref:`config-file/v2:build.jobs` key.
This example configuration defines commands to be executed *before* installing and *after* the build has finished,
and also overrides the default build command for the ``htmlzip`` format, while keeping the default commands for the ``html`` and ``pdf`` formats:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   formats: [htmlzip, pdf]
   sphinx:
      configuration: docs/conf.py
   python:
      install:
        - requirements: docs/requirements.txt
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     jobs:
       pre_install:
         - bash ./scripts/pre_install.sh
       build:
         # The default commands for generating the HTML and pdf formats will still run.
         htmlzip:
           - echo "Override default build command for htmlzip format"
           - mkdir -p $READTHEDOCS_OUTPUT/htmlzip/
           - echo "Hello, world!" > $READTHEDOCS_OUTPUT/htmlzip/index.zip
       post_build:
         - curl -X POST \
           -F "project=${READTHEDOCS_PROJECT}" \
           -F "version=${READTHEDOCS_VERSION}" https://example.com/webhooks/readthedocs/

Features and limitations
~~~~~~~~~~~~~~~~~~~~~~~~

* The current working directory is at the root of your project's cloned repository.
* Environment variables are expanded for each individual command (see :doc:`/reference/environment-variables`).
* Each command is executed in a new shell process, so modifications done to the shell environment do not persist between commands.
* Any command returning non-zero exit code will cause the build to fail immediately
  (note there is a special exit code to `cancel the build <cancel-build-based-on-a-condition>`_).
* ``build.os`` and ``build.tools`` are required when using ``build.jobs``.
* If the :ref:`config-file/v2:sphinx` or :ref:`config-file/v2:mkdocs` configuration is defined,
  the ``create_environment``, ``install``, and ``build`` jobs will use the default commands for the selected tool.
* If neither of the :ref:`config-file/v2:sphinx` or :ref:`config-file/v2:mkdocs` configurations are defined,
  the ``create_environment``, ``install``, and ``build`` jobs will default to run nothing,
  giving you full control over the build process.

Where to put files
~~~~~~~~~~~~~~~~~~

It is your responsibility to generate HTML and other formats of your documentation when overriding the steps from :ref:`config-file/v2:build.jobs.build`.
The contents of the ``$READTHEDOCS_OUTPUT/<format>/`` directory will be hosted as part of your documentation.

We store the base folder name ``_readthedocs/`` in the environment variable ``$READTHEDOCS_OUTPUT`` and encourage that you use this to generate paths.

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

Alternative syntax
~~~~~~~~~~~~~~~~~~

Alternatively, you can use the :ref:`config-file/v2:build.commands` key to completely override the build process.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     commands:
       - pip install pelican
       - pelican --settings docs/pelicanconf.py --output $READTHEDOCS_OUTPUT/html/ docs/

But we recommend using :ref:`config-file/v2:build.jobs` instead:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     jobs:
       install:
         - pip install pelican
       build:
         html:
           - pelican --settings docs/pelicanconf.py --output $READTHEDOCS_OUTPUT/html/ docs/

``build.jobs`` offers the same functionality as ``build.commands``,
but in a more structured way that allows you to define different commands for each format,
while also supporting installing system dependencies via ``build.apt_packages``.

Examples
--------

We've included some common examples where using :ref:`config-file/v2:build.jobs` will be useful.
These examples may require some adaptation for each projects' use case,
we recommend you use them as a starting point.

Unshallow git clone
~~~~~~~~~~~~~~~~~~~

Read the Docs does not perform a full clone in the ``checkout`` job in order to reduce network data and speed up the build process.
Instead, it performs a `shallow clone <https://git-scm.com/docs/shallow>`_ and only fetches the branch or tag that you are building documentation for.
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

If your build also relies on the contents of other branches, it may also be necessary to re-configure git to fetch these:

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
         - git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*' || true
         - git fetch --all --tags || true


Cancel build based on a condition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
       python: "3.12"
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
       python: "3.12"
     jobs:
       post_checkout:
         # Use `git log` to check if the latest commit contains "skip ci",
         # in that case exit the command with 183 to cancel the build
         - (git --no-pager log --pretty="tformat:%s -- %b" -1 | paste -s -d " " | grep -viq "skip ci") || exit 183


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
   mkdocs:
     configuration: mkdocs.yml
   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.10"
     jobs:
       pre_build:
         - pydoc-markdown --build --site-dir "$READTHEDOCS_OUTPUT/html"


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
         - python -m sphinx -b linkcheck -D linkcheck_timeout=1 docs/ $READTHEDOCS_OUTPUT/linkcheck


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
         - tar xvfz git-lfs-linux-amd64-v3.1.4.tar.gz git-lfs
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


Install dependencies with Poetry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
       post_install:
         # Install poetry
         # https://python-poetry.org/docs/#installing-manually
         - pip install poetry
         # Install dependencies with 'docs' dependency group
         # https://python-poetry.org/docs/managing-dependencies/#dependency-groups
         # VIRTUAL_ENV needs to be set manually for now.
         # See https://github.com/readthedocs/readthedocs.org/pull/11152/
         - VIRTUAL_ENV=$READTHEDOCS_VIRTUALENV_PATH poetry install --with docs

   sphinx:
     configuration: docs/conf.py


Install dependencies with ``uv``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects managed with `uv <https://github.com/astral-sh/uv/>`__ can install `uv` with asdf,
and then rely on it to set up the environment and install the python project and its dependencies.
Read the Docs' own build steps expect it by setting the ``UV_PROJECT_ENVIRONMENT`` variable,
usually reducing the time taken to install compared to pip.

The following examples assumes a uv project as described in its
`projects concept <https://docs.astral.sh/uv/concepts/projects/>`__. As an introduction
refer to its `Working on projects guide <https://docs.astral.sh/uv/guides/projects/>`__.
The ``docs`` dependency group which should is pulled in during the ``uv sync`` step (if additional
extras are required they can be added with the `--extra attribute <https://docs.astral.sh/uv/concepts/projects/sync/#syncing-optional-dependencies>`__).

If a ``uv.lock`` file exists it is respected.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   sphinx:
      configuration: docs/conf.py

   build:
      os: ubuntu-24.04
      tools:
         python: "3.13"
      jobs:
         pre_create_environment:
            - asdf plugin add uv
            - asdf install uv latest
            - asdf global uv latest
         create_environment:
            - uv venv "${READTHEDOCS_VIRTUALENV_PATH}"
         install:
            - UV_PROJECT_ENVIRONMENT="${READTHEDOCS_VIRTUALENV_PATH}" uv sync --frozen --group docs

Install dependencies from Dependency Groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python `Dependency Groups <https://packaging.python.org/en/latest/specifications/dependency-groups/>`_
are a way of storing lists of dependencies in your ``pyproject.toml``.

``pip`` version 25.1+ as well as many other tools support Dependency Groups.
This example uses ``pip`` and installs from a group named ``docs``:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   build:
      os: ubuntu-24.04
      tools:
         python: "3.13"
      jobs:
         install:
            # Since the install step is overridden, pip is no longer updated automatically.
            - pip install --upgrade pip
            - pip install --group 'docs'

For more information on relevant ``pip`` usage, see the
`pip user guide on Dependency Groups <https://pip.pypa.io/en/stable/user_guide/#dependency-groups>`_.

Install dependencies with ``pixi``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects can use `pixi <https://github.com/prefix-dev/pixi/>`__,
to install Python dependencies, usually reducing the time taken to install compared to conda or pip.
Take a look at the following example:


.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   build:
      os: ubuntu-24.04
      tools:
          python: "latest"
      jobs:
         create_environment:
            - asdf plugin add pixi
            - asdf install pixi latest
            - asdf global pixi latest
         install:
            # assuming you have an environment called "docs"
            - pixi install -e docs
         build:
            html:
               - pixi run -e docs sphinx-build -T -b html docs $READTHEDOCS_OUTPUT/html

MkDocs projects could use ``NO_COLOR=1 pixi run -e docs mkdocs build --strict --site-dir $READTHEDOCS_OUTPUT/html`` instead.

Update Conda version
~~~~~~~~~~~~~~~~~~~~

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

   sphinx:
      configuration: docs/conf.py

    conda:
      environment: environment.yml

Using Pelican
~~~~~~~~~~~~~

`Pelican <https://blog.getpelican.com/>`__ is a well-known static site generator that's commonly used for blogs and landing pages.
If you are building your project with Pelican you could use a configuration file similar to the following:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.10"
     jobs:
       install:
         - pip install pelican[markdown]
       build:
         html:
           - pelican --settings docs/pelicanconf.py --output $READTHEDOCS_OUTPUT/html/ docs/


Using Docsify
~~~~~~~~~~~~~

`Docsify <https://docsify.js.org/>`__ generates documentation websites on the fly, without the need to build static HTML.
These projects can be built using a configuration file like this:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     jobs:
       build:
         html:
           - mkdir --parents $READTHEDOCS_OUTPUT/html/
           - cp --recursive docs/* $READTHEDOCS_OUTPUT/html/

Using Asciidoc
~~~~~~~~~~~~~~

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
     jobs:
       install:
         - npm install -g asciidoctor
       build:
         html:
           - asciidoctor -D $READTHEDOCS_OUTPUT/html index.asciidoc

Using pydoctor
~~~~~~~~~~~~~~

`Pydoctor <https://github.com/twisted/pydoctor>`_ is an easy-to-use standalone API documentation tool for Python.
Here is an example configuration file:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     jobs:
       install:
         - pip install pydoctor
       build:
         html:
           - |
             pydoctor \
               --project-version=${READTHEDOCS_GIT_IDENTIFIER} \
               --project-url=${READTHEDOCS_GIT_CLONE_URL%*.git} \
               --html-viewsource-base=${READTHEDOCS_GIT_CLONE_URL%*.git}/tree/${READTHEDOCS_GIT_COMMIT_HASH} \
               --html-base-url=${READTHEDOCS_CANONICAL_URL} \
               --html-output $READTHEDOCS_OUTPUT/html/ \
               ./src/my_project

Generate text format with Sphinx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There might be various reasons why would you want to generate your
documentation in `text` format (secondary to `html`). One of such reasons
would be generating LLM friendly documentation.

See the following example for how to add generation of additional `text`
format to your existing documentation. Deviations from standard build
configuration are highlighted/emphasized:

.. code-block:: yaml
   :caption: .readthedocs.yaml
   :emphasize-lines: 14-

   version: 2

   sphinx:
     configuration: docs/conf.py

   python:
     install:
     - requirements: docs/requirements.txt

   build:
     os: ubuntu-22.04
     tools:
       python: "3.12"
     jobs:
       post_build:
         - mkdir -p $READTHEDOCS_OUTPUT/html/
         - sphinx-build -n -b text docs $READTHEDOCS_OUTPUT/html/

The generated ``.txt`` files will be placed in the `html` directory, together
with ``.html`` files.
