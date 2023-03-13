Proposed contents for new Sphinx guides
=======================================

.. note::

   This work is in progress, see discussion on `this Sphinx
   issue <https://github.com/sphinx-doc/sphinx/issues/9165>`_
   and the pull requests linked at the end.

The two main objectives are:

- Contributing a good Sphinx tutorial for beginners.
  This should introduce the readers to all the various Sphinx major features
  in a pedagogical way, and be mostly focused on Markdown using MyST.
  We would try to find a place for it in the official Sphinx documentation.
- Write a new narrative tutorial for Read the Docs
  that complements the existing guides
  and offers a cohesive story of how to use the service.

Sphinx tutorial
---------------

Appendixes are optional, i.e. not required to follow the tutorial, but
highly recommended.

#. The Sphinx way

   -  Preliminary section giving an overview of what Sphinx is, how it works,
      how reStructuredText and Markdown/MyST are related to it, some terminology
      (toctree, builders), what can be done with it.

#. About this tutorial

   -  A section explaining the approach of the tutorial,
      as well as how to download the result of each section
      for closer inspection or for skipping parts of it.

#. Getting started

   #. Creating our project

      -  Present a fictitious goal for a documentation project
      -  Create a blank ``README.md`` to introduce the most basic elements of Markdown
         (headings and paragraph text)

   #. Installing Sphinx and cookiecutter in a new development environment

      -  Install Python (or miniforge)
      -  Create a virtual environment (and/or conda environment)
      -  Activate our virtual environment (it will always be the first
         step)
      -  Install Sphinx inside the virtual environment
      -  Check that ``sphinx-build --help`` works (yay!)

   #. Creating the documentation layout

      -  Apply our cookiecutter to create a minimal ``docs/`` directory
         (similar to what ``sphinx-quickstart`` does, but
         with source and build separation by default,
         project release 0.1, English language,
         and a MyST index, if at all) [1]_
      -  Check that the correct files are created (yay!)

   #. Appendix: Using version control

      -  Install git (we will not use it during the tutorial)
      -  Add a proper ``.gitignore`` file (copied from gitignore.io)
      -  Create the first commit for the project (yay!)

#. First steps to document our project using Sphinx

   #. Converting our documentation to local HTML

      -  Create (or minimally tweak) ``index.md``
      -  Build the HTML output using
         ``sphinx-build -b -W html doc doc/_build/html``  [2]_
      -  Navigate to ``doc/_build/html`` and launch an HTTP server
         (``python -m http.server``)
      -  Open http://localhost:8000 in a web browser, and see the HTML
         documentation (yay!)

   #. Converting our documentation to other formats

      -  Build PseudoXML using ``make pseudoxml``
      -  Build Text using ``make text``
      -  See how the various formats change the output (yay!)

   #. Appendix: Simplify documentation building by using Make [3]_

      -  Install Make (nothing is needed on Windows, `make.bat` is standalone)
      -  Add more content to ``index.md``
      -  Build HTML doing ``cd doc && make html``
      -  Observe that the HTML docs have changed (yay!)

   #. Appendix: PDF without LaTeX using rinoh (beta)

#. Customizing Sphinx configuration

   #. Changing the HTML theme

      -  Install https://pypi.org/project/furo/
      -  Change the ``html_theme`` in ``conf.py``
      -  Rebuild the HTML documentation and observe that the theme has
         changed (yay!)

   #. Changing the PDF appearance

      -  Add a ``latex_theme`` and set it to ``howto``
      -  Rebuild ``make latexpdf``
      -  Check that the appearance changed (yay!)

   #. Enable an extension

      -  Add a string to the ``extensions`` list in ``conf.py`` for
         ``sphinx.ext.duration``
      -  Rebuild the HTML docs ``make html`` and notice that now the
         times are printed (yay!)

#. Writing narrative documentation with Sphinx

   -  First focus on ``index.md``, diving more into Markdown
      and mentioning Semantic Line Breaks.
   -  Then add another ``.md`` file to teach how ``toctree`` works.
   -  Then continue introducing elements of the syntax to add pictures,
      cross-references, and the like.

#. Describing code in Sphinx

   -  Explain the Python domain as part of narrative documentation to
      interleave code with text, include doctests, and justify the
      usefulness of the next section.

#. Autogenerating documentation from code in Sphinx
#. Deploying a Sphinx project online

   - A bit of background on the options: GitHub/GitLab Pages,
     custom server, Netlify, Read the Docs
   - Make reference to Read the Docs tutorial

#. Appendix: Using Jupyter notebooks inside Sphinx
#. Appendix: Understanding the docutils document tree
#. Appendix: Where to go from here

   - Refer the user to the Sphinx, reST and MyST references,
     prominent projects already using Sphinx,
     compilations of themes and extensions,
     the development documentation.

.. note

   - Looks like MathJax is enabled by default now? Can't see a reference in the docstrings

Read the Docs tutorial
----------------------

#. The Read the Docs way
#. Getting started

   #. Preparing our project on GitHub

      - Fork a starter GitHub repository (something like `our demo template
        <https://github.com/readthedocs/template>`_,
        as a starting point that
        helps mimicking the `sphinx-quickstart` or `cookiecutter` step
        without having to checkout the code locally)

   #. Importing our project to Read the Docs

      - Sign up with GitHub on RTD
      - Import the project (don't "Edit advanced project options", we
        will do this later)
      - The project is created on RTD
      - Browse "builds", open the build live logs, wait a couple of minutes,
        open the docs (yay!)

   #. Basic configuration changes

      - Add a description, homepage, and tags
      - Configure your email for build failure notification
        (until we turn them on by default)
      - Enable "build pull requests for this project" in the advanced settings
      - Edit a file from the GitHub UI as part of a new branch, and open a pull request
      - See the RTD check on the GitHub PR UI, wait a few minutes, open result (yay!)

#. Customizing the build process

   - Use `.readthedocs.yaml` (rather than the web UI) to customize build formats,
     change build requirements and Python version, enable fail-on-warnings

#. Versioning documentation

   - Explain how to manage versions on RTD: create release branches,
     activate the corresponding version, browse them in the version selector,
     selectively build versions
   - Intermediate topics: hide versions, create Automation Rules

#. Getting insights from your projects

   - Move around the project, explore results in Traffic Analytics
   - Play around with server-side search, explore results in Search Analytics

#. Managing translations

#. Where to go from here

   - Reference our existing guides, prominent projects already using RTD,
     domain configuration, our support form, our contributing documentation

Possible new how-to Guides
--------------------------

Some ideas for extra guides on specific topics,
still for beginners but more problem-oriented documents,
covering a wide range of use cases:

-  How to turn a bunch of Markdown files into a Sphinx project
-  How to turn a bunch of Jupyter notebooks into a Sphinx project
-  How to localize an existing Sphinx project
-  How to customize the appearance of the HTML output of a Sphinx
   project
-  How to convert existing reStructuredText documentation to Markdown
-  How to use Doxygen autogenerated documentation inside a Sphinx
   project
-  How to keep a changelog of your project

Reference
---------

All the references should be external: the Sphinx reference, the MyST
and reST syntax specs, and so forth.

.. [1]
   Similar to https://github.com/sphinx-contrib/cookiecutter,
   but only for the `docs/` directory? This way it can be less opinionated
   about everything else
.. [2]
   At first I considered “make mode”, but the current maintainers don’t
   know much about its original intent (see `my comment
   here <https://github.com/sphinx-doc/sphinx/issues/3196#issuecomment-819529513>`__
   and the discussion after it)
.. [3]
   There have been attempts at creating a `sphinx` command, see
   `this pull request <https://github.com/sphinx-doc/sphinx/pull/6938/>`__
