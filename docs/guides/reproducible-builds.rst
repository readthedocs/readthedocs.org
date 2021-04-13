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

   # Build from the docs/ directory with Sphinx
   sphinx:
     configuration: docs/conf.py

   # Explicitly set the version of Python and its requirements
   python:
     version: 3.7
     install:
       - requirements: docs/requirements.txt

.. code-block::

   # File: docs/requirements.txt

   # Defining the exact version will make sure things don't break
   sphinx==3.4.3
   sphinx_rtd_theme==0.5.1
   readthedocs-sphinx-search==0.1.0

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

      sphinx:
        configuration: docs/conf.py

      python:
        version: 3.7
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

      sphinx==3.4.3
      sphinx_rtd_theme==0.5.1
      readthedocs-sphinx-search==0.1.0rc3

   .. code-block:: yaml
      
      # File: docs/environment.yaml

      name: docs
      channels:
        - conda-forge
        - defaults
      dependencies:
        - sphinx==3.4.3
        - nbsphinx==0.8.1 
        - pip:
          - sphinx_rtd_theme==0.5.1

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

   .. TODO: link to the supported versions policy.
