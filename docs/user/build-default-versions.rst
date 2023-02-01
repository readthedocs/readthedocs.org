:orphan:


.. This page contains good detailed content about the exact versions Read the
   Docs is install by default, but I don't think it's good content as a
   user-facing documentation page. However, I'm keeping it around and linking it
   from the "Build process" page when mentioning there are some dependencies
   installed by default.

Default versions of dependencies
================================

Read the Docs supports two tools to build your documentation:
`Sphinx <https://www.sphinx-doc.org/>`__ and `MkDocs <https://www.mkdocs.org/>`__.
In order to provide :doc:`several features </features>`,
Read the Docs injects or modifies some content while building your docs.

In particular, if you don't specify the dependencies of your project,
we install some of them on your behalf.
In the past we used to pin these dependencies to a specific version and update them after some time,
but doing so would break some builds and make it more difficult for new projects to use new versions.
For this reason, we are now installing their latest version by default.

.. note::

   In order to keep your builds reproducible,
   it's highly recommended declaring its dependencies and versions explicitly.
   See :doc:`/guides/reproducible-builds`.

External dependencies
---------------------

Python
~~~~~~

These are the dependencies that are installed by default when using a Python environment:

Sphinx:
  Projects created before Oct 20, 2020 use ``1.8.x``.
  New projects use the latest version.

Mkdocs:
  Projects created before April 3, 2019 (April 23, 2019 for :doc:`/commercial/index`) use ``0.17.3``.
  Projects created before March 9, 2021 use ``1.0.4``.
  New projects use the latest version.

sphinx-rtd-theme:
  Projects created before October 20, 2020 (January 21, 2021 for :doc:`/commercial/index`) use ``0.4.3``.
  New projects use the latest version.

pip:
  Latest version by default.

setuptools:
  ``58.2.0`` or older.

mock:
  ``1.0.1`` (could be removed in the future).

pillow:
  ``5.4.1`` when using Python 2.7, 3.4, 3.5, 3.6, 3.7. Otherwise, its latest version
  (could be removed in the future).

alabaster:
  ``0.7.x`` (could be removed in the future).

commonmark:
  ``0.8.1`` (could be removed in the future).

recommonmark:
  ``0.5.0`` (could be removed in the future).

Conda
~~~~~

These are the dependencies that are installed by default when using a Conda environment:

Conda:
   Miniconda2 ``4.6.14``
   (could be updated in the future to use the latest version by default).

Mkdocs:
  Latest version by default installed via ``conda``.

Sphinx:
  Latest version by default installed via ``conda``.

sphinx-rtd-theme:
  Latest version by default installed via ``conda``.

mock:
  Latest version by default installed via ``pip`` (could be removed in the future).

pillow:
  Latest version by default installed via ``pip`` (could be removed in the future).

recommonmark:
  Latest version by default installed via ``conda`` (could be removed in the future).

Internal dependencies
---------------------

Internal dependencies are needed to integrate your docs with Read the Docs.
We guarantee that these dependencies will work with all current supported versions of our tools,
you don't need to specify them in your requirements.

- `readthedocs-sphinx-ext <https://github.com/readthedocs/readthedocs-sphinx-ext>`__
