Build PDF format for non-ASCII languages
========================================

Sphinx offers different `LaTeX engines`_ that support Unicode characters and non-ASCII languages,
like Japanese or Chinese.
By default Sphinx uses ``pdflatex``,
which does not have good support for Unicode characters and may make the PDF builder fail.

.. _LaTeX engines: http://www.sphinx-doc.org/en/master/usage/configuration.html#confval-latex_engine

To build your documentation in PDF format, you need to configure Sphinx properly in your project's ``conf.py``.
Read the Docs will execute the proper commands depending on these settings.
There are `several settings that can be defined`_ (all the ones starting with ``latex_``),
to modify Sphinx and Read the Docs behavior to make your documentation to build properly.

.. _several settings that can be defined: http://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-latex-output

For docs that are not written in Chinese or Japanese,
and if your build fails from a Unicode error,
then try ``xelatex`` as the ``latex_engine`` instead of the default ``pdflatex`` in your ``conf.py``:

.. code-block:: python

    latex_engine = 'xelatex'

When Read the Docs detects that your documentation is in Chinese or Japanese,
it automatically adds some defaults for you.

For *Chinese* projects, it appends to your ``conf.py`` these settings:

.. code-block:: python

    latex_engine = 'xelatex'
    latex_use_xindy = False
    latex_elements = {
        'preamble': '\\usepackage[UTF8]{ctex}\n',
    }

And for *Japanese* projects:

.. code-block:: python

    latex_engine = 'platex'
    latex_use_xindy = False

.. tip::

   You can always override these settings if you define them by yourself in your ``conf.py`` file.

.. note::

   ``xindy`` is currently not supported by Read the Docs,
   but we plan to support it in the near future.
