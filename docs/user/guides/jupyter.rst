How to use Jupyter notebooks in Sphinx
======================================

`Jupyter`_ notebooks are a popular tool to describe computational narratives
that mix code, prose, images, interactive components, and more.
Embedding them in your Sphinx project allows using these rich documents as documentation,
which can provide a great experience for tutorials, examples, and other types of technical content.
There are a few extensions that allow integrating Jupyter and Sphinx,
and this document will explain how to achieve some of the most commonly requested features.

.. _Jupyter: https://jupyter.org/

.. _ipynb-notebooks-sphinx:

Including classic ``.ipynb`` notebooks in Sphinx documentation
--------------------------------------------------------------

There are two main extensions that add support Jupyter notebooks as source files in Sphinx:
nbsphinx_ and MyST-NB_. They have similar intent and basic functionality:
both can read notebooks in ``.ipynb`` and additional formats supported by `jupytext`_,
and are configured in a similar way
(see :ref:`nb-background` for more background on their differences).

First of all, create a Jupyter notebook using the editor of your liking (for example, JupyterLab_).
For example, ``source/notebooks/Example 1.ipynb``:

.. figure:: /_static/images/guides/example-notebook.png
   :width: 80%
   :align: center
   :alt: Example Jupyter notebook created on JupyterLab

   Example Jupyter notebook created on JupyterLab

.. _JupyterLab: https://jupyterlab.readthedocs.io/

Next, you will need to enable one of the extensions, as follows:

.. tabs::

   .. tab:: nbsphinx

      .. code-block:: python
         :caption: conf.py

         extensions = [
             "nbsphinx",
         ]

   .. tab:: MyST-NB

      .. code-block:: python
         :caption: conf.py

         extensions = [
             "myst_nb",
         ]

Finally, you can include the notebook in any *toctree*.
For example, add this to your root document:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         .. toctree::
            :maxdepth: 2
            :caption: Contents:

            notebooks/Example 1

   .. tab:: MyST (Markdown)

      .. code-block:: md

         ```{toctree}
         ---
         maxdepth: 2
         caption: Contents:
         ---
         notebooks/Example 1
         ```

The notebook will render as any other HTML page in your documentation
after doing ``make html``.

.. figure:: /_static/images/guides/example-notebook-rendered.png
   :width: 80%
   :align: center
   :alt: Example Jupyter notebook rendered on HTML by nbsphinx

   Example Jupyter notebook rendered on HTML by nbsphinx

To further customize the rendering process among other things,
refer to the nbsphinx_ or MyST-NB_ documentation.

Rendering interactive widgets
-----------------------------

Widgets are eventful python objects that have a representation in the browser
and that you can use to build interactive GUIs for your notebooks.
Basic widgets using `ipywidgets`_ include controls like sliders, textboxes, and buttons,
and more complex widgets include interactive maps, like the ones provided by `ipyleaflet`_.

.. _ipywidgets: https://ipywidgets.readthedocs.io/
.. _ipyleaflet: https://ipyleaflet.readthedocs.io/

You can embed these interactive widgets on HTML Sphinx documentation.
For this to work, it's necessary to *save the widget state*
before generating the HTML documentation,
otherwise the widget will appear as empty.
Each editor has a different way of doing it:

- The classical Jupyter Notebook interface
  provides a "Save Notebook Widget State" action in the "Widgets" menu,
  :doc:`as explained in the ipywidgets
  documentation <ipywidgets:embedding>`.
  You need to click it before exporting your notebook to HTML.
- JupyterLab provides a "Save Widget State Automatically" option in the "Settings" menu.
  You need to leave it checked so that widget state is automatically saved.
- In Visual Studio Code `it's not possible to save the widget
  state <https://github.com/microsoft/vscode-jupyter/issues/4404>`_
  at the time of writing (June 2021).

.. figure:: /_static/images/guides/jupyterlab-save-widget-state.png
   :width: 30%
   :align: center
   :alt: JupyterLab option to save the interactive widget state automatically

   JupyterLab option to save the interactive widget state automatically

For example, if you create a notebook with a simple
`IntSlider <https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20List.html#intslider>`__
widget from ipywidgets and save the widget state,
the slider will render correctly in Sphinx.

.. figure:: /_static/images/guides/widget-html.gif
   :width: 80%
   :align: center
   :alt: Interactive widget rendered in HTML by Sphinx

   Interactive widget rendered in HTML by Sphinx

To see more elaborate examples:

- `ipyleaflet`_ provides several widgets for interactive maps,
  and renders live versions of them :doc:`in their documentation <ipyleaflet:layers/velocity>`.
- `PyVista <https://docs.pyvista.org/>`_ is used for scientific 3D visualization
  with several interactive backends and `examples in their
  documentation <https://docs.pyvista.org/index.html#maps-and-geoscience>`_ as well.

.. warning::

   Although widgets themselves can be embedded in HTML,
   :doc:`events <ipywidgets:examples/Widget Events>`
   require a backend (kernel) to execute.
   Therefore, ``@interact``, ``.observe``, and related functionalities relying on them
   will not work as expected.

.. note::

   If your widgets need some additional JavaScript libraries,
   you can add them using :py:meth:`~sphinx.application.Sphinx.add_js_file`.

.. _other-formats:

Using notebooks in other formats
--------------------------------

For example, this is how a simple notebook looks like in MyST Markdown format:

.. code-block::
   :caption: Example 3.md

   ---
   jupytext:
     text_representation:
       extension: .md
       format_name: myst
       format_version: 0.13
       jupytext_version: 1.10.3
   kernelspec:
     display_name: Python 3
     language: python
     name: python3
   ---

   # Plain-text notebook formats

   This is a example of a Jupyter notebook stored in MyST Markdown format.

   ```{code-cell} ipython3
   import sys
   print(sys.version)
   ```

   ```{code-cell} ipython3
   from IPython.display import Image
   ```

   ```{code-cell} ipython3
   Image("http://sipi.usc.edu/database/preview/misc/4.2.03.png")
   ```

To render this notebook in Sphinx
you will need to add this to your ``conf.py``:

.. tabs::

   .. tab:: nbsphinx

      .. code-block:: python
         :caption: conf.py

         nbsphinx_custom_formats = {
             ".md": ["jupytext.reads", {"fmt": "mystnb"}],
         }

   .. tab:: MyST-NB

      .. code-block:: python
         :caption: conf.py

         nb_custom_formats = {
             ".md": ["jupytext.reads", {"fmt": "mystnb"}],
         }

Notice that the Markdown format does not store the outputs of the computation.
Sphinx will automatically execute notebooks without outputs,
so in your HTML documentation they appear as complete.

.. _notebook-galleries:

Creating galleries of examples using notebooks
----------------------------------------------

`nbsphinx`_ has support for :doc:`creating thumbnail galleries from a list of Jupyter
notebooks <nbsphinx:subdir/gallery>`.

There are two ways to create the gallery:

- From a reStructuredText source file, using the ``.. nbgallery::`` directive,
  :ref:`as showcased in the
  documentation <nbsphinx:/a-normal-rst-file.rst#thumbnail-galleries>`.
- From a Jupyter notebook, adding a ``"nbsphinx-gallery"`` tag to the metadata of a cell.
  Each editor has a different way of modifying the cell metadata (see figure below).

.. figure:: /_static/images/guides/jupyterlab-metadata.png
   :width: 80%
   :align: center
   :alt: Panel to modify cell metadata in JupyterLab

   Panel to modify cell metadata in JupyterLab

For example, this markup would create a thumbnail gallery:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         Thumbnails gallery
         ==================

         .. nbgallery::
            notebooks/Example 1
            notebooks/Example 2

   .. tab:: MyST (Markdown)

      .. code-block:: md

         # Thumbnails gallery

         ```{nbgallery}
         notebooks/Example 1
         notebooks/Example 2
         ```

.. figure:: /_static/images/guides/thumbnail-gallery.png
   :width: 80%
   :align: center
   :alt: Simple thumbnail gallery created using nbsphinx

   Simple thumbnail gallery created using nbsphinx

To see some examples of notebook galleries in the wild:

- `poliastro <https://docs.poliastro.space/>`_ offers tools for interactive Astrodynamics in Python,
  and features :doc:`several examples and how-to guides using notebooks <poliastro:gallery>`
  and displays them in an appealing thumbnail gallery.
  In addition, `poliastro uses unpaired MyST
  Notebooks <https://github.com/poliastro/poliastro/tree/0.15.x/docs/source/examples>`_
  to reduce repository size and improve integration with git.

Background
----------

.. _nb-background:

Existing relevant extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the first part of this document
we have seen that `nbsphinx`_ and `MyST-NB`_ are similar.
However, there are some differences between them:

- nsphinx uses `pandoc <https://pandoc.org/>`_
  to convert the Markdown from Jupyter notebooks to reStructuredText
  and then to `docutils AST <https://docutils.sourceforge.io/docs/ref/doctree.html>`_,
  whereas MyST-NB uses `MyST-Parser`_
  to directly convert the Markdown text to docutils AST.
  Therefore, nbsphinx assumes `pandoc flavored Markdown <https://pandoc.org/MANUAL.html#pandocs-markdown>`_,
  whereas MyST-NB uses :doc:`MyST flavored Markdown <myst-parser:index>`.
  Both Markdown flavors are mostly equal,
  but they have some differences.
- nbsphinx executes each notebook during the parsing phase,
  whereas MyST-NB can execute all notebooks up front
  and cache them with `jupyter-cache <https://jupyter-cache.readthedocs.io/>`_.
  This can result in shorter build times when notebooks are modified
  if using MyST-NB.
- nbsphinx provides functionality to create thumbnail galleries,
  whereas MyST-NB does not have such functionality at the moment
  (see :ref:`notebook-galleries` for more information about galleries).
- MyST-NB allows embedding Python objects coming from the notebook in the documentation
  (read :doc:`their "glue" documentation <myst-nb:render/glue>`
  for more information)
  and provides more sophisticated :doc:`error reporting <myst-nb:computation/execute>`
  than the one nbsphinx has.
- The visual appearance of code cells and their outputs is slightly different:
  nbsphinx renders the cell numbers by default,
  whereas MyST-NB doesn't.

.. _nbsphinx: https://nbsphinx.readthedocs.io/
.. _MyST-NB: https://myst-nb.readthedocs.io/
.. _MyST-Parser: https://myst-parser.readthedocs.io/
.. _jupytext: https://jupytext.readthedocs.io/

Deciding which one to use depends on your use case. As general recommendations:

- If you want to use :ref:`other notebook formats <other-formats>`
  or :ref:`generate a thumbnail gallery from your notebooks <notebook-galleries>`,
  nbsphinx is the right choice.
- If you want to leverage a more optimized execution workflow
  and a more streamlined parsing mechanism,
  as well as some of the unique MyST-NB functionalities,
  you should use MyST-NB.

Alternative notebook formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jupyter notebooks in ``.ipynb`` format
(as described in the `nbformat
documentation <https://nbformat.readthedocs.io/>`_)
are by far the most widely used for historical reasons.

However, to compensate some of the disadvantages of the ``.ipynb`` format
(like cumbersome integration with version control systems),
`jupytext`_ offers :doc:`other formats <jupytext:formats-markdown>`
based on plain text rather than JSON.

As a result, there are three modes of operation:

- Using classic ``.ipynb`` notebooks. It's the most straightforward option,
  since all the tooling is prepared to work with them,
  and does not require additional pieces of software.
  It is therefore simpler to manage, since there are fewer moving parts.
  However, it requires some care when working with Version Control Systems (like git),
  by doing one of these things:

  - Clear outputs before commit.
    Minimizes conflicts, but might defeat the purpose of notebooks themselves,
    since the computation results are not stored.
  - Use tools like `nbdime <https://nbdime.readthedocs.io/>`_ (open source)
    or `ReviewNB <https://www.reviewnb.com/>`_ (proprietary)
    to improve the review process.
  - Use a different collaboration workflow that doesn't involve notebooks.

- Replace ``.ipynb`` notebooks with :doc:`a text-based format <jupytext:formats-markdown>`.
  These formats behave better under version control
  and they can also be edited with normal text editors
  that do not support cell-based JSON notebooks.
  However, text-based formats do not store the outputs of the cells,
  and this might not be what you want.
- Pairing ``.ipynb`` notebooks with a text-based format,
  and putting the text-based file in version control,
  as suggested in the :doc:`jupytext documentation <jupytext:paired-notebooks>`.
  This solution has the best of both worlds.
  In some rare cases you might experience synchronization issues between both files.

These approaches are not mutually exclusive,
nor you have to use a single format for all your notebooks.
For the examples in this document, we have used the :doc:`MyST Markdown
format <jupytext:formats-markdown>`.

If you are using alternative formats for Jupyter notebooks,
you can include them in your Sphinx documentation
using either `nbsphinx`_ or `MyST-NB`_
(see :ref:`nb-background`
for more information about the differences between them).
