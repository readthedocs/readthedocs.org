How to use Jupyter notebooks in Sphinx
======================================

By default, `Sphinx only supports reStructuredText source files for
documentation <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-source_suffix>`_.
Luckily, there are a few extensions to also allow Jupyter notebooks as source files.

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

TBC

Using notebooks in other formats
--------------------------------

TBC
