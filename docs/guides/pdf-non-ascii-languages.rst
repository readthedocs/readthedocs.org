Build PDF format for non-ASCII languages
========================================


.. warning::

   To be able to follow this guide and build PDF with this method,
   you need to ask to enable ``USE_PDF_LATEXMK`` :doc:`feature flag </guides/feature-flags>` in your project.
   Please, `open an issue`_ in our repository asking for this and wait for one of the core team to enable it.

.. _open an issue: https://github.com/rtfd/readthedocs.org/issues/new


Sphinx comes with support for different `LaTeX engines`_ that support non-ASCII languages,
like Japanese or Chinese, for example.
By default Sphinx uses ``pdflatex``,
which does not have good support for Unicode characters and may make the PDF builder to fail on these languages.

.. _LaTeX engines: http://www.sphinx-doc.org/en/master/usage/configuration.html#confval-latex_engine

In case you want to build your documentation in PDF format you need to configure Sphinx properly,
so Read the Docs can execute the proper commands depending on these settings.
There are `several settings that can be defined`_ (all the ones starting with ``latex_``),
to modify Sphinx and Read the Docs behavior to make your documentation to build properly.

A good first try would be to use only ``latex_engine = 'xelatex'`` in your ``conf.py``,
if your docs are not written in Chinese or Japanese.
This is because your build could be failing just because of an Unicode error
(which ``xelatex`` has better support for them than the default ``pdflatex``)

.. _several settings that can be defined: http://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-latex-output

When Read the Docs detects that your documentation is in Chinese or Japanese it automatically adds some defaults for you.

For *Chinese* projects, it appends to your ``conf.py`` these configurations:

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

   You can always override these configurations if you define them by yourself in your ``conf.py`` file.

.. note::

   ``xindy`` is currently not supported by Read the Docs,
   but we plan to support it in the near future.
