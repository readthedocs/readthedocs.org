How to use Jupyter notebooks in Sphinx
======================================

`Jupyter`_ notebooks are a popular tool to describe computational narratives
that mix code, prose, images, interactive components, and more.
Embedding them in your Sphinx project allows using these rich documents as documentation,
which can provide a great experience for tutorials, examples, and other types of technical content.
There are a few extensions that allow integrating Jupyter and Sphinx,
and this document will explain how to achieve some of the most commonly requested features.

.. _Jupyter: https://jupyter.org/

By default, `Sphinx only supports reStructuredText source files for
documentation <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-source_suffix>`_.
Luckily, there are a few extensions to also allow Jupyter notebooks as source files.

.. _ipynb-notebooks-sphinx:

Including ``.ipynb`` notebooks in Sphinx documentation
------------------------------------------------------

There are two main extensions that add support for ``.ipynb`` as source files in Sphinx:
nbsphinx_ and MyST-NB_. Even though they have some differences,
their basic mode of operation is very similar. However, they are mutually exclusive,
so you have to choose one of them.

.. _nbsphinx: https://nbsphinx.readthedocs.io/
.. _MyST-NB: https://myst-nb.readthedocs.io/

First of all, create a Jupyter notebook using the editor of your liking (for example, JupyterLab_).
For example, ``source/notebooks/Example 1.ipynb``:

.. figure:: /_static/images/guides/example-notebook.png
   :width: 80%
   :align: center
   :alt: Example Jupyter notebook created on JupyterLab

   Example Jupyter notebook created on JupyterLab

.. _JupyterLab: https://jupyterlab.readthedocs.io/

Next, you will need to enable one of the extensions. For example, in the case of nbsphinx:

.. code-block:: python
   :caption: conf.py

   # Add any Sphinx extension module names here, as strings. They can be
   # extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
   # ones.
   extensions = [
       "nbsphinx",
       # "myst_nb",  # In case you want to use MyST-NB instead
   ]

Both extensions will register themselves as processors for ``.ipynb`` notebooks,
so you don't need to change the
`source_suffix <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-source_suffix>`_
configuration yourself.

Finally, you can include the notebook in any *toctree*.
For example, add this to your root document:

.. code-block:: rest

   .. toctree::
      :maxdepth: 2
      :caption: Contents:

      notebooks/Example 1

The notebook will render as any other HTML page in your documentation
after doing ``make html``.

.. figure:: /_static/images/guides/example-notebook-rendered.png
   :width: 80%
   :align: center
   :alt: Example Jupyter notebook rendered on HTML by nbsphinx

   Example Jupyter notebook rendered on HTML by nbsphinx

To further customize the rendering process among other things,
refer to the nbsphinx_ or MyST-NB_ documentation.

.. note::

   The visual appearance of code cells and their outputs
   is slightly different in nbsphinx and MyST-NB:
   the former renders the cell numbers by default,
   whereas the latter doesn't.

Rendering interactive widgets
-----------------------------

You can also embed interactive widgets from Jupyter notebooks created using ipywidgets_
on HTML Sphinx documentation. This includes basic widgets from ipywidgets_ and also
more complex ones,
like `ipyleaflet`_ visualizations.

.. _ipyleaflet: https://ipyleaflet.readthedocs.io/

For this to work, it's necessary to *save the widget state*
before generating the HTML documentation,
otherwise the widget will appear as empty.
Each editor has a different way of doing it:

- The classical Jupyter Notebook interface
  provides a "Save Notebook Widget State" action in the "Widgets" menu,
  `as explained in the ipywidgets
  documentation <https://ipywidgets.readthedocs.io/en/latest/embedding.html#embedding-widgets-in-html-web-pages>`_.
  You need to click it before exporting your notebook to HTML.
- JupyterLab provides a "Save Widget State Automatically" option in the "Settings" menu.
  You need to leave it checked so that widget state is automatically saved.
- In Visual Studio Code `it's not possible to save the widget
  state <https://github.com/microsoft/vscode-jupyter/issues/4404>`_
  at the time of writing.

.. _ipywidgets: https://ipywidgets.readthedocs.io/

.. figure:: /_static/images/guides/jupyterlab-save-widget-state.png
   :width: 30%
   :align: center
   :alt: JupyterLab option to save the interactive widget state automatically

   JupyterLab option to save the interactive widget state automatically

For example, if you create a notebook with a simple
`IntSlider <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20List.html#IntSlider>`_
widget from ipywidgets and save the widget state,
the slider will render correctly in Sphinx.

.. figure:: /_static/images/guides/widget-html.gif
   :width: 80%
   :align: center
   :alt: Interactive widget rendered in HTML by Sphinx

   Interactive widget rendered in HTML by Sphinx

To see more elaborate examples:

- `ipyleaflet`_ provides several widgets for interactive maps,
  and renders live versions of them `in their
  documentation <https://ipyleaflet.readthedocs.io/en/latest/api_reference/velocity.html>`_.
- `PyVista <https://docs.pyvista.org/>`_ is used for scientific 3D visualization
  with several interactive backends and `examples in their
  documentation <https://docs.pyvista.org/index.html#maps-and-geoscience>`_ as well.

.. warning::

   Although widgets themselves can be embedded in HTML as shown above,
   `events <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Events.html>`_
   require a backend (kernel) to execute.
   Therefore, ``@interact``, ``.observe``, and related functionalities relying on them
   will not work as expected.

Creating galleries of examples using notebooks
----------------------------------------------

If you want to create an HTML gallery of examples for your project,
`Sphinx-Gallery <https://sphinx-gallery.github.io/>`_
offers a very convenient way of doing so from Sphinx,
including thumbnail generation.
However, `it works with Python scripts rather than
notebooks <https://github.com/sphinx-gallery/sphinx-gallery/issues/245>`_,
which might not be what you want.

`nbsphinx`_ has support for `creating thumbnail galleries from a list of Jupyter
notebooks <https://nbsphinx.readthedocs.io/en/latest/subdir/gallery.html>`_,
and it is compatible with Sphinx-Gallery styles.
To use it, you will need to install both nbsphinx and Sphinx-Gallery,
and modify your ``conf.py`` as follows:

.. code-block:: python
   :caption: conf.py

   extensions = [
      'nbsphinx',
      'sphinx_gallery.load_style',
   ]

After doing that, there are two ways to create the gallery:

- From a reStructuredText source file, using the ``.. nbgallery::`` directive,
  `as showcased in the
  documentation <https://nbsphinx.readthedocs.io/en/latest/a-normal-rst-file.html#thumbnail-galleries>`_.
- From a Jupyter notebook, adding a ``"nbsphinx-gallery"`` tag to the metadata of a cell.
  Each editor has a different way of modifying the cell metadata (see figure below).

.. figure:: /_static/images/guides/jupyterlab-metadata.png
   :width: 80%
   :align: center
   :alt: Panel to modify cell metadata in JupyterLab

   Panel to modify cell metadata in JupyterLab

For example, this reST markup would create a thumbnail gallery
with generic images as thumbnails,
thanks to the Sphinx-Gallery default style:

.. code-block:: rest

   Thumbnails gallery
   ==================

   .. nbgallery::
      notebooks/Example 1
      notebooks/Example 2

.. figure:: /_static/images/guides/thumbnail-gallery.png
   :width: 80%
   :align: center
   :alt: Simple thumbnail gallery created using nbsphinx

   Simple thumbnail gallery created using nbsphinx

Using notebooks in other formats
--------------------------------

Jupyter notebooks in ``.ipynb`` format
(as described in the `nbformat
documentation <https://nbformat.readthedocs.io/en/latest/>`_)
are by far the most widely used for historical reasons.

However, to compensate some of the disadvantages of the ``.ipynb`` format
(like cumbersome integration with version control systems),
`jupytext`_ offers `other formats <https://jupytext.readthedocs.io/en/latest/formats.html>`_
based on plain text rather than JSON.

One of such formats is the `MyST Markdown
format <https://jupytext.readthedocs.io/en/latest/formats.html#myst-markdown>`_,
which is based on `MyST`_, an extensible flavor of Markdown
that includes some features from reStructuredText.

If you are interested in using alternative formats for Jupyter notebooks,
nowadays there are two main ways to include them
in your Sphinx documentation:

- Parsing the notebooks with `jupytext`_ and rendering them with `nbsphinx`_.
  It is especially convenient if you are already using nbsphinx,
  or if you want to use a notebook format
  different from both ``.ipynb`` and MyST Markdown.
- Using `MyST-NB`_. This is the simplest option
  if you don't need any of nbsphinx or jupytext functionalities.

.. _jupytext: https://jupytext.readthedocs.io/
.. _MyST: https://myst-parser.readthedocs.io/

.. note::

   In summary: both nbsphinx and MyST-NB
   can parse ``.ipynb`` notebooks and include them in Sphinx documentation
   (:ref:`see above <ipynb-notebooks-sphinx>`).
   In addition, MyST-NB can read MyST Markdown notebooks,
   and nbsphinx can read any alternative formats understood by jupytext.

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

To render this notebook in Sphinx using nbsphinx and jupytext,
you will need to add this to your ``conf.py``:

.. code-block:: python
   :caption: conf.py

   nbsphinx_custom_formats = {
      '.md': ['jupytext.reads', {'fmt': 'mystnb'}],
   }

Notice that the Markdown format does not store the outputs of the computation.
nbsphinx will automatically execute notebooks without outputs,
so in your HTML documentation they appear as complete.
