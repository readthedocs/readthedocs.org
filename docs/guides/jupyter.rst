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

.. _nb-background:

Background on the existing relevant extensions
----------------------------------------------

There are two main extensions that add support Jupyter notebooks as source files in Sphinx:
nbsphinx_ and MyST-NB_. Although they have similar intent and basic functionality,
there are some differences:

- nsphinx uses `pandoc <https://pandoc.org/>`_ to convert the Markdown from Jupyter notebooks
  to reStructuredText and then to docutils AST,
  whereas MyST-NB uses `MyST-Parser`_ to directly convert the Markdown text to docutils AST.
  Both Markdown flavors are mostly equal, but they have some differences.
- Both nbsphinx and MyST-NB support canonical ``.ipynb`` notebooks.
  nbsphinx can process any format supported by `jupytext`_,
  whereas MyST-NB focuses on MyST Markdown Notebooks
  (see :ref:`below <other-formats>` for more information about other notebook formats).
- nbsphinx executes each notebook during the parsing phase,
  whereas MyST-NB can execute all notebooks up front
  and cache them with `jupyter-cache <https://jupyter-cache.readthedocs.io/>`_.
  This can result in shorter build times when when notebooks are slightly modified
  if using MyST-NB.
- nbsphinx provides functionality to create thumbnail galleries,
  whereas MyST-NB does not have such functionality at the moment
  (see :ref:`below <notebook-galleries>` for more information about galleries).
- The visual appearance of code cells and their outputs is slightly different:
  nbsphinx renders the cell numbers by default,
  whereas MyST-NB doesn't.

.. _nbsphinx: https://nbsphinx.readthedocs.io/
.. _MyST-NB: https://myst-nb.readthedocs.io/
.. _MyST-Parser: https://myst-parser.readthedocs.io/
.. _jupytext: https://jupytext.readthedocs.io/

Using which one to use depends on your use case. As general recommendations:

- If you want to use :ref:`other notebook formats <other-formats>`
  or :ref:`generate a thumbnail gallery from your notebooks <notebook-galleries>`,
  nbsphinx is the right choice.
- If you will be focusing on MyST Markdown notebooks
  or want to leverage a more optimized execution workflow
  and a more streamlined parsing mechanism,
  you should use MyST-NB.

For the rest of this document we will focus on `nbsphinx`_
because it is more flexible and offers some extra functionality,
and we will point out the differences with `MyST-NB`_ where appropriate.
Notice that they can't both be used at the same time.

.. _ipynb-notebooks-sphinx:

Including classic ``.ipynb`` notebooks in Sphinx documentation
--------------------------------------------------------------

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

.. _notebook-galleries:

Creating galleries of examples using notebooks
----------------------------------------------

`nbsphinx`_ has support for `creating thumbnail galleries from a list of Jupyter
notebooks <https://nbsphinx.readthedocs.io/en/latest/subdir/gallery.html>`_.
This functionality relies on `Sphinx-Gallery <https://sphinx-gallery.github.io/>`_
and extends it to work with Jupyter notebooks rather than Python scripts.

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

Background on alternative notebook formats
------------------------------------------

Jupyter notebooks in ``.ipynb`` format
(as described in the `nbformat
documentation <https://nbformat.readthedocs.io/en/latest/>`_)
are by far the most widely used for historical reasons.

However, to compensate some of the disadvantages of the ``.ipynb`` format
(like cumbersome integration with version control systems),
`jupytext`_ offers `other formats <https://jupytext.readthedocs.io/en/latest/formats.html>`_
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

- Replace ``.ipynb`` notebooks with `a text-based
  format <https://jupytext.readthedocs.io/en/latest/formats.html>`_.
  These formats behave better under version control
  and they can also be edited with normal text editors
  that do not support cell-based JSON notebooks.
  However, text-based formats do not store the outputs of the cells,
  and this might not be what you want.
- Pairing ``.ipynb`` notebooks with a text-based format,
  and putting the text-based file in version control,
  as suggested in the `jupytext
  documentation <https://jupytext.readthedocs.io/en/latest/paired-notebooks.html>`_.
  This solution has the best of both worlds.
  In some rare cases you might experience synchronization issues between both files.

These approaches are not mutually exclusive,
nor you have to use a single format for all your notebooks.
For the examples in this document, we will use the `MyST Markdown
format <https://jupytext.readthedocs.io/en/latest/formats.html#myst-markdown>`_.

If you are using alternative formats for Jupyter notebooks,
there are two main ways to include them
in your Sphinx documentation:

- Parsing the notebooks with `jupytext`_ and rendering them with `nbsphinx`_.
  It is especially convenient if you are already using nbsphinx,
  or if you want to use a notebook format
  different from both ``.ipynb`` and MyST Markdown.
- Using `MyST-NB`_. This is the simplest option
  if you don't need any of nbsphinx or jupytext functionalities.

.. _MyST: https://myst-parser.readthedocs.io/

.. note::

   In summary: both nbsphinx and MyST-NB
   can parse ``.ipynb`` notebooks and include them in Sphinx documentation.
   In addition, MyST-NB can read MyST Markdown notebooks,
   and nbsphinx can read any alternative formats understood by jupytext.
   You can :ref:`read more above <nb-background>`.

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
