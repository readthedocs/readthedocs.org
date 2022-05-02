Reproducible Builds
===================

Your docs depend on tools and other dependencies to be built.
If your docs don't have reproducible builds,
an update in a dependency can break your builds when least expected,
or make your docs look different from your local version.
This guide will help you to keep your builds working over time, and in a reproducible way.

.. contents:: Contents
   :local:
   :depth: 3

Building your docs
------------------

To test your build process, you can build them locally in a clean environment
(this is without any dependencies installed).
Then you should make sure you are running those same steps on Read the Docs.

You can configure how your project is built from the web interface (:guilabel:`Admin` tab),
or by :ref:`using a configuration file <guides/reproducible-builds:using a configuration file>` (recommended).
If you aren't familiar with these tools, check our docs:

- :doc:`/intro/getting-started-with-sphinx`
- :doc:`/intro/getting-started-with-mkdocs`
- :doc:`/config-file/v2`

.. note::

   You can see the exact commands that are run on Read the Docs by going to the :guilabel:`Builds` tab of your project.

Using a configuration file
--------------------------

If you use the web interface to configure your project,
the options are applied to *all* versions and builds of your docs,
and can be lost after changing them over time.
Using a :doc:`configuration file </config-file/v2>` **provides you per version settings**,
and **those settings live in your repository**.

A configuration file with explicit dependencies looks like this:

.. code-block:: yaml

   # File: .readthedocs.yaml

   version: 2

   build:
     os: "ubuntu-20.04"
     tools:
       python: "3.9"

   # Build from the docs/ directory with Sphinx
   sphinx:
     configuration: docs/conf.py

   # Explicitly set the version of Python and its requirements
   python:
     install:
       - requirements: docs/requirements.txt

.. code-block::

   # File: docs/requirements.txt

   # Defining the exact version will make sure things don't break
   sphinx==4.2.0
   sphinx_rtd_theme==1.0.0
   readthedocs-sphinx-search==0.1.1

Don't rely on implicit dependencies
-----------------------------------

By default Read the Docs will install the tool you chose to build your docs,
and other dependencies, this is done so new users can build their docs without much configuration.

We highly recommend not to assume these dependencies will always be present or that their versions won't change.
Always declare your dependencies explicitly using a :ref:`configuration file <guides/reproducible-builds:using a configuration file>`,
for example:

✅ Good:
   Your project is declaring the Python version explicitly,
   and its dependencies using a requirements file.

   .. code-block:: yaml

      # File: .readthedocs.yaml

      version: 2

      build:
        os: "ubuntu-20.04"
        tools:
          python: "3.9"

      sphinx:
        configuration: docs/conf.py

      python:
        install:
          - requirements: docs/requirements.txt

❌ Bad:
   Your project is relying on the default Python version and default installed dependencies.

   .. code-block:: yaml

      # File: .readthedocs.yaml

      version: 2

      sphinx:
         configuration: docs/conf.py

Pinning dependencies
--------------------

As you shouldn't rely on implicit dependencies,
you shouldn't rely on undefined versions of your dependencies.
Some examples:

✅ Good:
   The specified versions will be used for all your builds,
   in all platforms, and won't be updated unexpectedly.

   .. code-block::

      # File: docs/requirements.txt

      sphinx==4.2.0
      sphinx_rtd_theme==1.0.0
      readthedocs-sphinx-search==0.1.1

   .. code-block:: yaml

      # File: docs/environment.yaml

      name: docs
      channels:
        - conda-forge
        - defaults
      dependencies:
        - sphinx==4.2.0
        - nbsphinx==0.8.1
        - pip:
          - sphinx_rtd_theme==1.0.0

❌ Bad:
   The latest or any other already installed version will be used,
   and your builds can fail or change unexpectedly any time.

   .. code-block::

      # File: docs/requirements.txt

      sphinx
      sphinx_rtd_theme
      readthedocs-sphinx-search

   .. code-block:: yaml

      # File: docs/environment.yaml

      name: docs
      channels:
        - conda-forge
        - defaults
      dependencies:
        - sphinx
        - nbsphinx
        - pip:
          - sphinx_rtd_theme

Check the `pip user guide`_ for more information about requirements files,
or our Conda docs about :ref:`environment files <guides/conda:creating the \`\`environment.yml\`\`>`.

.. _`pip user guide`: https://pip.pypa.io/en/stable/user_guide/#requirements-files

.. tip::

   Remember to update your docs' dependencies from time to time to get new improvements and fixes.
   It also makes it easy to manage in case a version reaches its end of support date.


Pinning transitive dependencies
-------------------------------

Once you have pinned your own dependencies,
the next thing to worry about are the additional dependencies of these projects.
Transitive dependencies are these extra dependencies.

We recommend `pip-tools`_ to help address this problem.
It allows you to specify a ``requirements.in`` file with your first-level dependencies,
and it generates a ``requirementes.txt`` file with the full set of transitive dependencies.

.. _pip-tools: https://pip-tools.readthedocs.io/en/latest/

✅ Good:
    All your transitive dependencies will stay defined,
    not allowing a package upgrade to break your docs.

   .. code-block::

      # File: docs/requirements.in

      sphinx==4.2.0

   .. code-block:: yaml

      # File: docs/requirements.txt

      # This file is autogenerated by pip-compile with python 3.7
      # To update, run:
      #
      #    pip-compile docs.in
      #
      alabaster==0.7.12
          # via sphinx
      babel==2.10.1
          # via sphinx
      certifi==2021.10.8
          # via requests
      charset-normalizer==2.0.12
          # via requests
      docutils==0.17.1
          # via sphinx
      idna==3.3
          # via requests
      imagesize==1.3.0
          # via sphinx
      importlib-metadata==4.11.3
          # via sphinx
      jinja2==3.1.2
          # via sphinx
      markupsafe==2.1.1
          # via jinja2
      packaging==21.3
          # via sphinx
      pygments==2.11.2
          # via sphinx
      pyparsing==3.0.8
          # via packaging
      pytz==2022.1
          # via babel
      requests==2.27.1
          # via sphinx
      snowballstemmer==2.2.0
          # via sphinx
      sphinx==4.4.0
          # via -r docs.in
      sphinxcontrib-applehelp==1.0.2
          # via sphinx
      sphinxcontrib-devhelp==1.0.2
          # via sphinx
      sphinxcontrib-htmlhelp==2.0.0
          # via sphinx
      sphinxcontrib-jsmath==1.0.1
          # via sphinx
      sphinxcontrib-qthelp==1.0.3
          # via sphinx
      sphinxcontrib-serializinghtml==1.1.5
          # via sphinx
      typing-extensions==4.2.0
          # via importlib-metadata
      urllib3==1.26.9
          # via requests
      zipp==3.8.0
          # via importlib-metadata
