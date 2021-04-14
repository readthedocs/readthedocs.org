Proposed contents for new Sphinx guides
=======================================

This classification follows the `Diátaxis Framework <https://diataxis.fr/>`__.

Tutorial
--------

   **Objective**: Write a tutorial, some examples, and reference
   documentation for our Python code.

Every step should lead to a “yay!” moment, which marks the end of the
section. This keeps the learner motivated.

Appendixes are optional, i.e. not required to follow the tutorial, but
highly recommended.

1. Getting started

   1. Creating our code project

      -  What is our library (present some minimal ``x.py`` file in a
         dedicated directory, will be the basis of the tutorial)
      -  Install Python
      -  Check that our code works (yay!)

   2. Using virtual environments for development

      -  Create a virtual environment (and/or conda environment)
      -  Activate our virtual environment (it will always be the first
         step)
      -  Check that our code also works (yay!)

   3. Adding external dependencies

      -  Add import from small third party library
      -  Install it inside our virtual environment
      -  Check that our code works (yay!) and it doesn’t outside the
         virtual environment (as expected)

   4. Appendix: Using version control

      -  Install git (we will use it during the tutorial)
      -  Write a barebones ``README.md`` (we will expand it later), a
         ``.gitignore`` file (copied from gitignore.io), and a proper
         ``LICENSE`` file

         -  ``LICENSE.md``? ``LICENSE``? ``COPYING``? Whatever

      -  Create the first commit for the project (yay!)

2. First steps to document our project using Sphinx

   1. Installing Sphinx

      -  Activate our virtual environment
      -  Install Sphinx inside the virtual environment
      -  Check that ``sphinx-build --help`` works (yay!)

   2. Creating the project layout

      -  Run the sphinx-quickstart wizard: separate source and build
         (``y``), project name, author name, and go
      -  Check that the correct files are created (yay!)

   3. Converting our documentation to local HTML

      -  Build the HTML output using
         ``sphinx-build -b -W html doc doc/_build/html``  [1]_
      -  Navigate to ``doc/_build/html`` and launch an HTTP server
         (``python -m http.server``)
      -  Open http://localhost:8000 in a web browser, and see the HTML
         documentation (yay!)

   4. Making a change and regenerating the documentation

      -  Add a sentence to ``index.rst`` (no need to explain in detail
         what reST is at this stage)
      -  Rebuild HTML ``sphinx-build -W -b html ...``
      -  Observe that the HTML docs have changed (yay!) (we will have to
         do this every time we change something)

   5. Simplify documentation building by using Make

      -  Install Make (and its Windows counterpart)
      -  Make another trivial change
      -  Build HTML doing ``cd doc && make html``
      -  Observe that the HTML docs have changed (yay!)

   6. Converting our documentation to PDF

      -  Install TeX Live to create PDF output (should work on every
         operative system)
      -  Build LaTeX using ``make latexpdf``
      -  See that the PDF appeared (yay!)

   7. Appendix: PDF without LaTeX using rinoh (beta)

3. Customizing Sphinx configuration

   1. Changing the HTML theme

      -  Install https://pypi.org/project/furo/
      -  Change the ``html_theme`` in ``conf.py``
      -  Rebuild the HTML documentation and observe that the theme has
         changed (yay!)

   2. Changing the PDF appearance

      -  Add a ``latex_theme`` and set it to ``howto``
      -  Rebuild ``make latexpdf``
      -  Check that the appearance changed (yay!)

   3. Enable an extension

      -  Add a string to the ``extensions`` list in ``conf.py`` for
         ``sphinx.ext.duration``
      -  Rebuild the HTML docs ``make html`` and notice that now the
         times are printed (yay!)

4. Writing narrative documentation with Sphinx

   -  First focus on ``index.rst``, gently introducing the learner to
      reST and mentioning Semantic Line Breaks.
   -  Then add another ``.rst`` file to teach how ``toctree`` works.
   -  Then enable Markdown adding ``myst_parser`` to the extensions and
      authoring a Markdown file, to show that both can exist at the same
      time.
   -  Then continue introducing elements of the syntax to add pictures,
      cross-references, and the like.

5. Using Jupyter notebooks inside Sphinx
6. Describing code in Sphinx

   -  Explain the Python domain as part of narrative documentation to
      interleave code with text, include doctests, and justify the
      usefulness of the next section.

7. Autogenerating documentation from code in Sphinx

.. note 

   - Looks like MathJax is enabled by default now? Can't see a reference in the docstrings
   - The fact that the ``index.rst`` created by ``sphinx-quickstart`` is written in
     reStructuredText gets in the way of teaching Markdown (MyST).
     On the other hand, users need to know reST anyway to write Python docstrings,
     so it is necessary to teach both.

How-to Guides
-------------

Practical, problem-oriented documents, more open ended than the
tutorial. For example:

-  How to publish (deploy) a Sphinx project
-  How to publish (deploy) the documentation of a Python library to PyPI
-  How to turn a bunch of Markdown files into a Sphinx project
-  How to turn a bunch of Jupyter notebooks into a Sphinx project
-  How to localize an existing Sphinx project
-  How to customize the appearance of the HTML output of a Sphinx
   project
-  How to convert existing reStructuredText documentation to Markdown
-  How to use Doxygen autogenerated documentation inside a Sphinx
   project
-  How to keep a changelog of your project

Background
----------

More detailed explanations of certain topics. For example:

-  Understanding reStructuredText in Sphinx
-  What to put in ``conf.py``
-  Sphinx internals

Reference
---------

All the references should be external: the Sphinx reference, the MyST
and reST syntax specs, and so forth.

.. [1]
   At first I considered “make mode”, but the current maintainers don’t
   know much about its original intent (see `my comment
   here <https://github.com/sphinx-doc/sphinx/issues/3196#issuecomment-819529513>`__
   and the discussion after it)
