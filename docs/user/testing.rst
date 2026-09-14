Automating and Testing Documentation
====================================

Documentation is important to your users,
so you want to make sure it's always correct.
Read the Docs can automatically validate and test your documentation during each build,
catching issues before they reach production.

This guide shows you how to integrate testing tools into your Read the Docs builds
using custom build jobs and dependencies.

Overview
--------

Read the Docs builds can run custom validation commands as part of the build process.
You can integrate linting, code snippet validation, and link checking directly in ``.readthedocs.yaml``.
If a validation step fails, the entire build fails and the docs are not deployed.

Vale: Prose and style linting
------------------------------

Vale checks for consistency in voice, tone, terminology, and style across your documentation.
Unlike generic linters, Vale understands documentation best practices and catches issues like passive voice overuse, inconsistent terminology, and style guide violations.

**Setup**

Create a ``.vale.ini`` file in your project root:

.. code-block:: ini

   [*]
   BasedOnStyles = Vale,Microsoft
   StylesPath = styles
   MinAlertLevel = warning

Vale comes with built-in style guides (Vale, Microsoft, Google). You can also create custom style rules.

**Integration in Read the Docs**

Add Vale to your ``docs/requirements.txt``:

.. code-block:: text

   vale==3.0.0

Then configure a custom build job in ``.readthedocs.yaml``:

.. code-block:: yaml

   version: 2
   build:
     os: ubuntu-22.04
     tools:
       python: "3.11"

   python:
     install:
       - requirements: docs/requirements.txt

   jobs:
     post_build:
       - vale docs/

If Vale finds style issues, the build fails and displays the full report. You can configure which checks fail the build using alert levels in ``.vale.ini``:

.. code-block:: ini

   [*]
   MinAlertLevel = error

This way, warnings don't fail the build but errors do.

Doc Detective: Code snippet validation
---------------------------------------

Doc Detective automatically executes code snippets embedded in your documentation to ensure they actually work.
This is invaluable for keeping examples up-to-date as your product evolves.
It supports Python, JavaScript, Go, Bash, and other languages, catching broken examples and outdated API usage that would confuse users.

**Setup**

Create a ``doc-detective.json`` in your project root:

.. code-block:: json

   {
     "runTests": true,
     "checkLinks": true,
     "autoDetectLanguages": true,
     "errorOnFail": true,
     "ignorePatterns": ["node_modules", ".git"]
   }

Add test configurations for your language. Example for Python:

.. code-block:: json

   {
     "runTests": true,
     "testRunnerConfig": {
       "python": {
         "install": ["pip install -r requirements.txt"],
         "setup": "import sys; sys.path.insert(0, '.')"
       }
     }
   }

**Integration in Read the Docs**

Add doc-detective to your ``docs/requirements.txt``:

.. code-block:: text

   doc-detective==0.5.0

In code blocks, wrap examples with metadata comments:

   .. code-block:: python

      # doc-detective-test
      result = 1 + 1
      assert result == 2

Configure the build in ``.readthedocs.yaml``:

.. code-block:: yaml

   version: 2
   build:
     os: ubuntu-22.04
     tools:
       python: "3.11"

   python:
     install:
       - requirements: docs/requirements.txt

   jobs:
     post_build:
       - doc-detective execute

If any code snippet fails, the build fails and shows which snippet broke and why.

Sphinx build strictness
-----------------------

For reStructuredText projects, Sphinx can catch structural and formatting issues automatically.
Configure Sphinx to treat warnings as errors, so broken cross-references and malformed directives fail the build immediately.

**Setup in conf.py**

.. code-block:: python

   import warnings

   warnings.filterwarnings("error", category=Warning)

**Configuration in Read the Docs**

Set ``fail_on_warning`` in ``.readthedocs.yaml``:

.. code-block:: yaml

   version: 2
   build:
     os: ubuntu-22.04
     tools:
       python: "3.11"

   python:
     install:
       - requirements: docs/requirements.txt

   sphinx:
     configuration: docs/conf.py
     fail_on_warning: true

This automatically fails the build if Sphinx encounters any warnings, including:

* Broken internal references and ``.. automodule::`` directives
* Malformed RST syntax
* Missing or duplicate labels
* Unused footnotes and citations

Complete example
----------------

Here's a complete ``.readthedocs.yaml`` with multiple validation steps:

.. code-block:: yaml

   version: 2

   build:
     os: ubuntu-22.04
     tools:
       python: "3.11"

   python:
     install:
       - requirements: docs/requirements.txt

   sphinx:
     configuration: docs/conf.py
     fail_on_warning: true

   jobs:
     post_build:
       - vale docs/
       - doc-detective execute

When you push changes, Read the Docs will:

1. Install your documentation dependencies
2. Build Sphinx and fail on any warnings
3. Run Vale for prose linting
4. Execute and validate all code snippets with Doc Detective
5. Only deploy if all steps pass

This ensures your documentation is correct, complete, and ready for your users.
