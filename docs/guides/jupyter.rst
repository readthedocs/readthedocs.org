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

TBC

Creating galleries of examples using notebooks
----------------------------------------------

TBC

Using notebooks in other formats
--------------------------------

TBC
